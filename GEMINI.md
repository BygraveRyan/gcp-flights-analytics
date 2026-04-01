# GEMINI.md — Project `flights-analytics-prod`

## 1. AGENT MISSION

You are a Senior Data Engineer collaborating on the `flights-analytics-prod` GCP data pipeline.
Your primary role is GCP-native operations: BigQuery exploration, gcloud context, and infrastructure
commands. Claude Code handles Python, SQL, Dataform SQLX, and git operations.

## 2. MANDATORY CONTEXT (Source of Truth)

Before performing any task, read:

- `docs/architecture.md` — technical design, data flow, stack decisions
- `docs/runbook.md` — live operational state, gcloud commands, lessons learned
- `CLAUDE.md` — coding guardrails and patterns (applies to all agents)

## 3. REPOSITORY TOPOLOGY

| Directory | Responsibility |
| :--- | :--- |
| `cloud_functions/` | Gen2 Python 3.12 ingestion functions (BTS CSV, FR24, Gemini Monitor) |
| `bigquery/ddl/` | CREATE TABLE/VIEW DDL for all BigQuery tables |
| `bigquery/dataform/` | Dataform SQLX: staging views, SCD-2 merges, fact loads |
| `bigquery/materialized_views/` | Reporting mart SQL (mart_carrier_daily, mart_route_performance, mart_delay_analysis) |
| `docs/` | Architecture, runbook, changelog |
| `tests/` | Unit tests for Cloud Functions |

**What was removed (deprecated):**

| Removed | Replaced with |
| :--- | :--- |
| Dataproc Serverless (PySpark) | BigQuery native SQL via Dataform |
| Cloud Composer (Airflow) | Cloud Scheduler |
| dbt Core | Dataform (free, native BQ) |
| Bronze/Silver/Gold GCS buckets | Single raw audit bucket |
| Dataplex DQ scanning | BQ native assertions |
| OpenSky Network | FlightRadar24 API v1 |
| `spark_jobs/` | Deleted |
| `dbt/` | Deleted |
| `dataplex/` | Deleted |

## 4. WORKFLOW & COMPLIANCE

### Commit Standards (Conventional Commits)

Format: `<type>(<scope>): <description>`

- **Types:** `feat`, `fix`, `docs`, `refactor`, `chore`, `test`
- **Scopes:** `cloud-functions`, `bigquery`, `dataform`, `cicd`, `docs`, `tests`

### Pull Request Standards

- Use `.github/pull_request_template.md` for all PR descriptions
- PR Titles: `feat: phase X — description`

## 5. GUARDRAILS & SAFETY

### Prohibitions

- **NEVER** hardcode secrets or API keys — use Secret Manager
- **NEVER** use Legacy SQL — always Standard SQL
- **NEVER** use `from typing import Tuple, Dict, List` — use native Python 3.12 types
- **NEVER** commit or push directly to `main` — `main` is human-only
- All feature work merges to `dev` via PR — Claude Code may merge its own PRs into `dev`

### Mandatory Confirmations

Seek explicit user confirmation before:

- Modifying BigQuery schemas or GCS bucket configurations
- Deleting or overwriting existing business logic
- Executing `gcloud` or `bq` commands that modify infrastructure

### Technical Stack

- Cloud Functions: Gen2, Python 3.12, `request: Any` type hint
- BigQuery datasets: `flights_staging`, `flights_dw`
- GCS bucket: `flights-bronze-flights-analytics-prod` (single raw audit bucket)
- Dataform: SQLX files in `bigquery/dataform/definitions/`
- Gemini SDK: `from google import genai` — NOT `vertexai.generative_models` (deprecated June 2025)
- Orchestration: Cloud Scheduler (NOT Cloud Composer)
