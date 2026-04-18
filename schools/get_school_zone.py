import json
import logging
import os
import sys

import pandas as pd
from DrissionPage import ChromiumPage, ChromiumOptions
from sqlalchemy import create_engine

from cloudflare_bypass import CloudflareBypass
from postgresql_upsert import upsert_dataframe

# %% Setup logger.
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(pathname)s %(message)s",
    stream=sys.stdout,
)

# %% Load schools.
engine = create_engine(os.environ["NEON_DB"], pool_recycle=300)
with engine.connect() as c:
    school_ids = pd.read_sql(
        "select school_number from schools where enrollment_scheme is true", c)
school_ids = school_ids['school_number'].tolist()

# %% Load school zone.
base_url = "https://www.educationcounts.govt.nz/js-content/school-enrolment-zone-geo-data"
referer_base_url = "https://www.educationcounts.govt.nz/find-school/school/profile"
with open("schools/header_school_zone.json") as f:
    header = json.load(f)
co = ChromiumOptions()
co.headless()
co.set_argument('--no-sandbox')
co.set_argument('--disable-gpu')
chrome = ChromiumPage(co)
user_agent = chrome.user_agent.replace("Headless", "")
co.set_user_agent(user_agent)
chrome = ChromiumPage(co)


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


zones = BatchList("schools_zones", ["school_number"])
for school_id in school_ids:
    header_ins = header.copy()
    header_ins['referer'] = f"{referer_base_url}?school={school_id}"
    try:
        url = f"{base_url}?school={school_id}"
        chrome.get(url)
        cf_bypass = CloudflareBypass(chrome)
        cf_bypass.bypass()
        school_zones = chrome.json.get('schoolZones', [])
        if len(school_zones) > 1:
            logging.warning(f"When ID = {school_id}, school zones length >= 2, keep the "
                            f"first zone only.")
        for zone in school_zones:
            zones.append({
                "school_number": school_id,
                "geometry": zone.get("geometry", {})
            })
    except Exception as e:
        logging.warning(f"Cannot fetch school zone of school ID {school_id}. "
                        f"{type(e).__name__}: {e}")
zones.flush()
