import base64
import gzip
import json
import logging
import os
import random
import sys
import time
import uuid

import pandas as pd
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from requests import Session
from sqlalchemy import create_engine

from postgresql_ops import upsert

# %% Initialize.
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
)
with open("fuel/dart_header.json") as f:
    dart_header = json.load(f)
neon_db = os.environ["NEON_DB"]
engine = create_engine(neon_db, pool_recycle=300)
device_id = str(uuid.uuid4()).upper()
chunk_size = 2000

# %% Login.
session = Session()
response = session.post(
    url="https://gaspy.nz/api/v1/Public/login",
    data=json.dumps({
        "email": os.environ["GASPY_EMAIL"],
        "password": os.environ["GASPY_PASSWORD"],
        "gold_key": None,
        "v": "26",
        "a": "3.30.12",
    }),
    headers=dart_header,
)
if response.status_code != 200:
    raise Exception(f"Status code: {response.status_code}. Reason: {response.reason}")
assert response.json().get('success'), "gaspy.nz username and password don't match."
response_json = response.json()
fuel_types = response_json['data']['fuel_types']
fuel_types = {
    meta['code']: int(key)  # unsafe conversion, aim to raise problems before query.
    for key, meta in fuel_types.items()
}
brands = response_json['data']['brands']
selected_fuel_types = ['91', 'D', '95', '98']
assert all(fuel_type in fuel_types.keys() for fuel_type in selected_fuel_types), \
    "Some of petrol #91, #95, #98 or diesel don't have a fuel type ID."

# %% Define cities.
# Tool: https://www.calcmaps.com/map-radius/
cities = {
    # latitude, longitude, radius (km)
    "Auckland": [-36.93850, 174.80141, 40],
    "Hamilton": [-37.79170, 175.30655, 25],
    "Wellington": [-41.17934, 174.92432, 25],
    "Christchurch": [-43.51038, 172.54940, 20],
}


# %% Search fuel prices.
def decrypt(text_encrypted, csrf_token_):
    aes_key = ("e875c333" + csrf_token_[4:20] + "8f97b3e6").encode("utf-8")
    iv_b64, ct_b64 = text_encrypted.split(":", 1)
    aes_cipher = AES.new(aes_key, AES.MODE_CBC, base64.b64decode(iv_b64))
    aes_decrypted = aes_cipher.decrypt(base64.b64decode(ct_b64))
    aes_decrypted_unpadded = unpad(aes_decrypted, 16)
    if aes_decrypted_unpadded.startswith(b"\x1f\x8b"):
        aes_decrypted_unpadded = gzip.decompress(aes_decrypted_unpadded)
    aes_decrypted_unpadded_dict = json.loads(aes_decrypted_unpadded)
    return aes_decrypted_unpadded_dict


for city_name, (latitude, longitude, radius) in cities.items():
    try:
        response = session.post(
            url="https://gaspy.nz/api/v1/FuelPrice/searchFuelPricesV2",
            data={
                "longitude": longitude,
                "latitude": latitude,
                "distance": radius,
                "order_by": "price",
                "fuel_type_id": 1,
                "ev_plug_types": [],
                "device_type": "I",
                "is_mock_location": False,
                "is_jail_broken": False,
                "is_not_real_device": False,
                "v": "26",
                "a": "3.30.12",
                "udid": "ios_" + device_id,
            }
        )
        response.raise_for_status()
        time.sleep(random.uniform(0.7, 1.3))
        response_json = decrypt(response.text, session.cookies.get("XSRF-TOKEN"))
        prices = response_json.get('data')

        prices = pd.DataFrame(prices)
        prices['date_updated'] = pd.to_datetime(
            prices['date_updated'], format="%Y-%m-%d %H:%M:%S", errors='coerce', utc=True)
        prices.sort_values(inplace=True, by=["date_updated"], ascending=False)
        prices.drop_duplicates(inplace=True, subset=["station_key", "fuel_type_name"])
        prices['datetime_added'] = pd.to_datetime(
            prices['datetime_added'], format="%Y-%m-%d %H:%M:%S", errors='coerce',
            utc=True)

        stations = prices.copy()
        stations.drop_duplicates(inplace=True, subset=["station_key"])
        logging.info(f"Collected {stations.shape[0]} in city \"{city_name}\".")
        stations = stations[['station_key', 'station_name', 'station_street',
                             'station_suburb', 'station_city', 'station_region',
                             'station_postcode', 'station_lat', 'station_lng',
                             'datetime_added']]
        stations.rename(columns=lambda col: col.removeprefix("station_"),
                        inplace=True)
        stations.rename(columns={
            "key": "station_id",
            "lat": "latitude",
            "lng": "longitude",
            "datetime_added": "created_time",
        }, inplace=True)
        for i in range(0, stations.shape[0], chunk_size):
            upsert(
                engine, stations.iloc[i:i+chunk_size],
                ["station_id"], "fuel_stations",
            )

        prices = prices[['station_key', 'fuel_type_name', 'brand_name', 'current_price',
                         'date_updated']]
        prices.rename(columns={
            "station_key": "station_id",
            "fuel_type_name": "fuel_type",
            "brand_name": "brand",
            "current_price": "price",
            "date_updated": "update_time"
        }, inplace=True)
        for i in range(0, prices.shape[0], chunk_size):
            upsert(
                engine, prices.iloc[i:i+chunk_size],
                ["station_id", "fuel_type", "update_time"],
                "fuel_prices"
            )

    except Exception as e:
        logging.warning(f"Fail to parse city \"{city_name}\". {type(e).__name__}: {e}")
        continue
