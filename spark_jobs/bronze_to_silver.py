"""
Dataproc Serverless PySpark Job: Bronze → Silver transformation.
- Reads raw BTS CSV ZIP and OpenSky NDJSON from GCS Bronze
- Enforces schema, deduplicates, casts types
- Writes Parquet to GCS Silver partitioned by flight_date
Python 3.12 / PySpark 3.5
"""

import logging
import sys
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (BooleanType, DateType, DoubleType, IntegerType,
                               StringType, StructField, StructType,
                               TimestampType)

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

PROJECT_ID = "flights-analytics-prod"
BRONZE_BUCKET = f"gs://flights-bronze-{PROJECT_ID}"
SILVER_BUCKET = f"gs://flights-silver-{PROJECT_ID}"

BTS_SCHEMA = StructType(
    [
        StructField("Year", IntegerType(), True),
        StructField("Month", IntegerType(), True),
        StructField("DayofMonth", IntegerType(), True),
        StructField("DayOfWeek", IntegerType(), True),
        StructField("FlightDate", StringType(), True),
        StructField("Reporting_Airline", StringType(), True),
        StructField("Tail_Number", StringType(), True),
        StructField("Flight_Number_Reporting_Airline", StringType(), True),
        StructField("Origin", StringType(), True),
        StructField("OriginCityName", StringType(), True),
        StructField("OriginState", StringType(), True),
        StructField("Dest", StringType(), True),
        StructField("DestCityName", StringType(), True),
        StructField("DestState", StringType(), True),
        StructField("CRSDepTime", StringType(), True),
        StructField("DepTime", StringType(), True),
        StructField("DepDelay", DoubleType(), True),
        StructField("TaxiOut", DoubleType(), True),
        StructField("WheelsOff", StringType(), True),
        StructField("WheelsOn", StringType(), True),
        StructField("TaxiIn", DoubleType(), True),
        StructField("CRSArrTime", StringType(), True),
        StructField("ArrTime", StringType(), True),
        StructField("ArrDelay", DoubleType(), True),
        StructField("Cancelled", DoubleType(), True),
        StructField("CancellationCode", StringType(), True),
        StructField("Diverted", DoubleType(), True),
        StructField("CRSElapsedTime", DoubleType(), True),
        StructField("ActualElapsedTime", DoubleType(), True),
        StructField("AirTime", DoubleType(), True),
        StructField("Distance", DoubleType(), True),
        StructField("CarrierDelay", DoubleType(), True),
        StructField("WeatherDelay", DoubleType(), True),
        StructField("NASDelay", DoubleType(), True),
        StructField("SecurityDelay", DoubleType(), True),
        StructField("LateAircraftDelay", DoubleType(), True),
    ]
)


def get_spark_session() -> SparkSession:
    return (
        SparkSession.builder.appName("flights-bronze-to-silver")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .config(
            "spark.hadoop.fs.gs.impl",
            "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem",
        )
        .config("spark.hadoop.google.cloud.auth.service.account.enable", "true")
        .getOrCreate()
    )


