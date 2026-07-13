# Module 03 — Pandas ETL Pipelines

**Status:** Migration in progress · Pandas notebook + refactored `.py` ETL scripts landing in `notebooks/` and `src/`.

End-to-end ETL work on the NovaBuild dataset using Pandas — the workhorse library for tabular data in Python. Covers the patterns a Data Engineer uses daily: extract from multiple sources, clean messy data, transform to analytical shapes, load to warehouse-ready formats.

---

## What This Module Demonstrates

- **Extraction** — reading from CSV, JSON, Parquet, and PostgreSQL sources
- **Cleaning at scale** — handling missing values, type coercion, deduplication, date parsing on ~76,500-row NovaBuild dataset
- **Transformation patterns** — groupby aggregations, pivot/melt reshaping, window operations, merges/joins that mirror SQL semantics
- **Business logic** — computing contractor risk scores, aggregating claims by policy year, deriving compliance status flags
- **Performance discipline** — vectorized operations over row-by-row loops, chunked processing for large files, memory-aware dtypes
- **Output shapes** — loading cleaned data back to PostgreSQL, exporting to Parquet for downstream Spark/Databricks work

---

## Structure
---

## Skills Demonstrated

`Pandas` · `NumPy` · `ETL Design` · `Data Cleaning` · `PostgreSQL Integration` · `Parquet` · `Vectorized Operations`

---

## Domain Context

All ETL work is applied to the NovaBuild insurance schema. The pipeline output feeds directly into Module 04 (SQL), Module 06 (Data Warehousing), and Module 08 (Spark). See [`/datasets`](../../datasets).
