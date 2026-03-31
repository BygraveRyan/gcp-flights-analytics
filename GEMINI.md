# GEMINI.md — gcp-flights-analytics

## Agent Overview

This repository is the source of truth for the `flights-analytics-prod` data platform. The architecture was refactored from an overengineered Spark/dbt/Dataplex lakehouse to a right-sized Cloud Functions + BigQuery + Dataform stack — reducing cost from ~£65/month to £2–5/month.

## Read First

Always start with:
- `README.md` — architecture overview and refactor rationale
- `CLAUDE.md` — agent permissions, branch strategy, guardrails

Load on demand when relevant:
- `docs/runbook.md` — live infrastructure and operational context
- `docs/architecture_summary.md` — current target-state design
- `.github/pull_request_template.md` — when preparing a PR

## Repo Map

```
cloud_functions/              # Gen2 ingestion — ingest_bts_csv, ingest_fr24, gemini_monitor
bigquery/ddl/                 # CREATE OR REPLACE TABLE DDL — apply via bq CLI
bigquery/dataform/            # Dataform project — staging views, SCD-2 MERGEs, incremental facts
bigquery/materialized_views/  # Looker Studio mart views
.github/workflows/            # CI: PR quality checks + prod deploy via Workload Identity
tests/unit/                   # pytest unit tests — no live GCP calls
docs/                         # Architecture, runbook, changelog
```

## Current Stack

| Layer | Technology |
|---|---|
| Ingestion | Cloud Functions Gen2 (Python 3.12) |
| Raw Storage | GCS — single Bronze bucket (365d TTL) |
| Warehouse | BigQuery — partitioned + clustered, SCD Type 2 |
| Transformation | Dataform (SQLX) |
| Orchestration | Cloud Scheduler |
| Dashboards | Looker Studio Pro + Conversational Analytics |
| AI Monitoring | Gemini 2.5 Pro via `google-genai` SDK |
| CI/CD | GitHub Actions + Workload Identity Federation |

## Commit & PR Standards

Use Conventional Commits: `<type>(<scope>): <description>`

Valid scopes: `cloud-functions` · `bigquery` · `dataform` · `cicd` · `infra` · `docs`

PR descriptions must follow `.github/pull_request_template.md` (Why / How / Impact framework).

## Operational Guardrails

- Never run `gcloud`, `bq`, `gsutil`, or `git merge` — always propose for human execution
- No secrets, API keys, or project IDs hardcoded — Secret Manager and env vars only
- All new work on `feat/<name>` branches, PRs targeting `dev`
- Never push directly to `main` or `dev`
- Treat every DDL change as a migration: schema-safe and idempotent

## What Was Removed (Do Not Recreate)

The following were deleted during the architectural refactor and must not be recreated:

| Removed | Reason |
|---|---|
| `spark_jobs/` | Over-engineered for 600K rows/month; Cloud Functions are sufficient |
| `dbt/` | Replaced by Dataform — same capability, zero additional cost |
| `vertex_ai/` | No ML workload exists; speculative infrastructure |
| `dataplex/` | DQ layer removed in favour of Dataform assertions |
| VPC Connector | Was in ERROR state, costing ~£8/month unnecessarily |
