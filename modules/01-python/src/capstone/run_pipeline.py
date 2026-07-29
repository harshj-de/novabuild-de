"""Capstone entry point — wire up logging and run the CustomerPipeline.

Run from the module01/src directory with:
    python -m capstone.run_pipeline

or from anywhere with the src/ folder on sys.path:
    python capstone/run_pipeline.py
"""

import logging

from .customer_pipeline import CustomerPipeline


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


# A small fixture that mirrors the shape of real, messy input:
# * whitespace on names, mixed case on statuses
# * one bad float, one empty name, one invalid status
SAMPLE_RAW_CUSTOMERS: list[dict] = [
    {"id": "301", "name": "  Priya Mehta  ", "spent": "45000", "status": "active"},
    {"id": "302", "name": "Arjun Patel",     "spent": "bad",   "status": "active"},
    {"id": "303", "name": "  Sneha Shah  ",  "spent": "12000", "status": "inactive"},
    {"id": "304", "name": "Rahul Verma",     "spent": "72000", "status": "Active"},
    {"id": "305", "name": "",                "spent": "9000",  "status": "active"},
    {"id": "306", "name": "Divya Nair",      "spent": "31000", "status": "invalid"},
]


def main() -> None:
    configure_logging()
    pipeline = CustomerPipeline()
    pipeline.run(SAMPLE_RAW_CUSTOMERS)


if __name__ == "__main__":
    main()
