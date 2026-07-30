"""
Module 04 · Setup · generate_saas_data.py

Populates the 10-table SaaS schema with realistic, referentially-consistent
seed data. Every query in fundamentals/, advanced/, and portfolio_queries/
is designed to run against this dataset.

Approximate volumes generated:
    accounts         :    100 companies
    plans            :      3 tiers (Starter, Growth, Enterprise)
    users            :  ~1000 (10 per account on average)
    subscriptions    :  ~150  (each account has 1-2 lifetime subs)
    invoices         :  ~800  (about 8 per account)
    payments         :  ~750  (small fraction fail / are outstanding)
    features         :      8 fixed feature names
    feature_usage    : ~10,000 (events across users x features x days)
    sales_reps       :     10
    deals            :   ~120
    support_tickets  :   ~300

Usage:
    export DATABASE_URL=postgresql://user:pass@localhost:5432/saas_demo
    python setup/generate_saas_data.py

    # Or explicitly:
    python setup/generate_saas_data.py --db postgresql://... --seed 42

Requires:
    psycopg[binary] (from requirements.txt in the module root)

Notes:
    * Uses `psycopg` v3, which is the current recommended driver.
    * All inserts wrap in a single transaction. Failure rolls back cleanly.
    * Deterministic when `--seed` is passed (default: 42) so query outputs
      are reproducible across machines.
"""

from __future__ import annotations

import argparse
import os
import random
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Sequence

try:
    import psycopg
except ImportError as exc:
    raise SystemExit(
        "psycopg is required. Install it with:\n"
        "    pip install 'psycopg[binary]'"
    ) from exc


# ─── Constants ─────────────────────────────────────────────────────────

INDUSTRIES = [
    "SaaS", "Fintech", "Healthcare", "Retail", "Manufacturing",
    "Education", "Insurance", "Logistics", "Media", "Real Estate",
]
REGIONS = ["North America", "Europe", "APAC", "LATAM", "MEA"]
ROLES = ["admin", "user", "viewer"]
FEATURE_NAMES = [
    "Dashboards", "Reports", "API Access", "Integrations",
    "Advanced Analytics", "Custom Alerts", "Data Export", "User Management",
]
SUB_STATUSES = ["active", "cancelled", "upgraded", "downgraded"]
INVOICE_STATUSES = ["paid", "pending", "overdue"]
PAYMENT_STATUSES = ["success", "success", "success", "failed", "refunded"]
DEAL_STAGES = ["prospecting", "qualified", "proposal", "won", "lost"]
TICKET_TYPES = ["bug", "billing", "onboarding", "feature_request", "other"]
TICKET_STATUSES = ["open", "in_progress", "resolved", "closed"]


# ─── Helpers ───────────────────────────────────────────────────────────


def random_date(rng: random.Random, start: date, end: date) -> date:
    """Uniformly random date in [start, end]."""
    delta = (end - start).days
    return start + timedelta(days=rng.randint(0, delta))


def random_datetime_after(rng: random.Random, dt: date) -> datetime:
    """Random datetime on the given date, business hours."""
    return datetime.combine(dt, datetime.min.time()) + timedelta(
        hours=rng.randint(9, 17),
        minutes=rng.randint(0, 59),
    )


def maybe(rng: random.Random, prob: float) -> bool:
    return rng.random() < prob


# ─── Generators (return list-of-tuples ready for executemany) ─────────


def gen_accounts(rng: random.Random, n: int = 100) -> list[tuple]:
    """Return n rows for the accounts table."""
    start_of_window = date(2024, 1, 1)
    end_of_window = date(2024, 12, 1)
    rows = []
    for i in range(1, n + 1):
        rows.append(
            (
                f"Acme {i:03d} Inc.",
                rng.choice(INDUSTRIES),
                random_date(rng, start_of_window, end_of_window),
                rng.choice(REGIONS),
                rng.choices(
                    ["active", "churned", "trial"], weights=[70, 20, 10]
                )[0],
            )
        )
    return rows


def gen_plans() -> list[tuple]:
    return [
        ("Starter", Decimal("49.00")),
        ("Growth", Decimal("199.00")),
        ("Enterprise", Decimal("999.00")),
    ]


def gen_users(rng: random.Random, account_ids: Sequence[int]) -> list[tuple]:
    """~10 users per account, distributed roles."""
    first_names = ["Alex", "Priya", "Sam", "Jordan", "Taylor", "Casey",
                   "Morgan", "Riley", "Jamie", "Drew", "Quinn", "Skyler"]
    last_names = ["Chen", "Patel", "Kim", "Singh", "Garcia", "Nguyen",
                  "Kumar", "Silva", "Ali", "Smith", "Johnson", "Lee"]
    rows = []
    for acc_id in account_ids:
        for _ in range(rng.randint(3, 15)):
            rows.append(
                (
                    acc_id,
                    f"{rng.choice(first_names)} {rng.choice(last_names)}",
                    rng.choices(ROLES, weights=[15, 70, 15])[0],
                    random_date(rng, date(2024, 1, 1), date(2024, 12, 1)),
                    maybe(rng, 0.85),  # 85% still active
                )
            )
    return rows


