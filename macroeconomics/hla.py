import os

from sqlalchemy import create_engine

from macroeconomics.get_interest import *
from postgresql_upsert import insert_if_not_exists

chart_id, series_names = get_chart_and_series(
    "https://www.interest.co.nz/charts/real-estate/hla-young-family"
)
hla_low_all = get_chart_data(chart_id)

hla_low_idx = get_series_idx(series_names, r"Auckland")
hla_low_akl = list_to_df(hla_low_all[hla_low_idx], 'month')
engine = create_engine(os.environ['NEON_DB'])
with engine.begin() as c:
    insert_if_not_exists(
        engine, hla_low_akl,
        ["year", "month"],
        "macroeconomics_hla_low"
    )


chart_id, series_names = get_chart_and_series(
    "https://www.interest.co.nz/charts/real-estate/hla-second-rung"
)
hla_mid_all = get_chart_data(chart_id)

hla_mid_idx = get_series_idx(series_names, r"Auckland")
hla_mid_akl = list_to_df(hla_mid_all[hla_mid_idx], 'month')
engine = create_engine(os.environ['NEON_DB'])
with engine.begin() as c:
    insert_if_not_exists(
        engine, hla_mid_akl,
        ["year", "month"],
        "macroeconomics_hla_mid"
    )
