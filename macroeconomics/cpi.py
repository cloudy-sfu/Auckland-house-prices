import os

from sqlalchemy import create_engine

from macroeconomics.get_interest import *
from postgresql_upsert import insert_if_not_exists

chart_id, series_names = get_chart_and_series(
    "https://www.interest.co.nz/charts/prices/consumer-prices-index"
)
all_data = get_chart_data(chart_id)

cpi_all_idx = get_series_idx(series_names, r"^CPI")
cpi_all = list_to_df(all_data[cpi_all_idx], 'quarter')
engine = create_engine(os.environ['NEON_DB'])
with engine.begin() as c:
    insert_if_not_exists(
        engine, cpi_all,
        ["year", "quarter"],
        "macroeconomics_cpi_all"
    )

cpi_non_tradable_idx = get_series_idx(series_names, r"^Non-tradable")
cpi_non_tradable = list_to_df(all_data[cpi_non_tradable_idx], 'quarter')
with engine.begin() as c:
    insert_if_not_exists(
        engine, cpi_non_tradable,
        ["year", "quarter"],
        "macroeconomics_cpi_non_tradable"
    )
