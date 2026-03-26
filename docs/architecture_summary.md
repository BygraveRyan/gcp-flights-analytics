# Architecture Summary

This file is the concise, current-state summary of committed assets.
For design detail, see `docs/architecture.md`. For operator notes, see `docs/runbook.md`.

## Stack

Cloud Functions Gen2 (Python 3.12) ingest raw data from the BTS On-Time Performance API
and the FlightRadar24 API. Raw data lands in GCS Bronze and is loaded to BigQuery staging
tables. Dataform transforms staging data into a star schema warehouse (SCD-2 dimensions
and incremental fact tables) in the `flights_dw` dataset. Materialized views serve
pre-aggregated marts to Looker Studio. A Gemini monitor function queries the warehouse
and writes AI-generated summaries to `pipeline_run_log`.

There is no Spark, no dbt, no Gold GCS layer, and no Composer/Airflow in this stack.
Dataform handles all SQL transformations and scheduling via Cloud Scheduler.

## Committed Asset Footprint

**Ingestion — `cloud_functions/`**

- `ingest_bts_csv/` — downloads BTS monthly CSV zip, loads to `flights_staging.raw_bts_flights`; idempotency check on `stg_bts_flights`
- `ingest_fr24/` — fetches FR24 live positions, loads to `flights_staging.raw_fr24_positions`
- `gemini_monitor/` — queries `flights_dw` for daily stats, calls Gemini 2.5 Pro, writes summary to `pipeline_run_log`

**Warehouse DDL — `bigquery/ddl/`**

- `dim_date.sql` — static calendar spine 2020-2030
- `dim_carrier.sql` — SCD Type 2, partitioned by `effective_from`
- `dim_airport.sql` — SCD Type 2, role-playing dim (origin + destination)
- `fact_flights.sql` — partitioned by `flight_date`, clustered by `carrier_code`, `origin_airport_code`
- `fact_positions.sql` — partitioned by `position_date`, clustered by `icao24`
- `pipeline_run_log.sql` — audit and Gemini summary table

**Dataform — `bigquery/dataform/`**

- `dataform.json` — project config (flights-analytics-prod, flights_dw, europe-west2)
- `definitions/staging/` — `stg_bts_flights`, `stg_fr24_positions` (type: view, light casting only)
- `definitions/transforms/` — `merge_dim_carrier`, `merge_dim_airport` (SCD-2 MERGE operations); `load_fact_flights`, `load_fact_positions` (type: incremental)

**Materialized Views — `bigquery/materialized_views/`**

- `mart_carrier_daily.sql` — carrier performance by day (Looker Studio carrier page)
- `mart_route_performance.sql` — route metrics + geo coordinates (route map page)
- `mart_delay_analysis.sql` — monthly delay attribution by source (delay + AI commentary page)

**CI/CD — `.github/workflows/`**

- `pr_checks.yml` — flake8, pytest, sqlfluff on every PR targeting main
- `deploy_prod.yml` — gcloud functions deploy on push to main, Workload Identity Federation auth

**Tests — `tests/unit/`**

- `conftest.py`, `test_bronze_to_silver.py`

**Data Quality — `dataplex/dq_rules/`**

- `silver_flights_dq.yaml`

## Data Flow

```text
BTS API / FR24 API
       │
       ▼
Cloud Functions (Gen2)
       │
       ├──► GCS Bronze (raw NDJSON audit copy)
       │
       └──► BigQuery: flights_staging.*
                      │
                      ▼
               Dataform (SQLX)
               staging views → SCD-2 MERGEs → incremental facts
                      │
                      ▼
               flights_dw.* (star schema)
                      │
               ┌──────┴──────┐
               ▼             ▼
    Materialized Views   pipeline_run_log
    (Looker Studio)      (Gemini Monitor)
```
