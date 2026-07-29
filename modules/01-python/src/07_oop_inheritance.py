"""
Section 1.6 (continued) — Inheritance.

Where OOP earns its keep in a DE codebase. If you need three pipelines —
Orders, Customers, Products — all with the same logging, error tracking,
and summary behavior, inheritance lets you write that once in a base
class. Each specialised pipeline inherits it automatically.

Covers:
  * Writing a BasePipeline parent.
  * Child classes with `super().__init__()`.
  * Method overriding — child's version replaces parent's.
  * Calling the parent from within an overridden method via `super()`.
  * Polymorphism — a heterogeneous list of children handled uniformly.

Run: `python 07_oop_inheritance.py`
"""


# --- The parent -----------------------------------------------------------


class BasePipeline:
    """Common behaviour every pipeline needs.

    Every pipeline logs, counts errors, and shows a summary. Writing it
    here once means each specialised pipeline inherits it for free.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.errors = 0
        self.high_value_count = 0  # only used by children that care

    def log(self, message: str) -> None:
        print(f"[{self.name}] {message}")

    def summary(self) -> None:
        print(f"[{self.name}] Summary — errors: {self.errors}")


# --- Children -------------------------------------------------------------


class OrderPipeline(BasePipeline):
    """Process a batch of order dicts.

    Inherits log(), summary(), and error tracking from BasePipeline.
    Adds a specialised run() and overrides summary() to include
    high-value count.
    """

    HIGH_VALUE_THRESHOLD = 10000

    def __init__(self) -> None:
        super().__init__("OrderPipeline")

    def run(self, orders: list[dict]) -> None:
        self.log("Starting")
        for order in orders:
            self.log(f"Processing order {order['order_id']}")
            if order["amount"] > self.HIGH_VALUE_THRESHOLD:
                self.high_value_count += 1
        self.log("Finished")
        self.summary()

    def summary(self) -> None:
        # First call the parent's summary...
        super().summary()
        # ...then add child-specific detail.
        print(f"[{self.name}] High-value orders: {self.high_value_count}")


class CustomerPipeline(BasePipeline):
    """Process a batch of customer dicts.

    Does not need to override summary() — the parent's version is enough.
    """

    def __init__(self) -> None:
        super().__init__("CustomerPipeline")

    def run(self, customers: list[dict]) -> None:
        self.log("Starting")
        for customer in customers:
            self.log(f"Processing customer {customer['name']}")
        self.log("Finished")
        self.summary()


# --- Second inheritance example: consumer product hierarchy --------------
# Uses the Phone / SamsungPhone / IPhone example from the original notebook
# to reinforce the same pattern in a non-pipeline context.


class Phone:
    def __init__(self, brand: str, battery: int) -> None:
        self.brand = brand
        self.battery = battery

    def make_call(self, number: str) -> None:
        print(f"[{self.brand}] calling {number}")

    def charge(self, amount: int) -> None:
        self.battery = min(self.battery + amount, 100)
        print(f"[{self.brand}] battery now {self.battery}%")


class SamsungPhone(Phone):
    def __init__(self, battery: int) -> None:
        super().__init__("Samsung", battery)
        self.camera_mode = "normal"

    def switch_camera(self, mode: str) -> None:
        self.camera_mode = mode
        print(f"Samsung camera switched to {mode}")


class IPhone(Phone):
    def __init__(self, battery: int) -> None:
        super().__init__("iPhone", battery)
        self.face_id_enabled = False

    def enable_face_id(self) -> None:
        self.face_id_enabled = True
        print("iPhone Face ID enabled")

    # Overriding make_call — child chooses different behaviour than parent.
    def make_call(self, number: str) -> None:
        if self.face_id_enabled:
            print(f"iPhone verified your face, calling {number}")
        else:
            print(f"iPhone calling {number} without verification")


def demo_pipelines() -> None:
    print("=" * 60)
    print("INHERITANCE — PIPELINES")
    print("=" * 60)

    orders = [
        {"order_id": 101, "amount": 15000},
        {"order_id": 102, "amount": 4000},
        {"order_id": 103, "amount": 22000},
    ]
    customers = [{"name": "Priya Mehta"}, {"name": "Arjun Patel"}]

    OrderPipeline().run(orders)
    print()
    CustomerPipeline().run(customers)


def demo_polymorphism() -> None:
    """A list of different Phone subclasses, treated uniformly."""
    print("\n" + "=" * 60)
    print("POLYMORPHISM — MIXED PHONE LIST")
    print("=" * 60)

    phones: list[Phone] = [
        Phone("Nokia", 90),
        SamsungPhone(40),
        IPhone(80),
    ]

    # Every phone responds to make_call(), but each does it its own way.
    for phone in phones:
        phone.make_call("9999999999")


def main() -> None:
    demo_pipelines()
    demo_polymorphism()


if __name__ == "__main__":
    main()
