-- Table: flights_staging.raw_bts_flights
-- Source: ingest_bts_csv (cloud_functions/ingest_bts_csv/main.py)
-- Run with: bq query --use_legacy_sql=false < bigquery/ddl/raw_bts_flights.sql

-- All columns match the BTS On-Time Performance CSV schema (BTS_SCHEMA in spark_jobs/bronze_to_silver.py).
-- The Cloud Function downloads the monthly BTS CSV ZIP and writes it verbatim to GCS Bronze.
-- row_id must be populated at insert time as:
--   TO_HEX(MD5(CONCAT(
--     COALESCE(Reporting_Airline, ''), '|',
--     COALESCE(Flight_Number_Reporting_Airline, ''), '|',
--     COALESCE(FlightDate, ''), '|',
--     COALESCE(Origin, ''), '|',
--     COALESCE(Dest, '')
--   )))

CREATE TABLE IF NOT EXISTS `flights-analytics-prod.flights_staging.raw_bts_flights`
(
  -- Surrogate key: MD5(Reporting_Airline | Flight_Number | FlightDate | Origin | Dest), populated at insert time
  row_id                          STRING    OPTIONS(description="Surrogate key: MD5 of natural key fields, populated at insert time"),

  -- BTS On-Time Performance CSV fields (verbatim column names from BTS source)
  Year                            INT64     OPTIONS(description="Year of the flight"),
  Month                           INT64     OPTIONS(description="Month of the flight (1-12)"),
  DayofMonth                      INT64     OPTIONS(description="Day of the month (1-31)"),
  DayOfWeek                       INT64     OPTIONS(description="Day of week (1=Monday, 7=Sunday)"),
  FlightDate                      STRING    OPTIONS(description="Flight date in YYYY-MM-DD format (partition key source)"),
  Reporting_Airline               STRING    OPTIONS(description="IATA carrier code of the reporting airline"),
  Tail_Number                     STRING    OPTIONS(description="Aircraft tail number / registration"),
  Flight_Number_Reporting_Airline STRING    OPTIONS(description="Flight number assigned by the reporting airline"),
  Origin                          STRING    OPTIONS(description="Origin airport IATA code"),
  OriginCityName                  STRING    OPTIONS(description="Origin city and state name"),
  OriginState                     STRING    OPTIONS(description="Origin state abbreviation"),
  Dest                            STRING    OPTIONS(description="Destination airport IATA code"),
  DestCityName                    STRING    OPTIONS(description="Destination city and state name"),
  DestState                       STRING    OPTIONS(description="Destination state abbreviation"),
  CRSDepTime                      STRING    OPTIONS(description="Scheduled departure time (hhmm local)"),
  DepTime                         STRING    OPTIONS(description="Actual departure time (hhmm local)"),
  DepDelay                        FLOAT64   OPTIONS(description="Departure delay in minutes (negative = early)"),
  TaxiOut                         FLOAT64   OPTIONS(description="Taxi-out time in minutes"),
  WheelsOff                       STRING    OPTIONS(description="Wheels-off time (hhmm local)"),
  WheelsOn                        STRING    OPTIONS(description="Wheels-on time (hhmm local)"),
  TaxiIn                          FLOAT64   OPTIONS(description="Taxi-in time in minutes"),
  CRSArrTime                      STRING    OPTIONS(description="Scheduled arrival time (hhmm local)"),
  ArrTime                         STRING    OPTIONS(description="Actual arrival time (hhmm local)"),
  ArrDelay                        FLOAT64   OPTIONS(description="Arrival delay in minutes (negative = early)"),
  Cancelled                       FLOAT64   OPTIONS(description="1.0 if flight was cancelled, 0.0 otherwise"),
  CancellationCode                STRING    OPTIONS(description="Reason for cancellation: A=Carrier, B=Weather, C=NAS, D=Security"),
  Diverted                        FLOAT64   OPTIONS(description="1.0 if flight was diverted, 0.0 otherwise"),
  CRSElapsedTime                  FLOAT64   OPTIONS(description="Scheduled elapsed time in minutes"),
  ActualElapsedTime               FLOAT64   OPTIONS(description="Actual elapsed time in minutes"),
  AirTime                         FLOAT64   OPTIONS(description="Time in the air in minutes"),
  Distance                        FLOAT64   OPTIONS(description="Great-circle distance between origin and destination in miles"),
  CarrierDelay                    FLOAT64   OPTIONS(description="Carrier-attributed delay in minutes"),
  WeatherDelay                    FLOAT64   OPTIONS(description="Weather-attributed delay in minutes"),
  NASDelay                        FLOAT64   OPTIONS(description="National Airspace System delay in minutes"),
  SecurityDelay                   FLOAT64   OPTIONS(description="Security delay in minutes"),
  LateAircraftDelay               FLOAT64   OPTIONS(description="Late arriving aircraft delay in minutes"),

  -- Ingestion metadata added by the Cloud Function
  ingestion_timestamp             TIMESTAMP OPTIONS(description="UTC timestamp when the Cloud Function ingested this batch"),

  -- Partition pseudo-column (value populated from FlightDate at load time)
  flight_date                     DATE      OPTIONS(description="Partition column: PARSE_DATE('%Y-%m-%d', FlightDate), populated at insert time")
)
PARTITION BY flight_date
-- Clustered by Origin and Dest for efficient route-based queries
CLUSTER BY Origin, Dest
OPTIONS(
  description="Raw BTS On-Time Performance flight records ingested by fn-ingest-bts-csv. One row per BTS CSV record.",
  require_partition_filter = false
);
