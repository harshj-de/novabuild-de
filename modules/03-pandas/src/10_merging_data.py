"""
Section 3.10 — Merging Data.

Joining DataFrames — the Pandas equivalent of SQL JOINs. Same four
verbs, same semantics, easier to reason about once you accept the
mental model is identical.

Covers:
  * inner join — only matching rows from both sides
  * left join — every row from left, matched rows from right (NaN otherwise)
  * right join — mirror of left
  * outer join — every row from both sides
  * Join keys with different column names (left_on / right_on)
  * Joining on the index (left_index / right_index)
  * Cross join — every row of left with every row of right
  * concat — stacking DataFrames (vertical or horizontal), not a join

Rule of thumb: check row counts before AND after a merge. A left join
that returns MORE rows than the left side had means duplicate keys
on the right — silent data multiplication.

Run: `python 10_merging_data.py`
"""

import pandas as pd


def sample_customers() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C003", "C004"],
            "name": ["Priya", "Arjun", "Sneha", "Rahul"],
            "country": ["India", "USA", "UK", "India"],
        }
    )


def sample_orders() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": ["O001", "O002", "O003", "O004", "O005"],
            "customer_id": ["C001", "C001", "C002", "C005", "C002"],
            # Notice C005 — an order for a customer not in the customers table.
            "amount": [4500, 12000, 800, 3200, 6700],
        }
    )


def demo_inner_join() -> None:
    """Inner — only rows where the key appears in BOTH DataFrames."""
    print("=" * 60)
    print("INNER JOIN")
    print("=" * 60)

    customers = sample_customers()
    orders = sample_orders()

    inner = orders.merge(customers, on="customer_id", how="inner")
    print(inner)
    print(f"\n{len(inner)} rows (dropped C005 order — not in customers)")


def demo_left_join() -> None:
    """Left — every row from left; right's rows only where they match."""
    print("\n" + "=" * 60)
    print("LEFT JOIN")
    print("=" * 60)

    customers = sample_customers()
    orders = sample_orders()

    left = orders.merge(customers, on="customer_id", how="left")
    print(left)
    print(f"\n{len(left)} rows (C005 kept, name/country are NaN)")


def demo_right_and_outer() -> None:
    """Right and outer — the two remaining join types, less common in practice."""
    print("\n" + "=" * 60)
    print("RIGHT JOIN AND OUTER JOIN")
    print("=" * 60)

    customers = sample_customers()
    orders = sample_orders()

    right = orders.merge(customers, on="customer_id", how="right")
    print("right join — every customer, orders where they exist:")
    print(right)

    outer = orders.merge(customers, on="customer_id", how="outer")
    print(f"\nouter join — union of both sides, {len(outer)} rows:")
    print(outer)


def demo_different_key_names() -> None:
    """left_on and right_on — when the join columns have different names."""
    print("\n" + "=" * 60)
    print("DIFFERENT KEY COLUMN NAMES")
    print("=" * 60)

    left = pd.DataFrame(
        {"cust_id": ["C001", "C002"], "spend": [45000, 4000]}
    )
    right = pd.DataFrame(
        {"customer_id": ["C001", "C002"], "name": ["Priya", "Arjun"]}
    )

    merged = left.merge(right, left_on="cust_id", right_on="customer_id")
    print(merged)


def demo_index_join() -> None:
    """Joining on the DataFrame index rather than a column."""
    print("\n" + "=" * 60)
    print("JOINING ON INDEX")
    print("=" * 60)

    customers = sample_customers().set_index("customer_id")
    orders = sample_orders().set_index("customer_id")

    joined = orders.join(customers, how="left")
    print(joined)


def demo_check_row_counts() -> None:
    """Detect silent multiplication from duplicate keys — a real DE bug."""
    print("\n" + "=" * 60)
    print("DETECTING SILENT ROW MULTIPLICATION")
    print("=" * 60)

    # Duplicate C001 rows on the right — will multiply left rows.
    left = pd.DataFrame({"customer_id": ["C001", "C002"], "spend": [45000, 4000]})
    right = pd.DataFrame(
        {
            "customer_id": ["C001", "C001", "C002"],
            "email": ["p@x.com", "priya@x.com", "arjun@x.com"],
        }
    )

    print(f"left has {len(left)} rows, right has {len(right)} rows")
    result = left.merge(right, on="customer_id", how="left")
    print(f"result has {len(result)} rows — one input row became two.")
    print(result)


def demo_concat_stacking() -> None:
    """concat — stacking DataFrames. NOT a join."""
    print("\n" + "=" * 60)
    print("concat — VERTICAL STACKING")
    print("=" * 60)

    jan = pd.DataFrame({"month": ["Jan"] * 2, "orders": [100, 150]})
    feb = pd.DataFrame({"month": ["Feb"] * 2, "orders": [120, 180]})

    combined = pd.concat([jan, feb], ignore_index=True)
    print(combined)


def main() -> None:
    demo_inner_join()
    demo_left_join()
    demo_right_and_outer()
    demo_different_key_names()
    demo_index_join()
    demo_check_row_counts()
    demo_concat_stacking()


if __name__ == "__main__":
    main()
