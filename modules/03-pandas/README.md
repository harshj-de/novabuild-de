# Module 03 — Pandas for Data Engineering

The DataFrame toolkit every Data Engineer reaches for daily. Sections 3.1
through 3.12 of the curriculum, refactored from the original Colab notebooks
into runnable production-style Python files. Two end-to-end capstones tie the
concepts to real deliverables.

---

## What This Module Demonstrates

- **Section 3.1 — Series and DataFrame** · Series semantics, DataFrame
  creation, the five discovery commands (shape, dtypes, info, head,
  describe), null checks.
- **Section 3.2 — Loading Data** · Naive vs. proper `read_csv` (dtype,
  parse_dates, na_values), category dtype for memory savings, reading
  JSON and Parquet, chunked reads for out-of-RAM files.
- **Section 3.3 — Selecting and Filtering** · Column selection, `.loc`,
  `.iloc`, boolean masks, `.isin()`, `.query()`, null filtering.
- **Section 3.4 — Indexing and MultiIndex** · `set_index`, `reset_index`,
  sort variants, MultiIndex creation, navigation, and the flatten pattern.
- **Section 3.5 — Data Cleaning** · Null detection and fill strategies,
  duplicate handling, string cleaning via the `.str` accessor, type
  coercion with `errors='coerce'`, outlier detection (IQR + z-score),
  `.clip()`.
- **Section 3.6 — Datetime Handling** · `to_datetime`, `errors='coerce'`,
  `.dt` accessor, date-range filtering, timezone localize/convert,
  `date_range`, resampling.
- **Section 3.7 — Transformations** · `assign`, `apply`, `map`, `replace`,
  `where`/`mask`, `np.where`, `pd.cut`/`pd.qcut`, `rank`.
- **Section 3.8 — GroupBy and Aggregations** · Simple aggregations, `.agg`
  with multiple functions, named aggregations, multi-key groupby,
  `transform` for row-level group metrics, `filter` on groups.
- **Section 3.9 — Reshaping Data** · `pivot_table` (long → wide), `melt`
  (wide → long), `stack`/`unstack`.
- **Section 3.10 — Merging Data** · Inner / left / right / outer joins,
  different key names, index joins, silent row-multiplication detection,
  `concat`.
- **Section 3.11 — Window Operations** · Rolling averages, expanding
  cumulative, `shift` for lag/lead, `pct_change`, cumulative helpers,
  groupby + rolling, group-level rank.
- **Section 3.12 — Performance, Output, Validation, Method Chaining** ·
  Vectorization vs Python loops (measured speedup), output-format
  comparison (CSV / Parquet / JSON), validation assertions,
  production-style method chaining.

---

## Capstone Projects

Two end-to-end deliverables in [`src/capstone/`](./src/capstone).

### Capstone 1 — CSV Ingestion + Validation Pipeline

`csv_ingestion_pipeline.py` · Generates a 1,000-row messy sales CSV, parses
it, validates each record, and splits output into `cleaned_sales_data.csv`
(loadable) and `rejected_sales_data.csv` (quarantined with error reasons).
This is the shape every real ETL job takes.

**Bug fixes flagged in-line** — the original notebook version had a stray
`\t` in the join separator, a misplaced product-missing check nested
inside an unrelated `except` block, and a column-order mismatch on
output. All fixed with the reason called out in a comment.

### Capstone 2 — Olympic Bios Cleaner

`olympic_bios_cleaner.py` · End-to-end cleaning of an Olympic athlete
biographical dataset. Every step ties back to a section concept:

- Discovery ritual (§3.1)
- String cleaning with regex (§3.5)
- Multi-column extraction from free text — measurements → height / weight,
  birthplace → city / region / country (§3.5, §3.9)
- Multi-format date parsing (§3.6)
- Range validation with `.between()` (§3.5)
- Method-chained pipeline (§3.12)

Includes a 25-row sample of the dataset at `data/bios_sample.csv` so the
pipeline runs out of the box. Full dataset available on Kaggle
(`olympic athletes bios`).

Run:
```bash
cd modules/03-pandas/src/capstone
python olympic_bios_cleaner.py
```

---

## Structure

```
03-pandas/
├── README.md                                       (this file)
├── requirements.txt
├── src/
│   ├── 01_series_and_dataframe.py                  (§3.1)
│   ├── 02_loading_data.py                          (§3.2)
│   ├── 03_selecting_and_filtering.py               (§3.3)
│   ├── 04_indexing_and_multiindex.py               (§3.4)
│   ├── 05_data_cleaning.py                         (§3.5)
│   ├── 06_datetime_handling.py                     (§3.6)
│   ├── 07_transformations.py                       (§3.7)
│   ├── 08_groupby_and_aggregations.py              (§3.8)
│   ├── 09_reshaping_data.py                        (§3.9)
│   ├── 10_merging_data.py                          (§3.10)
│   ├── 11_window_operations.py                     (§3.11)
│   ├── 12_performance_output_validation.py         (§3.12)
│   └── capstone/
│       ├── __init__.py
│       ├── csv_ingestion_pipeline.py               (Capstone 1)
│       └── olympic_bios_cleaner.py                 (Capstone 2)
├── notebooks/                                      (originals preserved)
│   ├── 00_pandas_module_3_main.ipynb
│   ├── 01_pandas_module_3_alternate.ipynb
│   ├── 02_olympic_bios_cleaner.ipynb
│   └── 03_csv_creation_validator.ipynb
└── data/
    └── bios_sample.csv                             (25-row sample)
```

Every `.py` file in `src/` runs standalone:
```bash
python 01_series_and_dataframe.py
python 02_loading_data.py
# ...etc
```

---

## Skills Demonstrated

`pandas 2+` · `numpy` · `pyarrow (Parquet)` · `regex-driven extraction` ·
`groupby transforms` · `window functions` · `long/wide reshaping` ·
`streaming ETL patterns` · `production validation` · `method chaining`

---

## Runtime Environment

Requires Python 3.10+ and the packages in `requirements.txt`:
```bash
pip install -r requirements.txt
```
