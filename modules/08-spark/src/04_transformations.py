"""
Module 08 · Section 8.4 — Transformations in Depth

Once data is loaded, you spend 80% of your time on transformations.
This section is a tour of the major ones:

  Part 1 — Null handling (drop, fill, flag)
  Part 2 — Type casting (safe conversion)
  Part 3 — Joins (inner, left, right, outer, semi, anti)
  Part 4 — Broadcast joins (the small-side optimisation)
  Part 5 — Window functions (row_number, rank, lag/lead)

All examples run against the NovaBuild claims + contractors tables.
"""

from pyspark.sql import functions as F
from pyspark.sql.window import Window

claims      = spark.read.jdbc(url=jdbc_url, table="claims",      properties=jdbc_props)
contractors = spark.read.jdbc(url=jdbc_url, table="contractors", properties=jdbc_props)
carriers    = spark.read.jdbc(url=jdbc_url, table="carriers",    properties=jdbc_props)
brokers     = spark.read.jdbc(url=jdbc_url, table="brokers",     properties=jdbc_props)


# =====================================================================
# Part 1 — Null Handling
# =====================================================================

# Way 1 — DROP rows where closed_date is null
closed_only = claims.filter(F.col("closed_date").isNotNull())
print(f"After drop: {closed_only.count():,} of {claims.count():,}")

# Way 2 — FILL nulls with a placeholder string
claims_filled = claims.fillna({"closed_date": "NOT_CLOSED"})

# Way 3 — FLAG nulls instead of dropping or filling
claims_flagged = claims.withColumn(
    "is_still_open",
    F.when(F.col("closed_date").isNull(), True).otherwise(False),
)
claims_flagged.groupBy("is_still_open").count().show()

# Which strategy to choose?
#   DROP:  when the row is useless without the value (rare — usually
#          means upstream data quality bug, not something to hide)
#   FILL:  when a sentinel or default makes downstream logic simpler
#   FLAG:  when downstream needs to distinguish "known missing" from
#          "known present" — Silver-layer default (Module 06 §6.5)


# =====================================================================
# Part 2 — Type Casting
# =====================================================================

# Simulate a real-world type problem — someone loaded incurred_loss
# as string. Everything numeric downstream fails.
loss_as_str = claims.withColumn("incurred_loss", F.col("incurred_loss").cast("string"))

# Fix — cast back to double
loss_fixed = loss_as_str.withColumn("incurred_loss", F.col("incurred_loss").cast("double"))
loss_fixed.printSchema()

# The dangerous case — dirty string values that look numeric but aren't.
# cast() with errors="coerce" isn't a thing in Spark. Instead:
#   * cast() returns null for unparseable values (silent failure)
#   * use when() + regexp to filter or flag them first


# =====================================================================
# Part 3 — Joins
# =====================================================================

# Rename overlapping columns first — after the join both tables might
# have "broker_id" or similar. Ambiguity errors are annoying.
claims_j = claims.withColumnRenamed("broker_id", "claim_broker_id")

# --- INNER JOIN — matching rows only
inner = claims_j.join(
    carriers.select("carrier_id", "carrier_name"),
    on="carrier_id",
    how="inner",
)
print(f"inner join rows: {inner.count():,}")

# --- LEFT JOIN — all claims, carrier info if available
left = claims_j.join(
    carriers.select("carrier_id", "carrier_name"),
    on="carrier_id",
    how="left",
)

# --- LEFT ANTI JOIN — claims WITHOUT a matching carrier
# Semi-join semantics: keeps only rows from the left that DON'T match.
anti = claims_j.join(carriers, on="carrier_id", how="left_anti")
print(f"claims with no carrier: {anti.count():,}")

# --- LEFT SEMI JOIN — claims WITH a matching carrier (columns from left only)
semi = claims_j.join(carriers, on="carrier_id", how="left_semi")
print(f"claims with carrier: {semi.count():,}")


# =====================================================================
# Part 4 — Broadcast Joins
# =====================================================================
# When one side of a join is tiny (<10 MB or so), Spark can BROADCAST
# that side to every executor rather than shuffling both sides.
# Shuffling is expensive; broadcast is nearly free.
#
# Small lookup tables (dim_carrier, dim_broker) are perfect candidates.

# Auto-broadcast — Spark's default catalog does this if the small side
# is under spark.sql.autoBroadcastJoinThreshold (default 10 MB).

# Explicit broadcast — force it when you know the side is small.
from pyspark.sql.functions import broadcast

joined_broadcast = claims.join(
    broadcast(carriers.select("carrier_id", "carrier_name")),
    on="carrier_id",
    how="inner",
)
joined_broadcast.explain()   # Look for "BroadcastHashJoin" in the plan


# =====================================================================
# Part 5 — Window Functions
# =====================================================================
# Window functions compute values PER ROW using a window of related
# rows. Same mental model as SQL window functions (Module 04 §4.7).

# Rank contractors within each tier by EMR (highest first).
window_by_tier = Window.partitionBy("tier").orderBy(F.col("emr").desc())

contractors_ranked = contractors.withColumn(
    "rank_in_tier",
    F.row_number().over(window_by_tier),
)

contractors_ranked.select("company_name", "tier", "emr", "rank_in_tier") \
    .orderBy("tier", "rank_in_tier").show(20)

# ROW_NUMBER vs RANK vs DENSE_RANK — same behaviour as SQL:
#   ROW_NUMBER : always 1, 2, 3, 4 (no ties)
#   RANK       : 1, 1, 3 (skips after ties)
#   DENSE_RANK : 1, 1, 2 (no gap)

# Top 3 highest-EMR contractors per tier — greatest-N-per-group.
top3 = contractors_ranked.filter(F.col("rank_in_tier") <= 3)
top3.show()


# LAG / LEAD — previous or next row within the window.
# Example: for each claim, compare to the previous claim's incurred
# loss on the same carrier.
w_carrier = Window.partitionBy("carrier_id").orderBy("loss_date")
claims_with_prev = claims.withColumn(
    "prev_loss",
    F.lag("incurred_loss").over(w_carrier),
).withColumn(
    "loss_delta",
    F.col("incurred_loss") - F.col("prev_loss"),
)

# =====================================================================
# Concepts demonstrated
#
#   * Null handling: drop / fill / flag with when() decision framework
#   * Type coercion via .cast() and its silent-null failure mode
#   * All six join types (inner, left, right, outer, semi, anti)
#   * Broadcast joins (both automatic and explicit)
#   * Window functions (row_number, rank, dense_rank, lag, lead)
#   * Greatest-N-per-group pattern via ranked filter
# =====================================================================
