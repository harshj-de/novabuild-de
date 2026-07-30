-- =====================================================================
-- Module 04 — SQL · Fundamentals · Section 4.3
-- Aggregations, GROUP BY, HAVING
--
-- Where SQL becomes analytical. Every report and dashboard question —
-- "revenue by region", "orders per customer", "average deal size by
-- industry" — reduces to an aggregate + GROUP BY.
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────
-- Block 1 — The five basic aggregates
-- COUNT(*) counts all rows.
-- COUNT(col) counts rows where col IS NOT NULL — subtly different.
-- SUM, AVG, MIN, MAX ignore NULLs.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    COUNT(*)              AS total_accounts,
    COUNT(status)         AS accounts_with_status,      -- same here since NOT NULL
    COUNT(DISTINCT industry) AS unique_industries,
    MIN(signup_date)      AS earliest_signup,
    MAX(signup_date)      AS latest_signup
FROM accounts;


-- ─────────────────────────────────────────────────────────────────────
-- Block 2 — GROUP BY with one column
-- Every non-aggregate column in the SELECT list MUST appear in
-- GROUP BY. Postgres enforces this strictly; MySQL is more lenient
-- and can return surprising values.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    industry,
    COUNT(*) AS account_count
FROM accounts
GROUP BY industry
ORDER BY account_count DESC;


-- ─────────────────────────────────────────────────────────────────────
-- Block 3 — GROUP BY with multiple columns
-- Produces one row per unique combination of the group-by columns.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    industry,
    region,
    COUNT(*)                       AS account_count,
    COUNT(DISTINCT status)         AS distinct_statuses
FROM accounts
GROUP BY industry, region
ORDER BY industry, region;


-- ─────────────────────────────────────────────────────────────────────
-- Block 4 — Aggregating over a join
-- Total revenue per account. Because payments live in another table,
-- we join first, then aggregate. Use LEFT JOIN + COALESCE to include
-- zero-revenue accounts explicitly.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    a.account_id,
    a.company_name,
    COALESCE(SUM(p.amount_paid), 0) AS total_revenue
FROM accounts a
LEFT JOIN invoices i ON a.account_id = i.account_id
LEFT JOIN payments p ON i.invoice_id = p.invoice_id
GROUP BY a.account_id, a.company_name
ORDER BY total_revenue DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────
-- Block 5 — HAVING
-- Filter groups AFTER aggregation. HAVING sees aggregate values;
-- WHERE cannot. Rule of thumb: WHERE filters rows, HAVING filters
-- groups.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    a.industry,
    COUNT(*) AS account_count,
    AVG(i.amount) AS avg_invoice
FROM accounts a
JOIN invoices i ON a.account_id = i.account_id
GROUP BY a.industry
HAVING COUNT(*) > 20
ORDER BY avg_invoice DESC;


-- ─────────────────────────────────────────────────────────────────────
-- Block 6 — WHERE + GROUP BY + HAVING together
-- The full pipeline: filter rows first (WHERE), group them (GROUP BY),
-- filter groups (HAVING).
-- ─────────────────────────────────────────────────────────────────────
SELECT
    a.industry,
    COUNT(DISTINCT a.account_id) AS active_account_count,
    SUM(p.amount_paid)           AS industry_revenue
FROM accounts a
JOIN invoices i  ON a.account_id  = i.account_id
JOIN payments p ON i.invoice_id  = p.invoice_id
WHERE a.status = 'active'
  AND p.status = 'success'
GROUP BY a.industry
HAVING SUM(p.amount_paid) > 5000
ORDER BY industry_revenue DESC;


-- ─────────────────────────────────────────────────────────────────────
-- Block 7 — GROUP BY with expressions
-- You can group by any expression, not just a raw column. Common
-- example: bucket by month using DATE_TRUNC.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    DATE_TRUNC('month', p.payment_date)::date AS month,
    COUNT(*)                                  AS payment_count,
    SUM(p.amount_paid)                        AS monthly_revenue
FROM payments p
WHERE p.status = 'success'
GROUP BY DATE_TRUNC('month', p.payment_date)
ORDER BY month;


-- ─────────────────────────────────────────────────────────────────────
-- Block 8 — Ratio aggregation (part / whole)
-- Combining SUM with CASE lets you compute rates and percentages
-- inside a single aggregate expression. Very common for churn rate,
-- conversion rate, error rate.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    industry,
    COUNT(*)                                        AS total_accounts,
    SUM(CASE WHEN status = 'churned' THEN 1 ELSE 0 END) AS churned_count,
    ROUND(
        100.0 * SUM(CASE WHEN status = 'churned' THEN 1 ELSE 0 END)
        / COUNT(*),
        2
    ) AS churn_rate_pct
FROM accounts
GROUP BY industry
ORDER BY churn_rate_pct DESC;


-- ─────────────────────────────────────────────────────────────────────
-- Block 9 — GROUPING SETS, ROLLUP, CUBE
-- Advanced GROUP BY variants — produce subtotals at multiple levels
-- in one query. Common in reporting / dashboards.
-- ROLLUP(a, b, c) produces groups: (a,b,c), (a,b), (a), (): totals.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    industry,
    region,
    COUNT(*) AS account_count
FROM accounts
GROUP BY ROLLUP (industry, region)
ORDER BY industry NULLS LAST, region NULLS LAST;

-- =====================================================================
-- End of fundamentals/03_aggregations_groupby.sql
-- =====================================================================
