"""
Section 3.6 — Datetime Handling.

Every DE pipeline has dates. Loading them wrong (as strings) means all
time-based analysis breaks silently. This module covers the datetime
patterns you must own.

Covers:
  * pd.to_datetime — safe parsing with errors='coerce'
  * The .dt accessor — year, month, day, dayofweek, quarter
  * Time-based filtering (last N days, this quarter, between two dates)
  * Timezone handling (naive vs aware, tz_localize, tz_convert)
  * pd.date_range for building calendars / gap-fill indices
  * Resampling — turning event-level data into hourly / daily / weekly

Run: `python 06_datetime_handling.py`
"""

import pandas as pd


def sample_orders_with_dates() -> pd.DataFrame:
    dates = [
        "2024-01-15",
        "2024-01-16",
        "2024-01-17",
        "2024-02-01",
        "2024-02-15",
        "2024-03-01",
        "2024-03-15",
    ]
    return pd.DataFrame(
        {
            "order_id": [f"O{i:03d}" for i in range(1, len(dates) + 1)],
            "order_date": dates,
            "amount": [4500, 12000, 800, 3200, 15000, 6700, 8900],
        }
    )


def demo_to_datetime() -> None:
    print("=" * 60)
    print("pd.to_datetime — SAFE PARSING")
    print("=" * 60)

    df = sample_orders_with_dates()
    print("before parsing — dtype:", df["order_date"].dtype)

    df["order_date"] = pd.to_datetime(df["order_date"])
    print("after parsing — dtype:", df["order_date"].dtype)
    print(df.head(3))


def demo_errors_coerce() -> None:
    """errors='coerce' turns unparseable dates into NaT instead of raising."""
    print("\n" + "=" * 60)
    print("errors='coerce' — SURVIVING BAD DATES")
    print("=" * 60)

    dates = pd.Series(["2024-01-15", "not_a_date", "2024-02-01"])
    parsed = pd.to_datetime(dates, errors="coerce")
    print(parsed)
    print(f"NaT count: {parsed.isnull().sum()}")


def demo_dt_accessor() -> None:
    """The .dt namespace — every datetime component available as a Series."""
    print("\n" + "=" * 60)
    print(".dt ACCESSOR — YEAR, MONTH, DAY, DOW, QUARTER")
    print("=" * 60)

    df = sample_orders_with_dates()
    df["order_date"] = pd.to_datetime(df["order_date"])

    df["year"] = df["order_date"].dt.year
    df["month"] = df["order_date"].dt.month
    df["day_of_week"] = df["order_date"].dt.day_name()
    df["quarter"] = df["order_date"].dt.quarter

    print(df[["order_id", "order_date", "year", "month", "day_of_week", "quarter"]])


def demo_date_filtering() -> None:
    """Filtering by date range — the daily DE task."""
    print("\n" + "=" * 60)
    print("DATE-RANGE FILTERING")
    print("=" * 60)

    df = sample_orders_with_dates()
    df["order_date"] = pd.to_datetime(df["order_date"])

    # Orders in February 2024.
    mask = (df["order_date"] >= "2024-02-01") & (df["order_date"] <= "2024-02-29")
    print("February 2024 orders:")
    print(df[mask])

    # Between two Timestamps — the more explicit form.
    start = pd.Timestamp("2024-01-15")
    end = pd.Timestamp("2024-02-15")
    print(f"\norders between {start.date()} and {end.date()}:")
    print(df[df["order_date"].between(start, end)])


def demo_timezone_handling() -> None:
    """tz_localize (assign a tz) vs tz_convert (change tz)."""
    print("\n" + "=" * 60)
    print("TIMEZONES — LOCALIZE VS CONVERT")
    print("=" * 60)

    df = sample_orders_with_dates()
    df["order_date"] = pd.to_datetime(df["order_date"])

    # Assign a timezone to naive timestamps (they must be naive first).
    df["order_date_IST"] = df["order_date"].dt.tz_localize("Asia/Kolkata")

    # Convert to a different timezone.
    df["order_date_UTC"] = df["order_date_IST"].dt.tz_convert("UTC")

    print(df[["order_id", "order_date", "order_date_IST", "order_date_UTC"]].head(3))


def demo_date_range() -> None:
    """pd.date_range — build calendars, gap-fill missing days."""
    print("\n" + "=" * 60)
    print("pd.date_range — BUILDING CALENDARS")
    print("=" * 60)

    # 7 daily periods starting from a date.
    calendar = pd.date_range(start="2024-01-01", periods=7, freq="D")
    print(f"daily: {calendar.tolist()[:3]} ...")

    # Business-day range — skips weekends.
    biz = pd.date_range(start="2024-01-01", end="2024-01-10", freq="B")
    print(f"\nbusiness days between Jan 1 and Jan 10: {biz.tolist()}")


def demo_resampling() -> None:
    """Resample — event-level to hourly / daily / monthly aggregates."""
    print("\n" + "=" * 60)
    print("RESAMPLING — DAILY TO MONTHLY")
    print("=" * 60)

    df = sample_orders_with_dates()
    df["order_date"] = pd.to_datetime(df["order_date"])
    df = df.set_index("order_date")

    # Monthly totals.
    monthly = df.resample("ME")["amount"].sum()
    print("monthly totals:")
    print(monthly)


def main() -> None:
    demo_to_datetime()
    demo_errors_coerce()
    demo_dt_accessor()
    demo_date_filtering()
    demo_timezone_handling()
    demo_date_range()
    demo_resampling()


if __name__ == "__main__":
    main()
