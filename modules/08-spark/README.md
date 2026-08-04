# Module 08 — Apache Spark for Data Engineering

Production-shape PySpark against the NovaBuild insurance dataset (the same
domain used in Modules 04, 06, and 12). Sections 8.1 through 8.13 covering
the full DE-relevant Spark surface: DataFrames, transformations, Spark SQL,
UDFs, performance tuning, Delta Lake, Structured Streaming, and MLflow.

Target platform: **PySpark 3.5+ on Colab or local Linux/macOS/WSL.**
Everything runs on the Databricks Free Edition equivalent stack — no
paid Databricks required for the module content itself.

---

## Sections

| # | Topic | Type | What you'll learn |
|---|---|---|---|
| 8.1 | Fundamentals | PySpark | SparkSession, DataFrames, first end-to-end pipeline |
| 8.2 | Partitions & Parallelism | PySpark | repartition vs coalesce, partition inspection |
| 8.3 | Reading & Writing Data | PySpark | JDBC with parallelism, Parquet, partitionBy, daily ingest |
| 8.4 | Transformations | PySpark | Null handling, casting, joins, broadcast, windows |
| 8.5 | Actions vs Transformations | PySpark | Lazy evaluation, when the plan actually runs |
| 8.6 | Spark SQL | Spark SQL | 16 queries, mixing SQL + DataFrame API |
| 8.7 | UDFs | PySpark | Regular, Pandas (vectorised), SQL-registered UDFs |
| 8.8 | Partitioning & Performance | PySpark | AQE, skew + salting, explain plans, caching |
| 8.9 | Delta Lake | Delta | ACID, time travel, MERGE, VACUUM, OPTIMIZE |
| 8.10 | Structured Streaming | PySpark | File stream, stream-static join, watermarks, Delta sink |
| 8.12 | Databricks Workflows | Docs | Multi-task jobs, DABs, compute selection (Lakeflow Jobs) |
| 8.13 | MLflow | Python | Tracking, model registry, batch scoring pattern |

Section 8.11 is intentionally skipped — the number was previously reserved
for the Databricks Free Edition Medallion demo, which is now the capstone.

---

## Structure

```
08-spark/
├── README.md                              (this file)
├── setup/
│   ├── colab_setup.py                     (JDBC driver + SparkSession)
│   └── novabuild_schema_reference.md      (table reference)
├── src/
│   ├── 01_fundamentals.py                 (§8.1)
│   ├── 02_partitions_parallelism.py       (§8.2)
│   ├── 03_reading_writing.py              (§8.3)
│   ├── 04_transformations.py              (§8.4)
│   ├── 05_actions.py                      (§8.5)
│   ├── 06_spark_sql.py                    (§8.6)
│   ├── 07_udfs.py                         (§8.7)
│   ├── 08_partitioning_performance.py     (§8.8)
│   ├── 09_delta_lake.py                   (§8.9)
│   ├── 10_structured_streaming.py         (§8.10)
│   ├── 11_mlflow.py                       (§8.13)
│   └── capstone/
│       └── medallion_pipeline.py          (Bronze/Silver/Gold on Delta)
├── docs/
│   └── databricks_workflows.md            (§8.12)
└── notebooks/
    ├── module8_spark.ipynb                (original — §8.1-8.9)
    └── module8_spark_full.ipynb           (extended — adds §8.10, §8.13)
```

---

## Getting started

### 1. Set connection variables

```bash
export PG_JDBC_URL="jdbc:postgresql://localhost:5432/novabuilds"
export PG_USER="saas_user"
export PG_PASSWORD="saas_pass"
```

### 2. Bootstrap Spark (Colab)

```python
%run setup/colab_setup.py
```

Or locally:

```bash
python setup/colab_setup.py
```

### 3. Run any section

```python
%run src/01_fundamentals.py
%run src/09_delta_lake.py
%run src/capstone/medallion_pipeline.py
```

---

## The Capstone

`src/capstone/medallion_pipeline.py` — a full **Bronze → Silver → Gold**
pipeline built on Delta Lake at Spark scale. Mirror of the pandas-based
Medallion demo in Module 06 §6.5, now distributed.

- **Bronze:** JDBC ingest from Postgres, land as Delta with ingestion
  metadata columns, partitioned by ingest date for pruning and time travel
- **Silver:** quality gates, dedupe via `row_number` window, business-neutral
  cleaning
- **Gold:** two mart tables (`contractor_risk_profile`, `monthly_loss`) with
  idempotent Delta MERGE refresh

Every technique from §8.3, §8.4, §8.6, §8.9 shows up in this one pipeline.
This is the artifact recruiters click first.

---

## Skills demonstrated

`PySpark 3.5+` · `SparkSession configuration and JDBC drivers` ·
`DataFrame API mental model` · `lazy transformations vs eager actions` ·
`repartition vs coalesce with cost trade-offs` ·
`JDBC parallel reads with lowerBound/upperBound/numPartitions` ·
`Parquet as the lakehouse default with partitionBy for pruning` ·
`inner / left / right / outer / semi / anti joins` ·
`broadcast joins (automatic + explicit)` ·
`window functions with partitionBy + orderBy for top-N-per-group` ·
`lag / lead / rank / dense_rank / row_number / ntile` ·
`Spark SQL registered views and CTE composition` ·
`Regular / Pandas / SQL-registered UDFs with performance tradeoffs` ·
`Adaptive Query Execution and its runtime optimisations` ·
`data skew detection and salting fix pattern` ·
`explain plans (physical / formatted / true)` ·
`Delta Lake ACID guarantees` · `time travel via versionAsOf` ·
`MERGE for idempotent incremental loads` ·
`VACUUM + OPTIMIZE + Z-ORDER for lake maintenance` ·
`Structured Streaming (readStream, watermarks, tumbling windows)` ·
`stream-static joins for dimension enrichment` ·
`Delta sink pattern with checkpointing for exactly-once semantics` ·
`Databricks Workflows / Lakeflow Jobs orchestration model` ·
`Declarative Automation Bundles (DABs) as YAML` ·
`MLflow tracking with parameters, metrics, artifacts` ·
`Model Registry with stage transitions` ·
`batch scoring pattern loading from models:/name/Production` ·
`Medallion Architecture end-to-end in Spark + Delta`

---

## Where this leads

- **Module 09 (Kafka)** — streaming source side. Structured Streaming's
  main production input is Kafka, not directory watching.
- **Module 10 (Airflow)** — orchestration alternative to Databricks Workflows.
- **Module 11 (Azure DE + DP-203)** — the same patterns on ADF + Azure
  Databricks + Synapse.
- **Module 8E (Databricks Cert Prep)** — deepens §8.1–8.13 for the
  Databricks Certified Data Engineer Associate exam.

Everything you learn here appears in every subsequent module.
