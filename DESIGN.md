# DESIGN: the Backlog learning series

The contract for everything in this folder. It turns the approved spec (kept elsewhere) into names, numbers and files.

## What this is

A series of 7 interactive posts that teach pair prototyping and the loop, for engineers first. Posts use Learning-Kit's machinery (figures, predict-then-reveal, recall cards, warm-ups, review), copied into `kit/`. A local Python server builds and serves the site, and runs `claude -p` for part 2's live example.

Brew Board is the setting, not the subject. The learner never builds it. Agents change it in the exercises.

## Layout

| Path | Holds |
|---|---|
| `serve.py` | `build` (site → `_site/`), `serve` (build, then serve on port **8765** with the API) |
| `learning.json` | title, headline, tagline, parts |
| `kit/assets/`, `kit/pages/` | copied from Learning-Kit, edited here (no dependency) |
| `site/` | `intro.html`, `posts/NN-slug.html`, `viz/NN-slug.js`, `cards/NN.js`, `wild/NN.js`, `static/` |
| `brewboard/` | the Brew Board repo template: app, warehouse models, docs, tests |
| `datagen/generate.py` | writes the 90-day data into a Brew Board checkout (deterministic, seed 7) |
| `starters/make_starter.py` | builds a part's starter folder: a git repo with history, the data, the exercise, a grader skill |
| `starters/partNN/` | `EXERCISE.md`, `grader.md` (the rubric), any extra files for that part |
| `tools/` | `record_part2.py`, `record_part4.py` (capture real agent runs as page data), `check/` (headless-Chrome check) |

Python 3.11+, standard library only. The server, the app and the generator need no install.

## The fictional org

A small coffee company that runs Brew Board, its ordering app, in three stores. No real company names or branding.

| Who | Role |
|---|---|
| **Morgan** | product owner for ordering (writes the raw inputs, asks the questions) |
| **Sam** | barista at Pearl Street (marks milks sold out, writes the barista notes) |
| **Ada, Grace, Linus** | toy customers in the live app |
| **the learner** | the engineer paired with Morgan |
| **Jo** | the engineer who started the abandoned `substitutions` branch |

## The domain (from the Datastar Brew Board, in Python)

Menu, prices in cents. Sizes and milks in the order shown.

| id | name | base | sizes | milks |
|---|---|---|---|---|
| `espresso` | Espresso | 300 | single, double | none |
| `americano` | Americano | 350 | small, large | none |
| `latte` | Latte | 450 | small, medium, large | whole, oat, almond |
| `cappuccino` | Cappuccino | 425 | small, medium | whole, oat |
| `mocha` | Mocha | 500 | small, medium, large | whole, oat, almond |
| `chai` | Chai Latte | 450 | medium, large | whole, oat, almond |

Size deltas: single 0, double 100, small 0, medium 50, large 100. Milk deltas: whole 0, oat 60, almond 60. `price_cents(latte, medium, oat)` = 560.

Order status: `placed → making → ready → picked_up`; also `cancelled`. Sold-out applies to milks only.

## The planted truth

**When oat sells out, 35% of the sessions that wanted oat abandon. The other 65% switch: to almond where the drink offers it (50 of the 65), else to whole.** For drinks with almond: 35% leave, 50% almond, 15% whole. For cappuccino (no almond): 35% leave, 65% whole.

The generator draws these with a seeded RNG, so the measured rates land near, not on, the targets. `datagen/generate.py --truth` prints the measured rates; the grader uses those numbers, with a tolerance of ±5 points.

The orders table cannot show this: it holds only the people who stayed.

## The planted flaws

Things a product person's agent cannot see from documents. The engineer's agent finds them in parts 4 and 5.

| # | Flaw | Where it lives | What it does to the numbers |
|---|---|---|---|
| F1 | Session events are not in the warehouse | `brewboard/events.py` writes `logs/session_events/YYYY-MM-DD.jsonl`; `warehouse/load.py` does not load them | The only place `saw_sold_out` and pre-cart abandons exist |
| F2 | Sold-out status is cached for 5 minutes | `brewboard/stock.py`, `CACHE_TTL_SECONDS = 300` | For 5 minutes after Sam marks a milk out, customers still order it. The counter rejects those lines: `logs/counter/YYYY-MM-DD.log` |
| F3 | An abandoned `substitutions` branch | git branch `substitutions` in the starter repo, `NOTES.md` on it | Jo stopped because the POS contract rejects a modified line |
| F4 | The dashboard abandonment metric leaves out carts open under 60 s | `warehouse/models/metric_daily_abandonment.sql` (`where open_seconds >= 60`, comment "drop bounces") | Most sold-out abandons are fast or have no cart, so the dashboard barely moves on sell-out days |

Also planted, for the part 4 sidebar and part 7:
- `contracts/pos_order_line.schema.json`: one `milk`, `additionalProperties: false`, no "substituted" field.
- `docs/postmortems/2026-03-14-sold-out-double-charge.md`: the sold-out flag once caused double charges.
- Counter substitutions: when the counter rejects an oat line, Sam makes it with almond in half the cases. The order line still says `oat`.

## The data (written by `datagen/generate.py`)

