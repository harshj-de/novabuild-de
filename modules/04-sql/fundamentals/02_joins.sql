-- =====================================================================
-- Module 04 — SQL · Fundamentals · Section 4.2
-- Joins — INNER, LEFT, RIGHT, FULL OUTER, CROSS, SELF
--
-- The single most-tested SQL concept in interviews and the source of
-- most subtle bugs in production queries. Understand what each join
-- does to row counts.
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────
-- Block 1 — INNER JOIN
-- Returns only rows where the join key matches in BOTH tables.
-- Rows with no match on either side are dropped silently — this is
-- where "missing data" bugs usually originate.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    a.company_name,
    i.invoice_id,
    i.amount,
    i.invoice_date
FROM accounts a
INNER JOIN invoices i
    ON a.account_id = i.account_id
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────
-- Block 2 — LEFT JOIN
-- Every row from the left (accounts) is kept, matched with data from
-- the right (invoices) if present, NULL otherwise. Use LEFT JOIN
-- when you want to see "all accounts, WITH their invoices IF any."
-- ─────────────────────────────────────────────────────────────────────
SELECT
    a.account_id,
    a.company_name,
    i.invoice_id,
    i.amount
FROM accounts a
LEFT JOIN invoices i
    ON a.account_id = i.account_id
ORDER BY a.account_id
LIMIT 15;


-- ─────────────────────────────────────────────────────────────────────
-- Block 3 — LEFT JOIN + IS NULL — the "anti-join" pattern
-- Rows on the LEFT that have NO match on the right. Answers
-- questions like "which accounts have never been invoiced?"
-- ─────────────────────────────────────────────────────────────────────
SELECT
    a.account_id,
    a.company_name
FROM accounts a
LEFT JOIN invoices i
    ON a.account_id = i.account_id
WHERE i.invoice_id IS NULL;


-- ─────────────────────────────────────────────────────────────────────
-- Block 4 — Multi-table join
-- accounts → invoices → payments — following the customer money trail.
-- Every additional join potentially multiplies rows on 1:many joins,
-- so aggregate carefully afterwards.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    a.company_name,
    i.invoice_id,
    p.amount_paid,
    p.payment_date
FROM accounts a
INNER JOIN invoices i
    ON a.account_id = i.account_id
INNER JOIN payments p
    ON i.invoice_id = p.invoice_id
WHERE a.industry = 'Fintech'
ORDER BY p.payment_date DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────
-- Block 5 — FULL OUTER JOIN
-- Every row from BOTH sides. Match where possible, NULL where not.
-- Useful for reconciliation (e.g. "which invoices lack payments AND
-- which payments have no invoice"). Slow — Postgres materialises both.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    i.invoice_id,
    i.amount        AS invoice_amount,
    p.payment_id,
    p.amount_paid
FROM invoices i
FULL OUTER JOIN payments p
    ON i.invoice_id = p.invoice_id
WHERE i.invoice_id IS NULL
   OR p.payment_id IS NULL
LIMIT 20;


-- ─────────────────────────────────────────────────────────────────────
-- Block 6 — Self-join
-- A table joined to itself. Common for hierarchical data (manager →
-- employee), or in the SaaS context, comparing two subscriptions of
-- the same account (upgrade path).
-- ─────────────────────────────────────────────────────────────────────
SELECT
    s1.account_id,
    p1.plan_name AS from_plan,
    p2.plan_name AS to_plan,
    s1.end_date  AS switched_on
FROM subscriptions s1
JOIN subscriptions s2
    ON s1.account_id = s2.account_id
   AND s2.start_date = s1.end_date  -- s2 begins when s1 ends
JOIN plans p1 ON s1.plan_id = p1.plan_id
JOIN plans p2 ON s2.plan_id = p2.plan_id
WHERE s1.status IN ('upgraded', 'downgraded')
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────
-- Block 7 — CROSS JOIN
-- Cartesian product of both tables — every left row paired with
-- every right row. Rarely intended; often the result of an accidental
-- missing ON clause. Useful for generating calendar tables or filling
-- in missing (account × month) combinations.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    a.company_name,
    p.plan_name,
    p.monthly_price
FROM accounts a
CROSS JOIN plans p
LIMIT 15;


-- ─────────────────────────────────────────────────────────────────────
-- Block 8 — USING vs ON
-- If the join column has the same name in both tables, `USING` is
-- terser. It also collapses the two columns into one in the result.
-- Prefer ON in production — it's explicit and survives column renames.
-- ─────────────────────────────────────────────────────────────────────
SELECT
    account_id,
    invoice_id,
    amount
FROM accounts
JOIN invoices USING (account_id)
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────
-- Block 9 — The row-multiplication trap
-- A 1:many join multiplies rows on the LEFT for every match on the
-- RIGHT. When aggregating afterwards, an unwary SUM will double-count.
-- Rule: always check row counts before AND after every join.
-- ─────────────────────────────────────────────────────────────────────

-- Demonstration: each account has multiple invoices. Sum-of-amount
-- per account is fine. But joining payments too would double-count.

SELECT COUNT(*) AS row_count
FROM accounts a
JOIN invoices i ON a.account_id = i.account_id;

-- vs.
SELECT COUNT(*) AS row_count
FROM accounts a
JOIN invoices i ON a.account_id = i.account_id
JOIN payments p ON i.invoice_id = p.invoice_id;
-- Numbers will differ — sanity-check before aggregating.

-- =====================================================================
-- End of fundamentals/02_joins.sql
-- =====================================================================
