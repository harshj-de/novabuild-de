-- =====================================================================
-- Module 04 — SQL · Setup · Schema DDL
--
-- Ten-table SaaS operational schema based on the SAAS_DataSet notebook.
-- Column names reflect the actual queries in the notebook (which use the
-- generator-produced schema — the CREATE TABLE cells in the notebook
-- referenced column names that differ from the ones the queries assume).
--
-- Target engine: PostgreSQL 15+.
-- Tested against: PostgreSQL 15, PostgreSQL 16.
--
-- Order matters — FK-dependent tables come after their parents.
-- Wrap the whole file in a transaction so a partial failure rolls back
-- cleanly.
-- =====================================================================

BEGIN;

-- Drop existing objects so the file is safe to re-run during development.
-- CASCADE tears down dependent objects; safe here because we own the schema.
DROP TABLE IF EXISTS support_tickets CASCADE;
DROP TABLE IF EXISTS deals CASCADE;
DROP TABLE IF EXISTS sales_reps CASCADE;
DROP TABLE IF EXISTS feature_usage CASCADE;
DROP TABLE IF EXISTS features CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS invoices CASCADE;
DROP TABLE IF EXISTS subscriptions CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS plans CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;


-- ---------------------------------------------------------------------
-- accounts — one row per customer company
-- ---------------------------------------------------------------------
CREATE TABLE accounts (
    account_id      SERIAL       PRIMARY KEY,
    company_name    TEXT         NOT NULL,
    industry        TEXT         NOT NULL,
    signup_date     DATE         NOT NULL,
    region          TEXT         NOT NULL,
    -- 'active' | 'churned' | 'trial' — drives churn analytics.
    status          TEXT         NOT NULL DEFAULT 'active'
                                 CHECK (status IN ('active', 'churned', 'trial'))
);

CREATE INDEX ix_accounts_industry     ON accounts(industry);
CREATE INDEX ix_accounts_signup_date  ON accounts(signup_date);
CREATE INDEX ix_accounts_status       ON accounts(status);


-- ---------------------------------------------------------------------
-- plans — the tiered pricing catalogue
-- ---------------------------------------------------------------------
CREATE TABLE plans (
    plan_id         SERIAL       PRIMARY KEY,
    plan_name       TEXT         NOT NULL UNIQUE,      -- 'Starter', 'Growth', 'Enterprise'
    monthly_price   NUMERIC(10,2) NOT NULL CHECK (monthly_price >= 0)
);


