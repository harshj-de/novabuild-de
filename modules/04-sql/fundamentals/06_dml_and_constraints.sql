-- =====================================================================
-- Module 04 — SQL · Fundamentals · Section 4.6
-- DML (INSERT, UPDATE, DELETE, UPSERT) and Constraints
--
-- The mutation side of SQL. In pipelines this is what actually
-- persists your work. Get it wrong and rows disappear silently.
--
-- Every mutating statement should be prepared to survive:
--   * partial failure (transactions + rollback)
--   * concurrent writes (proper isolation + constraints)
--   * repeated execution (idempotency via UPSERT)
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────
-- Block 1 — Single-row INSERT
-- Always list column names explicitly. Positional inserts break
-- silently when the schema changes (e.g. someone adds a column).
-- ─────────────────────────────────────────────────────────────────────
INSERT INTO accounts (company_name, industry, signup_date, region, status)
VALUES ('New Corp Inc.', 'SaaS', '2024-12-01', 'North America', 'trial');


-- ─────────────────────────────────────────────────────────────────────
-- Block 2 — Multi-row INSERT
-- One statement, many rows. Much faster than N single-row inserts —
-- planner overhead and transaction cost paid once instead of N times.
-- ─────────────────────────────────────────────────────────────────────
INSERT INTO plans (plan_name, monthly_price) VALUES
    ('Bronze',   19.00),
    ('Silver',   49.00),
    ('Gold',    149.00);


-- ─────────────────────────────────────────────────────────────────────
-- Block 3 — INSERT ... SELECT
-- Populate a table from a query. Common for backfills and for
-- copying data between environments.
-- ─────────────────────────────────────────────────────────────────────

-- Backfill a "vip_accounts" table with high-revenue accounts.
CREATE TABLE IF NOT EXISTS vip_accounts (
    account_id     INTEGER PRIMARY KEY,
    company_name   TEXT NOT NULL,
    total_revenue  NUMERIC(12,2) NOT NULL
);

INSERT INTO vip_accounts (account_id, company_name, total_revenue)
SELECT
    a.account_id,
    a.company_name,
    SUM(p.amount_paid) AS total_revenue
FROM accounts a
JOIN invoices i ON a.account_id = i.account_id
JOIN payments p ON i.invoice_id = p.invoice_id
WHERE p.status = 'success'
GROUP BY a.account_id, a.company_name
HAVING SUM(p.amount_paid) > 5000
ON CONFLICT (account_id) DO NOTHING;   -- idempotent — safe to re-run


-- ─────────────────────────────────────────────────────────────────────
-- Block 4 — UPSERT — INSERT ... ON CONFLICT
-- The idempotent-insert pattern every DE pipeline needs.
-- ON CONFLICT tells Postgres what to do when a unique constraint
-- would be violated.
-- ─────────────────────────────────────────────────────────────────────
INSERT INTO plans (plan_name, monthly_price)
VALUES ('Enterprise', 1200.00)          -- price changed
ON CONFLICT (plan_name)
DO UPDATE SET monthly_price = EXCLUDED.monthly_price;
-- EXCLUDED refers to the row that would have been inserted.


-- ─────────────────────────────────────────────────────────────────────
-- Block 5 — UPDATE with WHERE
-- ALWAYS write the WHERE first (as a SELECT), verify the rows are
-- what you intend, THEN convert to UPDATE. UPDATE without WHERE
-- touches every row — the classic career-ending mistake.
-- ─────────────────────────────────────────────────────────────────────

-- Step 1: verify.
SELECT COUNT(*)
FROM accounts
WHERE status = 'trial'
  AND signup_date < '2024-06-01';

-- Step 2: apply.
UPDATE accounts
SET status = 'churned'
WHERE status = 'trial'
  AND signup_date < '2024-06-01';


-- ─────────────────────────────────────────────────────────────────────
-- Block 6 — UPDATE ... FROM (Postgres-specific)
-- Update rows by joining to another table. In standard SQL this
-- requires a correlated subquery — Postgres/PG-compatible engines
-- offer the terser FROM form.
-- ─────────────────────────────────────────────────────────────────────
UPDATE accounts a
SET status = 'churned'
FROM subscriptions s
WHERE s.account_id = a.account_id
  AND s.status = 'cancelled'
  AND s.end_date < CURRENT_DATE - INTERVAL '90 days';


-- ─────────────────────────────────────────────────────────────────────
-- Block 7 — DELETE
-- Same warning as UPDATE. Preview with SELECT first.
-- Prefer soft-delete (a `deleted_at` timestamp) over hard-delete
-- for anything a user or auditor might need to see later.
-- ─────────────────────────────────────────────────────────────────────

-- Preview:
SELECT COUNT(*)
FROM support_tickets
WHERE status = 'closed'
  AND resolved_date < CURRENT_DATE - INTERVAL '365 days';

-- Apply:
DELETE FROM support_tickets
WHERE status = 'closed'
  AND resolved_date < CURRENT_DATE - INTERVAL '365 days';


-- ─────────────────────────────────────────────────────────────────────
-- Block 8 — RETURNING (Postgres)
-- Get the just-inserted or just-updated rows back in the same round
-- trip. Useful for capturing generated keys or logging what changed.
-- ─────────────────────────────────────────────────────────────────────
INSERT INTO accounts (company_name, industry, signup_date, region, status)
VALUES ('Fresh Inc.', 'Retail', CURRENT_DATE, 'APAC', 'trial')
RETURNING account_id, company_name;


-- ─────────────────────────────────────────────────────────────────────
-- Block 9 — Constraints — the compile-time contract
-- Constraints move validation from application code into the schema.
-- Cheaper (DB enforces it in C), safer (multiple apps can't drift),
-- and self-documenting.
-- ─────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS orders (
    order_id      SERIAL       PRIMARY KEY,
    account_id    INTEGER      NOT NULL,
    order_date    DATE         NOT NULL DEFAULT CURRENT_DATE,
    amount        NUMERIC(10,2) NOT NULL,
    status        TEXT         NOT NULL,

    CONSTRAINT fk_orders_account
        FOREIGN KEY (account_id) REFERENCES accounts(account_id)
        ON DELETE RESTRICT,           -- prevent deleting an account with orders

    CONSTRAINT chk_orders_amount_positive
        CHECK (amount > 0),

    CONSTRAINT chk_orders_status
        CHECK (status IN ('draft', 'placed', 'shipped', 'delivered', 'cancelled'))
);

-- Uniqueness across multiple columns:
ALTER TABLE orders
    ADD CONSTRAINT uq_orders_account_date UNIQUE (account_id, order_date);


-- ─────────────────────────────────────────────────────────────────────
-- Block 10 — Transactions
-- All-or-nothing. Wrap related mutations in BEGIN ... COMMIT so
-- a failure rolls the whole set back. ACID essentials in section 4.9.
-- ─────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO accounts (company_name, industry, signup_date, region, status)
VALUES ('Transactional Corp', 'SaaS', CURRENT_DATE, 'Europe', 'trial');

INSERT INTO users (account_id, full_name, role, signup_date, is_active)
VALUES (
    (SELECT account_id FROM accounts WHERE company_name = 'Transactional Corp'),
    'First Admin', 'admin', CURRENT_DATE, TRUE
);

-- If anything above raised, we'd ROLLBACK. Otherwise:
COMMIT;

-- =====================================================================
-- End of fundamentals/06_dml_and_constraints.sql
-- =====================================================================
