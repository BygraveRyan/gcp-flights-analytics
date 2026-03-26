-- ============================================================
-- fact_flights — Star schema: core flight segment fact table
-- Grain: one row per flight segment (BTS On-Time Performance)
-- Partitioned by flight_date: aligns with BTS monthly loads;
--   enables partition pruning on date-range queries.
-- Clustered by carrier_code, origin_airport_code: the most
--   common filter and group-by axes in analytical queries.
-- Project: flights-analytics-prod | Dataset: flights_dw
-- Region:  europe-west2
-- ============================================================

CREATE OR REPLACE TABLE `flights-analytics-prod.flights_dw.fact_flights`
(
  flight_sk              STRING     NOT NULL,  -- PK: MD5 surrogate key
  date_sk                STRING     NOT NULL,  -- FK → dim_date.date_sk
  carrier_sk             STRING     NOT NULL,  -- FK → dim_carrier.carrier_sk
  origin_airport_sk      STRING     NOT NULL,  -- FK → dim_airport.airport_sk (origin role)
  dest_airport_sk        STRING     NOT NULL,  -- FK → dim_airport.airport_sk (destination role)
  carrier_code           STRING     NOT NULL,
  origin_airport_code    STRING     NOT NULL,
  dest_airport_code      STRING     NOT NULL,
  flight_number          STRING,
  tail_number            STRING,
  flight_date            DATE       NOT NULL,  -- partition column
  dep_delay_minutes      FLOAT64,
  arr_delay_minutes      FLOAT64,
  distance_miles         FLOAT64,
  air_time_minutes       FLOAT64,
  is_cancelled           BOOL,
  is_diverted            BOOL,
  cancellation_code      STRING,
  delay_category         STRING,
  carrier_delay_minutes  FLOAT64,
  weather_delay_minutes  FLOAT64,
  nas_delay_minutes      FLOAT64,
  ingestion_timestamp    TIMESTAMP  NOT NULL
)
PARTITION BY flight_date
CLUSTER BY carrier_code, origin_airport_code
OPTIONS (
  description             = 'Flight segment fact table. Grain: one row per BTS On-Time Performance segment. Partitioned by flight_date, clustered by carrier_code and origin_airport_code.',
  require_partition_filter = false
);
