-- =====================================================================
-- Module 04 — SQL · Advanced · Section 4.11
-- Incremental Loads, CDC, and SCD Type 2
--
-- The three patterns that every real DE pipeline uses to load
-- production data efficiently and preserve history.
--
--   Incremental load  — only pull rows that changed since last run
--   CDC               — capture ROW-LEVEL changes (inserts / updates / deletes)
--   SCD Type 2        — preserve history when dimension attributes change
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────
-- Block 1 — Full load — the naïve baseline
-- Truncate the target, copy everything from source, done. Simple but
-- unsustainable at scale. Use only for reference tables or when
-- source is guaranteed small.
-- ─────────────────────────────────────────────────────────────────────

-- Illustrative — target and source are both accounts here.
-- In production, target would be a warehouse table.
TRUNCATE TABLE vip_accounts;

INSERT INTO vip_accounts (account_id, company_name, total_revenue)
SELECT
    a.account_id,
    a.company_name,
    COALESCE(SUM(p.amount_paid), 0)
FROM accounts a
LEFT JOIN invoices i ON a.account_id = i.account_id
LEFT JOIN payments p ON i.invoice_id = p.invoice_id
GROUP BY a.account_id, a.company_name;


-- ─────────────────────────────────────────────────────────────────────
-- Block 2 — Watermark-based incremental load
-- The bread-and-butter pattern. Track the max updated_at (or a
-- monotonic ID) already loaded. Next run, only pull rows newer than
-- that watermark.
--
-- Requires: source rows have a reliable ordering column (updated_at,
-- created_at, or an autoincrement id).
-- ─────────────────────────────────────────────────────────────────────

-- One-time setup: a table to hold the last-loaded watermark.
CREATE TABLE IF NOT EXISTS etl_watermarks (
    pipeline_name  TEXT PRIMARY KEY,
    last_loaded_at TIMESTAMP NOT NULL
);

INSERT INTO etl_watermarks (pipeline_name, last_loaded_at)
VALUES ('load_payments', '1900-01-01')
ON CONFLICT (pipeline_name) DO NOTHING;


-- Every run: get the watermark, load only newer rows, advance it.
BEGIN;

-- 1. Read current watermark.
--    In a real pipeline this would happen in the orchestrator.
--    Here we use a CTE for illustration.
WITH wm AS (
    SELECT last_loaded_at FROM etl_watermarks WHERE pipeline_name = 'load_payments'
),
new_payments AS (
    SELECT
        p.payment_id,
        p.invoice_id,
        p.amount_paid,
        p.payment_date
    FROM payments p, wm
    WHERE p.payment_date > wm.last_loaded_at
)
-- 2. Load new rows into the target (using a fake `payments_dw` target).
INSERT INTO vip_accounts (account_id, company_name, total_revenue)
SELECT i.account_id, a.company_name, SUM(np.amount_paid)
FROM new_payments np
JOIN invoices i ON np.invoice_id = i.invoice_id
JOIN accounts a ON i.account_id = a.account_id
GROUP BY i.account_id, a.company_name
ON CONFLICT (account_id) DO UPDATE
SET total_revenue = vip_accounts.total_revenue + EXCLUDED.total_revenue;

-- 3. Advance the watermark to the max in the source at the time of read.
UPDATE etl_watermarks
SET last_loaded_at = (SELECT MAX(payment_date) FROM payments)
WHERE pipeline_name = 'load_payments';

COMMIT;

-- Important: reading watermark, source, and updating watermark must
-- all happen in one txn — otherwise concurrent writes to source
-- during the run can slip through the crack.


-- ─────────────────────────────────────────────────────────────────────
-- Block 3 — Change Data Capture (CDC)
-- Track EVERY change to source rows, not just "what's new since X."
-- Answers audit questions ("who updated this and when") and enables
-- downstream systems to react to each change.
--
-- Three common implementations:
--
--   1. Application-level triggers writing to an audit table
--   2. DB-level triggers (below)
--   3. Log-based CDC (Debezium reading the WAL) — most production
--
-- Log-based is the standard for real-time streaming pipelines.
-- Triggers are simpler and still common at smaller scale.
-- ─────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS accounts_cdc (
    cdc_id       BIGSERIAL PRIMARY KEY,
    account_id   INTEGER   NOT NULL,
    operation    TEXT      NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    old_row      JSONB,                       -- previous state (NULL on INSERT)
    new_row      JSONB,                       -- next state     (NULL on DELETE)
    changed_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by   TEXT      NOT NULL DEFAULT CURRENT_USER
);

