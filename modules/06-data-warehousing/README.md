# Module 06 — Data Warehousing

The theory foundation and practical patterns every Data Engineer must
own. Sections 6.1 through 6.8, all applied to the NovaBuild insurance
domain (the same 21-table dataset used in Modules 08 and 12).

Target engine: **PostgreSQL 15+** for SQL sections. Python 3.10+ +
Pandas + pyarrow for the Medallion section.

---

## Sections

| # | Topic | Format | What you'll learn |
|---|---|---|---|
| 6.1 | Fundamentals | Markdown | OLTP vs OLAP, ETL vs ELT, Kimball vs Inmon |
| 6.2 | Dimensional Modelling | Markdown | Star schema, grain, surrogate keys, SCD types overview |
| 6.3 | SCD Type 2 | SQL | Contractor tier history — the workhorse dimension pattern |
| 6.4 | Data Vault 2.0 | SQL | Hub / Satellite / Link — the regulated-industry pattern |
| 6.5 | Medallion Architecture | Python | Bronze / Silver / Gold — the Databricks lakehouse pattern |
| 6.6 | Data Mesh | Markdown | Domain-oriented data ownership |
| 6.7 | OLAP Operations | SQL | Drill-down, roll-up, slice, dice, pivot |
| 6.8 | Aggregate Tables | SQL | Pre-computed summaries for BI performance |

---

## Structure

```
06-data-warehousing/
├── README.md
├── setup/
│   └── novabuild_schema_reference.md
├── 01_fundamentals.md              (§6.1 — theory)
├── 02_dimensional_modeling.md      (§6.2 — theory)
├── 03_scd_type_2.sql               (§6.3 — SQL)
├── 04_data_vault_2_0.sql           (§6.4 — SQL)
├── 05_medallion_architecture.py    (§6.5 — Python)
├── 06_data_mesh.md                 (§6.6 — theory)
├── 07_olap_operations.sql          (§6.7 — SQL)
├── 08_aggregate_tables.sql         (§6.8 — SQL)
└── notebooks/
    └── original_data_warehousing.ipynb   (source notebook preserved)
```

The mix of formats is intentional — real DW work is mixed-format.
Theory sections are markdown because they're theory. SQL patterns are
SQL because they're SQL. The Medallion pipeline is Python because
that's how it actually gets written in production.

---

## Prerequisites

- PostgreSQL 15+ with the NovaBuild schema loaded (see
  [setup/novabuild_schema_reference.md](./setup/novabuild_schema_reference.md))
- Python 3.10+ with `pandas`, `pyarrow`, `psycopg2-binary` (for §6.5)

---

## Getting started

Read the two theory sections first (§6.1, §6.2). Then work through the
SQL sections in order — each builds on the previous.

```bash
psql -d novabuilds -f 03_scd_type_2.sql
psql -d novabuilds -f 04_data_vault_2_0.sql
```

For §6.5 (Medallion):

```bash
pip install pandas pyarrow psycopg2-binary
export PG_DB=novabuilds PG_USER=saas_user PG_PASSWORD=saas_pass
python 05_medallion_architecture.py
```

For §6.7 and §6.8 (OLAP + aggregates):

```bash
psql -d novabuilds -f 07_olap_operations.sql
psql -d novabuilds -f 08_aggregate_tables.sql
```

---

## Skills demonstrated

`OLTP vs OLAP mental model` · `ETL vs ELT trade-off analysis` ·
`Kimball dimensional modelling` · `star schema design` ·
`fact/dimension grain declaration` · `surrogate key patterns` ·
`Slowly Changing Dimensions (Type 1 / 2 / 3 / 4 / 6)` ·
`SCD Type 2 implementation with valid_from/valid_to/is_current` ·
`Point-in-time joins for historical dimension lookup` ·
`Data Vault 2.0 with Hub / Satellite / Link tables` ·
`MD5 hash keys for warehouse identity` ·
`Medallion Architecture (Bronze / Silver / Gold)` ·
`Parquet as the lakehouse storage format` ·
`Data quality gates in the Silver layer` ·
`Data Mesh organisational pattern` ·
`OLAP cube operations (drill-down / roll-up / slice / dice / pivot)` ·
`ROLLUP for multi-level aggregations` ·
`Pre-aggregate tables for BI dashboard performance` ·
`Incremental refresh strategies` ·
`Idempotent DDL patterns (DROP IF EXISTS)`

---

## Where this leads

Module 06 is the theory foundation for:

- **Module 07 (dbt)** — SCD2 becomes a dbt snapshot; aggregate tables
  become mart models; Medallion becomes the staging/intermediate/mart
  folder structure.
- **Module 08 (Spark)** — Bronze/Silver/Gold shifts to Delta Lake on
  Databricks with proper distributed compute.
- **Module 11 (Azure DE)** — Same patterns but on ADLS Gen2 +
  Databricks + Synapse.
- **SAP DE track** — BW/4HANA has its own SCD implementation
  (0DATETO/0DATFROM columns); the concepts transfer directly.

Everything you learn here recurs.
