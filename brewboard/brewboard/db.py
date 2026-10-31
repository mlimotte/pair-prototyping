"""The app database (SQLite). The warehouse is loaded from it each night."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "brewboard.db"

SCHEMA = """
create table if not exists orders (
  order_id integer primary key, store_id text, session_id text, customer_id text,
  placed_at text, ready_at text, picked_up_at text, status text, total_cents integer);
create table if not exists order_lines (
  order_id integer, line_no integer, drink text, size text, milk text, qty integer, price_cents integer);
create table if not exists carts (
  cart_id integer primary key, session_id text, store_id text,
  created_at text, last_activity_at text, converted integer);
create table if not exists stock_events (store_id text, milk text, at text, sold_out integer);
"""


def connect(path=DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
