-- =====================================================================
-- Module 04 — Portfolio Query 4 — Top 3 Accounts by Revenue per Industry
--
-- Business question:
--   Within each industry, which are the top-3 revenue-generating
--   accounts? (Classic "greatest-N-per-group" problem.)
--
-- Why this query matters:
--   Sales leadership uses this every quarter to identify strategic
--   accounts and to spot concentration risk.
--
-- Concepts used: total revenue aggregation via 3-table join, then
--   RANK inside a CTE, then WHERE rank <= 3.
--
-- Note on RANK vs ROW_NUMBER:
--   RANK gives ties the same rank and skips the next value ("bronze,
--   bronze, no silver, gold"). ROW_NUMBER always gives distinct
--   values. Choose based on how you want ties handled.
--   Here we use RANK — if two accounts tie for #3, both appear.
-- =====================================================================

WITH account_revenue AS (
    SELECT
        a.account_id,
        a.company_name,
        a.industry,
        SUM(p.amount_paid) AS revenue
    FROM accounts a
    JOIN invoices i ON a.account_id = i.account_id
    JOIN payments p ON i.invoice_id = p.invoice_id
    WHERE p.status = 'success'
    GROUP BY a.account_id, a.company_name, a.industry
),
ranked AS (
    SELECT
        industry,
        company_name,
        revenue,
        RANK() OVER (
            PARTITION BY industry
            ORDER BY revenue DESC
        ) AS revenue_rank
    FROM account_revenue
)
SELECT
    industry,
    revenue_rank,
    company_name,
    revenue
FROM ranked
WHERE revenue_rank <= 3
ORDER BY industry, revenue_rank;

-- Extension for the interview:
--   * "What if I want top 3 STRICTLY, no ties?" → use ROW_NUMBER.
--   * "Show me the % of industry revenue each top-3 account owns."
--     → add SUM(revenue) OVER (PARTITION BY industry) and divide.
