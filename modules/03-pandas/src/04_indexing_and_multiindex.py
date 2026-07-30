"""
Section 3.4 — Indexing and MultiIndex.

The index is the "row identifier" side of a DataFrame. Get the index right
and lookups are instant and readable; get it wrong and you're doing brittle
positional gymnastics.

Covers:
  * set_index() — making a meaningful column the index
  * Instant O(log n) lookups by index label
  * reset_index() — undoing set_index
  * sort_index() and sort_values()
  * MultiIndex (hierarchical indexing) — how DE-scale aggregates land
  * Navigating a MultiIndex with `.loc`
  * Flattening a MultiIndex — the most-used cleanup after groupby

Run: `python 04_indexing_and_multiindex.py`
"""

import pandas as pd


def sample_orders() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": ["O001", "O002", "O003", "O004", "O005", "O006"],
            "customer_id": ["C001", "C002", "C001", "C003", "C002", "C001"],
            "product": ["A", "B", "A", "C", "B", "C"],
            "region": ["IN", "US", "IN", "UK", "US", "IN"],
            "amount": [4500, 12000, 800, 3200, 15000, 6700],
        }
    )


def demo_set_index() -> None:
    """Make a column the index — cleaner lookups and joins downstream."""
    print("=" * 60)
    print("set_index() — MAKING A COLUMN THE INDEX")
    print("=" * 60)

    orders = sample_orders()
    indexed = orders.set_index("order_id")
    print(indexed)

    # Instant lookup by label — much cleaner than a boolean mask.
    print("\nindexed.loc['O003']:")
    print(indexed.loc["O003"])


def demo_reset_index() -> None:
    """reset_index() — undo set_index, put the label back as a column."""
    print("\n" + "=" * 60)
    print("reset_index() — PUTTING THE INDEX BACK AS A COLUMN")
    print("=" * 60)

    orders = sample_orders().set_index("order_id")
    back = orders.reset_index()
    print(back.head(3))


def demo_sort_index_vs_sort_values() -> None:
    """Two different sorts — by the index labels vs by a column's values."""
    print("\n" + "=" * 60)
    print("sort_index() VS sort_values()")
    print("=" * 60)

    orders = sample_orders().set_index("order_id")

    # Sort by the index labels alphabetically.
    print("sorted by index labels:")
    print(orders.sort_index().head(3))

    # Sort by a column's values.
    print("\nsorted by amount descending:")
    print(orders.sort_values("amount", ascending=False).head(3))


def demo_multiindex_creation() -> None:
    """MultiIndex — two-level index. Common after groupby."""
    print("\n" + "=" * 60)
    print("MULTIINDEX — HIERARCHICAL INDEXING")
    print("=" * 60)

    orders = sample_orders()

    # Groupby with multiple keys naturally produces a MultiIndex.
    mi = orders.groupby(["region", "product"])["amount"].sum()
    print("groupby(['region', 'product'])['amount'].sum():")
    print(mi)
    print(f"\nindex type: {type(mi.index).__name__}")


def demo_multiindex_navigation() -> None:
    """Navigating a MultiIndex — .loc with tuples, slice(None) for wildcards."""
    print("\n" + "=" * 60)
    print("MULTIINDEX NAVIGATION")
    print("=" * 60)

    orders = sample_orders()
    mi = orders.groupby(["region", "product"])["amount"].sum()

    # Select an entire outer level.
    print("mi.loc['IN']:")
    print(mi.loc["IN"])

    # Select a specific (region, product) pair with a tuple.
    print(f"\nmi.loc[('IN', 'A')]: {mi.loc[('IN', 'A')]}")


def demo_multiindex_flatten() -> None:
    """The most-used cleanup: turn a MultiIndex result into a flat DataFrame.

    Downstream code (writers, dashboards, joins) usually expects flat
    columns rather than a hierarchical index.
    """
    print("\n" + "=" * 60)
    print("FLATTENING A MULTIINDEX (the most-used pattern)")
    print("=" * 60)

    orders = sample_orders()
    mi = (
        orders.groupby(["region", "product"])["amount"]
        .sum()
        .reset_index()  # brings region and product back as columns
    )
    print(mi)


def main() -> None:
    demo_set_index()
    demo_reset_index()
    demo_sort_index_vs_sort_values()
    demo_multiindex_creation()
    demo_multiindex_navigation()
    demo_multiindex_flatten()


if __name__ == "__main__":
    main()
