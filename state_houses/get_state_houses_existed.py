import logging
import os
import sys
from math import ceil

import pandas as pd
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
session = Session()

# %% Get layer URL.
app_id = "8501fe601f7648718d0e3a2f3f1ed216"
response = session.get(
    f"https://linz.maps.arcgis.com/sharing/rest/content/items/{app_id}/data",
    params={"f": "json"}
)
response.raise_for_status()
config = response.json()
map_id = config["map"]["itemId"]

response = session.get(
    f"https://linz.maps.arcgis.com/sharing/rest/content/items/{map_id}/data",
    params={"f": "json"}
)
response.raise_for_status()
map_ = response.json()

layer_url = None
layers = map_.get('operationalLayers')
if not layers:
    raise Exception("This map don't have any layer.")
for layer in layers:
    if layer['id'] == 'CRoSL_Layer_N_675':
        layer_url = layer['url']
        break
else:
    raise Exception("Cannot find layer 'CRoSL_Layer_N_675'.")

# %% Get metadata of the layer.
response = session.get(layer_url, params={"f": "json"})
response.raise_for_status()
layer_1 = response.json()
batch_size = layer_1["maxRecordCount"]
col_names = [col['name'] for col in layer_1['fields']]
col_names_str = ",".join(col_names)
response = session.get(layer_url + "/query", params={
    "where": "Region = 'Auckland'",
    "returnCountOnly": True,
    "f": "json",
})
n_records = response.json()["count"]
n_pages = ceil(n_records / batch_size)
logging.info(f"Total number of pages: {n_pages}.")

# %% Request objects.
def flatten_record(record_):
    d = record_['properties']
    d['geometry'] = record_['geometry']
    return d


records = []
for page in range(n_pages):
    logging.info(f"Starting to parse page {page+1}/{n_pages}.")
    response = session.get(layer_url + "/query", params={
        "where": "Region = 'Auckland'",
        "outFields": col_names_str,
        "returnGeometry": True,
        "outSR": 4326,  # WGS84 lon/lat coordinates
        "f": "geojson",
        "resultOffset": page * batch_size,
        "resultRecordCount": batch_size,
    })
    response.raise_for_status()
    response_json = response.json()
    records_page_raw = response_json.get("features", [])
    records_page = list(map(flatten_record, records_page_raw))
    records += records_page

# %% Post-processing.
records = pd.DataFrame(records)
records = records.convert_dtypes()
records = records[
    ['Parcel_ID', 'Title_No', 'Managed_By', 'Shape__Area', 'Date_Updated', 'geometry']]
records['Date_Updated'] = pd.to_datetime(records['Date_Updated'], format='%Y%m%d')
records.rename(
    columns={
        'Parcel_ID': 'parcel_id',
        'Title_No': 'record_of_title',
        'Managed_By': 'owner',
        'Shape__Area': 'area',
        'Date_Updated': 'updated_date'
    },
    inplace=True
)

# %% Export.
engine = create_engine(os.environ['NEON_DB'])
upsert_dataframe(
    engine,
    records,
    ['parcel_id'],
    'state_houses',
)
