"""Customer processing pipeline — capstone project for Module 01.

Demonstrates every concept from sections 1.1–1.8 working together:

  * dataclass for typed record representation (customer_dataclass)
  * base class + inheritance for reusable pipeline plumbing (base_pipeline)
  * generator with skip-and-log validation (clean_customers)
  * logging for observability
  * a runnable entry point (run_pipeline)

The four files below are meant to be read in this order:
  1. customer_dataclass.py  — the domain model
  2. base_pipeline.py       — the reusable base class
  3. customer_pipeline.py   — the specialised child + validation generator
  4. run_pipeline.py        — the entry point that wires everything together
"""

from .customer_dataclass import Customer
from .base_pipeline import BasePipeline
from .customer_pipeline import CustomerPipeline, clean_customers

__all__ = ["Customer", "BasePipeline", "CustomerPipeline", "clean_customers"]
