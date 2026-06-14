import logging

import pandas as pd
from sqlalchemy import engine

from postgresql_ops import upsert


class BatchList:
    def __init__(self, table_name, unique_key_columns, batch_size=500):
        self._items = []  # Internal list
        self.table_name = table_name
        self.unique_key_columns = unique_key_columns
        self.batch_size = batch_size

    def append(self, obj):
        self._items.append(obj)
        if len(self._items) >= self.batch_size:
            self.flush()

    def flush(self):
        df = pd.DataFrame(self._items).convert_dtypes()
        df.drop_duplicates(subset=self.unique_key_columns, keep='first', inplace=True)
        upsert(
            engine,
            df,
            self.unique_key_columns,
            self.table_name
        )
        self._items.clear()
        logging.info(f"Upserted {df.shape[0]} records to {self.table_name}.")
