"""Tests for InventoryManager, including a randomized check against a brute-force model."""

import random
import unittest
from decimal import Decimal

from inventory import InventoryManager, Product


def sample_inventory():
    inv = InventoryManager(seed=42)
    inv.add_product(Product("LAP-100", "Laptop 14in", "Electronics", "899.99", 12, reorder_point=5))
    inv.add_product(Product("MOU-200", "Wireless Mouse", "Electronics", "24.50", 3, reorder_point=10))
    inv.add_product(Product("PEN-300", "Gel Pens (12)", "Office", "8.99", 140, reorder_point=50))
    inv.add_product(Product("CHR-400", "Desk Chair", "Furniture", "149.00", 0, reorder_point=2))
    inv.add_product(Product("NBK-500", "Notebook", "Office", "3.25", 60, reorder_point=40))
    return inv


class TestInventoryManager(unittest.TestCase):
    def test_add_get_and_duplicates(self):
        inv = sample_inventory()
        self.assertEqual(len(inv), 5)
        self.assertEqual(inv.get("PEN-300").price, Decimal("8.99"))
        with self.assertRaises(KeyError):
            inv.add_product(Product("PEN-300", "Dup", "Office", 1, 1))

    def test_category_queries_and_change(self):
        inv = sample_inventory()
        self.assertEqual([p.sku for p in inv.products_in_category("Office")], ["NBK-500", "PEN-300"])
        inv.change_category("CHR-400", "Office")
        self.assertEqual(inv.categories(), ["Electronics", "Office"])   # empty category dropped
        self.assertEqual(inv.get("CHR-400").category, "Office")

    def test_price_range_and_update(self):
        inv = sample_inventory()
        self.assertEqual([p.sku for p in inv.products_in_price_range(5, 150)],
                         ["PEN-300", "MOU-200", "CHR-400"])
        inv.update_price("LAP-100", "99.00")
        self.assertEqual([p.sku for p in inv.products_in_price_range(99, 99)], ["LAP-100"])
        self.assertEqual(inv.cheapest(2)[0].sku, "NBK-500")

    def test_quantity_and_low_stock(self):
        inv = sample_inventory()
        # CHR-400 is 2 under, MOU-200 is 7 under -> MOU-200 most urgent.
        self.assertEqual([p.sku for p in inv.low_stock()], ["MOU-200", "CHR-400"])
        inv.adjust_quantity("MOU-200", 50)                  # restock
        inv.adjust_quantity("NBK-500", -25)                 # sale drops below reorder point
        self.assertEqual([p.sku for p in inv.low_stock()], ["NBK-500", "CHR-400"])
        self.assertEqual(inv.most_urgent().sku, "NBK-500")
        with self.assertRaises(ValueError):
            inv.adjust_quantity("CHR-400", -1)

    def test_total_value_tracks_changes(self):
        inv = sample_inventory()
        expected = sum(p.price * p.quantity for p in (inv.get(s) for s in
                       ("LAP-100", "MOU-200", "PEN-300", "CHR-400", "NBK-500")))
        self.assertEqual(inv.total_value, expected)
        inv.adjust_quantity("PEN-300", -40)
        inv.update_price("LAP-100", 799)
        inv.remove_product("MOU-200")
        expected = Decimal("799") * 12 + Decimal("8.99") * 100 + Decimal("3.25") * 60
        self.assertEqual(inv.total_value, expected)

    def test_products_are_immutable(self):
        inv = sample_inventory()
        with self.assertRaises(Exception):
            inv.get("PEN-300").quantity = 0

    def test_invalid_product_rejected(self):
        with self.assertRaises(ValueError):
            Product("X", "Bad", "Misc", "-1.00", 1)
        with self.assertRaises(ValueError):
            Product("X", "Bad", "Misc", "1.00", -1)


class TestRandomizedConsistency(unittest.TestCase):
    """Apply thousands of random operations and compare every query with a plain dict."""

    def test_against_brute_force(self):
        rng = random.Random(532)
        inv, ref = InventoryManager(seed=1), {}
        cats = ["A", "B", "C", "D"]
        next_id = 0
        for step in range(3_000):
            op = rng.random()
            if op < 0.25 or not ref:
                sku = f"S{next_id:05}"
                next_id += 1
                p = Product(sku, sku, rng.choice(cats), Decimal(rng.randint(100, 9999)) / 100,
                            rng.randint(0, 100), rng.randint(0, 30))
                inv.add_product(p)
                ref[sku] = p
            else:
                sku = rng.choice(sorted(ref))
                if op < 0.35:
                    inv.remove_product(sku)
                    del ref[sku]
                elif op < 0.6:
                    delta = rng.randint(-ref[sku].quantity, 40)
                    ref[sku] = inv.adjust_quantity(sku, delta)
                elif op < 0.8:
                    ref[sku] = inv.update_price(sku, Decimal(rng.randint(100, 9999)) / 100)
                elif op < 0.9:
                    ref[sku] = inv.change_category(sku, rng.choice(cats))
                else:
                    ref[sku] = inv.set_reorder_point(sku, rng.randint(0, 30))

            if step % 100 == 0:
                self.check(inv, ref, cats)
        self.check(inv, ref, cats)

    def check(self, inv, ref, cats):
        self.assertEqual(len(inv), len(ref))
        self.assertEqual(inv.total_value, sum((p.price * p.quantity for p in ref.values()), Decimal(0)))
        for c in cats:
            self.assertEqual(inv.products_in_category(c),
                             sorted((p for p in ref.values() if p.category == c), key=lambda p: p.sku))
        lo, hi = Decimal("20.00"), Decimal("60.00")
        self.assertEqual(inv.products_in_price_range(lo, hi),
                         sorted((p for p in ref.values() if lo <= p.price <= hi),
                                key=lambda p: (p.price, p.sku)))
        self.assertEqual(inv.low_stock(),
                         sorted((p for p in ref.values() if p.stock_gap <= 0),
                                key=lambda p: (p.stock_gap, p.sku)))


if __name__ == "__main__":
    unittest.main()
