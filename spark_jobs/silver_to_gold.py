"""
Dataproc Serverless PySpark Job: Silver → Gold transformation.
- Reads validated Silver Parquet
- Enriches with computed columns (total delay, delay category, surrogate keys)
- Computes route-level aggregations
- Writes Gold Parquet for BQ external table consumption
Python 3.12 / PySpark 3.5
"""

import logging
import sys
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, LongType

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# Default Constants
PROJECT_ID = "flights-analytics-prod"
DEFAULT_SILVER_BUCKET = f"gs://flights-silver-{PROJECT_ID}"
DEFAULT_GOLD_BUCKET = f"gs://flights-gold-{PROJECT_ID}"


def get_spark_session() -> SparkSession:
    """Creates a Spark Session with standard GCP configuration."""
    return (
        SparkSession.builder.appName("flights-silver-to-gold")
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


def build_fact_flights(spark: SparkSession, run_date: str, silver_bucket: str, gold_bucket: str) -> int:
    """Enrich Silver BTS with computed columns → Gold fact_flights Parquet."""
    silver_path = f"{silver_bucket}/bts"
    logger.info(f"Reading Silver BTS from: {silver_path}")

    silver_df = spark.read.parquet(silver_path)

    enriched_df = (
        silver_df.withColumn(
            "total_delay_minutes",
            F.when(
                F.col("is_cancelled"),
                F.lit(None).cast(DoubleType()),
            ).otherwise(F.coalesce(F.col("arr_delay_minutes"), F.lit(0.0))),
        )
        .withColumn(
            "delay_category",
            F.when(F.col("is_cancelled"), F.lit("CANCELLED"))
            .when(F.col("is_diverted"), F.lit("DIVERTED"))
            .when(F.col("total_delay_minutes") <= 0, F.lit("ON_TIME"))
            .when(F.col("total_delay_minutes") <= 15, F.lit("MINOR_DELAY"))
            .when(F.col("total_delay_minutes") <= 60, F.lit("MODERATE_DELAY"))
            .otherwise(F.lit("SEVERE_DELAY")),
        )
        .withColumn(
            "route_key",
            F.concat_ws("-", F.col("origin_airport"), F.col("dest_airport")),
        )
        .withColumn(
            "flight_surrogate_key",
            F.md5(
                F.concat_ws(
                    "|",
                    F.col("carrier_code"),
                    F.col("flight_number"),
                    F.col("flight_date").cast("string"),
                    F.col("origin_airport"),
                    F.col("dest_airport"),
                )
            ),
        )
    )

    gold_path = f"{gold_bucket}/fact_flights"
    logger.info(f"Writing fact_flights Gold to: {gold_path}")
    (
        enriched_df.repartition(F.col("flight_date"))
        .write.mode("overwrite")
        .partitionBy("flight_date")
        .parquet(gold_path)
    )
    
    row_count = enriched_df.count()
    logger.info(f"fact_flights Gold: wrote {row_count:,} rows")
    return row_count


def build_route_aggregates(spark: SparkSession, silver_bucket: str, gold_bucket: str) -> int:
    """Compute route-level daily aggregates → Gold mart_route_performance Parquet."""
    silver_df = spark.read.parquet(f"{silver_bucket}/bts")

    route_df = (
        silver_df.filter(~F.col("is_cancelled"))
        .groupBy("flight_date", "carrier_code", "origin_airport", "dest_airport")
        .agg(
            F.count("*").alias("total_flights"),
            F.avg("dep_delay_minutes").alias("avg_dep_delay_minutes"),
            F.avg("arr_delay_minutes").alias("avg_arr_delay_minutes"),
            F.percentile_approx("arr_delay_minutes", 0.5).alias(
                "median_arr_delay_minutes"
            ),
            F.percentile_approx("arr_delay_minutes", 0.95).alias(
                "p95_arr_delay_minutes"
            ),
            F.avg("distance_miles").alias("avg_distance_miles"),
            F.sum(F.when(F.col("arr_delay_minutes") > 60, 1).otherwise(0))
            .cast(LongType())
            .alias("severe_delay_count"),
        )
        .withColumn(
            "on_time_rate",
            F.round(
                1.0 - (F.col("severe_delay_count") / F.col("total_flights")),
                4,
            ),
        )
    )

    gold_path = f"{gold_bucket}/mart_route_performance"
    logger.info(f"Writing mart_route_performance Gold to: {gold_path}")
    (
        route_df.repartition(F.col("flight_date"))
        .write.mode("overwrite")
        .partitionBy("flight_date")
        .parquet(gold_path)
    )
    
    row_count = route_df.count()
    logger.info(f"mart_route_performance Gold: wrote {row_count:,} rows")
    return row_count


def main():
    # python silver_to_gold.py <run_date> <silver_bucket> <gold_bucket>
    run_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).strftime("%Y%m%d")
    silver_bucket = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_SILVER_BUCKET
    gold_bucket = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_GOLD_BUCKET

    logger.info(f"Starting Silver → Gold pipeline for run_date={run_date}")
    logger.info(f"Using silver_bucket={silver_bucket}, gold_bucket={gold_bucket}")

    spark = get_spark_session()

    try:
        fact_rows = build_fact_flights(spark, run_date, silver_bucket, gold_bucket)
        mart_rows = build_route_aggregates(spark, silver_bucket, gold_bucket)
        logger.info(
            f"Silver→Gold complete. fact_flights={fact_rows:,} rows, mart_route_performance={mart_rows:,} rows"
        )
    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
