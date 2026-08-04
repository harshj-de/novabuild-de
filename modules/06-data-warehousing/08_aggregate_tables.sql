-- =====================================================================
-- Section 6.8 — Aggregate Tables
--
-- The final section. Aggregate tables are pre-computed summaries that
-- BI tools query INSTEAD of the raw fact tables. They exist for one
-- reason: query speed.
--
-- Why they matter:
--
--   Every Power BI visual runs a query. If Power BI has to scan 76,529
--   raw claim rows and JOIN 4 tables to render "monthly loss trend"
--   every time a dashboard loads, that's 10 users × 76,529 rows =
--   765,290 rows scanned per dashboard view.
--
--   Pre-aggregate that same query into 48 monthly rows once, and
--   Power BI reads 48 rows × 10 users = 480 rows per view.
--
-- In dbt (Module 7 coming) these become your "mart" models. In
-- Databricks / Azure they sit in the Gold layer. In Snowflake they
-- might be tables or materialised views. Same idea everywhere.
--
-- This section builds three aggregate tables that would drive a
-- real NovaBuild dashboard.
--
-- Target engine: PostgreSQL 15+
-- Assumed tables: contractors, claims, coi_verifications,
--                 contractor_enrollments, wrap_programs
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────
-- Table 1 — agg_monthly_claim_summary
--
-- Grain: one row per (year, month)
-- Powers: monthly loss line chart on the executive dashboard
-- ─────────────────────────────────────────────────────────────────────

DROP TABLE IF EXISTS agg_monthly_claim_summary;

CREATE TABLE agg_monthly_claim_summary (
    year               INTEGER      NOT NULL,
    month              INTEGER      NOT NULL,
    claim_count        INTEGER      NOT NULL,
    total_incurred     NUMERIC(14,2) NOT NULL,
    paid_amount        NUMERIC(14,2) NOT NULL,
    reserve_amount     NUMERIC(14,2) NOT NULL,
    avg_claim_size     NUMERIC(12,2) NOT NULL,
    computed_at        TIMESTAMP    NOT NULL DEFAULT NOW(),
    PRIMARY KEY (year, month)
);

INSERT INTO agg_monthly_claim_summary (
    year, month, claim_count, total_incurred,
    paid_amount, reserve_amount, avg_claim_size
)
SELECT
    EXTRACT(YEAR  FROM loss_date)::int   AS year,
    EXTRACT(MONTH FROM loss_date)::int   AS month,
    COUNT(*)                              AS claim_count,
    COALESCE(SUM(total_incurred), 0)      AS total_incurred,
    COALESCE(SUM(paid_amount),    0)      AS paid_amount,
    COALESCE(SUM(reserve_amount), 0)      AS reserve_amount,
    ROUND(COALESCE(AVG(total_incurred), 0)::numeric, 2) AS avg_claim_size
FROM claims
WHERE loss_date IS NOT NULL
GROUP BY year, month;

