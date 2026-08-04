"""
Module 08 · Section 8.8 — Partitioning and Performance

Every Spark job eventually hits performance issues. The main levers:

  1. Number and size of partitions
  2. Broadcast vs shuffle joins
  3. Data skew mitigation (salting)
  4. Adaptive Query Execution (AQE)
  5. Choice of file format (Parquet > CSV always)

This section covers all four.
"""

from pyspark.sql import functions as F

claims = spark.read.jdbc(url=jdbc_url, table="claims", properties=jdbc_props)


# =====================================================================
# 1. repartition vs coalesce (recap from §8.2)
# =====================================================================
# repartition(N) does a FULL SHUFFLE — every row can move partition.
#   * Expensive
#   * Produces balanced partitions
#   * Use when increasing partitions or when skew fix is needed
#
# coalesce(N) MERGES adjacent partitions — no shuffle.
#   * Cheap
#   * Can produce skewed partitions
#   * Use when reducing partitions (e.g. after a heavy filter)

heavily_filtered = claims.filter(F.col("incurred_loss") > 1_000_000)
print(f"before coalesce: {heavily_filtered.rdd.getNumPartitions()}")
small = heavily_filtered.coalesce(2)
print(f"after coalesce:  {small.rdd.getNumPartitions()}")


# =====================================================================
# 2. partitionBy at write time (recap from §8.3)
# =====================================================================
# The write-time partition scheme determines how downstream reads work.
# Query patterns should drive the choice:
#   Filters on status?           partitionBy("status")
#   Filters on date?             partitionBy("year", "month")
#   Filters on both?             partitionBy("status", "year", "month")


# =====================================================================
# 3. Adaptive Query Execution (AQE)
# =====================================================================
# AQE is a suite of runtime optimisations added in Spark 3:
#   * coalescePartitions: shrink over-shuffled output
#   * skewJoin: detect + salt-fix skewed joins automatically
#   * localShuffleReader: read shuffle output locally where possible
#
# Enabled in setup/colab_setup.py. Check:

print(f"AQE enabled: {spark.conf.get('spark.sql.adaptive.enabled')}")
print(f"AQE coalesce: {spark.conf.get('spark.sql.adaptive.coalescePartitions.enabled')}")
print(f"AQE skew:    {spark.conf.get('spark.sql.adaptive.skewJoin.enabled', 'true')}")


# =====================================================================
# 4. Data Skew and Salting
# =====================================================================
# A skewed join = one key value has WAY more rows than the others.
# One task has to process 1M rows while others process 100 each.
# Result: 99% of tasks finish in 1 second, one task takes 10 minutes.

# Simulate skewed data: 800 rows with key A, 50 each for B, C, D.
skewed_data = spark.createDataFrame(
    [("A", i) for i in range(800)] +
    [("B", i) for i in range(50)] +
    [("C", i) for i in range(50)] +
    [("D", i) for i in range(50)],
    ["key", "value"],
)

print("Distribution BEFORE salting:")
skewed_data.groupBy("key").count().orderBy(F.desc("count")).show()


# --- The salting fix ---
# Add a random suffix (0-3) to the skewed key. Now the "A" rows get
# distributed across 4 subkeys: A_0, A_1, A_2, A_3.

import random
salted = skewed_data.withColumn(
    "salt", (F.rand() * 4).cast("int")
).withColumn(
    "salted_key", F.concat(F.col("key"), F.lit("_"), F.col("salt"))
)

print("Distribution AFTER salting:")
salted.groupBy("salted_key").count().orderBy(F.desc("count")).show()

# The lookup table (right side of the join) has to be pre-expanded to
# have all 4 salted versions of each key. Then join on salted_key.
# Post-join you strip the salt back off.
#
# AQE's skewJoin does this for you automatically since Spark 3.0.
# You only need to do manual salting if you're on older Spark
# or need finer control.


# =====================================================================
# 5. Explain and plan reading
# =====================================================================
# .explain() prints the physical plan. Two levels of detail:
#
#   .explain()             — the physical plan
#   .explain(True)         — parsed / analysed / optimised / physical
#   .explain("formatted")  — pretty-printed physical plan

query = claims.filter(F.col("status") == "Open") \
    .groupBy("carrier_id") \
    .agg(F.sum("incurred_loss").alias("total"))

query.explain("formatted")

# Look for:
#   * SCAN — how much of the source is read
#   * FILTER — is the predicate pushed down to the source?
#   * SHUFFLE / EXCHANGE — is there an expensive shuffle?
#   * BROADCAST — is one side small enough to broadcast?


# =====================================================================
# 6. Caching decisions
# =====================================================================
# Cache when:
#   * You act on the same DataFrame 2+ times
#   * The computation to produce it is expensive
#   * The result fits in memory (or you can .persist(StorageLevel.DISK))
#
# Don't cache when:
#   * You only use the DataFrame once
#   * The intermediate is huge and won't fit
#   * Memory pressure would kick out useful RDDs

# from pyspark import StorageLevel
# df.persist(StorageLevel.MEMORY_AND_DISK)


# =====================================================================
# Rules of thumb
#
#   * Prefer Parquet + partitionBy for storage
#   * Enable AQE (Spark 3+) — free performance
#   * Watch for skew via Spark UI's stage-detail page
#   * Read .explain() output when a query is slow
#   * Cache multi-use DataFrames; unpersist when done
#   * Target ~128 MB per partition for reads; ~200 shuffle partitions
#     as a default (or let AQE decide)
# =====================================================================
