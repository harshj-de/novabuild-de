-- =====================================================================
-- Section 6.4 — Data Vault 2.0
--
-- Data Vault is a warehouse modelling approach designed for
-- regulated industries (insurance, banking, healthcare) where:
--
--   * Auditability matters — every load is timestamped and traceable
--   * Source systems change frequently — the model tolerates change
--     without breaking downstream
--   * Multiple sources describe the same business entity — each source
--     is captured separately, unified at query time
--
-- Three table types:
--
--   HUB       — one row per business key (identity of a thing)
--               "Every contractor that ever existed, keyed by MD5 of
--                contractor_id."
--
--   SATELLITE — descriptive attributes about a Hub, timestamped
--               "This is what we knew about contractor X on this date."
--
--   LINK      — relationships between Hubs
--               "This claim was filed by this contractor."
--
-- Why the separation matters:
--   * Adding a new attribute = add a Satellite (no schema break)
--   * Adding a new source = add another Satellite (no re-model)
--   * Adding a new relationship = add a Link (no change to Hubs)
--
-- Downside:
--   * Complex — you need many joins to reconstruct simple business
--     views. Data Vault is a RAW layer under a Kimball star schema,
--     not a query layer analysts touch directly.
--
-- NovaBuild has claims + contractors + wrap_programs + contractor_enrollments.
-- We'll build the Data Vault equivalent of the "claim by contractor"
-- relationship.
--
-- Target engine: PostgreSQL 15+
-- Assumed tables: contractors, claims, wrap_programs, contractor_enrollments
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────
-- Step 1 — Hub_Contractor
--
-- A Hub has exactly four columns:
--   hash key      — MD5 of the business key (deterministic)
--   business key  — the natural key from source
--   load_date     — when this Hub row first appeared in the warehouse
--   record_source — which source system produced it
--
-- Nothing describes the contractor — no name, no tier. Those are
-- Satellite attributes.
-- ─────────────────────────────────────────────────────────────────────

DROP TABLE IF EXISTS link_claim_contractor;
DROP TABLE IF EXISTS sat_contractor_details;
DROP TABLE IF EXISTS hub_claim;
DROP TABLE IF EXISTS hub_contractor;

CREATE TABLE hub_contractor (
    hub_contractor_hk  CHAR(32)    PRIMARY KEY,     -- MD5 of contractor_id
    contractor_id      VARCHAR(20) NOT NULL,
    load_date          TIMESTAMP   NOT NULL,
    record_source      VARCHAR(50) NOT NULL
);

INSERT INTO hub_contractor
SELECT
    md5(contractor_id)        AS hub_contractor_hk,
    contractor_id             AS contractor_id,
    NOW()                     AS load_date,
    'postgresql.contractors'  AS record_source
FROM contractors;

-- Verify
SELECT COUNT(*) AS hub_contractor_rows FROM hub_contractor;


-- ─────────────────────────────────────────────────────────────────────
-- Step 2 — Sat_Contractor_Details
--
-- Descriptive attributes of a Hub. One row per (hub_hk, load_date).
-- Every load creates new rows; nothing is ever updated. Point-in-time
-- queries pick the most recent row for a hub as of a given date.
--
-- PRIMARY KEY (hub_contractor_hk, load_date) — a hub can have many
-- historical states.
-- ─────────────────────────────────────────────────────────────────────

CREATE TABLE sat_contractor_details (
    hub_contractor_hk  CHAR(32)     NOT NULL,
    load_date          TIMESTAMP    NOT NULL,
    company_name       VARCHAR(200),
    trade              VARCHAR(100),
    state              VARCHAR(50),
    tier               VARCHAR(50),
    emr                NUMERIC(5,2),
    employees_count    INTEGER,
    record_source      VARCHAR(50)  NOT NULL,
    PRIMARY KEY (hub_contractor_hk, load_date)
);

INSERT INTO sat_contractor_details
SELECT
    md5(contractor_id)        AS hub_contractor_hk,
    NOW()                     AS load_date,
    company_name,
    trade,
    state,
    tier,
    emr,
    employees_count,
    'postgresql.contractors'  AS record_source
FROM contractors;

