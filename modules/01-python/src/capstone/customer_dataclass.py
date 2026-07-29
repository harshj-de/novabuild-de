"""Domain model for one customer.

A `@dataclass` gives us:
  * Auto-generated __init__ from field annotations.
  * Auto-generated __repr__ for debuggable printing.
  * Equality comparison based on field values (useful in tests).

Business logic — the tier computation — is attached as a method so
callers do not need to know the tier thresholds.
"""

from dataclasses import dataclass


@dataclass
class Customer:
    """One customer with typed fields and a business rule attached."""

    id: int
    name: str
    spent: float
    status: str

    def get_tier(self) -> str:
        """Return the customer's loyalty tier based on lifetime spend."""
        if self.spent > 50000:
            return "Platinum"
        if self.spent > 20000:
            return "Gold"
        if self.spent > 5000:
            return "Silver"
        return "Bronze"


if __name__ == "__main__":
    c = Customer(id=301, name="Priya Mehta", spent=45000, status="active")
    print(c)
    print(f"tier: {c.get_tier()}")
