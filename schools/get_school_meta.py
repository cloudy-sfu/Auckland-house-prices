import logging
import os
import re
import sys

import pandas as pd
import requests
from sqlalchemy import create_engine

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

# %% Get data.
session = requests.Session()
# Source: https://www.educationcounts.govt.nz/directories/list-of-nz-schools
# API documentation: https://catalogue.data.govt.nz/api/1/util/snippet/api_info.html?resource_id=4b292323-9fcc-41f8-814b-3c7b19cf14b3
# Noun definitions: https://www.educationcounts.govt.nz/site-info/glossary-filter
response = session.get(
    "https://catalogue.data.govt.nz/api/3/action/datastore_search_sql",
    params={"sql": "SELECT * FROM \"4b292323-9fcc-41f8-814b-3c7b19cf14b3\""}
)
response.raise_for_status()
try:
    response_json = response.json()
except requests.exceptions.JSONDecodeError as e:
    logging.info(response.text)
    raise e
schools = response_json['result']['records']
schools = pd.DataFrame(schools)
schools = schools.convert_dtypes()

# %% School types.
years_pattern = re.compile(r"\(Year\s+(\d+)\s*-\s*(\d+)\)")
years_pre_defined = {
    "Composite": (1, 13),
    "Full Primary": (1, 8),
    "Contributing": (1, 6),
    "Intermediate": (7, 8),
}


def infer_school_type(row):
    school_type = row['Org_Type']
    definition = row['Definition']

    if pd.isna(school_type):
        year_from = pd.NA
        year_to = pd.NA
        school_type_1 = definition
    else:
        match = re.search(years_pattern, school_type)
        if match:
            year_from = match.group(1)
            year_to = match.group(2)
            school_type_1 = definition
        elif school_type in years_pre_defined.keys():
            year_from, year_to = years_pre_defined[school_type]
            school_type_1 = definition
        else:
            year_from = pd.NA
            year_to = pd.NA
            if pd.isna(definition):
                school_type_1 = school_type
            else:
                school_type_1 = school_type + "; " + definition
    return year_from, year_to, school_type_1

schools[['year_from', 'year_to', 'school_type']] = (
    schools[['Org_Type', 'Definition']].apply(
        infer_school_type, axis=1, result_type='expand'))

# %% Institute language.
languages = {
    "All students taught in te reo Māori":
        (False, True, False),  #  ["Maori"]
    "Some students taught in te reo Māori":
        (True, True, False),  # ["English", "Maori"]
    "All students taught in a Pacific language":
        (False, False, True),  # ["Pacific"]
    "Some students taught in a Pacific language":
        (True, False, True),  # ["English", "Pacific"]
    "All students taught in te reo Māori or a Pacific language":
        (False, True, True),  # ["Maori", "Pacific"]
    "Some students taught in te reo Māori or a Pacific language":
        (True, True, True),  # ["English", "Maori", "Pacific"]
    "All students taught in English":
        (True, False, False),  # ["English"]
}


def infer_languages(row):
    language = languages.get(row['Language_of_Instruction'], (False, False, False))
    return language


schools[['lang_eng', 'lang_maori', 'lang_pacific']] = (
    schools[['Language_of_Instruction']].apply(
        infer_languages, axis=1, result_type="expand"))

# %% Public or private schools.
schools['is_public'] = ~schools['Authority'].str.startswith("Private")


# %% Gender.
def infer_gender(gender):
    if pd.isna(gender):
        gender_ = pd.NA
    elif "Co-Ed" in gender:
        gender_ = "mixed"
    elif "Boys" in gender:  # "Boys/Senior Co-Ed", "Primary Co-Ed, Secondary Girls" -> mixed
        gender_ = "boys"
    elif "Girls" in gender:
        gender_ = "girls"
    else:  # "Not Applicable"
        gender_ = pd.NA
    return gender_

schools['gender'] = schools["CoEd_Status"].apply(infer_gender)

# %% Other columns format converter.
schools['enrollment_scheme'] = schools['Enrolment_Scheme'] == 'Yes'
schools['boarding_facilities'] = schools['BoardingFacilities'] == 'Yes'
schools["eqi"] = pd.to_numeric(schools["EQi_Index"], errors="coerce")
schools['open_date'] = pd.to_datetime(schools['DateSchoolOpened']).dt.date.fillna(pd.NA)

# %% Directly convert columns.
schools.rename(columns={
    "School_Id": "school_number",
    "Org_Name": "school_name",
    "Add1_Line1": "street",
    "Add1_Suburb": "suburb",
    "Add1_City": "city",
    "Latitude": "latitude",
    "Longitude": "longitude",
    "Total": "students_total",
    "European": "students_european",
    "Māori": "students_maori",
    "Pacific": "students_pacific",
    "Asian": "students_asian",
    "MELAA": "students_melaa",
    "Other": "students_others",
    "International": "students_international",
}, inplace=True)

# %% Filter columns.
schools = schools[[
    "school_number",
    "school_name",
    "street",
    "suburb",
    "city",
    "school_type",
    "gender",
    "enrollment_scheme",
    "latitude",
    "longitude",
    "students_total",
    "students_european",
    "students_maori",
    "students_pacific",
    "students_asian",
    "students_melaa",
    "students_others",
    "students_international",
    "boarding_facilities",
    "year_from",
    "year_to",
    "is_public",
    "eqi",
    "lang_eng",
    "lang_maori",
    "lang_pacific",
    "open_date"
]]

# %% Export.
engine = create_engine(os.environ["NEON_DB"])
batch_size = 2000
with engine.begin() as c:
    for i in range(0, schools.shape[0], batch_size):
        upsert_dataframe(
            engine, schools.iloc[i:i+batch_size, :],
            ["school_number"],
            "schools"
        )
logging.info("Execution successful.")
