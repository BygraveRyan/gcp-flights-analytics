# GEMINI.md - Project `flights-analytics-prod`

This document provides an authoritative guide for the Gemini agent. Adhere strictly to these conventions and instructions when performing any software engineering task within this repository.

---

## 1. PROJECT IDENTITY

- **Project ID**: `flights-analytics-prod`
- **Region**: `europe-west2`
- **Python Version**: `3.12`
- **Key Libraries**:
    - PySpark: `3.5`
    - dbt Core: `1.8.x`
    - Airflow: `2.10.3` (via Cloud Composer 3)
    - google-cloud-storage: `2.18.2`
    - functions-framework: `3.8.1`

---

## 2. ARCHITECTURE SUMMARY

### 2.1. GCS Lakehouse Zones

- **Bronze Zone (Raw)**
    - **Bucket**: `gs://flights-bronze-flights-analytics-prod`
    - **Purpose**: Raw, unaltered data from sources (CSV, JSON).
    - **TTL**: 30 days
- **Silver Zone (Validated)**
    - **Bucket**: `gs://flights-silver-flights-analytics-prod`
    - **Purpose**: Cleaned, schema-enforced, deduplicated data in Parquet format.
    - **TTL**: 90 days
- **Gold Zone (Business)**
    - **Bucket**: `gs://flights-gold-flights-analytics-prod`
    - **Purpose**: Business-level aggregates and features for analytics.
    - **TTL**: Indefinite

### 2.2. BigQuery Datasets

- **`flights_raw`**: External tables pointing to GCS Silver zone.
- **`flights_staging`**: dbt staging models (views).
- **`flights_dw`**: Core data warehouse with facts (SCD-2) and dimensions.
- **`flights_marts`**: Reporting-layer tables aggregated for consumption by Looker Studio.

### 2.3. Data Flow

1.  **Sources**: BTS (CSV), OpenSky (API), FAA Airports (BQ Public), Airline IDs (BQ Public)
2.  **Ingestion (Cloud Functions)**: `fn-ingest-bts-csv` and `fn-ingest-opensky` write raw data to the **Bronze** GCS bucket.
3.  **Bronze → Silver (Dataproc)**: `bronze_to_silver.py` PySpark job enforces schema, deduplicates, and writes validated Parquet to the **Silver** GCS bucket.
4.  **Silver → Gold (Dataproc)**: `silver_to_gold.py` PySpark job enriches, aggregates, and writes business-level Parquet to the **Gold** GCS bucket.
5.  **Gold → BigQuery**: External tables in `flights_raw` read from Gold GCS buckets.
6.  **dbt Transformation**: dbt runs models to build staging views, intermediate tables, and final dimension/fact tables in the `flights_dw` and `flights_marts` datasets.
7.  **Looker Studio**: Dashboards query the `flights_marts` and `flights_dw` views for reporting.

---

## 3. SERVICE ACCOUNTS & IAM

- **Pipeline Runner SA**: `flights-pipeline-sa@flights-analytics-prod.iam.gserviceaccount.com`
    - **Roles**: `roles/bigquery.dataEditor`, `roles/bigquery.jobUser`, `roles/storage.objectAdmin`, `roles/dataproc.editor`, `roles/dataplex.editor`, `roles/aiplatform.user`, `roles/composer.worker`, `roles/cloudfunctions.invoker`.
- **Dataproc SA**: `flights-dataproc-sa@flights-analytics-prod.iam.gserviceaccount.com`
    - **Roles**: `roles/bigquery.dataEditor`, `roles/bigquery.jobUser`, `roles/storage.objectAdmin`, `roles/dataproc.worker`.
- **CI/CD SA**: `flights-cicd-sa@flights-analytics-prod.iam.gserviceaccount.com`
    - **Roles**: `roles/bigquery.dataEditor`, `roles/bigquery.jobUser`, `roles/storage.objectAdmin`, `roles/dataproc.editor`, `roles/cloudfunctions.developer`, `roles/iam.serviceAccountTokenCreator`.

---

## 4. CODING CONVENTIONS

### 4.1. Python (Cloud Functions & PySpark)

- **Style**: Adhere to PEP 8. Use `black` and `isort` for formatting.
- **Logging**: Use the standard `logging` module. Always include informative log messages for key operations (e.g., reading/writing data, API calls).
- **Error Handling**: Use `try...except` blocks for operations that can fail (e.g., API requests, file I/O). Log exceptions with `exc_info=True`. Raise exceptions for unrecoverable errors.
- **Type Hints**: Use type hints for all function signatures (`def my_function(param: str) -> int:`).

### 4.2. PySpark

- **Session Creation**: Use a dedicated `get_spark_session()` function. Configure `spark.sql.adaptive.enabled` and GCS connector settings.
- **Partitioning**: Repartition data before writing to GCS (`.repartition("partition_key")`) to control output file sizes.
- **Column Naming**: Use `snake_case` for all DataFrame columns created.
- **Immutability**: Treat DataFrames as immutable. Create new DataFrames for each transformation step.

### 4.3. SQL (BigQuery)

- **Style**: Use `sqlfluff` with the provided `.sqlfluff` config.
    - Keywords: **UPPERCASE** (`SELECT`, `FROM`, `WHERE`).
    - Identifiers (columns, tables): **lowercase** (`my_table`, `my_column`).
    - Functions: **UPPERCASE** (`COUNT()`, `SUM()`).
- **Aliasing**: Use explicit `AS` for all aliases (`table_name AS t`).
- **BigQuery Specifics**:
    - Always use `project-id.dataset.table` for cross-dataset queries.
    - Use `PARTITION BY` and `CLUSTER BY` on large tables.
    - Never use Legacy SQL. Always use `standard#`.

