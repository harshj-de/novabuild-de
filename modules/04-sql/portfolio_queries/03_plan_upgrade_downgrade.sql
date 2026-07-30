-- =====================================================================
-- Module 04 — Portfolio Query 3 — Plan Upgrade / Downgrade Tracking
--
-- Business question:
--   Every time an account changed plans, was it an upgrade or a
--   downgrade, and when did it happen?
--
-- Definition:
--   Compare the new plan to the previous plan for the same account
--   using LAG. If the new monthly_price > previous → Upgrade;
--   if new < previous → Downgrade; equal (rare, same price different
--   plan) → Lateral.
--
-- Why this query matters:
--   Product teams live and die by upgrade rate. This query gives them
--   the raw event stream to compute expansion revenue.
--
-- Concepts used: LAG window function, join to plans for pricing,
--   CASE for classification.
-- =====================================================================

WITH sub_history AS (
    SELECT
        s.account_id,
        s.plan_id,
        s.start_date,
        s.status,
        p.plan_name,
        p.monthly_price,
        LAG(p.plan_name)    OVER (
            PARTITION BY s.account_id ORDER BY s.start_date
        ) AS prev_plan_name,
        LAG(p.monthly_price) OVER (
            PARTITION BY s.account_id ORDER BY s.start_date
        ) AS prev_price
    FROM subscriptions s
    JOIN plans p ON s.plan_id = p.plan_id
)
SELECT
    account_id,
    start_date        AS change_date,
    prev_plan_name    AS from_plan,
    plan_name         AS to_plan,
    prev_price,
    monthly_price,
    CASE
        WHEN monthly_price > prev_price THEN 'Upgrade'
        WHEN monthly_price < prev_price THEN 'Downgrade'
        ELSE 'Lateral'
    END AS change_type
FROM sub_history
WHERE prev_plan_name IS NOT NULL         -- exclude the initial subscription
ORDER BY account_id, change_date;

-- Extension for the interview:
--   * "How much expansion revenue did we generate in Q3?"
--     → SUM(monthly_price - prev_price) WHERE change_type='Upgrade'
--       AND change_date is in Q3, × 12 for annualized impact.
