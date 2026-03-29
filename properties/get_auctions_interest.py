import json
import logging
import os
import random
import re
import sys
import time

import pandas as pd
from bs4 import BeautifulSoup
from requests import Session
from sqlalchemy import create_engine, text

from postgresql_upsert import upsert_dataframe

# %% Initialization.
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
)
script_start_time = pd.Timestamp('now', tz='UTC')
session = Session()
with open("properties/header_interest.json") as f:
    header = json.load(f)
listings = []
engine = create_engine(os.environ['NEON_DB'], pool_recycle=300)
with engine.begin() as c:
    result = c.execute(text("select max(solving_start_time) from collect_auction_interest "
                            "where solving_end_time is not null;"))
    last_checkout_time = result.fetchone()[0]
    result = c.execute(text("insert into collect_auction_interest default values "
                            "returning id;"))
    task_id = result.fetchone()[0]
if last_checkout_time is None:
    last_checkout_time = pd.Timestamp(0, tz="UTC")
last_auction_date = (last_checkout_time - pd.Timedelta(days=1)).date()

# %% Main.
base_url = "https://www.interest.co.nz/property/auction-results/load-more-properties"
page_size = 25
n = page_size
i = 0
max_failed_pages = 5
failed_pages = 0
is_github_actions = os.getenv("GITHUB_ACTIONS") == "true"
while n == page_size:
    if i % int(500 / page_size) == 0:
        listings_df = pd.DataFrame(listings)
        listings_df = listings_df.convert_dtypes()
        listings_df.drop_duplicates(subset=["auction_date", "address"], inplace=True)
        logging.info(f"Queued {listings_df.shape[0]} records of auctions, uploading to "
                     f"database.")
        upsert_dataframe(
            engine,
            listings_df,
            ["auction_date", "address"],
            "properties_auction_interest",
        )
        listings.clear()

    if (is_github_actions and pd.Timestamp('now', tz='UTC') - script_start_time
            > pd.Timedelta(hours=5, minutes=45)):
        logging.warning("Execution time reaches 5 hours and 45 minutes, stop.")
        with engine.begin() as c:
            c.execute(text("UPDATE collect_auction_interest SET solving_end_time = NOW(), "
                           "stop_before_page = :page "
                           "WHERE id = :task_id"),
                      {"page": i, "task_id": task_id})
        break

    request_args = {
        "offset": i * page_size,
        "section": "Residential",
        "region": "auckland",
        "district": "-",
        "suburb": "-",
    }
    request_url = base_url + "?" + "&".join(f"{k}={v}" for k, v in request_args.items())
    header_ins = header.copy()
    header_ins['referer'] = request_url
    try:
        response = session.get(url=base_url, params=request_args, headers=header_ins)
        response.raise_for_status()
        web_page = BeautifulSoup(response.text, "html.parser")
        listings_raw = web_page.find_all(
            'div', {'class': "padb-new-property-card"})
    except Exception as e:
        logging.warning(f"Fail to fetch page {i} (index from 0), skip. "
                        f"{type(e).__name__}: {e}")
        failed_pages += 1
        if failed_pages <= max_failed_pages:
            with engine.begin() as c:
                c.execute(text("UPDATE collect_auction_interest SET failed_pages = "
                               "array_append(COALESCE(failed_pages, ARRAY[]::integer[]), "
                               ":page) WHERE id = :task_id;"),
                          {"page": i, "task_id": task_id})
            continue
        else:
            with engine.begin() as c:
                c.execute(text("UPDATE collect_auction_interest SET stop_before_page = "
                               ":page WHERE id = :task_id;"),
                          {"page": i, "task_id": task_id})
            logging.error("Exceed maximum number pages failed to parse, stop.")
            break
    else:
        time.sleep(random.uniform(0.3, 0.7))

    n = len(listings_raw)
    for house in listings_raw:
        try:
            bedroom = int(house.find('div', {'class': 'padb-beds'}).text)
        except:
            bedroom = None
        try:
            bathroom = int(house.find('div', {'class': 'padb-baths'}).text)
        except:
            bathroom = None
        try:
            parking = int(house.find('div', {'class': 'padb-parking'}).text)
        except:
            parking = None
        try:
            address = house.find('div', {'class': 'bottom-row'}).text
            address = address.strip()[:128]
        except:
            logging.warning("Skipped a house where address (part of primary key) is not "
                            "available.")
            continue
        try:
            sold_desc = house.find('div', {'class': 'property-status'}).text
            sold_desc = sold_desc.strip()
            match = re.search(
                r'Sold\s+for\s+\$+([0-9]{1,3}(?:,[0-9]{3})*)', sold_desc)
            if match:
                sold = True
                price = int(match.group(1).replace(",", ""))
                status = "Sold"
            else:
                sold = False
                price = None
                status = sold_desc[:16]
        except:
            sold = None
            price = None
            status = None
        try:
            qv_est = (house.find('div', {'class': 'rv-block'})
                      .find('span', {'class': None}).text)
            qv_est = int(qv_est.strip().removeprefix("$").replace(",", ""))
        except:
            qv_est = None
        try:
            span = house.find('span', string=lambda t: t and 'Agents:' in t)
            agents = "".join(span.parent.find_all(string=True, recursive=False))
            agents = [name.strip()[:32] for name in agents.split(",")]
        except:
            agents = []
        try:
            span = house.find('span', string=lambda t: t and 'Agency:' in t)
            agency = "".join(span.parent.find_all(string=True, recursive=False))
            agency = agency.strip()[:32]
        except:
            agency = None
        try:
            span = house.find('span', string=lambda t: t and 'Auction date:' in t)
            date_raw = "".join(span.parent.find_all(string=True, recursive=False))
            date_raw = date_raw.strip()
            date_raw = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_raw)
            date_ = pd.to_datetime(date_raw, format="%A, %d %B '%y").date()
        except:
            logging.warning("Skipped a house where auction date (part of primary key) is "
                            "not available.")
            continue

        if date_ <= last_auction_date:
            logging.info(f"Reached last completely recorded auction date "
                         f"{last_auction_date}, stop.")
            break

        listings.append({
            "bedroom": bedroom,
            "bathroom": bathroom,
            "parking": parking,
            "address": address,
            "sold": sold,
            "price": price,
            "status": status,
            "qv_estimation": qv_est,
            "agents": agents,
            "auction_date": date_,
            "agency": agency,
            "task_id": task_id,
        })
    logging.info(f"Finished processing page {i}.")
    i += 1

listings_df = pd.DataFrame(listings)
listings_df = listings_df.convert_dtypes()
listings_df.drop_duplicates(subset=["auction_date", "address"], inplace=True)
logging.info(f"Queued {listings_df.shape[0]} records of auctions, uploading to "
             f"database.")
upsert_dataframe(
    engine,
    listings_df,
    ["auction_date", "address"],
    "properties_auction_interest",
)
listings.clear()

with engine.begin() as c:
    c.execute(text("UPDATE collect_auction_interest SET solving_end_time = NOW(), "
                   "complete_after_page = :page "
                   "WHERE id = :task_id"),
              {"page": i, "task_id": task_id})
