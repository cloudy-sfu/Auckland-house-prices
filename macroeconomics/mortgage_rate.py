import os

from sqlalchemy import create_engine

from macroeconomics.get_interest import *
from postgresql_upsert import upsert_dataframe

chart_id, series_names_raw = get_chart_and_series(
    "https://www.interest.co.nz/charts/interest-rates/mortgage-rates"
)
mortgage_all = get_chart_data(chart_id)
series_renamer = {
    '_float': get_series_idx(series_names_raw, r"^Floating"),
    '_0_5_years': get_series_idx(series_names_raw, r"^6 months"),
    '_1_years': get_series_idx(series_names_raw, r"^1 year"),
    '_1_5_years': get_series_idx(series_names_raw, r"^18 months"),
    '_2_years': get_series_idx(series_names_raw, r"^2 year"),
    '_3_years': get_series_idx(series_names_raw, r"^3 year"),
    '_4_years': get_series_idx(series_names_raw, r"^4 year"),
    '_5_years': get_series_idx(series_names_raw, r"^5 year"),
}
mortgage = []
for col_name, series_idx in series_renamer.items():
    mortgage_per = list_to_df(mortgage_all[series_idx], 'day')
    mortgage_per.set_index('date', inplace=True)
    mortgage_per.rename({'value': col_name}, axis=1, inplace=True)
    mortgage.append(mortgage_per)
mortgage = pd.concat(mortgage, axis=1)
mortgage.reset_index(inplace=True)
engine = create_engine(os.environ['NEON_DB'])
with engine.begin() as c:
    upsert_dataframe(  # upsert because there are multiple time series
        engine, mortgage,
        ["date"],
        "macroeconomics_mortgage_rate"
    )
