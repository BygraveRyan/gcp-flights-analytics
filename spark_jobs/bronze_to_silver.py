"""
Dataproc Serverless PySpark Job: Bronze → Silver transformation.
- Reads raw BTS CSV ZIP and FR24 NDJSON from GCS Bronze
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

# Default Constants
PROJECT_ID = "flights-analytics-prod"
DEFAULT_BRONZE_BUCKET = f"gs://flights-bronze-{PROJECT_ID}"
DEFAULT_SILVER_BUCKET = f"gs://flights-silver-{PROJECT_ID}"

# Unit conversion constants
_FT_TO_M = 0.3048
_KT_TO_MS = 0.514444

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


def process_bts_bronze(spark: SparkSession, run_date: str, bronze_bucket: str, silver_bucket: str) -> int:
    """Read BTS CSV from Bronze, enforce schema, deduplicate, write Silver Parquet."""
    year = run_date[:4]
    month = run_date[4:6]
    bronze_path = f"{bronze_bucket}/bts/{year}/{month}/*.zip"

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

    silver_path = f"{silver_bucket}/bts"
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


def process_fr24_bronze(spark: SparkSession, run_date: str, bronze_bucket: str, silver_bucket: str) -> int:
    """Read FR24 NDJSON from Bronze, schema enforce, write Silver Parquet."""
    year = run_date[:4]
    month = run_date[4:6]
    day = run_date[6:8]
    bronze_path = f"{bronze_bucket}/fr24/{year}/{month}/{day}/*.ndjson"

    logger.info(f"Reading FR24 bronze from: {bronze_path}")
    raw_df = spark.read.json(bronze_path)

    silver_df = (
        raw_df.withColumn("position_date", F.to_date(F.col("ingestion_timestamp")))
        .withColumn("icao24", F.upper(F.trim(F.col("hex"))))
        .withColumn("callsign", F.trim(F.col("callsign")))
        .withColumn("latitude", F.col("lat").cast(DoubleType()))
        .withColumn("longitude", F.col("lon").cast(DoubleType()))
        .withColumn("baro_altitude_m", (F.col("alt").cast(DoubleType()) * _FT_TO_M))
        .withColumn("velocity_ms", (F.col("gspeed").cast(DoubleType()) * _KT_TO_MS))
        .withColumn("on_ground", F.col("on_ground").cast(BooleanType()))
        .withColumn("vertical_rate_ms", F.col("vspeed").cast(DoubleType()))
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

    silver_path = f"{silver_bucket}/fr24"
    (
        silver_df.repartition(F.col("position_date"))
        .write.mode("overwrite")
        .partitionBy("position_date")
        .parquet(silver_path)
    )

    row_count = silver_df.count()
    logger.info(f"FR24 Silver: wrote {row_count:,} rows")
    return row_count


def main():
    # python bronze_to_silver.py <run_date> <bronze_bucket> <silver_bucket>
    run_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).strftime("%Y%m%d")
    bronze_bucket = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_BRONZE_BUCKET
    silver_bucket = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_SILVER_BUCKET

    logger.info(f"Starting Bronze → Silver pipeline for run_date={run_date}")
    logger.info(f"Using bronze_bucket={bronze_bucket}, silver_bucket={silver_bucket}")

    spark = get_spark_session()

    try:
        bts_rows = process_bts_bronze(spark, run_date, bronze_bucket, silver_bucket)
        fr24_rows = process_fr24_bronze(spark, run_date, bronze_bucket, silver_bucket)
        logger.info(
            f"Bronze→Silver complete. BTS={bts_rows:,} rows, FR24={fr24_rows:,} rows"
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