-- Verify
SELECT year, month, claim_count, total_incurred
FROM agg_monthly_claim_summary
ORDER BY year, month
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────
-- Table 2 — agg_contractor_risk_summary
--
-- Grain: one row per contractor
-- Powers: contractor risk profile page (the underwriter's screen)
-- ─────────────────────────────────────────────────────────────────────

DROP TABLE IF EXISTS agg_contractor_risk_summary;

CREATE TABLE agg_contractor_risk_summary (
    contractor_id       VARCHAR(20)  PRIMARY KEY,
    company_name        VARCHAR(200) NOT NULL,
    tier                VARCHAR(50),
    emr                 NUMERIC(5,2),
    trade               VARCHAR(100),
    state               VARCHAR(50),

    claim_count         INTEGER      NOT NULL DEFAULT 0,
    total_claims_value  NUMERIC(14,2) NOT NULL DEFAULT 0,
    largest_claim       NUMERIC(12,2) NOT NULL DEFAULT 0,
    latest_claim_date   DATE,

    coi_certificate_count INTEGER    NOT NULL DEFAULT 0,
    expired_certificates  INTEGER    NOT NULL DEFAULT 0,

    computed_at         TIMESTAMP    NOT NULL DEFAULT NOW()
);

INSERT INTO agg_contractor_risk_summary (
    contractor_id, company_name, tier, emr, trade, state,
    claim_count, total_claims_value, largest_claim, latest_claim_date,
    coi_certificate_count, expired_certificates
)
SELECT
    c.contractor_id,
    c.company_name,
    c.tier,
    c.emr,
    c.trade,
    c.state,

    COALESCE(claim_stats.claim_count,        0),
    COALESCE(claim_stats.total_claims_value, 0),
    COALESCE(claim_stats.largest_claim,      0),
    claim_stats.latest_claim_date,

    COALESCE(coi_stats.cert_count,           0),
    COALESCE(coi_stats.expired_count,        0)

FROM contractors c

-- Claim stats sub-aggregate
LEFT JOIN (
    SELECT
        ce.contractor_id,
        COUNT(*)                          AS claim_count,
        SUM(cl.total_incurred)            AS total_claims_value,
        MAX(cl.total_incurred)            AS largest_claim,
        MAX(cl.loss_date)::date           AS latest_claim_date
    FROM claims cl
    JOIN wrap_programs wp           ON cl.program_id = wp.program_id
    JOIN contractor_enrollments ce  ON wp.program_id = ce.program_id
    GROUP BY ce.contractor_id
) claim_stats ON c.contractor_id = claim_stats.contractor_id

-- COI stats sub-aggregate
LEFT JOIN (
    SELECT
        contractor_id,
        COUNT(*)                                                   AS cert_count,
        COUNT(*) FILTER (WHERE expiration_date < CURRENT_DATE)     AS expired_count
    FROM coi_verifications
    GROUP BY contractor_id
) coi_stats ON c.contractor_id = coi_stats.contractor_id;

-- Verify
SELECT company_name, tier, claim_count, total_claims_value, expired_certificates
FROM agg_contractor_risk_summary
ORDER BY total_claims_value DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────
-- Table 3 — agg_coi_compliance_summary
--
-- Grain: one row per (year, month)
-- Powers: COI compliance rate KPI card on the exec dashboard
-- ─────────────────────────────────────────────────────────────────────

DROP TABLE IF EXISTS agg_coi_compliance_summary;

CREATE TABLE agg_coi_compliance_summary (
    year                  INTEGER       NOT NULL,
    month                 INTEGER       NOT NULL,
    total_certificates    INTEGER       NOT NULL,
    active_certificates   INTEGER       NOT NULL,
    expired_certificates  INTEGER       NOT NULL,
    compliance_rate_pct   NUMERIC(5,2)  NOT NULL,
    computed_at           TIMESTAMP     NOT NULL DEFAULT NOW(),
    PRIMARY KEY (year, month)
);

INSERT INTO agg_coi_compliance_summary (
    year, month, total_certificates, active_certificates,
    expired_certificates, compliance_rate_pct
)
SELECT
    EXTRACT(YEAR  FROM verification_date)::int  AS year,
    EXTRACT(MONTH FROM verification_date)::int  AS month,
    COUNT(*)                                     AS total_certificates,
    COUNT(*) FILTER (WHERE expiration_date >= verification_date)
                                                 AS active_certificates,
    COUNT(*) FILTER (WHERE expiration_date < verification_date)
                                                 AS expired_certificates,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE expiration_date >= verification_date)
        / NULLIF(COUNT(*), 0),
        2
    )                                            AS compliance_rate_pct
FROM coi_verifications
WHERE verification_date IS NOT NULL
GROUP BY year, month;

-- Verify
SELECT year, month, total_certificates, compliance_rate_pct
FROM agg_coi_compliance_summary
ORDER BY year, month
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────
-- Keeping aggregates fresh
--
-- Aggregate tables go stale the moment new data lands in the source.
-- Three strategies for keeping them current:
--
--   1. TRUNCATE + INSERT — simplest, safe to re-run any time.
--      Fine when source data fits in memory and rebuild is fast.
--
--   2. INCREMENTAL upsert — only re-compute changed periods.
--      Use etl_watermarks (see Module 04 §4.11) to track "last month
--      recomputed" and only rebuild months that touched new claims.
--
--   3. MATERIALIZED VIEW — Postgres will manage the query, you just
--      REFRESH it. Slower than a custom table for very large datasets
--      but zero maintenance code.
--
-- In production dbt orchestrates strategy 2 via incremental models.
-- Section 6.5's Medallion pipeline is strategy 1 (rebuild Silver + Gold
-- every run).
-- ─────────────────────────────────────────────────────────────────────


-- ─────────────────────────────────────────────────────────────────────
-- The connecting thread — how all sections tie together
--
-- What this module built:
--
--   §6.1  →  Why warehouses exist (OLTP vs OLAP, ETL vs ELT)
--   §6.2  →  Star schema and grain — the dimensional model
--   §6.3  →  SCD Type 2 — history preservation for dimensions
--   §6.4  →  Data Vault — regulated-industry pattern
--   §6.5  →  Medallion — Bronze/Silver/Gold layering (Databricks style)
--   §6.6  →  Data Mesh — organisational pattern
--   §6.7  →  OLAP operations — how analysts consume warehouses
--   §6.8  →  Aggregate tables — how BI tools stay fast
--
-- Next: dbt (Module 7). Everything you built here — SCD Type 2,
-- Medallion layers, aggregate tables — becomes reusable dbt models
-- with tests, documentation, and lineage.
-- ─────────────────────────────────────────────────────────────────────
