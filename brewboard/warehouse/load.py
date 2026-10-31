"""Nightly load: copy app tables into the warehouse, then build the models."""
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TABLES = ["orders", "order_lines", "carts", "stock_events"]
MODELS = ["metric_daily_abandonment"]


def load(app_db, warehouse_db):
    wh = sqlite3.connect(warehouse_db)
    wh.execute("attach database ? as app", (str(app_db),))
    for t in TABLES:
        wh.execute(f"drop table if exists main.{t}")
        wh.execute(f"create table main.{t} as select * from app.{t}")
    wh.commit()
    wh.execute("detach database app")
    for m in MODELS:
        build_model(wh, m)
    wh.close()


def build_model(wh, name):
    sql = (HERE / "models" / f"{name}.sql").read_text()
    wh.execute(f"drop table if exists {name}")
    wh.execute(f"create table {name} as {sql}")
    wh.commit()


if __name__ == "__main__":
    load(sys.argv[1], sys.argv[2])
