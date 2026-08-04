-- =====================================================================
-- Section 6.3 — SCD Type 2 in Practice
--
-- Business scenario:
--   NovaBuild insures contractors. Each contractor has a tier
--   (Probationary / Standard / Preferred / Elite) that changes as they
--   demonstrate safety performance and financial responsibility.
--
--   Underwriters ask questions like:
--     * "What tier was Allied Concrete Builders in when their 2023
--        claim was filed?"
--     * "How many contractors were Preferred tier at end of Q2 2024?"
--
--   The current `contractors` table only knows the CURRENT tier.
--   We need to preserve tier history.
--
-- Solution:
--   Build `dim_contractor_scd2` — same columns as contractors, plus
--   valid_from / valid_to / is_current / sk (surrogate key).
--
-- Target engine: PostgreSQL 15+ (NovaBuild demo database)
-- Assumed prerequisite tables: contractors, claims
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────
-- Step 1 — Create the SCD Type 2 dimension table
--
-- Same columns as `contractors` + four SCD2 metadata columns:
--   sk          — surrogate key, one per version of each contractor
--   valid_from  — timestamp when this version became active
--   valid_to    — timestamp when this version was superseded (NULL if current)
--   is_current  — TRUE for the current version (denormalised for query speed)
-- ─────────────────────────────────────────────────────────────────────

DROP TABLE IF EXISTS dim_contractor_scd2;

CREATE TABLE dim_contractor_scd2 (
    sk                 SERIAL       PRIMARY KEY,
    contractor_id      VARCHAR(20)  NOT NULL,
    company_name       VARCHAR(200) NOT NULL,
    trade              VARCHAR(100),
    state              VARCHAR(50),
    tier               VARCHAR(50),
    emr                NUMERIC(5,2),
    employees_count    INTEGER,
    valid_from         TIMESTAMP    NOT NULL,
    valid_to           TIMESTAMP,                  -- NULL = still current
    is_current         BOOLEAN      NOT NULL DEFAULT TRUE
);

-- Fast lookup for the "current version of contractor X" query.
CREATE INDEX ix_dim_contractor_scd2_current
    ON dim_contractor_scd2 (contractor_id, is_current);

-- Fast point-in-time lookup: "what version was active on YYYY-MM-DD?"
CREATE INDEX ix_dim_contractor_scd2_time_travel
    ON dim_contractor_scd2 (contractor_id, valid_from, valid_to);


-- ─────────────────────────────────────────────────────────────────────
-- Step 2 — Initial load from the operational table
--
-- Every current contractor gets one row with is_current = TRUE and
-- valid_from = NOW(). This is the starting point of history — anything
-- that existed before this load is treated as "always was this way."
-- ─────────────────────────────────────────────────────────────────────

INSERT INTO dim_contractor_scd2 (
    contractor_id, company_name, trade, state, tier, emr,
    employees_count, valid_from, valid_to, is_current
)
SELECT
    contractor_id,
    company_name,
    trade,
    state,
    tier,
    emr,
    employees_count,
    NOW()  AS valid_from,
    NULL   AS valid_to,
    TRUE   AS is_current
FROM contractors;


-- ─────────────────────────────────────────────────────────────────────
-- Step 3 — The SCD Type 2 update pattern (the core of this section)
--
-- Scenario: Allied Concrete Builders Inc has been upgraded from
-- Probationary tier to Preferred tier after 12 months of clean claims.
--
-- The SCD2 update happens in TWO atomic steps inside one transaction:
--   3a. Close the current version — set valid_to = NOW, is_current = FALSE
--   3b. Insert the new version   — new tier, valid_from = NOW, is_current = TRUE
--
-- Wrap in a transaction so both succeed or both fail — otherwise you
-- can end up with two "current" rows or zero.
-- ─────────────────────────────────────────────────────────────────────

BEGIN;

-- Step 3a — Close the current row
UPDATE dim_contractor_scd2
SET valid_to   = NOW(),
    is_current = FALSE
WHERE contractor_id = 'C-1234'          -- Allied Concrete Builders Inc
  AND is_current = TRUE;

-- Step 3b — Insert the new current row
INSERT INTO dim_contractor_scd2 (
    contractor_id, company_name, trade, state, tier, emr,
    employees_count, valid_from, valid_to, is_current
)
SELECT
    contractor_id,
    company_name,
    trade,
    state,
    'Preferred'      AS tier,           -- ← THE CHANGE
    1.05             AS emr,            -- new EMR reflecting good performance
    employees_count,
    NOW()            AS valid_from,
    NULL             AS valid_to,
    TRUE             AS is_current
