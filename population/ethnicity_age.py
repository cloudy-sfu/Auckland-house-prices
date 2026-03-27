# https://tools.summaries.stats.govt.nz/
import json
import logging
import os
import re
import sys
import time
from urllib.parse import quote
from random import uniform

import pandas as pd
import unicodedata
from bs4 import BeautifulSoup
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
with open("population/header_summaries_stats.json") as f:
    header = json.load(f)
engine = create_engine(os.environ['NEON_DB'], pool_recycle=300)
with engine.connect() as c:
    suburbs = pd.read_sql("select suburb_id, name from suburbs", c)
n_suburbs = suburbs.shape[0]


# %% Get ethnicity per suburb.
def create_slug(name):
    # https://tools.summaries.stats.govt.nz/_next/static/chunks/main-83224ffbc7866958.js
    # Regularize e.g. Ōtara -> otara
    nfd_string = unicodedata.normalize('NFD', name)
    name = ''.join(char for char in nfd_string if unicodedata.category(char) != 'Mn')
    slug = name.lower()
    slug = re.sub(r'[()]', '', slug)
    slug = slug.strip()
    slug = re.sub(r'[\s_-]+', '-', slug)
    return slug


ethnicity_all_suburbs = []
age_all_suburbs = []
for i, row in suburbs.iterrows():
    db_suburb_name = row['name']
    suburb_id = row['suburb_id']
    try:
        response = session.get(
            f"https://tools.summaries.stats.govt.nz/api/place/by-descriptor/"
            f"{quote(db_suburb_name)}",
            headers=header
        )
        response.raise_for_status()
        results = response.json()
        website_suburb_name = next(result['descriptor'] for result in results
                                   if result['code'] == str(suburb_id))
    except Exception as e:
        logging.warning(f"Fail to search suburb name in Stats NZ corresponding to "
                        f"\"{db_suburb_name}\". {type(e).__name__}: {e}")
        continue
    else:
        time.sleep(uniform(0.3, 0.7).__round__(2))

    url_name = create_slug(website_suburb_name)
    try:
        response = session.get(
            f"https://tools.summaries.stats.govt.nz/places/SA2/{url_name}",
            headers=header,
        )
        response.raise_for_status()
    except Exception as e:
        logging.warning(f"Cannot request data of suburb \"{db_suburb_name}\". "
                        f"{type(e).__name__}: {e}")
        continue
    else:
        time.sleep(uniform(0.3, 0.7).__round__(2))

    content = BeautifulSoup(response.text, 'html.parser')
    data_element = content.find('script', {'id': '__NEXT_DATA__'})
    if data_element is None:
        logging.warning(f"Cannot parse data of suburb \"{db_suburb_name}\". "
                        f"__NEXT_DATA__ JSON structure not found.")
        continue

    data = json.loads(data_element.text)

    try:
        topics = data['props']['pageProps']['place']
        ethnicity_topic = next(topic for topic in topics if topic['topic_id'] == 13)
        concepts = ethnicity_topic['concepts']
        ethnicity_concept = next(concept for concept in concepts
                                 if concept['concept_id'] == 109)
        sections = ethnicity_concept['sections']
        ethnicity_section = next(section for section in sections
                                 if section['section_id'] == 1033)
        ethnicity = ethnicity_section['numbers_data']['numbers']
    except Exception as e:
        logging.warning(f"Cannot parse ethnicity of suburb \"{db_suburb_name}\". "
                        f"{type(e).__name__}: {e}")
    else:
        ethnicity = pd.DataFrame(ethnicity)[['period', 'variable1_descriptor', 'value']]
        ethnicity['suburb_id'] = suburb_id
        ethnicity_all_suburbs.append(ethnicity)

    try:
        topics = data['props']['pageProps']['place']
        age_topic = next(topic for topic in topics if topic['topic_id'] == 11)
        concepts = age_topic['concepts']
        age_concept = next(concept for concept in concepts
                                 if concept['concept_id'] == 102)
        sections = age_concept['sections']
        age_section = next(section for section in sections
                                 if section['section_id'] == 1018)
        age = age_section['numbers_data']['numbers']
    except Exception as e:
        logging.warning(f"Cannot parse age structure of suburb \"{db_suburb_name}\". "
                        f"{type(e).__name__}: {e}")
    else:
        age = pd.DataFrame(age)
        age['age_group'] = age[
            'variable1_descriptor'].str.extract(r'^(\d+)')[0].astype(int)
        age['suburb_id'] = suburb_id
        age = age[['suburb_id', 'period', 'age_group', 'value']]
        age_all_suburbs.append(age)

    logging.info(f"Processed ethnicity of suburbs {i+1}/{n_suburbs}.")

# %% Post-processing.
ethnicity_all_suburbs = pd.concat(ethnicity_all_suburbs, axis=0)
ethnicity_all_suburbs.rename(
    columns={'period': 'year', 'variable1_descriptor': 'ethnicity', 'value': 'percentage'},
    inplace=True
)
ethnicity_all_suburbs.drop_duplicates(
    subset=['suburb_id', 'year', 'ethnicity'], inplace=True)
ethnicity_all_suburbs = ethnicity_all_suburbs.convert_dtypes()
age_all_suburbs = pd.concat(age_all_suburbs, axis=0)
age_all_suburbs.rename(
    columns={'period': 'year', 'value': 'percentage'},
    inplace=True
)

# %% Export.
batch_size = 500
for i in range(0, ethnicity_all_suburbs.shape[0], batch_size):
    upsert_dataframe(
        engine,
        ethnicity_all_suburbs.iloc[i:i+batch_size, :],
        ['suburb_id', 'year', 'ethnicity'],
        "ethnicity",
    )
for i in range(0, age_all_suburbs.shape[0], batch_size):
    upsert_dataframe(
        engine,
        age_all_suburbs.iloc[i:i+batch_size, :],
        ['suburb_id', 'year', 'age_group'],
        "age_structure",
    )
