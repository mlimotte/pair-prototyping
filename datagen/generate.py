"""Generate 90 days of Brew Board data with a planted truth.

    python datagen/generate.py --repo <brewboard checkout> --logs <log dir> [--truth]

Writes <repo>/data/warehouse.sqlite (via the repo's own warehouse/load.py, so the dashboard
model's SQL is what defines the metric), <repo>/inputs/, and <logs>/session_events/*.jsonl and
<logs>/counter/*.log. Deterministic: the same seed gives the same files.
"""
import argparse
import csv
import json
import random
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = 7
START, DAYS = date(2026, 7, 1), 90
STORES = {"pearl": "Pearl Street", "union": "Union Station", "river": "Riverside"}
CACHE_SECONDS = 300  # must match brewboard/stock.py CACHE_TTL_SECONDS

MENU = {
    "espresso":   ("Espresso", 300, ["single", "double"], []),
    "americano":  ("Americano", 350, ["small", "large"], []),
    "latte":      ("Latte", 450, ["small", "medium", "large"], ["whole", "oat", "almond"]),
    "cappuccino": ("Cappuccino", 425, ["small", "medium"], ["whole", "oat"]),
    "mocha":      ("Mocha", 500, ["small", "medium", "large"], ["whole", "oat", "almond"]),
    "chai":       ("Chai Latte", 450, ["medium", "large"], ["whole", "oat", "almond"]),
}
SIZE_DELTA = {"single": 0, "double": 100, "small": 0, "medium": 50, "large": 100}
MILK_DELTA = {"whole": 0, "oat": 60, "almond": 60}
DRINK_WEIGHTS = {"latte": 30, "americano": 20, "espresso": 16, "cappuccino": 12, "mocha": 12, "chai": 10}

# The planted truth: what a customer does when their milk shows as sold out.
LEAVE = {"oat": 0.35, "almond": 0.25}
SWITCH_TO = {"oat": [("almond", 50 / 65), ("whole", 15 / 65)], "almond": [("oat", 0.7), ("whole", 0.3)]}
BASELINE_ABANDON = 0.05


def price(drink, size, milk):
    return MENU[drink][1] + SIZE_DELTA[size] + (MILK_DELTA[milk] if milk else 0)


def iso(dt):
    return dt.isoformat(timespec="seconds")


def pick(rng, weighted):
    items, weights = zip(*weighted.items()) if isinstance(weighted, dict) else zip(*weighted)
    return rng.choices(items, weights)[0]


def arrival(rng, day):
    """A session start time: a morning peak over a flat day."""
    if rng.random() < 0.45:
        minutes = rng.uniform(6.5 * 60, 10 * 60)
    else:
        minutes = rng.uniform(6 * 60, 19.75 * 60)
    return datetime.combine(day, datetime.min.time()) + timedelta(minutes=minutes)


