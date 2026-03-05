from functools import partial


def get_dtype(d, *keys, dtype):
    value = d
    try:
        for key in keys:
            value = value[key]
    except (KeyError, IndexError, TypeError, AttributeError):
        return None
    if value is None:
        return value
    try:
        value = dtype(value)
    except (TypeError, ValueError):
        return None
    return value


get_float = partial(get_dtype, dtype=float)
get_bool = partial(get_dtype, dtype=bool)
get_str = partial(get_dtype, dtype=str)
get_int = partial(get_dtype, dtype=int)
