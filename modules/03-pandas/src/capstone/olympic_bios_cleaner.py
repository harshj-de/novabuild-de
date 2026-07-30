"""
Capstone 2 — Olympic Bios Cleaner.

End-to-end cleaning of a real messy dataset — Olympic athlete
biographical records. Every cleaning step ties back to a specific
Pandas concept from sections 3.1–3.12:

  * Discovery ritual (3.1) — shape, dtypes, info, isna
  * Loading (3.2) — read_csv with proper params
  * String cleaning (3.5) — dot removal, whitespace normalisation
  * Regex extraction (3.5+3.6) — pulling structured fields out of free text
  * Type coercion (3.5) — height/weight to numeric with errors='coerce'
  * Range validation (3.5) — clip impossible values to NaN
  * Date parsing (3.6) — three date formats -> single datetime column
  * Reshaping (3.7+3.9) — expand a compound column into multiple columns

Inputs:
    data/bios_sample.csv — small representative sample (25 rows) so the
    pipeline runs out of the box.
    (Full dataset available on Kaggle: 'olympic athletes bios')

Output:
    bios_cleaned.csv — cleaned, structured, one row per athlete.

Run:
    python olympic_bios_cleaner.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


# Resolve data path relative to this file, so the script runs from any cwd.
DATA_DIR = Path(__file__).parent.parent.parent / "data"
SOURCE = DATA_DIR / "bios_sample.csv"
OUTPUT = Path("bios_cleaned.csv")


# ─── Loading + discovery ──────────────────────────────────────────────


def load_and_inspect(path: Path) -> pd.DataFrame:
    """Read the CSV and print the five discovery commands."""
    df = pd.read_csv(path)
    print(f"[load] shape: {df.shape}")
    print(f"[load] columns: {df.columns.tolist()}")
    print(f"[load] dtypes:\n{df.dtypes}")
    print(f"[load] nulls per column:\n{df.isnull().sum()}")
    return df


# ─── Name cleaning ────────────────────────────────────────────────────


def clean_names(df: pd.DataFrame) -> pd.DataFrame:
    """Replace bullet separators, build a display_name with spaces.

    Some Olympic bios source data uses '•' as a separator between name
    parts. This step normalises to spaces and also constructs a
    "camel-split" display_name (e.g. 'JohnSmith' -> 'John Smith').
    """
    # Replace the dot variants with a single space and strip surrounding whitespace.
    df["Used name"] = (
        df["Used name"].astype(str)
        .str.replace(r"[•·‧]", " ", regex=True)
        .str.strip()
    )

    # Build display_name — dot removal + insert a space between adjacent
    # lowercase-uppercase runs to handle 'JohnSmith' -> 'John Smith'.
    df["display_name"] = (
        df["Used name"]
        .str.replace(r"[•·‧]", "", regex=True)
        .str.replace(r"([a-z])([A-Z])", r"\1 \2", regex=True)
        .str.strip()
    )
    return df


# ─── Measurements — extract height and weight ─────────────────────────


def parse_measurements(df: pd.DataFrame) -> pd.DataFrame:
    """Split 'XXX cm / YYY kg' into two numeric columns.

    Handles missing measurements (NaN in output), non-numeric junk,
    and out-of-range values via IQR-informed clipping.
    """
    # Regex-extract the two integers into new columns.
    extracted = df["Measurements"].str.extract(
        r"(\d+)\s*cm\s*/\s*(\d+)\s*kg"
    )
    df[["height_cm", "weight_kg"]] = extracted

    # Coerce to numeric — junk becomes NaN.
    df["height_cm"] = pd.to_numeric(df["height_cm"], errors="coerce")
    df["weight_kg"] = pd.to_numeric(df["weight_kg"], errors="coerce")

    # Range validation — impossible values become NaN (better than dropping).
    df.loc[~df["height_cm"].between(120, 250), "height_cm"] = pd.NA
    df.loc[~df["weight_kg"].between(30, 250), "weight_kg"] = pd.NA

    return df


# ─── Born — extract birth date and birthplace ────────────────────────


def parse_birth_info(df: pd.DataFrame) -> pd.DataFrame:
    """Extract a date and a (city, region, country) triple from the Born field.

    Real bios have three date formats in one column:
        "June 30, 1985 in ..."         (Month DD, YYYY)
        "21 August 1986 in ..."        (DD Month YYYY)
        "1997-03-14 in ..."            (ISO YYYY-MM-DD)
    We match any of the three with a compound regex, then let
    pd.to_datetime parse each.
    """
    born_extracted = df["Born"].str.extract(
        r"([A-Za-z]+\s+\d{1,2},\s+\d{4}"          # Month DD, YYYY
        r"|\d{1,2}\s+[A-Za-z]+\s+\d{4}"           # DD Month YYYY
        r"|\d{4}-\d{2}-\d{2})"                    # YYYY-MM-DD
    )
    df["born_date"] = pd.to_datetime(born_extracted[0], errors="coerce")

    # Extract "in CITY, REGION (COUNTRY)".
    location = df["Born"].str.extract(
        r"in\s+([^,]+),\s*([^()]+)\s*\(([^)]+)\)"
    )
    df[["birth_city", "birth_region", "birth_country"]] = location

    # Trim whitespace on all three parts.
    for col in ("birth_city", "birth_region", "birth_country"):
        df[col] = df[col].str.strip()

    return df


# ─── Final cleanup ────────────────────────────────────────────────────


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Drop the messy source columns and reorder for readability."""
    df = df.drop(columns=["Born", "Measurements", "Used name"])
    ordered = [
        "athlete_id",
        "display_name",
        "Sex",
        "born_date",
        "birth_city",
        "birth_region",
        "birth_country",
        "height_cm",
        "weight_kg",
        "NOC",
        "Roles",
    ]
    df = df[[c for c in ordered if c in df.columns]]
    return df


def validate_output(df: pd.DataFrame) -> None:
    """Cheap assertions on the shape and quality of the final DataFrame."""
    assert len(df) > 0, "output is empty"
    assert df["athlete_id"].is_unique, "duplicate athlete_id rows"
    # Reasonable non-null coverage — not 100%, some source rows are just poor.
    coverage = df["display_name"].notnull().mean()
    print(f"[validate] display_name coverage: {coverage:.0%}")
    print(f"[validate] {len(df)} rows, {df.isnull().sum().sum()} total nulls")


# ─── Main pipeline (method-chained) ───────────────────────────────────


def main() -> None:
    df = load_and_inspect(SOURCE)

    cleaned = (
        df
        .pipe(clean_names)
        .pipe(parse_measurements)
        .pipe(parse_birth_info)
        .pipe(finalize)
    )

    validate_output(cleaned)

    cleaned.to_csv(OUTPUT, index=False)
    print(f"\n[write] cleaned data -> {OUTPUT}")

    print("\n=== first 5 cleaned rows ===")
    print(cleaned.head())


if __name__ == "__main__":
    main()
