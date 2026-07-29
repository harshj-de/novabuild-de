"""
Section 1.5 — Error Handling.

The section that separates scripts from pipelines. A script that crashes
on one bad record is useless in production — a pipeline must skip bad
records, log them, and keep going.

Covers:
  * try / except / else / finally.
  * Catching multiple exception types.
  * The pattern for "skip-and-log" record processing.
  * Why record.get('key', 'unknown') matters inside except blocks.

Run: `python 05_error_handling.py`
"""

import logging


def demo_basic_try_except() -> None:
    """Structural walk-through of try/except/finally."""
    print("=" * 60)
    print("BASIC TRY / EXCEPT / FINALLY")
    print("=" * 60)

    def process_record(raw_value):
        try:
            result = int(raw_value)
            print(f"Processed: {result}")
        except ValueError:
            print(f"Skipped bad value: {raw_value}")
        finally:
            # `finally` runs whether the try succeeded or failed.
            # Use it for cleanup: close a file, release a connection, log completion.
            print("Record attempt complete")

    process_record("1500")
    process_record("bad")


def safe_clean(record: dict) -> dict | None:
    """Return a typed record on success, or None on failure.

    Catches both ValueError (from int/float conversion) and KeyError
    (from a missing required field). The .get() call in the error
    message avoids a secondary crash if `customer_id` itself is missing.
    """
    try:
        return {
            "customer_id": int(record["customer_id"]),
            "total_spent": float(record["total_spent"]),
        }
    except (ValueError, KeyError) as exc:
        print(
            f"Skipped record {record.get('customer_id', 'unknown')} -> {exc}"
        )
        return None


def demo_skip_and_log_pattern() -> None:
    """Process a batch — bad records skip, good records accumulate.

    This is THE production pattern for ingesting messy source data.
    """
    print("\n" + "=" * 60)
    print("SKIP-AND-LOG PATTERN")
    print("=" * 60)

    records = [
        {"customer_id": "301", "total_spent": "15000.50"},
        {"customer_id": "302", "total_spent": "not_a_number"},
        {"customer_id": "bad", "total_spent": "9200.00"},
        {"customer_id": "304", "total_spent": "42000.75"},
        {"total_spent": "5000.00"},  # missing customer_id
    ]

    cleaned_records = []
    for record in records:
        cleaned = safe_clean(record)
        if cleaned:
            cleaned_records.append(cleaned)

    print("\nFinal cleaned records:")
    for r in cleaned_records:
        print(f"  {r}")


def demo_logging_instead_of_print() -> None:
    """Same pattern but using the logging module — production-ready.

    Print statements disappear. Logs can be:
      - filtered by level (INFO, WARNING, ERROR)
      - routed to files, monitoring systems, and alerting tools
      - timestamped automatically
    """
    print("\n" + "=" * 60)
    print("SKIP-AND-LOG WITH THE LOGGING MODULE")
    print("=" * 60)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    logger = logging.getLogger("record_processor")

    def process_with_logging(record):
        try:
            return {
                "customer_id": int(record["customer_id"]),
                "total_spent": float(record["total_spent"]),
            }
        except (ValueError, KeyError) as exc:
            logger.error(
                "Skipped record %s -> %s",
                record.get("customer_id", "unknown"),
                exc,
            )
            return None

    records = [
        {"customer_id": "401", "total_spent": "22000"},
        {"customer_id": "402", "total_spent": "invalid"},
    ]

    cleaned = [r for r in (process_with_logging(rec) for rec in records) if r]
    logger.info("Processed %d valid records", len(cleaned))


def main() -> None:
    demo_basic_try_except()
    demo_skip_and_log_pattern()
    demo_logging_instead_of_print()


if __name__ == "__main__":
    main()
