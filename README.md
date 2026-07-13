# NovaBuild — Contractor Risk Intelligence Platform

**A production-simulation data engineering system for commercial construction insurance.**  
21-table PostgreSQL schema · Python + Spark ETL pipelines · FastAPI risk-scoring service · Power BI executive dashboards.  
Modeled after modern InsurTech operations at scale.

---

## 🛠 Tech Stack

**Languages & Frameworks:** Python 3.11 · SQL · FastAPI · Pandas · Apache Spark (PySpark) · dbt  
**Databases & Storage:** PostgreSQL (Supabase) · Delta Lake · Databricks  
**Orchestration & Deployment:** Docker · Databricks Workflows · GitHub Actions (planned)  
**Analytics & Visualization:** Power BI · MLflow · Great Expectations (planned)

---

## 🏗 The System

**NovaBuild** is a purpose-built data platform that mirrors the operational complexity of commercial construction insurance — a domain where a single project can involve dozens of contractors, hundreds of certificates, weekly compliance checks, and millions in exposure.

The schema (21 tables, ~76,500 rows of realistic seeded data) models the full lifecycle:  
**Contractor enrollment → Compliance verification → Policy binding → Claims tracking → Risk scoring**

This mirrors the product surface of leading InsurTech platforms — contractor prequalification, insurance certificate management, project risk analytics, and claims intelligence — and provides a realistic substrate for demonstrating production-grade Data Engineering work.

Every module in this repository operates on the NovaBuild dataset, producing artifacts a real InsurTech data team would ship: risk-scoring APIs, medallion-architecture Databricks pipelines, executive dashboards, and warehouse models.

---

## 📚 Module Map

| Module | Focus Area | Key Deliverables |
|--------|-----------|------------------|
| [01 — Python](./modules/01-python) | Python fundamentals, OOP, production patterns | Generators, class hierarchies, structured code |
| [03 — Pandas](./modules/03-pandas) | ETL pipelines, data cleaning at scale | End-to-end Pandas ETL capstone |
| [04 — SQL](./modules/04-sql) | Advanced SQL, window functions, SCD Type 2 | 11-section PostgreSQL deep dive |
| [05 — Power BI](./modules/05-powerbi) | Data modeling, DAX, executive dashboards | Galaxy schema (6 facts / 8 dimensions), 22 DAX measures, 3-page dashboard |
| [06 — Data Warehousing](./modules/06-data-warehousing) | Kimball, Data Vault 2.0, Medallion, Data Mesh | Warehouse patterns applied to NovaBuild |
| [08 — Spark](./modules/08-spark) | PySpark, Delta Lake, Structured Streaming | Bronze/Silver/Gold pipeline on Databricks |
| [12 — FastAPI](./modules/12-fastapi) | Production API service | Contractor Risk Intelligence API — 9 endpoints, HMAC-verified webhooks, weighted risk scoring (GO/CONDITIONAL/NO GO) |

---

## 🔍 Dataset

The NovaBuild schema and seed data live in [`/datasets`](./datasets). Full DDL, entity relationships, and sample records are documented.

---

## 👤 About the Author

**Harsh Jariwala** — Data Engineer with deep domain expertise in commercial insurance and enterprise systems.

Nine years spent working inside the operations of construction, waste management, and specialty insurance organizations — including engagements with clients such as Grunley Construction (Washington DC) and Quayclean (Australia) — mapping how these businesses actually function end-to-end. That domain fluency is now applied to building the data platforms that make such operations measurable, auditable, and scalable.

The work in this repository reflects a shift from analyzing enterprise systems to engineering them.

**Currently focused on:** InsurTech data infrastructure · SAP Business Data Cloud · Databricks & Delta Lake production patterns

---

## 📫 Contact

**Email:** harsh.jariwala.de@gmail.com  
**LinkedIn:** [linkedin.com/in/harsh-jariwala-72b7293b0](https://www.linkedin.com/in/harsh-jariwala-72b7293b0)  
**Location:** Surat, India · Open to remote & international opportunities

---

*Repository is actively developed as part of an ongoing Data Engineering curriculum. Every module produces a public artifact; every artifact is derived from real problems in a domain the author has spent nearly a decade inside.*
