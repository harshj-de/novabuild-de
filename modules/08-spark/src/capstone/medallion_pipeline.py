"""
Module 08 · Capstone — Medallion Pipeline on Delta Lake

The final Module 08 artifact. Everything from §8.1-8.9 tied together
into a production-shape Bronze/Silver/Gold pipeline that:

  1. Ingests from Postgres via JDBC (§8.3)
  2. Lands raw in Bronze as Delta (§8.9)
  3. Cleans + validates into Silver (§8.4)
  4. Aggregates + computes risk score in Gold (§8.6, §8.4)
  5. Uses windows (§8.4) and Delta MERGE (§8.9) throughout

Mirror of the Module 06 §6.5 Pandas-based Medallion pipeline, but
implemented at scale in Spark with Delta Lake.

Run this with the setup/ Spark session already initialised.
"""

from pyspark.sql import functions as F
from pyspark.sql.window import Window
from delta.tables import DeltaTable

LAKE_ROOT = "/tmp/novabuild_delta_lake"


# =====================================================================
# BRONZE — raw ingestion
# =====================================================================

def load_bronze():
    """Extract from Postgres, land raw in Bronze with ingestion metadata."""

    tables = ["contractors", "claims", "safety_incidents", "certificates"]

    for name in tables:
        src = spark.read.jdbc(url=jdbc_url, table=name, properties=jdbc_props)

        # The Bronze contract — ingestion metadata columns.
        enriched = (src
            .withColumn("_ingested_at",   F.current_timestamp())
            .withColumn("_source_system", F.lit("postgres.novabuilds"))
            .withColumn("_ingestion_date", F.current_date())
        )

        # Land as Delta, partitioned by ingest date for time-travel & pruning.
        (enriched.write
            .format("delta")
            .mode("append")
            .partitionBy("_ingestion_date")
            .save(f"{LAKE_ROOT}/bronze/{name}")
        )

        print(f"[bronze] wrote {enriched.count():>7,} rows -> {name}")


# =====================================================================
# SILVER — cleaned, typed, validated
# =====================================================================
# Business-neutral cleaning. One row of Bronze -> at most one row of Silver.

def build_silver_contractors():
    src = spark.read.format("delta").load(f"{LAKE_ROOT}/bronze/contractors")

    df = (src
        .filter(F.col("contractor_id").isNotNull())
        .filter(F.col("emr").between(0.5, 3.0))                     # sensible EMR range
        .withColumn("contractor_id", F.trim(F.upper(F.col("contractor_id"))))
        .withColumn("state", F.trim(F.upper(F.col("state"))))
        # Deduplicate — keep only the latest ingestion for each id.
        .withColumn(
            "_rank",
            F.row_number().over(
                Window.partitionBy("contractor_id").orderBy(F.desc("_ingested_at"))
            ),
        )
        .filter(F.col("_rank") == 1)
        .drop("_rank")
    )

    (df.write
        .format("delta")
        .mode("overwrite")
        .save(f"{LAKE_ROOT}/silver/contractors")
    )
    print(f"[silver] contractors: {df.count():,}")


def build_silver_claims():
    src = spark.read.format("delta").load(f"{LAKE_ROOT}/bronze/claims")

    df = (src
        .filter(F.col("claim_id").isNotNull())
        .filter(F.col("loss_date").isNotNull())
        .filter(F.col("incurred_loss") >= 0)
        # Cast money columns explicitly to double.
        .withColumn("incurred_loss", F.col("incurred_loss").cast("double"))
        # Add a quality-flag column instead of dropping partial rows.
        .withColumn(
            "quality_flag",
            F.when(F.col("closed_date").isNull(), "OPEN")
             .when(F.col("adjuster_name").isNull(), "MISSING_ADJUSTER")
             .otherwise("CLEAN"),
        )
    )

    (df.write.format("delta").mode("overwrite").save(f"{LAKE_ROOT}/silver/claims"))
    print(f"[silver] claims: {df.count():,}")


def build_silver_safety_incidents():
    src = spark.read.format("delta").load(f"{LAKE_ROOT}/bronze/safety_incidents")

    df = (src
        .filter(F.col("contractor_id").isNotNull())
        .filter(F.col("incident_date").isNotNull())
        .withColumn("contractor_id", F.trim(F.upper(F.col("contractor_id"))))
    )

    (df.write.format("delta").mode("overwrite").save(f"{LAKE_ROOT}/silver/safety_incidents"))
    print(f"[silver] safety_incidents: {df.count():,}")


