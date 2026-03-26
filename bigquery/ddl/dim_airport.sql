-- ============================================================
-- dim_airport — Star schema: airport dimension (role-playing)
-- Grain: one row per airport version (SCD Type 2)
-- Role-playing: joined twice on fact_flights as
--   origin_airport_sk and destination_airport_sk
-- Partitioned by effective_from to support time-travel queries
-- Project: flights-analytics-prod | Dataset: flights_dw
-- Region:  europe-west2
-- ============================================================

CREATE OR REPLACE TABLE `flights-analytics-prod.flights_dw.dim_airport`
(
  airport_sk      STRING   NOT NULL,  -- PK: MD5 surrogate key
  airport_code    STRING   NOT NULL,  -- IATA 3-letter code
  airport_name    STRING   NOT NULL,
  city            STRING,
  state_code      STRING,
  country_code    STRING,
  latitude        FLOAT64,
  longitude       FLOAT64,
  elevation_ft    INT64,
  is_current      BOOL     NOT NULL,
  effective_from  DATE     NOT NULL,
  effective_to    DATE                -- NULL means current record
)
PARTITION BY effective_from
OPTIONS (
  description = 'Airport dimension with SCD Type 2 history. Role-playing dim — joined as both origin and destination on fact_flights. Partitioned by effective_from.'
);
