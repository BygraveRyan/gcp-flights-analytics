# ✈️ GCP Flights Analytics Pipeline

A production-grade, end-to-end data engineering pipeline built on Google Cloud Platform — ingesting real-world flight data, transforming it through a Bronze/Silver/Gold lakehouse architecture, and surfacing insights via a Gemini AI-powered monitoring dashboard.

> Built as a hands-on learning project to develop real data engineering skills across the full modern data stack.

---

## 🎯 Project Goal

To design and build a complete batch data pipeline from scratch — covering ingestion, transformation, data quality, orchestration, CI/CD, and AI-powered monitoring — using the same tools and patterns found in production data engineering environments.

---

## 🏗️ Architecture Overview

```
BTS API (CSV)  ──┐
                 ├──► Cloud Functions (Gen2) ──► GCS Bronze
FR24 API ────────┘                                    │
                                                       ▼
                                            PySpark (Dataproc Serverless)
                                            Bronze ──► Silver ──► Gold
                                                       │
                                                       ▼
                                              BigQuery (SCD-2 Warehouse)
                                                       │
                                                       ▼
                                              dbt (Staging → Marts)
                                                       │
                                              ┌────────┴────────┐
                                              ▼                 ▼
                                       Looker Studio     Gemini AI Monitor
```

### Lakehouse Zones

| Zone | Bucket | Purpose | Retention |
|------|--------|---------|-----------|
| 🥉 Bronze | `flights-bronze-*` | Raw, unaltered source data | 30 days |
| 🥈 Silver | `flights-silver-*` | Cleaned, schema-enforced Parquet | 90 days |
| 🥇 Gold | `flights-gold-*` | Business-level aggregates | Indefinite |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Cloud | Google Cloud Platform (GCP) |
| Region | `europe-west2` (London) |
| Ingestion | Cloud Functions Gen2 (Python 3.12) |
| Storage | Google Cloud Storage |
| Processing | Dataproc Serverless PySpark 3.5 |
| Warehouse | BigQuery (partitioned + clustered, SCD-2) |
| Transformation | dbt Core 1.8.x |
| Orchestration | Cloud Composer 3 (Airflow 2.10) |
| Data Quality | Dataplex Universal Catalog |
| AI Monitoring | Gemini 2.5 Pro via `AI.GENERATE_TEXT` |
| CI/CD | GitHub Actions |
| Dashboard | Looker Studio |
| Dev | MacBook, VS Code, Gemini Code Assist |

---

## 📦 Pipeline Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | GCP Foundation — buckets, datasets, service accounts, Dataplex | ✅ Complete |
| 2 | Cloud Functions Gen2 — BTS CSV & FlightRadar24 API ingestion | ✅ Complete |
| 3 | PySpark Bronze → Silver | 🔄 In Progress |
| 4 | PySpark Silver → Gold | ⬜ Not Started |
| 5 | BigQuery DDL — partitioned tables, external tables | ⬜ Not Started |
| 6 | SCD Type 2 MERGE stored procedures | ⬜ Not Started |
| 7 | dbt Project — staging, intermediate, marts | ⬜ Not Started |
| 8 | Cloud Composer 3 DAG — full pipeline orchestration | ⬜ Not Started |
| 9 | Gemini AI Monitoring Dashboard | ⬜ Not Started |
| 10 | GitHub Actions CI/CD | ⬜ Not Started |
| 11 | Looker Studio Dashboard | ⬜ Not Started |

---

## 📊 Data Sources

- **[BTS On-Time Performance](https://www.transtats.bts.gov/)** — Monthly US domestic flight performance data (CSV via HTTP)
- **[FlightRadar24 API v1](https://fr24api.flightradar24.com/)** — Live European airspace flight positions via REST API (Explorer plan)

---

## 🗂️ Repository Structure

```
gcp-flights-analytics/
├── .github/
│   ├── pull_request_template.md
│   └── workflows/
│       ├── deploy_prod.yml
│       └── pr_checks.yml
├── cloud_functions/
│   ├── ingest_bts_csv/
│   └── ingest_fr24/
├── spark_jobs/
│   ├── bronze_to_silver.py
│   └── silver_to_gold.py
├── bigquery/
│   ├── ddl/
│   ├── stored_procs/
│   └── remote_models/
├── dbt/
│   └── models/
│       ├── staging/
│       ├── intermediate/
│       └── marts/
├── dataplex/
│   └── dq_rules/
├── dags/
├── docs/
│   └── architecture.md
└── tests/
    └── unit/
```

---

## 🔐 Infrastructure

**GCP Project:** `flights-analytics-prod`  
**Region:** `europe-west2`

**Service Accounts:**

- `flights-pipeline-sa` — Pipeline runner (functions, Spark, BQ)
- `flights-dataproc-sa` — Dataproc Serverless worker
- `flights-cicd-sa` — GitHub Actions deployments

**BigQuery Datasets:**

- `flights_raw` — External tables over GCS Silver
- `flights_staging` — dbt staging views
- `flights_dw` — SCD-2 dimensions and fact tables
- `flights_marts` — Reporting layer for Looker Studio

---

## 📐 Data Modelling

The warehouse uses **SCD Type 2** for dimension tables, tracking historical changes with `is_current`, `effective_from`, `effective_to`, and `row_hash` fields.

**Key Tables:**

| Table | Type | Partitioned By | Clustered By |
|-------|------|---------------|--------------|
| `fct_flights` | Fact | `flight_date` | `carrier_code`, `origin_airport` |
| `dim_carriers` | SCD-2 Dimension | — | — |
| `dim_airports` | SCD-2 Dimension | — | — |
| `mart_delay_summary` | Reporting Mart | `summary_date` | `carrier_code` |

---

## 🤖 AI Monitoring

Phase 9 integrates **Gemini 2.5 Pro** directly into BigQuery via `AI.GENERATE_TEXT` to provide natural language pipeline health summaries — anomaly detection, delay pattern analysis, and data quality reporting — surfaced in a Looker Studio dashboard.

---

## 🚀 What I'm Learning

This project is intentionally built across the full data engineering lifecycle to develop real, employable skills:

- Designing and implementing a cloud lakehouse from scratch
- Writing production-quality PySpark transformation jobs
- Building SCD Type 2 data models in BigQuery
- Orchestrating multi-step pipelines with Apache Airflow
- Applying data quality rules with Dataplex
- Integrating LLMs into data pipelines for AI-powered monitoring
- CI/CD for data infrastructure with GitHub Actions

---

## 📄 Documentation

Full pipeline architecture, DDL, PySpark logic, dbt models, and DAG code are documented in [`docs/architecture.md`](docs/architecture.md).

---

*Built with ☁️ GCP, 🐍 Python 3.12, and a lot of learning along the way.*
