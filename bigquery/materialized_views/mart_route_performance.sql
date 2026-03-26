-- ============================================================
-- mart_route_performance — Materialized View
-- Powers: Route map and route ranking pages in Looker Studio
-- Grain: one row per route (origin + destination + carrier)
-- Includes airport geo coordinates for map visualization
-- Refreshes hourly
-- ============================================================

CREATE OR REPLACE MATERIALIZED VIEW `flights-analytics-prod.flights_dw.mart_route_performance`
CLUSTER BY origin_airport_code
OPTIONS (
  enable_refresh = true,
  refresh_interval_minutes = 60,
  description = 'Route-level performance metrics with geo coordinates. Powers Looker Studio route map and ranking pages.'
)
AS
SELECT
  f.origin_airport_code,
  f.dest_airport_code,
  f.carrier_code,
  dim_origin.airport_name AS origin_airport_name,
  dim_dest.airport_name AS dest_airport_name,
  dim_origin.latitude AS origin_latitude,
  dim_origin.longitude AS origin_longitude,
  dim_dest.latitude AS dest_latitude,
  dim_dest.longitude AS dest_longitude,
  COUNT(*) AS total_flights,
  ROUND(AVG(f.arr_delay_minutes), 2) AS avg_arr_delay,
  ROUND(COUNTIF(f.delay_category = 'On Time') / COUNT(*), 4) AS on_time_rate,
  ROUND(COUNTIF(f.delay_category = 'Severe') / COUNT(*), 4) AS pct_severe_delays
FROM
  `flights-analytics-prod.flights_dw.fact_flights` f
  LEFT JOIN `flights-analytics-prod.flights_dw.dim_airport` dim_origin
    ON f.origin_airport_sk = dim_origin.airport_sk
    AND dim_origin.is_current = TRUE
  LEFT JOIN `flights-analytics-prod.flights_dw.dim_airport` dim_dest
    ON f.dest_airport_sk = dim_dest.airport_sk
    AND dim_dest.is_current = TRUE
GROUP BY
  f.origin_airport_code,
  f.dest_airport_code,
  f.carrier_code,
  dim_origin.airport_name,
  dim_dest.airport_name,
  dim_origin.latitude,
  dim_origin.longitude,
  dim_dest.latitude,
  dim_dest.longitude
;
