"""
Section 3.12 — Performance, Output, Validation, Method Chaining.

The section that turns a working notebook into shippable code.

Covers:
  * Vectorization — why looping over rows is 10-100x slower than
    letting Pandas process a column at once
  * Category dtype for low-cardinality strings (memory)
  * Chunked reads for big files
  * The output verbs: to_csv, to_parquet, to_json — plus when each fits
  * Validation — assert-style row-count and null checks before writing
  * Method chaining — the "one pipeline expression" style used in
    production Pandas code

Run: `python 12_performance_output_validation.py`
"""

import io
import tempfile
import time
from pathlib import Path

import pandas as pd


def demo_vectorization_speed() -> None:
    """Show that vectorized arithmetic beats a Python for-loop badly.

    Loops materialize each row as a dict; vectorization stays in NumPy
    the whole way. Even on a small DataFrame the difference is visible.
    """
    print("=" * 60)
    print("VECTORIZATION VS PYTHON LOOP")
    print("=" * 60)

    n = 200_000
    df = pd.DataFrame(
        {"a": range(n), "b": range(n)},
    )

    # Loop (slow).
    t0 = time.perf_counter()
    result_loop = []
    for _, row in df.iterrows():
        result_loop.append(row["a"] + row["b"])
    t_loop = time.perf_counter() - t0

    # Vectorized (fast).
    t0 = time.perf_counter()
    result_vec = (df["a"] + df["b"]).tolist()
    t_vec = time.perf_counter() - t0

    print(f"loop:       {t_loop:.3f} s")
    print(f"vectorized: {t_vec:.3f} s")
    print(f"speedup:    {t_loop / t_vec:.1f}x")


def demo_output_formats(tmpdir: Path) -> None:
    """Write the same DataFrame in three formats — compare size and speed."""
    print("\n" + "=" * 60)
    print("OUTPUT FORMATS — CSV, PARQUET, JSON")
    print("=" * 60)

    n = 9_999  # multiple of 3 so the country column matches length
    df = pd.DataFrame(
        {
            "customer_id": [f"C{i:04d}" for i in range(n)],
            "spent": [i * 3.14 for i in range(n)],
            "country": ["India", "USA", "UK"] * (n // 3),
        }
    )

    csv_path = tmpdir / "out.csv"
    parquet_path = tmpdir / "out.parquet"
    json_path = tmpdir / "out.json"

    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)
    df.to_json(json_path, orient="records")

    print(f"CSV:     {csv_path.stat().st_size:>10,} bytes")
    print(f"PARQUET: {parquet_path.stat().st_size:>10,} bytes (compressed + typed)")
    print(f"JSON:    {json_path.stat().st_size:>10,} bytes")

    print(
        "\nParquet wins for DE storage — smaller, faster, dtypes preserved."
    )


def demo_validation_pattern() -> None:
    """Assert-style validation before writing — catches issues early."""
    print("\n" + "=" * 60)
    print("VALIDATION BEFORE WRITING")
    print("=" * 60)

    df = pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C003"],
            "spent": [45000.0, 4000.0, 12000.0],
        }
    )

    def validate(df: pd.DataFrame) -> None:
        """Raise if any expected invariant is violated."""
        assert len(df) > 0, "output is empty"
        assert df["customer_id"].is_unique, "duplicate customer_ids present"
        assert df["spent"].notnull().all(), "null spend values present"
        assert (df["spent"] >= 0).all(), "negative spend values present"

    validate(df)
    print(f"validation passed for {len(df)} rows")


def demo_method_chaining() -> None:
    """The production Pandas style — one pipeline expression per operation.

    Advantages:
      * The whole transformation reads top-to-bottom.
      * No throwaway intermediate variables.
      * Every step is a testable sub-expression.
    """
    print("\n" + "=" * 60)
    print("METHOD CHAINING")
    print("=" * 60)

    raw = pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C003", "C004", "C005"],
            "name": ["  Priya  ", "arjun", None, "SNEHA", "Rahul"],
            "total_spent": ["45000", "4000", "12000", "bad", "72000"],
            "country": ["India", "usa", "uk", "India", "USA"],
        }
    )

    cleaned = (
        raw
        .assign(
            name=lambda d: d["name"].str.strip().str.title(),
            country=lambda d: d["country"].str.strip().str.title(),
            total_spent=lambda d: pd.to_numeric(d["total_spent"], errors="coerce"),
        )
        .dropna(subset=["name", "total_spent"])
        .assign(
            tier=lambda d: pd.cut(
                d["total_spent"],
                bins=[0, 5000, 20000, 50000, float("inf")],
                labels=["Bronze", "Silver", "Gold", "Platinum"],
            )
        )
        .reset_index(drop=True)
    )

    print(cleaned)


def main() -> None:
    demo_vectorization_speed()

    with tempfile.TemporaryDirectory() as td:
        demo_output_formats(Path(td))

    demo_validation_pattern()
    demo_method_chaining()


if __name__ == "__main__":
    main()
