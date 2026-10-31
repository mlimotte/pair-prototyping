"""Sold-out milks. The barista marks a milk out; customers cannot pick it."""
import time

from . import db

# Stock reads went to the POS on every page view. Cache them to cut load on the POS.
CACHE_TTL_SECONDS = 300

_cache = {}  # store_id -> (read_at, set of sold-out milks)


def sold_out(conn, store_id, now=None):
    """Return the set of milks sold out at a store, as the customer page sees it."""
    now = time.time() if now is None else now
    hit = _cache.get(store_id)
    if hit and now - hit[0] < CACHE_TTL_SECONDS:
        return hit[1]
    milks = _read(conn, store_id)
    _cache[store_id] = (now, milks)
    return milks


def _read(conn, store_id):
    rows = conn.execute(
        "select milk, sold_out from stock_events where store_id = ? order by at", (store_id,)).fetchall()
    out = set()
    for r in rows:
        (out.add if r["sold_out"] else out.discard)(r["milk"])
    return out


def toggle(conn, store_id, milk, at):
    """Barista action: flip a milk between sold out and available."""
    now_out = milk not in _read(conn, store_id)
    conn.execute("insert into stock_events values (?, ?, ?, ?)", (store_id, milk, at, int(now_out)))
    conn.commit()
    return now_out
