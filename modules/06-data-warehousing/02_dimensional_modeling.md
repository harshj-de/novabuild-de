# Section 6.2 — Dimensional Modelling

Section 6.1 established WHY warehouses look different from OLTP databases.
This section explains the HOW — how to actually design one.

Every star schema has the same shape:

- **One fact table** at the centre (measurable events — claims, sales, page views)
- **Multiple dimension tables** around it (descriptive context — who, what, where, when)
- **Foreign keys** from fact rows to dimension rows via surrogate keys

---

## Fact vs Dimension — the mental model

| | **Fact** | **Dimension** |
|---|---|---|
| **Contains** | Measurable events — one row per event | Descriptive context — one row per entity |
| **Grain** | The atomic thing being measured (one claim, one sale, one login) | The entity being described (one contractor, one product, one date) |
| **Columns** | Foreign keys + numeric measures | Attributes (names, categories, hierarchies) |
| **Growth** | Grows fast — millions of rows over time | Grows slowly — hundreds to thousands of rows |
| **Typical width** | Narrow (10-20 columns) | Wide (20-100 columns of attributes) |

**NovaBuild examples:**

- `fact_claims` — one row per claim filed. FKs to contractor, policy, date. Measures: total_incurred, paid_amount, reserve_amount.
- `dim_contractor` — one row per contractor. Attributes: company_name, trade, state, tier, emr, employees_count.

---

## The three grains

**Grain = "what does one row in this fact table represent?"** Getting the grain right is 80% of dimensional modelling.

1. **Transaction grain** — one row per event.
   Example: one row per claim, one row per sale.
   Most common. Highest fidelity.

2. **Periodic snapshot grain** — one row per entity per period.
   Example: one row per contractor per month with their tier + EMR at that moment.
   Used for trending analysis.

3. **Accumulating snapshot grain** — one row per entity, updated as it moves through a process.
   Example: one row per claim, with columns for filed_date, investigated_date, settled_date, closed_date.
   Used for pipeline / lifecycle analysis.

Pick ONE grain per fact table. Never mix. If you need both, build two facts.

---

## Star Schema

```
        dim_contractor           dim_date
              │                     │
              │                     │
              ▼                     ▼
       ┌────────────────────────────────────┐
       │           fact_claims              │
       │                                    │
       │  contractor_sk  (FK)               │
       │  date_sk        (FK)               │
       │  policy_sk      (FK)               │
       │  total_incurred (measure)          │
       │  paid_amount    (measure)          │
       └────────────────────────────────────┘
              ▲                     ▲
              │                     │
              │                     │
         dim_policy            dim_loss_type
```

**Star** because it visually looks like a star — the fact at the centre, dimensions radiating outward.

**Why it's fast:**
- Only ONE join between fact and any dimension (no chains)
- Query optimisers know this shape well
- BI tools produce clean SQL against it

**Why analysts love it:**
- Easy to understand: "give me total incurred by contractor tier and month"
- Easy to slice: filter dimensions, aggregate facts

---

## Snowflake Schema

Dimensions themselves get normalised into sub-dimensions.

```
dim_contractor  →  dim_trade  →  dim_trade_category
     │
     └───────────→  dim_state  →  dim_country
```

**Pros:** less redundancy (each `trade_category` stored once, not repeated in every contractor row)
**Cons:** more joins → slower queries → less BI-friendly

**Modern practice: use star, not snowflake.** Storage is cheap now; joins are the bottleneck. Only snowflake dimensions that are genuinely huge and rarely queried together.

---

## Surrogate Keys

Every dimension gets an integer primary key (`_sk`) that's independent of the source system's natural key.

**Why?**
- Source keys can change (contractor_id "C-1234" gets renamed)
- Source keys can collide across sources (contractor_id "C-1234" in Source A ≠ Source B)
- Surrogate keys enable **SCD Type 2** — you can have two rows with the same natural key but different surrogate keys, one per historical version

**NovaBuild pattern:**
```
dim_contractor_scd2:
    sk            SERIAL PRIMARY KEY          ← surrogate key
    contractor_id VARCHAR NOT NULL            ← natural key from source
    company_name  VARCHAR
    tier          VARCHAR
    valid_from    TIMESTAMP
    valid_to      TIMESTAMP
    is_current    BOOLEAN
```

Section 6.3 shows this table in action.

---

## Slowly Changing Dimensions (SCD Types)

When a dimension attribute changes (contractor's tier moves from Probationary → Preferred), how do you record it?

| Type | Behaviour | Example | Use |
|---|---|---|---|
| **Type 0** | Never change | date_of_birth | Static attributes |
| **Type 1** | Overwrite in place | Fix a typo in company_name | When history isn't valuable |
| **Type 2** | Add a new row; expire the old | Tier change | **Most common in warehouses** |
| **Type 3** | Add a column for previous value | previous_tier | Rare, limited history |
| **Type 4** | Split into current + history tables | dim_contractor_current + dim_contractor_history | Very large dims |
| **Type 6** | Hybrid — Type 1 + 2 + 3 in one dim | Complex — rarely justified | Specialty use |

**Rule of thumb:** default to Type 2 unless you have a specific reason.

**Section 6.3 implements SCD Type 2** for the contractor tier change scenario.

---

## The dimensional-modelling checklist

Before shipping any star schema, ask:

- [ ] Is the fact table's grain declared explicitly?
- [ ] Are all facts at the SAME grain (no mixing)?
- [ ] Do dimensions have surrogate keys (not just natural keys)?
- [ ] Is there a `dim_date` (even if generated)?
- [ ] Are conformed dimensions shared across marts (same `dim_contractor` used by both Claims and COI marts)?
- [ ] Are numeric attributes-that-should-be-dimensions actually in dims (e.g. contractor size band)?
- [ ] Do measures include both additive (total_incurred), semi-additive (reserve_amount snapshotted), and non-additive (loss_ratio) considerations?

---

## Summary

- **Fact tables** hold measurable events; **dimension tables** hold descriptive context. Star schemas surround one fact with many dims.
- **Grain** = "what does one row of this fact represent?" Get it right first.
- **Star** beats snowflake in practice — fewer joins, BI-friendly.
- **Surrogate keys** decouple warehouse identity from source-system identity — required for SCD Type 2.
- **SCD Type 2** is the default for handling dimension changes.

Next: Section 6.3 — SCD Type 2 in action on NovaBuild contractor tier changes.
