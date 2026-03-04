# PySpark Optimization Standards

Follow these for all scripts in `spark_jobs/`:

## Session Creation
- Use `get_spark_session()` with standard GCS configuration.
- Enable `spark.sql.adaptive.enabled`.

## Partitioning
- **Repartitioning**: Repartition data before writing to GCS (`.repartition("partition_key")`) to control output file sizes.
- **Partition Discovery**: Use appropriate base paths for reading from Bronze/Silver/Gold.

## Data Lake Zones
- **Bronze (Raw)**: Parquet/JSON/CSV (30 days TTL).
- **Silver (Validated)**: Schema enforced, deduplicated Parquet (90 days TTL).
- **Gold (Business)**: Aggregate/Rich features Parquet (Indefinite).

## Immutability
- Treat DataFrames as immutable. Create new DataFrames for each transformation step.
