import os

import pandas as pd
from requests import Session
from sqlalchemy import create_engine

from postgresql_upsert import upsert_dataframe

session = Session()

response = session.get(
    "https://production.infometrics.co.nz/api/dimensions/small_area_map/",
    params={
        "app_type": "REP",
        "area_id": "auckland",
        "area_type": "SA2_26"
    },
)
response.raise_for_status()
suburbs = response.json()['features']['features']

suburbs = [
    {
        "suburb_id": int(suburb['properties']['area_code']),
        "name": suburb['properties']['name'].strip(),
        "geometry": suburb['geometry'],
    }
    for suburb in suburbs
]
suburbs = pd.DataFrame(suburbs)

engine = create_engine(os.environ['NEON_DB'], pool_recycle=300)
upsert_dataframe(engine, suburbs, ["suburb_id"], "suburbs")
