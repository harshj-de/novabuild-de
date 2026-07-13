# NovaBuild — Entity Relationships

This document maps the foreign-key relationships across all 21 tables. Use it as a reading guide when navigating the schema or writing joins.

---

## Reading the Relationships

Every foreign key is written as: `<child_table>.<column> → <parent_table>.<column>`

Cardinalities noted where meaningful. Most relationships are **many-to-one** (child rows point to a single parent) unless flagged otherwise.

---

## 1. Reference / Master Layer

These tables are the root nodes — nothing depends on tables above them.

- `carriers` — no upstream FKs (root)
- `brokers` — no upstream FKs (root)
- `sponsors` — no upstream FKs (root)
- `contractors` — no upstream FKs (root)

**Downstream referenced by:** projects, wrap_programs, policies, enrollments, claims, and most operational tables.

---

## 2. Projects & Wrap
A **project** is a construction job. A **wrap program** is the insurance umbrella covering all contractors on that project (Owner-Controlled or Contractor-Controlled Insurance Program).

- `projects.sponsor_id` → `sponsors.sponsor_id`
- `projects.broker_id` → `brokers.broker_id`

- `wrap_programs.project_id` → `projects.project_id`
- `wrap_programs.carrier_id` → `carriers.carrier_id`
- `wrap_programs.broker_id` → `brokers.broker_id`

**Cardinality:** one project → typically one wrap program (may be zero for non-wrapped projects).

---

## 3. Enrollment & Payroll

Contractors get enrolled into wrap programs; payroll is reported monthly against those enrollments (feeding premium calculation).

- `contractor_enrollments.program_id` → `wrap_programs.program_id`
- `contractor_enrollments.project_id` → `projects.project_id`
- `contractor_enrollments.contractor_id` → `contractors.contractor_id`

- `payroll_reports.enrollment_id` → `contractor_enrollments.enrollment_id`
- `payroll_reports.program_id` → `wrap_programs.program_id`
- `payroll_reports.contractor_id` → `contractors.contractor_id`

**Cardinality:**
- one wrap program → many enrollments (10–80 contractors typical)
- one enrollment → many payroll reports (one per report period)

---

## 4. Policies, Coverages, Endorsements, Premiums

The insurance layer. A **policy** is the legal contract; **coverages** are the coverage lines (GL, WC, Auto, Umbrella); **endorsements** are amendments; **premiums** are the invoicing.

- `policies.program_id` → `wrap_programs.program_id`
- `policies.project_id` → `projects.project_id`
- `policies.carrier_id` → `carriers.carrier_id`
- `policies.broker_id` → `brokers.broker_id`

- `policy_coverages.policy_id` → `policies.policy_id`
- `endorsements.policy_id` → `policies.policy_id`
- `premiums.policy_id` → `policies.policy_id`
- `premiums.program_id` → `wrap_programs.program_id`

**Cardinality:**
- one policy → many coverage lines (2–4 lines typical)
- one policy → many endorsements over its lifetime
- one policy → many premium invoices (quarterly or event-based)

---

## 5. Certificates & COI Verification

**Certificates of Insurance** are what contractors submit to prove they're covered. Verifications are the compliance team's review of each certificate.

- `certificates.enrollment_id` → `contractor_enrollments.enrollment_id`
- `certificates.contractor_id` → `contractors.contractor_id`
- `certificates.project_id` → `projects.project_id`

- `coi_verifications.certificate_id` → `certificates.certificate_id`
- `coi_verifications.contractor_id` → `contractors.contractor_id`
- `coi_verifications.project_id` → `projects.project_id`

**Cardinality:**
- one enrollment → one or more certificates (renewed on expiration)
- one certificate → typically one verification (occasionally more if follow-up is required)

---

## 6. Compliance Tracking & Prequalifications

**Compliance tracking** is the operational state of each enrollment across compliance dimensions (COI, WC, safety, etc.). **Prequalifications** are the annual contractor-level financial and safety reviews.

- `compliance_tracking.enrollment_id` → `contractor_enrollments.enrollment_id`
- `compliance_tracking.contractor_id` → `contractors.contractor_id`
- `compliance_tracking.project_id` → `projects.project_id`
- `compliance_tracking.program_id` → `wrap_programs.program_id`

- `prequalifications.contractor_id` → `contractors.contractor_id`

**Cardinality:**
- one contractor → one prequalification per year (renewed annually)
- one enrollment → multiple compliance records (one per compliance dimension: COI, WC, Safety, Financial…)

---

## 7. Safety & Inspections

Project-level safety data — incidents that occurred and inspections that were performed.

- `safety_incidents.project_id` → `projects.project_id`
- `safety_incidents.contractor_id` → `contractors.contractor_id`
- `safety_incidents.enrollment_id` → `contractor_enrollments.enrollment_id`

- `inspections.project_id` → `projects.project_id`

**Note:** Inspections attach to projects, not to specific contractors. Incidents attach to both.

---

## 8. Claims Lifecycle

The claims triangle: a **claim** is reported → **assessed** for coverage/liability → **payments** are made over its lifetime.

- `claims.policy_id` → `policies.policy_id`
- `claims.program_id` → `wrap_programs.program_id`
- `claims.project_id` → `projects.project_id`
- `claims.carrier_id` → `carriers.carrier_id`

- `claim_assessments.claim_id` → `claims.claim_id`
- `claim_assessments.policy_id` → `policies.policy_id`

- `claim_payments.claim_id` → `claims.claim_id`
- `claim_payments.policy_id` → `policies.policy_id`

**Cardinality:**
- one claim → typically one assessment (some may have revisions)
- one claim → many payments (initial indemnity + subsequent + expenses + recoveries)

---

## Reading Path — How the Data Flows

The natural reading order of the schema, from left to right:
---

## Key Join Patterns

Common paths reviewers of the SQL and Spark modules will see:

**Loss ratio by project type:**
`projects → wrap_programs → policies → premiums (LEFT JOIN) → claims (LEFT JOIN)`

**Contractor risk composite:**
`contractors → prequalifications → contractor_enrollments → compliance_tracking → safety_incidents (LEFT JOIN)`

**Expiring COI dashboard:**
`certificates → contractors → coi_verifications (latest per certificate)`

**Payroll audit variance:**
`payroll_reports → contractor_enrollments → wrap_programs`

These patterns show up repeatedly in Module 04 (SQL), Module 06 (warehouse), and Module 08 (Spark). Understanding this map makes reading those modules significantly faster.
