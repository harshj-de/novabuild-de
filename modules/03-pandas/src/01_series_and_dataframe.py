"""
Section 3.1 — Series and DataFrame.

The two data structures every Pandas workflow rests on:

  * Series — one column of data with a shared index.
  * DataFrame — a table: multiple Series sharing the same row index.

This module covers the operations that turn "I loaded a CSV" into
"I understand what's in it." The five commands (shape / dtypes / info /
head / describe) plus the null-check are the discovery ritual every DE
runs on every new dataset.

Run: `python 01_series_and_dataframe.py`
"""

import pandas as pd


def demo_series_basics() -> None:
    """A Series is one column of data — think spreadsheet column."""
    print("=" * 60)
    print("SERIES — ONE COLUMN OF DATA")
    print("=" * 60)

    amounts = pd.Series([15000, 4000, 8000, 22000, 3000])
    print("amounts:")
    print(amounts)
    print(f"dtype: {amounts.dtype}")


def demo_vectorized_operations() -> None:
    """Every Series operation applies to all values at once — no loops needed."""
    print("\n" + "=" * 60)
    print("VECTORIZED OPERATIONS ON A SERIES")
    print("=" * 60)

    amounts = pd.Series([15000, 4000, 8000, 22000, 3000])

    # Multiply — happens on every element without a loop.
    print("amounts * 1.18 (add 18% tax):")
    print((amounts * 1.18).tolist())

    # Boolean comparison — returns a Series of booleans.
    print(f"amounts > 10000: {(amounts > 10000).tolist()}")

    # Aggregations.
    print(f"total: {amounts.sum()}")
    print(f"average: {amounts.mean()}")
    print(f"max: {amounts.max()}, min: {amounts.min()}")


def demo_dataframe_creation() -> None:
    """A DataFrame is multiple Series sharing the same index — a full table."""
    print("\n" + "=" * 60)
    print("DATAFRAME — A FULL TABLE")
    print("=" * 60)

    customers = pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C003", "C004"],
            "name": ["Priya", "Arjun", "Sneha", "Rahul"],
            "spent": [45000, 4000, 12000, 72000],
            "status": ["active", "inactive", "active", "active"],
        }
    )
    print(customers)


def demo_discovery_commands() -> None:
    """The five commands you run on every new dataset — the discovery ritual."""
    print("\n" + "=" * 60)
    print("THE FIVE DISCOVERY COMMANDS")
    print("=" * 60)

    customers = pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C003", "C004"],
            "name": ["Priya", "Arjun", "Sneha", "Rahul"],
            "spent": [45000, 4000, 12000, 72000],
            "status": ["active", "inactive", "active", "active"],
        }
    )

    # 1. Shape — rows and columns.
    print(f"1. shape: {customers.shape}")

    # 2. Dtypes — types per column.
    print("\n2. dtypes:")
    print(customers.dtypes)

    # 3. Info — dtypes + null counts + memory in one view.
    print("\n3. info():")
    customers.info()

    # 4. Head — first few rows, sanity check.
    print("\n4. head(3):")
    print(customers.head(3))

    # 5. Describe — statistical summary for numeric columns.
    print("\n5. describe():")
    print(customers.describe())


def demo_null_check() -> None:
    """The one-liner that catches most data problems before they cause bugs."""
    print("\n" + "=" * 60)
    print("NULL CHECK — RUN THIS ON EVERY DATASET")
    print("=" * 60)

    # Introduce a null to make the check meaningful.
    customers = pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C003", "C004"],
            "name": ["Priya", "Arjun", None, "Rahul"],
            "spent": [45000, None, 12000, 72000],
            "status": ["active", "inactive", "active", "active"],
        }
    )

    print("customers with intentional nulls:")
    print(customers)
    print("\nisnull().sum() per column:")
    print(customers.isnull().sum())


def main() -> None:
    demo_series_basics()
    demo_vectorized_operations()
    demo_dataframe_creation()
    demo_discovery_commands()
    demo_null_check()


if __name__ == "__main__":
    main()
