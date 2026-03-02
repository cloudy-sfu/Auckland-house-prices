import logging
import os
import sys

import pandas as pd
from requests import Session
from sqlalchemy import create_engine, NullPool, text

from postgresql_upsert import upsert_dataframe

# %% Initialization.
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
)
session = Session()

global_start_year = 2015
global_start_month = 1
now = pd.Timestamp('now', tz='UTC')
end_year = now.year - (now.month == 1)  # minus one natural month
end_month = (now.month - 2) % 12 + 1

# %% Get start year & month for each suburb.
with open("crime/crime_start_year_month.sql") as f:
    sql_start_year_month = f.read()
engine = create_engine(os.environ['NEON_DB'], poolclass=NullPool)
with engine.connect() as c:
    start_year_month = pd.read_sql(sql=text(sql_start_year_month), con=c)
start_year_month = start_year_month.convert_dtypes()

# %% Main loop.
records_all = []
for _, row in start_year_month.iterrows():
    suburb_id = row['suburb_id']
    next_month = row['next_month']
    if pd.isna(next_month):
        start_year = global_start_year
        start_month = global_start_month
    else:
        start_year = next_month // 12
        start_month = next_month % 12 + 1  # convert mod to month, not plus 1 month

    try:
        # %% Fetch criminal cases.
        records = []
        page_size = 1000
        i = 1
        while True:
            response_ = session.get(
                "https://nz-crime-8kpe.onrender.com/api/crimes",
                params={
                    "suburb_id": suburb_id,
                    "start_date": f"{start_year}-{str(start_month).zfill(2)}-01",
                    "end_date": f"{end_year}-{str(end_month).zfill(2)}-01",
                    "page": i,
                    "page_size": page_size,
                }
            )
            response_.raise_for_status()
            buffer_records = response_.json()
            records += buffer_records
            if len(buffer_records) < page_size:
                break
            i += 1
        records = pd.DataFrame(records)
        if records.empty:
            logging.info(f"No crime counts of suburb {suburb_id} from year={start_year}, "
                         f"month={start_month} to year={end_year}, month={end_month}.")
            continue

        # %% Calc monthly sum of criminal cases.
        records['victimisation_date'] = pd.to_datetime(records['victimisation_date'])
        records['year'] = records['victimisation_date'].dt.year
        records['month'] = records['victimisation_date'].dt.month
        records_monthly = records.groupby(
            ['year', 'month', 'offence_code']).count()[['event_id']]
        records_monthly.reset_index(inplace=True)
        records_monthly.rename(columns={'event_id': 'count'}, inplace=True)
        offence_code_to_name = {
            "2": "assault",  # attack people
            "3": "sexual_offence",
            "4": "endanger_people",  # e.g. kidnapping
            "5": "robbery",  # robbery with weapon
            "6": "burglary",  # break in and commit a crime
            "7": "theft",
        }
        records_monthly['offence_name'] = records_monthly['offence_code'].map(
            offence_code_to_name)
        records_monthly = records_monthly.loc[~records_monthly['offence_name'].isna(), :]
        records_monthly = records_monthly.pivot(
            index=['year', 'month'],
            columns='offence_name',
            values='count'
        ).reindex(columns=offence_code_to_name.values())

        # %% Fill holes in time range.
        observed_start_year, observed_start_month = records_monthly.index.min()
        observed_end_year, observed_end_month = records_monthly.index.max()
        observed_series = [
            (n // 12, n % 12 + 1)
            for n in range(
                observed_start_year * 12 + observed_start_month - 1,
                observed_end_year * 12 + observed_end_month
            )
        ]
        observed_series = pd.MultiIndex.from_tuples(observed_series)
        observed_series = pd.DataFrame(index=observed_series)
        observed_series.index.names = ('year', 'month')
        records_monthly = pd.merge(records_monthly, observed_series,
                                   how='left', left_index=True, right_index=True)
        records_monthly = records_monthly.fillna(0)

        # %% Adjust format to what database expects.
        records_monthly = records_monthly.convert_dtypes()
        records_monthly.reset_index(inplace=True)
        records_monthly.columns.name = None
        records_monthly.insert(0, 'suburb_id', suburb_id, allow_duplicates=False)

    except Exception as e:
        logging.info(f"Finding error when fetching data of suburb {suburb_id} from "
                     f"year={start_year}, month={start_month} to year={end_year}, "
                     f"month={end_month}. {type(e).__name__}: {e}")
    else:
        records_all.append(records_monthly)

if records_all:
    records_all = pd.concat(records_all, axis=0)
    upsert_dataframe(
        engine, records_all,
        ['suburb_id', 'year', 'month'],
        'crimes'
    )
