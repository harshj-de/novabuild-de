# Module 04 — SQL for Data Engineering

Production-shape SQL against a realistic 10-table SaaS operational schema.
Sections 4.1 through 4.11 of the curriculum, plus 8 portfolio-facing
analytical queries that answer real business questions.

Target engine: **PostgreSQL 15+**. Most queries are portable to Snowflake
with minor changes; engine-specific features (window `FILTER`, `ILIKE`,
`ON CONFLICT`, `DATE_TRUNC`, `PERCENTILE_CONT`) are called out in comments
where used.

---

## Schema (11 tables)

```
accounts        — one row per customer company
plans           — the tiered pricing catalogue (Starter / Growth / Enterprise)
users           — humans at accounts
subscriptions   — which plan an account is on, and history of changes
invoices        — what was billed to whom, when
payments        — money actually received against invoices
features        — app capabilities being metered
feature_usage   — event log per (user, feature, day)
sales_reps      — internal sellers
deals           — sales pipeline
support_tickets — CX metrics + resolution SLA tracking
```

Full DDL in [`setup/00_create_schema.sql`](./setup/00_create_schema.sql).
Foreign keys, indexes, and CHECK constraints defined at schema-creation time.

---

## Getting Started

### 1. Create the schema

```bash
psql -d your_db -f setup/00_create_schema.sql
```

### 2. Load seed data

```bash
export DATABASE_URL=postgresql://user:pass@localhost:5432/your_db
pip install 'psycopg[binary]'
python setup/generate_saas_data.py
```

Approximate volumes generated (deterministic with default seed=42):

| Table | Rows |
|---|---|
| accounts | 100 |
| plans | 3 |
| users | ~1,000 |
| subscriptions | ~150 |
| invoices | ~800 |
| payments | ~750 |
| features | 8 |
| feature_usage | ~10,000 |
| sales_reps | 10 |
| deals | ~120 |
| support_tickets | ~300 |

### 3. Run any .sql file

```bash
psql -d your_db -f fundamentals/01_select_where_orderby.sql
psql -d your_db -f portfolio_queries/01_mrr_by_plan.sql
```

Each SQL file is organised into commented "Blocks" — read top-to-bottom
or run individual blocks in your SQL client.

---

## Structure

```
04-sql/
├── README.md
├── requirements.txt
├── setup/
│   ├── 00_create_schema.sql              (11-table DDL, FKs, indexes, CHECK)
│   └── generate_saas_data.py             (deterministic seed loader)
├── fundamentals/                          (Sections 4.1–4.6)
│   ├── 01_select_where_orderby.sql
│   ├── 02_joins.sql
│   ├── 03_aggregations_groupby.sql
│   ├── 04_subqueries_and_ctes.sql
│   ├── 05_set_operations_and_case.sql
│   └── 06_dml_and_constraints.sql
├── advanced/                              (Sections 4.7–4.11)
│   ├── 07_window_functions.sql
│   ├── 08_recursive_ctes.sql
│   ├── 09_explain_analyze_and_indexing.sql
│   ├── 10_transactions_and_isolation.sql
│   └── 11_incremental_load_scd2_cdc.sql
├── portfolio_queries/                     (Recruiter-facing showcase)
│   ├── 01_mrr_by_plan.sql
│   ├── 02_churn_by_industry_month.sql
│   ├── 03_plan_upgrade_downgrade.sql
│   ├── 04_top3_accounts_per_industry.sql
│   ├── 05_support_resolution_time.sql
│   ├── 06_feature_adoption_by_plan.sql
│   ├── 07_running_total_with_reset.sql
│   └── 08_gap_islands.sql
├── incremental_loads/
│   └── full_load_vs_incremental.sql
└── notebooks/                             (originals preserved for reference)
    ├── 00_saas_dataset_and_first_queries.ipynb
    ├── 01_saas_sql_advanced.ipynb
    ├── 02_atliq_duckdb_analytical.ipynb
    ├── 03_olympic_sql_practice.ipynb
    └── 04_full_load_vs_incremental.ipynb
```

---

## Portfolio Queries — Business Value

The 8 files in `portfolio_queries/` each answer a specific business question
that a real SaaS analytics team gets asked weekly. Each file includes a
problem statement, the query, and an "extension for the interview" section
showing how to expand on it.

| # | Query | Business Question |
|---|---|---|
| 01 | MRR by Plan | What's monthly recurring revenue per plan over time? |
| 02 | Churn by Industry & Month | Where and when are we losing customers? |
| 03 | Plan Upgrade / Downgrade | What's expansion revenue vs contraction? |
| 04 | Top 3 Accounts per Industry | Who are the strategic accounts? |
| 05 | Support Resolution Time | Which industries breach our SLA? |
| 06 | Feature Adoption by Plan | Which features drive Enterprise engagement? |
| 07 | Running Total with Reset | Payment success streak analysis |
| 08 | Gaps and Islands | Consecutive months of billing per account |

---

## Skills Demonstrated

`PostgreSQL 15+` · `schema design with FK + CHECK constraints` ·
`realistic seed-data generation via psycopg 3` ·
`SELECT / WHERE / ORDER BY / LIMIT` ·
`joins (inner / left / full outer / cross / self)` · `anti-join pattern` ·
`aggregations with GROUP BY / HAVING / ROLLUP` ·
`subqueries (scalar, IN, EXISTS, correlated)` ·
`CTEs (single, multiple, MATERIALIZED, RECURSIVE)` ·
`set operations (UNION / INTERSECT / EXCEPT)` ·
`CASE expressions and conditional aggregation` ·
`UPSERT / DML with transactions and constraints` ·
`window functions (ROW_NUMBER / RANK / LAG / LEAD / SUM OVER)` ·
`ROWS vs RANGE frames` · `NTILE for percentile bucketing` ·
`recursive CTEs for hierarchy and sequence generation` ·
`EXPLAIN ANALYZE and index selection` ·
`partial indexes, partitioning, materialised views` ·
`ACID and isolation levels (READ COMMITTED / REPEATABLE READ / SERIALIZABLE)` ·
`SELECT FOR UPDATE and deadlock avoidance` ·
`watermark-based incremental loads` · `CDC via triggers` ·
`SCD Type 2 dimension updates` ·
`gaps-and-islands, greatest-N-per-group, MRR, churn analysis`

---

## Runtime Environment

Everything except the seed generator is pure SQL and requires only
PostgreSQL 15+. The generator needs Python 3.10+ and `psycopg[binary]`
(see `requirements.txt`).
