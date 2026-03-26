-- ============================================================
-- mart_carrier_daily — Materialized View
-- Powers: Carrier Performance Dashboard page in Looker Studio
-- Grain: one row per carrier + flight_date
-- Refreshes hourly to keep dashboard current
-- ============================================================

CREATE OR REPLACE MATERIALIZED VIEW `flights-analytics-prod.flights_dw.mart_carrier_daily`
PARTITION BY flight_date
OPTIONS (
  enable_refresh = true,
  refresh_interval_minutes = 60,
  description = 'Carrier daily performance metrics. Powers Looker Studio carrier performance dashboard.'
)
AS
SELECT
  f.flight_date,
  f.carrier_code,
  c.carrier_name,
  COUNT(*) AS total_flights,
  COUNTIF(f.is_cancelled = TRUE) AS cancelled_flights,
  ROUND(COUNTIF(f.is_cancelled = TRUE) / COUNT(*), 4) AS cancellation_rate,
  ROUND(AVG(f.dep_delay_minutes), 2) AS avg_dep_delay,
  ROUND(AVG(f.arr_delay_minutes), 2) AS avg_arr_delay,
  COUNTIF(f.delay_category = 'On Time') AS on_time_count,
  ROUND(COUNTIF(f.delay_category = 'On Time') / COUNT(*), 4) AS on_time_rate,
  COUNTIF(f.delay_category = 'Severe') AS severe_delay_count
FROM
  `flights-analytics-prod.flights_dw.fact_flights` f
  LEFT JOIN `flights-analytics-prod.flights_dw.dim_carrier` c
    ON f.carrier_sk = c.carrier_sk
    AND c.is_current = TRUE
GROUP BY
  f.flight_date,
  f.carrier_code,
  c.carrier_name
;
