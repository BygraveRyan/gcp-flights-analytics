# CLAUDE.md — GCP Flights Analytics Pipeline

## 1. Agent Mission

All actions are governed by strict engineering standards.

- Produce clean, idiomatic Python 3.12 and GoogleSQL.
- Always propose terminal commands for the human to run — never execute
  `gcloud`, `bq`, `gsutil`, or `git merge` yourself.
- Default to the smallest change that satisfies the requirement.
- Treat every DDL change as a migration: schema-safe and reversible.

---

## 2. Stack

| Layer           | Technology                                              |
|-----------------|---------------------------------------------------------|
| Cloud           | Google Cloud Platform — region `europe-west2` (London) |
| Ingestion       | Cloud Functions Gen2 (Python 3.12)                      |
| Raw storage     | Google Cloud Storage (Bronze / Silver / Gold buckets)   |
| Warehouse       | BigQuery (partitioned + clustered tables, SCD-2)        |
| Transformation  | Dataform (SQL workflows, scheduling, assertions)        |
| Orchestration   | Cloud Scheduler (trigger Cloud Functions & Dataform)    |
| Dashboards      | Looker Studio Pro + Conversational Analytics            |
| AI Monitoring   | `google-genai` SDK — Gemini models                      |
| CI/CD           | GitHub Actions                                          |
| Data Quality    | Dataplex Universal Catalog                              |

---

## 3. Repository Topology

```
cloud_functions/              # Gen2 HTTP/Pub-Sub functions — one sub-dir per source
bigquery/ddl/                 # CREATE TABLE / VIEW DDL; apply via bq CLI, never in-place edits
bigquery/dataform/            # Dataform project — sqlx models, assertions, schedules
bigquery/materialized_views/  # Standalone materialized-view DDL outside Dataform
.github/workflows/            # CI/CD pipelines — lint, unit tests, deploy gates
tests/unit/                   # pytest unit tests; no live GCP calls, no mocks of BQ schema
docs/                         # Architecture diagrams, ADRs, pipeline runbooks
```

---

## 4. Star Schema

The BigQuery warehouse uses a **star schema** centred on two fact tables.

| Table            | Grain                            | Notes                                                                                          |
|------------------|----------------------------------|------------------------------------------------------------------------------------------------|
| `fact_flights`   | One flight segment               | Links to all four dims; partitioned on `flight_date`                                           |
| `fact_positions` | One FR24 position record         | High-volume; partitioned on `position_ts` (DATE)                                               |
| `dim_date`       | One calendar day                 | Static spine 2020-2030; never SCD                                                              |
| `dim_carrier`    | One carrier version              | SCD Type 2; surrogate key `carrier_sk`                                                         |
| `dim_airport`    | One airport version              | SCD Type 2; **role-playing** dim — joined twice on `fact_flights` as `origin_airport_sk` and `destination_airport_sk` |

---

## 5. Commit Standards

Use **Conventional Commits** format: `<type>(<scope>): <subject>`

**Types:** `feat` · `fix` · `docs` · `refactor` · `chore` · `test`

**Scopes:**

| Scope              | When to use                                      |
|--------------------|--------------------------------------------------|
| `cloud-functions`  | Changes inside `cloud_functions/`                |
| `bigquery`         | DDL, stored procs, remote models                 |
| `dataform`         | Anything inside `bigquery/dataform/`             |
| `composer`         | DAG files in `dags/`                             |
| `cicd`             | `.github/workflows/`                             |
| `infra`            | Terraform / gcloud infrastructure                |
| `docs`             | `docs/`, `README.md`, `CLAUDE.md`                |

Example: `feat(cloud-functions): add retry logic to ingest_fr24`

---

## 6. Git Workflow

### Branch strategy

| Branch | Purpose |
| ------ | ------- |
| `main` | Production only — never commit directly |
| `dev` | Integration branch — all feature PRs target here |
| `feat/<short-description>` | All new work (e.g. `feat/bigquery-ddl`, `feat/dataform-setup`) |

### Claude Code git permissions

Claude Code **may** run:

- `git checkout -b feat/<name>` — create a feature branch
- `git add` — stage changes
- `git commit` — commit using Conventional Commits format
- `git push origin feat/<name>` — push the feature branch
- `gh pr create` — open a PR targeting `dev`

### Human responsibilities

- Review and approve PRs on GitHub
- `gh pr merge --squash` — merge feature PRs into `dev`
- Periodically merge `dev` into `main` via a PR
- All `gcloud`, `bq`, and `gsutil` commands

### Claude Code must NEVER

- Push directly to `main` or `dev`
- Merge any PR
- Run infrastructure commands (`gcloud`, `bq`, `gsutil`)

---

## 7. Guardrails

### Never do autonomously
- Run `gcloud`, `bq`, `gsutil`, or `git merge` — always propose the command for the human.
- Hardcode secrets, API keys, or project IDs — use Secret Manager references or env vars.
- Write Legacy SQL (`#legacySQL`) — always GoogleSQL (standard SQL).

### Python rules
- Cloud Functions entry points must type-hint the request parameter as
  `flask.Request`, **not** `functions_framework.Request`.
- Use native Python 3.12 built-in types (`list[str]`, `dict[str, int]`, `tuple`,
  `X | None`) — do **not** import from the `typing` module (`List`, `Dict`,
  `Optional`, etc.).
- One Cloud Function per sub-directory under `cloud_functions/`; each has its
  own `requirements.txt` and `main.py`.

### SQL rules
- All DDL must be idempotent (`CREATE OR REPLACE` / `IF NOT EXISTS`).
- Partition and cluster every fact table; document the rationale in a comment.
- SCD-2 merges go in `bigquery/stored_procs/` as named stored procedures.
