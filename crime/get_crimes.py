import logging
import os
import subprocess
import sys

import pandas as pd
from requests import Session
from sqlalchemy import create_engine, NullPool, text

from postgresql_upsert import upsert_dataframe

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
)
session = Session()


def get_crimes(suburb_id, start_year, start_month, end_year, end_month):
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
        logging.info(f"No crime counts of suburb {suburb_id_} from year={start_year}, "
                     f"month={start_month} to year={end_year}, month={end_month}.")
        return None
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
    )
    records_monthly = records_monthly.convert_dtypes()
    records_monthly.reset_index(inplace=True)
    records_monthly.columns.name = None
    records_monthly.insert(0, 'suburb_id', suburb_id, allow_duplicates=False)
    return records_monthly


def get_missing_periods(missing_df, start_year, start_month, end_year, end_month):
    # If the dataframe is empty, return an empty list
    if missing_df.shape[0] == 0:
        return []
    # Ensure the dataframe is sorted chronologically
    df_sorted = missing_df.sort_values(by=['year', 'month']).reset_index(drop=True)
    # Optional boundary enforcement (if the dataframe contains data outside the global limits)
    if start_year and start_month:
        df_sorted = df_sorted[(df_sorted['year'] > start_year) | (
                (df_sorted['year'] == start_year) & (
                df_sorted['month'] >= start_month))]
    if end_year and end_month:
        df_sorted = df_sorted[(df_sorted['year'] < end_year) | (
                (df_sorted['year'] == end_year) & (df_sorted['month'] <= end_month))]

    df_sorted.reset_index(drop=True, inplace=True)
    if df_sorted.shape[0] == 0:
        return []
    # Map year and month to an absolute sequence to easily detect gaps
    absolute_months = df_sorted['year'] * 12 + df_sorted['month']
    # Calculate difference. A diff > 1 means the months are not consecutive.
    common_mask = absolute_months.diff() > 1
    # Extract index boundaries
    common_idx = common_mask[common_mask].index.tolist()
    start_idx = [0] + common_idx
    end_idx = [i - 1 for i in common_idx] + [len(absolute_months) - 1]
    # Build the 2D list of [start_year, start_month, end_year, end_month]
    missing_periods = [
        [
            df_sorted.loc[s, 'year'], df_sorted.loc[s, 'month'],
            df_sorted.loc[e_, 'year'], df_sorted.loc[e_, 'month']
        ]
        for s, e_ in zip(start_idx, end_idx)
    ]
    return missing_periods


start_year_ = 2020
start_month_ = 1
now = pd.Timestamp('now', tz='UTC')
end_year_ = now.year
end_month_ = now.month

with open("crime/crimes_missing.sql") as f:
    sql_missing = f.read()
engine = create_engine(os.environ['NEON_DB'], poolclass=NullPool)
with engine.connect() as c:
    tasks_all = pd.read_sql(
        sql=text(sql_missing), con=c,
        params={"end_month": f"{end_year_}-{str(end_month_).zfill(2)}-01"}
    )

records_all = []
for suburb_id_, tasks_per_suburb in tasks_all.groupby('suburb_id'):
    query_periods = get_missing_periods(
        tasks_per_suburb, start_year_, start_month_, end_year_, end_month_)
    for query_period in query_periods:
        try:
            records_ = get_crimes(suburb_id_, *query_period)
            records_all.append(records_)
        except Exception as e:
            logging.warning(f"Finding error when fetching crime counts of suburb "
                            f"{suburb_id_} from year={query_period[0]}, "
                            f"month={query_period[1]} to year={query_period[2]}, "
                            f"month={query_period[3]}. {type(e).__name__}: {e}")

if records_all:
    records_all = pd.concat(records_all, axis=0)
    upsert_dataframe(
        engine, records_all,
        ['suburb_id', 'year', 'month'],
        'crimes'
    )