def gen_subscriptions(
    rng: random.Random,
    account_ids: Sequence[int],
    plan_ids: Sequence[int],
) -> list[tuple]:
    """1-2 subscriptions per account, with occasional plan changes."""
    rows = []
    for acc_id in account_ids:
        # First subscription — starts at signup.
        start = random_date(rng, date(2024, 1, 1), date(2024, 6, 1))
        plan = rng.choice(plan_ids)
        # ~30% of accounts change plans mid-year.
        if maybe(rng, 0.3):
            change_date = start + timedelta(days=rng.randint(60, 180))
            new_plan = rng.choice([p for p in plan_ids if p != plan])
            rows.append((acc_id, plan, start, change_date,
                         rng.choice(["upgraded", "downgraded"])))
            rows.append((acc_id, new_plan, change_date, None, "active"))
        else:
            # Some churn; rest stay active.
            if maybe(rng, 0.2):
                end = start + timedelta(days=rng.randint(30, 300))
                rows.append((acc_id, plan, start, end, "cancelled"))
            else:
                rows.append((acc_id, plan, start, None, "active"))
    return rows


def gen_invoices(
    rng: random.Random,
    account_ids: Sequence[int],
) -> list[tuple]:
    """~8 invoices per account, monthly cadence."""
    rows = []
    for acc_id in account_ids:
        first = random_date(rng, date(2024, 1, 1), date(2024, 3, 1))
        n_months = rng.randint(4, 10)
        for m in range(n_months):
            inv_date = first + timedelta(days=30 * m)
            amount = Decimal(rng.choice([49, 199, 199, 199, 999])) \
                     + Decimal(rng.randint(0, 50))
            status = rng.choices(
                INVOICE_STATUSES, weights=[80, 15, 5]
            )[0]
            rows.append((acc_id, amount, inv_date, status))
    return rows


def gen_payments(
    rng: random.Random,
    invoices: list[tuple],
    invoice_ids: Sequence[int],
) -> list[tuple]:
    """One payment per PAID invoice (most cases)."""
    rows = []
    for inv_id, (acc_id, amount, inv_date, status) in zip(invoice_ids, invoices):
        if status == "paid" or (status == "pending" and maybe(rng, 0.3)):
            pay_date = inv_date + timedelta(days=rng.randint(0, 15))
            pay_amount = amount
            if maybe(rng, 0.05):
                pay_amount = amount - Decimal(rng.randint(1, 20))
            rows.append(
                (inv_id, pay_amount, pay_date, rng.choice(PAYMENT_STATUSES))
            )
    return rows


def gen_features() -> list[tuple]:
    return [(name,) for name in FEATURE_NAMES]


def gen_feature_usage(
    rng: random.Random,
    user_ids: Sequence[int],
    feature_ids: Sequence[int],
) -> list[tuple]:
    """~10 events per user across a small subset of features."""
    rows = []
    for user_id in user_ids:
        num_features = rng.randint(2, 5)
        used_features = rng.sample(list(feature_ids), num_features)
        for fid in used_features:
            for _ in range(rng.randint(1, 5)):
                rows.append(
                    (
                        user_id,
                        fid,
                        random_date(rng, date(2024, 1, 1), date(2024, 12, 1)),
                        rng.randint(1, 20),
                    )
                )
    return rows


def gen_sales_reps(rng: random.Random, n: int = 10) -> list[tuple]:
    return [
        (f"Rep {i:02d}", rng.choice(REGIONS)) for i in range(1, n + 1)
    ]


def gen_deals(
    rng: random.Random,
    account_ids: Sequence[int],
    rep_ids: Sequence[int],
) -> list[tuple]:
    """~1.2 deals per account."""
    rows = []
    for acc_id in account_ids:
        for _ in range(rng.randint(0, 3)):
            stage = rng.choice(DEAL_STAGES)
            close_date = (
                random_date(rng, date(2024, 1, 1), date(2024, 12, 15))
                if stage in ("won", "lost") else None
            )
            rows.append(
                (
                    acc_id,
                    rng.choice(rep_ids),
                    Decimal(rng.randint(1000, 100_000)),
                    stage,
                    close_date,
                )
            )
    return rows


def gen_support_tickets(
    rng: random.Random,
    account_ids: Sequence[int],
) -> list[tuple]:
    """~3 tickets per account, some unresolved."""
    rows = []
    for acc_id in account_ids:
        for _ in range(rng.randint(0, 6)):
            created = random_datetime_after(
                rng, random_date(rng, date(2024, 1, 1), date(2024, 11, 30))
            )
            status = rng.choice(TICKET_STATUSES)
            resolved = None
            if status in ("resolved", "closed"):
                resolved = created + timedelta(
                    hours=rng.randint(1, 168)  # 1 hour to 1 week
                )
            rows.append(
                (
                    acc_id,
                    rng.choice(TICKET_TYPES),
                    status,
                    created,
                    resolved,
                )
            )
    return rows


