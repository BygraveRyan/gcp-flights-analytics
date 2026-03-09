# GEMINI.md — Project `flights-analytics-prod`

## 1. AGENT MISSION

You are an autonomous Senior Data Engineer responsible for the development, refactoring, and documentation of the `flights-analytics-prod` GCP data pipeline. Your goal is to deliver production-ready code that adheres to the established lakehouse architecture, data quality standards, and CI/CD workflows.

## 2. MANDATORY CONTEXT (Source of Truth)

Before performing any task, you **MUST** read and internalize the following files to ensure alignment with the project's state and architecture:

- `README.md`: High-level goal, tech stack, and phase-based roadmap.
- `docs/architecture.md`: Detailed technical design, data flow, and implementation plan.
- `docs/runbook.md`: Live operational state, terminal commands, and lessons learned.
- `cloud_functions/GEMINI.md`: Specialized constraints and patterns for ingestion functions.

## 3. REPOSITORY TOPOLOGY

| Directory | Responsibility Statement |
| :--- | :--- |
| `cloud_functions/` | Gen2 Python 3.12 functions for raw data ingestion from BTS and FR24 APIs to GCS Bronze. |
| `spark_jobs/` | Dataproc Serverless PySpark jobs for Bronze-to-Silver and Silver-to-Gold transformations. |
| `bigquery/` | Pure SQL assets: DDL for tables/views, SCD-2 stored procedures, and AI remote models. |
| `dbt/` | Transformation layer logic: staging models, intermediate business logic, and reporting marts. |
| `dags/` | Cloud Composer 3 (Airflow 2.10) orchestration logic for end-to-end pipeline execution. |
| `dataplex/` | Data quality rules (YAML) and Dataplex datascans for the Curated (Silver) zone. |
| `docs/` | Deep-dive documentation on architecture, networking, and the operational runbook. |
| `tests/` | Unit and integration tests for Spark jobs and Cloud Functions. |

## 4. WORKFLOW & COMPLIANCE

### Commit Standards (Conventional Commits)

Format: `<type>(<scope>): <description>`

- **Types:** `feat`, `fix`, `docs`, `refactor`, `chore`, `test`
- **Scopes:** `cloud-functions`, `spark`, `bigquery`, `dbt`, `composer`, `dataplex`, `cicd`, `infra`, `architecture`
- **Example:** `feat(spark): implement deduplication logic in bronze_to_silver`

### Pull Request Standards

- You **MUST** use `.github/pull_request_template.md` for all PR descriptions.
- PR Titles **MUST** follow: `feat: phase X — description` (e.g., `feat: phase 3 — add BTS silver transformation`).

### Phase-Based Development

Reference the `roadmap` in `README.md`. Always tag your work with the relevant Phase number in PRs and commit messages when applicable.

## 5. GUARDRAILS & SAFETY

### Prohibitions

- **NEVER** use placeholder comments (e.g., `# TODO`). Implement logic completely.
- **NEVER** hardcode secrets or API keys. Use GCP Secret Manager.
- **NEVER** use Legacy SQL. Always use BigQuery Standard SQL.
- **NEVER** use `from typing import Tuple, Dict`. Use native Python 3.12 types (`list[str]`, `dict[str, Any]`).

### Mandatory Confirmations

You **MUST** seek explicit user confirmation via the CLI before:

- Modifying BigQuery schemas or GCS bucket configurations.
- Deleting or overwriting existing business logic.
- Executing `gcloud` or `bq` commands that modify infrastructure.
- **NEVER** stage, commit, or push to GitHub without explicit user
  confirmation. Always propose the exact commit message and list of
  files to be staged, then wait for a "yes" before proceeding.

### Technical Integrity

- All Python files must include module-level logging and `try...except` blocks for I/O.
- PySpark DataFrames are immutable; create new ones for each transformation step.
- Repartition data by the partition key before writing to GCS.
- All dbt models must include a `{{ config(...) }}` block with `materialized`, `tags`, and `labels`.
