"""Customer-specific pipeline built on top of BasePipeline.

Two exports:

  clean_customers(raw_records)
      A generator that yields validated Customer objects one at a time.
      For each raw record it asks three questions in order:
        1. Is `name` empty?      -> skip
        2. Does `spent` convert? -> if no, skip
        3. Is `status` valid?    -> if no, skip
      Failures are logged with structured context; successes are yielded.

  CustomerPipeline
      Specialised pipeline that runs the generator, tracks processed
      and skipped counts, and prints a final summary.
"""

import logging
from collections.abc import Iterator

from .base_pipeline import BasePipeline
from .customer_dataclass import Customer

logger = logging.getLogger("CustomerPipeline")

VALID_STATUSES: set[str] = {"active", "inactive"}


def clean_customers(raw_records: list[dict]) -> Iterator[Customer]:
    """Yield validated Customer objects, one raw record at a time.

    Records that fail any of the three checks are logged and skipped.
    The generator never raises — bad data cannot kill the pipeline.
    """
    for raw in raw_records:
        # Check 1 — name must be non-empty after stripping whitespace.
        name = raw.get("name", "").strip()
        if not name:
            logger.error("Skipped record %s -- name is empty", raw.get("id"))
            continue

        # Check 2 — spent must convert to float.
        try:
            spent = float(raw["spent"])
        except (ValueError, KeyError, TypeError):
            logger.error(
                "Skipped record %s -- spent %r is not a number",
                raw.get("id"),
                raw.get("spent"),
            )
            continue

        # Check 3 — status must be in the valid set (case-insensitive).
        status = raw.get("status", "").strip().lower()
        if status not in VALID_STATUSES:
            logger.error(
                "Skipped record %s -- status %r is invalid",
                raw.get("id"),
                status,
            )
            continue

        # All three passed — yield a typed Customer.
        yield Customer(
            id=int(raw["id"]),
            name=name,
            spent=spent,
            status=status,
        )


class CustomerPipeline(BasePipeline):
    """Run the customer validation + tiering pipeline over a batch."""

    def __init__(self) -> None:
        super().__init__("CustomerPipeline")

    def run(self, raw_records: list[dict]) -> None:
        self.log("Starting")
        total = len(raw_records)

        for customer in clean_customers(raw_records):
            self.processed += 1
            self.log(f"Valid: {customer.name} | Tier: {customer.get_tier()}")

        self.skipped = total - self.processed
        self.summary()
