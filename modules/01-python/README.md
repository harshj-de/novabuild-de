# Module 01 — Python for Data Engineering

Python fundamentals applied to real Data Engineering concerns — data validation,
error tolerance, pipeline structure, and streaming record processing. Sections
1.1 through 1.8 of the curriculum, refactored from the original Colab notebooks
into runnable production-style Python files.

---

## What This Module Demonstrates

- **Section 1.1 — Types & Collections** · primitives, `None` handling, the four
  collection types, safe type conversion from strings, and a `clean_record()`
  reference implementation.
- **Section 1.2 — Operators & Control Flow** · boolean logic on records,
  membership tests, `if/elif`, `for/while`, and a retry-with-backoff pattern.
- **Section 1.3 — Comprehensions** · list/dict/set comprehensions, filtering,
  and the readability line where you should fall back to a plain loop.
- **Section 1.4 — Functions** · pure vs impure, defaults, `*args`/`**kwargs`,
  the mutable-default trap and its fix, safe `.get()`-based dict access.
- **Section 1.5 — Error Handling** · `try/except/finally`, the skip-and-log
  pattern for record-by-record ETL, and logging inside `except`.
- **Section 1.6 — OOP Basics** · classes with `__init__` and `__repr__`,
  class variables, validation at construction time.
- **Section 1.6 (cont.) — Inheritance** · `BasePipeline` parent, specialised
  children, `super()`, method overriding, and polymorphism.
- **Section 1.7 — Generators** · `yield`, streaming filters, chained generators
  for multi-stage streaming ETL.
- **Section 1.8 — Production Logging** · configured loggers, log levels, named
  loggers, `logger.exception()`, and rotating file handlers.

---

## Capstone Project — Customer Processing Pipeline

Located in [`src/capstone/`](./src/capstone). Four files that combine every
concept from the module into a runnable streaming pipeline:

| File | Role |
|------|------|
| `customer_dataclass.py` | Typed domain model with attached business logic |
| `base_pipeline.py`      | Reusable base class for named, observable pipelines |
| `customer_pipeline.py`  | Validation generator + specialised child pipeline |
| `run_pipeline.py`       | Runnable entry point with sample data and logging setup |

Run from the `src/` directory:
```bash
python -m capstone.run_pipeline
```

Sample output — 6 raw records in, 3 valid customers processed, 3 bad records
logged and skipped (invalid float, empty name, unrecognised status).

---

## Structure

```
01-python/
├── README.md              (this file)
├── src/
│   ├── 01_primitives_and_collections.py
│   ├── 02_operators_and_control_flow.py
│   ├── 03_comprehensions.py
│   ├── 04_functions.py
│   ├── 05_error_handling.py
│   ├── 06_oop_basics.py
│   ├── 07_oop_inheritance.py
│   ├── 08_generators.py
│   ├── 09_production_logging.py
│   └── capstone/
│       ├── __init__.py
│       ├── customer_dataclass.py
│       ├── base_pipeline.py
│       ├── customer_pipeline.py
│       └── run_pipeline.py
├── notebooks/                                (original Colab notebooks preserved)
│   ├── 00_module1_python_foundations.ipynb
│   ├── 01_capstone_customer_pipeline.ipynb
│   ├── 02_blackjack_oop_practice.ipynb
│   ├── 03_regex_practice.ipynb
│   └── 04_practice_sandbox.ipynb
└── requirements.txt
```

Every `.py` file in `src/` runs standalone as a self-contained demonstration:
```bash
python 01_primitives_and_collections.py
python 02_operators_and_control_flow.py
# ...etc
```

Notebooks under `notebooks/` are the original Colab source. They are preserved
for reviewers who want to see the exploratory learning journey; the `src/`
files are what a reviewer should evaluate for production coding style.

---

## Skills Demonstrated

`Python 3.10+` · `dataclasses` · `type hints` · `generators` · `OOP` ·
`inheritance` · `error handling` · `logging` · `streaming ETL patterns`

---

## Runtime Environment

Zero external dependencies. Uses standard library only (`dataclasses`,
`logging`, `collections.abc`, `typing`). Requires Python 3.10+ for the
union type syntax (`dict | None`).
