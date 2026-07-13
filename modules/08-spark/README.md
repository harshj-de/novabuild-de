# Module 08 — Apache Spark & Delta Lake on Databricks

**Status:** Migration in progress · notebooks and PySpark modules landing in `notebooks/` and `src/`.

The distributed-computing tier of the NovaBuild platform. Covers PySpark, Delta Lake, and Databricks Workflows — the stack that runs production data pipelines at every serious InsurTech and enterprise DE shop.

---

## What This Module Demonstrates

- **Spark architecture fluency** — drivers, executors, stages, tasks, shuffle mechanics, and why they matter for job performance
- **RDDs, DataFrames, Datasets** — when to use each, why DataFrames dominate modern PySpark work
- **Advanced DataFrame operations** — window functions, broadcast joins for skewed data, salt-based skew mitigation, cache/persist strategy
- **Spark SQL** — running the NovaBuild queries from Module 04 at distributed scale
- **UDFs (Python and Pandas/Arrow)** — plus the performance trade-offs of each
- **Partitioning strategy** — physical partitioning, coalesce vs. repartition, avoiding small-file problems
- **Delta Lake** — ACID transactions on the lakehouse, time travel, MERGE INTO for upserts, OPTIMIZE + ZORDER for query performance, VACUUM lifecycle, transaction log internals
- **Structured Streaming** — micro-batch and continuous processing modes, checkpointing, watermarking for late-arriving data
- **Databricks Medallion Pipeline** — Bronze / Silver / Gold applied end-to-end to NovaBuild ingestion, transformation, and aggregation
- **Databricks Workflows** — job orchestration, task dependencies, retry logic, alerting
- **MLflow tracking** — experiment logging for risk-scoring model iterations

---

## Structure
---

## Skills Demonstrated

`PySpark` · `Delta Lake` · `Databricks` · `Structured Streaming` · `Medallion Architecture` · `Broadcast Joins` · `Window Functions` · `Partitioning` · `MLflow` · `Databricks Workflows`

---

## Domain Context

The full Bronze → Silver → Gold pipeline is built against the NovaBuild insurance dataset. Bronze ingests raw contractor, policy, and claims records; Silver applies conformance and quality gates; Gold produces the risk-scoring and executive-reporting tables that feed Module 12's FastAPI service. See [`/datasets`](../../datasets).

---

## Runtime Environment

Developed in Google Colab (PySpark 3.5.3 + delta-spark 3.2.0) and Databricks Free Edition. Both are documented in the notebooks so a reviewer can reproduce either environment.
