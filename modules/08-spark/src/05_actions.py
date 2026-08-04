"""
Module 08 · Section 8.5 — Actions vs Transformations

The single most important thing to understand about Spark:

  TRANSFORMATIONS are LAZY.
      .filter(), .select(), .withColumn(), .join(), .groupBy() —
      none of these run. They add nodes to the query plan.

  ACTIONS trigger EXECUTION.
      .show(), .count(), .collect(), .take(), .first(), .write.*() —
      these force Spark to actually run the plan.

If you write 100 transformations and never call an action, Spark did
NO work. If you call .count() 5 times, Spark ran the whole pipeline 5
times unless you cached.
"""

from pyspark.sql import functions as F

claims = spark.read.jdbc(url=jdbc_url, table="claims", properties=jdbc_props)


# -----------------------------------------------------------------------
# Example — this does NOTHING
# -----------------------------------------------------------------------
# All three lines add nodes to the plan. Zero rows read.

plan_only = claims \
    .filter(F.col("status") == "Open") \
    .filter(F.col("incurred_loss") > 100_000) \
    .withColumn("year", F.year(F.col("loss_date")))

print("Plan built — no execution yet.")
print(type(plan_only))     # DataFrame


# -----------------------------------------------------------------------
# Action 1 — show(N)
# -----------------------------------------------------------------------
# Executes the plan, brings the first N rows to the driver, prints.
plan_only.show(5)


# -----------------------------------------------------------------------
# Action 2 — count()
# -----------------------------------------------------------------------
# Full scan. Returns a single number.
n = plan_only.count()
print(f"count: {n:,}")


# -----------------------------------------------------------------------
# Action 3 — take(N)
# -----------------------------------------------------------------------
# Returns the first N rows as a Python LIST of Row objects.
# Cheaper than collect() — Spark stops as soon as N rows are gathered.
first_three = plan_only.take(3)
for row in first_three:
    print(f"  {row.claim_id} - {row.incurred_loss}")


# -----------------------------------------------------------------------
# Action 4 — collect()
# -----------------------------------------------------------------------
# Brings the ENTIRE DataFrame to the driver as a Python list.
# DANGEROUS on large data — you're pulling potentially millions of rows
# into a single JVM's memory. Use only when you know the result is small
# (e.g. after aggregation).

# Safe example — an aggregation result should always be small.
summary = claims.groupBy("status").count().collect()
for row in summary:
    print(f"  {row.status}: {row['count']:,}")


# -----------------------------------------------------------------------
# Action 5 — first()
# -----------------------------------------------------------------------
# Same as take(1)[0]. Returns a Row.
first = plan_only.first()
print(f"first: {first}")


# -----------------------------------------------------------------------
# Action 6 — write.*()
# -----------------------------------------------------------------------
# Any of the write methods (parquet, jdbc, csv, delta) is an action —
# it forces the pipeline to run and materialises output.

# plan_only.write.mode("overwrite").parquet("/tmp/big_losses")


# -----------------------------------------------------------------------
# Caching — when you'll act on the same DataFrame multiple times
# -----------------------------------------------------------------------
# Without caching, every action re-runs the whole plan.
# .cache() and .persist() tell Spark to keep the result of a DataFrame
# in memory (or disk).

# Trigger action 5 times WITHOUT caching — Spark reads Postgres 5 times.
# expensive_stage = claims.join(contractors, ...).filter(...)
# expensive_stage.count()
# expensive_stage.count()  # re-runs everything!

# With caching:
expensive_stage = plan_only.cache()

# First action materialises + caches.
expensive_stage.count()

# Subsequent actions read from cache — much faster.
expensive_stage.count()
expensive_stage.show(5)

# Unpersist when done to free memory.
expensive_stage.unpersist()


# =====================================================================
# Common actions vs transformations reference
#
#   Transformations (lazy — return a new DataFrame):
#     select, filter, where, withColumn, drop, join, union,
#     groupBy, agg, orderBy, sort, distinct, dropDuplicates,
#     limit, repartition, coalesce, sample
#
#   Actions (eager — trigger the plan):
#     show, count, collect, take, first, head, foreach,
#     write, save, saveAsTable, toPandas
# =====================================================================
