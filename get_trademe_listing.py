import json
import logging
import os
import sys

import pandas as pd
from bs4 import BeautifulSoup
from requests import Session
from sqlalchemy import create_engine, text
from tqdm import tqdm

from postgresql_upsert import upsert_dataframe

# %% Setup logger.
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
)

# %% Calc last checkout
engine = create_engine(os.environ["NEON_DB"])
with engine.begin() as c:
    result = c.execute(text("select max(\"solving_start_time\") from trademe_crawler "
                            "where solving_end_time is not null;"))
    last_checkout_time = result.fetchone()[0]
if last_checkout_time is None:
    last_checkout_time = pd.Timestamp(0, tz="UTC")

# %% Initialize web crawler.
session = Session()
with open("headers/header_1.json", "r") as f:
    header = json.load(f)

# %% Initialize meta data.
with engine.begin() as c:
    result = c.execute(text("insert into trademe_crawler (solving_start_time) values "
                            "(NOW()) RETURNING id;"))
    task_id = result.fetchone()[0]

# %%
try:
    response = session.get(
        "https://www.trademe.co.nz/a/property/residential/sale/auckland",
        headers=header,
    )
    response.raise_for_status()
    tree = BeautifulSoup(response.text, "html.parser")
    entities = tree.find('script', {'id': 'frend-state'}).text
    entities = json.loads(entities)
    meta_parent = entities["NGRX_STATE"]['search']['entities']
    token = list(meta_parent.keys())[0]
    meta = meta_parent[token]['item']
    n_pages = int(meta['totalCount'] / meta['pageSize']) + 1  # equivalent to "ceil"
except Exception as e:
    logging.error(f"[Meta data] {type(e).__name__}: {e}")
    exit(1)

max_failed_pages = 5
failed_pages = 0
for page in tqdm(range(1, n_pages + 1), desc="Read properties"):
    try:
        response = session.get(
            "https://www.trademe.co.nz/a/property/residential/sale/auckland",
            headers=header,
            # duration cannot be shorter than 56 days; it counts from item.startDate and
            # can be relisted.
            params={"page": str(page), "sort_order": "expirydesc"}
        )
        response.raise_for_status()

        tree = BeautifulSoup(response.text, "html.parser")
        entities = tree.find('script', {'id': 'frend-state'}).text
        entities = json.loads(entities)
        entities = entities["NGRX_STATE"]["listing"]["cachedSearchResults"]["entities"]
    except Exception as e:
        failed_pages += 1
        if failed_pages <= max_failed_pages:
            logging.warning(f"[Page {page}] {type(e).__name__}: {e}")
            with engine.begin() as c:
                c.execute(text("UPDATE trademe_crawler SET failed_pages = array_append("
                               "COALESCE(failed_pages, ARRAY[]::integer[]), :page) "
                               "WHERE id = :task_id;"),
                          {"page": page, "task_id": task_id})
        else:
            with engine.begin() as c:
                c.execute(text("UPDATE trademe_crawler SET stop_before_page = :page "
                               "WHERE id = :task_id;"),
                          {"page": page, "task_id": task_id})
            logging.error("Exceed maximum number pages failed to parse.")
            exit(1)
    else:
        if not entities.items():
            logging.warning(f"Page {page} is empty.")
            failed_pages += 1
            continue
        entities_df = pd.DataFrame(entities.items(), columns=['listing_id', 'entity'])
        entities_df['entity'] = entities_df['entity'].apply(lambda x: x.get('item', {}))
        entities_df['entity'].apply(lambda x: x.pop('listingId', None))
        start_time_str = entities_df['entity'].apply(
            lambda x: x.get('startDate', '').removeprefix('__date__:'))
        entities_df['start_time'] = pd.to_datetime(start_time_str, errors="coerce")
        entities_df['entity'] = entities_df['entity'].apply(lambda x: json.dumps(x))
        entities_df['task_id'] = task_id
        if entities_df['start_time'].min() <= last_checkout_time:
            entities_df = entities_df.loc[entities_df['start_time'] > last_checkout_time, :]
            upsert_dataframe(
                engine,
                entities_df,
                ['listing_id'],
                'trademe_properties',
            )
            with engine.begin() as c:
                c.execute(text("UPDATE trademe_crawler SET solving_end_time = NOW(), "
                               "complete_after_page = :page "
                               "WHERE id = :task_id"),
                          {"page": page, "task_id": task_id})
            logging.info("Reach last checkout time, successfully finished.")
            break
        else:
            upsert_dataframe(
                engine,
                entities_df,
                ['listing_id'],
                'trademe_properties',
            )
