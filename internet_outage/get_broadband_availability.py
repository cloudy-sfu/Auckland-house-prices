import json
import logging
import os
import secrets
import sys
import time
import uuid
from math import ceil

import pandas as pd
from requests import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from tqdm import tqdm

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
engine = create_engine(os.environ['NEON_DB'], poolclass=NullPool)


def rate_limit(header_):
    remained_1_str, remained_2_str = header_['x-ratelimit-remaining'].split(',')
    remained_1 = int(remained_1_str)
    remained_2 = int(remained_2_str)
    reset_1_str, reset_2_str = header_['x-ratelimit-reset'].split(',')
    reset_1 = int(reset_1_str)  # unit: 1e-3 second
    reset_1_s = ceil(reset_1 / 100) / 10  # round up to 0.1 second
    reset_2 = int(reset_2_str)
    reset_2_s = ceil(reset_2 / 100) / 10
    if remained_1 <= 0:  # reached daily limit
        if reset_1_s > 30:
            # according to tests, usually reset at about 11:15 UTC+13
            # winter time haven't tested
            return False  # the program should store data and quit
        else:
            time.sleep(reset_1_s)
    if remained_2 <= 0:
        time.sleep(reset_2_s)
    return True


# %% Get headers.
with open("internet_outage/chorus_address_look_up.json") as f:
    header_address = json.load(f)
header_address['x-transaction-id'] = str(uuid.uuid4())
with open("internet_outage/chorus_broadband_availability.json") as f:
    header_availability = json.load(f)

# %% Get address to fetch.
with open("internet_outage/missing_broadband_availability_trademe.sql") as f:
    sql_listings = f.read()
with engine.connect() as c:
    listings = pd.read_sql(sql_listings, c)

# %% Main loop.
records = []
trademe_chorus_link = []
valve_1 = valve_2 = valve_3 = True
for i, row in tqdm(listings.iterrows(), total=listings.shape[0]):
    address = row['address']

    # %% Check conditions to quit loop.
    if i % 500 == 0:
        records_df = pd.DataFrame(records)
        logging.info(f"Queued {records_df.shape[0]} records of broadband availability, "
                     f"uploading to database.")
        upsert_dataframe(
            engine,
            records_df,
            ["tlc"],
            "internet_availability"
        )
        records.clear()
        trademe_chorus_link_df = pd.DataFrame(trademe_chorus_link)
        logging.info(f"Queued {records_df.shape[0]} records of trademe listing ID and "
                     f"Chorus address ID pairs, uploading to database.")
        upsert_dataframe(
            engine,
            trademe_chorus_link_df,
            ["listing_id"],
            "properties_trademe_chorus_tlc"
        )
    if not (valve_1 and valve_2 and valve_3):
        logging.warning("Chorus API reaches daily limit and won't reset shortly, stop.")
        break

    now = pd.Timestamp('now', tz='UTC')
    if now - script_start_time > pd.Timedelta(hours=5, minutes=45):
        logging.warning("Execution time reaches 5 hours and 45 minutes, stop.")
        break

    try:
        # %% Get "aid".
        response = session.get(
            "https://api.chorus.co.nz/addresslookup/v1/addresses",
            params={"fuzzy": "true", "q": address},
            headers=header_address,
        )
        response.raise_for_status()
        valve_1 = rate_limit(response.headers)
        response_json = response.json()
        assert response_json['results'], "Chorus cannot find AID of this address."
        aid = response_json['results'][0]['aid']
        if not valve_1:
            # the next step will use the same API again, so quit when reached the limit
            continue

        # %% Get "tlc".
        response = session.get(
            f"https://api.chorus.co.nz/addresslookup/v1/addresses/aid:{aid}",
            headers=header_address,
        )
        response.raise_for_status()
        valve_2 = rate_limit(response.headers)
        response_json = response.json()
        tlc = response_json['references']['tlc']
        structured_address = response_json['structuredAddress']
    except Exception as e:
        logging.warning(f"Fail to parse address and service ID of \"{address}\". "
                        f"{type(e).__name__}: {e}")
        trademe_chorus_link.append({
            "listing_id": row['listing_id'],
            "tlc": pd.NA,
        })
        continue
    else:
        trademe_chorus_link.append({
            "listing_id": row['listing_id'],
            "tlc": tlc,
        })

    try:
        # %% Get available service.
        sentry_trace_id = uuid.uuid4().hex
        sentry_span_id = secrets.token_hex(8)
        baggage = (f"sentry-environment=production,sentry-release=public-website-frontend"
                   f"%402.1.40,sentry-public_key=6d1e0cc8e0964ad2a39a4ced25ee0b3c,"
                   f"sentry-trace_id={sentry_trace_id}")
        header_availability_1 = header_availability.copy()
        header_availability_1['baggage'] = baggage
        header_availability_1['sentry-trace'] = f"{sentry_trace_id}-{sentry_span_id}"

        response = session.get(
            f"https://www.chorus.co.nz/api/bbc/bcc/{tlc}",
            headers=header_availability_1
        )
        response.raise_for_status()
        valve_3 = int(response.headers['X-RateLimit-Remaining']) > 0

        # %% Parse the best available service.
        response_json = response.json()
        assert response_json['success'], \
            f"Chorus raises status code {response_json['statusCode']}."
        services = pd.DataFrame(response_json['available_services'])
        if services.empty:
            service_name = pd.NA
            max_speed = pd.NA
        else:
            services = services.loc[services['capable'] == 'YES', :]
            services_b = services.iloc[services['speed_mbps'].argmax()]
            max_speed = services_b['speed_mbps']
            service_name = services_b['service']
    except Exception as e:
        logging.warning(f"Fail to parse broadband availability of \"{address}\". "
                        f"{type(e).__name__}: {e}")
        service_name = pd.NA
        max_speed = pd.NA
    records.append({
        "tlc": tlc,
        "unit": structured_address.get('unit'),
        "street_number": structured_address.get('streetNumber'),
        "street_name": structured_address.get('streetName'),
        "road_type": structured_address.get('roadType'),
        "suburb": structured_address.get('suburb'),
        "service_name": service_name,
        "max_speed": max_speed,
        "aid": aid,
    })

records_df = pd.DataFrame(records)
logging.info(f"Queued {records_df.shape[0]} records of broadband availability, "
             f"uploading to database.")
upsert_dataframe(
    engine,
    records_df,
    ["tlc"],
    "internet_availability"
)
records.clear()
trademe_chorus_link_df = pd.DataFrame(trademe_chorus_link)
logging.info(f"Queued {records_df.shape[0]} records of trademe listing ID and "
             f"Chorus address ID pairs, uploading to database.")
upsert_dataframe(
    engine,
    trademe_chorus_link_df,
    ["listing_id"],
    "properties_trademe_chorus_tlc"
)