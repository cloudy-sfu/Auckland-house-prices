import json
import logging
import os
import sys

import pandas as pd
from requests import Session
from sqlalchemy import create_engine, NullPool
from tqdm import tqdm

from dict_ops import get_float, get_int, get_bool, get_str
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
with open("properties/trademe_missing_homes.sql") as f:
    sql_listings = f.read()

# %% Load listings to work on.
engine = create_engine(os.environ['NEON_DB'], poolclass=NullPool)
with engine.connect() as c:
    listings = pd.read_sql(sql_listings, c)

# %% Main loop.
homes_trademe_link = []
houses = []
for i, row in tqdm(listings.iterrows(), total=listings.shape[0]):
    listing_id = row['listing_id']
    address = row['address']

    if i % 500 == 0:
        houses_df = pd.DataFrame(houses)
        houses_df.drop_duplicates(subset=['property_id'], inplace=True)
        logging.info(f"Queued {houses_df.shape[0]} records of houses "
                     f"information, uploading to database.")
        upsert_dataframe(
            engine,
            houses_df,
            ["property_id"],
            "properties_homes"
        )
        houses.clear()

        homes_trademe_link_df = pd.DataFrame(homes_trademe_link)
        homes_trademe_link_df.drop_duplicates(subset=["homes_property_id"], inplace=True)
        logging.info(f"Queued {homes_trademe_link_df.shape[0]} records of trademe "
                     f"listing ID and homes property ID pairs, uploading to database.")
        upsert_dataframe(
            engine,
            homes_trademe_link_df,
            ["assessment_id"],
            "properties_trademe_homes_id"
        )
        homes_trademe_link.clear()

    now = pd.Timestamp('now', tz='UTC')
    if now - script_start_time > pd.Timedelta(hours=5, minutes=45):
        logging.warning("Execution time reaches 5 hours and 45 minutes, stop.")
        break

    # %% Search address.
    try:
        for _ in range(3):
            response = session.get(
                "https://gateway.homes.co.nz/address/search",
                params={"Address": address},
                headers=header
            )
            response.raise_for_status()
            result = response.json()["Results"][0]
            property_id = result['PropertyID']
            if property_id:
                break
            else:
                address = result['Title']
    except Exception as e:
        logging.warning(f"Address \"{address}\" (trademe listing ID {listing_id}) not "
                        f"found. {type(e).__name__}: {e}")
        homes_trademe_link.append({
            "listing_id": listing_id,
            "homes_property_id": pd.NA
        })
        continue

    if property_id:
        homes_trademe_link.append({
            "listing_id": listing_id,
            "homes_property_id": property_id
        })
    else:
        homes_trademe_link.append({
            "listing_id": listing_id,
            "homes_property_id": pd.NA
        })
        continue

    # %% Get house properties.
    try:
        response = session.get(
            "https://gateway.homes.co.nz/properties",
            params={"property_ids": property_id}
        )
        response.raise_for_status()
        house_raw = response.json()['cards'][0]
        latitude = get_float(house_raw, 'point', 'lat')
        longitude = get_float(house_raw, 'point', 'long')
        homes_estimated_price = get_int(house_raw, 'price')
        title_record = get_int(house_raw, 'property_details', 'certificate_of_title')
        garage_parking = get_int(house_raw, 'property_details', 'garage_parking')
        has_deck = get_bool(house_raw, 'property_details', 'has_deck')
        has_laundry = get_bool(house_raw, 'property_details', 'has_laundry_or_workshop')
        has_gas = get_bool(house_raw, 'property_details', 'first_gas_enabled')
        decade_built = get_int(house_raw, 'property_details', 'decade_built')
        bathrooms = get_int(house_raw, 'property_details', 'latest_bathrooms')
        bedrooms = get_int(house_raw, 'property_details', 'latest_bedrooms')
        car_spaces = get_int(house_raw, 'property_details', 'latest_car_spaces')
        ownership_type = get_str(house_raw, 'property_details', 'ownership_type')

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
        construction = get_str(house_raw, 'property_details', 'building_construction')
        if len(construction) == 2:
            external_wall = construction[0]
            roof = construction[1]
        else:
            external_wall = roof = pd.NA
        solar_value = get_str(house_raw, 'solar', 'estimate')
        try:
            solar_value = int(solar_value.replace(",", ""))
        except (TypeError, ValueError, AttributeError):
            solar_value = pd.NA

        # LV: Level
        # EF: Easy to moderate fall
        # ER: Easy to moderate rise
        # SF: Steep fall
        # SR: Steep rise
        contour = get_str(house_raw, 'property_details', 'contour')

    except Exception as e:
        logging.warning(f"Cannot parse basic information of the house at \"{address}\", "
                        f"property ID \"{property_id}\". {type(e).__name__}: {e}")
        house = {
            "property_id": property_id,
            "latitude": pd.NA,
            "longitude": pd.NA,
            "homes_estimated_price": pd.NA,
            "title_record": pd.NA,
            "garage_parking": pd.NA,
            "has_deck": pd.NA,
            "has_laundry": pd.NA,
            "has_gas": pd.NA,
            "decade_built": pd.NA,
            "bathrooms": pd.NA,
            "bedrooms": pd.NA,
            "car_spaces": pd.NA,
            "ownership_type": pd.NA,
            "sales": pd.NA,
            "evaluation": pd.NA,
            "external_wall_material": pd.NA,
            "roof_material": pd.NA,
            "solar_value": pd.NA,
            "contour": pd.NA,
        }
    else:
        house = {
            "property_id": property_id,
            "latitude": latitude,
            "longitude": longitude,
            "homes_estimated_price": homes_estimated_price,
            "title_record": title_record,
            "garage_parking": garage_parking,
            "has_deck": has_deck,
            "has_laundry": has_laundry,
            "has_gas": has_gas,
            "decade_built": decade_built,
            "bathrooms": bathrooms,
            "bedrooms": bedrooms,
            "car_spaces": car_spaces,
            "ownership_type": ownership_type,
            "external_wall_material": external_wall,
            "roof_material": roof,
            "solar_value": solar_value,
            "contour": contour,
        }

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
                "sale_date": pd.to_datetime(event['date']),
                "price": get_int(event, 'data', 'price'),
                "sale_type": get_str(event, 'data', 'sale_type'),
            }
            for event in events_raw
            if event.get('key') == 'property_sale'
        ]
        evaluation = [
            {
                # No key error protection, because if key misses, no default value can
                # be provided.
                "evaluated_date": pd.to_datetime(event['date']),
                "land_value": get_int(event, 'data', 'land_value'),
                "improvement_value": get_int(event, 'data', 'improvement_value'),
            }
            for event in events_raw
            if event.get('key') == 'valuation'
        ]
    except Exception as e:
        logging.warning(
            f"Cannot parse sales and capital value history of the house at \"{address}\", "
            f"property ID \"{property_id}\". {type(e).__name__}: {e}")
        house['sales'] = house['evaluation'] = pd.NA
    else:
        house['sales'] = sales
        house['evaluation'] = evaluation

    try:
        response = session.get(
            "https://api-gateway.homes.co.nz/details",
            params={"property_id": property_id},
            headers=header,
        )
        response.raise_for_status()
        details = response.json()['property']

        # G: "Good",
        # A: "Average",
        # F: "Fair",
        # P: "Poor",
        # X: "Mixed"
        building_condition = get_str(details, 'building_condition')
        if len(building_condition) == 2:
            external_wall = building_condition[0]
            roof = building_condition[1]
        else:
            external_wall = roof = pd.NA

        homes_estimated_price_updated_date = details.get(
            "estimated_value_revision_date", pd.NA)
        estimated_rental_lower_value = details.get("estimated_rental_lower_value", pd.NA)
        estimated_rental_upper_value = details.get("estimated_rental_upper_value", pd.NA)
        estimated_rental_updated_time = details.get("estimated_rental_revision_date", pd.NA)
    except Exception as e:
        logging.warning(
            f"Cannot parse detailed information of the house at \"{address}\", "
            f"property ID \"{property_id}\". {type(e).__name__}: {e}")
        house['external_wall_condition'] = house['roof_condition'] = \
            house['homes_estimated_price_updated_date'] = \
            house['homes_estimated_rental_lb'] = \
            house['homes_estimated_rental_ub'] = \
            house['homes_estimated_rental_updated_date'] = pd.NA
    else:
        house['external_wall_condition'] = external_wall
        house['roof_condition'] = roof
        house['homes_estimated_price_updated_date'] = homes_estimated_price_updated_date
        house['homes_estimated_rental_lb'] = estimated_rental_lower_value
        house['homes_estimated_rental_ub'] = estimated_rental_upper_value
        house['homes_estimated_rental_updated_date'] = estimated_rental_updated_time

    houses.append(house)

houses_df = pd.DataFrame(houses)
houses_df.drop_duplicates(subset=['property_id'], inplace=True)
logging.info(f"Queued {houses_df.shape[0]} records of houses "
             f"information, uploading to database.")
upsert_dataframe(
    engine,
    houses_df,
    ["property_id"],
    "properties_homes"
)
houses.clear()

homes_trademe_link_df = pd.DataFrame(homes_trademe_link)
homes_trademe_link_df.drop_duplicates(subset=["homes_property_id"], inplace=True)
logging.info(f"Queued {homes_trademe_link_df.shape[0]} records of trademe "
             f"listing ID and homes property ID pairs, uploading to database.")
upsert_dataframe(
    engine,
    homes_trademe_link_df,
    ["assessment_id"],
    "properties_trademe_homes_id"
)
homes_trademe_link.clear()
