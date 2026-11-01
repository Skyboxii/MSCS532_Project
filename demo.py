"""
Walk through a day of inventory activity using InventoryManager.

Usage:  python demo.py
"""

from inventory import InventoryManager, Product


def show(title, products):
    print(f"\n{title}")
    for p in products:
        print(f"  {p.sku:8} {p.name:18} {p.category:12} ${p.price:>8}  qty {p.quantity:>4}"
              f"  (reorder at {p.reorder_point})")


def main():
    inv = InventoryManager(seed=532)
    for p in (
        Product("LAP-100", "Laptop 14in", "Electronics", "899.99", 12, reorder_point=5),
        Product("MOU-200", "Wireless Mouse", "Electronics", "24.50", 3, reorder_point=10),
        Product("HDM-210", "HDMI Cable", "Electronics", "12.00", 45, reorder_point=15),
        Product("PEN-300", "Gel Pens (12)", "Office", "8.99", 140, reorder_point=50),
        Product("NBK-500", "Notebook", "Office", "3.25", 60, reorder_point=40),
        Product("CHR-400", "Desk Chair", "Furniture", "149.00", 0, reorder_point=2),
        Product("LMP-410", "Desk Lamp", "Furniture", "39.95", 8, reorder_point=4),
    ):
        inv.add_product(p)

    print(f"Loaded {len(inv)} products, total value ${inv.total_value:,.2f}")
    show("Needs reorder (most urgent first):", inv.low_stock())
    show("Priced $10-$50:", inv.products_in_price_range(10, 50))

    print("\n-- Receive 40 mice, sell 25 notebooks, mark down the lamp, move pens to Supplies --")
    inv.adjust_quantity("MOU-200", 40)
    inv.adjust_quantity("NBK-500", -25)
    inv.update_price("LMP-410", "29.95")
    inv.change_category("PEN-300", "Supplies")

    show("Needs reorder (most urgent first):", inv.low_stock())
    show("Priced $10-$50:", inv.products_in_price_range(10, 50))
    show("Supplies category:", inv.products_in_category("Supplies"))
    print(f"\nCategories: {', '.join(inv.categories())}")
    print(f"Total value ${inv.total_value:,.2f}")

    try:
        inv.adjust_quantity("CHR-400", -1)
    except ValueError as e:
        print(f"\nRejected sale: {e}")


if __name__ == "__main__":
    main()
