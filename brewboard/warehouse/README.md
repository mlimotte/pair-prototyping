# Warehouse

`warehouse.sqlite` is rebuilt each night by `load.py` from the app database. BI and the ops dashboard read it.

| Table | What |
|---|---|
| `stores`, `menu_items` | reference data |
| `orders`, `order_lines` | every order and its lines |
| `carts` | carts, converted or not |
| `stock_events` | the barista's sold-out toggles |
| `metric_daily_abandonment` | model: daily abandonment rate per store (the dashboard tile) |
