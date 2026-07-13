-- ══════════════════════════════════════════════════════════════════════════════
-- NovaBuild Risk Management — PostgreSQL Schema
-- Domain: Commercial Construction Insurance
-- Tables: 21  |  Rows: ~76,500  |  Date range: 2021–2024
-- ══════════════════════════════════════════════════════════════════════════════
--
-- To reproduce the full dataset:
--   1. Provision a PostgreSQL 15 database
--   2. Run this file to create all 21 tables
--   3. Run the seed script (arrives with Module 03 migration)
--
-- ══════════════════════════════════════════════════════════════════════════════

-- Drop existing tables (safe re-run)
DROP TABLE IF EXISTS
    claim_payments, claim_assessments, claims,
    inspections, safety_incidents,
    prequalifications, compliance_tracking,
    coi_verifications, certificates,
    premiums, endorsements, policy_coverages, policies,
    payroll_reports, contractor_enrollments, wrap_programs,
    projects, contractors, sponsors, brokers, carriers
CASCADE;

-- ── Reference / Master Layer ──────────────────────────────────────────────────

CREATE TABLE carriers (
    carrier_id          TEXT PRIMARY KEY,
    carrier_name        TEXT NOT NULL,
    am_best_rating      TEXT,
    state_licensed      TEXT,
    contact_name        TEXT,
    contact_email       TEXT,
    contact_phone       TEXT,
    active              BOOLEAN DEFAULT TRUE
);

CREATE TABLE brokers (
    broker_id           TEXT PRIMARY KEY,
    broker_name         TEXT NOT NULL,
    firm_name           TEXT,
    license_number      TEXT,
    state               TEXT,
    email               TEXT,
    phone               TEXT,
    years_experience    INTEGER,
    specialty           TEXT,
    active              BOOLEAN DEFAULT TRUE
);

CREATE TABLE sponsors (
    sponsor_id          TEXT PRIMARY KEY,
    company_name        TEXT NOT NULL,
    industry            TEXT,
    state               TEXT,
    contact_name        TEXT,
    contact_email       TEXT,
    contact_phone       TEXT,
    annual_construction_volume NUMERIC(18,2),
    tier                TEXT,
    created_at          DATE
);

CREATE TABLE contractors (
    contractor_id       TEXT PRIMARY KEY,
    company_name        TEXT NOT NULL,
    trade               TEXT,
    state               TEXT,
    license_number      TEXT,
    contact_name        TEXT,
    contact_email       TEXT,
    contact_phone       TEXT,
    employees_count     INTEGER,
    years_in_business   INTEGER,
    annual_revenue      NUMERIC(18,2),
    emr                 NUMERIC(4,2),
    tier                TEXT,
    created_at          DATE
);

-- ── Projects & Wrap Programs ──────────────────────────────────────────────────

CREATE TABLE projects (
    project_id          TEXT PRIMARY KEY,
    project_name        TEXT NOT NULL,
    project_type        TEXT,
    sponsor_id          TEXT REFERENCES sponsors(sponsor_id),
    broker_id           TEXT REFERENCES brokers(broker_id),
    state               TEXT,
    city                TEXT,
    start_date          DATE,
    projected_end_date  DATE,
    actual_end_date     DATE,
    total_insured_value NUMERIC(18,2),
    contract_value      NUMERIC(18,2),
    status              TEXT,
    wrap_type           TEXT,
    created_at          DATE
);

CREATE TABLE wrap_programs (
    program_id          TEXT PRIMARY KEY,
    project_id          TEXT REFERENCES projects(project_id),
    carrier_id          TEXT REFERENCES carriers(carrier_id),
    broker_id           TEXT REFERENCES brokers(broker_id),
    program_name        TEXT,
    program_type        TEXT,
    program_start       DATE,
    program_end         DATE,
    estimated_payroll   NUMERIC(18,2),
    actual_payroll      NUMERIC(18,2),
    enrolled_contractors INTEGER DEFAULT 0,
    status              TEXT,
    created_at          DATE
);

-- ── Enrollment & Payroll ──────────────────────────────────────────────────────

CREATE TABLE contractor_enrollments (
    enrollment_id       TEXT PRIMARY KEY,
    program_id          TEXT REFERENCES wrap_programs(program_id),
    project_id          TEXT REFERENCES projects(project_id),
    contractor_id       TEXT REFERENCES contractors(contractor_id),
    enrollment_date     DATE,
    scope_of_work       TEXT,
    subcontract_value   NUMERIC(18,2),
    estimated_payroll   NUMERIC(18,2),
    status              TEXT,
    withdrawal_date     DATE,
    created_at  DATE
);

