import logging
import os
import sys

from sqlalchemy import create_engine

from macroeconomics.get_interest import *
from postgresql_ops import insert_skip_conflict

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

chart_id, series_names = get_chart_and_series(
    "https://www.interest.co.nz/charts/interest-rates/ocr"
)
all_data = get_chart_data(chart_id)

ocr_idx = get_series_idx(series_names, r"^NZ Official")
ocr = list_to_df(all_data[ocr_idx], 'day')
changed_mask = ocr['value'] != ocr['value'].shift(1)
ocr_1 = ocr[changed_mask].reset_index(drop=True)
ocr_1['date'] = pd.to_datetime(ocr_1['date'])
ocr_1 = ocr_1.convert_dtypes()

engine = create_engine(os.environ['NEON_DB'])
insert_skip_conflict(
    engine, ocr_1,
    ["date"],
    "macroeconomics_ocr"
)

annual_count = ocr_1.groupby(ocr_1['date'].dt.year).size()
logging.info(f"The times of OCR adjustment in each year:\n{annual_count}")
