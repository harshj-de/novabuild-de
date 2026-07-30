-- =====================================================================
-- Module 04 — Portfolio Query 1 — Monthly Recurring Revenue (MRR)
--
-- Business question:
--   For each calendar month, what was the MRR contributed by each plan?
--
-- Definition:
--   For every month M and every plan P, MRR = number of accounts on P
--   during M × plans.monthly_price. An account counts as "on P during
--   M" if its subscription overlaps that month (start_date <= end of
--   month AND (end_date IS NULL OR end_date > start of month)).
--
-- Why this query matters:
--   MRR is the single most-tracked SaaS metric. It's how boards judge
--   growth. Every SaaS DE writes this query in their first month.
--
-- Concepts used: recursive CTE for month generation, subscription
--   overlap logic with COALESCE, aggregation with JOIN.
-- =====================================================================

WITH RECURSIVE months AS (
    SELECT DATE '2024-01-01' AS month_start
  UNION ALL
    SELECT (month_start + INTERVAL '1 month')::date
    FROM months
    WHERE month_start < DATE '2024-12-01'
),
account_month_plan AS (
    -- Every (account, plan, month) tuple where the subscription was
    -- active for at least part of that month.
    SELECT
        s.account_id,
        s.plan_id,
        m.month_start
    FROM subscriptions s
    JOIN months m
        ON  s.start_date <= (m.month_start + INTERVAL '1 month' - INTERVAL '1 day')::date
        AND COALESCE(s.end_date, DATE '9999-12-31') > m.month_start
)
SELECT
    TO_CHAR(amp.month_start, 'YYYY-MM')  AS month,
    p.plan_name,
    COUNT(DISTINCT amp.account_id)       AS active_accounts,
    p.monthly_price,
    COUNT(DISTINCT amp.account_id) * p.monthly_price AS mrr
FROM account_month_plan amp
JOIN plans p ON amp.plan_id = p.plan_id
GROUP BY amp.month_start, p.plan_id, p.plan_name, p.monthly_price
ORDER BY amp.month_start, p.plan_name;

-- Extension for the interview:
--   * "How would you handle mid-month plan changes?"
--     → prorate by days in each plan within the month.
--   * "What if we bill annually?"
--     → divide annual price by 12; MRR ≠ ARR / 12 exactly under
--       cancellation, so track ARR separately.
