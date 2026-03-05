import json
import logging
import os
import sys

import pandas as pd
from requests import Session
from sqlalchemy import create_engine

import polyline
from dict_ops import *
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
        address = get_str(card, 'property_details', 'address')
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
        construction = get_str(card, 'property_details', 'building_construction')
        if construction and len(construction) == 2:
            external_wall_material = construction[0]
            roof_material = construction[1]
        else:
            external_wall_material = roof_material = None
        solar_value = get_str(card, 'solar', 'estimate')
        try:
            solar_value = int(solar_value.replace(",", ""))
        except:
            solar_value = None

        house = {
            "property_id": property_id,
            "suburb_id": suburb['suburb_id'],
            "address": address[:128],
            "latitude": get_float(card, 'point', 'lat'),
            "longitude": get_float(card, 'point', 'long'),
            "decade_built": get_int(card, 'property_details', 'decade_built'),
            "has_deck": get_bool(card, 'property_details', 'has_deck'),
            "has_laundry": get_bool(card, 'property_details', 'has_laundry_or_workshop'),
            "has_gas": get_bool(card, 'property_details', 'first_gas_enabled'),
            "bathrooms": get_int(card, 'property_details', 'latest_bathrooms'),
            "bedrooms": get_int(card, 'property_details', 'latest_bedrooms'),
            "garage_parking": get_int(card, 'property_details', 'garage_parking'),
            "car_spaces": get_int(card, 'property_details', 'latest_car_spaces'),
            "record_of_title": get_str(card, 'property_details', 'certificate_of_title'),
            "ownership_type": get_str(card, 'property_details', 'ownership_type'),
            "external_wall_material": external_wall_material,
            "roof_material": roof_material,
            # LV: Level
            # EF: Easy to moderate fall
            # ER: Easy to moderate rise
            # SF: Steep fall
            # SR: Steep rise
            "contour": get_str(card, 'property_details', 'contour'),
            "estimated_price": get_int(card, 'price'),
            "trademe_listing_id": card.get('tm_ids'),
        }
        houses.append(house)
    houses = pd.DataFrame(houses)
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
