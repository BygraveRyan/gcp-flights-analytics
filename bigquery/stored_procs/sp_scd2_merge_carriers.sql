-- SCD-2 MERGE stored procedure for dim_carriers
-- Uses MD5 row hash for change detection
CREATE OR REPLACE PROCEDURE `flights-analytics-prod.flights_dw.sp_scd2_merge_carriers`()
BEGIN
  DECLARE run_date DATE DEFAULT CURRENT_DATE();

  -- Step 1: Stage new/changed records with row hash
  CREATE OR REPLACE TEMP TABLE staging_carriers AS
  SELECT
    MD5(CONCAT(
      COALESCE(Code, ''),
      '|',
      COALESCE(Description, '')
    )) AS row_hash,
    MD5(Code) AS carrier_sk,
    Code AS carrier_code,
    Description AS carrier_name,
    CAST(NULL AS STRING) AS carrier_group -- Placeholder as public source lacks this
  FROM `bigquery-public-data.airline_id.airline_id`
  WHERE Code IS NOT NULL;

  -- Step 2: Expire records where row_hash has changed
  UPDATE `flights-analytics-prod.flights_dw.dim_carriers` AS dim
  SET
    is_current    = FALSE,
    effective_to  = DATE_SUB(run_date, INTERVAL 1 DAY),
    dbt_updated_at = CURRENT_TIMESTAMP()
  WHERE dim.is_current = TRUE
    AND dim.carrier_code IN (
      SELECT s.carrier_code
      FROM staging_carriers s
      JOIN `flights-analytics-prod.flights_dw.dim_carriers` d
        ON s.carrier_code = d.carrier_code
       AND d.is_current = TRUE
       AND s.row_hash != d.row_hash
    );

  -- Step 3: Insert new and changed records
  INSERT INTO `flights-analytics-prod.flights_dw.dim_carriers`
  (
    carrier_sk, carrier_code, carrier_name, carrier_group,
    row_hash, is_current, effective_from, effective_to,
    dbt_updated_at, dbt_created_at
  )
  SELECT
    s.carrier_sk,
    s.carrier_code,
    s.carrier_name,
    s.carrier_group,
    s.row_hash,
    TRUE                AS is_current,
    run_date            AS effective_from,
    NULL                AS effective_to,
    CURRENT_TIMESTAMP() AS dbt_updated_at,
    CURRENT_TIMESTAMP() AS dbt_created_at
  FROM staging_carriers s
  WHERE NOT EXISTS (
    SELECT 1
    FROM `flights-analytics-prod.flights_dw.dim_carriers` d
    WHERE d.carrier_code = s.carrier_code
      AND d.is_current = TRUE
  );
END;