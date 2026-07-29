"""
Section 1.4 — Functions for Data Engineering.

Every pipeline you will ever build lives inside functions. This module
covers the function-writing patterns a DE must own:

  * Pure vs. impure functions and why purity matters for testability.
  * Default arguments — and the mutable-default trap that catches most
    self-taught Python developers.
  * *args and **kwargs — variable argument patterns used in logging and
    config helpers.
  * Safe dict access with .get() to survive missing keys.
  * A production-quality clean_record() reference implementation.

Run: `python 04_functions.py`
"""


# --- Pure vs. Impure -------------------------------------------------------


DISCOUNT_GLOBAL = 0.10  # only for the "impure" demo below


def calculate_price_impure(amount: float) -> float:
    """Impure — depends on the module-level DISCOUNT_GLOBAL.

    Two problems:
      1. You cannot test without setting up the global.
      2. Silent behavior change if someone else edits DISCOUNT_GLOBAL.
    """
    return amount * (1 - DISCOUNT_GLOBAL)


def calculate_price_pure(amount: float, discount: float) -> float:
    """Pure — every input the function needs is passed in explicitly.

    Same inputs always produce the same output. Easy to test.
    """
    return amount * (1 - discount)


def calculate_price_with_default(amount: float, discount: float = 0.10) -> float:
    """Pure with a sensible default — the pattern to prefer in real code."""
    return amount * (1 - discount)


# --- Safe cleaning with .get() ---------------------------------------------


def clean_record(raw: dict) -> dict:
    """Return a typed, whitespace-normalized copy of a raw record.

    Every field access uses .get() with a default so a missing key never
    crashes the pipeline. This is the production-quality version — the
    naive version that indexes with raw["field"] will crash the first
    time it sees a partial record.
    """
    return {
        "customer_id": int(raw.get("customer_id", 0)),
        "name": raw.get("name", "Unknown").strip(),
        "total_spent": float(raw.get("total_spent", 0)),
        "is_active": raw.get("is_active", "false").strip().lower() == "true",
        "country": raw.get("country", "Unknown").strip().title(),
    }


def demo_pure_vs_impure() -> None:
    print("=" * 60)
    print("PURE VS IMPURE FUNCTIONS")
    print("=" * 60)
    print(f"impure  calc(10000)              = {calculate_price_impure(10000)}")
    print(f"pure    calc(50000, 0.10)        = {calculate_price_pure(50000, 0.10)}")
    print(f"pure    calc(100000, 0.20)       = {calculate_price_pure(100000, 0.20)}")
    print(f"default calc(50000)              = {calculate_price_with_default(50000)}")
    print(f"default calc(100000, 0.20)       = {calculate_price_with_default(100000, 0.20)}")


def demo_clean_record() -> None:
    print("\n" + "=" * 60)
    print("SAFE CLEANING WITH .get()")
    print("=" * 60)

    complete = {
        "customer_id": "4021",
        "name": "  Ravi Sharma  ",
        "total_spent": "28500.00",
        "is_active": "True",
        "country": "india",
    }
    partial = {
        "customer_id": "4022",
        "name": "Sneha Patel",
        "total_spent": "15000.00",
        "is_active": "True",
        # country is missing on purpose
    }
    print("complete record:")
    print(f"  {clean_record(complete)}")
    print("partial record (country missing) — does NOT crash:")
    print(f"  {clean_record(partial)}")


# --- *args and **kwargs ----------------------------------------------------


def total_revenue(*amounts: float) -> float:
    """Accept any number of positional numeric arguments.

    Called with total_revenue(100, 200) or total_revenue(100, 200, 300, 400).
    Inside the function, `amounts` is a tuple.
    """
    return sum(amounts)


def log_event(event_type: str, **details) -> None:
    """Accept any number of named arguments — the DE logging pattern.

    Called with log_event("order_placed", order_id=5021, amount=12000).
    Inside the function, `details` is a dict.
    """
    print(f"Event: {event_type}")
    for key, value in details.items():
        print(f"  {key}: {value}")


def demo_args_kwargs() -> None:
    print("\n" + "=" * 60)
    print("*args AND **kwargs")
    print("=" * 60)

    print(f"total_revenue(100, 200, 300)         = {total_revenue(100, 200, 300)}")
    print(f"total_revenue(1020, 2030, 3040, 4050) = {total_revenue(1020, 2030, 3040, 4050)}")

    print("\nlog_event example:")
    log_event(
        "order_placed",
        order_id=5021,
        amount=12000,
        customer="Priya",
    )


# --- Mutable-default trap --------------------------------------------------


def add_tag_broken(record: dict, tags: list = []) -> dict:
    """DO NOT USE — mutable default argument is shared across calls.

    The default list is created ONCE at function definition and reused.
    Every call that relies on the default appends to the same list.
    """
    tags.append("processed")
    record["tags"] = tags
    return record


def add_tag_fixed(record: dict, tags: list | None = None) -> dict:
    """The correct pattern — use None as the default, build a new list inside.

    A fresh list is created on every call, so state does not leak between
    calls.
    """
    if tags is None:
        tags = []
    tags.append("processed")
    record["tags"] = tags
    return record


def demo_mutable_default_trap() -> None:
    print("\n" + "=" * 60)
    print("THE MUTABLE-DEFAULT TRAP")
    print("=" * 60)

    r1 = add_tag_broken({})
    r2 = add_tag_broken({})
    print(f"broken  — r1 tags: {r1['tags']}")
    print(f"broken  — r2 tags: {r2['tags']}  # shared list — WRONG")

    r3 = add_tag_fixed({})
    r4 = add_tag_fixed({})
    print(f"fixed   — r3 tags: {r3['tags']}")
    print(f"fixed   — r4 tags: {r4['tags']}  # each call gets a fresh list")


def main() -> None:
    demo_pure_vs_impure()
    demo_clean_record()
    demo_args_kwargs()
    demo_mutable_default_trap()


if __name__ == "__main__":
    main()
