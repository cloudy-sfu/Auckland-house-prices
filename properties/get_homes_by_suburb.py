import json
import logging
import os
import sys

import pandas as pd
from requests import Session
from sqlalchemy import create_engine

import polyline
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
with open("properties/suburbs_homes_outdated.sql") as f:
    sql_suburbs = f.read()

# %% Get all suburbs.
engine = create_engine(os.environ['NEON_DB'])
with engine.connect() as c:
    suburbs = pd.read_sql(sql_suburbs, c)
if suburbs.shape[0] == 0:
    logging.info("Properties of all suburbs are updated within 6 days and 20 hours "
                 "ago, nothing to fetch.")
for _, suburb in suburbs.iterrows():
    logging.info(f"Start collecting house information in suburb ID {suburb['suburb_id']}.")

    # %% Encode polylines of suburb boundary.
    polylines = []
    for seg in suburb['coordinates']:
        if len(seg) == 1:
            seg = seg[0]
        encoded_seg = polyline.encode(seg)
        polylines.append(encoded_seg)

    # %% Collect all properties in this suburb.
    page = 1
    cards = []
    try:
        while True:
            response = session.post(
                "https://gateway.homes.co.nz/map/cards",
                data=json.dumps({
                    "limit": 100,
                    "page": page,
                    "polylines": polylines
                }),
                headers=header
            )
            response.raise_for_status()
            response_json = response.json()
            cards += response_json['cards']
            if page * 100 >= response_json['hits']:
                break
            else:
                page += 1
    except Exception as e:
        logging.warning(f"Fail to search properties in suburb ID {suburb['suburb_id']}. "
                        f"{type(e).__name__}: {e}")
        continue

    # %% Parse data of properties.
    houses = []
    for card in cards:
        property_id = card.get("property_id")
        property_details = card.get('property_details')
        if not isinstance(property_details, dict):
            property_details = {}
        address = property_details.get('address')
        if not property_id:
            url = card.get('url')
            logging.warning("Cannot find property ID of:\n"
                            f"Address = {address}\n"
                            f"URL = https://homes.co.nz/address{url}")
            continue
        # A: "Aluminium, including aluminium-coated timber",
        # B: "Brick, including clay and concrete bricks",
        # C: "Concrete, including reinforced block and precast slab",
        # F: "Fibrous cement, including flat or corrugated sheets and sidings",
        # G: "Glass",
        # I: "Iron, including steel and corrugated long-run",
        # M: "All forms of fabric, bitumen, and butyl rubber",
        # P: "Plastic",
        # R: "Roughcast, including stucco and all modern texture coat finishes",
        # S: "Stone",
        # T: "Tiles, including all materials with a tile profile",
        # W: "Wood in all forms, including treated plywood and compressed wood products",
        # X: "Mixture of materials without a predominant material, or a material not included above"
        construction = property_details.get('building_construction')
        if isinstance(construction, str) and len(construction) == 2:
            external_wall_material = construction[0]
            roof_material = construction[1]
        else:
            external_wall_material = roof_material = None
        solar = card.get('solar')
        if isinstance(solar, dict):
            solar_value_str = solar.get('estimate')
            if isinstance(solar_value_str, str):
                solar_value_str = solar_value_str.replace(",", "")
                try:
                    solar_value = int(solar_value_str)
                except ValueError:
                    solar_value = None
            else:
                solar_value = None
        else:
            solar_value = None
        record_of_title = property_details.get('certificate_of_title')
        if record_of_title is None:
            record_of_title = []
        else:
            record_of_title = record_of_title.split(",")
        try:
            latitude = float(card['point']['lat'])
            longitude = float(card['point']['long'])
        except (KeyError, AttributeError, TypeError, ValueError):
            latitude = longitude = None
        try:
            decade_built = int(property_details.get('decade_built'))
        except (TypeError, ValueError):
            decade_built = None
        has_deck = property_details.get('has_deck')
        if has_deck is not None:
            has_deck = bool(has_deck)
        has_laundry = property_details.get('has_laundry_or_workshop')
        if has_laundry is not None:
            has_laundry = bool(has_laundry)
        has_gas = property_details.get('first_gas_enabled')
        if has_gas is not None:
            has_gas = bool(has_gas)
        try:
            bathrooms = int(property_details.get('latest_bathrooms'))
        except (TypeError, ValueError):
            bathrooms = None
        try:
            bedrooms = int(property_details.get('latest_bedrooms'))
        except (TypeError, ValueError):
            bedrooms = None
        try:
            garage_parking = int(property_details.get('garage_parking'))
        except (TypeError, ValueError):
            garage_parking = None
        try:
            car_spaces = int(property_details.get('latest_car_spaces'))
        except (TypeError, ValueError):
            car_spaces = None
        try:
            estimated_price = int(card.get('price'))
        except (TypeError, ValueError):
            estimated_price = None
        house = {
            "property_id": property_id,
            "suburb_id": suburb['suburb_id'],
            "address": address[:128],
            "latitude": latitude,
            "longitude": longitude,
            "decade_built": decade_built,
            "has_deck": has_deck,
            "has_laundry": has_laundry,
            "has_gas": has_gas,
            "bathrooms": bathrooms,
            "bedrooms": bedrooms,
            "garage_parking": garage_parking,
            "car_spaces": car_spaces,
            "record_of_title": record_of_title,
            "ownership_type": property_details.get('ownership_type'),
            "external_wall_material": external_wall_material,
            "roof_material": roof_material,
            # LV: Level
            # EF: Easy to moderate fall
            # ER: Easy to moderate rise
            # SF: Steep fall
            # SR: Steep rise
            "contour": property_details.get('contour'),
            "estimated_price": estimated_price,
            "trademe_listing_id": card.get('tm_ids'),
        }
        houses.append(house)
    houses = pd.DataFrame(houses)
    # NaN still exists, and will raise "integer out of range", so convert to pd.NA.
    houses = houses.convert_dtypes()
    houses.drop_duplicates(subset=['property_id'], inplace=True)
    upsert_dataframe(
        engine,
        houses,
        ["property_id"],
        "properties_homes"
    )
    logging.info(
        f"Finish collecting house information in suburb ID {suburb['suburb_id']}, "
        f"{houses.shape[0]} rows upserted."
    )