-- Verify
SELECT COUNT(*) AS sat_details_rows FROM sat_contractor_details;


-- ─────────────────────────────────────────────────────────────────────
-- Step 3 — Hub_Claim
--
-- Same shape as Hub_Contractor. Business key = claim_id.
-- ─────────────────────────────────────────────────────────────────────

CREATE TABLE hub_claim (
    hub_claim_hk   CHAR(32)    PRIMARY KEY,
    claim_id       VARCHAR(20) NOT NULL,
    load_date      TIMESTAMP   NOT NULL,
    record_source  VARCHAR(50) NOT NULL
);

INSERT INTO hub_claim
SELECT
    md5(claim_id)          AS hub_claim_hk,
    claim_id               AS claim_id,
    NOW()                  AS load_date,
    'postgresql.claims'    AS record_source
FROM claims;

SELECT COUNT(*) AS hub_claim_rows FROM hub_claim;


-- ─────────────────────────────────────────────────────────────────────
-- Step 4 — Link_Claim_Contractor
--
-- Represents the relationship "this claim was filed against this
-- contractor's policy."
--
-- The relationship isn't directly on the claims table — it goes
-- through wrap_programs and contractor_enrollments. The Data Vault
-- Link captures that relationship regardless of how it changes in
-- source.
-- ─────────────────────────────────────────────────────────────────────

CREATE TABLE link_claim_contractor (
    link_claim_contractor_hk  CHAR(32)    PRIMARY KEY,
    hub_claim_hk              CHAR(32)    NOT NULL,
    hub_contractor_hk         CHAR(32)    NOT NULL,
    load_date                 TIMESTAMP   NOT NULL,
    record_source             VARCHAR(50) NOT NULL
);

INSERT INTO link_claim_contractor
SELECT
    md5(cl.claim_id || ce.contractor_id)  AS link_claim_contractor_hk,
    md5(cl.claim_id)                      AS hub_claim_hk,
    md5(ce.contractor_id)                 AS hub_contractor_hk,
    NOW()                                 AS load_date,
    'postgresql.claims'                   AS record_source
FROM claims cl
JOIN wrap_programs wp
    ON cl.program_id = wp.program_id
JOIN contractor_enrollments ce
    ON wp.program_id = ce.program_id;

SELECT COUNT(*) AS link_rows FROM link_claim_contractor;


-- ─────────────────────────────────────────────────────────────────────
-- Step 5 — Business query via the Vault
--
-- "How many contractors are in each tier, according to the Data Vault?"
--
-- Notice we join Hub → Satellite → GROUP BY. In a normal Kimball star
-- we'd just do `SELECT tier, COUNT(*) FROM dim_contractor GROUP BY tier`.
-- The Vault is verbose by design — but the raw layer preserves
-- everything.
-- ─────────────────────────────────────────────────────────────────────

SELECT
    s.tier,
    COUNT(DISTINCT h.contractor_id) AS contractor_count
FROM hub_contractor h
JOIN sat_contractor_details s
    ON h.hub_contractor_hk = s.hub_contractor_hk
-- Get the LATEST satellite row per hub
WHERE s.load_date = (
    SELECT MAX(s2.load_date)
    FROM sat_contractor_details s2
    WHERE s2.hub_contractor_hk = s.hub_contractor_hk
)
GROUP BY s.tier
ORDER BY contractor_count DESC;


-- =====================================================================
-- When to use Data Vault (interview point)
--
-- USE Data Vault when:
--   * You're in a regulated industry (insurance, banking, pharma)
--   * You have multiple source systems describing the same entities
--   * Auditability requirements demand exact reconstruction of
--     "what did we know at time T"
--   * Source schemas change frequently and you can't afford to
--     re-model downstream every time
--
-- DON'T use Data Vault when:
--   * You have one source system and stable schemas
--   * BI/analytics is the primary use case (analysts don't want to
--     write 4-way joins for every question)
--   * Team is < 5 DEs — the maintenance overhead isn't justified
--
-- Real-world pattern:
--   Data Vault as the RAW warehouse layer.
--   Kimball star schemas built ON TOP of the Vault for analyst use.
--   dbt manages the transformation from Vault to stars.
-- =====================================================================
