"""
Module 08 · Section 8.3 — Reading and Writing Data

Every real Spark job starts with a read and ends with a write. The
formats and modes matter more than the transformations in between.

Covered:
  * Reading from JDBC (with partitioning for parallelism)
  * Reading from Parquet, CSV, JSON
  * Writing Parquet with various modes
  * partitionBy() at write time — how downstream reads get fast
  * A production-shape daily-ingest pattern
"""

from pyspark.sql import functions as F

# -----------------------------------------------------------------------
# Reading from JDBC — with partitioning
# -----------------------------------------------------------------------
# JDBC without partitioning => 1 partition, 1 connection, serial pull.
# With partitionColumn / lowerBound / upperBound / numPartitions,
# Spark opens N parallel connections and splits the table by the
# partition column's range.

claims_parallel = spark.read.jdbc(
    url=jdbc_url,
    table="claims",
    column="claim_id",           # must be numeric or partitionable
    lowerBound=1,
    upperBound=100_000,
    numPartitions=8,
    properties=jdbc_props,
)

print(f"parallel JDBC load: {claims_parallel.rdd.getNumPartitions()} partitions")


# -----------------------------------------------------------------------
# Writing to Parquet
# -----------------------------------------------------------------------
# Parquet is the industry standard for lakehouse storage:
#   * columnar (fast partial-column scans)
#   * dtype preservation (dates stay dates)
#   * compressed by default (snappy)
#   * predicate pushdown when combined with Spark/Presto/Trino

# Simple write — one folder, one file per input partition.
claims_parallel.write \
    .mode("overwrite") \
    .parquet("/tmp/novabuild_lake/claims_parquet")

# Modes:
#   "overwrite" — delete target, write fresh
#   "append"    — add to existing
#   "ignore"    — do nothing if target exists
#   "error"     — raise if target exists (default)


# -----------------------------------------------------------------------
# partitionBy() — the write-time partitioning that makes reads fast
# -----------------------------------------------------------------------
# When you partitionBy("column"), Spark creates one folder per unique
# value:
#     /tmp/novabuild_lake/claims_partitioned/status=Open/
#     /tmp/novabuild_lake/claims_partitioned/status=Closed/
#
# Any read that filters on status can prune irrelevant folders —
# reading Closed claims doesn't touch Open files at all.
# THIS is why partitioning matters in production.

claims_parallel.write \
    .mode("overwrite") \
    .partitionBy("status") \
    .parquet("/tmp/novabuild_lake/claims_partitioned")


# -----------------------------------------------------------------------
# Reading it back
# -----------------------------------------------------------------------
# Point spark.read at the folder — Spark discovers the partition schema.

back = spark.read.parquet("/tmp/novabuild_lake/claims_partitioned")
print(f"Read back: {back.count():,} rows")

# Filter on the partition column — Spark prunes automatically:
open_only = spark.read.parquet("/tmp/novabuild_lake/claims_partitioned") \
    .filter(F.col("status") == "Open")
print(f"Open only (pruned): {open_only.count():,} rows")


# -----------------------------------------------------------------------
# Reading CSV and JSON — the misery formats
# -----------------------------------------------------------------------
# CSV: no dtypes (everything is a string unless you specify a schema)
# JSON: no dtypes, no compression, verbose
# Both: no predicate pushdown, no partition pruning
# Use only when you have to. Convert to Parquet ASAP.

# CSV read with header + inferred schema
csv_example = spark.read.option("header", "true") \
    .option("inferSchema", "true") \
    .csv("/tmp/incoming/*.csv")

# JSON — one JSON object per line (JSONL is Spark's default assumption)
json_example = spark.read.json("/tmp/incoming/events.json")


# -----------------------------------------------------------------------
# Production shape — a daily ingest job
# -----------------------------------------------------------------------
# What a real DE writes in Airflow every night:

def daily_ingest():
    """Extract from Postgres, transform, land in the lake as Parquet."""

    # 1. Extract
    src = spark.read.jdbc(
        url=jdbc_url,
        table="claims",
        column="claim_id",
        lowerBound=1,
        upperBound=100_000,
        numPartitions=8,
        properties=jdbc_props,
    )

    # 2. Add ingestion metadata (the Bronze contract, Module 06 §6.5)
    enriched = src \
        .withColumn("_ingested_at", F.current_timestamp()) \
        .withColumn("_source_system", F.lit("postgres.novabuilds")) \
        .withColumn("_ingestion_date", F.current_date())

    # 3. Land partitioned by ingest date (append-only Bronze)
    enriched.write \
        .mode("append") \
        .partitionBy("_ingestion_date") \
        .parquet("/tmp/novabuild_lake/bronze/claims")

    print(f"[daily_ingest] wrote {enriched.count():,} rows")


# =====================================================================
# Concepts demonstrated
#
#   * JDBC reads with partitioning options for parallelism
#   * Parquet as the lakehouse default format
#   * Write modes (overwrite / append / ignore / error)
#   * partitionBy() at write time and how it enables partition pruning
#   * Reading CSV and JSON with header + inferSchema
#   * A production-shape daily ingest with ingestion metadata columns
# =====================================================================
