"""Product record stored in the inventory."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Product:
    """
    An immutable product record. Updates produce a new Product via
    dataclasses.replace(), so callers can never change a field behind the
    indexes' backs and leave them out of sync.

    Prices use Decimal rather than float to avoid binary rounding errors in
    currency (e.g. 0.1 + 0.2 != 0.3 with floats).
    """
    sku: str
    name: str
    category: str
    price: Decimal
    quantity: int
    reorder_point: int = 0

    def __post_init__(self):
        # Normalize price so "19.99", 19.99, and Decimal("19.99") all match.
        object.__setattr__(self, "price", Decimal(str(self.price)))
        if not self.sku:
            raise ValueError("sku is required")
        if self.price < 0:
            raise ValueError("price cannot be negative")
        if self.quantity < 0:
            raise ValueError("quantity cannot be negative")
        if self.reorder_point < 0:
            raise ValueError("reorder_point cannot be negative")

    @property
    def stock_gap(self):
        """Units above the reorder point (<= 0 means reorder now)."""
        return self.quantity - self.reorder_point