# =====================================================================
# GOLD — business-facing aggregates
# =====================================================================
# One Gold table per business consumer.
# Each has an owner (Underwriting / Executive / Claims Ops).

def build_gold_contractor_risk_profile():
    """
    Per-contractor risk rollup. Powers the underwriter contractor page.
    """
    c = spark.read.format("delta").load(f"{LAKE_ROOT}/silver/contractors")
    cl = spark.read.format("delta").load(f"{LAKE_ROOT}/silver/claims")
    si = spark.read.format("delta").load(f"{LAKE_ROOT}/silver/safety_incidents")

    claim_agg = (cl
        .groupBy("contractor_id")
        .agg(
            F.count("claim_id").alias("claim_count"),
            F.sum("incurred_loss").alias("total_incurred"),
            F.max("incurred_loss").alias("largest_claim"),
        )
    )

    incident_agg = (si
        .groupBy("contractor_id")
        .agg(F.count("incident_id").alias("incident_count"))
    )

    gold = (c
        .join(claim_agg,    on="contractor_id", how="left")
        .join(incident_agg, on="contractor_id", how="left")
        .fillna({"claim_count": 0, "total_incurred": 0,
                 "largest_claim": 0, "incident_count": 0})
        # Weighted risk score — simple demonstration formula.
        .withColumn(
            "risk_score",
            F.col("emr") * 40
            + (F.col("claim_count") / F.greatest(F.col("employees_count"), F.lit(1))) * 30
            + (F.col("incident_count") / F.greatest(F.col("employees_count"), F.lit(1))) * 30,
        )
        .withColumn(
            "risk_tier",
            F.when(F.col("risk_score") < 40, "Low")
             .when(F.col("risk_score") < 70, "Medium")
             .when(F.col("risk_score") < 100, "High")
             .otherwise("Severe"),
        )
    )

    # Delta MERGE (upsert) — the idempotent Gold refresh pattern.
    target_path = f"{LAKE_ROOT}/gold/contractor_risk_profile"

    if DeltaTable.isDeltaTable(spark, target_path):
        target = DeltaTable.forPath(spark, target_path)
        (target.alias("t").merge(
            gold.alias("s"),
            "t.contractor_id = s.contractor_id",
        )
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute())
    else:
        gold.write.format("delta").mode("overwrite").save(target_path)

    print(f"[gold] contractor_risk_profile: {gold.count():,}")


def build_gold_monthly_loss():
    """Monthly aggregated losses. Powers exec dashboard line chart."""
    cl = spark.read.format("delta").load(f"{LAKE_ROOT}/silver/claims")

    gold = (cl
        .withColumn("month", F.date_trunc("month", F.col("loss_date")))
        .groupBy("month")
        .agg(
            F.count("claim_id").alias("claim_count"),
            F.sum("incurred_loss").alias("total_incurred"),
        )
        .orderBy("month")
    )

    (gold.write.format("delta").mode("overwrite").save(f"{LAKE_ROOT}/gold/monthly_loss"))
    print(f"[gold] monthly_loss: {gold.count():,}")


# =====================================================================
# Orchestrator
# =====================================================================

def run_pipeline():
    """Full Bronze → Silver → Gold refresh."""
    print("=== MEDALLION PIPELINE START ===")

    load_bronze()

    build_silver_contractors()
    build_silver_claims()
    build_silver_safety_incidents()

    build_gold_contractor_risk_profile()
    build_gold_monthly_loss()

    print("=== PIPELINE DONE ===")


if __name__ == "__main__":
    run_pipeline()


# =====================================================================
# Concepts demonstrated
#
#   * Full 3-layer Medallion on Delta at Spark scale
#   * Ingestion-metadata contract in Bronze
#   * Silver quality gates via filter + row_number dedupe pattern
#   * Delta MERGE for idempotent Gold refresh
#   * Window functions for latest-per-key extraction
#   * partitionBy(_ingestion_date) for pruning + time travel
#   * Same pipeline shape as Module 06 §6.5 (Pandas) — now distributed
# =====================================================================
