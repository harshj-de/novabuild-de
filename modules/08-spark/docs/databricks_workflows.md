# Section 8.12 — Databricks Workflows (Lakeflow Jobs)

**Note (2026):** Databricks renamed "Databricks Jobs" to **Lakeflow Jobs** in the May 2026 release. Both terms refer to the same thing.

This is a text-and-diagrams section, not runnable code — you configure Workflows through the Databricks UI or via the REST API / Terraform, not Python.

---

## What Workflows are

A **Job** is a pipeline definition. A pipeline is one or more **Tasks** organised into a DAG. Each Task can be:

- A notebook run
- A Python script
- A JAR
- A SQL script
- A dbt project run
- Another Job (nested)

Tasks have **dependencies** — Task B runs only after Task A succeeds. Multi-task Jobs are how you orchestrate anything meaningful on Databricks.

---

## Simple pipeline shape

```
        [ 1. Bronze Ingest ]
                │
                ▼
        [ 2. Silver Clean ]
                │
       ┌────────┴────────┐
       ▼                 ▼
[ 3a. Gold Risk ]   [ 3b. Gold Monthly ]
       │                 │
       └────────┬────────┘
                ▼
        [ 4. Data Quality Checks ]
                │
                ▼
        [ 5. Refresh Dashboard ]
```

- Task 1 fails → nothing downstream runs. Errors are contained.
- Task 3a fails but 3b succeeds → 3a can retry independently.
- Task 4 is a data-quality gate. If contracts fail, Task 5 is skipped.

---

## Job compute options

Every task runs on a **cluster**. Three choices:

| Type | When to use |
|---|---|
| **Job cluster (dedicated)** | Default. Spins up per run, tears down after. Cheapest for scheduled jobs. |
| **All-purpose cluster (shared)** | Interactive work / notebook development. More expensive because it's always warm. |
| **Serverless (2024+)** | Fast startup, auto-scaling, managed by Databricks. Best-fit for most workloads. |

**Rule of thumb:** Job clusters for scheduled jobs, Serverless for ad-hoc or fast-startup needs. Only use all-purpose for interactive dev.

---

## Retry policies

Every task has retry settings:

```
Max retries:       3
Retry interval:    30 seconds
Retry on timeout:  yes
Fail on max retries: yes
```

Real jobs need these. External APIs go down. S3 has 5xx blips. Databricks compute sometimes takes 3 tries to start.

---

## Notifications

Standard destinations for alerts:

- Email (start / success / failure / duration threshold)
- Slack (via webhook)
- PagerDuty (for on-call)
- Custom webhook (for any HTTP endpoint)

**Rule of thumb:** notify on FAILURE always; SLA MISS (job takes 2x expected time) sometimes; SUCCESS almost never (dashboard fatigue).

---

## Scheduling

Cron-based or continuous:

```
Cron:       0 2 * * *          (daily at 2 AM)
Continuous: run one after another with no gap  (streaming pattern)
File arrival: run when new file lands (event-driven)
```

The Medallion pipeline from `capstone/medallion_pipeline.py` is typically Cron-scheduled: `0 2 * * *` (daily 2 AM). Streaming pipelines use Continuous mode.

---

## Parametrisation

Jobs accept parameters at run time. Useful for backfills:

```
Parameter: --ingestion-date
Default value: {{start_date}}     (built-in variable)
```

Then in your notebook:
```python
dbutils.widgets.text("ingestion_date", "")
target_date = dbutils.widgets.get("ingestion_date")
```

A backfill is just running the job with parameter overrides.

---

## Declarative Automation Bundles (DABs)

**Note (2026):** Databricks Asset Bundles renamed to **Declarative Automation Bundles (DABs)** in the May 2026 release.

DABs let you define Jobs (and everything else — clusters, dashboards, MLflow experiments) as YAML. Committed to Git. Deployed via CLI.

```yaml
resources:
  jobs:
    medallion_pipeline:
      name: NovaBuild Medallion Pipeline
      schedule:
        quartz_cron_expression: "0 0 2 * * ?"
      tasks:
        - task_key: bronze_ingest
          notebook_task:
            notebook_path: /Repos/harshj/nova/bronze_ingest
        - task_key: silver_clean
          depends_on:
            - task_key: bronze_ingest
          notebook_task:
            notebook_path: /Repos/harshj/nova/silver_clean
```

DABs are the modern deployment pattern. Everything as code, CI/CD friendly. Older jobs configured via the UI still work but are considered legacy.

---

## When you'd migrate from something else

Common pre-Databricks orchestrators and their migration paths:

| From | Notes |
|---|---|
| **Airflow** | Both can coexist. Airflow calls Databricks jobs via the REST API operator. Some teams keep Airflow for cross-tool orchestration and use Workflows for pure-Databricks pipelines. |
| **Azure Data Factory** | Full replacement possible with Workflows + DABs. |
| **AWS Step Functions / Glue** | Replace Glue Workflows with Databricks Workflows; Step Functions can still orchestrate at higher level if needed. |
| **Prefect / Dagster** | Same coexistence pattern as Airflow. |

---

## Skills demonstrated

`Databricks Jobs / Lakeflow Jobs` · `multi-task DAG with dependency chains` · `Job vs All-purpose vs Serverless compute selection` · `retry policies + failure notifications` · `Cron / continuous / file-arrival triggers` · `parametrised runs for backfills` · `Declarative Automation Bundles (DABs) as YAML` · `Airflow / ADF / Prefect coexistence patterns`

---

## Where this leads

Module 09 (Kafka) covers the streaming source side. Module 10 (Airflow) covers the orchestration alternative to Workflows. Module 11 (Azure DE + DP-203) covers Azure Data Factory as the equivalent tool in Microsoft's stack.
