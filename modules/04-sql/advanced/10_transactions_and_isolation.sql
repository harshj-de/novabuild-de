-- =====================================================================
-- Module 04 — SQL · Advanced · Section 4.10
-- ACID, Transactions, Isolation Levels
--
-- The theory Data Engineers must own — every job interview will
-- probe this. This section covers what the letters mean, how to
-- write correct transactions, and what happens at each isolation
-- level (with concrete examples).
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────
-- Block 1 — ACID recap
--
--   Atomicity   — a transaction runs all-or-nothing. Partial results
--                 never persist. Enforced by the write-ahead log (WAL).
--   Consistency — the DB moves from one valid state to another; all
--                 constraints hold at commit time. Enforced by the DB.
--   Isolation   — concurrent transactions don't corrupt each other's
--                 view. Isolation LEVEL controls the trade-off.
--   Durability  — once committed, changes survive a crash. Enforced
--                 by fsync + WAL replay on restart.
--
-- ACID is what makes a database a database (vs a filesystem or cache).
-- ─────────────────────────────────────────────────────────────────────


-- ─────────────────────────────────────────────────────────────────────
-- Block 2 — Basic transaction: BEGIN, COMMIT, ROLLBACK
-- ─────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO accounts (company_name, industry, signup_date, region, status)
VALUES ('Txn Demo Inc.', 'SaaS', CURRENT_DATE, 'APAC', 'trial');

-- Save your work:
COMMIT;

-- Or, undo everything since BEGIN:
-- ROLLBACK;


-- ─────────────────────────────────────────────────────────────────────
-- Block 3 — SAVEPOINT — partial rollback
-- Mark a checkpoint mid-transaction; roll back to it without losing
-- earlier work. Useful in long ETL jobs where certain steps are
-- allowed to fail.
-- ─────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO accounts (company_name, industry, signup_date, region, status)
VALUES ('Definitely Good Inc.', 'SaaS', CURRENT_DATE, 'APAC', 'trial');

SAVEPOINT before_risky_step;

INSERT INTO accounts (company_name, industry, signup_date, region, status)
VALUES ('Maybe Bad Inc.', 'SaaS', CURRENT_DATE, 'APAC', 'trial');

-- Decided that INSERT was wrong; undo just it, keep the first.
ROLLBACK TO SAVEPOINT before_risky_step;

COMMIT;
-- Only "Definitely Good Inc." persists.


-- ─────────────────────────────────────────────────────────────────────
-- Block 4 — Isolation levels
--
-- Four levels, in increasing strictness:
--
--   READ UNCOMMITTED — dirty reads allowed (Postgres treats this as READ COMMITTED)
--   READ COMMITTED   — Postgres default. Each STATEMENT sees a fresh snapshot.
--                      No dirty reads. Non-repeatable reads and phantom reads
--                      still possible.
--   REPEATABLE READ  — snapshot at TRANSACTION start. Reads inside the txn
--                      are stable. Postgres uses snapshot isolation which
--                      also prevents phantoms.
--   SERIALIZABLE     — full serializability. Uses predicate locks; may abort
--                      one transaction to preserve correctness.
--
-- Set for a session:
--   SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL REPEATABLE READ;
-- Or per transaction:
--   BEGIN;
--   SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
--   ...
-- ─────────────────────────────────────────────────────────────────────


-- ─────────────────────────────────────────────────────────────────────
-- Block 5 — Anomalies each level prevents
--
--   Dirty read      — read data that was never committed
--   Non-repeatable  — same query returns different values within one txn
--   Phantom read    — same range query returns different sets of rows
--   Serialization   — result of concurrent txns is not equivalent to
--     anomaly         some serial ordering
--
--   Level              Dirty  Non-rep  Phantom  Ser
--   READ COMMITTED     no     yes      yes      yes
--   REPEATABLE READ    no     no       no*      yes
--   SERIALIZABLE       no     no       no       no
--
--   *Postgres prevents phantoms at REPEATABLE READ via snapshot isolation,
--    which is stricter than the SQL standard requires.
-- ─────────────────────────────────────────────────────────────────────


-- ─────────────────────────────────────────────────────────────────────
-- Block 6 — When to reach for SERIALIZABLE
-- The right isolation for anything involving cross-row invariants:
--   * Bank transfers (sum across two rows must stay balanced)
--   * Rate-limiting (count of recent events must not exceed a threshold)
--   * Inventory reservation (must not oversell a product)
--
-- The cost: some transactions may fail with a serialization error and
-- must be retried. Your app must handle this.
-- ─────────────────────────────────────────────────────────────────────
BEGIN ISOLATION LEVEL SERIALIZABLE;

-- Transfer $100 from account A to account B.
UPDATE accounts SET status = 'active' WHERE company_name = 'Definitely Good Inc.';
UPDATE accounts SET status = 'active' WHERE company_name = 'Txn Demo Inc.';

-- If a concurrent txn violated serializability, this COMMIT will fail
-- with SQLSTATE 40001 and the app must retry.
COMMIT;


-- ─────────────────────────────────────────────────────────────────────
-- Block 7 — SELECT ... FOR UPDATE — pessimistic locking
-- Read a row AND lock it for update. Any other txn trying to read it
-- FOR UPDATE will block until this one commits or rolls back.
-- ─────────────────────────────────────────────────────────────────────
BEGIN;

SELECT *
FROM accounts
WHERE account_id = 1
FOR UPDATE;

-- Now nobody else can modify this row until we COMMIT.
UPDATE accounts
SET status = 'churned'
WHERE account_id = 1;

COMMIT;


-- ─────────────────────────────────────────────────────────────────────
-- Block 8 — Deadlocks
-- Two transactions each holding a lock the other needs. Postgres
-- detects deadlocks and kills one with SQLSTATE 40P01.
--
-- The rule to avoid them: always acquire locks in the same order
-- across all transactions. If txn A locks row 1 then row 2, txn B
-- should also lock row 1 then row 2 — never the reverse.
-- ─────────────────────────────────────────────────────────────────────

-- =====================================================================
-- End of advanced/10_transactions_and_isolation.sql
-- =====================================================================
