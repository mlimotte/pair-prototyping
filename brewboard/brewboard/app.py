"""HTTP routes: the customer page and the barista board. Plain HTML forms."""
import html
import os
import uuid
from datetime import datetime
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from . import db, events, menu, orders, stock

STORE = os.environ.get("BREWBOARD_STORE", "pearl")
CARTS = {}  # sid -> list of lines (the draft before checkout)


def now():
    return datetime.now().isoformat(timespec="seconds")


def page(title, body):
    return (f"<!doctype html><meta charset=utf-8><title>{title}</title>"
            "<style>body{font:16px/1.5 system-ui;max-width:40rem;margin:2rem auto;padding:0 1rem}"
            "button{font:inherit}.out{color:#999;text-decoration:line-through}</style>"
            f"<h1>{title}</h1>{body}")


def customer_page(conn, sid):
    out = stock.sold_out(conn, STORE)
    drinks = "".join(f"<option value={d}>{m['name']}</option>" for d, m in menu.MENU.items())
    sizes = "".join(f"<option>{s}</option>" for s in menu.SIZE_DELTA)
    milks = "<option value=''>none</option>" + "".join(
        f"<option {'disabled' if m in out else ''}>{m}{' (sold out)' if m in out else ''}</option>" for m in menu.MILKS)
    cart = CARTS.get(sid, [])
    lines = "".join(f"<li>{l['drink']} {l['size']} {l.get('milk') or ''}</li>" for l in cart) or "<li>empty</li>"
    return page("Brew Board", f"""
      <form method=post action=/cart/items>
        <select name=drink>{drinks}</select> <select name=size>{sizes}</select>
        <select name=milk>{milks}</select> <button>Add</button></form>
      <h2>Cart</h2><ul>{lines}</ul>
      <form method=post action=/orders><input name=customer placeholder="Your name" required>
        <button {'disabled' if not cart else ''}>Place order</button></form>""")


def board_page(conn):
    rows = conn.execute("select * from orders where store_id = ? and status not in ('picked_up', 'cancelled') "
                        "order by order_id", (STORE,)).fetchall()
    items = "".join(f"<li>#{r['order_id']} {html.escape(r['customer_id'] or '')} · {r['status']} "
                    f"<form method=post action=/orders/{r['order_id']}/advance style=display:inline>"
                    f"<button>advance</button></form></li>" for r in rows) or "<li>no orders</li>"
    out = stock._read(conn, STORE)
    toggles = "".join(f"<form method=post action=/stock/{m}/toggle style=display:inline>"
                      f"<button class={'out' if m in out else ''}>{m}</button></form> " for m in menu.MILKS)
    return page("Board", f"<ul>{items}</ul><h2>Milks</h2>{toggles}")


class Handler(BaseHTTPRequestHandler):
    def sid(self):
        c = SimpleCookie(self.headers.get("Cookie", ""))
        return c["sid"].value if "sid" in c else None

    def send(self, body, status=200, cookie=None):
        data = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        if cookie:
            self.send_header("Set-Cookie", f"sid={cookie}; Path=/; SameSite=Lax")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, to):
        self.send_response(303)
        self.send_header("Location", to)
        self.end_headers()

    def form(self):
        n = int(self.headers.get("Content-Length", 0))
        return {k: v[0] for k, v in parse_qs(self.rfile.read(n).decode()).items()}

    def do_GET(self):
        conn = db.connect()
        if self.path == "/board":
            return self.send(board_page(conn))
        sid = self.sid() or uuid.uuid4().hex
        if self.path == "/":
            events.emit(now(), STORE, sid, None, "session_start")
            return self.send(customer_page(conn, sid), cookie=None if self.sid() else sid)
        self.send(page("Not found", ""), 404)

    def do_POST(self):
        conn, sid, f = db.connect(), self.sid(), self.form()
        parts = self.path.strip("/").split("/")
        try:
            if self.path == "/cart/items":
                line = {"drink": f["drink"], "size": f["size"], "milk": f.get("milk") or None, "qty": 1}
                orders.add_to_cart(conn, sid, STORE, line, now())
                CARTS.setdefault(sid, []).append(line)
                events.emit(now(), STORE, sid, None, "added_to_cart", **{k: line[k] for k in ("drink", "size", "milk")})
                return self.redirect("/")
            if self.path == "/orders":
                oid = orders.place_order(conn, sid, STORE, f["customer"], CARTS.pop(sid, []), now())
                events.emit(now(), STORE, sid, f["customer"], "placed_order", order_id=oid)
                return self.redirect("/")
            if parts[0] == "orders" and parts[2:] == ["advance"]:
                orders.advance(conn, int(parts[1]), now())
                return self.redirect("/board")
            if parts[0] == "stock" and parts[2:] == ["toggle"]:
                stock.toggle(conn, STORE, parts[1], now())
                return self.redirect("/board")
        except (KeyError, ValueError) as e:
            return self.send(page("Cannot do that", f"<p>{html.escape(str(e))}</p><a href=/>back</a>"), 400)
        self.send(page("Not found", ""), 404)


def serve(port=8766):
    print(f"Brew Board on http://localhost:{port}/  (barista: /board)")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
