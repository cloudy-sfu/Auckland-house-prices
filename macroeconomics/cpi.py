import os

from sqlalchemy import create_engine

from macroeconomics.get_interest import *
from postgresql_ops import insert_skip_conflict

chart_id, series_names = get_chart_and_series(
    "https://www.interest.co.nz/charts/prices/consumer-prices-index"
)
all_data = get_chart_data(chart_id)

cpi_all_idx = get_series_idx(series_names, r"^CPI")
cpi_all = list_to_df(all_data[cpi_all_idx], 'quarter')
cpi_all = cpi_all.convert_dtypes()
engine = create_engine(os.environ['NEON_DB'])
insert_skip_conflict(
    engine, cpi_all,
    ["year", "quarter"],
    "macroeconomics_cpi_all"
)

cpi_non_tradable_idx = get_series_idx(series_names, r"^Non-tradable")
cpi_non_tradable = list_to_df(all_data[cpi_non_tradable_idx], 'quarter')
cpi_non_tradable = cpi_non_tradable.convert_dtypes()
insert_skip_conflict(
    engine, cpi_non_tradable,
    ["year", "quarter"],
    "macroeconomics_cpi_non_tradable"
)