class World:
    def __init__(self, seed=SEED):
        self.rng = random.Random(seed)
        self.customers = {f"c{n:05d}": pick(self.rng, {"whole": 50, "oat": 30, "almond": 20}) for n in range(1, 3001)}
        self.customer_ids = list(self.customers)
        self.events = defaultdict(list)    # day -> event dicts
        self.counter = defaultdict(list)   # day -> log lines
        self.orders, self.lines, self.carts, self.stock = [], [], [], []
        self.next_order, self.next_cart = 40001, 1
        self.outcomes = []                 # (store, drink, milk_wanted, outcome) for --truth
        self.sellouts = []                 # (store, day, milk, at)

    def run(self):
        for d in range(DAYS):
            day = START + timedelta(days=d)
            for store in STORES:
                self.store_day(store, day)
        return self

    def store_day(self, store, day):
        rng = self.rng
        out_at = {}
        if rng.random() < 0.30:
            out_at["oat"] = datetime.combine(day, datetime.min.time()) + timedelta(minutes=rng.uniform(12 * 60, 17 * 60))
        if rng.random() < 0.08:
            out_at["almond"] = datetime.combine(day, datetime.min.time()) + timedelta(minutes=rng.uniform(13 * 60, 18 * 60))
        for milk, at in out_at.items():
            self.stock.append((store, milk, iso(at), 1))
            self.stock.append((store, milk, iso(datetime.combine(day + timedelta(days=1), datetime.min.time()) + timedelta(hours=5, minutes=50)), 0))
            self.sellouts.append((store, day.isoformat(), milk, iso(at)))
        n = max(100, int(rng.gauss(150, 15)))
        for t in sorted(arrival(rng, day) for _ in range(n)):
            self.session(store, day, t, out_at)

    def session(self, store, day, t, out_at):
        rng = self.rng
        sid = f"s{rng.getrandbits(40):010x}"
        cust = rng.choice(self.customer_ids)
        pref = self.customers[cust]
        ev = lambda ts, name, **kw: self.events[day].append({"ts": iso(ts), "store": store, "session": sid, "customer": cust, "event": name, **kw})
        truly_out = {m for m, at in out_at.items() if at <= t}
        visible_out = {m for m, at in out_at.items() if at + timedelta(seconds=CACHE_SECONDS) <= t}
        ev(t, "session_start")
        added, cart_id, cart_created = [], None, None
        for _ in range(1 if rng.random() < 0.85 else 2):
            drink = pick(rng, DRINK_WEIGHTS)
            _, _, sizes, milks = MENU[drink]
            size = rng.choice(sizes)
            milk = (pref if pref in milks else "whole") if milks else None
            t += timedelta(seconds=rng.uniform(5, 20))
            ev(t, "viewed_drink", drink=drink)
            if milk in visible_out:
                t += timedelta(seconds=rng.uniform(2, 8))
                ev(t, "saw_sold_out", milk=milk, drink=drink)
                if rng.random() < LEAVE[milk]:
                    self.outcomes.append((store, drink, milk, "left"))
                    t += timedelta(seconds=rng.uniform(5, 40))
                    ev(t, "abandoned_cart", cart_items=len(added))
                    self.close_cart(cart_id, cart_created, t, False, sid, store)
                    return
                options = [(m, w) for m, w in SWITCH_TO[milk] if m in milks and m not in visible_out] or [("whole", 1)]
                new = pick(rng, options)
                self.outcomes.append((store, drink, milk, new))
                t += timedelta(seconds=rng.uniform(3, 10))
                ev(t, "changed_milk", **{"from": milk, "to": new})
                milk = new
            t += timedelta(seconds=rng.uniform(10, 40))
            ev(t, "added_to_cart", drink=drink, size=size, milk=milk)
            if cart_id is None:
                cart_id, cart_created = self.next_cart, t
                self.next_cart += 1
            added.append((drink, size, milk))
        if rng.random() < BASELINE_ABANDON:
            t += timedelta(seconds=rng.uniform(60, 400))
            ev(t, "abandoned_cart", cart_items=len(added))
            self.close_cart(cart_id, cart_created, t, False, sid, store)
            return
        t += timedelta(seconds=rng.uniform(20, 120))
        oid = self.next_order
        self.next_order += 1
        ev(t, "placed_order", order_id=oid)
        self.close_cart(cart_id, cart_created, t, True, sid, store)
        self.order(store, day, sid, cust, oid, t, added, truly_out)

    def close_cart(self, cart_id, created, t, converted, sid, store):
        if cart_id is not None:
            self.carts.append((cart_id, sid, store, iso(created), iso(t), int(converted)))

    def order(self, store, day, sid, cust, oid, t, added, truly_out):
        rng = self.rng
        rejected = 0
        for i, (drink, size, milk) in enumerate(added, 1):
            self.lines.append((oid, i, drink, size, milk, 1, price(drink, size, milk)))
            if milk in truly_out:  # the cache showed it as available; the counter finds it gone
                alt = "almond" if milk == "oat" and "almond" in MENU[drink][3] and "almond" not in truly_out else "whole"
                action = "refund" if rng.random() < 0.5 else f"made_with_{alt}"
                rejected += action == "refund"
                at = t + timedelta(seconds=rng.uniform(60, 180))
                self.counter[day].append(f"{iso(at)} store={store} order={oid} line={i} REJECT reason=milk_unavailable milk={milk} action={action}")
        total = sum(price(*a) for a in added)
        hour_load = 1.6 if 7 <= t.hour < 10 else 1.0
        if rejected == len(added):
            self.orders.append((oid, store, sid, cust, iso(t), None, None, "cancelled", total))
            return
        ready = t + timedelta(minutes=rng.uniform(2, 6) * hour_load)
        picked = ready + timedelta(minutes=rng.uniform(1, 6))
        self.orders.append((oid, store, sid, cust, iso(t), iso(ready), iso(picked), "picked_up", total))


def truth(world):
    """Measured outcome rates for sessions that saw their milk sold out."""
    out = {}
    for milk in ("oat", "almond"):
        rows = [o for o in world.outcomes if o[2] == milk]
        c = Counter(o[3] for o in rows)
        out[milk] = {"sessions": len(rows), **{k: round(v / len(rows), 3) for k, v in sorted(c.items())}}
        with_almond = [o for o in rows if "almond" in MENU[o[1]][3]]
        if milk == "oat" and with_almond:
            c2 = Counter(o[3] for o in with_almond)
            out["oat_drinks_with_almond"] = {"sessions": len(with_almond), **{k: round(v / len(with_almond), 3) for k, v in sorted(c2.items())}}
    out["counter_rejects"] = sum(len(v) for v in world.counter.values())
    out["oat_sellout_store_days"] = sum(1 for s in world.sellouts if s[2] == "oat")
    return out


