# NovaBuild Schema Reference

The Module 06 SQL and Python files run against the NovaBuild
insurance dataset — the same domain used in Modules 08 (Spark) and
Module 12 (FastAPI). This document is a quick reference to the tables
referenced across §6.3 – §6.8.

The full schema and seed data live with Module 12 (the FastAPI risk
intelligence API). Point Module 06 at the same PostgreSQL database.

---

## Core tables referenced

### `contractors`
One row per contractor company doing work under a wrap-up insurance program.

| Column | Type | Notes |
|---|---|---|
| contractor_id | VARCHAR(20) PK | Natural key (e.g. `C-1234`) |
| company_name | VARCHAR(200) | |
| trade | VARCHAR(100) | Electrical, Concrete, Steel, etc. |
| state | VARCHAR(50) | Two-letter state code |
| tier | VARCHAR(50) | Probationary / Standard / Preferred / Elite |
| emr | NUMERIC(5,2) | Experience Modification Rate |
| employees_count | INTEGER | |

### `claims`
One row per claim event.

| Column | Type | Notes |
|---|---|---|
| claim_id | VARCHAR(20) PK | Natural key |
| program_id | VARCHAR(20) FK → wrap_programs | |
| loss_date | DATE | When the loss occurred |
| loss_type | VARCHAR(100) | Bodily Injury, Property Damage, etc. |
| total_incurred | NUMERIC(12,2) | Paid + reserved |
| paid_amount | NUMERIC(12,2) | |
| reserve_amount | NUMERIC(12,2) | |

### `wrap_programs`
One row per wrap-up insurance program (a construction project).

| Column | Type | Notes |
|---|---|---|
| program_id | VARCHAR(20) PK | |
| program_name | VARCHAR(200) | |
| start_date | DATE | |
| end_date | DATE | |
| owner_id | VARCHAR(20) | Program owner |

### `contractor_enrollments`
Bridge table: which contractors are enrolled in which programs.

| Column | Type | Notes |
|---|---|---|
| enrollment_id | SERIAL PK | |
| program_id | VARCHAR(20) FK | |
| contractor_id | VARCHAR(20) FK | |
| enrollment_date | DATE | |

### `coi_verifications`
Certificate of Insurance (COI) records per contractor.

| Column | Type | Notes |
|---|---|---|
| verification_id | SERIAL PK | |
| contractor_id | VARCHAR(20) FK | |
| verification_date | DATE | When we last verified |
| expiration_date | DATE | When the certificate expires |
| status | VARCHAR(50) | active / expired / lapsed |

### `safety_incidents`
Safety incident events reported on projects.

| Column | Type | Notes |
|---|---|---|
| incident_id | SERIAL PK | |
| contractor_id | VARCHAR(20) FK | |
| incident_date | DATE | |
| severity | VARCHAR(50) | minor / moderate / severe |
| description | TEXT | |

---

## Warehouse tables created by this module

Module 06 creates several tables on top of the operational schema:

| Section | Table | Purpose |
|---|---|---|
| §6.3 | `dim_contractor_scd2` | SCD Type 2 dimension with tier history |
| §6.4 | `hub_contractor`, `sat_contractor_details` | Data Vault contractor hub + satellite |
| §6.4 | `hub_claim`, `link_claim_contractor` | Data Vault claim hub + link |
| §6.5 | Parquet files in `/tmp/novabuild_lake/{bronze,silver,gold}/` | Medallion lake |
| §6.8 | `agg_monthly_claim_summary` | Monthly claim losses aggregate |
| §6.8 | `agg_contractor_risk_summary` | Per-contractor risk rollup |
| §6.8 | `agg_coi_compliance_summary` | Monthly COI compliance rate |

All warehouse tables use `DROP TABLE IF EXISTS` at the top so the SQL
files are idempotent — safe to re-run during development.

---

## Getting the data locally

If you don't have the NovaBuild data loaded:

1. **From Module 12** — the FastAPI capstone repo has the schema DDL
   and seed loader. Point your local Postgres at it and run the
   loader.

2. **Colab notebook (fallback)** — the original notebook in
   `notebooks/original_data_warehousing.ipynb` includes a setup cell
   that installs Postgres, creates the `novabuilds` database, and
   loads seed data. Run that cell first if working in Colab.

3. **Bring-your-own** — swap the file references. Any SaaS-style
   dataset with an entities + events + relationships structure will
   let the concepts land.
