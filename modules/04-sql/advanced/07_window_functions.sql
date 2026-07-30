-- =====================================================================
-- Module 04 — SQL · Advanced · Section 4.7
-- Window Functions
--
-- The single most powerful feature in SQL for analytics. A window
-- function computes a value for each row using a "window" of related
-- rows, without collapsing the result set the way GROUP BY does.
--
-- Mental model:
--   SELECT ..., FUNC() OVER (PARTITION BY x ORDER BY y ROWS BETWEEN ...)
--
--   PARTITION BY  → reset the window per group (like GROUP BY)
--   ORDER BY      → row ordering within the window
--   ROWS/RANGE    → the frame — which rows count as "the window"
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────
-- Block 1 — ROW_NUMBER, RANK, DENSE_RANK
-- Three ways to number rows. The difference matters when values tie.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    i.account_id,
    p.payment_id,
    p.amount_paid,
    ROW_NUMBER() OVER (PARTITION BY i.account_id ORDER BY p.amount_paid DESC) AS row_num,
    RANK()       OVER (PARTITION BY i.account_id ORDER BY p.amount_paid DESC) AS rank_num,
    DENSE_RANK() OVER (PARTITION BY i.account_id ORDER BY p.amount_paid DESC) AS dense_num
FROM payments p
JOIN invoices i ON p.invoice_id = i.invoice_id
LIMIT 20;

-- ROW_NUMBER: 1,2,3,4 always distinct
-- RANK:       1,1,3,4 (gap after tie)
-- DENSE_RANK: 1,1,2,3 (no gap)


-- ─────────────────────────────────────────────────────────────────────
-- Block 2 — Top-N per group (the "greatest-N-per-group" pattern)
-- Get the top 2 highest payments per account. Nesting is required
-- because you cannot filter on a window function directly in WHERE.
-- ─────────────────────────────────────────────────────────────────────
SELECT *
FROM (
    SELECT
        i.account_id,
        p.payment_id,
        p.amount_paid,
        p.payment_date,
        ROW_NUMBER() OVER (
            PARTITION BY i.account_id
            ORDER BY p.amount_paid DESC
        ) AS rn
    FROM payments p
    JOIN invoices i ON p.invoice_id = i.invoice_id
) t
WHERE rn <= 2
ORDER BY account_id, rn;


-- ─────────────────────────────────────────────────────────────────────
-- Block 3 — LAG and LEAD — previous / next row
-- LAG returns the value N rows BEFORE the current row.
-- LEAD returns the value N rows AFTER. Classic use: period-over-period
-- comparisons.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    i.account_id,
    p.payment_date,
    p.amount_paid,
    LAG(p.amount_paid) OVER (
        PARTITION BY i.account_id ORDER BY p.payment_date
    ) AS prev_payment,
    p.amount_paid - LAG(p.amount_paid) OVER (
        PARTITION BY i.account_id ORDER BY p.payment_date
    ) AS change_from_prev
FROM payments p
JOIN invoices i ON p.invoice_id = i.invoice_id
ORDER BY i.account_id, p.payment_date
LIMIT 20;


-- ─────────────────────────────────────────────────────────────────────
-- Block 4 — Running / cumulative totals
-- SUM() with ORDER BY makes it cumulative rather than global.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    i.account_id,
    p.payment_date,
    p.amount_paid,
    SUM(p.amount_paid) OVER (
        PARTITION BY i.account_id
        ORDER BY p.payment_date
    ) AS running_total
FROM payments p
JOIN invoices i ON p.invoice_id = i.invoice_id
WHERE p.status = 'success'
ORDER BY i.account_id, p.payment_date
LIMIT 20;


