# Reference: https://www.chorus.co.nz/help/tools/broadband-availability-map
import json
import logging
import os
import sys
import time
from argparse import ArgumentParser
from io import BytesIO

import mercantile
import numpy as np
import pandas as pd
from PIL import Image
from rasterio import features
from rasterio.transform import from_bounds
from requests import Session
from sqlalchemy import create_engine

from batch_list import BatchList

# %% Constants.
parser = ArgumentParser()
parser.add_argument('--service', required=True)
args, _ = parser.parse_known_args()

# %% Initialization.
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
)

session = Session()
with open("broadband/chorus_broadband_coverage.json") as f:
    header = json.load(f)
engine = create_engine(os.environ['NEON_DB'], pool_recycle=300)
with open("broadband/broadband_coverage_terminal_nodes.sql") as f:
    sql_terminal_nodes = f.read()
service = args.service
match service:
    case 'fiber':
        dataset_ = "viewer_fibre.1761908400.1762372040"
        nocache = "1762372055"  # Thu Nov 06 2025 08:47:35 GMT+1300 (New Zealand Daylight Time)
        sql_terminal_nodes = (
            sql_terminal_nodes.replace(':table_name', 'broadband_coverage_tree'))
        trees = BatchList("broadband_coverage_tree", ["z", "x", "y"])
        records = BatchList("broadband_coverage", ["x", "y"])
    case 'hyperfiber':
        dataset_ = "hyperfibre.0004"
        nocache = "1602412470"  # Sun Oct 11 2020 23:34:30 GMT+1300 (New Zealand Daylight Time)
        sql_terminal_nodes = (
            sql_terminal_nodes.replace(':table_name', 'broadband_coverage_tree_hyperfiber'))
        trees = BatchList("broadband_coverage_tree_hyperfiber", ["z", "x", "y"])
        records = BatchList("broadband_coverage_hyperfiber", ["x", "y"])
    case _:
        raise Exception("Cannot recognize Internet connection type.")
start_zoom = 10
end_zoom = 15
assert end_zoom - start_zoom > 0, "End zoom must be larger than start zoom."

# %% Traverse operations.
def _get_tile_mask(x, y, z, dataset):
    response = session.get(
        "https://bbc-viewer-v4.wivolo.com/tiles/render",
        params={
            "dataset": dataset,
            "nocache": nocache,
            "index": f"{z}/{x}/{y}",
            "notice": "for-display-on-chorus-website-only",
        },
        headers=header,
    )
    response.raise_for_status()
    time.sleep(0.3)
    img = Image.open(BytesIO(response.content)).convert("RGBA")
    img_array = np.array(img)
    mask = (img_array[:, :, 3] > 0).astype(np.uint8)
    assert mask.shape == (256, 256), "Returned PNG size is not 256*256."
    return mask


def get_leaf(x, y, z, dataset, parent_x=None, parent_y=None, role=None):
    assert z == end_zoom, f"get_leaf requires z = {end_zoom}, received z = {z}."
    try:
        mask = _get_tile_mask(x, y, z, dataset)
    except Exception as e:
        logging.warning(f"Fail to parse tile {z}/{x}/{y}, service {service}. "
                        f"{type(e).__name__}: {e}")
        return

    geometries = []
    if np.any(mask):
        bounds = mercantile.xy_bounds(x, y, z)
        height, width = mask.shape
        transform = from_bounds(
            bounds.left, bounds.bottom, bounds.right, bounds.top, width, height
        )
        for geom_dict, val in features.shapes(mask, mask=mask, transform=transform):
            if val == 1:  # Only keep the shapes where mask == 1
                geometries.append(geom_dict)
    tree = {
        "z": z,
        "x": x,
        "y": y,
        "q1_empty": None,
        "q1_full": None,
        "q2_empty": None,
        "q2_full": None,
        "q3_empty": None,
        "q3_full": None,
        "q4_empty": None,
        "q4_full": None,
        "parent_x": parent_x,
        "parent_y": parent_y,
        "role": role,
    }
    trees.append(tree)
    record = {
        "x": x,
        "y": y,
        "geometry": geometries
    }
    records.append(record)


