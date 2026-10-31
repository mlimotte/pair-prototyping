"""Compute part 4's figure data from a generated starter: three views of one question.

    python tools/export_part4.py <starter dir> > site/static/data/part4.json

"When oat sells out, do customers switch or leave?" as seen by the orders table, the dashboard
tile, and the session events (which are not in the warehouse).
"""
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def main(starter):
    starter = Path(starter)
    wh = sqlite3.connect(starter / "brewboard/data/warehouse.sqlite")
    out_at = {(s, at[:10]): at for s, at in wh.execute(
        "select store_id, at from stock_events where milk = 'oat' and sold_out = 1")}

    # 1. Orders: milk mix of milk-drink lines placed after the sell-out vs at the same hours on other days.
    mix = {"during": Counter(), "normal": Counter()}
    for store, placed, milk in wh.execute(
            "select o.store_id, o.placed_at, l.milk from orders o join order_lines l using (order_id) "
            "where l.milk is not null and o.status = 'picked_up'"):
        hour = int(placed[11:13])
        if hour < 12:
            continue
        at = out_at.get((store, placed[:10]))
        if at and placed >= at:
            mix["during"][milk] += 1
        elif not at:
            mix["normal"][milk] += 1
    share = {k: {m: round(c[m] / sum(c.values()), 3) for m in ("whole", "oat", "almond")} for k, c in mix.items()}

    # 2. Dashboard: the abandonment tile on sell-out days vs other days.
    tile = defaultdict(lambda: [0, 0])
    for day, store, carts, abandoned in wh.execute("select day, store_id, carts, abandoned from metric_daily_abandonment"):
        k = "sellout_days" if (store, day) in out_at else "other_days"
        tile[k][0] += carts
        tile[k][1] += abandoned
    dash = {k: round(a / c, 4) for k, (c, a) in tile.items()}
    overall = wh.execute("select round(1.0 * sum(abandoned) / sum(carts), 4) from metric_daily_abandonment").fetchone()[0]

    # 3. Session events: what people did after they saw oat sold out.
    carts = {sid: (created, last) for sid, created, last in wh.execute(
        "select session_id, created_at, last_activity_at from carts where converted = 0")}
    # Per session: the first reaction after it first saw oat sold out, and whether it ordered in the end.
    first, ordered, items_at_leave = {}, set(), {}
    for f in sorted((starter / "logs/session_events").glob("*.jsonl")):
        for line in f.open():
            e = json.loads(line)
            sid = e["session"]
            if e["event"] == "saw_sold_out" and e["milk"] == "oat" and sid not in first:
                first[sid] = None
            elif sid in first and first[sid] is None and e["event"] in ("changed_milk", "abandoned_cart"):
                first[sid] = e["to"] if e["event"] == "changed_milk" else "left"
                if e["event"] == "abandoned_cart":
                    items_at_leave[sid] = e["cart_items"]
            if e["event"] == "placed_order":
                ordered.add(sid)
    outcome = Counter(first.values())
    n = len(first)
    in_tile = sum(1 for sid in items_at_leave if sid in carts and
                  (datetime.fromisoformat(carts[sid][1]) - datetime.fromisoformat(carts[sid][0])).total_seconds() >= 60)
    rejects = sum(len(f.read_text().splitlines()) for f in (starter / "logs/counter").glob("*.log"))

    print(json.dumps({
        "orders_milk_share": share,
        "orders_lines": {k: sum(c.values()) for k, c in mix.items()},
        "dashboard_rate": {**dash, "overall": overall},
        "events": {"sessions_saw_oat_sold_out": n, **{k: outcome[k] for k in ("left", "almond", "whole")},
                   "share": {k: round(outcome[k] / n, 3) for k in ("left", "almond", "whole")},
                   "switched_then_ordered": sum(1 for sid, o in first.items() if o != "left" and sid in ordered),
                   "ordered": sum(1 for sid in first if sid in ordered)},
        "leavers": {"total": len(items_at_leave), "no_cart": sum(1 for i in items_at_leave.values() if i == 0),
                    "with_cart": sum(1 for i in items_at_leave.values() if i > 0), "counted_by_tile": in_tile},
        "sellout_store_days": len(out_at),
        "counter_rejects": rejects,
    }, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