def write(world, repo, logs):
    repo, logs = Path(repo), Path(logs)
    with tempfile.TemporaryDirectory() as tmp:
        app_db = Path(tmp) / "app.db"
        con = sqlite3.connect(app_db)
        con.executescript((repo / "brewboard/db.py").read_text().split('SCHEMA = """')[1].split('"""')[0])
        con.executemany("insert into orders values (?,?,?,?,?,?,?,?,?)", sorted(world.orders))
        con.executemany("insert into order_lines values (?,?,?,?,?,?,?)", world.lines)
        con.executemany("insert into carts values (?,?,?,?,?,?)", sorted(world.carts))
        con.executemany("insert into stock_events values (?,?,?,?)", sorted(world.stock, key=lambda r: r[2]))
        con.commit()
        con.close()
        (repo / "data").mkdir(exist_ok=True)
        wh_path = repo / "data/warehouse.sqlite"
        wh_path.unlink(missing_ok=True)
        subprocess.run([sys.executable, str(repo / "warehouse/load.py"), str(app_db), str(wh_path)], check=True)
    wh = sqlite3.connect(wh_path)
    wh.execute("create table stores (store_id text, name text)")
    wh.executemany("insert into stores values (?, ?)", STORES.items())
    wh.execute("create table menu_items (drink text, name text, base_cents integer)")
    wh.executemany("insert into menu_items values (?, ?, ?)", [(d, m[0], m[1]) for d, m in MENU.items()])
    wh.commit()
    wh.close()

    for sub in ("session_events", "counter"):
        shutil.rmtree(logs / sub, ignore_errors=True)
        (logs / sub).mkdir(parents=True)
    for day, evs in world.events.items():
        (logs / "session_events" / f"{day}.jsonl").write_text("".join(json.dumps(e) + "\n" for e in sorted(evs, key=lambda e: e["ts"])))
    for day, lines in world.counter.items():
        (logs / "counter" / f"{day}.log").write_text("".join(l + "\n" for l in sorted(lines)))

    inputs = repo / "inputs"
    inputs.mkdir(exist_ok=True)
    for f in (HERE / "inputs").iterdir():
        shutil.copy(f, inputs / f.name)
    feedback(world, inputs / "customer-feedback.csv")


FEEDBACK = {
    "oat": ["Came in for an oat latte. Sold out again. Left.", "Oat was out by 2pm. Third time this month.",
            "Why does the app let me order oat when it's gone? Got a refund at the counter.",
            "Oat milk sold out, switched to almond. It was fine I guess.", "Please stock more oat milk!",
            "Ordered oat in the app, barista said they were out and made it with almond without asking."],
    "wait": ["Waited 12 minutes for a latte at the morning rush.", "Pickup shelf was a mess, couldn't find my order.",
             "Fast as usual, thanks Sam.", "Order said ready but it wasn't."],
    "price": ["Oat costs 60 cents extra?", "Prices went up again.", "Good value for a large."],
    "app": ["App is easy to use.", "Wish I could save a favorite drink.", "The app logged me out twice.",
            "Would love to pick a pickup time."],
}


def feedback(world, path):
    rng = random.Random(SEED + 1)
    oat_days = [(s, d) for s, d, m, _ in world.sellouts if m == "oat"]
    rows = []
    for _ in range(150):
        theme = pick(rng, {"oat": 30, "wait": 30, "price": 15, "app": 25})
        if theme == "oat":
            store, day = rng.choice(oat_days)
        else:
            store, day = rng.choice(list(STORES)), (START + timedelta(days=rng.randrange(DAYS))).isoformat()
        rating = rng.choice([1, 2, 2, 3]) if theme == "oat" else rng.choice([2, 3, 4, 4, 5, 5])
        rows.append((day, store, rating, rng.choice(FEEDBACK[theme])))
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "store", "rating", "text"])
        w.writerows(sorted(rows))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo")
    ap.add_argument("--logs")
    ap.add_argument("--truth", action="store_true", help="print the measured planted truth as JSON")
    a = ap.parse_args()
    world = World().run()
    if a.repo:
        write(world, a.repo, a.logs or Path(a.repo).parent / "logs")
    if a.truth or not a.repo:
        print(json.dumps(truth(world), indent=1))


if __name__ == "__main__":
    main()
