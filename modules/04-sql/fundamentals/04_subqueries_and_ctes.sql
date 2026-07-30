-- =====================================================================
-- Module 04 — SQL · Fundamentals · Section 4.4
-- Subqueries and CTEs
--
-- Both let you compose a query out of smaller queries. Subqueries
-- inline the sub-result; CTEs (WITH clauses) name it and make the
-- whole query readable top-to-bottom.
--
-- Rule of thumb: reach for a CTE first. Only inline a subquery when
-- it's genuinely single-use and short.
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────
-- Block 1 — Scalar subquery in SELECT
-- Returns a single value used inline. The subquery must return
-- exactly one row and one column.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    account_id,
    company_name,
    (SELECT COUNT(*) FROM invoices i
      WHERE i.account_id = accounts.account_id) AS invoice_count
FROM accounts
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────
-- Block 2 — Subquery in WHERE with IN
-- Filter parent rows based on a derived set of ids.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    account_id,
    company_name,
    industry
FROM accounts
WHERE account_id IN (
    SELECT account_id
    FROM invoices
    WHERE amount > 500
);


-- ─────────────────────────────────────────────────────────────────────
-- Block 3 — EXISTS
-- Often faster than IN when the subquery is large. EXISTS stops as
-- soon as it finds a match — semi-join semantics.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    account_id,
    company_name
FROM accounts a
WHERE EXISTS (
    SELECT 1
    FROM support_tickets t
    WHERE t.account_id = a.account_id
      AND t.status = 'open'
);


-- ─────────────────────────────────────────────────────────────────────
-- Block 4 — NOT EXISTS (anti-join)
-- Rows in the parent that DON'T have any matching child. Preferred
-- over `NOT IN` because NOT IN with a nullable subquery produces
-- surprising results (any NULL in the subquery makes everything unknown).
-- ─────────────────────────────────────────────────────────────────────
SELECT
    account_id,
    company_name
FROM accounts a
WHERE NOT EXISTS (
    SELECT 1
    FROM invoices i
    WHERE i.account_id = a.account_id
);


-- ─────────────────────────────────────────────────────────────────────
-- Block 5 — Correlated subquery
-- The inner query references the outer row (a.account_id). One
-- inner query runs per outer row — expensive on large tables.
-- Often refactorable to a JOIN + window function.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    a.account_id,
    a.company_name,
    (SELECT MAX(p.payment_date)
     FROM payments p
     JOIN invoices i ON p.invoice_id = i.invoice_id
     WHERE i.account_id = a.account_id) AS latest_payment
FROM accounts a
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────
-- Block 6 — Basic CTE (WITH clause)
-- Name a sub-result and reference it by name below. Reads like
-- a small script instead of nested parentheses.
-- ─────────────────────────────────────────────────────────────────────
WITH account_revenue AS (
    SELECT
        i.account_id,
        SUM(p.amount_paid) AS total_revenue
    FROM invoices i
    JOIN payments p ON i.invoice_id = p.invoice_id
    WHERE p.status = 'success'
    GROUP BY i.account_id
)
SELECT
    a.company_name,
    ar.total_revenue
FROM accounts a
JOIN account_revenue ar ON a.account_id = ar.account_id
ORDER BY ar.total_revenue DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────
-- Block 7 — Multiple CTEs
-- Chain named sub-queries. Each CTE can reference earlier ones. The
-- final SELECT ties them together.
-- ─────────────────────────────────────────────────────────────────────
WITH
account_revenue AS (
    SELECT
        i.account_id,
        SUM(p.amount_paid) AS total_revenue
    FROM invoices i
    JOIN payments p ON i.invoice_id = p.invoice_id
    WHERE p.status = 'success'
    GROUP BY i.account_id
),
active_user_counts AS (
    SELECT
        account_id,
        COUNT(*) FILTER (WHERE is_active) AS active_users
    FROM users
    GROUP BY account_id
)
SELECT
    a.company_name,
    a.industry,
    ar.total_revenue,
    auc.active_users
FROM accounts a
LEFT JOIN account_revenue ar  ON a.account_id = ar.account_id
LEFT JOIN active_user_counts auc ON a.account_id = auc.account_id
ORDER BY ar.total_revenue DESC NULLS LAST
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────
-- Block 8 — CTE vs derived table
-- The same query written as a derived table (subquery in FROM):
-- functionally equivalent but harder to scan. Prefer CTEs.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    a.company_name,
    ar.total_revenue
FROM accounts a
JOIN (
    SELECT
        i.account_id,
        SUM(p.amount_paid) AS total_revenue
    FROM invoices i
    JOIN payments p ON i.invoice_id = p.invoice_id
    WHERE p.status = 'success'
    GROUP BY i.account_id
) ar ON a.account_id = ar.account_id
ORDER BY ar.total_revenue DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────
-- Block 9 — Materialisation note
-- Postgres 12+ can inline CTEs when they're referenced once (like
-- subqueries) or materialise them when referenced multiple times.
-- Force behaviour with MATERIALIZED / NOT MATERIALIZED if you need
-- to override the planner's choice.
-- ─────────────────────────────────────────────────────────────────────

-- Force materialisation (compute once, reuse):
WITH revenue AS MATERIALIZED (
    SELECT account_id, SUM(amount) AS total FROM invoices GROUP BY account_id
)
SELECT COUNT(*) FROM revenue WHERE total > 1000;

-- =====================================================================
-- End of fundamentals/04_subqueries_and_ctes.sql
-- =====================================================================
