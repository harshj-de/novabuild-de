-- =====================================================================
-- Module 04 — Portfolio Query 5 — Support Resolution Time by Industry
--
-- Business question:
--   Which industries have the fastest / slowest ticket resolution,
--   and how many tickets do we have per industry?
--
-- Why this query matters:
--   Support SLA is a top-3 recurring KPI for any B2B SaaS. Investors
--   ask about it every quarter.
--
-- Concepts used: date arithmetic on TIMESTAMP, FILTER for
--   conditional counting, careful handling of unresolved tickets.
-- =====================================================================

SELECT
    a.industry,
    COUNT(*)                                                AS total_tickets,
    COUNT(*) FILTER (WHERE t.status = 'resolved')           AS resolved_tickets,
    COUNT(*) FILTER (WHERE t.status IN ('open','in_progress')) AS unresolved_tickets,

    -- Average resolution time in HOURS. EXTRACT(EPOCH FROM ...) gives
    -- seconds, / 3600 converts to hours. AVG ignores NULLs from
    -- unresolved tickets automatically.
    ROUND(
        AVG(
            EXTRACT(EPOCH FROM (t.resolved_date - t.created_date)) / 3600
        )::numeric,
        2
    ) AS avg_resolution_hours,

    -- Median is often more useful than mean when a few tickets take
    -- forever. Postgres has PERCENTILE_CONT.
    ROUND(
        PERCENTILE_CONT(0.5) WITHIN GROUP (
            ORDER BY EXTRACT(EPOCH FROM (t.resolved_date - t.created_date)) / 3600
        )::numeric,
        2
    ) AS median_resolution_hours

FROM support_tickets t
JOIN accounts a ON t.account_id = a.account_id
GROUP BY a.industry
ORDER BY avg_resolution_hours NULLS LAST;

-- Extension for the interview:
--   * "Break this down by issue_type." → add issue_type to GROUP BY.
--   * "What % of tickets breach a 48-hour SLA?"
--     → COUNT(*) FILTER (WHERE resolution_hours > 48) / COUNT(*).
