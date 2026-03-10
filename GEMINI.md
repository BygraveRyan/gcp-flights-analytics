# GEMINI.md — flights-analytics-prod

## Agent Overview

This repository is the source of truth for the `flights-analytics-prod` data platform and its AI workflow. Keep persistent context here thin, keep detailed procedures in workspace skills, and treat Obsidian notes only as mirrors of repo state.

## Read First

Always start with:
- `README.md`
- `docs/architecture_summary.md`
- `docs/changelog.md`

Load on demand when relevant:
- `docs/runbook.md` for live infrastructure and operational context
- `docs/architecture.md` for deeper target-state design
- `.github/pull_request_template.md` when preparing a PR
- `cloud_functions/GEMINI.md` when editing ingestion functions

## Repo Map

- `cloud_functions/`: Gen2 ingestion functions for BTS, FR24, and legacy OpenSky assets
- `spark_jobs/`: Dataproc Serverless PySpark jobs
- `bigquery/`: DDL, stored procedures, and Gemini monitoring SQL
- `dbt/`: warehouse transformation models
- `dataplex/`: data quality rules
- `dags/`: orchestration folder; currently no DAG files are committed
- `docs/`: architecture, runbook, summaries, changelog, and mirror notes
- `tests/`: unit coverage

## Architecture Summary

The repo implements a GCP lakehouse pipeline: ingestion functions land raw data in GCS Bronze, Spark promotes Bronze data toward curated layers, and BigQuery/dbt/Dataplex provide warehouse, transformation, and data quality assets. Some layers described in long-form docs are planned or partial, so verify repo contents before describing a component as implemented.

## Phase Conventions

The project uses phase labels in `README.md`, but the roadmap can lag or lead the committed code. When using a phase in docs, commits, or PRs, verify the touched components against the current repo state first.

## Commit And PR Standards

- Use conventional commits: `<type>(<scope>): <description>`
- Existing scopes in repo materials include `cloud-functions`, `spark`, `bigquery`, `dbt`, `composer`, `dataplex`, `cicd`, `infra`, and `architecture`
- PR descriptions should follow `.github/pull_request_template.md`
- For non-trivial work, reference the matching file in `.ai/change_plans/` from the PR description

## Operational Guardrails

- Repo files are canonical; Obsidian mirror notes are never the source of truth
- Keep `GEMINI.md` thin and persistent; put procedures, templates, and checklists in skills
- Use `change-planner` for multi-file, architectural, schema, infrastructure, or cross-directory work
- Use `docs-maintainer` when architecture, pipeline shape, schema, infrastructure, or major phase state changes
- Distinguish clearly between implemented, partial, and planned components
- Do not run infrastructure-changing commands or git stage/commit/push operations without explicit approval

## Skill Routing

Preferred workspace skills live in `.agents/skills/`. The repo also contains older `.gemini/skills/` skills; leave them intact unless the task explicitly migrates them.

- `change-planner`: create or update concise implementation plans in `.ai/change_plans/`
- `docs-maintainer`: maintain `docs/architecture_summary.md` and `docs/changelog.md`
- `pr-author`: draft PR content from repo truth and the PR template
- `obsidian-mirror`: refresh dashboard-style mirror notes without creating a second system of record
