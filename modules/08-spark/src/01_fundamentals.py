"""
Module 08 · Section 8.1 — Spark Fundamentals + First Pipeline

The mental model:
  Spark = a distributed engine that turns Python/SQL into a job graph,
  splits data into partitions, ships work to executors, and collects
  results back to the driver.

You never write the parallel code. Spark does that. You write the
transformations declaratively.

This section builds your first end-to-end pipeline on the NovaBuild
dataset:
  Source:  8 PostgreSQL tables (claims, contractors, safety_incidents, ...)
  Task:    OSHA-recordable incidents by contractor tier + risk flag
  Target:  Aggregated report showing incident count + average EMR
           per (tier, risk_flag)
"""

from pyspark.sql import functions as F
from pyspark.sql.functions import count, when, round as spark_round, avg

# Assumes SparkSession + jdbc_url + jdbc_props already exist from setup/.
# In Colab: %run setup/colab_setup.py before running this file.


# -----------------------------------------------------------------------
# Step 1 — Load the tables we need
# -----------------------------------------------------------------------
# spark.read.jdbc pulls a full table from Postgres and represents it as
# a DataFrame — the primary distributed abstraction in Spark.

claims          = spark.read.jdbc(url=jdbc_url, table="claims",           properties=jdbc_props)
contractors     = spark.read.jdbc(url=jdbc_url, table="contractors",      properties=jdbc_props)
safety_incidents = spark.read.jdbc(url=jdbc_url, table="safety_incidents", properties=jdbc_props)

print(f"claims rows          : {claims.count():,}")
print(f"contractors rows     : {contractors.count():,}")
print(f"safety_incidents rows: {safety_incidents.count():,}")


# -----------------------------------------------------------------------
# Step 2 — Filter to OSHA-recordable incidents only
# -----------------------------------------------------------------------
# The .filter() call adds a node to the query plan; nothing runs yet.
# Spark is LAZY — transformations are only executed when an action
# (.count(), .show(), .write(), .collect()) is called. Section 8.5
# covers actions in depth.

osha_incidents = safety_incidents.filter(F.col("osha_recordable") == True)


# -----------------------------------------------------------------------
# Step 3 — Join to contractors to bring tier + EMR into scope
# -----------------------------------------------------------------------
# This is an INNER JOIN. Section 8.4 covers left/right/broadcast joins.

incidents_with_tier = osha_incidents.join(
    contractors.select("contractor_id", "company_name", "tier", "emr"),
    on="contractor_id",
    how="inner",
)

print(f"incidents joined to contractors: {incidents_with_tier.count():,}")


# -----------------------------------------------------------------------
# Step 4 — The capstone pipeline — one chained expression
# -----------------------------------------------------------------------
# Real Spark code is written in chained form. Each step feeds the next.
# Read top-to-bottom: withColumn -> groupBy -> agg -> orderBy.

final_summary = (
    incidents_with_tier
    .withColumn(
        "risk_flag",
        when(F.col("severity") == "Fatality",  "CRITICAL")
        .when(F.col("severity") == "Lost Time", "HIGH")
        .when(F.col("severity") == "Recordable", "MEDIUM")
        .otherwise("LOW"),
    )
    .groupBy("tier", "risk_flag")
    .agg(
        count("incident_id").alias("incident_count"),
        spark_round(avg("emr"), 2).alias("avg_emr"),
    )
    .orderBy("tier", "risk_flag")
)

final_summary.show(truncate=False)


# =====================================================================
# Concepts demonstrated
#
#   * SparkSession as the entry point for all Spark work
#   * DataFrame — the distributed table abstraction
#   * spark.read.jdbc for loading from an external database
#   * .filter() as a lazy transformation
#   * .join() with an inner join
#   * .withColumn() + when/otherwise for conditional column creation
#   * .groupBy(...).agg(...) — the workhorse aggregation pattern
#   * .orderBy() as the final sort
#   * Lazy evaluation — the whole pipeline only runs when .show() fires
# =====================================================================
