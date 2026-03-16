import os

from sqlalchemy import create_engine

from macroeconomics.get_interest import *
from postgresql_upsert import insert_if_not_exists

chart_id, series_names_raw = get_chart_and_series(
    "https://www.interest.co.nz/charts/interest-rates/swap-rates"
)
mortgage_all = get_chart_data(chart_id)
series_renamer = {
    '_1_years': get_series_idx(series_names_raw, r"^1 year"),
    '_2_years': get_series_idx(series_names_raw, r"^2 year"),
    '_3_years': get_series_idx(series_names_raw, r"^3 year"),
    '_4_years': get_series_idx(series_names_raw, r"^4 year"),
    '_5_years': get_series_idx(series_names_raw, r"^5 year"),
    '_7_years': get_series_idx(series_names_raw, r"^7 year"),
    '_10_years': get_series_idx(series_names_raw, r"^10 year"),
}
swap_rate = []
for col_name, series_idx in series_renamer.items():
    swap_rate_per = list_to_df(mortgage_all[series_idx], 'day')
    swap_rate_per.set_index('date', inplace=True)
    swap_rate_per.rename({'value': col_name}, axis=1, inplace=True)
    swap_rate_per = swap_rate_per[~swap_rate_per.index.duplicated(keep='last')]
    swap_rate.append(swap_rate_per)
swap_rate = pd.concat(swap_rate, axis=1)
swap_rate.reset_index(inplace=True)
swap_rate = swap_rate.convert_dtypes()
engine = create_engine(os.environ['NEON_DB'])
insert_if_not_exists(  # upsert because there are multiple time series
    engine, swap_rate,
    ["date"],
    "macroeconomics_wholesale_swap_rate"
)
