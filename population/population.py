import logging
import os
import sys

import pandas as pd
from requests import Session
from sqlalchemy import create_engine

from postgresql_upsert import upsert_dataframe

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
)
session = Session()

now = pd.Timestamp('now', tz='UTC')
end_year = now.year

engine = create_engine(os.environ['NEON_DB'])
with engine.connect() as c:
    existed_years = pd.read_sql("select distinct year from public.population", c)
all_years = set(range(2015, end_year + 1))
if not existed_years.empty:
    all_years = all_years.difference(existed_years['year'].tolist())

all_populations = []
for year in all_years:
    response = session.get(
        "https://production.infometrics.co.nz/api/rep/data/",
        params={
            "breakdown": "SMALL",
            "series": "ERP",
            "year": year,
            "area_id": "auckland",
            "area_type": "SA2_26"
        }
    )
    response.raise_for_status()
    population = response.json()['series'][0]['values']
    if not population:
        logging.warning(f"Auckland population of year {year} hasn't been published.")
        continue
    population = pd.DataFrame(population)
    population = population[['small_area_code', 'year', 'value']]
    population = population.convert_dtypes()
    population.rename(columns={"small_area_code": "suburb_id"}, inplace=True)

    upsert_dataframe(
        engine, population,
        ['suburb_id', 'year'],
        "population"
    )
