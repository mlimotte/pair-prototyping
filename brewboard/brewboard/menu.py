"""The menu. Prices are in cents."""

MENU = {
    "espresso":   {"name": "Espresso",   "base": 300, "sizes": ["single", "double"],          "milks": []},
    "americano":  {"name": "Americano",  "base": 350, "sizes": ["small", "large"],            "milks": []},
    "latte":      {"name": "Latte",      "base": 450, "sizes": ["small", "medium", "large"],  "milks": ["whole", "oat", "almond"]},
    "cappuccino": {"name": "Cappuccino", "base": 425, "sizes": ["small", "medium"],           "milks": ["whole", "oat"]},
    "mocha":      {"name": "Mocha",      "base": 500, "sizes": ["small", "medium", "large"],  "milks": ["whole", "oat", "almond"]},
    "chai":       {"name": "Chai Latte", "base": 450, "sizes": ["medium", "large"],           "milks": ["whole", "oat", "almond"]},
}

SIZE_DELTA = {"single": 0, "double": 100, "small": 0, "medium": 50, "large": 100}
MILK_DELTA = {"whole": 0, "oat": 60, "almond": 60}
MILKS = ["whole", "oat", "almond"]


def price_cents(drink, size, milk=None):
    """Return the price of one drink."""
    item = MENU[drink]
    if size not in item["sizes"]:
        raise ValueError(f"{drink} has no size {size}")
    if milk is not None and milk not in item["milks"]:
        raise ValueError(f"{drink} has no milk {milk}")
    return item["base"] + SIZE_DELTA[size] + (MILK_DELTA[milk] if milk else 0)