def get_branch(x, y, z, dataset, parent_x=None, parent_y=None, role=None):
    assert z < end_zoom, f"get_branch requires z < {end_zoom}, received z = {z}."
    try:
        mask = _get_tile_mask(x, y, z, dataset)
    except Exception as e:
        logging.warning(f"Fail to parse tile {z}/{x}/{y}, service {service}. "
                        f"{type(e).__name__}: {e}")
        return

    q1 = mask[:128, :128]
    q1_any = q1.any()
    q1_full = q1.all()
    q2 = mask[:128, 128:]
    q2_any = q2.any()
    q2_full = q2.all()
    q3 = mask[128:, :128]
    q3_any = q3.any()
    q3_full = q3.all()
    q4 = mask[128:, 128:]
    q4_any = q4.any()
    q4_full = q4.all()

    if not (z > start_zoom and (parent_x is None or parent_y is None)):
        # exclude restored terminal nodes
        tree = {
            "z": z,
            "x": x,
            "y": y,
            "q1_empty": not q1_any,
            "q1_full": q1_full,
            "q2_empty": not q2_any,
            "q2_full": q2_full,
            "q3_empty": not q3_any,
            "q3_full": q3_full,
            "q4_empty": not q4_any,
            "q4_full": q4_full,
            "parent_x": parent_x,
            "parent_y": parent_y,
            "role": role,
        }
        trees.append(tree)

    if q1_any and (not q1_full):
        if z < end_zoom - 1:
            get_branch(2 * x, 2 * y, z + 1, dataset, x, y, 1)
        else:  # z == end_zoom - 1
            get_leaf(2 * x, 2 * y, z + 1, dataset, x, y, 1)
    if q2_any and (not q2_full):
        if z < end_zoom - 1:
            get_branch(2 * x + 1, 2 * y, z + 1, dataset, x, y, 2)
        else:  # z == end_zoom - 1
            get_leaf(2 * x + 1, 2 * y, z + 1, dataset, x, y, 2)
    if q3_any and (not q3_full):
        if z < end_zoom - 1:
            get_branch(2 * x, 2 * y + 1, z + 1, dataset, x, y, 3)
        else:  # z == end_zoom - 1
            get_leaf(2 * x, 2 * y + 1, z + 1, dataset, x, y, 3)
    if q4_any and (not q4_full):
        if z < end_zoom - 1:
            get_branch(2 * x + 1, 2 * y + 1, z + 1, dataset, x, y, 4)
        else:  # z == end_zoom - 1
            get_leaf(2 * x + 1, 2 * y + 1, z + 1, dataset, x, y, 4)


# %% Build from root node.
west, south, east, north = 174.20, -37.35, 175.30, -36.10
base_tiles = mercantile.tiles(west, south, east, north, zooms=[start_zoom])
base_tiles = [[tile.z, tile.x, tile.y] for tile in base_tiles]
base_tiles = pd.DataFrame(data=base_tiles, columns=["z", "x", "y"])
with engine.connect() as c:
    recorded_base_tiles = pd.read_sql(
        f"select x, y from broadband_coverage_tree where z = {start_zoom}", c)
base_tiles_idx = pd.MultiIndex.from_frame(base_tiles[['x', 'y']])
recorded_base_tiles_idx = pd.MultiIndex.from_frame(recorded_base_tiles[['x', 'y']])
missed_base_tiles = base_tiles.loc[~base_tiles_idx.isin(recorded_base_tiles_idx)]

# %% Build from terminal node.
with engine.connect() as c:
    terminal_nodes = pd.read_sql(sql_terminal_nodes, c)

# %% Execute tasks.
for _, base_tile in missed_base_tiles.iterrows():
    get_branch(base_tile['x'], base_tile['y'], base_tile['z'], dataset_)
for _, row in terminal_nodes.iterrows():
    get_branch(row['x'], row['y'], row['z'], dataset_)
trees.flush()
records.flush()
