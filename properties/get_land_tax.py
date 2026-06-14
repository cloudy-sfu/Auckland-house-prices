import json
import logging
import os
import sys

import pandas as pd
from requests import Session
from sqlalchemy import create_engine

from postgresql_ops import upsert, insert_skip_conflict

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
engine = create_engine(os.environ['NEON_DB'], pool_recycle=300)

# %% Get address to fetch.
with open("properties/homes_no_land_tax_record.sql") as f:
    sql_houses = f.read()
with engine.connect() as c:
    houses = pd.read_sql(sql_houses, c)

# %% Main loop.
homes_land_link = []
records = []
is_github_actions = os.getenv("GITHUB_ACTIONS") == "true"
logging.info(f"Total number of properties to query land tax: {houses.shape[0]}")
for i, row in houses.iterrows():
    address = row['address']

    # %% Check conditions to quit loop.
    if i % 500 == 0:
        records_df = pd.DataFrame(records)
        records_df = records_df.convert_dtypes()
        records_df.drop_duplicates(subset=['assessment_id'], inplace=True)
        logging.info(f"Queued {records_df.shape[0]} records of land tax, uploading to "
                     f"database.")
        upsert(
            engine,
            records_df,
            ["assessment_id"],
            "properties_land_tax"
        )
        records.clear()

        homes_land_link_df = pd.DataFrame(homes_land_link)
        homes_land_link_df = homes_land_link_df.convert_dtypes()
        homes_land_link_df.drop_duplicates(inplace=True)
        logging.info(f"Queued {homes_land_link_df.shape[0]} records of "
                     f"homes.co.nz property ID and land tax assessment ID pairs, "
                     f"uploading to database.")
        insert_skip_conflict(
            engine,
            homes_land_link_df,
            ["property_id"],
            "properties_homes_land_tax_link"
        )
        homes_land_link.clear()

    if (is_github_actions and pd.Timestamp('now', tz='UTC') - script_start_time
            > pd.Timedelta(hours=5, minutes=45)):
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
        assessment = response.json()
        assessment_id = assessment['items'][0]['id']
    except Exception as e:
        logging.warning(f"Cannot find rate account key of \"{address}\" in "
                        f"Auckland council. {type(e).__name__}: {e}")
        homes_land_link.append({
            "property_id": row['property_id'],
            "assessment_id": None,
        })
        continue
    else:
        homes_land_link.append({
            "property_id": row['property_id'],
            "assessment_id": assessment_id,
        })

    try:
        # %% Get land information.
        response = session.get(
            f"https://experience.aucklandcouncil.govt.nz/nextapi/property/"
            f"{assessment_id}/rate-assessment",
            headers=header,
        )
        response.raise_for_status()
        assessment = response.json()
    except Exception as e:
        logging.warning(f"Cannot find land information of \"{address}\" in "
                        f"Auckland council. {type(e).__name__}: {e}")
        continue

    # %% Parse land information.
    record_of_title = assessment.get('recordOfTitle')
    if record_of_title is None:
        record_of_title = []
    else:
        record_of_title = record_of_title.split(",")
    try:
        land_area = int(assessment.get('area'))
    except (TypeError, ValueError):
        land_area = None
    try:
        floor_area = int(assessment.get('totalFloorArea'))
    except (TypeError, ValueError):
        floor_area = None
    try:
        building_coverage_area = int(assessment.get('buildingSiteCoverage'))
    except (TypeError, ValueError):
        building_coverage_area = None
    try:
        land_value = int(assessment.get('landValue'))
    except (TypeError, ValueError):
        land_value = None
    try:
        improvements_value = int(assessment.get('valueOfImprovements'))
    except (TypeError, ValueError):
        improvements_value = None
    try:
        land_tax = float(assessment.get('totalRatesInclCip'))
    except (TypeError, ValueError):
        land_tax = None
    try:
        nztm2000_x = float(assessment.get('x'))
    except (TypeError, ValueError):
        nztm2000_x = None
    try:
        nztm2000_y = float(assessment.get('y'))
    except (TypeError, ValueError):
        nztm2000_y = None
    records.append({
        "assessment_id": assessment_id,
        "land_area": land_area,
        "floor_area": floor_area,
        "building_coverage_area": building_coverage_area,
        "land_value": land_value,
        "improvements_value": improvements_value,
        "land_tax": land_tax,
        "land_usage": assessment.get('landUseDescription', '')[:64],
        "land_tax_break_down": assessment.get('rateBreakdown', []),
        "nztm2000_x": nztm2000_x,
        "nztm2000_y": nztm2000_y,
        "record_of_title": record_of_title,
        "street_number": assessment.get('streetNumber'),
        "street_name": assessment.get('streetName'),
        "suburb_name": assessment.get('suburbName'),
    })

records_df = pd.DataFrame(records)
records_df = records_df.convert_dtypes()
records_df.drop_duplicates(subset=['assessment_id'], inplace=True)
logging.info(f"Queued {records_df.shape[0]} records of land tax, uploading to "
             f"database.")
upsert(
    engine,
    records_df,
    ["assessment_id"],
    "properties_land_tax"
)
records.clear()

homes_land_link_df = pd.DataFrame(homes_land_link)
homes_land_link_df = homes_land_link_df.convert_dtypes()
homes_land_link_df.drop_duplicates(inplace=True)
logging.info(f"Queued {homes_land_link_df.shape[0]} records of "
             f"homes.co.nz property ID and land tax assessment ID pairs, "
             f"uploading to database.")
insert_skip_conflict(
    engine,
    homes_land_link_df,
    ["property_id"],
    "properties_homes_land_tax_link"
)
homes_land_link.clear()
