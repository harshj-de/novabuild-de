# Section 6.6 — Data Mesh

This section is a design exercise, not code.

Data Mesh is a way of organising data ownership across a company. It
doesn't compete with Kimball / Data Vault / Medallion — it operates
one layer above them. Kimball says HOW to model your warehouse. Data
Mesh says WHO OWNS each part of the warehouse.

---

## The problem Data Mesh solves

**Centralised model (traditional):**

```
                       ┌────────────────────┐
                       │  Central DE Team   │
                       │  (5 engineers)     │
                       └────────────────────┘
                       ▲          ▲         ▲
                       │          │         │
              ┌────────┘          │         └────────┐
              │                   │                  │
     ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
     │   Claims Team  │  │    COI Team    │  │  Safety Team   │
     └────────────────┘  └────────────────┘  └────────────────┘
```

Every request funnels through the central team. Every schema change
requires their approval. The central team becomes a bottleneck:

- Claims team needs a new report → JIRA ticket → 2-week queue
- COI team needs a fresh KPI → JIRA ticket → 2-week queue
- Safety team needs a schema change → JIRA ticket → 3-week queue

The central team becomes the reason the business slows down. This is
a real pattern; it kills warehouse initiatives at large companies.

---

## The Data Mesh alternative

```
     ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
     │   Claims Team  │  │    COI Team    │  │  Safety Team   │
     │                │  │                │  │                │
     │  owns:         │  │  owns:         │  │  owns:         │
     │  fact_claims   │  │  fact_coi      │  │  fact_safety   │
     │  dim_claim     │  │  dim_coi       │  │  dim_safety    │
     └────────────────┘  └────────────────┘  └────────────────┘
              │                   │                  │
              ▼                   ▼                  ▼
     ┌──────────────────────────────────────────────────────────┐
     │            Federated Data Discovery Layer                │
     │                                                          │
     │   Everyone can browse and query everyone else's data —   │
     │   but publishers own their own quality and schema.       │
     └──────────────────────────────────────────────────────────┘
```

Each domain team OWNS the data for their domain. They publish it as a
"data product" for consumption by other teams. A central platform
team provides tooling (dbt, catalog, orchestration) but does NOT own
the data itself.

---

## The four principles of Data Mesh

1. **Domain-oriented ownership** — the team closest to the business
   process owns the data about it. Claims team owns claim data,
   full stop.

2. **Data as a product** — each domain's data output has:
   - Documentation
   - Quality guarantees (freshness SLA, uptime SLA)
   - Discoverability (searchable catalog)
   - Consumer support (Slack channel, on-call)
   - Versioning (v1, v2, deprecation timeline)

3. **Self-serve data platform** — a central team provides the tools
   (ingestion, transformation, storage, catalog) but not the data
   itself. Think dbt Cloud + Snowflake + Alation.

4. **Federated computational governance** — cross-domain standards
   (naming conventions, PII handling, common dimensions) enforced by
   a governance council, not by a central data team acting as
   gatekeepers.

---

## Applying it to NovaBuild

Suppose NovaBuild grows to 300 people. Central DE team of 4 can't
keep up. A Data Mesh restructuring:

| Domain | Team | Owns data products |
|---|---|---|
| **Claims** | Claims Ops | `fact_claims`, `dim_claim_status`, `agg_monthly_loss` |
| **COI Compliance** | COI Team | `fact_coi_verifications`, `dim_certificate_type`, `agg_compliance_rate` |
| **Safety** | Safety Team | `fact_safety_incidents`, `dim_incident_type`, `agg_incident_rate` |
| **Contractor Master** | Underwriting | `dim_contractor_scd2`, `fact_tier_changes` |
| **Financial** | Finance | `fact_premiums`, `fact_reserves` |
| **Platform** | Central DE | dbt Cloud, Snowflake, orchestration, catalog — but NO business data |

The Claims team publishes `fact_claims` as a data product. Underwriting
subscribes to it. Safety subscribes to it. If Claims wants to change
the schema, they publish v2 and give consumers 3 months to migrate.

---

## When Data Mesh actually makes sense

**Adopt Data Mesh when:**
- Company has > 200 employees and > 20 distinct data domains
- Central DE team is genuinely bottlenecked
- Business domains have their own data-capable engineers
- Executive commitment to distributed governance

**DON'T adopt Data Mesh when:**
- Team is < 50 people — you don't have the mass
- Domains don't have data engineers — you'd just create silos
- Culture doesn't support distributed ownership — mesh needs buy-in
- You're already struggling with the basics — fix Bronze/Silver/Gold
  first

**The uncomfortable truth:** most companies who say they're doing
Data Mesh are just doing Kimball with cross-team documentation. That's
fine — Kimball with good ownership is 90% of the value.

---

## Comparison to alternatives

| | **Central Warehouse** | **Data Lake** | **Data Mesh** |
|---|---|---|---|
| Ownership | Central DE team | Central DE team | Distributed to domains |
| Schema | Kimball star | Schema-on-read | Kimball star per domain |
| Discovery | Wiki, manual | Difficult | Catalog + data products |
| Quality | Central team's responsibility | Data-quality-day | Domain team's responsibility |
| Time-to-first-report | Slow | Very slow | Fast (once domains own) |
| Best for | < 100 people | Analytics with big data | 200+ people with data-capable domains |

---

## Design exercise for NovaBuild (interview-style)

**Scenario:** NovaBuild has grown to 400 people. The 5-person central
DE team is drowning. The Claims team has 3 engineers who could own
their own data pipelines. Executive wants a Data Mesh transition.

**Design questions:**

1. What are NovaBuild's data domains? (Suggested answer: Claims, COI,
   Safety, Contractor Master, Financial, Platform)
2. What data products does each domain publish?
3. What common dimensions get shared? (Suggested: `dim_contractor` —
   this needs governance, otherwise every domain will have a
   different one)
4. What does the platform team keep owning? (Ingestion, transformation
   tooling, storage, catalog, orchestration, monitoring)
5. What's the incremental rollout plan? (Start with ONE domain — pick
   the one most bottlenecked and most engineering-capable. Prove it
   works. Then expand.)

---

## Summary

- **Data Mesh** is a data-ownership pattern, not a technical pattern.
  It lives one layer above Kimball / Data Vault / Medallion.
- **The problem it solves:** central DE team becoming a bottleneck.
- **Four principles:** domain ownership, data as product, self-serve
  platform, federated governance.
- **Real prerequisites:** > 200 people, data-capable domain teams,
  executive commitment.
- **Common mistake:** claiming Data Mesh while doing Kimball + Slack.

Next: Section 6.7 — the analytical query patterns Data Mesh enables
(OLAP operations against the published data products).