### 4.4. dbt

- **Macros**: Use `generate_surrogate_key()` for all primary keys. Use `scd2_merge()` for all SCD-2 dimension tables.
- **Surrogate Keys**: Generate surrogate keys using `MD5()` of the natural key and relevant business columns.
- **SCD-2**: For SCD-2 dimensions, always include `is_current` (BOOL), `effective_from` (DATE), and `effective_to` (DATE) columns.
- **Config Block**: Every model must have a `{{ config(...) }}` block at the top, specifying `materialized`, `tags`, and `labels`.

---

## 5. NAMING CONVENTIONS

- **Table Prefixes**:
    - `fct_`: Fact tables (e.g., `fct_flights`).
    - `dim_`: Dimension tables (e.g., `dim_airports`).
    - `stg_`: Staging models (views, e.g., `stg_bts_flights`).
    - `int_`: Intermediate models (tables, e.g., `int_flights_enriched`).
    - `mart_`: Reporting marts (e.g., `mart_delay_summary`).
- **File Naming**:
    - Python scripts: `snake_case.py` (e.g., `bronze_to_silver.py`).
    - SQL files: `snake_case.sql` (e.g., `fct_flights.sql`).
- **Variable Naming**: Use `snake_case` for all Python and SQL variables and columns.

---

## 6. DATA CONTRACTS

### 6.1. Delay Categories (`delay_category` column)

- **SEVERE_DELAY**: `arr_delay_minutes > 60`
- **MODERATE_DELAY**: `15 < arr_delay_minutes <= 60`
- **MINOR_DELAY**: `0 < arr_delay_minutes <= 15`
- **ON_TIME**: `arr_delay_minutes <= 0`
- **CANCELLED**: `is_cancelled = TRUE`
- **DIVERTED**: `is_diverted = TRUE`

### 6.2. SCD-2 Fields (in `dim_*` tables)

- **`is_current`**: `BOOL` - `TRUE` if this is the active record for the natural key.
- **`effective_from`**: `DATE` - The date this version of the record became active.
- **`effective_to`**: `DATE` - The date this version of the record expired (`NULL` for current records).
- **`row_hash`**: `STRING` - `MD5` of business attribute columns to detect changes.

### 6.3. BigQuery Partitioning & Clustering

- **`fact_flights`**: `PARTITION BY flight_date`, `CLUSTER BY carrier_code, origin_airport`.
- **`mart_delay_summary`**: `PARTITION BY summary_date`, `CLUSTER BY carrier_code`.

---

## 7. GEMINI AGENT INSTRUCTIONS

- **Fixed Values**:
    - Always use `PROJECT_ID="flights-analytics-prod"`.
    - Always use `REGION="europe-west2"`.
- **Code Generation**:
    - **Never** use placeholder comments like `# TODO` or `...`. Implement the logic completely.
    - **Always** include logging in all Python files (`cloud_functions/` and `spark_jobs/`).
    - **Always** write BigQuery Standard SQL. Never use Legacy SQL.
    - **Always** add appropriate `try...except` error handling in Python for I/O and API calls.
- **dbt Models**:
    - All dbt models **must** include a `config()` block at the top.
    - The `config()` block **must** specify `materialized`, `tags`, and `labels`.

---

## 8. FILE STRUCTURE REFERENCE

```
flights-analytics/
├── .github/
│   └── workflows/
│       ├── pr_checks.yml
│       └── deploy_prod.yml
├── .sqlfluff
├── cloud_functions/
│   ├── ingest_bts_csv/
│   │   ├── main.py
│   │   └── requirements.txt
│   └── ingest_opensky/
│       ├── main.py
│       └── requirements.txt
├── spark_jobs/
│   ├── bronze_to_silver.py
│   └── silver_to_gold.py
├── dataplex/
│   └── dq_rules/
│       └── silver_flights_dq.yaml
├── bigquery/
│   ├── ddl/
│   │   ├── create_tables.sql
│   │   └── create_views.sql
│   ├── stored_procs/
│   │   ├── sp_scd2_merge_airports.sql
│   │   ├── sp_scd2_merge_carriers.sql
│   │   └── sp_daily_monitor.sql
│   └── remote_models/
│       └── gemini_monitor_model.sql
├── dbt/
│   ├── dbt_project.yml
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   ├── macros/
│   └── tests/
├── dags/
│   └── flights_daily_pipeline.py
├── tests/
│   └── unit/
└── vertex_ai/
    └── gemini_experimental.py
```

---

## 🤖 AI & GIT CONVENTIONS

### Commit Message Format
All commits follow: `type(scope): description`
- **Types:** feat, fix, docs, refactor, chore, test
- **Scopes:** cloud-functions, spark, bigquery, dbt, composer, dataplex, cicd, docs, infra

### Python 3.12 Standards (MANDATORY)
- **Typing:** Never use `from typing import Tuple, Dict`. 
- **Rule:** Use native lowercase types: `dict[str, Any]`, `list[int]`, `tuple[str, int]`.
- **Reason:** Required for Cloud Functions Gen2 runtime stability.

### Pull Request & Merging
- **Title:** `feat: phase X — description`
- **Merge Style:** Squash and merge only.
- **Sync:** After every merge run all three commands:
```bash
  git checkout dev
  git pull origin main
  git push origin dev
```
- **Scope note:** Never use `docs` as a scope. Use the specific area e.g. `gemini`, `architecture`, `readme`

## 📁 Repository Structure Reference
gcp-flights-analytics/
├── .github/pull_request_template.md    # PR structure
├── GEMINI.md                            # This file
└── docs/architecture.md                 # Technical source of truth