# ─── Main ──────────────────────────────────────────────────────────────


def load(conn, rng: random.Random) -> None:
    """Populate every table inside a single transaction."""
    with conn.cursor() as cur:
        # --- accounts ---
        rows = gen_accounts(rng)
        cur.executemany(
            "INSERT INTO accounts (company_name, industry, signup_date, "
            "region, status) VALUES (%s, %s, %s, %s, %s)",
            rows,
        )
        cur.execute("SELECT account_id FROM accounts ORDER BY account_id")
        account_ids = [r[0] for r in cur.fetchall()]
        print(f"[load] accounts: {len(account_ids)}")

        # --- plans ---
        cur.executemany(
            "INSERT INTO plans (plan_name, monthly_price) VALUES (%s, %s)",
            gen_plans(),
        )
        cur.execute("SELECT plan_id FROM plans ORDER BY plan_id")
        plan_ids = [r[0] for r in cur.fetchall()]

        # --- users ---
        rows = gen_users(rng, account_ids)
        cur.executemany(
            "INSERT INTO users (account_id, full_name, role, "
            "signup_date, is_active) VALUES (%s, %s, %s, %s, %s)",
            rows,
        )
        cur.execute("SELECT user_id FROM users ORDER BY user_id")
        user_ids = [r[0] for r in cur.fetchall()]
        print(f"[load] users: {len(user_ids)}")

        # --- subscriptions ---
        rows = gen_subscriptions(rng, account_ids, plan_ids)
        cur.executemany(
            "INSERT INTO subscriptions (account_id, plan_id, start_date, "
            "end_date, status) VALUES (%s, %s, %s, %s, %s)",
            rows,
        )
        print(f"[load] subscriptions: {len(rows)}")

        # --- invoices ---
        invoice_rows = gen_invoices(rng, account_ids)
        cur.executemany(
            "INSERT INTO invoices (account_id, amount, invoice_date, status) "
            "VALUES (%s, %s, %s, %s)",
            invoice_rows,
        )
        cur.execute("SELECT invoice_id FROM invoices ORDER BY invoice_id")
        invoice_ids = [r[0] for r in cur.fetchall()]
        print(f"[load] invoices: {len(invoice_ids)}")

        # --- payments ---
        rows = gen_payments(rng, invoice_rows, invoice_ids)
        cur.executemany(
            "INSERT INTO payments (invoice_id, amount_paid, payment_date, "
            "status) VALUES (%s, %s, %s, %s)",
            rows,
        )
        print(f"[load] payments: {len(rows)}")

        # --- features ---
        cur.executemany(
            "INSERT INTO features (feature_name) VALUES (%s)", gen_features()
        )
        cur.execute("SELECT feature_id FROM features ORDER BY feature_id")
        feature_ids = [r[0] for r in cur.fetchall()]

        # --- feature_usage ---
        rows = gen_feature_usage(rng, user_ids, feature_ids)
        cur.executemany(
            "INSERT INTO feature_usage (user_id, feature_id, usage_date, "
            "usage_count) VALUES (%s, %s, %s, %s)",
            rows,
        )
        print(f"[load] feature_usage: {len(rows)}")

        # --- sales_reps ---
        cur.executemany(
            "INSERT INTO sales_reps (full_name, region) VALUES (%s, %s)",
            gen_sales_reps(rng),
        )
        cur.execute("SELECT rep_id FROM sales_reps ORDER BY rep_id")
        rep_ids = [r[0] for r in cur.fetchall()]

        # --- deals ---
        rows = gen_deals(rng, account_ids, rep_ids)
        cur.executemany(
            "INSERT INTO deals (account_id, rep_id, deal_value, stage, "
            "close_date) VALUES (%s, %s, %s, %s, %s)",
            rows,
        )
        print(f"[load] deals: {len(rows)}")

        # --- support_tickets ---
        rows = gen_support_tickets(rng, account_ids)
        cur.executemany(
            "INSERT INTO support_tickets (account_id, issue_type, status, "
            "created_date, resolved_date) VALUES (%s, %s, %s, %s, %s)",
            rows,
        )
        print(f"[load] support_tickets: {len(rows)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        default=os.environ.get("DATABASE_URL"),
        help="Postgres connection string (or set DATABASE_URL env var)",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed (default: 42)"
    )
    args = parser.parse_args()

    if not args.db:
        raise SystemExit(
            "No DB connection given. Pass --db or set DATABASE_URL."
        )

    rng = random.Random(args.seed)

    print(f"[generate_saas_data] connecting to {args.db.split('@')[-1]}...")
    with psycopg.connect(args.db) as conn:
        load(conn, rng)
        conn.commit()
    print("[generate_saas_data] done — all tables populated.")


if __name__ == "__main__":
    main()
