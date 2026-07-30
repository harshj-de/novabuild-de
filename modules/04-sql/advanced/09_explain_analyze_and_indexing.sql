-- =====================================================================
-- Module 04 — SQL · Advanced · Section 4.9
-- Query Performance: EXPLAIN ANALYZE, Indexing, Partitioning
--
-- Every Data Engineer will get "why is this query slow?" questions.
-- This section gives you the tools to answer them:
--   * Read an execution plan
--   * Add the right kind of index for the right kind of query
--   * Partition big tables so scans stay local
--
-- Everything here is Postgres-specific in syntax but the concepts
-- (sequential vs index scans, hash vs nested-loop joins, planner
-- statistics) apply to every RDBMS.
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────
-- Block 1 — EXPLAIN vs EXPLAIN ANALYZE
-- EXPLAIN            → planner's estimate (fast; doesn't run the query)
-- EXPLAIN ANALYZE    → actually runs it and shows real timings
-- EXPLAIN (ANALYZE, BUFFERS) → also shows cache hits / disk reads
--
-- Rule of thumb: use EXPLAIN ANALYZE BUFFERS for anything you're
-- optimizing seriously. Never run EXPLAIN ANALYZE on a mutating
-- statement unless wrapped in a transaction you'll roll back.
-- ─────────────────────────────────────────────────────────────────────
EXPLAIN ANALYZE
SELECT
    a.company_name,
    a.industry,
    COUNT(i.invoice_id) AS invoice_count,
    SUM(i.amount)       AS total_amount
FROM accounts a
JOIN invoices i ON a.account_id = i.account_id
WHERE i.invoice_date >= '2024-01-01'
  AND i.status = 'paid'
GROUP BY a.company_name, a.industry
ORDER BY total_amount DESC;


-- ─────────────────────────────────────────────────────────────────────
-- Block 2 — What to look at in the plan
-- Read the plan bottom-up (leaves execute first). Key things:
--
--   Seq Scan on invoices  →  full table scan. Fine if the table is
--                            small OR you're selecting a large fraction
--                            of rows. Bad if you're filtering hard.
--   Index Scan            →  uses an index. Usually what you want.
--   Bitmap Heap Scan      →  Postgres decided to combine multiple
--                            index results. Common with OR filters.
--   Hash Join             →  builds a hash of one side (fast for
--                            large joins)
--   Nested Loop           →  fine for small right-side; catastrophic
--                            for large
--   Sort                  →  expensive if it can't fit in work_mem
--   Rows removed by Filter → planner overestimated selectivity; may
--                            want to add an index
-- ─────────────────────────────────────────────────────────────────────


-- ─────────────────────────────────────────────────────────────────────
-- Block 3 — B-tree index — the default and best for most cases
-- Good for: = comparisons, range comparisons (<, >, BETWEEN), ORDER BY.
-- Already created in setup — this shows the SYNTAX.
-- ─────────────────────────────────────────────────────────────────────

-- Example: speed up "get invoices for account X within a date range"
CREATE INDEX IF NOT EXISTS
    ix_invoices_account_and_date
ON invoices (account_id, invoice_date);

-- Column order matters: this index accelerates queries filtering on
-- (account_id) alone or (account_id, invoice_date) together.
-- It does NOT accelerate filtering on invoice_date alone —
-- postgres cannot skip the leading column.


-- ─────────────────────────────────────────────────────────────────────
-- Block 4 — Partial index — indexing only a subset of rows
-- Cheaper storage, faster maintenance, faster query — when you almost
-- always filter on the same predicate.
-- ─────────────────────────────────────────────────────────────────────

-- Speed up queries that always filter on paid invoices.
CREATE INDEX IF NOT EXISTS
    ix_invoices_paid_only
ON invoices (invoice_date)
WHERE status = 'paid';

-- The planner will only use this when the WHERE clause is compatible.


-- ─────────────────────────────────────────────────────────────────────
-- Block 5 — When indexes DON'T help
--   * Very small tables      → sequential scan is faster than an index seek
--   * High-cardinality writes → every index slows INSERT / UPDATE / DELETE
--   * Filter selectivity too low → planner ignores the index and scans anyway
--   * Function on column     → indexes on `col` don't help `WHERE UPPER(col) = ...`
--     Use functional index instead: CREATE INDEX ... ON t (UPPER(col))
-- ─────────────────────────────────────────────────────────────────────


-- ─────────────────────────────────────────────────────────────────────
-- Block 6 — Partitioning — for tables too big to scan effectively
-- Split one logical table into many physical child tables. Postgres
-- automatically routes rows to the right partition and only scans
-- relevant partitions ("partition pruning") when the query has a
-- filter on the partition key.
--
-- Rule of thumb: partition when a table exceeds ~50-100 GB or when
-- queries always filter on time and you can partition by month.
-- ─────────────────────────────────────────────────────────────────────

-- Example: a hypothetical partitioned event log by month.
CREATE TABLE IF NOT EXISTS events (
    event_id     BIGSERIAL,
    account_id   INTEGER NOT NULL,
    event_type   TEXT    NOT NULL,
    occurred_at  TIMESTAMP NOT NULL,
    payload      JSONB,
    PRIMARY KEY (event_id, occurred_at)     -- partition key must be in PK
) PARTITION BY RANGE (occurred_at);

-- Create monthly partitions.
CREATE TABLE IF NOT EXISTS events_2024_01
    PARTITION OF events
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE IF NOT EXISTS events_2024_02
    PARTITION OF events
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- When a query filters on occurred_at, Postgres skips irrelevant
-- partitions entirely. This is "partition pruning."


-- ─────────────────────────────────────────────────────────────────────
-- Block 7 — Common performance interview question
-- "You have a table with a billion rows and this query is slow.
--  Walk me through what you'd do."
--
-- The right answer, in order:
--   1. EXPLAIN ANALYZE to see what's actually happening
--   2. Check row estimates vs actual — if very wrong, run ANALYZE
--   3. Look for Seq Scan on a large table with a selective filter
--   4. Consider an appropriate index — B-tree, partial, or functional
--   5. If the table is huge, consider partitioning by the filter column
--   6. Consider materialized views if the same aggregation is queried repeatedly
--   7. Look at work_mem — a hash join that spills to disk is 100x slower
-- ─────────────────────────────────────────────────────────────────────


-- ─────────────────────────────────────────────────────────────────────
-- Block 8 — Materialised views
-- Cache the result of an expensive query as a table. Refreshed on
-- demand rather than every read. Good for slow-moving dashboards.
-- ─────────────────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_monthly_revenue AS
    SELECT
        DATE_TRUNC('month', p.payment_date)::date AS month,
        SUM(p.amount_paid)                        AS revenue
    FROM payments p
    WHERE p.status = 'success'
    GROUP BY DATE_TRUNC('month', p.payment_date);

-- Refresh on schedule (or after ETL runs):
REFRESH MATERIALIZED VIEW mv_monthly_revenue;

-- Refresh without blocking readers (requires a unique index):
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_monthly_revenue;

-- =====================================================================
-- End of advanced/09_explain_analyze_and_indexing.sql
-- =====================================================================
