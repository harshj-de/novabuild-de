-- =====================================================================
-- Module 04 — Portfolio Query 7 — Running Total with Reset on Failure
--
-- Business question:
--   For each account, show a running total of payments — but reset
--   the total to zero every time a payment fails.
--
-- Why this query matters:
--   This is a hard interview question. The pattern (running total
--   with a reset trigger) shows up in fraud detection, uptime
--   streaks, loyalty programs, and cohort analytics. If you can
--   write this, you can defend "senior" as your title.
--
-- Concepts used: window function to create "reset groups", then a
--   second window inside each group. Two-step pattern.
--
-- Trick:
--   1. Increment a counter every time status = 'failed'. This gives
--      each streak of successes a unique group id.
--   2. SUM the amounts partitioned by that group id and ordered by
--      date. Result restarts at zero after each failure.
-- =====================================================================

WITH ordered_payments AS (
    SELECT
        i.account_id,
        p.payment_date,
        p.amount_paid,
        p.status
    FROM payments p
    JOIN invoices i ON p.invoice_id = i.invoice_id
),
with_reset_group AS (
    SELECT
        account_id,
        payment_date,
        amount_paid,
        status,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END)
            OVER (PARTITION BY account_id ORDER BY payment_date) AS reset_group
    FROM ordered_payments
)
SELECT
    account_id,
    payment_date,
    amount_paid,
    status,
    reset_group,
    CASE
        WHEN status = 'failed' THEN 0
        ELSE SUM(amount_paid) OVER (
            PARTITION BY account_id, reset_group
            ORDER BY payment_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        )
    END AS running_total
FROM with_reset_group
ORDER BY account_id, payment_date;

-- Extension for the interview:
--   * "What's each account's longest success streak?"
--     → COUNT(*) per (account_id, reset_group), MAX over account.
--   * "What was the largest running total ever reached before reset?"
--     → MAX(running_total) per (account_id, reset_group).
