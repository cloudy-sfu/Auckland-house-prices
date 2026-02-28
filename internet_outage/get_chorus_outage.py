import json
import logging
import os
import re
import sys

import pandas as pd
from requests import Session
from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
)
session = Session()

# %% Load header.
with open("internet_outage/chorus_config.json") as f:
    header_config = json.load(f)
with open("internet_outage/chorus_incidents.json") as f:
    header_incidents = json.load(f)

# %% Get auth.
response = session.get(
    "https://www.chorus.co.nz/config.json", headers=header_config, timeout=3)
if response.status_code != 200:
    raise Exception(f"Status code: {response.status_code}. Reason: {response.reason}")
response_json = response.json()
auth = response_json['OUTAGES']['AUTH']
logging.info("Received the authentication key.")

# %% Get outage.
header_incidents['authorization'] = auth
response = session.get(
    "https://api.chorus.co.nz/events/v3/incidents",
    params=json.dumps({"includePolygons": "true"}),
    headers=header_incidents,
    timeout=3,
)
if response.status_code != 200:
    logging.error(f"Status code: {response.status_code}. Reason: {response.reason}")
incidents = response.json()
logging.info("Received the outages' data structure.")

# %% Parse outage map.
assert isinstance(incidents, list), "Fail to parse outages' data structure."
update_re = re.compile(r'(?P<update_time>\d{2}/\d{2}/\d{4} \d{2}:\d{2})')


def extract_update_time(text: str):
    """
    Extracts the update time from a log line of the form
    "dd/mm/YYYY hh:MM Update ...".
    Returns the timestamp string if matched, otherwise pd.NA.
    """
    match = update_re.search(text)
    if match:
        update_time_str = match.group('update_time')
        update_time_naive = pd.to_datetime(
            update_time_str, format="%d/%m/%Y %H:%M", errors="coerce")
        update_time = update_time_naive.tz_localize(
            tz='Pacific/Auckland', ambiguous='NaT', nonexistent='NaT')
        return update_time
    else:
        return pd.NaT


outages = []
for incident in incidents:
    sites = incident.get('sites', [])
    start_time_raw = incident.get('start_time')
    if start_time_raw is None:
        start_time = pd.NaT
    else:
        start_time_naive = pd.to_datetime(start_time_raw, unit='s')
        start_time_utc = start_time_naive.tz_localize(tz='UTC', nonexistent='NaT')
        start_time = start_time_utc.tz_convert('Pacific/Auckland')
    update_lines = incident.get('add_desc', '').split('\n')
    match len(update_lines):
        case 0:
            update_time_ = pd.NA
            update_text = pd.NA
        case 1:
            update_time_ = pd.NaT
            update_text = update_lines[0]
        case _:  # n_lines >= 2
            update_time_ = extract_update_time(update_lines[0])
            update_text = update_lines[1]
    description = incident.get('description', '')
    for site in sites:
        try:
            # can be parsed by shapely.geometry.shape
            point = json.loads(site.get('point', ''))
        except json.JSONDecodeError:
            point = pd.NA
        try:
            # can be parsed by shapely.geometry.shape
            multi_polygon = json.loads(site.get('poly', ''))
        except json.JSONDecodeError:
            multi_polygon = pd.NA
        site_ = {
            "start_time": start_time,
            "incident_point": point,
            "incident_area": multi_polygon,
            "role": site.get('role', pd.NA),
            "n_impacted_services": site.get('impact', pd.NA),
            "description": description,
            "update_time": update_time_,
            "update_text": update_text,
        }
        outages.append(site_)
outages = pd.DataFrame(outages)

# %% Export.
outages['incident_point'] = outages['incident_point'].to_json()
outages['incident_area'] = outages['incident_area'].to_json()
engine = create_engine(os.environ['NEON_DB'])
with engine.begin() as c:
    delete_query = text("DELETE FROM public.internet_outage_chorus "
                        "WHERE recorded_time >= NOW() - INTERVAL '12 hours'")
    c.execute(delete_query)
    outages.to_sql(name="internet_outage_chorus", con=c, schema="public", if_exists="append",
                   index=False)
