import json
import logging
import os
import random
import sys
import time

import pandas as pd
from DrissionPage import ChromiumPage
from sqlalchemy import create_engine

from cloudflare_bypass import CloudflareBypass
from postgresql_upsert import upsert_dataframe
from telegram_logger import TelegramHandler

# %% Setup logger.
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(pathname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        TelegramHandler(os.environ.get("TG_BOT_TOKEN"), os.environ.get("TG_CHAT_ID"))
    ],
)

# %% Load schools.
with open("schools/get_schools_to_request_zone.sql") as f:
    sql_school_ids = f.read()
engine = create_engine(os.environ["NEON_DB"], pool_recycle=300)
with engine.connect() as c:
    school_ids = pd.read_sql(sql_school_ids, c)
school_ids = school_ids['school_number'].tolist()

# %% Load school zone.
base_url = "https://www.educationcounts.govt.nz/js-content/school-enrolment-zone-geo-data"
referer_base_url = "https://www.educationcounts.govt.nz/find-school/school/profile"
with open("schools/header_school_zone.json") as f:
    header = json.load(f)
chrome = ChromiumPage()


class BatchList:
    def __init__(self, table_name, unique_key_columns):
        self._items = []  # Internal list
        self.table_name = table_name
        self.unique_key_columns = unique_key_columns

    def append(self, obj):
        self._items.append(obj)
        if len(self._items) >= 500:
            self.flush()

    def flush(self):
        df = pd.DataFrame(self._items).convert_dtypes()
        df.drop_duplicates(subset=self.unique_key_columns, keep='first', inplace=True)
        upsert_dataframe(
            engine,
            df,
            self.unique_key_columns,
            self.table_name
        )
        self._items.clear()
        logging.info(f"Upserted {df.shape[0]} records to {self.table_name}.")


zones = BatchList("schools_zones", ["school_number", "poly_id"])
for school_id in school_ids:
    header_ins = header.copy()
    header_ins['referer'] = f"{referer_base_url}?school={school_id}"
    try:
        url = f"{base_url}?school={school_id}"
        chrome.get(url)
        cf_bypass = CloudflareBypass(chrome)
        cf_bypass.bypass()
        school_zones = chrome.json.get('schoolZones', [])
        for zone in school_zones:
            try:
                poly_id = zone['properties']['PolyID']
                assert poly_id
            except (KeyError, AttributeError, AssertionError):
                logging.warning(f"School zone of school ID {school_id} misses \"PolyID\".")
                continue
            zones.append({
                "school_number": school_id,
                "poly_id": poly_id,
                "geometry": zone.get("geometry", {})
            })
    except Exception as e:
        logging.warning(f"Cannot fetch school zone of school ID {school_id}. "
                        f"{type(e).__name__}: {e}")
    time.sleep(random.uniform(0.3, 0.7))

zones.flush()
chrome.quit()
logging.info("Execution successful.")
