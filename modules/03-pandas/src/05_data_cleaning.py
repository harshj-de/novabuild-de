"""
Section 3.5 — Data Cleaning.

The section every DE actually spends 60% of their time on. Loading is
easy, aggregating is easy — cleaning is where real value gets created.

Covers:
  * Detecting missing values (`isnull`, `sum`, per-column vs per-row)
  * Strategies: drop vs fill, and when each is appropriate
  * `fillna` with column-specific defaults, forward/backward fill
  * Detecting and removing duplicates
  * `.duplicated()` — subset-based dedup
  * String cleaning — strip, lower, replace, regex
  * Type coercion with `.astype()` and `pd.to_numeric(errors='coerce')`
  * Outlier detection with IQR and z-score (a real DE habit)
  * .clip() for bounded values

Run: `python 05_data_cleaning.py`
"""

import numpy as np
import pandas as pd


def messy_customers() -> pd.DataFrame:
    """A realistic messy fixture — nulls, duplicates, whitespace, bad types."""
    return pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C003", "C002", "C004", "C005"],
            "name": ["  Priya  ", "arjun", None, "arjun", "SNEHA", "Rahul"],
            "email": [
                "priya@x.com",
                "ARJUN@X.COM",
                "sneha@x.com",
                "arjun@x.com",
                None,
                "rahul@x.com",
            ],
            "total_spent": ["45000", "4000", "bad", "4000", None, "72000"],
            "country": ["India", "usa ", "uk", "usa ", "India", "UK"],
        }
    )


def demo_detecting_nulls() -> None:
    print("=" * 60)
    print("DETECTING NULLS")
    print("=" * 60)
    df = messy_customers()

    print("nulls per column:")
    print(df.isnull().sum())

    print("\nrows with ANY null:")
    print(df[df.isnull().any(axis=1)])


def demo_fillna_strategies() -> None:
    """Different strategies for different columns — never blanket-fill."""
    print("\n" + "=" * 60)
    print("FILLING MISSING VALUES")
    print("=" * 60)
    df = messy_customers()

    # Column-specific defaults — a dict maps each column to its fill value.
    filled = df.fillna(
        {
            "name": "Unknown",
            "email": "no-email@placeholder.com",
            "total_spent": "0",
        }
    )
    print(filled)


def demo_dropna() -> None:
    """When to drop instead of fill — rows with missing critical fields."""
    print("\n" + "=" * 60)
    print("DROPPING ROWS WITH NULLS")
    print("=" * 60)
    df = messy_customers()

    # Drop rows where the name is missing — often you cannot fabricate a
    # customer name.
    kept = df.dropna(subset=["name"])
    print(f"before: {len(df)} rows, after dropna(subset=['name']): {len(kept)} rows")


def demo_duplicates() -> None:
    """Duplicate detection and removal — subset matters."""
    print("\n" + "=" * 60)
    print("DUPLICATES")
    print("=" * 60)
    df = messy_customers()

    # Full-row duplicates.
    print(f"exact-duplicate rows: {df.duplicated().sum()}")

    # Business-rule duplicates — same customer_id even if other fields differ.
    print(f"customer_id duplicates: {df.duplicated(subset=['customer_id']).sum()}")

    # Keep first occurrence, drop the rest.
    deduped = df.drop_duplicates(subset=["customer_id"], keep="first")
    print(f"\nafter drop_duplicates(subset=['customer_id']): {len(deduped)} rows")


def demo_string_cleaning() -> None:
    """String cleaning via the .str accessor — strip, lower, title, replace."""
    print("\n" + "=" * 60)
    print("STRING CLEANING")
    print("=" * 60)
    df = messy_customers()

    # Chain string operations — strip whitespace then title-case.
    df["name_clean"] = df["name"].str.strip().str.title()
    df["email_clean"] = df["email"].str.strip().str.lower()
    df["country_clean"] = df["country"].str.strip().str.upper()

    print(df[["name", "name_clean", "email", "email_clean", "country", "country_clean"]])


def demo_type_coercion() -> None:
    """Bad string-to-number conversion is a common bug source.

    Use pd.to_numeric with errors='coerce' — bad values become NaN
    instead of raising. Then you can inspect and handle them.
    """
    print("\n" + "=" * 60)
    print("TYPE COERCION WITH errors='coerce'")
    print("=" * 60)
    df = messy_customers()

    # Naive .astype(float) would raise on 'bad'.
    df["total_spent_num"] = pd.to_numeric(df["total_spent"], errors="coerce")
    print(df[["total_spent", "total_spent_num"]])
    print(
        f"\ncoerced NaN count: {df['total_spent_num'].isnull().sum()} "
        "(originally bad values + originally null)"
    )


def demo_outlier_detection() -> None:
    """IQR and z-score — the two standard outlier detection methods."""
    print("\n" + "=" * 60)
    print("OUTLIER DETECTION (IQR + Z-SCORE)")
    print("=" * 60)

    amounts = pd.Series(
        [100, 120, 110, 105, 115, 125, 108, 112, 118, 100_000]  # last is outlier
    )

    # IQR method — anything outside [Q1 - 1.5*IQR, Q3 + 1.5*IQR] is an outlier.
    q1, q3 = amounts.quantile([0.25, 0.75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    print(f"IQR bounds: [{lower}, {upper}]")
    print(f"outliers by IQR: {amounts[(amounts < lower) | (amounts > upper)].tolist()}")

    # Z-score method — anything > 3 standard deviations from the mean.
    z = (amounts - amounts.mean()) / amounts.std()
    print(f"outliers by z-score > 3: {amounts[z.abs() > 3].tolist()}")


def demo_clip_bounded_values() -> None:
    """.clip() — cap values at known-good bounds instead of dropping rows."""
    print("\n" + "=" * 60)
    print(".clip() — CAPPING BOUNDED VALUES")
    print("=" * 60)

    ages = pd.Series([25, -5, 35, 150, 42])
    clipped = ages.clip(lower=0, upper=120)
    print(f"before: {ages.tolist()}")
    print(f"after clip(0, 120): {clipped.tolist()}")


def main() -> None:
    demo_detecting_nulls()
    demo_fillna_strategies()
    demo_dropna()
    demo_duplicates()
    demo_string_cleaning()
    demo_type_coercion()
    demo_outlier_detection()
    demo_clip_bounded_values()


if __name__ == "__main__":
    main()
