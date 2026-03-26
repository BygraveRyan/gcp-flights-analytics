-- ============================================================
-- fact_positions — Star schema: FR24 live position fact table
-- Grain: one row per FR24 position record
-- Partitioned by position_date: FR24 data arrives daily;
--   partition pruning is critical for this high-volume table.
-- Clustered by icao24: primary lookup key for aircraft traces
--   and join path to dim_carrier via callsign resolution.
-- Project: flights-analytics-prod | Dataset: flights_dw
-- Region:  europe-west2
-- ============================================================

CREATE OR REPLACE TABLE `flights-analytics-prod.flights_dw.fact_positions`
(
  position_sk          STRING     NOT NULL,  -- PK: MD5 surrogate key
  date_sk              STRING     NOT NULL,  -- FK → dim_date.date_sk
  position_date        DATE       NOT NULL,  -- partition column
  icao24               STRING     NOT NULL,  -- ICAO 24-bit hex aircraft address
  callsign             STRING,
  latitude             FLOAT64,
  longitude            FLOAT64,
  altitude_metres      FLOAT64,
  velocity_ms          FLOAT64,
  vertical_speed       INT64,
  on_ground            BOOL,
  ingestion_timestamp  TIMESTAMP  NOT NULL
)
PARTITION BY position_date
CLUSTER BY icao24
OPTIONS (
  description             = 'FR24 live position fact table. Grain: one row per FR24 position record. Partitioned by position_date, clustered by icao24.',
  require_partition_filter = false
);