CREATE TABLE payroll_reports (
    payroll_id          TEXT PRIMARY KEY,
    enrollment_id       TEXT REFERENCES contractor_enrollments(enrollment_id),
    program_id          TEXT REFERENCES wrap_programs(program_id),
    contractor_id       TEXT REFERENCES contractors(contractor_id),
    report_period       DATE,
    reported_payroll    NUMERIC(18,2),
    audited_payroll     NUMERIC(18,2),
    employee_count      INTEGER,
    submission_date     DATE,
    audit_date          DATE,
    status              TEXT
);

-- ── Policies, Coverages, Endorsements, Premiums ───────────────────────────────

CREATE TABLE policies (
    policy_id           TEXT PRIMARY KEY,
    policy_number       TEXT UNIQUE,
    program_id          TEXT REFERENCES wrap_programs(program_id),
    project_id          TEXT REFERENCES projects(project_id),
    carrier_id          TEXT REFERENCES carriers(carrier_id),
    broker_id           TEXT REFERENCES brokers(broker_id),
    policy_type         TEXT,
    effective_date      DATE,
    expiration_date     DATE,
    total_insured_value NUMERIC(18,2),
    annual_premium      NUMERIC(18,2),
    deductible          NUMERIC(18,2),
    status              TEXT,
    created_at          DATE
);

CREATE TABLE policy_coverages (
    coverage_id         TEXT PRIMARY KEY,
    policy_id           TEXT REFERENCES policies(policy_id),
    coverage_line       TEXT,
    coverage_limit      NUMERIC(18,2),
    per_occurrence_limit NUMERIC(18,2),
    aggregate_limit     NUMERIC(18,2),
    premium_allocation  NUMERIC(18,2),
    effective_date      DATE,
    expiration_date     DATE,
    status              TEXT
);

CREATE TABLE endorsements (
    endorsement_id      TEXT PRIMARY KEY,
    policy_id           TEXT REFERENCES policies(policy_id),
    endorsement_number  TEXT,
    endorsement_type    TEXT,
    effective_date      DATE,
    description         TEXT,
    premium_change      NUMERIC(18,2),
    issued_by           TEXT,
    status              TEXT,
    created_at          DATE
);

CREATE TABLE premiums (
    premium_id          TEXT PRIMARY KEY,
    policy_id           TEXT REFERENCES policies(policy_id),
    program_id          TEXT REFERENCES wrap_programs(program_id),
    invoice_number      TEXT,
    invoice_date        DATE,
    due_date            DATE,
    amount_due          NUMERIC(18,2),
    amount_paid         NUMERIC(18,2),
    payment_date        DATE,
    payment_method      TEXT,
    status              TEXT,
    created_at          DATE
);

-- ── Certificates & COI Verification ───────────────────────────────────────────

CREATE TABLE certificates (
    certificate_id      TEXT PRIMARY KEY,
    enrollment_id       TEXT REFERENCES contractor_enrollments(enrollment_id),
    contractor_id       TEXT REFERENCES contractors(contractor_id),
    project_id          TEXT REFERENCES projects(project_id),
    certificate_number  TEXT,
    issuing_agent       TEXT,
    holder_name         TEXT,
    issue_date          DATE,
    expiration_date     DATE,
    gl_limit            NUMERIC(18,2),
    wc_limit            NUMERIC(18,2),
    auto_limit          NUMERIC(18,2),
    umbrella_limit      NUMERIC(18,2),
    status              TEXT,
    submitted_via       TEXT,
    created_at          DATE
);

CREATE TABLE coi_verifications (
    verification_id     TEXT PRIMARY KEY,
    certificate_id      TEXT REFERENCES certificates(certificate_id),
    contractor_id       TEXT REFERENCES contractors(contractor_id),
    project_id          TEXT REFERENCES projects(project_id),
    verification_date   DATE,
    verified_by         TEXT,
    result              TEXT,
    gl_compliant        BOOLEAN,
    wc_compliant        BOOLEAN,
    auto_compliant      BOOLEAN,
    umbrella_compliant  BOOLEAN,
    deficiency_notes    TEXT,
    review_time_minutes NUMERIC(6,1),
    follow_up_required  BOOLEAN,
    resolved_date       DATE,
    created_at          DATE
);

-- ── Compliance Tracking & Prequalifications ───────────────────────────────────

