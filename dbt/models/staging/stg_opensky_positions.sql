-- Staging: 1:1 from external Silver OpenSky table
{{ config(
    materialized='view',
    tags=['staging', 'opensky']
) }}

WITH source AS (
    SELECT *
    FROM {{ source('flights_raw', 'ext_silver_opensky') }}
    WHERE position_date >= DATE('{{ var("start_date") }}')
),

renamed AS (
    SELECT
        CAST(position_date AS DATE)          AS position_date,
        UPPER(TRIM(icao24))                  AS icao24,
        TRIM(callsign)                       AS callsign,
        TRIM(origin_country)                 AS origin_country,
        CAST(latitude AS FLOAT64)            AS latitude,
        CAST(longitude AS FLOAT64)           AS longitude,
        CAST(baro_altitude_m AS FLOAT64)     AS baro_altitude_m,
        CAST(velocity_ms AS FLOAT64)         AS velocity_ms,
        CAST(on_ground AS BOOL)              AS on_ground,
        CAST(vertical_rate_ms AS FLOAT64)    AS vertical_rate_ms,
        ingestion_timestamp
    FROM source
)

SELECT * FROM renamed