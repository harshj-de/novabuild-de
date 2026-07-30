-- =====================================================================
-- Module 04 — SQL · Fundamentals · Section 4.1
-- SELECT, WHERE, ORDER BY, LIMIT
--
-- The four verbs every SQL statement starts with. Every downstream
-- concept (joins, aggregations, windows) still uses these.
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────
-- Block 1 — SELECT: pull specific columns instead of SELECT *
-- Using SELECT * in production code is a smell:
--   • schemas evolve and consumers break silently
--   • pulling all columns wastes network and memory
--   • it hides your intent from reviewers
-- ─────────────────────────────────────────────────────────────────────
SELECT
    account_id,
    company_name,
    industry
FROM accounts
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────
-- Block 2 — Column aliases with AS
-- Rename columns for readability, especially when the raw name is
-- cryptic or when the same column appears in multiple joined tables.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    account_id       AS id,
    company_name     AS name,
    signup_date      AS joined_on
FROM accounts
LIMIT 5;


-- ─────────────────────────────────────────────────────────────────────
-- Block 3 — WHERE with a single condition
-- Only returns rows where the predicate is TRUE. NULL comparisons
-- (`col = NULL`) always return unknown, not TRUE — see Block 6.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    account_id,
    company_name,
    industry
FROM accounts
WHERE industry = 'SaaS';


-- ─────────────────────────────────────────────────────────────────────
-- Block 4 — WHERE with combined conditions (AND, OR, NOT)
-- AND binds tighter than OR — always parenthesise mixed clauses to
-- express intent explicitly. `region IN (...)` is cleaner than a
-- string of OR clauses.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    account_id,
    company_name,
    industry,
    region
FROM accounts
WHERE industry = 'SaaS'
  AND region IN ('North America', 'Europe')
  AND status = 'active';


-- ─────────────────────────────────────────────────────────────────────
-- Block 5 — Pattern matching with LIKE
-- % matches any string of characters (including empty);
-- _ matches exactly one character.
-- Case-sensitivity is engine-dependent — Postgres has ILIKE (case-
-- insensitive) which is often what you actually want for user input.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    account_id,
    company_name
FROM accounts
WHERE company_name ILIKE 'Acme%';


-- ─────────────────────────────────────────────────────────────────────
-- Block 6 — NULL handling
-- NULL is not equal to anything (not even another NULL). Use
-- IS NULL / IS NOT NULL. Forgetting this is the classic beginner
-- bug that silently produces empty result sets.
-- ─────────────────────────────────────────────────────────────────────

-- Wrong — returns nothing:
-- SELECT * FROM subscriptions WHERE end_date = NULL;

-- Right — returns still-active subscriptions:
SELECT
    subscription_id,
    account_id,
    plan_id
FROM subscriptions
WHERE end_date IS NULL;


-- ─────────────────────────────────────────────────────────────────────
-- Block 7 — BETWEEN for range checks (inclusive on both ends)
-- ─────────────────────────────────────────────────────────────────────
SELECT
    invoice_id,
    account_id,
    amount,
    invoice_date
FROM invoices
WHERE invoice_date BETWEEN '2024-06-01' AND '2024-06-30'
ORDER BY invoice_date;


-- ─────────────────────────────────────────────────────────────────────
-- Block 8 — ORDER BY: single column, then multiple
-- Default sort is ASC (ascending). Use DESC for descending. When
-- sorting on nullable columns, decide NULLS FIRST or NULLS LAST
-- explicitly — engines differ on the default.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    account_id,
    company_name,
    signup_date
FROM accounts
ORDER BY signup_date DESC, company_name ASC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────
-- Block 9 — LIMIT and OFFSET
-- LIMIT caps the result count; OFFSET skips rows before returning.
-- Together they implement pagination. Note: OFFSET on large tables
-- is expensive — real production pagination uses keyset
-- (cursor-based) pagination instead.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    account_id,
    company_name
FROM accounts
ORDER BY account_id
LIMIT 10 OFFSET 20;   -- rows 21-30


-- ─────────────────────────────────────────────────────────────────────
-- Block 10 — DISTINCT
-- Removes duplicate rows from the result. Beware — applied AFTER
-- all columns are selected. `SELECT DISTINCT a, b FROM t` returns
-- unique (a, b) pairs, not just unique a's.
-- ─────────────────────────────────────────────────────────────────────
SELECT DISTINCT industry
FROM accounts
ORDER BY industry;

-- =====================================================================
-- End of fundamentals/01_select_where_orderby.sql
-- =====================================================================
