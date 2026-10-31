# Brew Board

Order coffee ahead. Baristas see a live board.

```bash
python -m brewboard        # http://localhost:8766/  (barista: /board)
python -m unittest         # tests
```

- `brewboard/`: the app (menu, stock, carts and orders, session events, routes)
- `warehouse/`: the nightly load and the dashboard models
- `contracts/`: what the POS accepts
- `docs/`: architecture and postmortems
- `data/`: `warehouse.sqlite`, a copy of the warehouse for analysis
- `inputs/`: notes and feedback from the product side
