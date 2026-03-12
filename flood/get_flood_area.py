import datetime
import logging
import os
import sys
from math import ceil

import pandas as pd
from requests import Session
from sqlalchemy import create_engine, NullPool

from postgresql_upsert import upsert_dataframe

# %% Initialization.
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
)
session = Session()

# %% Discover FeatureServer URLs from Auckland Council Open Data Hub.
# The VectorTileLayers in the map don't support /query.
# Instead, use the Auckland Council Open Data portal to find the
# corresponding FeatureServer endpoints.
# Ref: https://data-aucklandcouncil.opendata.arcgis.com/

# Map of layer titles to their Open Data Hub item IDs.
# You can find these by searching on data-aucklandcouncil.opendata.arcgis.com
# and looking at the GeoService API link on each dataset page.
FLOOD_LAYERS = {
    # https://data-aucklandcouncil.opendata.arcgis.com/datasets/aucklandcouncil::flood-plains/explore
    "Flood Plains": "690a7135410a437c99e128feaa0c66fb",
    # https://data-aucklandcouncil.opendata.arcgis.com/datasets/aucklandcouncil::flood-prone-areas/explore
    "Flood Prone Areas": "3a0ea32860a64eb48d33994f8627062a",
    # https://data-aucklandcouncil.opendata.arcgis.com/datasets/aucklandcouncil::overland-flow-paths
    "Overland Flow Paths": "6dd41c5b184f4513ae1304b1eb6bf03a",
    # https://data-aucklandcouncil.opendata.arcgis.com/
    "Coastal Inundation": "7a0bd38851b047cbb752f93404a27d53",
}

# %% Resolve all flood layer URLs and query them.
batch_size = 500
engine = create_engine(os.environ['NEON_DB'], poolclass=NullPool)

for layer_name, item_id in FLOOD_LAYERS.items():

    # Find feature server URL.
    # First, check item type and URL directly
    # Ref: https://developers.arcgis.com/rest/users-groups-and-items/item/
    response = session.get(
        f"https://www.arcgis.com/sharing/rest/content/items/{item_id}",
        params={"f": "json"},
    )
    response.raise_for_status()
    item_info = response.json()
    item_url = item_info.get("url", "")
    if "FeatureServer" in item_url:
        layer_url = item_url
    else:
        # If it's a VectorTileLayer, try to find a related FeatureServer
        # by searching the same org for a FeatureLayer with the same name.
        title = item_info.get("title", "")
        owner = item_info.get("owner", "")
        org_id = item_info.get("orgId", "")

        # Search Auckland Council's ArcGIS org for a FeatureLayer with matching title
        response = session.get(
            "https://www.arcgis.com/sharing/rest/search",
            params={
                "q": f'title:"{title}" orgid:{org_id} type:"Feature Service"',
                "f": "json",
                "num": 5,
            },
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        for r in results:
            if "FeatureServer" in r.get("url", ""):
                layer_url = r["url"]
                break
        else:
            logging.warning(
                f"Cannot find FeatureServer of layer \"{layer_name}\". "
                "This layer may only be available as vector tiles (no query API)."
            )
            continue

    # Ensure URL ends with a layer index (usually /0)
    if not layer_url.rstrip("/").split("/")[-1].isdigit():
        layer_url = layer_url.rstrip("/") + "/0"

    # Count total records (no WHERE filter needed — this is Auckland-specific data)
    response = session.get(
        layer_url + "/query",
        params={
            "where": "1=1",
            "returnCountOnly": True,
            "f": "json",
        },
    )
    response.raise_for_status()
    n_records = response.json()["count"]
    n_pages = ceil(n_records / batch_size)

    # Get layer metadata
    # response = session.get(layer_url, params={"f": "json"})
    # response.raise_for_status()
    # layer_meta = response.json()
    # col_names = [col["name"] for col in layer_meta.get("fields", [])]

    col_names_str = "sdeObjectID,YEAR_PRODUCED,Published_Date,Shape__Area"

    # Paginate through all records
    for page in range(n_pages):
        records = []
        start_time = pd.Timestamp('now', tz='UTC')
        response = session.get(
            layer_url + "/query",
            params={
                "where": "1=1",
                "outFields": col_names_str,
                "returnGeometry": True,
                "outSR": 4326,  # WGS84
                "f": "geojson",
                "resultOffset": page * batch_size,
                "resultRecordCount": batch_size,
            },
            timeout=120,
        )
        response.raise_for_status()
        end_time = pd.Timestamp('now', tz='UTC')
        logging.info(f"Layer: {layer_name}; Page: {page + 1}/{n_pages}; Response time: "
                     f"{end_time - start_time}; Batch size: {batch_size}.")
        features = response.json().get("features", [])
        for feat in features:
            d = feat["properties"]
            d["geometry"] = feat["geometry"]
            records.append(d)

        # %% Post-processing.
        records = pd.DataFrame(records)
        records = records.convert_dtypes()
        records['flood_type'] = layer_name
        records['Published_Date'] = pd.to_datetime(records['Published_Date'], unit='ms')
        records.rename(columns={
            "SDEObjectID": "sde_object_id",
            "YEAR_PRODUCED": "year_produced",
            "Published_Date": "published_date",
            "Shape__Area": "area",
        }, inplace=True)

        # %% Export.
        upsert_dataframe(
            engine, records,
            ["sde_object_id"],
            "flood_area",
        )
