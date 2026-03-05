import json
import logging
import os
import sys

import pandas as pd
from requests import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from dict_ops import get_float, get_int
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

# %% Get address to fetch.
with open("properties/trademe_missing_land_tax.sql") as f:
    sql_listings = f.read()
with engine.connect() as c:
    listings = pd.read_sql(sql_listings, c)

# %% Main loop.
trademe_land_link = []
records = []
logging.info(f"Total number of properties to query land tax: {listings.shape[0]}")
for i, row in listings.iterrows():
    address = row['address']

    # %% Check conditions to quit loop.
    if i % 500 == 0:
        records_df = pd.DataFrame(records)
        records_df.drop_duplicates(subset=['assessment_id'], inplace=True)
        logging.info(f"Queued {records_df.shape[0]} records of land tax, uploading to "
                     f"database.")
        upsert_dataframe(
            engine,
            records_df,
            ["assessment_id"],
            "properties_land_tax"
        )
        records.clear()

        trademe_land_link_df = pd.DataFrame(trademe_land_link)
        logging.info(f"Queued {trademe_land_link_df.shape[0]} records of "
                     f"trademe listing ID and Auckland Council rate account key pairs, "
                     f"uploading to database.")
        upsert_dataframe(
            engine,
            trademe_land_link_df,
            ["listing_id"],
            "properties_trademe_land_tax_assess"
        )
        trademe_land_link.clear()

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
        assessment_id = response_json['items'][0]['id']
    except Exception as e:
        logging.warning(f"Cannot find rate account key of \"{address}\" in "
                        f"Auckland council. {type(e).__name__}: {e}")
        trademe_land_link.append({
            "listing_id": row['listing_id'],
            "assessment_id": pd.NA,
        })
        continue
    else:
        trademe_land_link.append({
            "listing_id": row['listing_id'],
            "assessment_id": assessment_id,
        })

    try:
        # %% Get land information.
        response = session.get(
            f"https://www.aucklandcouncil.govt.nz/nextapi/property/"
            f"{assessment_id}/rate-assessment",
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
        "assessment_id": assessment_id,
        "land_area": get_int(response_json, 'area'),
        "floor_area": get_int(response_json, 'totalFloorArea'),
        "building_coverage_area": get_int(response_json, 'buildingSiteCoverage'),
        "land_value": get_int(response_json, 'landValue'),
        "improvements_value": get_int(response_json, 'valueOfImprovements'),
        "land_tax": get_float(response_json, 'totalRatesInclCip'),
        "land_usage": response_json.get('landUseDescription', '')[:64],
        "land_tax_break_down": response_json.get('rateBreakdown', {}),
        "nztm2000_x": get_float(response_json, 'x'),
        "nztm2000_y": get_float(response_json, 'y'),
        "title_record": get_int(response_json, 'recordOfTitle'),
    })

records_df = pd.DataFrame(records)
records_df.drop_duplicates(subset=['assessment_id'], inplace=True)
logging.info(f"Queued {records_df.shape[0]} records of land tax, uploading to "
             f"database.")
upsert_dataframe(
    engine,
    records_df,
    ["assessment_id"],
    "properties_land_tax"
)
records.clear()

trademe_land_link_df = pd.DataFrame(trademe_land_link)
logging.info(f"Queued {trademe_land_link_df.shape[0]} records of "
             f"trademe listing ID and Auckland Council rate account key pairs, "
             f"uploading to database.")
upsert_dataframe(
    engine,
    trademe_land_link_df,
    ["listing_id"],
    "properties_trademe_land_tax_assess"
)
trademe_land_link.clear()
