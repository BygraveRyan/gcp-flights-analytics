# Architecture Summary

This file is the concise, repo-state summary. For deeper design detail, read `docs/architecture.md`. For live infrastructure and operator notes, read `docs/runbook.md`.

## Current Repo Footprint

- Ingestion assets exist under `cloud_functions/` for BTS, FR24, and a legacy OpenSky path.
- Bronze-to-Silver processing is implemented in `spark_jobs/bronze_to_silver.py`.
- Silver-to-Gold processing is implemented in `spark_jobs/silver_to_gold.py`.
- Warehouse and monitoring assets exist under `bigquery/` for DDL, stored procedures, and Gemini monitoring SQL.
- dbt staging assets exist under `dbt/models/staging/`.
- Dataplex data quality rules exist under `dataplex/dq_rules/`.
- Unit tests currently center on the Bronze-to-Silver Spark job in `tests/unit/`.

## End-To-End Shape

1. Ingestion functions land raw source data in GCS Bronze.
2. Spark transforms Bronze data toward curated Parquet outputs.
3. BigQuery, dbt, and Dataplex assets define warehouse, transformation, monitoring, and data quality layers.

## Partial Or Planned Areas

- `dags/` exists, but no DAG files are currently committed.
- README phase labels do not fully match the committed asset footprint; verify repo contents before using phase claims.
- Long-form docs describe dashboards and orchestration, but those layers are not all represented as committed implementation files today.
