# MSCS 532 Project – Dynamic Inventory Management

Data structures for an inventory system that handles constant changes to
product quantities, prices, and categories. Phase 1 (this deliverable) covers
design and implementation; later phases add performance testing and
optimization.

## Design

`InventoryManager` is a facade over four indexes that it keeps in sync on
every change:

| Index | Structure | Key → value | Supports | Cost |
|-------|-----------|-------------|----------|------|
| Products | `HashTable` (open addressing, linear probing) | SKU → `Product` | lookup, add, remove, update | O(1) average |
| Price | `SkipList` | (price, SKU) → – | price change, range query, cheapest-k | O(log n) expected; range O(log n + k) |
| Category | `HashTable` of sets | category → {SKU} | list category, recategorize | O(1) average per change |
| Stock alerts | `IndexedMinHeap` | SKU → quantity − reorder point | quantity change, most urgent, low-stock report | O(log n) update; O(1) peek; report O(k log k) |

`Product` is a frozen dataclass, so updates create a new record instead of
changing one in place. Prices use `Decimal` to avoid float rounding errors.
Total inventory value is maintained incrementally in O(1).

## Layout

```
inventory/
    hash_table.py         HashTable
    skip_list.py          SkipList
    indexed_heap.py       IndexedMinHeap
    product.py            Product record
    inventory_manager.py  InventoryManager facade
tests/
    test_structures.py         unit tests for each structure
    test_inventory_manager.py  manager tests + randomized brute-force consistency test
demo.py                   walkthrough of a day of inventory activity
```

## Usage

Requires Python 3.8+ (standard library only).

```bash
python demo.py
python -m unittest -v
```

```python
from inventory import InventoryManager, Product

inv = InventoryManager()
inv.add_product(Product("MOU-200", "Wireless Mouse", "Electronics", "24.50", 3, reorder_point=10))
inv.adjust_quantity("MOU-200", 40)          # receive stock
inv.update_price("MOU-200", "19.99")
inv.products_in_price_range(10, 50)
inv.low_stock()                             # products at or below reorder point
```

## References

- Knuth, D. E. (1998). *The art of computer programming, Vol. 3: Sorting and searching* (2nd ed.). Addison-Wesley.
- Pugh, W. (1990). Skip lists: A probabilistic alternative to balanced trees. *Communications of the ACM, 33*(6), 668–676.
- Williams, J. W. J. (1964). Algorithm 232: Heapsort. *Communications of the ACM, 7*(6), 347–348.
