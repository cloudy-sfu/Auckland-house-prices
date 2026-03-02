from sqlalchemy import create_engine, text
import os

engine = create_engine(os.environ['NEON_DB'])
with engine.connect() as c:
    query_1 = c.execute(text("select count(*) from suburbs"))
    result = query_1.fetchone()
suburbs_count = result[0]
if suburbs_count == 0:
    exit(3)
else:
    exit(0)
