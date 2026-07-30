"""
Section 3.2 — Loading Data.

The moment your pipeline meets untyped source data. `read_csv` looks
simple but the difference between a naive load and a proper one is the
difference between "it works today" and "it works in production."

Covers:
  * Naive vs proper `read_csv` — dtype, parse_dates, na_values
  * Preventing string-ID coercion to int (leading-zero loss)
  * category dtype for low-cardinality columns (huge memory savings)
  * Reading JSON (records vs oriented forms)
  * Reading Parquet / Feather (columnar formats DEs actually use)
  * Reading Excel (the format you WILL be asked to load)
  * Chunked reading for files larger than RAM

Requires: pandas, pyarrow (for parquet), openpyxl (for xlsx).
Run:     `python 02_loading_data.py`

Note: this module builds tiny in-memory samples on the fly so it runs
without external files. In real usage the arguments below apply to
actual CSV/JSON/Parquet paths.
"""

import io
import json
from pathlib import Path

import pandas as pd


CSV_SAMPLE = """order_id,customer_id,product_id,order_date,amount,status
0001,C001,P100,2024-01-15,4500,delivered
0002,C002,P101,2024-01-16,12000,pending
0003,C003,P100,2024-01-17,bad_status,cancelled
0004,C001,P102,,3000,
0005,C004,P103,2024-01-18,22000,shipped
"""


def demo_naive_vs_proper_read_csv() -> None:
    """Show what goes wrong when you don't parameterize read_csv."""
    print("=" * 60)
    print("NAIVE VS PROPER read_csv")
    print("=" * 60)

    # Naive load — no parameters.
    df_bad = pd.read_csv(io.StringIO(CSV_SAMPLE))
    print("naive load — dtypes:")
    print(df_bad.dtypes)
    print(f"first order_id: {df_bad['order_id'].iloc[0]!r}")
    # order_id became int64 — leading zeros lost. Bad for join keys.

    # Proper load — parameterized.
    df_good = pd.read_csv(
        io.StringIO(CSV_SAMPLE),
        dtype={
            "order_id": str,
            "customer_id": str,
            "product_id": str,
        },
        parse_dates=["order_date"],
        na_values=["", " ", "bad_status", "NULL", "N/A"],
    )
    print("\nproper load — dtypes:")
    print(df_good.dtypes)
    print(f"first order_id: {df_good['order_id'].iloc[0]!r}")
    print(f"nulls after parameterized load:\n{df_good.isnull().sum()}")


def demo_category_dtype_savings() -> None:
    """category dtype — huge memory saving for low-cardinality columns."""
    print("\n" + "=" * 60)
    print("category dtype — MEMORY SAVINGS")
    print("=" * 60)

    # Simulate a bigger dataset with repeating values.
    n = 10_000
    df = pd.DataFrame(
        {
            "customer_id": [f"C{i:04d}" for i in range(n)],
            "country": ["India", "USA", "UK", "India", "USA"] * (n // 5),
            "status": ["active", "inactive"] * (n // 2),
        }
    )

    before = df.memory_usage(deep=True).sum()
    print(f"before category: {before:,} bytes")

    # Convert the low-cardinality columns.
    df["country"] = df["country"].astype("category")
    df["status"] = df["status"].astype("category")

    after = df.memory_usage(deep=True).sum()
    print(f"after category:  {after:,} bytes")
    print(f"savings: {(1 - after / before) * 100:.1f}%")


def demo_read_json() -> None:
    """JSON reading — records-list vs orient='records'."""
    print("\n" + "=" * 60)
    print("READ JSON")
    print("=" * 60)

    records_json = json.dumps(
        [
            {"customer_id": "C001", "name": "Priya", "spent": 45000},
            {"customer_id": "C002", "name": "Arjun", "spent": 4000},
        ]
    )
    df = pd.read_json(io.StringIO(records_json), orient="records")
    print(df)


def demo_read_parquet(tmpdir: Path) -> None:
    """Parquet — the columnar format DEs actually ship in production.

    Faster, smaller, preserves dtypes exactly (no re-parsing needed).
    """
    print("\n" + "=" * 60)
    print("PARQUET — WRITE + READ")
    print("=" * 60)

    df = pd.DataFrame(
        {
            "customer_id": ["C001", "C002", "C003"],
            "spent": [45000.0, 4000.0, 72000.0],
            "join_date": pd.to_datetime(["2024-01-15", "2024-01-16", "2024-01-17"]),
        }
    )
    out = tmpdir / "customers.parquet"
    df.to_parquet(out, index=False)

    round_tripped = pd.read_parquet(out)
    print("round-tripped from parquet:")
    print(round_tripped)
    print("\ndtypes preserved exactly (unlike CSV):")
    print(round_tripped.dtypes)


def demo_chunked_reading() -> None:
    """chunksize — the pattern for files that don't fit in RAM.

    Each chunk is a smaller DataFrame yielded one at a time. Aggregate
    incrementally instead of loading everything.
    """
    print("\n" + "=" * 60)
    print("CHUNKED CSV READING")
    print("=" * 60)

    # Build a bigger CSV in memory so chunking is meaningful.
    rows = ["order_id,amount"]
    for i in range(1, 101):
        rows.append(f"O{i:04d},{i * 100}")
    big_csv = io.StringIO("\n".join(rows))

    total = 0
    n_chunks = 0
    for chunk in pd.read_csv(big_csv, chunksize=25):
        total += chunk["amount"].sum()
        n_chunks += 1

    print(f"processed {n_chunks} chunks, total amount: {total:,}")


def main() -> None:
    demo_naive_vs_proper_read_csv()
    demo_category_dtype_savings()
    demo_read_json()

    # Parquet needs a real filesystem path.
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        demo_read_parquet(Path(td))

    demo_chunked_reading()


if __name__ == "__main__":
    main()
