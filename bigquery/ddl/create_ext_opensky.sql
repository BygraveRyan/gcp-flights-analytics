-- External Table: Silver OpenSky on GCS
CREATE EXTERNAL TABLE IF NOT EXISTS `flights-analytics-prod.flights_raw.ext_silver_opensky`
WITH PARTITION COLUMNS (
  position_date DATE
)
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://flights-silver-flights-analytics-prod/opensky/*.parquet'],
  hive_partition_uri_prefix = 'gs://flights-silver-flights-analytics-prod/opensky',
  require_hive_partition_filter = false
);