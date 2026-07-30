-- =====================================================================
-- Module 04 — SQL · Fundamentals · Section 4.5
-- Set operations (UNION, INTERSECT, EXCEPT) and CASE expressions
--
-- Set operations combine query results row-wise.
-- CASE is SQL's if/else — used everywhere from labels to conditional
-- aggregates.
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────
-- Block 1 — UNION (deduplicates) vs UNION ALL (keeps duplicates)
-- All parts must have the same number of columns with compatible types.
-- Prefer UNION ALL unless you actually need dedup — it's much cheaper.
-- ─────────────────────────────────────────────────────────────────────
SELECT industry, region FROM accounts WHERE status = 'active'
UNION
SELECT industry, region FROM accounts WHERE status = 'trial'
ORDER BY industry, region;

-- vs.
SELECT industry, region FROM accounts WHERE status = 'active'
UNION ALL
SELECT industry, region FROM accounts WHERE status = 'trial';
-- Faster and preserves duplicates; the row count reveals whether
-- there were overlaps.


-- ─────────────────────────────────────────────────────────────────────
-- Block 2 — INTERSECT
-- Rows appearing in BOTH result sets.
-- ─────────────────────────────────────────────────────────────────────

-- Industries present in both "active" and "churned" accounts:
SELECT DISTINCT industry FROM accounts WHERE status = 'active'
INTERSECT
SELECT DISTINCT industry FROM accounts WHERE status = 'churned';


-- ─────────────────────────────────────────────────────────────────────
-- Block 3 — EXCEPT (Postgres) / MINUS (Oracle)
-- Rows in the FIRST result set that are NOT in the second.
-- ─────────────────────────────────────────────────────────────────────

-- Industries with active accounts but NO churned accounts:
SELECT DISTINCT industry FROM accounts WHERE status = 'active'
EXCEPT
SELECT DISTINCT industry FROM accounts WHERE status = 'churned';


-- ─────────────────────────────────────────────────────────────────────
-- Block 4 — CASE for row labels (simple form)
-- Test the same column against multiple values. Falls back to ELSE.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    invoice_id,
    amount,
    CASE amount
        WHEN 49  THEN 'Starter'
        WHEN 199 THEN 'Growth'
        WHEN 999 THEN 'Enterprise'
        ELSE 'Custom'
    END AS billed_tier
FROM invoices
LIMIT 15;


-- ─────────────────────────────────────────────────────────────────────
-- Block 5 — CASE for row labels (searched form)
-- Each WHEN is its own boolean expression. Much more flexible.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    invoice_id,
    amount,
    CASE
        WHEN amount < 100                THEN 'Low'
        WHEN amount BETWEEN 100 AND 500  THEN 'Medium'
        WHEN amount > 500                THEN 'High'
        ELSE 'Unknown'
    END AS amount_tier
FROM invoices
LIMIT 15;


-- ─────────────────────────────────────────────────────────────────────
-- Block 6 — Conditional aggregation with CASE
-- Count / sum only the rows meeting a condition. Preferred over
-- separate queries + UNION when you want everything in one row.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    industry,
    COUNT(*)                                                       AS total,
    COUNT(*) FILTER (WHERE status = 'active')                      AS active_count,
    COUNT(*) FILTER (WHERE status = 'churned')                     AS churned_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'churned') / COUNT(*),
        2
    ) AS churn_pct
FROM accounts
GROUP BY industry
ORDER BY churn_pct DESC;

-- Note: Postgres supports both `SUM(CASE WHEN ... THEN 1 ELSE 0 END)`
-- and the terser `COUNT(*) FILTER (WHERE ...)`. Use FILTER when your
-- engine supports it — it reads more clearly.


-- ─────────────────────────────────────────────────────────────────────
-- Block 7 — CASE inside ORDER BY
-- Custom sort orders. Useful when the default alphabetical or numeric
-- order isn't what you want.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    plan_name,
    monthly_price
FROM plans
ORDER BY CASE plan_name
    WHEN 'Starter'    THEN 1
    WHEN 'Growth'     THEN 2
    WHEN 'Enterprise' THEN 3
    ELSE 999
END;


-- ─────────────────────────────────────────────────────────────────────
-- Block 8 — COALESCE and NULLIF
-- COALESCE returns the first non-null argument. NULLIF returns NULL
-- if two args are equal, else the first. Both are conceptual cousins
-- of CASE and often more readable.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    invoice_id,
    account_id,
    -- If the invoice has no payment yet, show 0 not NULL.
    COALESCE(
        (SELECT SUM(amount_paid) FROM payments p WHERE p.invoice_id = i.invoice_id),
        0
    ) AS total_paid
FROM invoices i
LIMIT 10;

-- NULLIF example: guard against divide-by-zero.
SELECT
    industry,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'churned')
        / NULLIF(COUNT(*), 0),          -- returns NULL, not error
        2
    ) AS churn_pct
FROM accounts
GROUP BY industry;

-- =====================================================================
-- End of fundamentals/05_set_operations_and_case.sql
-- =====================================================================
