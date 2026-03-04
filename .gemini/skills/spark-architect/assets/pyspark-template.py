import logging
from pyspark.sql import SparkSession, DataFrame

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_spark_session(app_name: str = "FlightsPipeline") -> SparkSession:
    """Creates a Spark Session with standard GCP configuration."""
    return SparkSession.builder 
        .appName(app_name) 
        .config("spark.sql.adaptive.enabled", "true") 
        .getOrCreate()

def run_job(spark: SparkSession) -> None:
    """Main job logic."""
    try:
        logger.info("Reading source data...")
        df = spark.read.parquet("gs://flights-bronze-flights-analytics-prod/...")
        
        logger.info("Enforcing schema and transformations...")
        # ... Transformations ...
        
        logger.info("Writing results to Silver/Gold...")
        df.repartition("partition_key") 
          .write.mode("overwrite") 
          .parquet("gs://flights-silver-flights-analytics-prod/...")
          
    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    spark = get_spark_session()
    run_job(spark)
    spark.stop()
