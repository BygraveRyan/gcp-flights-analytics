-- ============================================================
-- BigQuery DDL — flights-analytics-prod
-- All tables: europe-west2
-- ============================================================

-- ── External Table: Silver BTS on GCS ─────────────────────────
-- Created in Phase 3 to unblock Dataplex DQ which requires a BQ table source.
CREATE EXTERNAL TABLE IF NOT EXISTS `flights-analytics-prod.flights_raw.ext_silver_bts`
WITH PARTITION COLUMNS (
  flight_date DATE
)
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://flights-silver-flights-analytics-prod/bts/*.parquet'],
  hive_partition_uri_prefix = 'gs://flights-silver-flights-analytics-prod/bts',
  require_hive_partition_filter = false
);
