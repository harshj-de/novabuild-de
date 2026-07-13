# Module 04 — Advanced SQL & PostgreSQL

**Status:** Migration in progress · SQL scripts landing in `queries/`; supporting exploration notebook in `notebooks/`.

A deep dive into production-grade SQL applied to the NovaBuild insurance schema. Covers the query patterns a Data Engineer must own — not the SELECT/WHERE basics, but the analytical, warehousing, and integrity work that separates a DE from an analyst.

---

## What This Module Demonstrates

- **Advanced window functions** — RANK, DENSE_RANK, LAG/LEAD, running totals, moving averages applied to contractor risk trends and claims sequences
- **Common Table Expressions (CTEs)** — recursive CTEs for hierarchical contractor/subcontractor relationships, non-recursive CTEs for readable multi-stage queries
- **Aggregation depth** — GROUPING SETS, ROLLUP, CUBE for executive-level insurance rollups
- **Set operations** — UNION, INTERSECT, EXCEPT for reconciliation logic
- **SCD Type 2 patterns** — tracking policy changes and contractor status history over time
- **ACID & transactions** — BEGIN, COMMIT, ROLLBACK, isolation levels, and where they matter for claims processing
- **Performance work** — EXPLAIN ANALYZE reading, index strategy, query rewriting for large joins
- **PostgreSQL-specific features** — JSON/JSONB operations, array types, full-text search on claims descriptions

---

## Structure
The 11-section curriculum layout is preserved so a reviewer can walk topic-by-topic or jump directly to what interests them.

---

## Skills Demonstrated

`PostgreSQL 15` · `Window Functions` · `CTEs (Recursive)` · `SCD Type 2` · `ACID Transactions` · `Query Optimization` · `EXPLAIN ANALYZE` · `JSONB`

---

## Domain Context

Every query runs against the NovaBuild 21-table schema (~76,500 rows). Real analytical questions: "Which contractors have deteriorating risk scores over the last 6 quarters?" · "Reconcile bound policies against active certificates by state." · "Rank claims by exposure adjusted for policy limits." See [`/datasets`](../../datasets) for the schema.
