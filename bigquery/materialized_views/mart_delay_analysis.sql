-- ============================================================
-- mart_delay_analysis — Materialized View
-- Powers: Delay breakdown and AI commentary page in Looker Studio
-- Grain: one row per carrier + month (via DATE_TRUNC)
-- Only includes months with delays > 0 for focused analysis
-- Refreshes hourly; Gemini can use this for insights
-- ============================================================

CREATE OR REPLACE MATERIALIZED VIEW `flights-analytics-prod.flights_dw.mart_delay_analysis`
OPTIONS (
  enable_refresh = true,
  refresh_interval_minutes = 60,
  description = 'Monthly delay attribution by source (carrier, weather, NAS). Powers Looker Studio delay analysis and AI commentary page.'
)
AS
SELECT
  DATE_TRUNC(f.flight_date, MONTH) AS year_month,
  f.carrier_code,
  ROUND(AVG(f.carrier_delay_minutes), 2) AS avg_carrier_delay,
  ROUND(AVG(f.weather_delay_minutes), 2) AS avg_weather_delay,
  ROUND(AVG(f.nas_delay_minutes), 2) AS avg_nas_delay,
  ROUND(SUM(f.carrier_delay_minutes) + SUM(f.weather_delay_minutes) + SUM(f.nas_delay_minutes), 2) AS total_delay_minutes,
  ROUND(
    COALESCE(SUM(f.weather_delay_minutes), 0) / NULLIF(
      SUM(f.carrier_delay_minutes) + SUM(f.weather_delay_minutes) + SUM(f.nas_delay_minutes),
      0
    ),
    4
  ) AS weather_delay_share,
  ROUND(
    COALESCE(SUM(f.carrier_delay_minutes), 0) / NULLIF(
      SUM(f.carrier_delay_minutes) + SUM(f.weather_delay_minutes) + SUM(f.nas_delay_minutes),
      0
    ),
    4
  ) AS carrier_delay_share
FROM
  `flights-analytics-prod.flights_dw.fact_flights` f
GROUP BY
  DATE_TRUNC(f.flight_date, MONTH),
  f.carrier_code
HAVING
  (SUM(f.carrier_delay_minutes) + SUM(f.weather_delay_minutes) + SUM(f.nas_delay_minutes)) > 0
;
