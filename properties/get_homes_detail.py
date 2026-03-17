import json
import logging
import os
import sys

import pandas as pd
from pandas._libs.tslibs.np_datetime import OutOfBoundsDatetime
from requests import Session
from sqlalchemy import create_engine

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
with open("properties/header_homes.json") as f:
    header = json.load(f)
with open("properties/homes_no_detail.sql") as f:
    sql_no_detail = f.read()

# %% Load listings to work on.
engine = create_engine(os.environ['NEON_DB'], pool_recycle=300)
with engine.connect() as c:
    properties = pd.read_sql(sql_no_detail, c)
logging.info(f"Total number of properties to query details: {properties.shape[0]}")

# %% Main loop.
houses = []
for i, row in properties.iterrows():
    property_id = row['property_id']

    if i % 500 == 0:
        houses_df = pd.DataFrame(houses)
        houses_df = houses_df.convert_dtypes()
        houses_df.drop_duplicates(subset=['property_id'], inplace=True)
        logging.info(f"Queued {houses_df.shape[0]} records of houses "
                     f"information, uploading to database.")
        upsert_dataframe(
            engine,
            houses_df,
            ["property_id"],
            "properties_homes_detail"
        )
        houses.clear()

    now = pd.Timestamp('now', tz='UTC')
    if now - script_start_time > pd.Timedelta(hours=5, minutes=45):
        logging.warning("Execution time reaches 5 hours and 45 minutes, stop.")
        break

    # %% Get sales record.
    try:
        response = session.get(
            f"https://gateway.homes.co.nz/property/{property_id}/timeline",
            headers=header,
        )
        response.raise_for_status()
        events_raw = response.json()['events']
        sales = [
            {
                # No key error protection, because if key misses, no default value can
                # be provided.
                "date": event['date'],
                "price": event['data']['price'],
                "type": event['data']['sale_type'],
            }
            for event in events_raw
            if event.get('key') == 'property_sale'
        ]
        evaluation = [
            {
                # No key error protection, because if key misses, no default value can
                # be provided.
                "date": event['date'],
                "land": event['data']['land_value'],
                "improvement": event['data']['improvement_value'],
            }
            for event in events_raw
            if event.get('key') == 'valuation'
        ]
    except Exception as e:
        logging.warning(
            f"Cannot parse sales and capital values history of property {property_id}. "
            f"{type(e).__name__}: {e}"
        )
        sales = evaluation = []

    try:
        response = session.get(
            "https://api-gateway.homes.co.nz/details",
            params={"property_id": property_id},
            headers=header,
        )
        response.raise_for_status()
        details = response.json()['property']
    except Exception as e:
        logging.warning(
            f"Cannot parse detailed information of property {property_id}. "
            f"{type(e).__name__}: {e}"
        )
        external_wall = roof = estimated_price_date = estimated_rental_date = \
            estimated_rental_lb = estimated_rental_ub = None
    else:
        # G: "Good",
        # A: "Average",
        # F: "Fair",
        # P: "Poor",
        # X: "Mixed"
        building_condition = details.get('building_condition')
        if isinstance(building_condition, str) and len(building_condition) == 2:
            external_wall = building_condition[0]
            roof = building_condition[1]
        else:
            external_wall = roof = None
        try:
            estimated_price_date = details.get('estimated_value_revision_date')
        except (AttributeError, OutOfBoundsDatetime):
            estimated_price_date = None
        try:
            estimated_rental_date = details.get('estimated_rental_revision_date')
        except (AttributeError, OutOfBoundsDatetime):
            estimated_rental_date = None
        try:
            estimated_rental_lb = int(details.get("estimated_rental_lower_value"))
        except (TypeError, ValueError):
            estimated_rental_lb = None
        try:
            estimated_rental_ub = int(details.get("estimated_rental_upper_value"))
        except (TypeError, ValueError):
            estimated_rental_ub = None
    house = {
        "property_id": property_id,
        "sales": sales,
        "capital_values": evaluation,
        "external_wall_condition": external_wall,
        "roof_condition": roof,
        "estimated_price_date": estimated_price_date,
        "estimated_rental_date": estimated_rental_date,
        "estimated_rental_lb": estimated_rental_lb,
        "estimated_rental_ub": estimated_rental_ub,
    }
    houses.append(house)

houses_df = pd.DataFrame(houses)
houses_df = houses_df.convert_dtypes()
houses_df.drop_duplicates(subset=['property_id'], inplace=True)
logging.info(f"Queued {houses_df.shape[0]} records of houses information, uploading to "
             f"database.")
upsert_dataframe(
    engine,
    houses_df,
    ["property_id"],
    "properties_homes_detail"
)
houses.clear()
