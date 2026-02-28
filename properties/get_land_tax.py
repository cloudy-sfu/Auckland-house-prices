import json
import logging
import os
import sys

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
with open("properties/header_council.json") as f:
    header = json.load(f)
header_1 = header.copy()
header_1['referer'] = ("https://www.aucklandcouncil.govt.nz/en/property-rates-valuations/"
                       "find-property-rates-valuation.html")
header_1['host'] = "www.aucklandcouncil.govt.nz"
engine = create_engine(os.environ['NEON_DB'], poolclass=NullPool)


def get_int(d, key):
    value = d.get(key)
    try:
        value = int(value)
    except TypeError:
        value = pd.NA
    except ValueError:
        try:
            value = float(value)
            value = round(value)
        except ValueError:
            value = pd.NA
    return value


def get_float(d, key):
    value = d.get(key)
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = pd.NA
    return value


# %% Get address to fetch.
with open("properties/missing_land_tax_trademe.sql") as f:
    sql_listings = f.read()
with engine.connect() as c:
    listings = pd.read_sql(sql_listings, c)

# %% Main loop.
trademe_land_link = []
records = []
for i, row in tqdm(listings.iterrows(), total=listings.shape[0]):
    address = row['address']

    # %% Check conditions to quit loop.
    if i % 500 == 0:
        trademe_land_link_df = pd.DataFrame(trademe_land_link)
        logging.info(f"Queued {trademe_land_link_df.shape[0]} records of "
                     f"trademe listing ID and Auckland Council rate account key pairs, "
                     f"uploading to database.")
        upsert_dataframe(
            engine,
            trademe_land_link_df,
            ["listing_id"],
            "properties_trademe_land_rate_account_key"
        )
        trademe_land_link.clear()
        records_df = pd.DataFrame(records)
        logging.info(f"Queued {records_df.shape[0]} records of land tax, uploading to "
                     f"database.")
        upsert_dataframe(
            engine,
            records_df,
            ["land_id"],
            "properties_land_tax"
        )
        records.clear()

    now = pd.Timestamp('now', tz='UTC')
    if now - script_start_time > pd.Timedelta(hours=5, minutes=45):
        logging.warning("Execution time reaches 5 hours and 45 minutes, stop.")
        break

    try:
        # %% Get property ID.
        response = session.get(
            "https://experience.aucklandcouncil.govt.nz/nextapi/property",
            params={"query": address, "pageSize": "10"},
            headers=header
        )
        response.raise_for_status()
        response_json = response.json()
        land_id = response_json['items'][0]['id']
    except Exception as e:
        logging.warning(f"Cannot find rate account key of \"{address}\" in "
                        f"Auckland council. {type(e).__name__}: {e}")
        trademe_land_link.append({
            "listing_id": row['listing_id'],
            "land_id": pd.NA,
        })
        continue
    else:
        trademe_land_link.append({
            "listing_id": row['listing_id'],
            "land_id": land_id,
        })

    try:
        # %% Get land information.
        response = session.get(
            f"https://www.aucklandcouncil.govt.nz/nextapi/property/"
            f"{land_id}/rate-assessment",
            headers=header_1,
        )
        response.raise_for_status()
        response_json = response.json()
    except Exception as e:
        logging.warning(f"Cannot find land information of \"{address}\" in "
                        f"Auckland council. {type(e).__name__}: {e}")
        continue

    # %% Parse land information.
    records.append({
        "land_id": land_id,
        "address": response_json.get('address', '')[:128],
        "land_area": get_int(response_json, 'area'),
        "floor_area": get_int(response_json, 'totalFloorArea'),
        "building_coverage_area": get_int(response_json, 'buildingSiteCoverage'),
        "land_value": get_int(response_json, 'landValue'),
        "improvements_value": get_int(response_json, 'valueOfImprovements'),
        "land_tax": get_float(response_json, 'totalRatesInclCip'),
        "land_usage": response_json.get('landUseDescription', '')[:64],
        "land_tax_break_down": response_json.get('rateBreakdown', {}),
    })

trademe_land_link_df = pd.DataFrame(trademe_land_link)
logging.info(f"Queued {trademe_land_link_df.shape[0]} records of "
             f"trademe listing ID and Auckland Council rate account key pairs, "
             f"uploading to database.")
upsert_dataframe(
    engine,
    trademe_land_link_df,
    ["listing_id"],
    "properties_trademe_land_rate_account_key"
)
trademe_land_link.clear()
records_df = pd.DataFrame(records)
logging.info(f"Queued {records_df.shape[0]} records of land tax, uploading to "
             f"database.")
upsert_dataframe(
    engine,
    records_df,
    ["land_id"],
    "properties_land_tax"
)
records.clear()