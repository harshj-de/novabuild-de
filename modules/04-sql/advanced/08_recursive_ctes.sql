-- =====================================================================
-- Module 04 — SQL · Advanced · Section 4.8
-- Recursive CTEs
--
-- The SQL feature for problems that are naturally iterative:
--   * Hierarchy traversal (org charts, folder trees, category taxonomies)
--   * Sequence generation (calendars, gap-fills)
--   * Graph traversal (referral chains, dependency resolution)
--
-- Structure of every recursive CTE:
--
--   WITH RECURSIVE name AS (
--       -- ANCHOR (base case): non-recursive query, runs once
--       SELECT ... FROM ... WHERE ...
--     UNION ALL
--       -- RECURSIVE STEP: references `name` — the previous iteration's rows
--       SELECT ... FROM name JOIN ... WHERE (termination condition)
--   )
--   SELECT * FROM name;
--
-- The recursion terminates when the recursive step produces zero rows.
-- Without a termination condition it will loop forever — most engines
-- have a max recursion depth guard, but don't rely on it.
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────
-- Block 1 — Simplest example: generate a sequence of dates
-- Not the most useful (generate_series exists in Postgres), but the
-- clearest illustration of the mechanic.
-- ─────────────────────────────────────────────────────────────────────
WITH RECURSIVE dates AS (
    -- Anchor
    SELECT DATE '2024-01-01' AS d
  UNION ALL
    -- Recursive step
    SELECT d + INTERVAL '1 day'
    FROM dates
    WHERE d < DATE '2024-01-10'
)
SELECT d FROM dates;


-- ─────────────────────────────────────────────────────────────────────
-- Block 2 — Generate a monthly calendar
-- Useful for LEFT-JOINing against sparse event data to include
-- months with zero activity.
-- ─────────────────────────────────────────────────────────────────────
WITH RECURSIVE months AS (
    SELECT DATE '2024-01-01' AS month_start
  UNION ALL
    SELECT (month_start + INTERVAL '1 month')::date
    FROM months
    WHERE month_start < DATE '2024-12-01'
)
SELECT
    TO_CHAR(month_start, 'Mon YYYY') AS label,
    month_start
FROM months;


-- ─────────────────────────────────────────────────────────────────────
-- Block 3 — Employee / manager hierarchy (org chart)
-- Classic recursive CTE example. Given a self-referential table
-- (each employee has a manager_id), compute the reporting chain
-- from any employee up to the CEO.
--
-- We'll use a temporary example table for this section.
-- ─────────────────────────────────────────────────────────────────────
CREATE TEMP TABLE employees (
    emp_id     INTEGER PRIMARY KEY,
    emp_name   TEXT NOT NULL,
    manager_id INTEGER REFERENCES employees(emp_id)
);

INSERT INTO employees VALUES
    (1, 'CEO',        NULL),
    (2, 'CTO',        1),
    (3, 'VP Eng',     2),
    (4, 'Eng Mgr',    3),
    (5, 'SR Eng',     4),
    (6, 'Jr Eng',     5);

-- Anchor: start with the leaf employee.
-- Recursive step: follow manager_id up the tree.
WITH RECURSIVE chain AS (
    SELECT
        emp_id,
        emp_name,
        manager_id,
        0 AS depth
    FROM employees
    WHERE emp_id = 6                  -- start from Jr Eng
  UNION ALL
    SELECT
        e.emp_id,
        e.emp_name,
        e.manager_id,
        c.depth + 1
    FROM employees e
    JOIN chain c ON e.emp_id = c.manager_id
)
SELECT depth, emp_id, emp_name FROM chain ORDER BY depth;


-- ─────────────────────────────────────────────────────────────────────
-- Block 4 — Reverse direction: get the subtree under a node
-- Same table, opposite direction. From the CEO, walk down to every
-- descendant. Useful for "everyone reporting into X, directly or
-- indirectly".
-- ─────────────────────────────────────────────────────────────────────
WITH RECURSIVE subtree AS (
    SELECT emp_id, emp_name, manager_id, 0 AS depth
    FROM employees
    WHERE emp_id = 2                  -- start from CTO
  UNION ALL
    SELECT e.emp_id, e.emp_name, e.manager_id, s.depth + 1
    FROM employees e
    JOIN subtree s ON e.manager_id = s.emp_id
)
SELECT depth, emp_id, emp_name
FROM subtree
ORDER BY depth, emp_id;


-- ─────────────────────────────────────────────────────────────────────
-- Block 5 — Guard against infinite recursion
-- Any table with a cycle (A → B → A) will loop forever without a
-- termination guard. Two common patterns:
--   1. Track the path so far; skip when the next node is already in it.
--   2. Cap the depth explicitly.
-- ─────────────────────────────────────────────────────────────────────

-- Depth-cap example.
WITH RECURSIVE bounded AS (
    SELECT emp_id, emp_name, manager_id, 0 AS depth
    FROM employees
    WHERE manager_id IS NULL
  UNION ALL
    SELECT e.emp_id, e.emp_name, e.manager_id, b.depth + 1
    FROM employees e
    JOIN bounded b ON e.manager_id = b.emp_id
    WHERE b.depth < 10                 -- hard cap
)
SELECT * FROM bounded ORDER BY depth;


-- ─────────────────────────────────────────────────────────────────────
-- Block 6 — Practical use — a referral chain
-- Suppose accounts has a `referred_by_account_id` column. Trace how
-- an account was acquired all the way back to the originating account.
-- (Demonstration only — the schema doesn't have this column.)
-- ─────────────────────────────────────────────────────────────────────
-- WITH RECURSIVE referral_chain AS (
--     SELECT account_id, company_name, referred_by_account_id, 0 AS depth
--     FROM accounts
--     WHERE account_id = ?
--   UNION ALL
--     SELECT a.account_id, a.company_name, a.referred_by_account_id, rc.depth + 1
--     FROM accounts a
--     JOIN referral_chain rc ON a.account_id = rc.referred_by_account_id
-- )
-- SELECT * FROM referral_chain;

-- =====================================================================
-- End of advanced/08_recursive_ctes.sql
-- =====================================================================
