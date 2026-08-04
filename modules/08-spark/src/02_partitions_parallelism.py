"""
Module 08 · Section 8.2 — Partitions and Parallelism

Every Spark DataFrame is split into PARTITIONS — chunks of rows that
live on different executors. Partitions are the unit of parallelism.

Rule of thumb:
  * More partitions => more parallelism (up to core count)
  * Too many partitions => overhead per task dominates
  * Too few partitions => some cores sit idle, memory pressure per partition

This section shows how to inspect and reason about partitioning on the
NovaBuild data.

Assumes SparkSession + jdbc_url + jdbc_props from setup/.
"""

from pyspark.sql import functions as F

safety_incidents = spark.read.jdbc(url=jdbc_url, table="safety_incidents",
                                    properties=jdbc_props)


# -----------------------------------------------------------------------
# Inspect the current partition count
# -----------------------------------------------------------------------
# Every DataFrame carries a partitioning. rdd.getNumPartitions() reveals
# the current number.

n_before = safety_incidents.rdd.getNumPartitions()
print(f"safety_incidents partitions after JDBC load: {n_before}")

# JDBC without partitioning options ALWAYS loads into ONE partition —
# a single connection to Postgres pulls the whole table serially.
# This becomes a performance disaster on large tables. Section 8.3
# covers partitioned JDBC reads.


# -----------------------------------------------------------------------
# Increase parallelism via repartition
# -----------------------------------------------------------------------
# .repartition(N) does a FULL SHUFFLE — every row moves across the
# network to land in one of N new partitions. Expensive but produces
# balanced partitions.

incidents_8 = safety_incidents.repartition(8)
print(f"After repartition(8): {incidents_8.rdd.getNumPartitions()}")


# -----------------------------------------------------------------------
# Decrease partitions via coalesce
# -----------------------------------------------------------------------
# .coalesce(N) MERGES adjacent partitions without shuffling. Cheap but
# can produce skewed sizes. Use when reducing partitions after a heavy
# filter that shrunk the data.

incidents_2 = safety_incidents.repartition(8).coalesce(2)
print(f"After coalesce(2): {incidents_2.rdd.getNumPartitions()}")


# -----------------------------------------------------------------------
# Show partition-level counts — where the data actually is
# -----------------------------------------------------------------------
# spark_partition_id() is a function that returns the partition each
# row belongs to. groupBy it to see distribution.

incidents_8.withColumn("pid", F.spark_partition_id()) \
    .groupBy("pid").count().orderBy("pid").show()


# -----------------------------------------------------------------------
# The severity aggregation from Section 8.1 — with partition awareness
# -----------------------------------------------------------------------
# groupBy triggers a shuffle. Look at the output partitions of an
# aggregation vs the input.

severity_counts = safety_incidents.groupBy("severity").count()
print(f"After groupBy: {severity_counts.rdd.getNumPartitions()} partitions")
severity_counts.orderBy(F.desc("count")).show()

# The default post-shuffle partition count is controlled by
# spark.sql.shuffle.partitions (default: 200). For small datasets this
# is wasteful. AQE (enabled in setup/) auto-tunes it — Section 8.8.


# =====================================================================
# Rules of thumb
#
#   * JDBC without partitioning options => 1 partition. Bad for large tables.
#   * After a heavy filter, use .coalesce() to reduce partitions.
#   * After a heavy join or aggregation, let AQE handle partition tuning.
#   * Target ~128-200 MB per partition for parquet writes.
#   * Rule: sf-part-count = round(dataset_size_gb / 0.128) then cap at 200.
# =====================================================================
