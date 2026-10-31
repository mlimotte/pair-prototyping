"""Carts and orders."""
from . import menu, stock

FLOW = ["placed", "making", "ready", "picked_up"]


def add_to_cart(conn, session_id, store_id, line, at):
    """Add a line to the session's cart; create the cart on the first add."""
    menu.price_cents(line["drink"], line["size"], line.get("milk"))
    if line.get("milk") in stock.sold_out(conn, store_id):
        raise ValueError(f"{line['milk']} is sold out")
    cart = conn.execute("select cart_id from carts where session_id = ? and converted = 0", (session_id,)).fetchone()
    if cart is None:
        cur = conn.execute("insert into carts (session_id, store_id, created_at, last_activity_at, converted) "
                           "values (?, ?, ?, ?, 0)", (session_id, store_id, at, at))
        cart_id = cur.lastrowid
    else:
        cart_id = cart["cart_id"]
        conn.execute("update carts set last_activity_at = ? where cart_id = ?", (at, cart_id))
    conn.commit()
    return cart_id


def place_order(conn, session_id, store_id, customer_id, lines, at):
    """Turn the session's cart into an order. Return the order id."""
    total = sum(menu.price_cents(l["drink"], l["size"], l.get("milk")) * l.get("qty", 1) for l in lines)
    cur = conn.execute("insert into orders (store_id, session_id, customer_id, placed_at, status, total_cents) "
                       "values (?, ?, ?, ?, 'placed', ?)", (store_id, session_id, customer_id, at, total))
    order_id = cur.lastrowid
    for i, l in enumerate(lines, 1):
        conn.execute("insert into order_lines values (?, ?, ?, ?, ?, ?, ?)",
                     (order_id, i, l["drink"], l["size"], l.get("milk"), l.get("qty", 1),
                      menu.price_cents(l["drink"], l["size"], l.get("milk"))))
    conn.execute("update carts set converted = 1, last_activity_at = ? where session_id = ? and converted = 0",
                 (at, session_id))
    conn.commit()
    return order_id


def advance(conn, order_id, at):
    """Barista action: move an order one step along FLOW."""
    status = conn.execute("select status from orders where order_id = ?", (order_id,)).fetchone()["status"]
    if status not in FLOW[:-1]:
        return status
    nxt = FLOW[FLOW.index(status) + 1]
    col = {"ready": "ready_at", "picked_up": "picked_up_at"}.get(nxt)
    conn.execute(f"update orders set status = ?{f', {col} = ?' if col else ''} where order_id = ?",
                 (nxt, at, order_id) if col else (nxt, order_id))
    conn.commit()
    return nxt