-- ---------------------------------------------------------------------
-- users — one row per named human at an account
-- ---------------------------------------------------------------------
CREATE TABLE users (
    user_id         SERIAL       PRIMARY KEY,
    account_id      INTEGER      NOT NULL REFERENCES accounts(account_id),
    full_name       TEXT         NOT NULL,
    role            TEXT         NOT NULL,             -- 'admin', 'user', 'viewer'
    signup_date     DATE         NOT NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE INDEX ix_users_account_id ON users(account_id);
CREATE INDEX ix_users_is_active  ON users(is_active);


-- ---------------------------------------------------------------------
-- subscriptions — SCD-friendly view of which plan an account is on and when
-- ---------------------------------------------------------------------
CREATE TABLE subscriptions (
    subscription_id SERIAL       PRIMARY KEY,
    account_id      INTEGER      NOT NULL REFERENCES accounts(account_id),
    plan_id         INTEGER      NOT NULL REFERENCES plans(plan_id),
    start_date      DATE         NOT NULL,
    end_date        DATE,                              -- NULL means still active
    status          TEXT         NOT NULL              -- 'active', 'cancelled', 'upgraded', 'downgraded'
);

CREATE INDEX ix_subscriptions_account_id ON subscriptions(account_id);
CREATE INDEX ix_subscriptions_plan_id    ON subscriptions(plan_id);
CREATE INDEX ix_subscriptions_start_date ON subscriptions(start_date);


-- ---------------------------------------------------------------------
-- invoices — what was billed to whom, when
-- ---------------------------------------------------------------------
CREATE TABLE invoices (
    invoice_id      SERIAL       PRIMARY KEY,
    account_id      INTEGER      NOT NULL REFERENCES accounts(account_id),
    amount          NUMERIC(10,2) NOT NULL CHECK (amount >= 0),
    invoice_date    DATE         NOT NULL,
    status          TEXT         NOT NULL              -- 'paid', 'pending', 'overdue'
);

CREATE INDEX ix_invoices_account_id  ON invoices(account_id);
CREATE INDEX ix_invoices_invoice_date ON invoices(invoice_date);


-- ---------------------------------------------------------------------
-- payments — money actually received against invoices
-- Note: amount_paid may differ from invoices.amount (partial payments,
-- prepayments), which is why we keep them separate.
-- ---------------------------------------------------------------------
CREATE TABLE payments (
    payment_id      SERIAL       PRIMARY KEY,
    invoice_id      INTEGER      NOT NULL REFERENCES invoices(invoice_id),
    amount_paid     NUMERIC(10,2) NOT NULL CHECK (amount_paid >= 0),
    payment_date    DATE         NOT NULL,
    status          TEXT         NOT NULL              -- 'success', 'failed', 'refunded'
);

CREATE INDEX ix_payments_invoice_id   ON payments(invoice_id);
CREATE INDEX ix_payments_payment_date ON payments(payment_date);


-- ---------------------------------------------------------------------
-- features — the app capabilities being metered
-- ---------------------------------------------------------------------
CREATE TABLE features (
    feature_id      SERIAL       PRIMARY KEY,
    feature_name    TEXT         NOT NULL UNIQUE
);


-- ---------------------------------------------------------------------
-- feature_usage — event log; one row per (user, feature, day)
-- ---------------------------------------------------------------------
CREATE TABLE feature_usage (
    usage_id        SERIAL       PRIMARY KEY,
    user_id         INTEGER      NOT NULL REFERENCES users(user_id),
    feature_id      INTEGER      NOT NULL REFERENCES features(feature_id),
    usage_date      DATE         NOT NULL,
    usage_count     INTEGER      NOT NULL DEFAULT 1 CHECK (usage_count >= 0)
);

CREATE INDEX ix_feature_usage_user_id    ON feature_usage(user_id);
CREATE INDEX ix_feature_usage_feature_id ON feature_usage(feature_id);
CREATE INDEX ix_feature_usage_usage_date ON feature_usage(usage_date);


-- ---------------------------------------------------------------------
-- sales_reps — internal sellers
-- ---------------------------------------------------------------------
CREATE TABLE sales_reps (
    rep_id          SERIAL       PRIMARY KEY,
    full_name       TEXT         NOT NULL,
    region          TEXT         NOT NULL
);


-- ---------------------------------------------------------------------
-- deals — sales pipeline; account may have multiple deals over time
-- ---------------------------------------------------------------------
CREATE TABLE deals (
    deal_id         SERIAL       PRIMARY KEY,
    account_id      INTEGER      NOT NULL REFERENCES accounts(account_id),
    rep_id          INTEGER      REFERENCES sales_reps(rep_id),
    deal_value      NUMERIC(12,2) NOT NULL CHECK (deal_value >= 0),
    stage           TEXT         NOT NULL,             -- 'prospecting', 'qualified', 'proposal', 'won', 'lost'
    close_date      DATE
);

CREATE INDEX ix_deals_account_id ON deals(account_id);
CREATE INDEX ix_deals_stage      ON deals(stage);


-- ---------------------------------------------------------------------
-- support_tickets — CX metrics; resolution SLA computations
-- ---------------------------------------------------------------------
CREATE TABLE support_tickets (
    ticket_id       SERIAL       PRIMARY KEY,
    account_id      INTEGER      NOT NULL REFERENCES accounts(account_id),
    issue_type      TEXT         NOT NULL,             -- 'bug', 'billing', 'onboarding', 'other'
    status          TEXT         NOT NULL,             -- 'open', 'in_progress', 'resolved', 'closed'
    created_date    TIMESTAMP    NOT NULL,
    resolved_date   TIMESTAMP                          -- NULL when unresolved
);

CREATE INDEX ix_support_tickets_account_id ON support_tickets(account_id);
CREATE INDEX ix_support_tickets_status     ON support_tickets(status);


COMMIT;

-- =====================================================================
-- End of setup/00_create_schema.sql
-- Next: 01_seed_data.sql, or run generate_saas_data.py to load a
-- realistic 6-month dataset (~100 accounts, ~3000 users, ~30k events).
-- =====================================================================
