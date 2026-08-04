# Section 6.1 — Data Warehousing Fundamentals

Every DE needs to explain three trade-offs in an interview:

1. **OLTP vs OLAP** — what kind of workload the system serves
2. **ETL vs ELT** — where transformation happens
3. **Kimball vs Inmon** — how the warehouse is structured

This module lays those foundations. Later sections apply them to the
NovaBuild insurance dataset.

---

## OLTP vs OLAP

The single most-important distinction in the data world.

| | **OLTP** (Online Transaction Processing) | **OLAP** (Online Analytical Processing) |
|---|---|---|
| **What it does** | Runs the business — inserts, updates, deletes | Analyses the business — aggregations, trends, historical comparisons |
| **Users** | End users, applications, transactional workflows | Analysts, DE/DS teams, dashboards |
| **Query pattern** | Small, high-volume, low-latency (single row lookups) | Large, low-volume, high-latency-tolerant (multi-million row scans) |
| **Design goal** | Fast writes, referential integrity | Fast reads, denormalisation for scan speed |
| **Schema style** | Normalised (3NF) | Denormalised (star / snowflake) |
| **Indexes** | Many, small B-trees on FKs and lookup keys | Few, columnar / bitmap for scanning |
| **Example systems** | PostgreSQL running your app, SQL Server behind an ERP | Snowflake, BigQuery, Redshift, Databricks |

**NovaBuild example:**
- The `contractors`, `claims`, `policies` tables in Postgres — where the app writes when a claim is filed. This is **OLTP**.
- The `dim_contractor_scd2` table used for historical tier analysis — never touched by the app, only by analysts and dashboards. This is **OLAP**.

**The DE role sits between them:** move data from OLTP → OLAP reliably, on time, without breaking either side.

---

## ETL vs ELT

Same three letters, different order — profound consequences.

### ETL — Extract, Transform, Load

```
[Source]  →  [Staging server / ETL tool]  →  [Warehouse]
              (transform happens here,
               using dedicated compute)
```

**Where it made sense:**
- Warehouse compute was expensive (Teradata, on-prem Oracle)
- Storage was expensive — don't dump raw data
- ETL tools (Informatica, DataStage, SSIS) were the industry standard

**Downsides:**
- Transformation compute is a bottleneck (single ETL server)
- You lose the raw data (or store it twice)
- Any transformation change means re-extracting from source

### ELT — Extract, Load, Transform

```
[Source]  →  [Warehouse — raw layer]  →  [Warehouse — transformed layer]
                                          (transform happens INSIDE
                                           the warehouse, using its
                                           scaled compute)
```

**Why it took over (2015+):**
- Cloud warehouses (Snowflake, BigQuery, Databricks) have effectively infinite compute
- Storage got cheap — keep the raw forever
- Transformations can be re-run against raw whenever business logic changes
- Tools like **dbt** make in-warehouse transformation clean and testable

**NovaBuild example:**
- Raw `claims` land in the `bronze/` folder as-is from source (ELT — the L happens first)
- Transformation into `silver_claim` with typed columns and cleaned values happens INSIDE the warehouse via SQL (the T)
- Aggregation into `gold_monthly_loss` uses the warehouse's parallel scan (the next T)

**Modern DE = ELT with dbt.** ETL still exists for legacy systems.

---

## Kimball vs Inmon

The two philosophical schools of warehouse design. Every senior DE has an opinion.

### Kimball — Dimensional Modelling (Bottom-Up)

**Bill Inmon coined "data warehouse". Ralph Kimball made it practical.**

- Build a **dimensional model** (star schema) for each business process (claims, sales, marketing)
- Each is called a **data mart**
- **Conformed dimensions** shared across marts (e.g. `dim_contractor` used by both claims and COI marts)
- The "warehouse" is the union of all marts — bottom-up

**Pros:**
- Business users understand star schemas intuitively
- Fast to build one process at a time
- BI tools are optimised for stars

**Cons:**
- Requires discipline to keep dimensions conformed across marts
- Data engineers can duplicate work if governance is weak

### Inmon — Normalised Enterprise Warehouse (Top-Down)

- Build a fully-normalised **3NF enterprise warehouse** first
- Marts are derived from the warehouse afterwards
- The warehouse is a single source of truth — top-down

**Pros:**
- Enforces data consistency at the source
- Easier to reason about lineage

**Cons:**
- Slow to deliver first value
- Complex; requires strong modelling skills
- BI tools query the marts, not the 3NF core

### Which does NovaBuild use?

**Kimball, in practice.**
- `dim_contractor_scd2` — a conformed contractor dimension with history
- `fact_claims`, `fact_coi_verifications` — fact tables per process
- Aggregate tables (`agg_contractor_risk_summary`) — pre-computed summaries for dashboards

This is what the industry has largely converged on. **Section 6.2 shows how to actually build a star schema.**

---

## The Data Vault variant

Both Kimball and Inmon assume you know your business processes upfront. **Data Vault 2.0** (see Section 6.4) is a third approach — a staging layer between raw and marts, optimised for auditability and change tolerance. Used in regulated industries (insurance, banking, healthcare).

NovaBuild being an insurance-adjacent domain, this is genuinely relevant. The section will cover Hub / Satellite / Link tables.

---

## Summary

- **OLTP runs the business** with small fast transactions on normalised tables. **OLAP analyses the business** with large scans on denormalised tables. DEs move data between them.
- **ETL** transformed data in a middle tier (legacy). **ELT** loads raw first and transforms inside the warehouse (modern). Modern DE = ELT with dbt.
- **Kimball** builds star schemas per business process; **Inmon** builds a normalised enterprise warehouse first. Kimball won in practice.
- **Data Vault** is a third pattern for regulated industries — Section 6.4.

Next: Section 6.2 — how to build a star schema.
