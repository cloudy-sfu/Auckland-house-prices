import re

import pandas as pd
from bs4 import BeautifulSoup
from requests import Session

session = Session()


def get_chart_and_series(url):
    response = session.get(url)
    response.raise_for_status()
    response_text = BeautifulSoup(response.text, "html.parser")
    chart_wrapper_pattern = re.compile(r"^chart-wrapper-(\d+)$")
    chart_wrapper = response_text.find("div", {"id": chart_wrapper_pattern})
    chart_id = chart_wrapper_pattern.match(chart_wrapper.get('id', '')).group(1)
    selector = response_text.find("select", {"class": "chart-selector"})
    series_pattern = re.compile(rf"^chart-{chart_id}-(\d+)$")
    series_names = {
        series_pattern.match(e.get("value", "")).group(1):
        e.text
        for e in selector.find_all("option", {"value": series_pattern})
    }
    return chart_id, series_names


def get_series_idx(series_names, regex):
    for id_, name in series_names.items():
        if re.match(regex, name):
            return int(id_)
    else:
        raise Exception(f"No series name satisfies regex {regex}")


def get_chart_data(chart_id):
    response = session.post(
        "https://www.interest.co.nz/chart-data/get-csv-data",
        data={"nids[]": chart_id}
    )
    response.raise_for_status()
    response_json = response.json()[chart_id]['csv_data']
    return response_json


def list_to_df(series, freq):
    series = pd.DataFrame(data=series, columns=["timestamp", "value"])
    series['datetime'] = pd.to_datetime(series['timestamp'], unit='ms')

    match freq:
        case 'year':
            series['year'] = series['datetime'].dt.year
            return series[['year', 'value']]
        case 'quarter':
            series['year'] = series['datetime'].dt.year
            series['quarter'] = series['datetime'].dt.quarter
            return series[['year', 'quarter', 'value']]
        case 'month':
            series['year'] = series['datetime'].dt.year
            series['month'] = series['datetime'].dt.month
            return series[['year', 'month', 'value']]
        case 'day':
            series['date'] = series['datetime'].dt.date
            return series[['date', 'value']]
        case _:
            raise Exception("Argument 'freq' must be in ['year', 'quarter', 'month', "
                            "'day'].")
