"""
Module 08 · Section 8.10 — Structured Streaming

Structured Streaming lets you write a batch-style query that runs on
an unbounded stream. Spark handles the incremental execution:
"reprocess every new micro-batch of data as it arrives."

Sources supported:
  * File sources (directory watching)
  * Kafka (Module 09 covers this in depth)
  * Rate source (for testing)

Sinks supported:
  * Console (for testing)
  * File (Parquet/Delta) — production default
  * Kafka
  * ForeachBatch (for custom sinks like JDBC)

This section demonstrates five streaming transformations against
NovaBuild claims + contractors data, ending with a Delta sink pattern.
"""

from pyspark.sql import functions as F
from pyspark.sql.types import (StructType, StructField, StringType,
                                DoubleType, TimestampType)


# -----------------------------------------------------------------------
# Setup — a folder to watch, and a schema for the incoming JSON
# -----------------------------------------------------------------------
STREAM_INPUT_DIR = "/tmp/novabuild_stream/incoming"
STREAM_OUTPUT_DIR = "/tmp/novabuild_stream/output"
STREAM_CHECKPOINT = "/tmp/novabuild_stream/checkpoint"

import os
os.makedirs(STREAM_INPUT_DIR, exist_ok=True)

# Schema for the incoming claim events (JSON one-per-line).
claim_schema = StructType([
    StructField("claim_id",       StringType()),
    StructField("contractor_id",  StringType()),
    StructField("incurred_loss",  DoubleType()),
    StructField("loss_date",      TimestampType()),
    StructField("claim_type",     StringType()),
])


# -----------------------------------------------------------------------
# Transformation 1 — Basic file stream
# -----------------------------------------------------------------------
# Watch a folder for new JSON files. Every new file triggers a
# micro-batch. maxFilesPerTrigger caps how many files per batch.

basic_stream = (spark.readStream
    .schema(claim_schema)
    .option("maxFilesPerTrigger", 1)
    .json(STREAM_INPUT_DIR)
)

# Streaming DataFrames are still DataFrames — the same transformations
# work. Write to console for testing.
query_basic = (basic_stream
    .writeStream
    .format("console")
    .outputMode("append")
    .trigger(processingTime="10 seconds")
    .start()
)

# In production you'd never write to console — this is dev/testing only.
# query_basic.awaitTermination()   # would block indefinitely
# query_basic.stop()                # stop before starting the next stream


# -----------------------------------------------------------------------
# Transformation 2 — Stream + Static Join (enrich stream with dim)
# -----------------------------------------------------------------------
# Very common pattern: stream of events joined against a small static
# dimension.

contractors_static = spark.read.jdbc(
    url=jdbc_url, table="contractors", properties=jdbc_props
).select("contractor_id", "company_name", "tier", "emr")

enriched_stream = basic_stream.join(
    contractors_static,
    on="contractor_id",
    how="inner",
)

query_enriched = (enriched_stream
    .writeStream
    .format("console")
    .outputMode("append")
    .start()
)


# -----------------------------------------------------------------------
# Transformation 3 — Aggregation with Watermark + Tumbling Window
# -----------------------------------------------------------------------
# When aggregating a stream, you need a WATERMARK to tell Spark when
# it's safe to close a window (declare "no more late data will come
# for this bucket").
#
# Tumbling window = fixed non-overlapping intervals (10 sec, 1 min, ...)

windowed_agg = (basic_stream
    .withWatermark("loss_date", "1 hour")   # allow 1h of late arrivals
    .groupBy(
        F.window("loss_date", "10 minutes"),
        "claim_type",
    )
    .agg(
        F.count("*").alias("claim_count"),
        F.sum("incurred_loss").alias("total_loss"),
    )
)

query_windowed = (windowed_agg
    .writeStream
    .format("console")
    .outputMode("complete")   # "update" or "complete" required with agg
    .start()
)


# -----------------------------------------------------------------------
# Transformation 4 — Live Broker Performance Scorecard
# -----------------------------------------------------------------------
# Real use case: aggregate incoming claims per broker in real time,
# label brokers whose loss volume crosses a threshold.

brokers_static = spark.read.jdbc(
    url=jdbc_url, table="brokers", properties=jdbc_props
).select("broker_id", "broker_name")

policies_static = spark.read.jdbc(
    url=jdbc_url, table="policies", properties=jdbc_props
).select("policy_id", "broker_id", "premium_amount")

# Join claim stream -> policies (to get broker_id) -> brokers (name)
# Then aggregate per broker with a 30-minute window.

broker_scorecard = (basic_stream
    .join(policies_static, on="policy_id", how="inner")
    .join(brokers_static, on="broker_id", how="inner")
    .withWatermark("loss_date", "2 hours")
    .groupBy(
        F.window("loss_date", "30 minutes"),
        "broker_id",
        "broker_name",
    )
    .agg(
        F.count("*").alias("claim_count"),
        F.sum("incurred_loss").alias("total_loss"),
    )
    .withColumn(
        "risk_label",
        F.when(F.col("total_loss") > 1_000_000, "HIGH")
         .when(F.col("total_loss") > 100_000, "MEDIUM")
         .otherwise("LOW"),
    )
)


# -----------------------------------------------------------------------
# Transformation 5 — Delta Sink (the production pattern)
# -----------------------------------------------------------------------
# Console is for testing. Real streaming pipelines land in a Delta
# table on a durable storage system. Delta gives you exactly-once
# semantics + time travel + downstream batch queries.

delta_query = (basic_stream
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", STREAM_CHECKPOINT)
    .trigger(processingTime="30 seconds")
    .start(STREAM_OUTPUT_DIR)
)

# checkpointLocation is REQUIRED for delta sink. It stores the offset
# metadata so Spark can resume from where it left off if the job crashes.

# Read the Delta table like any other batch table (below the streaming
# job continues writing to it in real time):
#
#     landed = spark.read.format("delta").load(STREAM_OUTPUT_DIR)
#     landed.groupBy("claim_type").count().show()


# =====================================================================
# Concepts demonstrated
#
#   * File-source streaming with schema + maxFilesPerTrigger
#   * Streaming DataFrame is a normal DataFrame — same transformations
#   * Stream + Static join (enrich with dimensions)
#   * Watermark + tumbling window for stateful aggregation
#   * Multi-table stream pipeline with business-logic label
#   * Delta sink pattern for production durability
#   * outputMode: append (transformations) vs update / complete (aggregations)
#   * Trigger control: processingTime for cadence, availableNow for backfill
# =====================================================================
