# Brew Board architecture

- **Customer page** (`/`): pick a drink, size and milk; add to cart; place the order.
- **Barista board** (`/board`): live orders, advance each one; mark milks sold out.
- **App database** (SQLite here; Postgres in production): orders, carts, stock events.
- **POS**: every order is sent to the point-of-sale as lines. See `contracts/`.
- **Warehouse**: loaded nightly from the app database. See `warehouse/README.md`.
- **Logs**: app logs go to log storage.

Order status: placed → making → ready → picked up. A line has one milk.
