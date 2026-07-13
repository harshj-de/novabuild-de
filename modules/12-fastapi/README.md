# Module 12 — Contractor Risk Intelligence API (FastAPI + Supabase)

**Status:** Migration in progress · production-grade FastAPI service landing in `src/`; original build notebook in `notebooks/`.

The **capstone module** of the NovaBuild platform. A production-quality REST API service that exposes contractor risk intelligence — the same shape of endpoint a real InsurTech underwriting team would query for GO / CONDITIONAL / NO-GO decisions on new contractor enrollments.

---

## What This Module Demonstrates

- **FastAPI service design** — dependency injection, path/query/body validation with Pydantic, response models, OpenAPI/Swagger auto-generation
- **Permanent database backend** — Supabase PostgreSQL (21 tables, ~76,500 rows) — not an in-memory toy dataset
- **9 complete API cells**, including:
  - Contractor enrollment endpoints
  - Compliance certificate lookup
  - Policy binding status
  - Claims history retrieval
  - **Weighted risk-scoring endpoint** returning GO / CONDITIONAL / NO-GO decisions
  - **HMAC-verified webhooks** for event-driven integration with upstream systems
- **Production patterns** — RealDictCursor column aliasing for count queries, trailing-comma tuple parameters for psycopg2 safety, isolated endpoint logic for debuggability outside the FastAPI runtime
- **Error handling** — graceful failure modes, structured error responses, HTTP status semantics
- **Environment discipline** — `.env`-based credential loading, no secrets in code, `.gitignore` protection at every layer

---

## Structure
---

## Skills Demonstrated

`FastAPI` · `Pydantic` · `PostgreSQL` · `Supabase` · `REST API Design` · `HMAC Auth` · `psycopg2` · `OpenAPI` · `Dependency Injection` · `Structured Logging`

---

## Domain Context

This API is the **decision layer** that would sit in front of a real InsurTech operations team. It doesn't just query data — it synthesizes contractor risk, compliance, and claims context into a single actionable recommendation. The endpoints mirror the shape of decisions made every day at platforms like WrapPortal, Asuretify, and Prequaligy.

The underlying dataset is documented in [`/datasets`](../../datasets).

---

## Why This Module Is the Portfolio Capstone

- **Ties every prior module together** — Python (Module 01), Pandas (03), SQL (04), Data Warehousing (06), and Spark (08) all feed the API's data layer
- **Demonstrates full-stack DE thinking** — data model → pipeline → service → consumer
- **Production-realistic patterns** — the code style, error handling, and security discipline reflect what a mid-senior DE role expects on day one
