"""
Section 3.9 — Reshaping Data.

Long-form vs wide-form. The same data can be arranged two ways and each
shape suits a different downstream consumer:

  * Long form  — one row per observation (best for storage, groupby, plotting)
  * Wide form  — one row per entity, categories become columns (best for dashboards)

Every DE moves between them constantly. This module covers the four
verbs that do the conversion.

Covers:
  * pivot / pivot_table — long -> wide
  * melt — wide -> long (the inverse)
  * stack / unstack — index-based reshape
  * When each verb is the right choice

Run: `python 09_reshaping_data.py`
"""

import pandas as pd


def demo_pivot_long_to_wide() -> None:
    """pivot_table — long-form to wide-form for reporting."""
    print("=" * 60)
    print("pivot_table — LONG TO WIDE")
    print("=" * 60)

    long_form = pd.DataFrame(
        {
            "region": ["IN", "IN", "US", "US", "UK", "UK"],
            "product": ["A", "B", "A", "B", "A", "B"],
            "revenue": [5000, 3000, 8000, 6000, 4000, 2500],
        }
    )
    print("long form:")
    print(long_form)

    wide = long_form.pivot_table(
        index="region",
        columns="product",
        values="revenue",
        aggfunc="sum",
        fill_value=0,  # missing (region, product) combos default to 0
    )
    print("\npivoted (region as rows, product as columns):")
    print(wide)


def demo_melt_wide_to_long() -> None:
    """melt — the inverse of pivot. Every DE uses this to normalize wide data."""
    print("\n" + "=" * 60)
    print("melt — WIDE TO LONG")
    print("=" * 60)

    wide = pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C003"],
            "q1_revenue": [5000, 3000, 8000],
            "q2_revenue": [6000, 4000, 9000],
            "q3_revenue": [7000, 5000, 8500],
            "q4_revenue": [8000, 6000, 9500],
        }
    )
    print("wide form (one row per customer, quarters as columns):")
    print(wide)

    long_form = wide.melt(
        id_vars=["customer_id"],
        value_vars=["q1_revenue", "q2_revenue", "q3_revenue", "q4_revenue"],
        var_name="quarter",
        value_name="revenue",
    )
    print("\nmelted (one row per customer-quarter):")
    print(long_form)


def demo_stack_unstack() -> None:
    """stack / unstack — index-based reshaping.

    stack pushes the innermost column level into the row index.
    unstack does the reverse — pushes the innermost row-index level
    out to columns.
    """
    print("\n" + "=" * 60)
    print("stack / unstack — INDEX-BASED RESHAPE")
    print("=" * 60)

    # Start with a MultiIndex from groupby.
    orders = pd.DataFrame(
        {
            "region": ["IN", "IN", "US", "US"],
            "product": ["A", "B", "A", "B"],
            "revenue": [5000, 3000, 8000, 6000],
        }
    )
    grouped = orders.groupby(["region", "product"])["revenue"].sum()
    print("groupby result (MultiIndex Series):")
    print(grouped)

    # unstack — move product from row index to columns.
    unstacked = grouped.unstack("product")
    print("\nafter .unstack('product'):")
    print(unstacked)

    # stack — undo it.
    restacked = unstacked.stack()
    print("\nafter .stack() (back to long):")
    print(restacked)


def main() -> None:
    demo_pivot_long_to_wide()
    demo_melt_wide_to_long()
    demo_stack_unstack()


if __name__ == "__main__":
    main()
