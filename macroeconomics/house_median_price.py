import os

from sqlalchemy import create_engine

from macroeconomics.get_interest import *
from postgresql_upsert import insert_if_not_exists

chart_id, series_names = get_chart_and_series(
    "https://www.interest.co.nz/charts/real-estate/median-price-reinz"
)
all_data = get_chart_data(chart_id)

ocr_idx = get_series_idx(series_names, r"^Auckland$")
ocr = list_to_df(all_data[ocr_idx], 'month')
ocr = ocr.convert_dtypes()
engine = create_engine(os.environ['NEON_DB'])
insert_if_not_exists(
    engine, ocr,
    ["year", "month"],
    "macroeconomics_house_median_price"
)
