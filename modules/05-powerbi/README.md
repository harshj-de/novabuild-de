# Module 05 — Power BI Executive Dashboard

**Status:** Dashboard file (`.pbix`) and screenshots landing in this folder shortly. Design refresh in progress.

A production-quality Power BI dashboard built on the NovaBuild insurance schema. Demonstrates the full modeling and visualization stack — not just charts, but the semantic model, DAX, and UX decisions that produce a dashboard executives actually use.

---

## What This Module Demonstrates

- **Galaxy schema data modeling** — 6 fact tables + 8 dimension tables designed for star/snowflake queries and conformed dimensions
- **All 30 model relationships** — cardinality, cross-filter direction, and inactive relationships deliberately configured (not auto-generated)
- **22 DAX measures** — calculated columns, measures, time intelligence (YTD, QoQ, YoY), context transitions, iterators
- **3-page executive dashboard** — Overview, Contractor Deep-Dive, Claims & Exposure — designed with narrative arc, not just tiles
- **Row-Level Security (RLS)** — USERPRINCIPALNAME()-based filtering so regional underwriters see only their book
- **What-if parameters** — interactive risk-threshold sliders driving live re-scoring
- **Drillthrough + custom tooltips** — click a contractor tile → drillthrough to their claims history
- **Bookmarks & selections** — guided view states for exec presentations

---

---

## Why Screenshots Matter

Recruiters won't install Power BI Desktop to open a `.pbix`. Screenshots + a documented DAX file are what actually get evaluated. This folder is optimized for that reality.

---

## Skills Demonstrated

`Power BI Desktop` · `DAX` · `Galaxy Schema` · `RLS` · `Time Intelligence` · `Data Modeling` · `Executive Reporting`

---

## Domain Context

The dashboard answers questions an insurance operations executive actually asks: portfolio-level risk trend, contractor concentration, claims frequency by policy type, exposure vs. premium efficiency. Data comes from the NovaBuild schema. See [`/datasets`](../../datasets).
