# Architecture Summary Mirror

Mirror artifact. Canonical source: `docs/architecture_summary.md`

- **Ingestion:** Cloud Functions Gen2 (Python 3.12) ingest raw data from BTS CSV (monthly) and FR24 (live REST).
- **Storage:** NDJSON raw audit copy in GCS Bronze; source-of-truth in BigQuery `flights_staging` and `flights_dw` datasets.
- **Warehouse:** Star schema in BigQuery with SCD Type 2 dimensions and partitioned incremental fact tables.
- **Transformation:** Dataform (SQLX) manages staging views, MERGE operations for SCD-2, and fact load logic.
- **Monitoring:** Gemini 2.5 Pro monitor function evaluates warehouse health and generates AI summaries in `pipeline_run_log`.
- **CI/CD:** GitHub Actions (pytest, flake8, sqlfluff) and automated deployment via Workload Identity Federation.
- **Removed:** All Spark, dbt, and Dataplex assets have been pruned in favor of a right-sized, cost-optimized stack (~97% reduction).