-- The trigger function — one for all three operations.
CREATE OR REPLACE FUNCTION accounts_cdc_capture()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO accounts_cdc (account_id, operation, old_row, new_row)
        VALUES (NEW.account_id, 'INSERT', NULL, to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO accounts_cdc (account_id, operation, old_row, new_row)
        VALUES (NEW.account_id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO accounts_cdc (account_id, operation, old_row, new_row)
        VALUES (OLD.account_id, 'DELETE', to_jsonb(OLD), NULL);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Attach the trigger.
DROP TRIGGER IF EXISTS accounts_cdc_trigger ON accounts;
CREATE TRIGGER accounts_cdc_trigger
    AFTER INSERT OR UPDATE OR DELETE ON accounts
    FOR EACH ROW
    EXECUTE FUNCTION accounts_cdc_capture();

-- Now every change to accounts creates a row in accounts_cdc.


-- ─────────────────────────────────────────────────────────────────────
-- Block 4 — SCD Type 2 (Slowly Changing Dimensions)
-- Preserve history when a dimension attribute changes.
--
-- Type 1 = overwrite (lose history)
-- Type 2 = new row per change with valid_from / valid_to columns
-- Type 3 = keep previous value in a "previous_x" column (less common)
--
-- Type 2 is the industry standard. Every warehouse dimension table
-- (dim_customer, dim_product) should be SCD2.
-- ─────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_accounts_scd2 (
    surrogate_id  BIGSERIAL   PRIMARY KEY,
    account_id    INTEGER     NOT NULL,           -- business key
    company_name  TEXT        NOT NULL,
    industry      TEXT        NOT NULL,
    status        TEXT        NOT NULL,
    valid_from    TIMESTAMP   NOT NULL,
    valid_to      TIMESTAMP,                      -- NULL = current
    is_current    BOOLEAN     NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS ix_dim_accounts_scd2_account_current
    ON dim_accounts_scd2 (account_id, is_current);


-- Merge new source data into SCD2. Two things happen for each source row:
--   1. If it differs from the current SCD2 row, close the current row
--      (set valid_to = now, is_current = false).
--   2. Insert a new row with valid_from = now, is_current = true.

-- Assume `src_accounts` is a staging table holding the latest snapshot.
-- We'll use accounts directly here for demonstration.

BEGIN;

-- 1. Expire rows whose current state no longer matches source.
UPDATE dim_accounts_scd2 d
SET valid_to = CURRENT_TIMESTAMP,
    is_current = FALSE
FROM accounts a
WHERE d.account_id = a.account_id
  AND d.is_current
  AND (
        d.company_name IS DISTINCT FROM a.company_name
     OR d.industry     IS DISTINCT FROM a.industry
     OR d.status       IS DISTINCT FROM a.status
  );

-- 2. Insert new "current" versions for any changed or brand-new business keys.
INSERT INTO dim_accounts_scd2 (
    account_id, company_name, industry, status, valid_from, is_current
)
SELECT
    a.account_id, a.company_name, a.industry, a.status,
    CURRENT_TIMESTAMP,
    TRUE
FROM accounts a
LEFT JOIN dim_accounts_scd2 d
    ON a.account_id = d.account_id
   AND d.is_current
WHERE d.account_id IS NULL;      -- no current row = insert

COMMIT;

-- Historical query: "what industry did account 42 have on 2024-06-01?"
-- SELECT industry
-- FROM dim_accounts_scd2
-- WHERE account_id = 42
--   AND '2024-06-01'::timestamp BETWEEN valid_from AND COALESCE(valid_to, 'infinity');

-- =====================================================================
-- End of advanced/11_incremental_load_scd2_cdc.sql
-- =====================================================================
