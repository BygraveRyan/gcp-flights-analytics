{{ config(
    materialized='table',
    tags=['flights_analytics'],
    labels={'project': 'flights-analytics-prod'}
) }}

WITH source_data AS (
    SELECT
        *
    FROM {{ ref('stg_...') }}
),

transformed AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['natural_key']) }} AS pk_id,
        *,
        CURRENT_DATE() AS effective_from,
        NULL AS effective_to,
        TRUE AS is_current,
        MD5(CAST(business_column AS STRING)) AS row_hash
    FROM source_data
)

SELECT * FROM transformed
