# Reference:
# https://data-aucklandcouncil.opendata.arcgis.com/datasets/aucklandcouncil::flood-prone-areas/explore
import logging
import os
import re
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
item_id = "3a0ea32860a64eb48d33994f8627062a"
batch_size = 500

# Find feature server URL.
# Reference: https://developers.arcgis.com/rest/users-groups-and-items/item/
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
        raise Exception("Cannot find FeatureServer. This layer may only be available as "
                        "vector tiles (no query API).")

# %% Ensure URL ends with a layer index (usually /0)
if not re.search(r"/\d+$", layer_url):
    layer_url = layer_url.rstrip("/") + "/0"

# %% Get layer metadata
# response = session.get(layer_url, params={"f": "json"})
# response.raise_for_status()
# layer_meta = response.json()
# col_names = [col["name"] for col in layer_meta.get("fields", [])]
# https://www.arcgis.com/home/item.html?id=0be75c47bc1a4f28b9a7745a3eba5cbf&sublayer=0
col_names_str = ("FPA_ID,CatchmentArea,Depth100y,MaxDepth,MinimumLevel,RainfallExisting,"
                 "RainfallRequired,Vol100yrm3,VolumeM3,Shape__Area")

# %% Count total records
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

# %% Paginate through all records
engine = create_engine(os.environ['NEON_DB'], poolclass=NullPool)
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
    logging.info(f"Page: {page + 1}/{n_pages}; Response time: {end_time - start_time}; "
                 f"Batch size: {batch_size}.")
    features = response.json().get("features", [])
    for feat in features:
        d = feat["properties"]
        d["geometry"] = feat["geometry"]
        records.append(d)

    # %% Post-processing.
    records = pd.DataFrame(records)
    records = records.convert_dtypes()
    records.rename(columns={
        "FPA_ID": "fpa_id",
        "Shape__Area": "area",
        "CatchmentArea": "catchment_area",
        "Depth100y": "pounding_depth_100yr",
        "MaxDepth": "pounding_depth_spill",
        "MinimumLevel": "lowest_ground_elevation",
        # future estimation (considering climate change) = existing estimation * 1.168
        "RainfallExisting": "rainfall_100yr",
        "RainfallRequired": "rainfall_spill",
        # runoff_volume < capacity_volume: cannot fill
        # runoff_volume = capacity_volume: can fill
        # runoff_volume > capacity_volume: not observed in dataset
        "Vol100yrm3": "runoff_volume",
        "VolumeM3": "capacity_volume",
    }, inplace=True)
    records.drop_duplicates(subset=['fpa_id'], inplace=True)

    # %% Export.
    upsert_dataframe(
        engine, records,
        ["fpa_id"],
        "flood_flood_prone_areas",
    )
