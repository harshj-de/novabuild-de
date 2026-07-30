"""
Section 3.3 — Selecting and Filtering.

The most-used verbs in Pandas. Every downstream operation — cleaning,
transformation, aggregation — starts with "get me these rows and these
columns." Get comfortable with these and every other module feels lighter.

Covers:
  * Column selection (single vs multiple, Series vs DataFrame)
  * `.loc` — label-based selection
  * `.iloc` — position-based selection
  * Boolean filtering — the most important pattern
  * Multiple conditions with `&` / `|` (parentheses matter)
  * `.isin()` for list-membership filters
  * `.query()` — readable string-based filtering
  * Filtering on nulls with `.isnull()` / `.notnull()`

Run: `python 03_selecting_and_filtering.py`
"""

import pandas as pd


def sample_customers() -> pd.DataFrame:
    """Small in-memory fixture used by every demo below."""
    return pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C003", "C004", "C005"],
            "name": ["Priya", "Arjun", "Sneha", "Rahul", "Divya"],
            "country": ["India", "USA", "UK", "India", "USA"],
            "status": ["active", "inactive", "active", "active", "inactive"],
            "total_spent": [45000.0, 4000.0, 12000.0, 72000.0, None],
        }
    )


def demo_column_selection() -> None:
    print("=" * 60)
    print("COLUMN SELECTION")
    print("=" * 60)
    customers = sample_customers()

    # Single column with single brackets — returns a Series.
    name_series = customers["name"]
    print("customers['name'] — type:", type(name_series).__name__)
    print(name_series.tolist())

    # Multiple columns with double brackets — returns a DataFrame.
    subset = customers[["name", "country", "status"]]
    print("\ncustomers[['name', 'country', 'status']] — type:",
          type(subset).__name__)
    print(subset)


def demo_loc_label_based() -> None:
    """.loc — the label-based selector. Rows and columns by name/index label."""
    print("\n" + "=" * 60)
    print(".loc — LABEL-BASED SELECTION")
    print("=" * 60)
    customers = sample_customers()

    # All rows, specific columns.
    print("customers.loc[:, ['name', 'country']]:")
    print(customers.loc[:, ["name", "country"]])

    # Specific rows by label range, all columns.
    print("\ncustomers.loc[1:3, :]:")
    print(customers.loc[1:3, :])

    # Both — specific rows AND specific columns.
    print("\ncustomers.loc[0:2, ['name', 'total_spent']]:")
    print(customers.loc[0:2, ["name", "total_spent"]])


def demo_iloc_position_based() -> None:
    """.iloc — position-based selector. Zero-indexed, Python-slice semantics."""
    print("\n" + "=" * 60)
    print(".iloc — POSITION-BASED SELECTION")
    print("=" * 60)
    customers = sample_customers()

    # First 2 rows, first 3 columns.
    print("customers.iloc[:2, :3]:")
    print(customers.iloc[:2, :3])

    # Specific row and column indices.
    print("\ncustomers.iloc[[0, 2, 4], [1, 4]]:")
    print(customers.iloc[[0, 2, 4], [1, 4]])


def demo_boolean_filtering() -> None:
    """The single most important pattern in Pandas — boolean masks."""
    print("\n" + "=" * 60)
    print("BOOLEAN FILTERING")
    print("=" * 60)
    customers = sample_customers()

    # Build a boolean Series.
    mask = customers["total_spent"] > 10000
    print("mask (total_spent > 10000):")
    print(mask.tolist())

    # Apply the mask.
    print("\ncustomers[mask]:")
    print(customers[mask])


def demo_multiple_conditions() -> None:
    """Combining conditions — & (and), | (or), ~ (not), parentheses required."""
    print("\n" + "=" * 60)
    print("MULTIPLE CONDITIONS")
    print("=" * 60)
    customers = sample_customers()

    # Every condition needs parentheses — & and | bind tighter than comparisons.
    high_value_active = customers[
        (customers["total_spent"] > 10000) & (customers["status"] == "active")
    ]
    print("high-value active customers:")
    print(high_value_active)

    # `~` inverts a mask.
    print("\ninactive customers (~status == 'active'):")
    print(customers[~(customers["status"] == "active")])


def demo_isin_and_query() -> None:
    """.isin() for list membership, .query() for readable string filters."""
    print("\n" + "=" * 60)
    print(".isin() AND .query()")
    print("=" * 60)
    customers = sample_customers()

    # Membership test against a list.
    us_or_uk = customers[customers["country"].isin(["USA", "UK"])]
    print("customers in USA or UK:")
    print(us_or_uk)

    # .query() — readable string-based filtering. Column names become
    # variables in the string.
    high_value_india = customers.query(
        "country == 'India' and total_spent > 10000"
    )
    print("\n.query() — high-value India customers:")
    print(high_value_india)


def demo_null_filtering() -> None:
    """Filtering rows based on presence or absence of nulls."""
    print("\n" + "=" * 60)
    print("FILTERING ON NULLS")
    print("=" * 60)
    customers = sample_customers()

    # Rows where total_spent IS null.
    missing_spend = customers[customers["total_spent"].isnull()]
    print("rows with missing total_spent:")
    print(missing_spend)

    # Rows where total_spent is NOT null.
    with_spend = customers[customers["total_spent"].notnull()]
    print(f"\nrows with total_spent: {len(with_spend)} of {len(customers)}")


def main() -> None:
    demo_column_selection()
    demo_loc_label_based()
    demo_iloc_position_based()
    demo_boolean_filtering()
    demo_multiple_conditions()
    demo_isin_and_query()
    demo_null_filtering()


if __name__ == "__main__":
    main()
