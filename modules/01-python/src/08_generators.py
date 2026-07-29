"""
Section 1.7 — Generators.

The single most important Python feature for Data Engineers who work
with large data. A list holds every record in memory; a generator holds
only one at a time, yielding the next when asked.

Covers:
  * `yield` and the difference between a function and a generator.
  * Calling next() manually to see the mechanic.
  * Consuming a generator with `for`.
  * Filtering generators — the pattern used to stream valid records only.
  * Chaining generators for multi-stage streaming ETL.

Run: `python 08_generators.py`
"""

from collections.abc import Iterator


# --- The problem generators solve -----------------------------------------


def read_all_orders_as_list(n: int = 10_000) -> list[dict]:
    """Naive approach — builds an entire list in memory before returning.

    For 10 million records this becomes several GB and may crash the process.
    Kept small (n=10_000) here so it does not eat your laptop.
    """
    orders = []
    for i in range(n):
        orders.append({"order_id": i, "amount": i * 10})
    return orders


def generate_orders(n: int = 10_000) -> Iterator[dict]:
    """Generator version — one order at a time.

    Notice `yield` instead of `return`. The function does not execute
    to completion when called; it returns a generator object that
    produces values on demand.
    """
    for i in range(n):
        yield {"order_id": i, "amount": i * 10}


def demo_generator_basics() -> None:
    print("=" * 60)
    print("GENERATOR BASICS")
    print("=" * 60)

    # Calling the function does not run the loop yet — it returns a generator.
    orders = generate_orders(n=5)
    print(f"generator object: {orders}")

    # Manually pull records with next().
    print(f"next(orders): {next(orders)}")
    print(f"next(orders): {next(orders)}")
    print(f"next(orders): {next(orders)}")

    # The real way — consume with a for loop.
    print("\nfor loop over a fresh generator:")
    for order in generate_orders(n=3):
        print(f"  {order}")


# --- Filtering generator — the streaming ETL pattern ---------------------


def valid_orders(orders: list[dict]) -> Iterator[dict]:
    """Yield only orders whose status is in the valid set.

    Skips invalid ones silently. This is the streaming-filter pattern —
    consumers of this generator never see the bad records.
    """
    valid_statuses = {"pending", "shipped", "delivered", "cancelled"}
    for order in orders:
        if order.get("status") in valid_statuses:
            yield order


def demo_filtering_generator() -> None:
    print("\n" + "=" * 60)
    print("FILTERING GENERATOR")
    print("=" * 60)

    orders = [
        {"order_id": 101, "amount": 15000, "status": "pending"},
        {"order_id": 102, "amount": 4000, "status": "invalid"},
        {"order_id": 103, "amount": 8000, "status": "shipped"},
        {"order_id": 104, "amount": 22000, "status": "bad_status"},
        {"order_id": 105, "amount": 3000, "status": "delivered"},
    ]

    # Total revenue from valid orders only.
    # sum(...) can consume a generator directly — no intermediate list.
    total = sum(order["amount"] for order in valid_orders(orders))
    print(f"total revenue from valid orders: {total}")


# --- Chained generators — multi-stage streaming ETL ---------------------


def parse_lines(lines: Iterator[str]) -> Iterator[dict]:
    """Turn raw CSV-like lines into dicts."""
    for line in lines:
        parts = line.strip().split(",")
        if len(parts) != 3:
            continue
        yield {"order_id": parts[0], "amount": parts[1], "status": parts[2]}


def normalise_amounts(records: Iterator[dict]) -> Iterator[dict]:
    """Coerce amount to float and skip records that cannot convert."""
    for record in records:
        try:
            record["amount"] = float(record["amount"])
        except ValueError:
            continue
        yield record


def demo_chained_generators() -> None:
    """Three stages, connected by generators, processing records lazily.

    Nothing is materialised in memory except one record at a time as
    it flows through the chain. This is the exact pattern used in
    real streaming ETL jobs.
    """
    print("\n" + "=" * 60)
    print("CHAINED GENERATORS")
    print("=" * 60)

    raw_lines = iter(
        [
            "101,15000,pending",
            "102,bad,invalid",
            "103,8000,shipped",
            "malformed_line",
            "105,3000.50,delivered",
        ]
    )

    pipeline = normalise_amounts(parse_lines(raw_lines))

    for record in pipeline:
        print(f"  {record}")


def main() -> None:
    demo_generator_basics()
    demo_filtering_generator()
    demo_chained_generators()


if __name__ == "__main__":
    main()
