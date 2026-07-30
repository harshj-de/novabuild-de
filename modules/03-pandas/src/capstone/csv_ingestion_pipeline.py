"""
Capstone 1 — CSV Ingestion + Validation Pipeline.

End-to-end mini-project: generate a messy sales CSV, parse it, validate
each record, split output into `cleaned_sales_data.csv` and
`rejected_sales_data.csv` so downstream systems get only clean data.

This is the shape of every real ETL job: source is untrusted, ingest
tolerates errors row-by-row, output is split into "loadable" and
"quarantined" streams.

Run this file as a script:
    python csv_ingestion_pipeline.py

Outputs three files in the current directory:
    sales_data_1000.csv       — the messy source (regenerated on each run)
    cleaned_sales_data.csv    — records that passed all validation checks
    rejected_sales_data.csv   — records that failed, with the reason

Bug fixes flagged in-line vs the original notebook:
    * FIX 1: original used '\\n\\t'.join(lines) — the stray tab garbled
      every row. Replaced with '\\n'.
    * FIX 2: original nested the 'product is missing' check INSIDE the
      except: block for order_id. That meant the check only ran when
      order_id failed to parse — which is almost never. Moved to its
      own check outside any except.
    * FIX 3: original used bare `except:` which catches everything
      including KeyboardInterrupt. Replaced with `except ValueError`.
    * FIX 4: original wrote columns in a different order to the
      cleaned CSV than the header declared. Fixed to match header.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path


PRODUCTS = ["A", "B", "C", "D", "E"]
SOURCE_FILE = Path("sales_data_1000.csv")
CLEANED_FILE = Path("cleaned_sales_data.csv")
REJECTED_FILE = Path("rejected_sales_data.csv")


# ─── Step 1: generate a realistic messy source CSV ────────────────────


def generate_messy_csv(path: Path, n_rows: int = 1000, seed: int = 42) -> None:
    """Write a CSV with intentionally messy values for the validator to catch."""
    random.seed(seed)

    lines = ["order_id,product,quantity,price"]

    for i in range(1, n_rows + 1):
        # Occasional missing product.
        product = random.choice(PRODUCTS + [""])
        # Occasional bad quantity (empty or string).
        quantity = random.choice([1, 2, 3, 4, 5, "", "abc"])
        # Occasional bad price.
        price = random.choice([10, 20, 30, 40, 50, "xyz"])

        lines.append(f"{i},{product},{quantity},{price}")

    # FIX 1: original code used "\n\t".join(lines) — the tab character
    # got inserted between rows, corrupting parsing. Removed.
    path.write_text("\n".join(lines))
    print(f"[generate] wrote {n_rows} rows to {path}")


# ─── Step 2: parse the CSV into structured records ────────────────────


def parse_csv(path: Path) -> list[dict]:
    """Read a CSV file line by line into a list of dicts.

    Attaches a `_line_number` field to every record for error tracing.
    Uses the csv module for correct quote/escape handling — the original
    notebook used naive split(',') which breaks on any quoted field.
    """
    records: list[dict] = []

    with path.open() as f:
        reader = csv.DictReader(f)
        for line_number, row in enumerate(reader, start=2):  # start=2 accounts for header
            row["_line_number"] = line_number
            records.append(row)

    print(f"[parse] read {len(records)} records from {path}")
    return records


# ─── Step 3: validate each record, splitting into clean / rejected ────


def validate_records(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split records into (clean, rejected) with per-record error reasons."""
    clean: list[dict] = []
    rejected: list[dict] = []

    for record in records:
        errors: list[str] = []

        # order_id must be an integer.
        try:
            record["order_id"] = int(record["order_id"])
        except (ValueError, KeyError):
            errors.append("order_id must be an integer")

        # FIX 2 + FIX 3: original nested this check inside the order_id
        # except block, so it only ran when order_id also failed.
        # Bare except: was replaced with a specific exception class.
        if not record.get("product"):
            errors.append("product is missing")

        # quantity must be an integer.
        try:
            record["quantity"] = int(record["quantity"])
        except (ValueError, KeyError):
            errors.append("quantity must be an integer")

        # price must be a float.
        try:
            record["price"] = float(record["price"])
        except (ValueError, KeyError):
            errors.append("price must be a number")

        if errors:
            rejected.append(
                {
                    "line": record["_line_number"],
                    "record": {k: v for k, v in record.items() if k != "_line_number"},
                    "errors": errors,
                }
            )
        else:
            clean.append(record)

    print(f"[validate] clean: {len(clean)}, rejected: {len(rejected)}")
    return clean, rejected


# ─── Step 4: write the two output streams ─────────────────────────────


def write_clean(records: list[dict], path: Path) -> None:
    """Write clean records with columns in header order.

    FIX 4: original wrote price/product/quantity in a different order
    than the header declared. Now uses csv.DictWriter which enforces
    correct field ordering.
    """
    if not records:
        print(f"[write] no clean records — {path} not created")
        return

    with path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["order_id", "product", "quantity", "price"]
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "order_id": record["order_id"],
                    "product": record["product"],
                    "quantity": record["quantity"],
                    "price": record["price"],
                }
            )
    print(f"[write] {len(records)} clean records -> {path}")


def write_rejected(rejected: list[dict], path: Path) -> None:
    """Write rejected records with a piped list of reasons."""
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["line_number", "errors", "raw_record"])
        for item in rejected:
            writer.writerow(
                [
                    item["line"],
                    "|".join(item["errors"]),
                    item["record"],
                ]
            )
    print(f"[write] {len(rejected)} rejected records -> {path}")


# ─── Main pipeline ────────────────────────────────────────────────────


def main() -> None:
    generate_messy_csv(SOURCE_FILE, n_rows=1000)

    records = parse_csv(SOURCE_FILE)
    clean, rejected = validate_records(records)

    write_clean(clean, CLEANED_FILE)
    write_rejected(rejected, REJECTED_FILE)

    # Preview first 5 rows of each output.
    print("\n=== cleaned_sales_data.csv preview ===")
    for i, line in enumerate(CLEANED_FILE.read_text().splitlines()[:5]):
        print(f"  {line}")

    print("\n=== rejected_sales_data.csv preview ===")
    for i, line in enumerate(REJECTED_FILE.read_text().splitlines()[:5]):
        print(f"  {line}")


if __name__ == "__main__":
    main()
