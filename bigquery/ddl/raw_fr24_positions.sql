-- Table: flights_staging.raw_fr24_positions
-- Source: ingest_fr24 (cloud_functions/ingest_fr24/main.py)
-- Run with: bq query --use_legacy_sql=false < bigquery/ddl/raw_fr24_positions.sql

-- All fields are written verbatim from the FR24 API v1 /full endpoint response.
-- The Cloud Function copies each flight object and appends ingestion_timestamp.
-- row_id must be populated at insert time as:
--   TO_HEX(MD5(CONCAT(COALESCE(fr24_id, ''), '|', COALESCE(CAST(ingestion_timestamp AS STRING), ''))))

CREATE TABLE IF NOT EXISTS `flights-analytics-prod.flights_staging.raw_fr24_positions`
(
  -- Surrogate key: MD5(fr24_id || ingestion_timestamp), populated at insert time
  row_id                STRING    OPTIONS(description="Surrogate key: MD5 of fr24_id + ingestion_timestamp, populated at insert time"),

  -- FR24 API v1 /full response fields
  fr24_id               STRING    OPTIONS(description="FlightRadar24 unique flight identifier"),
  flight                STRING    OPTIONS(description="Flight number (e.g. BAW123)"),
  callsign              STRING    OPTIONS(description="ATC callsign"),
  hex                   STRING    OPTIONS(description="ICAO 24-bit Mode-S hex address (raw from API)"),
  reg                   STRING    OPTIONS(description="Aircraft registration (tail number)"),
  type                  STRING    OPTIONS(description="ICAO aircraft type designator (e.g. B738)"),
  lat                   FLOAT64   OPTIONS(description="Latitude in decimal degrees"),
  lon                   FLOAT64   OPTIONS(description="Longitude in decimal degrees"),
  track                 INT64     OPTIONS(description="True track / heading in degrees (0-360)"),
  alt                   INT64     OPTIONS(description="Barometric altitude in feet"),
  gspeed                INT64     OPTIONS(description="Ground speed in knots"),
  vspeed                INT64     OPTIONS(description="Vertical speed in feet per minute"),
  squawk                STRING    OPTIONS(description="Mode-A squawk code (4-digit octal)"),
  on_ground             BOOL      OPTIONS(description="True if aircraft is on the ground"),
  orig_iata             STRING    OPTIONS(description="Origin airport IATA code"),
  orig_icao             STRING    OPTIONS(description="Origin airport ICAO code"),
  dest_iata             STRING    OPTIONS(description="Destination airport IATA code"),
  dest_icao             STRING    OPTIONS(description="Destination airport ICAO code"),
  airline_iata          STRING    OPTIONS(description="Operating airline IATA code"),
  airline_icao          STRING    OPTIONS(description="Operating airline ICAO code"),
  operating_as          STRING    OPTIONS(description="Flight number as operated (may differ from painted_as)"),
  painted_as            STRING    OPTIONS(description="Livery/airline the aircraft is painted as"),
  eta                   INT64     OPTIONS(description="Estimated arrival time as UNIX epoch seconds"),
  timestamp             INT64     OPTIONS(description="Position fix time as UNIX epoch seconds from FR24 API"),
  source                STRING    OPTIONS(description="Data source identifier from FR24 API"),
  origin_country        STRING    OPTIONS(description="Country of origin derived from ICAO hex range"),

  -- Ingestion metadata added by the Cloud Function
  ingestion_timestamp   TIMESTAMP OPTIONS(description="UTC timestamp when the Cloud Function fetched this record"),

  -- Partition pseudo-column (value populated from ingestion_timestamp at load time)
  ingestion_date        DATE      OPTIONS(description="Partition column: DATE(ingestion_timestamp), populated at insert time")
)
PARTITION BY ingestion_date
-- Clustered by callsign and hex (hex is the ICAO 24-bit address, i.e. icao24)
CLUSTER BY callsign, hex
OPTIONS(
  description="Raw FlightRadar24 flight positions ingested by fn-ingest-fr24. One row per flight per fetch cycle.",
  require_partition_filter = false
);
