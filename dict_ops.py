from functools import partial


def get_dtype(d, *keys, dtype):
    value = d
    try:
        for key in keys:
            value = value[key]
        value = dtype(value)
    except:
        return None
    else:
        return value


get_float = partial(get_dtype, dtype=float)
get_bool = partial(get_dtype, dtype=bool)
get_str = partial(get_dtype, dtype=str)
get_int = partial(get_dtype, dtype=int)
