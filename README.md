# GCP Flights Analytics Pipeline

An end-to-end, production-style cloud data engineering platform on **Google Cloud Platform**.
Ingests live aviation data, models it into a star schema warehouse, and delivers analytics
and AI-generated monitoring through Looker Studio.

---

## Recruiter Panel

| Attribute | Value |
| --- | --- |
| **Role target** | Data Engineer / Cloud Data Engineer |
| **Cloud** | Google Cloud Platform — `europe-west2` |
| **Core skills demonstrated** | Cloud Functions (Gen2), BigQuery, Dataform, GCS, IAM, CI/CD |
| **Warehouse pattern** | Star schema with SCD Type 2 dimensions |
| **AI integration** | Gemini 2.5 Pro via `google-genai` SDK for pipeline monitoring |
| **Code standards** | Python 3.12 native types, GoogleSQL, Conventional Commits, flake8, sqlfluff |
| **Testing** | pytest unit tests, GitHub Actions CI on every PR |

---

## AI-Driven Development

This project is built using a **Human-in-the-Loop AI workflow**. All engineering decisions
are made by the human; AI agents (Claude Code, Gemini CLI) are used as accelerators under
strict guardrails defined in `CLAUDE.md`.

- Every terminal command that touches GCP is proposed by the agent and run by the human.
- No secrets, API keys, or project IDs are hardcoded — env vars and Secret Manager only.
- Conventional Commits with defined scopes keep history clean and auditable.

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Cloud | Google Cloud Platform — `europe-west2` (London) |
| Ingestion | Cloud Functions Gen2 (Python 3.12) |
| Raw Storage | Google Cloud Storage (Bronze bucket) |
| Warehouse | BigQuery — partitioned + clustered tables, SCD Type 2 |
| Transformation | Dataform — SQLX models, incremental loads, SCD-2 MERGEs |
| Orchestration | Cloud Scheduler |
| Dashboards | Looker Studio Pro + Conversational Analytics |
| AI Monitoring | Gemini 2.5 Pro via `google-genai` SDK |
| Data Quality | Dataplex Universal Catalog |
| CI/CD | GitHub Actions — flake8, pytest, sqlfluff, gcloud deploy |

---

## Architecture

```text
BTS API (CSV)  ──┐
                 ├──► Cloud Functions (Gen2) ──► GCS Bronze ──► BigQuery Staging
FR24 API ────────┘                                                      │
                                                                         ▼
                                                              Dataform (SQLX)
                                                       SCD-2 dims + incremental facts
                                                                         │
                                                              ┌──────────┴──────────┐
                                                              ▼                     ▼
                                                    Looker Studio Pro       Gemini AI Monitor
                                                 (Materialized View marts)  (pipeline_run_log)
```

---

## Pipeline Phases

| Phase | Description | Status |
| --- | --- | --- |
| 1 | GCP Foundation — buckets, datasets, service accounts, Dataplex | ✅ Complete |
| 2 | Cloud Functions Gen2 — BTS CSV & FR24 ingestion + BQ staging loads | ✅ Complete |
| 3 | BigQuery DDL — star schema tables, Dataform project, materialized views | 🔄 In Progress |
| 4 | Dataform execution — SCD-2 MERGEs and incremental fact loads | ⬜ Not Started |
| 5 | Gemini AI Monitor — deploy and wire to pipeline_run_log | ⬜ Not Started |
| 6 | Cloud Scheduler — orchestrate ingestion and Dataform runs | ⬜ Not Started |
| 7 | Looker Studio — build carrier, route, and delay dashboards | ⬜ Not Started |
| 8 | GitHub Actions CI/CD — PR checks and prod deploy pipeline | ⬜ Not Started |

---

## Data Sources

- **[BTS On-Time Performance](https://www.transtats.bts.gov/)** — Monthly US domestic flight performance (CSV)
- **[FlightRadar24 API v1](https://fr24api.flightradar24.com/)** — Live European airspace positions (REST, Explorer plan)

---

## Repository Layout

```text
cloud_functions/      # Gen2 ingestion functions — ingest_bts_csv, ingest_fr24, gemini_monitor
bigquery/ddl/         # CREATE OR REPLACE TABLE DDL — apply with bq CLI
bigquery/dataform/    # Dataform project — staging views, SCD-2 MERGEs, incremental facts
bigquery/materialized_views/  # Looker Studio mart views — refresh hourly
.github/workflows/    # CI: PR quality checks + prod deploy via Workload Identity
tests/unit/           # pytest unit tests — no live GCP calls
docs/                 # Architecture, runbook, changelog
```

---

*Built with GCP, Python 3.12, and AI pair-programming (Claude Code + Gemini CLI).*
