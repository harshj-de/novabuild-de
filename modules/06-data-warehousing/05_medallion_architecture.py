"""
Section 6.5 — Medallion Architecture (Bronze / Silver / Gold)

The Databricks-popularised pattern for organising data lakes and
lakehouses. Three progressive quality tiers:

    BRONZE   Raw ingested data — exactly as received from source.
             No cleaning, no typing, no business logic.
             One table per source. Immutable append-only.

    SILVER   Cleaned, typed, deduplicated data.
             Business-neutral quality corrections applied.
             One table per source, but properly typed and validated.
             This is where quality gates live.

    GOLD     Business-facing aggregates and dimensions.
             Star schemas, mart tables, KPI-ready datasets.
             What BI tools and analysts actually query.

Why the layers matter:
    * Bronze preserves raw truth — you can always re-derive Silver
      and Gold if business logic changes.
    * Silver isolates data quality concerns from business logic.
    * Gold is small, fast, and business-owned.

This module builds the pattern for NovaBuild's claims and contractor
data using Pandas + Parquet as a local demonstration. In production
this would be Delta Lake on ADLS Gen2 (Azure) or S3 (AWS), managed
by Databricks or Spark.

Target: Python 3.10+, Pandas 2.x, pyarrow (for Parquet writes).
Assumed prerequisite tables: contractors, claims, coi_verifications,
safety_incidents.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pandas as pd

# Root directory for the local lakehouse (mirrors S3/ADLS bucket layout).
LAKE_ROOT = Path("/tmp/novabuild_lake")


# =====================================================================
# BRONZE LAYER — raw ingestion
#
# Land data exactly as it arrived. No cleaning. No typing beyond what
# the reader inferred. Add ingestion metadata columns so downstream
# layers know what came from where and when.
# =====================================================================

def load_bronze(source_conn) -> None:
    """
    Read each source table and write it to bronze/ as Parquet.

    Adds three metadata columns to every bronze table:
        _ingested_at        — when this row landed in the lake
        _source_system      — which system it came from
        _ingestion_batch_id — the batch identifier (for lineage)

    Idempotent: overwrites the target file if it exists.
    """
    bronze_dir = LAKE_ROOT / "bronze"
    bronze_dir.mkdir(parents=True, exist_ok=True)

    ingested_at = datetime.now()
    batch_id = ingested_at.strftime("%Y%m%d_%H%M%S")

    for table_name in ["contractors", "claims", "coi_verifications",
                       "safety_incidents"]:
        # Read from source — Bronze does no transformation.
        df = pd.read_sql(f"SELECT * FROM {table_name}", source_conn)

        # Add ingestion metadata (the Bronze contract).
        df["_ingested_at"]        = ingested_at
        df["_source_system"]      = "postgresql.novabuilds"
        df["_ingestion_batch_id"] = batch_id

        target = bronze_dir / f"{table_name}.parquet"
        df.to_parquet(target, index=False)
        print(f"[bronze] wrote {len(df):>7,} rows to {target}")


# =====================================================================
# SILVER LAYER — cleaned + typed + validated
#
# Silver is where data quality happens. Business-neutral corrections:
#   * Standardise date/timestamp types
#   * Uppercase / lowercase / strip string keys
#   * Drop rows that fail validation (null primary keys, negative amounts)
#   * Add data quality flags for suspicious values
#
# One row of Bronze → at most one row of Silver.
# =====================================================================

def build_silver_contractors() -> pd.DataFrame:
    """
    Silver: contractor master data with normalised keys and typed
    numeric columns. Drops rows with null contractor_id (invalid).
    """
    src = pd.read_parquet(LAKE_ROOT / "bronze" / "contractors.parquet")

    df = src.copy()

    # Type coercion — Bronze may have loaded these as objects.
    df["emr"]             = pd.to_numeric(df["emr"], errors="coerce")
    df["employees_count"] = pd.to_numeric(df["employees_count"],
                                          errors="coerce").astype("Int64")

    # Normalise string identifiers so downstream joins are reliable.
    df["contractor_id"] = df["contractor_id"].str.strip().str.upper()
    df["state"]         = df["state"].str.strip().str.upper()

    # Quality gates.
    before = len(df)
    df = df[df["contractor_id"].notna()]
    df = df[df["emr"].between(0.5, 3.0, inclusive="both")]   # sensible EMR range
    dropped = before - len(df)
    print(f"[silver_contractors] kept {len(df):,} of {before:,} "
          f"({dropped:,} dropped by quality gates)")

    return df


def build_silver_claims() -> pd.DataFrame:
    """
    Silver: claim events with parsed dates and validated amounts.
    """
    src = pd.read_parquet(LAKE_ROOT / "bronze" / "claims.parquet")

    df = src.copy()

    # Parse loss_date into a real datetime (Bronze may have it as string).
    df["loss_date"]   = pd.to_datetime(df["loss_date"], errors="coerce")

    # Coerce money columns.
    for col in ["total_incurred", "paid_amount", "reserve_amount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Quality gates.
    before = len(df)
    df = df[df["claim_id"].notna()]
    df = df[df["loss_date"].notna()]
    df = df[df["total_incurred"] >= 0]   # negative claims are data errors
    dropped = before - len(df)
    print(f"[silver_claims] kept {len(df):,} of {before:,} "
          f"({dropped:,} dropped by quality gates)")

    return df


def build_silver_safety_incidents() -> pd.DataFrame:
    """
    Silver: safety incident events with parsed dates.
    """
    src = pd.read_parquet(LAKE_ROOT / "bronze" / "safety_incidents.parquet")
    df = src.copy()

    df["incident_date"] = pd.to_datetime(df["incident_date"], errors="coerce")

    before = len(df)
    df = df[df["contractor_id"].notna() & df["incident_date"].notna()]
    print(f"[silver_safety_incidents] kept {len(df):,} of {before:,}")

    return df


def load_silver() -> None:
    silver_dir = LAKE_ROOT / "silver"
    silver_dir.mkdir(parents=True, exist_ok=True)

    for name, builder in [
        ("contractors",       build_silver_contractors),
        ("claims",            build_silver_claims),
        ("safety_incidents",  build_silver_safety_incidents),
    ]:
        df = builder()
        target = silver_dir / f"{name}.parquet"
        df.to_parquet(target, index=False)


# =====================================================================
# GOLD LAYER — business facing
#
# Gold answers specific questions. Every Gold table has a business
# owner (Claims team, Underwriting team, Executive dashboard).
#
# The tables here mirror what would drive the NovaBuild Power BI
# dashboard.
# =====================================================================

def build_gold_contractor_risk() -> pd.DataFrame:
    """
    One row per contractor with rolled-up risk metrics.
    Powers the "contractor risk profile" page in Power BI.
    """
    contractors = pd.read_parquet(LAKE_ROOT / "silver" / "contractors.parquet")
    claims      = pd.read_parquet(LAKE_ROOT / "silver" / "claims.parquet")
    incidents   = pd.read_parquet(LAKE_ROOT / "silver" / "safety_incidents.parquet")

    claim_agg = (
        claims.groupby("contractor_id")
        .agg(
            claim_count      = ("claim_id", "count"),
            total_incurred   = ("total_incurred", "sum"),
            largest_claim    = ("total_incurred", "max"),
        )
        .reset_index()
    )

    incident_agg = (
        incidents.groupby("contractor_id")
        .agg(incident_count=("incident_date", "count"))
        .reset_index()
    )

    gold = (
        contractors
        .merge(claim_agg,    on="contractor_id", how="left")
        .merge(incident_agg, on="contractor_id", how="left")
        .fillna({"claim_count": 0, "total_incurred": 0,
                 "largest_claim": 0, "incident_count": 0})
    )

    # Business logic — combine metrics into a risk score.
    # (Simple weighted formula; a real model would be learned.)
    gold["risk_score"] = (
        gold["emr"] * 40
        + (gold["claim_count"]    / gold["employees_count"].clip(lower=1)) * 30
        + (gold["incident_count"] / gold["employees_count"].clip(lower=1)) * 30
    )

    gold["risk_tier_computed"] = pd.cut(
        gold["risk_score"],
        bins=[0, 40, 70, 100, float("inf")],
        labels=["Low", "Medium", "High", "Severe"],
    )

    return gold


def build_gold_monthly_loss() -> pd.DataFrame:
    """
    Monthly aggregated claim losses. Powers the line chart in Power BI.

    Grain: one row per (year, month).
    """
    claims = pd.read_parquet(LAKE_ROOT / "silver" / "claims.parquet")

    df = (
        claims.assign(month=claims["loss_date"].dt.to_period("M").dt.to_timestamp())
        .groupby("month")
        .agg(
            claim_count    = ("claim_id",       "count"),
            total_incurred = ("total_incurred", "sum"),
            paid_amount    = ("paid_amount",    "sum"),
        )
        .reset_index()
        .sort_values("month")
    )
    return df


def load_gold() -> None:
    gold_dir = LAKE_ROOT / "gold"
    gold_dir.mkdir(parents=True, exist_ok=True)

    for name, builder in [
        ("contractor_risk_profile", build_gold_contractor_risk),
        ("monthly_loss",            build_gold_monthly_loss),
    ]:
        df = builder()
        target = gold_dir / f"{name}.parquet"
        df.to_parquet(target, index=False)
        print(f"[gold] wrote {len(df):>7,} rows to {target}")


# =====================================================================
# End-to-end orchestration
# =====================================================================

def run_medallion_pipeline(source_conn) -> None:
    """Full Bronze → Silver → Gold refresh."""
    print("=== Medallion pipeline start ===")
    load_bronze(source_conn)
    load_silver()
    load_gold()
    print("=== Medallion pipeline done ===")


if __name__ == "__main__":
    # Demonstration entry point. In production this would run on a
    # schedule via Airflow / Databricks Jobs, and source_conn would
    # be a Databricks / Snowflake connection, not local Postgres.
    import psycopg2

    conn = psycopg2.connect(
        host=os.environ.get("PG_HOST", "localhost"),
        port=int(os.environ.get("PG_PORT", 5432)),
        dbname=os.environ.get("PG_DB", "novabuilds"),
        user=os.environ.get("PG_USER", "saas_user"),
        password=os.environ.get("PG_PASSWORD", "saas_pass"),
    )
    try:
        run_medallion_pipeline(conn)
    finally:
        conn.close()

# =====================================================================
# Interview extensions
#
# Q: "Why Parquet and not CSV?"
# A: Parquet is columnar (fast scans on subsets of columns), preserves
#    dtypes (dates stay dates, not strings), compresses well, and
#    supports predicate pushdown when combined with query engines.
#    CSV is human-readable but slow and lossy.
#
# Q: "What replaces Parquet in a production Lakehouse?"
# A: Delta Lake (Databricks), Iceberg (Snowflake/Trino), or Hudi (Uber).
#    All add ACID semantics + time travel on top of Parquet.
#
# Q: "How do you handle schema evolution in Bronze?"
# A: Bronze is append-only, so new columns just show up. Silver decides
#    whether to include or ignore them. Databricks Delta supports
#    ALTER TABLE ... ADD COLUMN for evolving lake tables.
# =====================================================================
