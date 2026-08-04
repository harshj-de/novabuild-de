-- =====================================================================
-- Section 6.7 — OLAP Operations
--
-- Five patterns every analyst uses against a warehouse. Each has a
-- SQL implementation and a Power BI equivalent — but the mental model
-- comes from OLAP cubes, so learning them as cube operations makes
-- them portable across tools.
--
--   1. DRILL-DOWN — go from summary to detail (year → month → day)
--   2. ROLL-UP    — go from detail to summary (day → month → year)
--   3. SLICE      — filter to one value of one dimension
--   4. DICE       — filter to a combination of multiple dimensions
--   5. PIVOT      — swap rows and columns (crosstab)
--
-- NovaBuild examples throughout. Assumes fact_claims + dim_contractor +
-- dim_date exist. In production these would sit in the Gold layer
-- (Section 6.5).
--
-- Target engine: PostgreSQL 15+
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────
-- Operation 1 — DRILL-DOWN
--
-- "Show me total claim losses by year — now break down the worst
--  year by month — now break down the worst month by contractor."
--
-- Each step goes DOWN the hierarchy: adds a finer dimension.
-- ─────────────────────────────────────────────────────────────────────

-- Level 1: by year
SELECT
    EXTRACT(YEAR FROM loss_date)::int AS year,
    ROUND(SUM(total_incurred)::numeric, 0) AS total_loss
FROM claims
GROUP BY year
ORDER BY year;

-- Level 2: worst year → break down by month
SELECT
    EXTRACT(YEAR FROM loss_date)::int  AS year,
    EXTRACT(MONTH FROM loss_date)::int AS month,
    ROUND(SUM(total_incurred)::numeric, 0) AS total_loss
FROM claims
WHERE EXTRACT(YEAR FROM loss_date) = 2023   -- drill into 2023
GROUP BY year, month
ORDER BY month;

-- Level 3: worst month → break down by contractor
SELECT
    c.company_name,
    ROUND(SUM(cl.total_incurred)::numeric, 0) AS total_loss
FROM claims cl
JOIN contractor_enrollments ce
    ON cl.program_id = ce.program_id
JOIN contractors c
    ON ce.contractor_id = c.contractor_id
WHERE EXTRACT(YEAR  FROM cl.loss_date) = 2023
  AND EXTRACT(MONTH FROM cl.loss_date) = 8       -- worst month = August
GROUP BY c.company_name
ORDER BY total_loss DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────
-- Operation 2 — ROLL-UP
--
-- The inverse of drill-down. Start with fine detail; aggregate to a
-- coarser hierarchy. In Postgres, ROLLUP() in GROUP BY gives you all
-- intermediate levels PLUS the grand total in one query.
-- ─────────────────────────────────────────────────────────────────────

-- Show claims by year, quarter, and month — plus subtotals.
SELECT
    EXTRACT(YEAR FROM loss_date)::int    AS year,
    EXTRACT(QUARTER FROM loss_date)::int AS quarter,
    EXTRACT(MONTH FROM loss_date)::int   AS month,
    COUNT(*)                             AS claim_count,
    ROUND(SUM(total_incurred)::numeric, 0) AS total_loss
FROM claims
GROUP BY ROLLUP(
    EXTRACT(YEAR FROM loss_date),
    EXTRACT(QUARTER FROM loss_date),
    EXTRACT(MONTH FROM loss_date)
)
ORDER BY year, quarter, month;

-- Read the output like this:
--   Rows with all three levels filled → most granular (month totals)
--   Rows with month = NULL             → quarter subtotals
--   Rows with quarter = NULL           → year subtotals
--   Row with year = NULL               → grand total


-- ─────────────────────────────────────────────────────────────────────
-- Operation 3 — SLICE
--
-- Fix ONE dimension to a single value. All measures return for that
-- slice only.
--
-- "Show me claims for Preferred-tier contractors only."
-- ─────────────────────────────────────────────────────────────────────

