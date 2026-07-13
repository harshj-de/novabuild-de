# Module 06 — Data Warehousing Patterns

**Status:** Migration in progress · warehouse design docs and worked examples landing in `docs/` and `notebooks/`.

The theoretical and applied foundations of data warehouse design. Covers the four major schools of thought a Data Engineer must be conversant in — Kimball, Inmon, Data Vault 2.0, and Data Mesh — plus the modern Medallion Architecture that ties them together in a Databricks/lakehouse context.

---

## What This Module Demonstrates

- **Kimball dimensional modeling** — star schemas, conformed dimensions, factless facts applied to NovaBuild's claims and policy data
- **Inmon 3NF enterprise warehouse** — normalized model contrasted against Kimball's denormalized approach; when each wins
- **SCD Type 2 mechanics** — surrogate keys, effective/expiry dates, current-flag patterns tracked through contractor lifecycle changes
- **Data Vault 2.0** — Hub / Link / Satellite architecture, business keys, hash diffs, load patterns for an insurance-vertical hub-and-spoke model
- **Medallion Architecture** — Bronze (raw) / Silver (cleaned + conformed) / Gold (aggregated + business-ready) pattern that dominates modern lakehouse work
- **Data Mesh principles** — domain-oriented ownership, self-serve data platforms, federated computational governance — applied conceptually to a multi-line insurance org
- **OLAP operations** — slice, dice, roll-up, drill-down, pivot — implemented in SQL against warehouse fact tables
- **Aggregate tables & materialized views** — the performance layer between raw fact and dashboard

---

## Structure
---

## Skills Demonstrated

`Kimball` · `Inmon` · `Data Vault 2.0` · `Medallion Architecture` · `Data Mesh` · `SCD Type 2` · `OLAP Design` · `Star Schema` · `Aggregate Tables`

---

## Domain Context

Every pattern is applied to the NovaBuild insurance schema. Same data, four different warehouse designs — showing how architectural choice drives what questions the warehouse can answer efficiently. See [`/datasets`](../../datasets).
