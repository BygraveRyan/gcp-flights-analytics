# ✈️ GCP Flights Analytics Pipeline
An end-to-end cloud data engineering platform built on **Google Cloud Platform** that ingests aviation datasets, processes them through a **lakehouse architecture**, and delivers **analytics-ready insights**.

> **Note:** This is an **AI-Native Engineering** project. It is developed using a "Human-in-the-Loop" workflow with autonomous agents, governed by strict engineering standards and domain-specific AI skills.

---

# 🤖 AI-Native Workflow

Unlike traditional development, this repository is managed as an **Agent-Led Environment**.

*   **Mission-Driven:** All engineering actions are governed by `GEMINI.md`, defining a "Senior Data Engineer" persona with strict guardrails.
*   **Specialized Skills:** The project utilizes custom agent skills (located in `.gemini/skills/`) for domain-specific tasks:
    *   `spark-architect`: Optimized PySpark jobs and partitioning logic.
    *   `dbt-architect`: SCD-2 modelling and dbt standards.
    *   `code-sanitizer`: Automated PEP 8 and SQL compliance.
*   **Safety First:** Mandatory confirmation protocols for all infrastructure changes and Git operations.

---

# 🔎 Quick Summary

This project simulates a **real-world cloud data engineering platform** that ingests aviation datasets and transforms them into analytics-ready data products.

It demonstrates how modern data teams design scalable pipelines using **cloud-native tools and lakehouse architecture patterns**.

### Key capabilities

• Automated ingestion of historical and live flight data  
• Lakehouse architecture (**Bronze → Silver → Gold**)  
• Distributed transformations using **Dataproc Serverless PySpark**  
• Dimensional modelling in **BigQuery using SCD Type 2**  
• Pipeline orchestration with **Apache Airflow (Cloud Composer)**  
• **AI-powered pipeline monitoring using Gemini**

---

# ⭐ Key Highlights

- Built a **production-style cloud data pipeline on GCP**
- Processes **real aviation datasets and live flight APIs**
- Implements **Lakehouse architecture (Bronze/Silver/Gold)**
- Uses **Dataproc Serverless PySpark for scalable transformations**
- Implements **SCD Type 2 dimensional modelling in BigQuery**
- Automated orchestration with **Apache Airflow**
- Includes **AI-powered pipeline monitoring with Gemini**

---

# 🛠️ Tech Stack

| Layer | Technology |
|------|-----------|
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
| **Dev / Agents** | **Gemini CLI, Claude Code, Gemini Code Assist** |

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


## 📦 Pipeline Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | GCP Foundation — buckets, datasets, service accounts, Dataplex | ✅ Complete |
| 2 | Cloud Functions Gen2 — BTS CSV & FlightRadar24 API ingestion | ✅ Complete |
| 3 | PySpark Bronze → Silver | ✅ Complete |
| 4 | PySpark Silver → Gold | ✅ Complete |
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

## 🚀 What I'm Learning

This project is intentionally built to develop real, employable skills in a modern, AI-augmented environment:

- **AI-Native Dev:** Building and managing an autonomous data engineering environment.
- **Lakehouse Design:** Implementing a multi-zone (Bronze/Silver/Gold) storage strategy.
- **Scalable Processing:** Writing production-quality PySpark jobs for Dataproc Serverless.
- **SCD Type 2:** Managing slowly changing dimensions in a BigQuery warehouse.
- **Orchestration:** Engineering complex dependencies with Apache Airflow.

---

## 📄 Documentation

Full pipeline architecture, DDL, PySpark logic, dbt models, and DAG code are documented in [`docs/architecture.md`](docs/architecture.md).

---

*Built with ☁️ GCP, 🐍 Python 3.12, and 🤖 AI Pair-Programming.*