CREATE TABLE compliance_tracking (
    compliance_id       TEXT PRIMARY KEY,
    enrollment_id       TEXT REFERENCES contractor_enrollments(enrollment_id),
    contractor_id       TEXT REFERENCES contractors(contractor_id),
    project_id          TEXT REFERENCES projects(project_id),
    program_id          TEXT REFERENCES wrap_programs(program_id),
    compliance_type     TEXT,
    current_status      TEXT,
    last_reviewed_date  DATE,
    next_review_date    DATE,
    days_until_expiry   INTEGER,
    auto_flagged        BOOLEAN,
    assigned_to         TEXT,
    notes               TEXT,
    created_at          DATE
);

CREATE TABLE prequalifications (
    prequal_id              TEXT PRIMARY KEY,
    contractor_id           TEXT REFERENCES contractors(contractor_id),
    review_date             DATE,
    expiry_date             DATE,
    overall_score           INTEGER,
    financial_score         INTEGER,
    safety_score            INTEGER,
    experience_score        INTEGER,
    insurance_score         INTEGER,
    status                  TEXT,
    reviewed_by             TEXT,
    annual_revenue_verified NUMERIC(18,2),
    bonding_capacity        NUMERIC(18,2),
    emr_at_review           NUMERIC(4,2),
    notes                   TEXT,
    created_at              DATE
);

-- ── Safety & Inspections ──────────────────────────────────────────────────────

CREATE TABLE safety_incidents (
    incident_id         TEXT PRIMARY KEY,
    project_id          TEXT REFERENCES projects(project_id),
    contractor_id       TEXT REFERENCES contractors(contractor_id),
    enrollment_id       TEXT REFERENCES contractor_enrollments(enrollment_id),
    incident_date       DATE,
    incident_type       TEXT,
    severity            TEXT,
    injured_count       INTEGER,
    fatality_count      INTEGER,
    lost_days           INTEGER,
    description         TEXT,
    root_cause          TEXT,
    osha_recordable     BOOLEAN,
    osha_reported       BOOLEAN,
    corrective_action   TEXT,
    closed_date         DATE,
    created_at          DATE
);

CREATE TABLE inspections (
    inspection_id       TEXT PRIMARY KEY,
    project_id          TEXT REFERENCES projects(project_id),
    inspection_date     DATE,
    inspector_name      TEXT,
    inspection_type     TEXT,
    score               INTEGER,
    result              TEXT,
    violations_found    INTEGER,
    critical_violations INTEGER,
    corrective_actions_required INTEGER,
    follow_up_required  BOOLEAN,
    follow_up_date      DATE,
    notes               TEXT,
    created_at          DATE
);

-- ── Claims Lifecycle ──────────────────────────────────────────────────────────

CREATE TABLE claims (
    claim_id            TEXT PRIMARY KEY,
    claim_number        TEXT UNIQUE,
    policy_id           TEXT REFERENCES policies(policy_id),
    program_id          TEXT REFERENCES wrap_programs(program_id),
    project_id          TEXT REFERENCES projects(project_id),
    carrier_id          TEXT REFERENCES carriers(carrier_id),
    loss_date           DATE,
    report_date         DATE,
    claim_type          TEXT,
    coverage_line       TEXT,
    claimant_name       TEXT,
    claimant_type       TEXT,
    description         TEXT,
    reserves            NUMERIC(18,2),
    incurred_loss       NUMERIC(18,2),
    status              TEXT,
    adjuster_name       TEXT,
    litigation          BOOLEAN,
    subrogation_potential BOOLEAN,
    created_at          DATE
);

CREATE TABLE claim_assessments (
    assessment_id       TEXT PRIMARY KEY,
    claim_id            TEXT REFERENCES claims(claim_id),
    policy_id           TEXT REFERENCES policies(policy_id),
    assessment_date     DATE,
    assessed_by         TEXT,
    coverage_confirmed  BOOLEAN,
    liability_determination TEXT,
    initial_reserve     NUMERIC(18,2),
    revised_reserve     NUMERIC(18,2),
    recommended_action  TEXT,
    investigation_required BOOLEAN,
    fraud_indicators    BOOLEAN,
    notes               TEXT,
    created_at          DATE
);

CREATE TABLE claim_payments (
    payment_id          TEXT PRIMARY KEY,
    claim_id            TEXT REFERENCES claims(claim_id),
    policy_id           TEXT REFERENCES policies(policy_id),
    payment_date        DATE,
    payment_type        TEXT,
    amount              NUMERIC(18,2),
    payee_name          TEXT,
    payee_type          TEXT,
    payment_method      TEXT,
    check_number        TEXT,
    approved_by         TEXT,
    recovery_amount     NUMERIC(18,2),
    status              TEXT,
    created_at          DATE
);
