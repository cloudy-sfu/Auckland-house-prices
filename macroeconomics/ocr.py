import os

from sqlalchemy import create_engine

from macroeconomics.get_interest import *
from postgresql_upsert import insert_if_not_exists

chart_id, series_names = get_chart_and_series(
    "https://www.interest.co.nz/charts/interest-rates/ocr"
)
all_data = get_chart_data(chart_id)

ocr_idx = get_series_idx(series_names, r"^NZ Official")
ocr = list_to_df(all_data[ocr_idx], 'day')
engine = create_engine(os.environ['NEON_DB'])
insert_if_not_exists(
    engine, ocr,
    ["date"],
    "macroeconomics_ocr"
)
