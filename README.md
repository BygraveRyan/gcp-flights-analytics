# GCP Flights Analytics Pipeline

A production-grade cloud data engineering platform on **Google Cloud Platform** — built to demonstrate architectural accountability, cost-justified infrastructure decisions, and AI-governed pipeline operations.

Ingests live aviation data (BTS On-Time Performance + FlightRadar24), models it into a star schema warehouse, and delivers analytics through Looker Studio with Gemini AI monitoring.

---

## The Architectural Decision

The first version of this project was overengineered — Spark jobs, dbt, Vertex AI, Dataplex, a full lakehouse stack running at **~£65/month** for a 600K rows/month workload.

The refactor question was simple: *does this architecture justify its cost?*

The answer was no. The stack was a Ferrari engine for a bicycle use case.

**Every unnecessary layer was deleted.** Spark jobs, dbt, Vertex AI processing, VPC connectors, stored procedures — all removed. The replacement stack (Cloud Functions + BigQuery + Dataform) handles the same workload for **£2–5/month** — a **97% cost reduction** — while being simpler to operate, test, and extend.

This is the core skill the refactor demonstrates: the ability to identify architectural theater and defend the decision to remove it.

---

## Recruiter Panel

| Attribute | Value |
| --- | --- |
| **Role target** | Data Engineer / Cloud Data Engineer / AI Infrastructure Engineer |
| **Cloud** | Google Cloud Platform — `europe-west2` |
| **Architectural decision** | Pruned overengineered lakehouse to right-sized stack — 97% cost reduction |
| **Cost governance** | £65/month → £2–5/month; every component justified by ROI |
| **AI governance** | Human-in-the-loop workflow with agent guardrails defined in `CLAUDE.md` |
| **Warehouse pattern** | Star schema, partitioned + clustered, SCD Type 2 dimensions |
| **AI integration** | Gemini 2.5 Pro via `google-genai` SDK for autonomous pipeline monitoring |
| **Code standards** | Python 3.12, GoogleSQL, Conventional Commits, flake8, sqlfluff |
| **Testing** | pytest unit tests, GitHub Actions CI on every PR |

---

## AI Governance Model

This project is built with a **Human-in-the-Loop AI workflow** — not because AI can't execute terminal commands, but because unaudited AI actions on cloud infrastructure create real financial and operational risk.

The governance model is intentional:

- All GCP commands (gcloud, bq, gsutil, gh pr merge) are proposed by the agent and executed by the human — no autonomous cloud writes.
- Agent behaviour is constrained by `CLAUDE.md` — scope, permitted actions, and escalation rules defined explicitly.
- No secrets or project IDs hardcoded — Secret Manager and environment variables only.
- All production changes go through feature branches with CI checks before human-approved merge.

This mirrors the "MCP safety layer" pattern emerging in enterprise AI infrastructure — constraining agent context to prevent unintended cost spikes or data modifications.

---

## Why This Stack

Every layer was chosen with a cost and fitness-for-purpose argument:

| Layer | Choice | Why |
| --- | --- | --- |
| Ingestion | Cloud Functions Gen2 | Right-sized for event-driven ingest; no cluster to manage or pay for at idle |
| Raw Storage | GCS (single bucket, 365d TTL) | Audit trail without the overhead of a multi-zone lakehouse |
| Warehouse | BigQuery (partitioned + clustered) | Serverless; cost controlled by partition pruning and clustering on query columns |
| Transformation | Dataform (SQLX) | Free, native to BigQuery, no external orchestrator needed for this workload |
| Orchestration | Cloud Scheduler | £0.08/month — no Airflow/Composer overhead for a twice-daily trigger |
| Monitoring | Gemini via Cloud Function | Autonomous anomaly detection on `pipeline_run_log` without a paid observability tool |
| CI/CD | GitHub Actions | Free for public repos; Workload Identity Federation — no service account keys stored |

**What was removed and why:**

| Removed | Reason |
| --- | --- |
| `spark_jobs/` | Spark is designed for petabyte-scale; scanning 600K rows with it is pure overhead |
| `dbt/` | Replaced by Dataform — same SQL transformation capability, zero additional cost |
| `vertex_ai/` | No ML workload exists yet; running Vertex infrastructure speculatively is theater |
| VPC Connector | Was in ERROR state and costing ~£8/month; Cloud Functions operate fine without it at this scale |
| Stored procedures | Moved transformation logic to Dataform SQLX for testability and version control |

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Cloud | Google Cloud Platform — `europe-west2` (London) |
| Ingestion | Cloud Functions Gen2 (Python 3.12) |
| Raw Storage | Google Cloud Storage (single Bronze bucket) |
| Warehouse | BigQuery — partitioned + clustered tables, SCD Type 2 |
| Transformation | Dataform — SQLX models, incremental loads, SCD-2 MERGEs |
| Orchestration | Cloud Scheduler |
| Dashboards | Looker Studio Pro + Conversational Analytics |
| AI Monitoring | Gemini 2.5 Pro via `google-genai` SDK |
| CI/CD | GitHub Actions — flake8, pytest, sqlfluff, Workload Identity deploy |

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
| 1 | GCP Foundation — buckets, datasets, service accounts | ✅ Complete |
| 2 | Cloud Functions Gen2 — BTS CSV & FR24 ingestion + BQ staging loads | ✅ Complete |
| 3 | BigQuery DDL — star schema tables, Dataform project, materialized views | ✅ Complete |
| 4 | Dataform execution — SCD-2 MERGEs and incremental fact loads | ✅ Complete |
| 5 | Gemini AI Monitor — deploy and wire to pipeline_run_log | ✅ Complete |
| 6 | Cloud Scheduler — orchestrate ingestion and Dataform runs | 🔄 In Progress |
| 7 | Looker Studio — build carrier, route, and delay dashboards | 🔄 In Progress |
| 8 | GitHub Actions CI/CD — PR checks and prod deploy pipeline | ✅ Complete |

---

## Data Sources

- **[BTS On-Time Performance](https://www.transtats.bts.gov/)** — Monthly US domestic flight performance (CSV)
- **[FlightRadar24 API v1](https://fr24api.flightradar24.com/)** — Live European airspace positions (REST, Explorer plan)

---

## Repository Layout

```text
cloud_functions/              # Gen2 ingestion functions — ingest_bts_csv, ingest_fr24, gemini_monitor
bigquery/ddl/                 # CREATE OR REPLACE TABLE DDL — apply with bq CLI
bigquery/dataform/            # Dataform project — staging views, SCD-2 MERGEs, incremental facts
bigquery/materialized_views/  # Looker Studio mart views
.github/workflows/            # CI: PR quality checks + prod deploy via Workload Identity
tests/unit/                   # pytest unit tests — no live GCP calls
docs/                         # Architecture, runbook, changelog
CLAUDE.md                     # Agent governance — permitted actions, escalation rules
```

---

*Built on GCP with Python 3.12. AI pair-programming (Claude Code + Gemini CLI) under explicit governance constraints.*
