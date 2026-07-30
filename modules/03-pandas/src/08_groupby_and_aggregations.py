"""
Section 3.8 — GroupBy and Aggregations.

The workhorse of analytical Pandas. Every report, every metric, every
dashboard question — "revenue by region", "orders per customer",
"average AOV by month" — comes back to groupby + agg.

Covers:
  * groupby(key) — the split-apply-combine mental model
  * Simple aggregation (sum, mean, count, nunique)
  * Aggregating multiple columns with .agg()
  * Multi-column groupby (produces MultiIndex — see section 3.4)
  * Named aggregations — the readable, column-name-preserving form
  * transform() — group-level computation broadcast back to row level
  * filter() on groups — keep only groups matching a predicate
  * .size() vs .count() — subtly different (nulls)

Run: `python 08_groupby_and_aggregations.py`
"""

import pandas as pd


def sample_orders() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": [f"O{i:03d}" for i in range(1, 11)],
            "customer_id": [
                "C001", "C002", "C001", "C003", "C002",
                "C001", "C004", "C003", "C002", "C001",
            ],
            "region": ["IN", "US", "IN", "UK", "US", "IN", "UK", "UK", "US", "IN"],
            "product": ["A", "B", "A", "C", "B", "C", "A", "C", "A", "B"],
            "amount": [4500, 12000, 800, 3200, 15000, 6700, 2400, 5100, 3600, 9200],
        }
    )


def demo_simple_aggregation() -> None:
    """One column, one aggregation — the simplest form."""
    print("=" * 60)
    print("SIMPLE AGGREGATION")
    print("=" * 60)

    orders = sample_orders()

    # Total revenue per region.
    print("revenue per region:")
    print(orders.groupby("region")["amount"].sum())

    # Order count per region.
    print("\norder count per region:")
    print(orders.groupby("region").size())

    # Unique customers per region.
    print("\nunique customers per region:")
    print(orders.groupby("region")["customer_id"].nunique())


def demo_agg_multiple_functions() -> None:
    """.agg() with a list — multiple aggregations on the same column at once."""
    print("\n" + "=" * 60)
    print(".agg() WITH MULTIPLE FUNCTIONS")
    print("=" * 60)

    orders = sample_orders()

    result = orders.groupby("region")["amount"].agg(["sum", "mean", "count", "max"])
    print(result)


def demo_named_aggregations() -> None:
    """Named aggregations — the readable, dashboard-ready form.

    Preferred pattern in production DE code. Column names in the
    output are exactly what you specify.
    """
    print("\n" + "=" * 60)
    print("NAMED AGGREGATIONS (the readable form)")
    print("=" * 60)

    orders = sample_orders()

    summary = orders.groupby("region").agg(
        total_revenue=("amount", "sum"),
        avg_order_value=("amount", "mean"),
        order_count=("order_id", "count"),
        unique_customers=("customer_id", "nunique"),
    )
    print(summary)


def demo_multi_key_groupby() -> None:
    """groupby with multiple keys — produces MultiIndex result."""
    print("\n" + "=" * 60)
    print("MULTI-KEY GROUPBY")
    print("=" * 60)

    orders = sample_orders()

    by_region_product = (
        orders.groupby(["region", "product"])
        .agg(
            revenue=("amount", "sum"),
            orders=("order_id", "count"),
        )
        .reset_index()  # flatten for downstream consumers
    )
    print(by_region_product)


def demo_transform_broadcast() -> None:
    """transform() — apply a group-level function but return row-level shape.

    Classic use: percentage-of-group calculations. Every row learns
    something about its group without collapsing to one row per group.
    """
    print("\n" + "=" * 60)
    print("transform() — GROUP-LEVEL METRICS AT ROW LEVEL")
    print("=" * 60)

    orders = sample_orders()

    # Compute region total per row.
    orders["region_total"] = orders.groupby("region")["amount"].transform("sum")
    # % this row contributes to its region total.
    orders["pct_of_region"] = orders["amount"] / orders["region_total"] * 100

    print(orders[["region", "amount", "region_total", "pct_of_region"]].round(2))


def demo_filter_groups() -> None:
    """filter() on groups — keep only groups meeting a predicate."""
    print("\n" + "=" * 60)
    print("filter() ON GROUPS")
    print("=" * 60)

    orders = sample_orders()

    # Only keep customers with more than 2 orders.
    high_freq = orders.groupby("customer_id").filter(lambda g: len(g) > 2)
    print("customers with > 2 orders:")
    print(high_freq)


def main() -> None:
    demo_simple_aggregation()
    demo_agg_multiple_functions()
    demo_named_aggregations()
    demo_multi_key_groupby()
    demo_transform_broadcast()
    demo_filter_groups()


if __name__ == "__main__":
    main()