FROM contractors
WHERE contractor_id = 'C-1234';

COMMIT;


-- ─────────────────────────────────────────────────────────────────────
-- Step 4 — Verify the history is preserved
--
-- Expected output: two rows for this contractor.
--   sk=X (older) — tier=Probationary, is_current=FALSE, valid_to=~NOW
--   sk=Y (newer) — tier=Preferred,    is_current=TRUE,  valid_to=NULL
-- ─────────────────────────────────────────────────────────────────────

SELECT
    sk,
    contractor_id,
    company_name,
    tier,
    emr,
    valid_from,
    valid_to,
    is_current
FROM dim_contractor_scd2
WHERE contractor_id = 'C-1234'
ORDER BY valid_from;


-- ─────────────────────────────────────────────────────────────────────
-- Step 5 — Time-travel query: "what tier was this contractor at
-- the time of claim CL-7823?"
--
-- This is the payoff of SCD Type 2. Join facts to the specific
-- historical version of the dimension.
-- ─────────────────────────────────────────────────────────────────────

SELECT
    c.claim_id,
    c.loss_date,
    d.company_name,
    d.tier          AS tier_at_time_of_claim,
    d.emr           AS emr_at_time_of_claim
FROM claims c
JOIN dim_contractor_scd2 d
    ON  d.contractor_id = c.contractor_id
    AND c.loss_date >= d.valid_from
    AND c.loss_date <  COALESCE(d.valid_to, '9999-12-31'::timestamp)
WHERE c.claim_id = 'CL-7823';

-- Note the join condition:
--   c.loss_date >= d.valid_from
--   AND c.loss_date < COALESCE(d.valid_to, +∞)
--
-- This is the standard "point-in-time" join. Works for both current
-- versions (where valid_to IS NULL, so COALESCE gives +∞) and
-- historical versions (where valid_to has a real timestamp).


-- ─────────────────────────────────────────────────────────────────────
-- Step 6 — Idempotent MERGE pattern (production-shape)
--
-- In a real pipeline, you don't hardcode 'C-1234'. Instead you compare
-- every source row against its current dimension row and only insert
-- new versions where attributes have changed.
--
-- Postgres 15+ has MERGE (SQL standard). Postgres 14 and older need
-- separate UPDATE and INSERT statements.
-- ─────────────────────────────────────────────────────────────────────

BEGIN;

-- 6a — Close rows where source has changed
UPDATE dim_contractor_scd2 d
SET valid_to   = NOW(),
    is_current = FALSE
FROM contractors s
WHERE d.contractor_id = s.contractor_id
  AND d.is_current    = TRUE
  AND (
        d.company_name    IS DISTINCT FROM s.company_name
     OR d.trade           IS DISTINCT FROM s.trade
     OR d.state           IS DISTINCT FROM s.state
     OR d.tier            IS DISTINCT FROM s.tier
     OR d.emr             IS DISTINCT FROM s.emr
     OR d.employees_count IS DISTINCT FROM s.employees_count
  );

-- 6b — Insert new current rows for either changed OR brand-new contractors
INSERT INTO dim_contractor_scd2 (
    contractor_id, company_name, trade, state, tier, emr,
    employees_count, valid_from, valid_to, is_current
)
SELECT
    s.contractor_id, s.company_name, s.trade, s.state, s.tier, s.emr,
    s.employees_count, NOW(), NULL, TRUE
FROM contractors s
LEFT JOIN dim_contractor_scd2 d
    ON  s.contractor_id = d.contractor_id
    AND d.is_current    = TRUE
WHERE d.contractor_id IS NULL;    -- no current row = new business key

COMMIT;


-- =====================================================================
-- Interview extensions
--
-- Q: "What if the source system deletes a contractor?"
-- A: SCD Type 2 typically uses soft-delete — mark the current row's
--    is_current = FALSE and valid_to = NOW, don't insert a replacement.
--    Some warehouses add is_deleted BOOLEAN column for clarity.
--
-- Q: "What if two updates happen on the same day?"
-- A: Grain matters. If valid_from/to are TIMESTAMP with microseconds,
--    that's fine. If they're DATE only, you'll have overlapping
--    versions — either promote to TIMESTAMP or add a version number.
--
-- Q: "How would you audit which columns changed?"
-- A: Add a JSONB `changed_attrs` column populated at insert time, or
--    join old + new rows using LAG in a view. See Section 6.4 (Data
--    Vault) for a cleaner separation of identity vs attributes.
-- =====================================================================
