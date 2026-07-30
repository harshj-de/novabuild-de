"""
Section 3.7 — Transformations.

Turning raw columns into business-ready ones. This is where the "T"
in ETL happens. Once you have a clean DataFrame, you shape it into
what downstream consumers need.

Covers:
  * assign() — the chainable way to add columns
  * apply() with a lambda — row-wise or column-wise custom transforms
  * map() — value-by-value mapping (Series only)
  * replace() — bulk substitution
  * where() and mask() — conditional replacement
  * numpy.where — vectorised if/else for a new column
  * pd.cut and pd.qcut — bucketing continuous values into bins
  * Rank and percentile

Rule of thumb: prefer vectorized operations (`df["a"] + df["b"]`) over
`.apply(lambda ...)` — vectorized is 10-100x faster on big DataFrames.

Run: `python 07_transformations.py`
"""

import numpy as np
import pandas as pd


def sample_customers() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C003", "C004", "C005", "C006"],
            "name": ["Priya", "Arjun", "Sneha", "Rahul", "Divya", "Manish"],
            "total_spent": [45000, 4000, 12000, 72000, 9500, 180000],
            "status": ["active", "inactive", "active", "active", "active", "active"],
        }
    )


def demo_assign_chainable() -> None:
    """assign() — add columns without mutating the original DataFrame."""
    print("=" * 60)
    print("assign() — CHAINABLE COLUMN ADDITION")
    print("=" * 60)

    customers = sample_customers()

    # Multiple new columns, referring to earlier ones via lambdas.
    result = customers.assign(
        spent_k=lambda d: d["total_spent"] / 1000,
        is_high_value=lambda d: d["total_spent"] > 20000,
    )
    print(result)


def demo_apply_rowwise() -> None:
    """apply() with axis=1 — a function per row.

    Powerful but slow. Use only when you cannot vectorize.
    """
    print("\n" + "=" * 60)
    print("apply() — ROW-WISE CUSTOM LOGIC")
    print("=" * 60)

    customers = sample_customers()

    def tier(row: pd.Series) -> str:
        s = row["total_spent"]
        if s > 50000:
            return "Platinum"
        if s > 20000:
            return "Gold"
        if s > 5000:
            return "Silver"
        return "Bronze"

    customers["tier"] = customers.apply(tier, axis=1)
    print(customers)


def demo_map_series() -> None:
    """map() — Series-level value substitution or lookup."""
    print("\n" + "=" * 60)
    print("map() — VALUE-BY-VALUE MAPPING")
    print("=" * 60)

    customers = sample_customers()

    country_of = {
        "C001": "India",
        "C002": "USA",
        "C003": "UK",
        "C004": "India",
    }
    # Missing customer_ids get NaN.
    customers["country"] = customers["customer_id"].map(country_of)
    print(customers[["customer_id", "name", "country"]])


def demo_replace_bulk_substitution() -> None:
    """replace() — bulk substitute values in one or many columns."""
    print("\n" + "=" * 60)
    print("replace() — BULK SUBSTITUTION")
    print("=" * 60)

    customers = sample_customers()
    customers["status"] = customers["status"].replace(
        {"active": "A", "inactive": "I"}
    )
    print(customers[["customer_id", "status"]])


def demo_where_and_mask() -> None:
    """.where() keeps values where condition is True; .mask() replaces them."""
    print("\n" + "=" * 60)
    print(".where() AND .mask()")
    print("=" * 60)

    customers = sample_customers()

    # .where — keeps original where condition True, else NaN (or replacement).
    kept = customers["total_spent"].where(customers["total_spent"] > 10000, other=0)
    print(f"where(> 10000, else 0): {kept.tolist()}")

    # .mask — inverse: replaces where condition is True.
    masked = customers["total_spent"].mask(customers["total_spent"] > 10000, other=0)
    print(f"mask(> 10000, else 0):  {masked.tolist()}")


def demo_numpy_where_vectorized() -> None:
    """np.where — the fast vectorized if/else for a new column."""
    print("\n" + "=" * 60)
    print("np.where — VECTORIZED IF/ELSE")
    print("=" * 60)

    customers = sample_customers()

    customers["is_vip"] = np.where(customers["total_spent"] > 50000, "VIP", "Regular")
    print(customers[["name", "total_spent", "is_vip"]])


def demo_cut_and_qcut() -> None:
    """pd.cut — equal-width bins; pd.qcut — equal-frequency bins."""
    print("\n" + "=" * 60)
    print("pd.cut AND pd.qcut — BUCKETING")
    print("=" * 60)

    customers = sample_customers()

    # cut — user-specified boundaries.
    customers["tier_cut"] = pd.cut(
        customers["total_spent"],
        bins=[0, 5000, 20000, 50000, float("inf")],
        labels=["Bronze", "Silver", "Gold", "Platinum"],
    )

    # qcut — 4 equal-frequency quartiles.
    customers["quartile"] = pd.qcut(
        customers["total_spent"],
        q=4,
        labels=["Q1", "Q2", "Q3", "Q4"],
    )

    print(customers[["name", "total_spent", "tier_cut", "quartile"]])


def demo_rank() -> None:
    """rank() — assign ranks; handy for leaderboards."""
    print("\n" + "=" * 60)
    print("rank() — LEADERBOARD")
    print("=" * 60)

    customers = sample_customers()

    customers["spend_rank"] = customers["total_spent"].rank(
        method="min", ascending=False
    )
    customers["spend_pct"] = customers["total_spent"].rank(pct=True)

    print(customers[["name", "total_spent", "spend_rank", "spend_pct"]])


def main() -> None:
    demo_assign_chainable()
    demo_apply_rowwise()
    demo_map_series()
    demo_replace_bulk_substitution()
    demo_where_and_mask()
    demo_numpy_where_vectorized()
    demo_cut_and_qcut()
    demo_rank()


if __name__ == "__main__":
    main()
