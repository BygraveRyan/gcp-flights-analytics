-- ============================================================
-- dim_carrier — Star schema: carrier (airline) dimension
-- Grain: one row per carrier version (SCD Type 2)
-- Surrogate key: MD5 hash of carrier_code + effective_from
-- Partitioned by effective_from to support time-travel queries
-- Project: flights-analytics-prod | Dataset: flights_dw
-- Region:  europe-west2
-- ============================================================

CREATE OR REPLACE TABLE `flights-analytics-prod.flights_dw.dim_carrier`
(
  carrier_sk      STRING  NOT NULL,  -- PK: MD5 surrogate key
  carrier_code    STRING  NOT NULL,
  carrier_name    STRING  NOT NULL,
  carrier_group   STRING,
  row_hash        STRING  NOT NULL,  -- MD5 of business key fields; used by SCD-2 MERGE
  is_current      BOOL    NOT NULL,
  effective_from  DATE    NOT NULL,
  effective_to    DATE               -- NULL means current record
)
PARTITION BY effective_from
OPTIONS (
  description = 'Carrier (airline) dimension with SCD Type 2 history. Partitioned by effective_from.'
);
