-- =====================================================================
-- Module 04 — Portfolio Query 8 — Gaps and Islands
--
-- Business question:
--   For each account, find the CONSECUTIVE ranges of months in which
--   invoices were issued. A break in the sequence starts a new "island."
--
-- Why this query matters:
--   Gaps-and-islands is one of the four or five classic SQL puzzles
--   that shows up in senior interviews. Once you know the trick you
--   can apply it to detecting session boundaries, contiguous device
--   uptime, streaks of positive stock returns, and dozens of other
--   real problems.
--
-- The trick:
--   1. Number the months per account with ROW_NUMBER (rn = 1, 2, 3, …).
--   2. Subtract rn (as months) from the actual month.
--   3. All rows in the same island produce the same value.
--      That value becomes the group key. GROUP BY it.
--
-- Example: months [Jan, Feb, Mar, Jun, Jul] with rn [1,2,3,4,5]
--          gives grp [Dec-1, Dec-1, Dec-1, Feb-1, Feb-1] — two islands.
-- =====================================================================

WITH invoice_months AS (
    SELECT DISTINCT
        account_id,
        DATE_TRUNC('month', invoice_date)::date AS month
    FROM invoices
),
numbered AS (
    SELECT
        account_id,
        month,
        ROW_NUMBER() OVER (
            PARTITION BY account_id ORDER BY month
        ) AS rn
    FROM invoice_months
),
with_group_key AS (
    SELECT
        account_id,
        month,
        month - (rn * INTERVAL '1 month') AS grp
    FROM numbered
)
SELECT
    account_id,
    MIN(month) AS island_start,
    MAX(month) AS island_end,
    COUNT(*)   AS island_length_months
FROM with_group_key
GROUP BY account_id, grp
ORDER BY account_id, island_start;

-- Extension for the interview:
--   * "How many gaps did each account have?" → COUNT(*) - 1 islands.
--   * "Find the longest island per account."
--     → wrap in another CTE, RANK by length within account.
