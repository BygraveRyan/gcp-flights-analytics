-- ============================================================
-- dim_date — Star schema: static date dimension
-- Grain: one row per calendar day (2020-2030 spine)
-- No SCD-2; this dimension never changes once populated.
-- Project: flights-analytics-prod | Dataset: flights_dw
-- Region:  europe-west2
-- ============================================================

CREATE OR REPLACE TABLE `flights-analytics-prod.flights_dw.dim_date`
(
  date_sk       STRING  NOT NULL,  -- PK: YYYYMMDD surrogate key
  full_date     DATE    NOT NULL,
  year          INT64   NOT NULL,
  month         INT64   NOT NULL,
  day_of_month  INT64   NOT NULL,
  day_name      STRING  NOT NULL,
  month_name    STRING  NOT NULL,
  quarter       INT64   NOT NULL,
  is_weekend    BOOL    NOT NULL
)
OPTIONS (
  description = 'Static calendar dimension, spine 2020-2030. No SCD-2 required.'
);
