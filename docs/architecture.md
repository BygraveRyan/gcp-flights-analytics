# GCP Flights Analytics Pipeline — Architecture
> **Project:** `flights-analytics-prod` | **Region:** `europe-west2`
> **Last updated:** March 2026
> **Status:** Simplified re-architecture complete, pipeline build in progress

---

## 1. Why This Architecture

The original design used Dataproc Serverless PySpark, dbt Core, Cloud Composer,
and a Bronze/Silver/Gold GCS lakehouse. At actual data volumes — 600K rows/month
BTS, ~50K rows/day FR24 — BigQuery processes the same transformations in seconds
with zero infrastructure. Distributed compute was unjustified.

**What was removed and why:**

| Removed | Replaced with | Saving |
|---|---|---|
| Dataproc Serverless (PySpark) | BigQuery native SQL | ~£30/month |
| Cloud Composer (Airflow) | Cloud Scheduler | ~£35/month |
| dbt Core | Dataform (free, native BQ) | £0 + complexity |
| Bronze/Silver/Gold GCS (3 buckets) | Single raw audit bucket | ~£2/month |
| Dataplex DQ scanning | BQ native assertions | ~£5/month |
| OpenSky Network | FlightRadar24 API v1 | (blocked GCP IPs) |
| vertexai.generative_models SDK | google-genai SDK | (deprecated June 2025) |

**Result:** £65/month → £2-5/month running. Same analytical output.

---

## 2. Architecture Overview
```
BTS API (monthly, ~600K rows)  ──┐
                                  ├──► Cloud Functions Gen2 ──► GCS (raw audit)
FR24 API (live, ~50K rows/day) ──┘              │
                                                 ▼
                                    BigQuery — flights_staging
                                    (raw_bts_flights, raw_fr24_positions)
                                                 │
                                    Dataform (free, native BQ)
                                    staging views → SCD-2 merges → fact loads
                                                 │
                                    BigQuery — flights_dw
                                    (star schema tables)
                                                 │
                                    BigQuery Materialized Views
                                    (mart_carrier_daily, mart_route_performance,
                                     mart_delay_analysis)
                                                 │
                         ┌───────────────────────┴───────────────────────┐
                         ▼                                               ▼
                  Looker Studio Pro                            Gemini Monitor
              (dashboards + Conversational                  (google-genai SDK,
               Analytics — NL querying)                   daily AI summaries →
                                                           pipeline_run_log)
```

**Orchestration:** Cloud Scheduler fires at 06:00 UTC daily, triggering both
Cloud Functions via authenticated HTTP POST. No Composer, no DAG complexity.

---

