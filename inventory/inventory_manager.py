"""
InventoryManager: a facade that keeps four indexes consistent.

    _products   HashTable      sku -> Product            O(1) avg lookup/update
    _by_price   SkipList       (price, sku) -> None      O(log n) price changes,
                                                         O(log n + k) range queries
    _categories HashTable      category -> set of skus   O(1) avg recategorize
    _stock      IndexedMinHeap sku -> quantity - reorder O(log n) quantity changes,
                                                         O(k) low-stock report

Every mutating method updates all affected indexes before returning, so
callers always see a consistent view.
"""

from dataclasses import replace
from decimal import Decimal

from .hash_table import HashTable
from .indexed_heap import IndexedMinHeap
from .product import Product
from .skip_list import SkipList


class InventoryManager:

    def __init__(self, seed=None):
        self._products = HashTable()
        self._by_price = SkipList(seed=seed)
        self._categories = HashTable()
        self._stock = IndexedMinHeap()
        self._total_value = Decimal("0")    # running sum of price * quantity

    # -- create / delete ------------------------------------------------------

    def add_product(self, product):
        """Add a new product to every index. O(log n) expected."""
        if product.sku in self._products:
            raise KeyError(f"SKU {product.sku!r} already exists")
        self._products.put(product.sku, product)
        self._by_price.insert((product.price, product.sku))
        self._category_set(product.category).add(product.sku)
        self._stock.push(product.sku, product.stock_gap)
        self._total_value += product.price * product.quantity

    def remove_product(self, sku):
        """Remove a product from every index and return it. O(log n) expected."""
        product = self._products.remove(sku)
        self._by_price.remove((product.price, sku))
        self._discard_from_category(product.category, sku)
        self._stock.remove(sku)
        self._total_value -= product.price * product.quantity
        return product

    # -- dynamic updates ------------------------------------------------------

    def adjust_quantity(self, sku, delta):
        """
        Apply a stock movement: positive for receiving, negative for sales.
        Rejects changes that would make quantity negative. O(log n).
        """
        product = self._products[sku]
        new_qty = product.quantity + delta
        if new_qty < 0:
            raise ValueError(f"insufficient stock for {sku}: have {product.quantity}, need {-delta}")
        updated = replace(product, quantity=new_qty)
        self._products.put(sku, updated)
        self._stock.update(sku, updated.stock_gap)
        self._total_value += product.price * delta
        return updated

    def update_price(self, sku, new_price):
        """Change a price and move the product in the price index. O(log n) expected."""
        product = self._products[sku]
        updated = replace(product, price=new_price)
        self._by_price.remove((product.price, sku))
        self._by_price.insert((updated.price, sku))
        self._products.put(sku, updated)
        self._total_value += (updated.price - product.price) * product.quantity
        return updated

    def change_category(self, sku, new_category):
        """Move a product to another category. O(1) average."""
        product = self._products[sku]
        if new_category == product.category:
            return product
        updated = replace(product, category=new_category)
        self._discard_from_category(product.category, sku)
        self._category_set(new_category).add(sku)
        self._products.put(sku, updated)
        return updated

    def set_reorder_point(self, sku, reorder_point):
        """Change when a product should be reordered. O(log n)."""
        updated = replace(self._products[sku], reorder_point=reorder_point)
        self._products.put(sku, updated)
        self._stock.update(sku, updated.stock_gap)
        return updated

    # -- queries --------------------------------------------------------------

    def get(self, sku):
        """Look up a product by SKU. O(1) average."""
        return self._products[sku]

    def products_in_category(self, category):
        """All products in a category, sorted by SKU. O(k log k)."""
        skus = self._categories.get(category, set())
        return [self._products[s] for s in sorted(skus)]

    def categories(self):
        return sorted(self._categories)

    def products_in_price_range(self, low, high):
        """Products with low <= price <= high, cheapest first. O(log n + k)."""
        low, high = Decimal(str(low)), Decimal(str(high))
        result = []
        for (price, sku), _ in self._by_price.iter_from((low, "")):
            if price > high:
                break
            result.append(self._products[sku])
        return result

    def cheapest(self, k=1):
        """The k lowest-priced products. O(k)."""
        result = []
        for (_, sku), _ in self._by_price:
            if len(result) == k:
                break
            result.append(self._products[sku])
        return result

    def low_stock(self):
        """Products at or below their reorder point, most urgent first.
        O(k log k) for k such products, independent of catalog size."""
        hits = sorted(self._stock.items_at_or_below(0), key=lambda e: (e[1], e[0]))
        return [self._products[sku] for sku, _ in hits]

    def most_urgent(self):
        """The product closest to (or furthest below) its reorder point. O(1)."""
        sku, _ = self._stock.peek()
        return self._products[sku]

    @property
    def total_value(self):
        """Inventory value (sum of price * quantity), maintained in O(1)."""
        return self._total_value

    def __contains__(self, sku):
        return sku in self._products

    def __len__(self):
        return len(self._products)

    # -- helpers --------------------------------------------------------------

    def _category_set(self, category):
        skus = self._categories.get(category)
        if skus is None:
            skus = set()
            self._categories.put(category, skus)
        return skus

    def _discard_from_category(self, category, sku):
        skus = self._categories[category]
        skus.discard(sku)
        if not skus:                    # drop empty categories
            self._categories.remove(category)
