# Architecture Summary Mirror

Mirror artifact. Canonical source: `docs/architecture_summary.md`

- Raw flight data lands through `cloud_functions/` into GCS Bronze.
- `spark_jobs/bronze_to_silver.py` is the main committed transformation job.
- BigQuery, dbt, and Dataplex assets define warehouse, transformation, monitoring, and DQ layers.
- Some architecture documented in `docs/architecture.md` is still planned or only partially represented in the repo.