def process_bts_bronze(spark: SparkSession, run_date: str) -> int:
    """Read BTS CSV from Bronze, enforce schema, deduplicate, write Silver Parquet."""
    year = run_date[:4]
    month = run_date[4:6]
    bronze_path = f"{BRONZE_BUCKET}/bts/{year}/{month}/*.zip"

    logger.info(f"Reading BTS bronze from: {bronze_path}")
    raw_df = (
        spark.read.option("header", "true")
        .option("inferSchema", "false")
        .schema(BTS_SCHEMA)
        .csv(bronze_path)
    )

    silver_df = (
        raw_df.filter(F.col("FlightDate").isNotNull())
        .withColumn("flight_date", F.to_date(F.col("FlightDate"), "yyyy-MM-dd"))
        .withColumn("carrier_code", F.trim(F.col("Reporting_Airline")))
        .withColumn("tail_number", F.upper(F.trim(F.col("Tail_Number"))))
        .withColumn("flight_number", F.trim(F.col("Flight_Number_Reporting_Airline")))
        .withColumn("origin_airport", F.upper(F.trim(F.col("Origin"))))
        .withColumn("dest_airport", F.upper(F.trim(F.col("Dest"))))
        .withColumn("dep_delay_minutes", F.col("DepDelay").cast(DoubleType()))
        .withColumn("arr_delay_minutes", F.col("ArrDelay").cast(DoubleType()))
        .withColumn("is_cancelled", (F.col("Cancelled") == 1.0).cast(BooleanType()))
        .withColumn("is_diverted", (F.col("Diverted") == 1.0).cast(BooleanType()))
        .withColumn("distance_miles", F.col("Distance").cast(DoubleType()))
        .withColumn("air_time_minutes", F.col("AirTime").cast(DoubleType()))
        .withColumn("carrier_delay_minutes", F.col("CarrierDelay").cast(DoubleType()))
        .withColumn("weather_delay_minutes", F.col("WeatherDelay").cast(DoubleType()))
        .withColumn("nas_delay_minutes", F.col("NASDelay").cast(DoubleType()))
        .withColumn("cancellation_code", F.col("CancellationCode"))
        .withColumn(
            "ingestion_timestamp",
            F.lit(datetime.now(timezone.utc).isoformat()).cast(TimestampType()),
        )
        .withColumn(
            "row_hash",
            F.md5(
                F.concat_ws(
                    "|",
                    F.col("carrier_code"),
                    F.col("flight_number"),
                    F.col("flight_date"),
                    F.col("origin_airport"),
                    F.col("dest_airport"),
                )
            ),
        )
        .dropDuplicates(["row_hash"])
        .select(
            "flight_date",
            "carrier_code",
            "tail_number",
            "flight_number",
            "origin_airport",
            "dest_airport",
            "dep_delay_minutes",
            "arr_delay_minutes",
            "is_cancelled",
            "is_diverted",
            "distance_miles",
            "air_time_minutes",
            "carrier_delay_minutes",
            "weather_delay_minutes",
            "nas_delay_minutes",
            "cancellation_code",
            "row_hash",
            "ingestion_timestamp",
        )
    )

    silver_path = f"{SILVER_BUCKET}/bts"
    logger.info(f"Writing BTS Silver Parquet to: {silver_path}")
    (
        silver_df.repartition(F.col("flight_date"))
        .write.mode("overwrite")
        .partitionBy("flight_date")
        .parquet(silver_path)
    )

    row_count = silver_df.count()
    logger.info(f"BTS Silver: wrote {row_count:,} rows")
    return row_count


def process_opensky_bronze(spark: SparkSession, run_date: str) -> int:
    """Read OpenSky NDJSON from Bronze, schema enforce, write Silver Parquet."""
    year = run_date[:4]
    month = run_date[4:6]
    day = run_date[6:8]
    bronze_path = f"{BRONZE_BUCKET}/opensky/{year}/{month}/{day}/*.ndjson"

    logger.info(f"Reading OpenSky bronze from: {bronze_path}")
    raw_df = spark.read.json(bronze_path)

    silver_df = (
        raw_df.withColumn("position_date", F.to_date(F.col("ingestion_timestamp")))
        .withColumn("icao24", F.upper(F.trim(F.col("icao24"))))
        .withColumn("callsign", F.trim(F.col("callsign")))
        .withColumn("latitude", F.col("latitude").cast(DoubleType()))
        .withColumn("longitude", F.col("longitude").cast(DoubleType()))
        .withColumn("baro_altitude_m", F.col("baro_altitude").cast(DoubleType()))
        .withColumn("velocity_ms", F.col("velocity").cast(DoubleType()))
        .withColumn("on_ground", F.col("on_ground").cast(BooleanType()))
        .withColumn("vertical_rate_ms", F.col("vertical_rate").cast(DoubleType()))
        .withColumn(
            "ingestion_timestamp",
            F.col("ingestion_timestamp").cast(TimestampType()),
        )
        .filter(F.col("icao24").isNotNull())
        .dropDuplicates(["icao24", "ingestion_timestamp"])
        .select(
            "position_date",
            "icao24",
            "callsign",
            "origin_country",
            "latitude",
            "longitude",
            "baro_altitude_m",
            "velocity_ms",
            "on_ground",
            "vertical_rate_ms",
            "ingestion_timestamp",
        )
    )

    silver_path = f"{SILVER_BUCKET}/opensky"
    (
        silver_df.repartition(F.col("position_date"))
        .write.mode("overwrite")
        .partitionBy("position_date")
        .parquet(silver_path)
    )

    row_count = silver_df.count()
    logger.info(f"OpenSky Silver: wrote {row_count:,} rows")
    return row_count


def main():
    if len(sys.argv) < 2:
        run_date = datetime.now(timezone.utc).strftime("%Y%m%d")
    else:
        run_date = sys.argv[1]

    logger.info(f"Starting Bronze → Silver pipeline for run_date={run_date}")
    spark = get_spark_session()

    try:
        bts_rows = process_bts_bronze(spark, run_date)
        opensky_rows = process_opensky_bronze(spark, run_date)
        logger.info(
            f"Bronze→Silver complete. BTS={bts_rows:,} rows, OpenSky={opensky_rows:,} rows"
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
