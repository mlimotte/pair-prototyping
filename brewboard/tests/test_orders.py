import unittest

from brewboard import db, orders, stock


class OrderTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        stock._cache.clear()

    def test_place_and_advance(self):
        line = {"drink": "latte", "size": "small", "milk": "whole", "qty": 1}
        orders.add_to_cart(self.conn, "s1", "pearl", line, "2026-07-01T08:00:00")
        oid = orders.place_order(self.conn, "s1", "pearl", "Ada", [line], "2026-07-01T08:01:00")
        self.assertEqual(orders.advance(self.conn, oid, "2026-07-01T08:02:00"), "making")
        cart = self.conn.execute("select converted from carts where session_id = 's1'").fetchone()
        self.assertEqual(cart["converted"], 1)

    def test_sold_out_milk_rejected(self):
        stock.toggle(self.conn, "pearl", "oat", "2026-07-01T08:00:00")
        with self.assertRaises(ValueError):
            orders.add_to_cart(self.conn, "s1", "pearl", {"drink": "latte", "size": "small", "milk": "oat"},
                               "2026-07-01T08:00:30")
