from functools import partial

import pandas as pd


def get_int(d, *keys):
    value = d
    try:
        for key in keys:
            value = value[key]
        value = int(value)
    except TypeError:
        value = pd.NA
    except ValueError:
        try:
            value = float(value)
            value = round(value)
        except ValueError:
            value = pd.NA
    return value


def get_dtype(cls, d, *keys):
    value = d
    try:
        for key in keys:
            value = value[key]
        value = cls(value)
    except (TypeError, ValueError):
        value = pd.NA
    return value


get_float = partial(get_dtype, float)
get_bool = partial(get_dtype, bool)
get_str = partial(get_dtype, str)
