"""
Module 08 · Section 8.9 — Delta Lake

Delta Lake adds ACID transactions, time travel, and MERGE (upsert) to
plain Parquet. It's the storage format for Databricks and one of the
three lakehouse table formats (Delta, Iceberg, Hudi).

What Delta gives you over plain Parquet:
  * ACID transactions       — no partial writes
  * Schema enforcement      — bad rows rejected at write time
  * Schema evolution        — add columns without breaking readers
  * Time travel             — query the table as it looked at any past version
  * MERGE (upsert)          — one-statement insert-or-update
  * VACUUM                  — clean up old file versions
  * OPTIMIZE + Z-ORDER      — layout tuning for fast reads

To run locally / in Colab, install delta-spark and reconfigure Spark:

    pip install delta-spark==3.1.0

    from delta import configure_spark_with_delta_pip
    builder = SparkSession.builder \\
        .appName("DeltaDemo") \\
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \\
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    spark = configure_spark_with_delta_pip(builder).getOrCreate()

This module assumes that setup has already happened.
"""

from pyspark.sql import functions as F
from delta.tables import DeltaTable

DELTA_PATH = "/tmp/novabuild_delta/claims"


# -----------------------------------------------------------------------
# Step 1 — Write the initial Delta table from Postgres
# -----------------------------------------------------------------------
claims = spark.read.jdbc(url=jdbc_url, table="claims", properties=jdbc_props)

claims.write \
    .format("delta") \
    .mode("overwrite") \
    .save(DELTA_PATH)

print(f"[delta] wrote {claims.count():,} rows to {DELTA_PATH}")


# -----------------------------------------------------------------------
# Step 2 — Load it back and inspect
# -----------------------------------------------------------------------
delta_df = spark.read.format("delta").load(DELTA_PATH)
delta_df.groupBy("status").count().orderBy("status").show()


# -----------------------------------------------------------------------
# Step 3 — UPDATE — impossible with plain Parquet, easy with Delta
# -----------------------------------------------------------------------
# Auto-close all Open claims with loss_date before 2022.

delta_table = DeltaTable.forPath(spark, DELTA_PATH)

n_before = spark.read.format("delta").load(DELTA_PATH) \
    .filter((F.col("status") == "Open") &
            (F.col("loss_date") < F.lit("2022-01-01"))).count()
print(f"Open claims before 2022: {n_before:,}")

delta_table.update(
    condition=(F.col("status") == "Open") & (F.col("loss_date") < F.lit("2022-01-01")),
    set={
        "status": F.lit("Closed"),
        "adjuster_name": F.lit("System Auto-Close"),
    },
)

print("After update:")
spark.read.format("delta").load(DELTA_PATH) \
    .groupBy("status").count().orderBy("status").show()


# -----------------------------------------------------------------------
# Step 4 — Time travel — see the table before AND after
# -----------------------------------------------------------------------
# Every Delta operation creates a new version. Read any historical
# version with .option("versionAsOf", N) or "timestampAsOf".

# Version 0 — before the auto-close
v0 = spark.read.format("delta").option("versionAsOf", 0).load(DELTA_PATH)
print("Version 0 (before update):")
v0.groupBy("status").count().orderBy("status").show()

# Current version — after the auto-close
current = spark.read.format("delta").load(DELTA_PATH)
print("Current version:")
current.groupBy("status").count().orderBy("status").show()

# See the full commit history:
delta_table.history().select(
    "version", "timestamp", "operation", "operationParameters"
).show(truncate=False)


# -----------------------------------------------------------------------
# Step 5 — DELETE
# -----------------------------------------------------------------------
# Remove Test-status claims from the table entirely.

# delta_table.delete(F.col("status") == "Test")


# -----------------------------------------------------------------------
# Step 6 — MERGE (upsert) — the killer Delta feature
# -----------------------------------------------------------------------
# MERGE lets you insert-new + update-existing in one atomic operation.
# The standard pattern for incremental loads.

# Suppose a fresh batch of claim updates arrives:
updates = spark.createDataFrame([
    ("CL-9001", 100_000.00, "Closed"),
    ("CL-9002", 250_000.00, "Open"),      # new claim
], ["claim_id", "incurred_loss", "status"])

delta_table.alias("target").merge(
    updates.alias("source"),
    "target.claim_id = source.claim_id"
).whenMatchedUpdate(
    set={
        "incurred_loss": "source.incurred_loss",
        "status":        "source.status",
    }
).whenNotMatchedInsert(
    values={
        "claim_id":      "source.claim_id",
        "incurred_loss": "source.incurred_loss",
        "status":        "source.status",
    }
).execute()


# -----------------------------------------------------------------------
# Step 7 — VACUUM — clean up old file versions
# -----------------------------------------------------------------------
# Every Delta write leaves the old files in place. Time travel needs
# them. But they accumulate. VACUUM removes files older than a
# retention threshold.
#
# Default retention: 168 hours (7 days). Set aggressively for demo.

# Careful — VACUUM with a short retention breaks time travel for
# older versions. Only use aggressive VACUUM after you're sure no
# process needs to query those versions.

# spark.sql(f"VACUUM delta.`{DELTA_PATH}` RETAIN 168 HOURS")


# -----------------------------------------------------------------------
# Step 8 — OPTIMIZE + Z-ORDER
# -----------------------------------------------------------------------
# OPTIMIZE compacts many small files into fewer large ones (better
# for query planning). Z-ORDER co-locates rows sharing values in the
# specified columns.

# spark.sql(f"OPTIMIZE delta.`{DELTA_PATH}` ZORDER BY (status, loss_date)")


# =====================================================================
# When to use Delta over plain Parquet
#
#   USE Delta when:
#     * You need ACID (concurrent writes / partial-failure protection)
#     * You need MERGE for incremental loads
#     * You need time travel for audit or bug-recovery
#     * You need schema evolution without downtime
#
#   Plain Parquet is fine when:
#     * Write-once-read-many with no updates
#     * Downstream doesn't need transactions
#     * You're on a platform that doesn't support Delta (fewer options each year)
# =====================================================================
