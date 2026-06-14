# Reference:
# https://data-aucklandcouncil.opendata.arcgis.com/datasets/aucklandcouncil::coastal-inundation-100-yr-return/explore
import logging
import os
import re
import sys
from math import ceil

import pandas as pd
from requests import Session
from sqlalchemy import create_engine

from postgresql_ops import upsert

# %% Initialization.
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
)
session = Session()
item_id = "2b1653374a8c4750960b4420791ec2c3"
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
col_names_str = "OBJECTID"

# %% Count total records
response = session.get(
    layer_url + "/query",
    params={
        "where": "VALIDATIONSTATE>=2",
        "returnCountOnly": True,
        "f": "json",
    },
)
response.raise_for_status()
n_records = response.json()["count"]
n_pages = ceil(n_records / batch_size)

# %% Paginate through all records
engine = create_engine(os.environ['NEON_DB'], pool_recycle=300)
for page in range(n_pages):
    records = []
    start_time = pd.Timestamp('now', tz='UTC')
    response = session.get(
        layer_url + "/query",
        params={
            "where": "VALIDATIONSTATE>=2",
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
        "OBJECTID": "object_id",
    }, inplace=True)
    records.drop_duplicates(subset=['object_id'], inplace=True)

    # %% Export.
    upsert(
        engine, records,
        ["object_id"],
        "flood_coastal_inundation",
    )