SELECT
    c.company_name,
    COUNT(cl.claim_id)                              AS claim_count,
    ROUND(SUM(cl.total_incurred)::numeric, 0)       AS total_loss,
    ROUND(AVG(cl.total_incurred)::numeric, 0)       AS avg_claim_size
FROM claims cl
JOIN contractor_enrollments ce
    ON cl.program_id = ce.program_id
JOIN contractors c
    ON ce.contractor_id = c.contractor_id
WHERE c.tier = 'Preferred'                          -- ← the SLICE
GROUP BY c.company_name
ORDER BY total_loss DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────
-- Operation 4 — DICE
--
-- Fix MULTIPLE dimensions to specific value(s). More restrictive than
-- SLICE — you're carving out a sub-cube.
--
-- "Show me Preferred-tier contractors in California with Bodily
--  Injury claims in 2023."
-- ─────────────────────────────────────────────────────────────────────

SELECT
    c.company_name,
    c.state,
    c.tier,
    cl.loss_type,
    cl.loss_date,
    ROUND(cl.total_incurred::numeric, 0) AS total_incurred
FROM claims cl
JOIN contractor_enrollments ce ON cl.program_id = ce.program_id
JOIN contractors c             ON ce.contractor_id = c.contractor_id
WHERE c.tier      = 'Preferred'                     -- dice: tier
  AND c.state     = 'CA'                            -- dice: state
  AND cl.loss_type = 'Bodily Injury'                -- dice: loss type
  AND EXTRACT(YEAR FROM cl.loss_date) = 2023        -- dice: year
ORDER BY cl.total_incurred DESC;


-- ─────────────────────────────────────────────────────────────────────
-- Operation 5 — PIVOT
--
-- Swap a dimension's values from rows into columns. Also called a
-- "crosstab" in reporting tools.
--
-- Postgres implements pivots via CASE + aggregation (or the
-- `crosstab()` function in the `tablefunc` extension).
--
-- "Show total loss with tier as rows and year as columns."
-- ─────────────────────────────────────────────────────────────────────

SELECT
    c.tier,
    ROUND(SUM(CASE WHEN EXTRACT(YEAR FROM cl.loss_date) = 2022
                   THEN cl.total_incurred ELSE 0 END)::numeric, 0) AS "2022",
    ROUND(SUM(CASE WHEN EXTRACT(YEAR FROM cl.loss_date) = 2023
                   THEN cl.total_incurred ELSE 0 END)::numeric, 0) AS "2023",
    ROUND(SUM(CASE WHEN EXTRACT(YEAR FROM cl.loss_date) = 2024
                   THEN cl.total_incurred ELSE 0 END)::numeric, 0) AS "2024",
    ROUND(SUM(cl.total_incurred)::numeric, 0) AS total
FROM claims cl
JOIN contractor_enrollments ce ON cl.program_id = ce.program_id
JOIN contractors c             ON ce.contractor_id = c.contractor_id
WHERE c.tier IS NOT NULL
GROUP BY c.tier
ORDER BY total DESC;


-- =====================================================================
-- Interview extensions
--
-- Q: "When would you use a materialised view for these queries?"
-- A: If the same drill-down / dice is run by a dashboard on every
--    page load, materialise it. The queries here scan the full claims
--    table each time. Section 6.8 covers pre-aggregate tables — the
--    same idea, but managed manually rather than by the DB.
--
-- Q: "What's the difference between GROUP BY ROLLUP and GROUPING SETS?"
-- A: ROLLUP((a,b,c)) gives you (a,b,c), (a,b), (a), (). GROUPING SETS
--    lets you specify any combination — including non-hierarchical
--    ones like ((a,b), (c)). CUBE gives you every combination.
--
-- Q: "How do you know if a column belongs in a fact or a dimension?"
-- A: If it's a measure you'd SUM or AVG, it's a fact. If it's an
--    attribute you'd GROUP BY, it's a dimension. Section 6.2 covered
--    the mental model.
-- =====================================================================
