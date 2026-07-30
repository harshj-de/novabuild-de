-- =====================================================================
-- Module 04 — Portfolio Query 6 — Feature Adoption by Plan
--
-- Business question:
--   For each subscription plan, what is the total feature usage per
--   feature? Which features drive engagement on Enterprise vs Starter?
--
-- Why this query matters:
--   Product-led-growth companies use this to decide which features
--   to move up a tier (paywall) or down (make free). It's the
--   quantitative half of every product roadmap conversation.
--
-- Concepts used: multi-table join across users → accounts →
--   subscriptions → plans; aggregation with proper de-duplication.
--
-- Correctness note:
--   An account may have multiple subscriptions over time (upgrades,
--   downgrades). We pick the CURRENT active subscription per account
--   (end_date IS NULL) so each user maps to exactly one plan.
-- =====================================================================

WITH current_plan_per_account AS (
    -- Pick each account's current subscription (or most recent).
    SELECT DISTINCT ON (account_id)
        account_id,
        plan_id
    FROM subscriptions
    WHERE end_date IS NULL
    ORDER BY account_id, start_date DESC
),
usage_with_plan AS (
    SELECT
        cpp.plan_id,
        fu.feature_id,
        fu.usage_count
    FROM feature_usage fu
    JOIN users u             ON fu.user_id    = u.user_id
    JOIN current_plan_per_account cpp
                            ON u.account_id  = cpp.account_id
)
SELECT
    p.plan_name,
    f.feature_name,
    SUM(uwp.usage_count) AS total_usage,
    COUNT(*)             AS event_count,
    ROUND(
        AVG(uwp.usage_count)::numeric,
        2
    ) AS avg_events_per_row
FROM usage_with_plan uwp
JOIN plans    p ON uwp.plan_id    = p.plan_id
JOIN features f ON uwp.feature_id = f.feature_id
GROUP BY p.plan_name, f.feature_name
ORDER BY p.plan_name, total_usage DESC;

-- Extension for the interview:
--   * "Show me feature adoption as a % of the plan's total usage."
--     → total_usage / SUM(total_usage) OVER (PARTITION BY plan_name).
--   * "Which features are used ONLY by Enterprise?"
--     → GROUP BY feature, HAVING COUNT(DISTINCT plan) = 1
--       AND MAX(plan_name) = 'Enterprise'.
