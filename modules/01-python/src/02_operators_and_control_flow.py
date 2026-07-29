"""
Section 1.2–1.3 — Operators, Boolean Logic, and Control Flow.

Every filter in a pipeline is an operator. Every business rule —
"flag orders above rupees 10,000" or "skip records where status is
null" — is a combination of operators. This module demonstrates:

  * Arithmetic operators including floor division and modulo.
  * Boolean operators (and, or, not) applied to record filtering.
  * Membership tests (`in`) against a set of valid values.
  * Conditional branching and the customer-tier pattern.
  * for / while loops including retry-with-backoff.

Run: `python 02_operators_and_control_flow.py`
"""


def demo_arithmetic() -> None:
    """Arithmetic operators with focus on floor division and modulo."""
    print("=" * 60)
    print("ARITHMETIC OPERATORS")
    print("=" * 60)

    revenue = 15000
    tax_rate = 0.18
    tax = revenue * tax_rate
    print(f"tax on {revenue} at {tax_rate*100}% = {tax}")

    # Floor division and modulo — used constantly for batching.
    print(f"17 // 3 = {17 // 3}  # floor division")
    print(f"17 %  3 = {17 % 3}  # modulo (remainder)")

    # Practical DE use — batching every N records.
    print("\nProcess every even-numbered row:")
    for i in range(1, 11):
        if i % 2 == 0:
            print(f"  Row {i} — process this batch")


def calculate_discounted_price(original_price: float, discount_percent: float) -> float:
    """Return the price after applying a percentage discount.

    Single-expression form — the pattern used inside DataFrame `.apply()`
    and list comprehensions later.
    """
    return original_price * (1 - discount_percent / 100)


def demo_boolean_logic() -> None:
    """Boolean operators combined with dict access — every filter in a pipeline."""
    print("\n" + "=" * 60)
    print("BOOLEAN LOGIC ON A RECORD")
    print("=" * 60)

    record = {
        "order_id": 5021,
        "amount": 4500,
        "status": "processing",
        "is_verified": True,
    }
    valid_statuses = {"pending", "shipped", "delivered", "cancelled", "processing"}

    # Business rules expressed as boolean expressions.
    free_shipping = record["amount"] > 3000 and record["is_verified"]
    status_valid = record["status"] in valid_statuses
    needs_review = record["amount"] > 10000 or not record["is_verified"]

    print(f"Free shipping : {free_shipping}")
    print(f"Status valid  : {status_valid}")
    print(f"Needs review  : {needs_review}")


def categorise_customer(total_spent: float) -> str:
    """Assign a loyalty tier based on lifetime spend.

    Classic tier table — the reusable version of a hardcoded if/elif block.
    Used across the module in loops and comprehensions.
    """
    if total_spent > 50000:
        return "Platinum"
    if total_spent > 20000:
        return "Gold"
    if total_spent > 5000:
        return "Silver"
    return "Bronze"


def demo_conditional_branching() -> None:
    """The classic if/elif/else tier pattern."""
    print("\n" + "=" * 60)
    print("CONDITIONAL BRANCHING")
    print("=" * 60)

    customers = [72000, 32000, 8000, 1500]
    for amount in customers:
        tier = categorise_customer(amount)
        print(f"Spent: {amount:>6}  ->  {tier}")


def demo_for_loop_with_enumerate() -> None:
    """Enumerate — when you need both the index and the value."""
    print("\n" + "=" * 60)
    print("FOR LOOP + ENUMERATE")
    print("=" * 60)

    orders = [
        {"order_id": 1, "amount": 4500, "status": "delivered"},
        {"order_id": 2, "amount": 12000, "status": "pending"},
        {"order_id": 3, "amount": 800, "status": "delivered"},
    ]

    for index, order in enumerate(orders):
        print(f"Row {index}: order {order['order_id']}, amount {order['amount']}")


def demo_while_with_retry() -> None:
    """Retry pattern — while loop with exception handling.

    In production every network call needs retry logic. This is the
    template most pipelines start with (then evolve into `tenacity`
    or `backoff` libraries for exponential retry with jitter).
    """
    print("\n" + "=" * 60)
    print("WHILE LOOP WITH RETRY")
    print("=" * 60)

    def fetch_data(attempt: int) -> dict:
        if attempt < 3:
            raise ConnectionError("API not responding")
        return {"records": 100}

    max_retries = 5
    attempt = 0
    while attempt < max_retries:
        try:
            result = fetch_data(attempt)
            print(f"Success on attempt {attempt + 1}: {result}")
            break
        except ConnectionError:
            attempt += 1
            print(f"Attempt {attempt} failed — retrying...")


def demo_customer_pipeline() -> None:
    """Combine loops, conditionals, and function calls on a batch."""
    print("\n" + "=" * 60)
    print("PROCESS A BATCH OF CUSTOMERS")
    print("=" * 60)

    customers = [
        {"name": "Priya", "total_spent": 62000},
        {"name": "Arjun", "total_spent": 25000},
        {"name": "Sneha", "total_spent": 4200},
        {"name": "Rahul", "total_spent": 180000},
        {"name": "Divya", "total_spent": 9500},
    ]

    gold_or_above_count = 0
    for c in customers:
        tier = categorise_customer(c["total_spent"])
        print(f"  {c['name']:<7} -> {tier}")
        if tier in ("Gold", "Platinum"):
            gold_or_above_count += 1

    print(f"\nGold or above: {gold_or_above_count} customers")


def main() -> None:
    demo_arithmetic()
    print(f"\nDiscounted 8500 at 12% = {calculate_discounted_price(8500, 12)}")
    demo_boolean_logic()
    demo_conditional_branching()
    demo_for_loop_with_enumerate()
    demo_while_with_retry()
    demo_customer_pipeline()


if __name__ == "__main__":
    main()
