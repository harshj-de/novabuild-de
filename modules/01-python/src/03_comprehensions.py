"""
Section 1.3 — Comprehensions (the DE shortcut).

Comprehensions turn multi-line loop-and-append patterns into single
readable expressions. They are the Python equivalent of `.map()` and
`.filter()` in other languages, and they show up constantly in DE code
(especially inside pandas .apply() and PySpark transformations).

Covers:
  * List comprehensions (basic mapping).
  * Filtered list comprehensions (map + filter combined).
  * Dict comprehensions (building lookup tables).
  * Set comprehensions (deduplication).
  * When NOT to use one — readability limits.

Run: `python 03_comprehensions.py`
"""


def categorise_customer(total_spent: float) -> str:
    """Loyalty tier — same helper as module 02, kept here for standalone runs."""
    if total_spent > 50000:
        return "Platinum"
    if total_spent > 20000:
        return "Gold"
    if total_spent > 5000:
        return "Silver"
    return "Bronze"


def demo_list_comprehension_mapping() -> None:
    """Turn a list of records into a list of transformed values."""
    print("=" * 60)
    print("LIST COMPREHENSION — MAPPING")
    print("=" * 60)

    customers = [
        {"name": "Priya", "total_spent": 62000},
        {"name": "Arjun", "total_spent": 25000},
        {"name": "Sneha", "total_spent": 4200},
        {"name": "Rahul", "total_spent": 180000},
        {"name": "Divya", "total_spent": 9500},
    ]

    # Loop version (3 lines):
    #   tiers = []
    #   for c in customers:
    #       tiers.append(categorise_customer(c["total_spent"]))

    # Comprehension (1 line):
    tiers = [categorise_customer(c["total_spent"]) for c in customers]
    print(f"tiers: {tiers}")


def demo_list_comprehension_filtering() -> None:
    """Filter + map in one line — the classic pipeline pattern."""
    print("\n" + "=" * 60)
    print("LIST COMPREHENSION — FILTERING")
    print("=" * 60)

    customers = [
        {"name": "Priya", "total_spent": 62000},
        {"name": "Arjun", "total_spent": 25000},
        {"name": "Sneha", "total_spent": 4200},
        {"name": "Rahul", "total_spent": 180000},
        {"name": "Divya", "total_spent": 9500},
    ]

    top_customers = [
        c["name"]
        for c in customers
        if categorise_customer(c["total_spent"]) in ("Gold", "Platinum")
    ]
    print(f"top customers (Gold or Platinum): {top_customers}")


def demo_dict_comprehension() -> None:
    """Build a lookup table — name to tier."""
    print("\n" + "=" * 60)
    print("DICT COMPREHENSION — LOOKUP TABLE")
    print("=" * 60)

    customers = [
        {"name": "Priya", "total_spent": 62000},
        {"name": "Arjun", "total_spent": 25000},
        {"name": "Sneha", "total_spent": 4200},
    ]
    tier_map = {c["name"]: categorise_customer(c["total_spent"]) for c in customers}
    print(f"tier_map: {tier_map}")


def demo_order_processing() -> None:
    """Two comprehensions on the same source — classic filter + build-map."""
    print("\n" + "=" * 60)
    print("ORDER PROCESSING — TWO COMPREHENSIONS")
    print("=" * 60)

    orders = [
        {"order_id": 101, "amount": 4500, "status": "delivered"},
        {"order_id": 102, "amount": 12000, "status": "pending"},
        {"order_id": 103, "amount": 800, "status": "delivered"},
        {"order_id": 104, "amount": 23000, "status": "cancelled"},
        {"order_id": 105, "amount": 6700, "status": "delivered"},
    ]

    # Amounts of delivered orders only.
    delivered_amounts = [o["amount"] for o in orders if o["status"] == "delivered"]
    print(f"delivered amounts: {delivered_amounts}")

    # Lookup: order_id -> amount (all orders).
    order_amount_map = {o["order_id"]: o["amount"] for o in orders}
    print(f"order_amount_map: {order_amount_map}")


def demo_set_comprehension() -> None:
    """Deduplicate on the fly."""
    print("\n" + "=" * 60)
    print("SET COMPREHENSION — DEDUPLICATION")
    print("=" * 60)

    records = [
        {"country": "India"},
        {"country": "USA"},
        {"country": "india"},
        {"country": "USA"},
        {"country": "UK"},
    ]

    unique_countries = {r["country"].strip().title() for r in records}
    print(f"unique_countries: {unique_countries}")


def demo_when_not_to_use() -> None:
    """The readability line — when to fall back to a plain loop."""
    print("\n" + "=" * 60)
    print("WHEN NOT TO USE A COMPREHENSION")
    print("=" * 60)

    # This is hard to read — three conditions and a computation.
    orders = [
        {"order_id": 1, "amount": 5000, "status": "delivered", "region": "IN"},
        {"order_id": 2, "amount": 12000, "status": "pending", "region": "US"},
    ]

    # Overloaded comprehension — technically works, but reviewer hostile.
    result = [
        o["amount"] * 0.9
        for o in orders
        if o["status"] == "delivered" and o["region"] == "IN" and o["amount"] > 1000
    ]

    # Same logic as a loop — more readable when logic gets busy.
    result_loop = []
    for o in orders:
        if o["status"] != "delivered":
            continue
        if o["region"] != "IN":
            continue
        if o["amount"] <= 1000:
            continue
        result_loop.append(o["amount"] * 0.9)

    print(f"comprehension result: {result}")
    print(f"loop result:          {result_loop}")
    print("Rule of thumb: if it wraps to a second line, use a loop.")


def main() -> None:
    demo_list_comprehension_mapping()
    demo_list_comprehension_filtering()
    demo_dict_comprehension()
    demo_order_processing()
    demo_set_comprehension()
    demo_when_not_to_use()


if __name__ == "__main__":
    main()
