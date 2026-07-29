"""
Section 1.6 — Object-Oriented Programming Basics.

Every pipeline has three parts — extract, transform, load. Classes give
each of those parts a proper home: its own state, its own behaviour,
its own tests. This module covers:

  * The simplest class — `__init__` and instance variables.
  * Adding behaviour with methods.
  * `__repr__` for debuggable string representations.
  * Class variables — data shared across all instances.
  * Validation inside `__init__` — reject bad data at construction.

Inheritance is covered in 07_oop_inheritance.py.

Run: `python 06_oop_basics.py`
"""


# --- The simplest class ----------------------------------------------------


class Customer:
    """Represent one customer with a business rule (tier) attached.

    Instance variables — customer_id, name, total_spent — live per object.
    The method get_tier() encapsulates the tier-assignment logic.
    """

    def __init__(self, customer_id: int, name: str, total_spent: float) -> None:
        self.customer_id = customer_id
        self.name = name
        self.total_spent = total_spent

    def __repr__(self) -> str:
        return (
            f"Customer(id={self.customer_id}, name={self.name!r}, "
            f"spent={self.total_spent})"
        )

    def get_tier(self) -> str:
        if self.total_spent > 50000:
            return "Platinum"
        if self.total_spent > 20000:
            return "Gold"
        if self.total_spent > 5000:
            return "Silver"
        return "Bronze"

    def apply_discount(self, percent: float) -> float:
        return self.total_spent * (1 - percent / 100)


# --- Class variables and validation ----------------------------------------


class Order:
    """Represent one order and enforce validity rules at construction.

    Class variables:
      VALID_STATUSES     — shared status vocabulary for all Order instances.
      HIGH_VALUE_THRESHOLD — the amount above which an order is high-value.
    Both live on the class, not per instance, and can be read as
    Order.VALID_STATUSES.
    """

    VALID_STATUSES: set[str] = {"pending", "shipped", "delivered", "cancelled"}
    HIGH_VALUE_THRESHOLD: float = 10000

    def __init__(
        self,
        order_id: int,
        customer_id: int,
        amount: float,
        status: str,
    ) -> None:
        self.order_id = int(order_id)
        self.customer_id = int(customer_id)
        self.amount = float(amount)
        # Normalize status at construction — lowercase, no surrounding whitespace.
        self.status = status.strip().lower()

        # Reject impossible orders at construction rather than downstream.
        if self.amount < 0:
            raise ValueError(
                f"Order {self.order_id} has negative amount: {self.amount}"
            )

    def __repr__(self) -> str:
        return (
            f"Order(id={self.order_id}, customer={self.customer_id}, "
            f"amount={self.amount}, status={self.status!r})"
        )

    def is_high_value(self) -> bool:
        return self.amount > Order.HIGH_VALUE_THRESHOLD

    def is_valid(self) -> bool:
        return self.status in Order.VALID_STATUSES


def demo_customer_class() -> None:
    print("=" * 60)
    print("CUSTOMER CLASS")
    print("=" * 60)

    customer = Customer(3001, "Priya Mehta", 45000)
    print(customer)
    print(f"tier: {customer.get_tier()}")
    print(f"discounted spend at 10%: {customer.apply_discount(10)}")


def demo_order_class() -> None:
    print("\n" + "=" * 60)
    print("ORDER CLASS — CLASS VARIABLES + VALIDATION")
    print("=" * 60)

    orders = [
        Order(101, 201, 15000, "Pending"),
        Order(102, 202, 4000, "SHIPPED"),
        Order(103, 203, 25000, "invalid_status"),
    ]

    for order in orders:
        print(order)
        print(f"  high value : {order.is_high_value()}")
        print(f"  valid      : {order.is_valid()}")

    # Show that construction itself raises on bad data.
    print("\nAttempting to construct a negative-amount order:")
    try:
        Order(999, 999, -500, "pending")
    except ValueError as exc:
        print(f"  correctly rejected -> {exc}")


def main() -> None:
    demo_customer_class()
    demo_order_class()


if __name__ == "__main__":
    main()
