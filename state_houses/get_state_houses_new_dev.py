import json
import logging
import os
import re
import sys
import time

import pandas as pd
from bs4 import BeautifulSoup
from requests import Session
from sqlalchemy import create_engine

from postgresql_upsert import upsert_dataframe

# %% Setup logger.
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
)

# %% Initialization.
session = Session()
with open("state_houses/header_2.json") as f:
    header = json.load(f)


def regex_extract(key, context):
    match_1 = re.search(rf"{key}:\s*(.*)\s*\n", context)
    if match_1:
        item = match_1.group(1)
        if item == 'TBC':
            item = pd.NA
    else:
        item = pd.NA
    return item


def regex_integer(text):
    if pd.isna(text):
        return pd.NA
    match_1 = re.search(r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?", text)
    if match_1:
        text_1 = match_1.group()
        text_1 = text_1.replace(",", "")
        try:
            int_1 = int(text_1)
        except (TypeError, ValueError):
            int_1 = pd.NA
    else:
        int_1 = pd.NA
    return int_1

# %% Get local bound list.
response = session.get("https://engage.kaingaora.govt.nz/auckland", headers=header)
response.raise_for_status()
response_text = BeautifulSoup(response.text, 'html.parser')
local_board_cards = response_text.find_all("article", {"data-project-location": "[\"Auckland\"]"})
state_houses = []
month_map = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12
}

for local_board_card in local_board_cards:
    local_board_link = local_board_card.find('a').get('href')
    match_3 = re.search(r"/([^/]+?)(?:-local-board)?/?$", local_board_link)
    if match_3:
        local_board = match_3.group(1)

        # %% Get JSON structure from local board's map.
        response = session.get(local_board_link, headers=header)
        if response.status_code != 200:
            logging.warning(f"Cannot fetch data from local board {local_board}.")
        response_text = BeautifulSoup(response.text, "html.parser")
        js_scripts = response_text.find("main").find_all("script")
        for js_script in js_scripts:
            js_script_text = js_script.text
            match = re.search(r'blockSets:\s*(\{[\s\S]*?})\s*,\s*blockUrls:', js_script_text,
                              flags=re.S)
            if match is not None:
                break
        else:
            logging.warning(f"Cannot parse data in developments map of local board {local_board}.")
            continue
        props = match.group(1)
        props = re.sub(r"\n+", "", props)
        props_dict = json.loads(props)
        time.sleep(0.7)

        # %% Parse state houses from JSON structure.
        categories_mapping = {}
        for category in props_dict.get('categories', []):
            categories_mapping[category['categoryID']] = category['name']

        layer_mapping = {}
        for layer in props_dict.get('layers', []):
            if layer.get('layerType') == 'geojson' and layer.get('file'):
                label = layer.get('layerLabel', '').removesuffix('boundary').strip()
                layer_mapping[label] = layer['file']

        for marker in props_dict.get('infoMarkers', []):
            info_marker_id = marker.get('infoMarkerID')
            if info_marker_id is None:
                continue

            address = marker.get('infoMarkerTitle', '').strip()
            if (address == "N/A") or (address == "n/a") or ("Example Street" in address):
                continue

            geom_obj = pd.NA
            if address in layer_mapping:
                try:
                    response_1 = session.get(layer_mapping[address], timeout=5)
                    response_1_json = response_1.json()
                    geom_obj = response_1_json['features'][0]['geometry']
                except Exception as e:
                    logging.warning(
                        f"Fail to parse geometry area. Object ID: {info_marker_id}. "
                        f"Boundary geometry URL: {layer_mapping[address]}\n"
                        f"{e}")

            # Clean HTML from the description
            raw_desc = marker.get('infoMarkerDescription') or ""
            if raw_desc:
                soup = BeautifulSoup(raw_desc, 'html.parser')
                # Extract text, replacing block-level tags and <br> with newlines
                description = soup.get_text(separator="\n")
                updated_time = regex_extract("Update", description)
                if not pd.isna(updated_time):
                    match_2 = re.search(
                        r"(January|February|March|April|May|June|July|August|"
                        r"September|October|November|December)\s.*(\d{4})$",
                        updated_time
                    )
                    if match_2:
                        updated_month = month_map[match_2.group(1)]
                        updated_year = int(match_2.group(2))
                    else:
                        updated_month = updated_year = pd.NA
                else:
                    updated_month = updated_year = pd.NA
                land_area = regex_integer(regex_extract("Land area", description))
                build_type = regex_extract("Build Type", description)
                number_of_homes = regex_extract("Number of homes", description)
                parking_space = regex_extract("Parking spaces", description)
                progress = regex_extract("Current status", description)
                planned_completion = regex_extract("Planned completion", description)
                if not pd.isna(planned_completion):
                    match_2 = re.match(r"(^.*\d{4}$)", planned_completion)
                    if match_2:
                        planned_completion = match_2.group(1)
                    else:
                        planned_completion = pd.NA
                else:
                    planned_completion = pd.NA
            else:
                updated_month = updated_year = land_area = build_type = \
                    number_of_homes = parking_space = progress = planned_completion = \
                    pd.NA

            # Parse the embedded GeoJSON string to a Shapely Geometry (Point/Polygon)
            geo_str = marker.get('infoMarkerGeo')
            if geo_str and pd.isna(geom_obj):
                try:
                    geo_json = json.loads(geo_str)
                    # The 'geometry' key within the Feature contains the coordinates & type
                    geom_obj = geo_json['geometry']
                except (json.JSONDecodeError, KeyError) as e:
                    logging.warning(f"Failed to parse geometry for '{address}' - {e}")

            # Match Type from Categories
            cat_id = marker.get('infoMarkerCategoryID')
            item_type = categories_mapping.get(cat_id, "").strip()

            state_houses.append({
                "info_marker_id": info_marker_id,
                'local_board': local_board,
                'address': address,
                "updated_year": updated_year,
                "updated_month": updated_month,
                "land_area": land_area,
                "build_type": build_type,
                "number_of_homes": number_of_homes,
                "parking_space": parking_space,
                "progress": progress,
                "planned_completion": planned_completion,
                'location': geom_obj,
                'step': item_type,
            })
    else:
        continue
state_houses = pd.DataFrame(state_houses)
state_houses = state_houses.convert_dtypes()

# %%
engine = create_engine(os.environ['NEON_DB'])
try:
    upsert_dataframe(
        engine,
        state_houses,
        ['info_marker_id'],
        "state_houses_new_dev"
    )
except Exception as e:
    logging.info(f"Number of records: {state_houses.shape[0]}\n"
                 f"Max length of local_board: {state_houses['local_board'].str.len().max()}\n"
                 f"Max length of address: {state_houses['address'].str.len().max()}\n"
                 f"Max length of build type: {state_houses['build_type'].str.len().max()}\n"
                 f"Max length of number_of_homes: {state_houses['number_of_homes'].str.len().max()}\n"
                 f"Max length of parking_space: {state_houses['parking_space'].str.len().max()}\n"
                 f"Max length of planned_completion: {state_houses['planned_completion'].str.len().max()}\n"
                 f"Max length of progress: {state_houses['progress'].str.len().max()}\n"
                 f"Max length of step: {state_houses['step'].str.len().max()}")
    raise e