## 3. Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Cloud | Google Cloud Platform | europe-west2 (London) |
| Ingestion | Cloud Functions Gen2, Python 3.12 | fn-ingest-bts-csv, fn-ingest-fr24 |
| Raw storage | GCS — single audit bucket | 365d TTL, immutable, reprocess any time |
| Staging | BigQuery — flights_staging dataset | raw_bts_flights, raw_fr24_positions |
| Transformation | Dataform (SQLX, free) | Git-connected, dependency DAG, version controlled |
| Warehouse | BigQuery — flights_dw dataset | Partitioned + clustered star schema |
| Reporting layer | BigQuery Materialized Views | Auto-refresh, sub-second Looker queries |
| Orchestration | Cloud Scheduler | ~£0.08/month, replaces Composer |
| Visualisation | Looker Studio Pro | Free tier, direct BQ connector |
| AI querying | Conversational Analytics | Natural language → chart, Looker Studio Pro |
| AI monitoring | Gemini 2.5 Pro, google-genai SDK | Daily pipeline health summaries |
| CI/CD | GitHub Actions | pr_checks.yml, deploy_prod.yml |
| Primary coding agent | Claude Code (VS Code extension) | Commits, PRs to feat/* branches |
| GCP console operations | Gemini Code Assist | BQ exploration, gcloud context |

---

## 4. Data Sources

### FlightRadar24 API v1
- Endpoint: `https://fr24api.flightradar24.com/api/live/flight-positions/full`
- Auth: Bearer token via Secret Manager (`fr24-api-key`)
- Bounding box: UK + NW Europe (61.5°N, 49°S, 8.5°W, 10.5°E)
- Volume: ~50K position records/day
- Plan: Explorer ($9/month) — sandbox key active until purchased
- GCS path: `fr24/{year}/{month:02d}/{day:02d}/positions_{YYYYMMDD_HHMMSS}.ndjson`

### BTS On-Time Performance
- Source: transtats.bts.gov — monthly ZIP download
- Volume: ~600K rows/month
- Cadence: Monthly lag (~1 month behind current)
- Idempotency: Function checks BQ staging row count before downloading
- GCS path: `bts/{year}/{month:02d}/bts_{YYYYMMDD}.csv`

---

## 5. Star Schema

All business logic and dimensional modelling lives in BigQuery/Dataform.
No transformation happens in GCS or during ingestion.

### Fact Tables

**fact_flights** — grain: one row per flight segment
- Partitioned by `flight_date`, clustered by `carrier_code`, `origin_airport_code`
- FKs: `date_sk`, `carrier_sk`, `origin_airport_sk`, `dest_airport_sk`
- Key fields: `flight_sk` (MD5 surrogate PK), `dep_delay_minutes`,
  `arr_delay_minutes`, `distance_miles`, `air_time_minutes`, `is_cancelled`,
  `is_diverted`, `delay_category` (On Time / Minor / Moderate / Severe),
  `carrier_delay_minutes`, `weather_delay_minutes`, `nas_delay_minutes`

**fact_positions** — grain: one FR24 position record
- Partitioned by `position_date`, clustered by `icao24`
- FKs: `date_sk`
- Key fields: `position_sk` (MD5 surrogate PK), `icao24`, `callsign`,
  `latitude`, `longitude`, `altitude_metres`, `velocity_ms`,
  `vertical_speed`, `on_ground`, `ingestion_timestamp`
- Note: No carrier or airport FK — FR24 telemetry does not reliably
  contain structured carrier codes. Joining via callsign parsing is
  brittle and unnecessary for analytical goals.

### Dimension Tables

**dim_date** — static, no SCD-2 required
- PK: `date_sk` (STRING, format YYYYMMDD)
- Range: 2020–2030, pre-populated once
- Key fields: `full_date`, `year`, `month`, `day_of_month`, `day_name`,
  `month_name`, `quarter`, `is_weekend`

**dim_carrier** — SCD-2 (airlines rename and merge)
- PK: `carrier_sk` (MD5 surrogate)
- Natural key: `carrier_code`
- SCD-2 fields: `is_current`, `effective_from`, `effective_to`, `row_hash`
- Source: BTS staging data (distinct carrier codes)

**dim_airport** — SCD-2, role-playing dimension
- PK: `airport_sk` (MD5 surrogate)
- Natural key: `airport_code`
- SCD-2 fields: `is_current`, `effective_from`, `effective_to`
- Source: bigquery-public-data.faa.us_airports
- Role-playing: fact_flights joins this table TWICE —
  once as origin_airport_sk, once as dest_airport_sk.
  In SQL: `JOIN dim_airport AS origin ON ...`
           `JOIN dim_airport AS dest ON ...`

### Audit Table

**pipeline_run_log** — not part of star schema, operational
- Records every pipeline execution
- Fields: `run_id`, `run_date`, `run_timestamp`, `source`,
  `total_rows_loaded`, `rows_rejected`, `avg_delay_minutes`,
  `gemini_summary`, `pipeline_status`, `created_at`
- Powers the AI Commentary panel in Looker Studio

---

## 6. Dataform Structure

Dataform is the transformation layer. Free, native to BigQuery,
Git-connected to this repo. All files in `bigquery/dataform/`.
```
bigquery/dataform/
├── dataform.json                          # Project config
└── definitions/
    ├── staging/
    │   ├── stg_bts_flights.sqlx           # View on raw_bts_flights
    │   └── stg_fr24_positions.sqlx        # View on raw_fr24_positions
    └── transforms/
        ├── merge_dim_carrier.sqlx         # SCD-2 MERGE into dim_carrier
        ├── merge_dim_airport.sqlx         # SCD-2 MERGE into dim_airport
        ├── load_fact_flights.sqlx         # Incremental load, surrogate keys
        └── load_fact_positions.sqlx       # Incremental load
```

**Run order enforced by Dataform dependency graph:**
1. stg_bts_flights, stg_fr24_positions (parallel)
2. merge_dim_carrier, merge_dim_airport (parallel, depend on staging)
3. load_fact_flights, load_fact_positions (depend on dims + staging)

**SCD-2 MERGE pattern for dim_carrier and dim_airport:**
- MERGE ON natural_key AND is_current = TRUE
- WHEN MATCHED AND row_hash changed:
  expire old row (effective_to = CURRENT_DATE() - 1, is_current = FALSE)
  then INSERT new current row
- WHEN NOT MATCHED: INSERT new row

**delay_category logic in load_fact_flights.sqlx:**
```sql
CASE
  WHEN arr_delay_minutes <= 15 THEN 'On Time'
  WHEN arr_delay_minutes <= 45 THEN 'Minor'
  WHEN arr_delay_minutes <= 120 THEN 'Moderate'
  ELSE 'Severe'
END AS delay_category
```

---

## 7. Materialized Views (Reporting Layer)

All in `bigquery/materialized_views/`. Auto-refresh every 60 minutes.
These are what Looker Studio queries — never the raw fact tables directly.

**mart_carrier_daily** — powers carrier performance dashboard
- Aggregates fact_flights by carrier_code + carrier_name + flight_date
- Metrics: total_flights, cancelled_flights, cancellation_rate,
  avg_dep_delay, avg_arr_delay, on_time_count, on_time_rate,
  severe_delay_count
- Partitioned by flight_date

**mart_route_performance** — powers route map and rankings
- Aggregates fact_flights by origin + destination + carrier
- Metrics: total_flights, avg_arr_delay, on_time_rate, pct_severe_delays
- Joins dim_airport twice for airport names and coordinates
  (coordinates needed for Looker Studio geo map)
- Clustered by origin_airport_code

**mart_delay_analysis** — powers delay breakdown and AI commentary
- Aggregates fact_flights by carrier + month (DATE_TRUNC)
- Metrics: avg_carrier_delay, avg_weather_delay, avg_nas_delay,
  total_delay_minutes, weather_delay_share, carrier_delay_share
- Only rows where total_delay_minutes > 0

---

## 8. Cloud Functions

All Gen2, Python 3.12. All use `request: Any` type hint —
`functions_framework.Request` does not exist on the Python 3.12 runtime.
All use native Python 3.12 types — no `from typing import` imports.
All credentials via Secret Manager — nothing hardcoded.

**fn-ingest-fr24**
- Trigger: HTTP (Cloud Scheduler authenticated POST)
- Calls FR24 API, writes NDJSON to GCS audit bucket
- Loads directly to flights_staging.raw_fr24_positions
  via google-cloud-bigquery load_table_from_json()
- No VPC connector (deleted — was in ERROR state, costing ~£8/month)
- Timeout: 120s, Memory: 256Mi

**fn-ingest-bts-csv**
- Trigger: HTTP (Cloud Scheduler authenticated POST)
- Idempotency check first: COUNT(*) from staging WHERE year+month
  If > 0: returns {"status": "already_loaded"}, 200 — exits cleanly
- Downloads BTS ZIP, extracts CSV (~600K rows)
- Writes CSV to GCS audit bucket
- Loads to flights_staging.raw_bts_flights
- Timeout: 540s, Memory: 512Mi

**fn-gemini-monitor**
- Trigger: HTTP (Cloud Scheduler authenticated POST, after pipeline run)
- Queries fact_flights for today's stats (total, avg delay, cancellations,
  severe delays, top 3 carriers by volume)
- Calls Gemini 2.5 Pro via google-genai SDK:
  `from google import genai`
  `client = genai.Client(vertexai=True, project=PROJECT_ID,
   location="europe-west2")`
- NOT vertexai.generative_models — deprecated June 2025,
  removed June 2026
- Writes 3-sentence summary to pipeline_run_log
- Timeout: 120s, Memory: 256Mi

---

## 9. Orchestration

Cloud Scheduler — two jobs, 06:00 UTC daily:
```
Job 1: trigger-ingest
  Schedule: 0 6 * * *
  Targets: fn-ingest-bts-csv, fn-ingest-fr24 (parallel)
  Auth: OIDC, flights-pipeline-sa service account

Job 2: trigger-gemini-monitor
  Schedule: 30 6 * * *  (30 min after ingestion)
  Target: fn-gemini-monitor
  Auth: OIDC, flights-pipeline-sa service account
```

Dataform runs are triggered via Dataform workflow configuration
in GCP Console, scheduled independently of Cloud Scheduler.
Dataform handles its own dependency ordering internally.

---

## 10. Looker Studio Dashboard

Connects directly to BigQuery materialized views — no ETL, no caching layer.

**Pages:**
1. Executive Overview — scorecards (total flights, avg delay,
   on-time rate, cancellation rate) + daily trend line
2. Route Performance — geo map (origin/destination with
   delay colour coding) + ranked route table
3. Carrier Rankings — sortable table with delay breakdown
4. AI Commentary — Gemini daily summaries from pipeline_run_log,
   delay analysis charts

**Conversational Analytics (Looker Studio Pro — free tier):**
Natural language querying powered by Gemini. Users type plain
English questions and receive charts without writing SQL.
Example: "Which routes had the worst average arrival delay last month?"
Requires: Looker Studio Pro subscription (free for personal GCP
accounts) + Gemini in Looker enabled by admin.

---

## 11. Security

- Workload Identity Federation for GitHub Actions — no SA key files
- Secret Manager for all credentials (fr24-api-key)
- No --allow-unauthenticated on any Cloud Function
- Column-level policy tag on tail_number (SENSITIVE_PII)
- Uniform bucket-level access on GCS bucket
- Least-privilege IAM — flights-pipeline-sa has only what it needs:
  bigquery.dataEditor, bigquery.jobUser, storage.objectAdmin,
  secretmanager.secretAccessor

---

## 12. Repository Structure
```
gcp-flights-analytics/
├── cloud_functions/
│   ├── ingest_bts_csv/
│   │   ├── main.py
│   │   └── requirements.txt
│   ├── ingest_fr24/
│   │   ├── main.py
│   │   └── requirements.txt
│   └── gemini_monitor/
│       ├── main.py
│       └── requirements.txt
├── bigquery/
│   ├── ddl/
│   │   ├── dim_date.sql
│   │   ├── dim_carrier.sql
│   │   ├── dim_airport.sql
│   │   ├── fact_flights.sql
│   │   ├── fact_positions.sql
│   │   └── pipeline_run_log.sql
│   ├── dataform/
│   │   ├── dataform.json
│   │   └── definitions/
│   │       ├── staging/
│   │       │   ├── stg_bts_flights.sqlx
│   │       │   └── stg_fr24_positions.sqlx
│   │       └── transforms/
│   │           ├── merge_dim_carrier.sqlx
│   │           ├── merge_dim_airport.sqlx
│   │           ├── load_fact_flights.sqlx
│   │           └── load_fact_positions.sqlx
│   └── materialized_views/
│       ├── mart_carrier_daily.sql
│       ├── mart_route_performance.sql
│       └── mart_delay_analysis.sql
├── .github/
│   └── workflows/
│       ├── pr_checks.yml
│       └── deploy_prod.yml
├── tests/
│   └── unit/
│       ├── conftest.py
│       └── test_ingest_fr24.py
├── docs/
│   ├── architecture.md          ← this file
│   ├── architecture_summary.md
│   ├── runbook.md
│   └── session_handover.md
└── CLAUDE.md
```

---

## 13. AI-Driven Development Workflow

This project is built using a structured AI-driven development approach.
AI agents act as engineering collaborators with human architectural
oversight — not as autocomplete.

| Tool | Role |
|---|---|
| Claude Code (VS Code extension) | Primary coding agent — Python, SQL, Dataform SQLX, config, git operations |
| Gemini Code Assist | GCP-native operations — BigQuery exploration, gcloud context |
| Human | Architecture decisions, PR merges, all infrastructure commands |

**Git workflow:**
- All new work on `feat/short-description` branches
- Claude Code: git add, commit, push to feat/*, gh pr create → dev
- Human: reviews PR, gh pr merge --squash into dev
- dev → main via PR after verification
- Never commit directly to main or dev

**Claude Code guardrails (enforced in CLAUDE.md):**
- Never run gcloud, bq, gsutil, git push to main
- Always propose infrastructure commands for human to run
- No hardcoded secrets or project IDs
- Standard SQL only — no Legacy SQL
- request: Any type hint on all Cloud Functions
- Native Python 3.12 types — no typing module imports

---

## 14. Cost Profile

| Service | Monthly cost | Notes |
|---|---|---|
| BigQuery storage | ~£0.02 | Tiny data volume |
| BigQuery queries | ~£0 | First 1TB/month free forever |
| GCS storage | ~£0.02 | Single bucket, small files |
| Cloud Functions | ~£0 | First 2M invocations/month free |
| Cloud Scheduler | ~£0.08 | First 3 jobs/month free |
| Dataform | £0 | Always free |
| Looker Studio Pro | £0 | Free for personal accounts |
| Gemini monitoring | ~£0.01/day | Token cost negligible |
| **Total running** | **~£2-5/month** | |
| **Total at rest** | **~£1/month** | No daily triggers |

**Cost guardrails:**
- All Cloud Functions: min-instances=0 (no idle cost)
- No VPC connector (deleted March 2026 — was ERROR state, ~£8/month)
- No BI Engine reservation (materialized views provide sufficient speed)
- No Dataproc, no Composer, no Dataplex DQ scanning

---

*Project: flights-analytics-prod | Region: europe-west2 | Python 3.12*
*Stack: Cloud Functions → GCS → BigQuery (Dataform) → Looker Studio*