-- ─────────────────────────────────────────────────────────────────────
-- Block 5 — ROWS vs RANGE frames (the interview question)
-- ROWS  — physical row offsets: "the 3 rows before this one"
-- RANGE — logical value offsets: "all rows with the same ORDER BY value"
--
-- The default when you write `ORDER BY x` with no explicit frame is
-- `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. If you have
-- ties in the ORDER BY, RANGE lumps them together. Almost always you
-- want ROWS.
-- ─────────────────────────────────────────────────────────────────────

-- 3-payment moving average (physical rows).
SELECT
    i.account_id,
    p.payment_date,
    p.amount_paid,
    AVG(p.amount_paid) OVER (
        PARTITION BY i.account_id
        ORDER BY p.payment_date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg_3
FROM payments p
JOIN invoices i ON p.invoice_id = i.invoice_id
WHERE p.status = 'success'
ORDER BY i.account_id, p.payment_date
LIMIT 20;


-- ─────────────────────────────────────────────────────────────────────
-- Block 6 — NTILE for percentile bucketing
-- Splits rows into N approximately-equal buckets. Common for quartile,
-- decile, or "which spending tier is this account in" analyses.
-- ─────────────────────────────────────────────────────────────────────
WITH account_revenue AS (
    SELECT
        i.account_id,
        SUM(p.amount_paid) AS revenue
    FROM payments p
    JOIN invoices i ON p.invoice_id = i.invoice_id
    WHERE p.status = 'success'
    GROUP BY i.account_id
)
SELECT
    account_id,
    revenue,
    NTILE(4) OVER (ORDER BY revenue DESC) AS revenue_quartile
FROM account_revenue
ORDER BY revenue DESC;


-- ─────────────────────────────────────────────────────────────────────
-- Block 7 — FIRST_VALUE, LAST_VALUE, NTH_VALUE
-- Direct access to specific frame positions without another subquery.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    i.account_id,
    p.payment_date,
    p.amount_paid,
    FIRST_VALUE(p.amount_paid) OVER (
        PARTITION BY i.account_id
        ORDER BY p.payment_date
    ) AS first_payment,
    LAST_VALUE(p.amount_paid) OVER (
        PARTITION BY i.account_id
        ORDER BY p.payment_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        -- ^ Must specify — the default frame ends at CURRENT ROW,
        --   which makes LAST_VALUE useless.
    ) AS last_payment
FROM payments p
JOIN invoices i ON p.invoice_id = i.invoice_id
ORDER BY i.account_id, p.payment_date
LIMIT 20;


-- ─────────────────────────────────────────────────────────────────────
-- Block 8 — PERCENT_RANK and CUME_DIST
-- Relative-position calculations for percentile analysis.
-- ─────────────────────────────────────────────────────────────────────
WITH account_revenue AS (
    SELECT
        i.account_id,
        SUM(p.amount_paid) AS revenue
    FROM payments p
    JOIN invoices i ON p.invoice_id = i.invoice_id
    WHERE p.status = 'success'
    GROUP BY i.account_id
)
SELECT
    account_id,
    revenue,
    PERCENT_RANK() OVER (ORDER BY revenue) AS pct_rank,
    CUME_DIST()    OVER (ORDER BY revenue) AS cume_dist
FROM account_revenue
ORDER BY revenue;


-- ─────────────────────────────────────────────────────────────────────
-- Block 9 — Named windows with WINDOW clause
-- When you use the same PARTITION BY / ORDER BY in multiple functions,
-- name the window once and reference it. Cleaner + less error-prone.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    i.account_id,
    p.payment_date,
    p.amount_paid,
    LAG(p.amount_paid)  OVER w AS prev_payment,
    LEAD(p.amount_paid) OVER w AS next_payment,
    SUM(p.amount_paid)  OVER w AS running_total,
    ROW_NUMBER()        OVER w AS payment_seq
FROM payments p
JOIN invoices i ON p.invoice_id = i.invoice_id
WINDOW w AS (PARTITION BY i.account_id ORDER BY p.payment_date)
ORDER BY i.account_id, p.payment_date
LIMIT 20;

-- =====================================================================
-- End of advanced/07_window_functions.sql
-- =====================================================================
