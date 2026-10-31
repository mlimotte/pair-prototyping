import unittest

from brewboard.menu import price_cents


class PriceTest(unittest.TestCase):
    def test_medium_oat_latte(self):
        self.assertEqual(price_cents("latte", "medium", "oat"), 560)

    def test_no_milk_drink(self):
        self.assertEqual(price_cents("espresso", "double"), 400)

    def test_bad_milk(self):
        with self.assertRaises(ValueError):
            price_cents("cappuccino", "small", "almond")
