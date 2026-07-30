-- =====================================================================
-- Module 04 · Incremental Loads · Full Load vs Incremental Load
--
-- A side-by-side demonstration of the two load patterns using a
-- realistic dimension table (dim_accounts).
--
-- Full load:
--   Every run, TRUNCATE the target and reload from source.
--   Simple, but the runtime grows linearly with source size, and it
--   also wipes any history you'd want to keep (see SCD Type 2 in
--   advanced/11 if you need history).
--
-- Incremental load:
--   Only pull rows changed since the last successful run. Runtime
--   proportional to CHANGE volume, not total size — makes daily
--   loads on billion-row tables tractable.
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────
-- Block 1 — The target: a simple accounts dimension
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_accounts (
    account_id     INTEGER PRIMARY KEY,
    company_name   TEXT NOT NULL,
    industry       TEXT NOT NULL,
    status         TEXT NOT NULL,
    last_synced_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ─────────────────────────────────────────────────────────────────────
-- Block 2 — Full load
-- Every run, blow away the target and rewrite it.
-- Works up to a point; catastrophic on billion-row source.
-- ─────────────────────────────────────────────────────────────────────
BEGIN;

TRUNCATE TABLE dim_accounts;

INSERT INTO dim_accounts (account_id, company_name, industry, status, last_synced_at)
SELECT
    account_id,
    company_name,
    industry,
    status,
    CURRENT_TIMESTAMP
FROM accounts;

COMMIT;


-- ─────────────────────────────────────────────────────────────────────
-- Block 3 — Incremental load — assumes source has an updated_at column
--
-- Our sample accounts table doesn't have updated_at, so we'll pretend
-- signup_date represents the last change (a real source system would
-- track updated_at or use CDC).
--
-- Pattern:
--   1. Read the last-loaded high-water mark from a metadata table.
--   2. Pull only rows with updated_at > that mark.
--   3. UPSERT into the target (insert new rows, update existing ones).
--   4. Advance the mark.
-- ─────────────────────────────────────────────────────────────────────

-- One-time: create the metadata table.
CREATE TABLE IF NOT EXISTS etl_watermarks (
    pipeline_name  TEXT PRIMARY KEY,
    last_loaded_at TIMESTAMP NOT NULL
);

INSERT INTO etl_watermarks (pipeline_name, last_loaded_at)
VALUES ('load_dim_accounts', DATE '1900-01-01')
ON CONFLICT (pipeline_name) DO NOTHING;


-- Every-run job:
BEGIN;

WITH wm AS (
    SELECT last_loaded_at FROM etl_watermarks
    WHERE pipeline_name = 'load_dim_accounts'
),
delta AS (
    SELECT a.*
    FROM accounts a, wm
    WHERE a.signup_date > wm.last_loaded_at
)
INSERT INTO dim_accounts (account_id, company_name, industry, status, last_synced_at)
SELECT account_id, company_name, industry, status, CURRENT_TIMESTAMP
FROM delta
ON CONFLICT (account_id) DO UPDATE
    SET company_name   = EXCLUDED.company_name,
        industry       = EXCLUDED.industry,
        status         = EXCLUDED.status,
        last_synced_at = EXCLUDED.last_synced_at;

UPDATE etl_watermarks
   SET last_loaded_at = (SELECT MAX(signup_date)::timestamp FROM accounts)
 WHERE pipeline_name = 'load_dim_accounts';

COMMIT;


-- ─────────────────────────────────────────────────────────────────────
-- Block 4 — Comparison
--
--   Metric                Full Load                Incremental Load
--   ─────────────────    ────────────────        ─────────────────
--   Runtime               O(source_size)          O(rows_changed)
--   Complexity            Trivial                 Requires watermark,
--                                                 handles updates/deletes
--   History preservation  No (target overwritten) No — separate SCD
--   Correctness on        Bulletproof             Depends on watermark
--   schema changes                                logic and clock skew
--   When to use           Reference tables,       Fact tables, dims
--                         small dims, hourly full  with millions+ rows
-- ─────────────────────────────────────────────────────────────────────
