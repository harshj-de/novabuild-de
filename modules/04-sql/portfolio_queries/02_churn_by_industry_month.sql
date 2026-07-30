-- =====================================================================
-- Module 04 — Portfolio Query 2 — Churn Analysis by Industry and Month
--
-- Business question:
--   For each (industry, month), what percent of accounts churned?
--
-- Definition used here:
--   Churn rate for (industry, month) = churned accounts in that month
--   as a percent of total accounts in the industry that were ever
--   active before or during that month.
--
--   (This is one of several valid definitions; the interviewer may
--    prefer "denominator = accounts active at the start of the month".
--    Both are defensible; state your definition upfront.)
--
-- Why this query matters:
--   Investors ask about churn every board meeting. The DE who can
--   produce it fresh in 5 minutes is the DE who gets promoted.
--
-- Concepts used: date_trunc for month bucketing, FILTER for
--   conditional counts, NULLIF to avoid divide-by-zero.
-- =====================================================================

WITH churn_by_month AS (
    SELECT
        DATE_TRUNC('month', signup_date)::date AS month,
        industry,
        COUNT(*) FILTER (WHERE status = 'churned') AS churned_count,
        COUNT(*)                                   AS total_count
    FROM accounts
    GROUP BY DATE_TRUNC('month', signup_date), industry
)
SELECT
    TO_CHAR(month, 'YYYY-MM') AS month,
    industry,
    total_count,
    churned_count,
    ROUND(
        100.0 * churned_count / NULLIF(total_count, 0),
        2
    ) AS churn_rate_pct
FROM churn_by_month
WHERE total_count > 0
ORDER BY month, industry;

-- Extension for the interview:
--   * "Show me the industries with worst churn."
--     → ORDER BY churn_rate_pct DESC.
--   * "What's the 3-month rolling churn per industry?"
--     → wrap the above in another CTE and use a windowed AVG.