90 days, 2026-07-01 to 2026-09-28. Stores `pearl` (Pearl Street), `union` (Union Station), `river` (Riverside). Open 06:00 to 20:00, morning peak. About 150 sessions per store per day.

Sell-outs: oat sells out on 30% of store-days, at a time between 12:00 and 17:00, until close. Almond on 8%. Whole never. Restock at open.

### `warehouse.sqlite` (what BI sees)

| Table | Columns |
|---|---|
| `stores` | `store_id, name` |
| `menu_items` | `drink, name, base_cents` |
| `orders` | `order_id, store_id, session_id, customer_id, placed_at, ready_at, picked_up_at, status, total_cents` |
| `order_lines` | `order_id, line_no, drink, size, milk, qty, price_cents` |
| `carts` | `cart_id, session_id, store_id, created_at, last_activity_at, converted` (a cart exists only after the first add) |
| `stock_events` | `store_id, milk, at, sold_out` (Sam's toggles) |
| `metric_daily_abandonment` | `day, store_id, carts, abandoned, rate` (materialized by running the model's SQL) |

Timestamps are ISO 8601 local time, no zone.

### `logs/` (not in the warehouse)

- `session_events/YYYY-MM-DD.jsonl`: one JSON object per line: `{"ts", "store", "session", "customer", "event", ...}`. Events: `session_start`, `viewed_drink {drink}`, `saw_sold_out {milk, drink}`, `changed_milk {from, to}`, `added_to_cart {drink, size, milk}`, `abandoned_cart {cart_items}`, `placed_order {order_id}`. Every abandoned session ends in `abandoned_cart`, with `cart_items` 0 when nothing was added.
- `counter/YYYY-MM-DD.log`: `2026-08-14T14:07:33 store=pearl order=48211 line=1 REJECT reason=milk_unavailable milk=oat action=refund|made_with_almond`.

### `inputs/` (Morgan's raw material)

- `customer-feedback.csv`: `date, store, rating, text` (about 150 rows; themes: oat sold out, waits, price, app).
- `barista-notes.md`: Sam's complaints (people order oat after it is marked out).
- `six-page-doc.md`: an AI-written proposal, "Smart Milk Substitution". Long, confident, mostly invented. Part 2 cuts it down.

## The Brew Board app (`brewboard/`)

A small, runnable app: `python -m brewboard` serves the customer page `/` and the barista board `/board` on port **8766**. Plain HTML forms, SQLite, the standard library. `python -m unittest` runs its tests. It exists so that prototypes (part 5) and the feature (part 7) land in real code with tests.

## Parts

| # | Slug | Title | Status |
|---|---|---|---|
| 1 | `constraint` | The constraint moves | later |
| 2 | `prompt` | Give me the prompt | first |
| 3 | `lineage` | An old loop | later |
| 4 | `pair` | Pair prototyping | first |
| 5 | `lock` | Lock as you learn | later |
| 6 | `gates` | Gates | later |
| 7 | `payoff` | It gets built | later |

## Part 2's live example

`POST /api/expand {prompt, mode}` runs `claude -p` (no tools, no user settings, a temp working directory) and returns the text. `mode` is `plain` ("write a spec") or `guided` (a spec-kit-style template: mark each unknown `[NEEDS CLARIFICATION: question]`, never guess). `POST /api/attribute {prompt, output}` runs a second pass that labels each sentence `prompt` or `invented`, as JSON. `GET /api/health` says whether `claude` is on the PATH.

The page works without the server: it shows recorded runs from `site/static/data/part2-runs.json` (captured by `tools/record_part2.py`, real outputs, not hand-written), and the live button appears only when `/api/health` answers.

## Part 4's question

"When oat sells out, do customers switch or leave?" The figure computes from the generated data (`tools/export_part4.py` → `site/static/data/part4.json`): what the orders table shows, what the dashboard shows, what the session events show. Measured per session: 477 sessions saw oat sold out; 166 (34.8%) left, 201 switched to almond, 110 to whole. The tile counts 1 of the 166 (156 had no cart) and is lower on sell-out days (7.1%) than other days (7.7%).

The second figure shows real agent runs (`tools/record_part4.py`, two per setup). Setups:

| Arm | Works in | Logs announced (`--add-dir ../logs`) | Pointer | Result (2026-10-29) |
|---|---|---|---|---|
| `product` | `product/` (warehouse copy, inputs, docs) | no | no | wrong both runs: "mostly switch", ≤4% leave |
| `quiet` | `brewboard/` | no | no | wrong both runs: "little sign of leaving" |
| `quiet-pointer` | `brewboard/` | no | "Check the session events in ../logs, not only the orders." | right both runs: ~35% |
| `none` | `brewboard/` | yes | no | right both runs: the announcement is itself a pointer |
| `pointer` | `brewboard/` | yes | "Check the session events, not only the orders." | right both runs |

The post and the exercise use `product`, `quiet`, `quiet-pointer`; the `--add-dir` result is an aside. If the recordings are redone, re-check every number the posts quote.

## Conventions

- Fictional org, Python examples, no real company branding.
- Posts in Simplified Technical English, dense and literal. A claim about Boehm, Cagan or a real template has a source link.
- Recorded agent output is shown as recorded, with the date and the model. Never edit it.
