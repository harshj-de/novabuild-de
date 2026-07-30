"""
Section 3.11 — Window Operations.

Analytical Pandas at its most powerful. Windows compute per-row values
that depend on nearby rows: rolling averages, running totals, rank
within group, lag/lead comparisons.

Covers:
  * rolling() — window-based aggregation (moving averages)
  * expanding() — cumulative window (running totals from the start)
  * shift() — lag and lead comparisons
  * pct_change() — period-over-period change
  * cumsum / cummax / cumcount — simple cumulative helpers
  * Groupby + rolling — rolling windows within each group
  * rank(method='dense') within a group — leaderboard patterns

Run: `python 11_window_operations.py`
"""

import numpy as np
import pandas as pd


def sample_daily_orders() -> pd.DataFrame:
    dates = pd.date_range(start="2024-01-01", periods=10, freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "customer_id": ["C001", "C002", "C001", "C003", "C002",
                            "C001", "C002", "C003", "C001", "C002"],
            "amount": [4500, 12000, 800, 3200, 15000, 6700, 2400, 5100, 3600, 9200],
        }
    )


def demo_rolling_average() -> None:
    """rolling(window=N) — the classic moving average."""
    print("=" * 60)
    print("rolling() — MOVING AVERAGE")
    print("=" * 60)

    df = sample_daily_orders()
    # 3-day moving average of amount.
    df["rolling_3d_avg"] = df["amount"].rolling(window=3).mean()
    print(df[["date", "amount", "rolling_3d_avg"]])


def demo_expanding_cumulative() -> None:
    """expanding() — cumulative window growing from the start."""
    print("\n" + "=" * 60)
    print("expanding() — RUNNING METRICS FROM THE START")
    print("=" * 60)

    df = sample_daily_orders()
    df["running_total"] = df["amount"].expanding().sum()
    df["running_avg"] = df["amount"].expanding().mean()
    print(df[["date", "amount", "running_total", "running_avg"]].round(2))


def demo_shift_lag_lead() -> None:
    """shift() — compare a row to the previous / next row."""
    print("\n" + "=" * 60)
    print("shift() — LAG AND LEAD")
    print("=" * 60)

    df = sample_daily_orders()
    df["prev_amount"] = df["amount"].shift(1)  # previous row
    df["next_amount"] = df["amount"].shift(-1)  # next row
    df["day_over_day"] = df["amount"] - df["prev_amount"]

    print(df[["date", "amount", "prev_amount", "next_amount", "day_over_day"]])


def demo_pct_change() -> None:
    """pct_change() — period-over-period percentage change."""
    print("\n" + "=" * 60)
    print("pct_change() — PERCENTAGE CHANGE")
    print("=" * 60)

    df = sample_daily_orders()
    df["pct_change"] = (df["amount"].pct_change() * 100).round(1)
    print(df[["date", "amount", "pct_change"]])


def demo_cumulative_helpers() -> None:
    """cumsum, cummax, cummin, cumcount — simple cumulative operations."""
    print("\n" + "=" * 60)
    print("cumsum, cummax, cummin")
    print("=" * 60)

    df = sample_daily_orders()
    df["cumsum"] = df["amount"].cumsum()
    df["running_max"] = df["amount"].cummax()
    df["running_min"] = df["amount"].cummin()
    print(df[["date", "amount", "cumsum", "running_max", "running_min"]])


def demo_groupby_rolling() -> None:
    """rolling within each group — the per-customer moving average pattern."""
    print("\n" + "=" * 60)
    print("GROUPBY + ROLLING")
    print("=" * 60)

    df = sample_daily_orders().sort_values(["customer_id", "date"])

    # Rolling 2-day average of amount, per customer.
    df["customer_rolling_avg"] = (
        df.groupby("customer_id")["amount"]
        .rolling(window=2, min_periods=1)
        .mean()
        .reset_index(level=0, drop=True)
    )

    print(df[["customer_id", "date", "amount", "customer_rolling_avg"]].round(2))


def demo_group_rank() -> None:
    """rank() within a group — the leaderboard pattern.

    method='dense' gives every distinct value a rank without gaps.
    """
    print("\n" + "=" * 60)
    print("GROUP-LEVEL RANK (LEADERBOARD)")
    print("=" * 60)

    df = sample_daily_orders()
    df["rank_in_customer"] = (
        df.groupby("customer_id")["amount"]
        .rank(method="dense", ascending=False)
    )

    print(df[["customer_id", "date", "amount", "rank_in_customer"]])


def main() -> None:
    demo_rolling_average()
    demo_expanding_cumulative()
    demo_shift_lag_lead()
    demo_pct_change()
    demo_cumulative_helpers()
    demo_groupby_rolling()
    demo_group_rank()


if __name__ == "__main__":
    main()
