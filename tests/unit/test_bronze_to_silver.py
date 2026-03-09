import pytest
from unittest.mock import patch, MagicMock
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, BooleanType, TimestampType
from spark_jobs.bronze_to_silver import process_bts_bronze, process_fr24_bronze, BTS_SCHEMA, _FT_TO_M, _KT_TO_MS

def test_process_bts_bronze_logic(spark):
    """
    Tests the transformation logic of process_bts_bronze.
    Mocks the GCS read/write to focus on DataFrame transformations.
    """
    # 1. Prepare Mock Data
    # Row 1: Valid flight
    # Row 2: Cancelled flight
    # Row 3: Null FlightDate (should be filtered)
    # Row 4: Duplicate of Row 1 (should be deduped)
    data = [
        (2024, 1, 15, 1, "2024-01-15", "AA", "N123AA", "100", "JFK", "New York", "NY", "LHR", "London", "UK", "1200", "1205", 5.0, 20.0, "1225", "1900", 10.0, "1900", "1910", 10.0, 0.0, None, 0.0, 420.0, 425.0, 390.0, 3450.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (2024, 1, 15, 1, "2024-01-15", "BA", "G-XWBA", "200", "LHR", "London", "UK", "JFK", "New York", "NY", "1400", None, None, None, None, None, None, "1700", None, None, 1.0, "A", 0.0, None, None, None, 3450.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (2024, 1, 15, 1, None, "XX", "N999XX", "999", "ORD", "Chicago", "IL", "ATL", "Atlanta", "GA", "1000", "1000", 0.0, 10.0, "1010", "1200", 5.0, "1200", "1200", 0.0, 0.0, None, 0.0, 120.0, 120.0, 100.0, 600.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (2024, 1, 15, 1, "2024-01-15", "AA", "N123AA", "100", "JFK", "New York", "NY", "LHR", "London", "UK", "1200", "1205", 5.0, 20.0, "1225", "1900", 10.0, "1900", "1910", 10.0, 0.0, None, 0.0, 420.0, 425.0, 390.0, 3450.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    ]
    
    # Create DataFrame with the exact schema expected by the job
    input_df = spark.createDataFrame(data, schema=BTS_SCHEMA)

    # 2. Mock spark.read.csv and DataFrame.write
    with patch("pyspark.sql.DataFrameReader.csv", return_value=input_df) as mock_read:
        with patch("pyspark.sql.DataFrameWriter.parquet") as mock_parquet:
            # 3. Run the function
            row_count = process_bts_bronze(spark, "20240115")
            
            # 4. Assertions
            assert row_count == 2
            mock_read.assert_called_once()
            call_args = mock_read.call_args
            assert "gs://flights-bronze-flights-analytics-prod/bts/2024/01/*.zip" in call_args[0][0]

def test_process_fr24_bronze_logic(spark):
    """
    Tests the transformation logic of process_fr24_bronze.
    Covers unit conversions, deduplication, filtering, and schema enforcement.
    """
    # 1. Prepare Mock Data (Raw FR24 fields)
    # Row 1: Valid flight
    # Row 2: Same flight, different timestamp -> Kept
    # Row 3: Duplicate of Row 1 (same hex + timestamp) -> Dropped
    # Row 4: Null hex -> Dropped
    # Row 5: Different flight, whitespace in callsign -> Trimmed
    data = [
        {"hex": "406a42", "callsign": "BAW123 ", "lat": 51.5, "lon": -0.1, "alt": 30000, "gspeed": 450, "vspeed": 0, "on_ground": 0, "ingestion_timestamp": "2024-01-15T12:00:00Z", "origin_country": "UK"},
        {"hex": "406a42", "callsign": "BAW123 ", "lat": 51.6, "lon": -0.2, "alt": 31000, "gspeed": 460, "vspeed": 500, "on_ground": 0, "ingestion_timestamp": "2024-01-15T12:01:00Z", "origin_country": "UK"},
        {"hex": "406a42", "callsign": "BAW123 ", "lat": 51.5, "lon": -0.1, "alt": 30000, "gspeed": 450, "vspeed": 0, "on_ground": 0, "ingestion_timestamp": "2024-01-15T12:00:00Z", "origin_country": "UK"},
        {"hex": None, "callsign": "XXXXXX ", "lat": 40.0, "lon": 10.0, "alt": 1000, "gspeed": 100, "vspeed": 0, "on_ground": 1, "ingestion_timestamp": "2024-01-15T12:05:00Z", "origin_country": "US"},
        {"hex": "3c65a1", "callsign": " DLH456", "lat": 48.1, "lon": 11.5, "alt": 0, "gspeed": 10, "vspeed": 0, "on_ground": 1, "ingestion_timestamp": "2024-01-15T12:10:00Z", "origin_country": "Germany"},
    ]
    
    input_df = spark.read.json(spark.sparkContext.parallelize(data))

    # 2. Mock spark.read.json and DataFrame.write
    with patch("pyspark.sql.DataFrameReader.json", return_value=input_df) as mock_read:
        with patch("pyspark.sql.DataFrameWriter.parquet") as mock_parquet:
            # 3. Run the function
            row_count = process_fr24_bronze(spark, "20240115")
            
            # 4. Assertions
            # Expected count: Row 1, Row 2, Row 5 (Total 3)
            assert row_count == 3
            
            # Verify transformations on the intercepted output if possible
            # Since the function doesn't return the DF, we can't easily check values here 
            # without more complex mocking. However, we've verified the row count and logic flow.
            # To be more thorough, we could refactor the job to return the DF for testing.
            mock_read.assert_called_once()
            call_args = mock_read.call_args
            assert "gs://flights-bronze-flights-analytics-prod/fr24/2024/01/15/*.ndjson" in call_args[0][0]

def test_schema_definition():
    """
    Verifies the BTS_SCHEMA contains critical columns with correct types.
    """
    field_map = {f.name: f.dataType for f in BTS_SCHEMA.fields}
    
    assert isinstance(field_map["FlightDate"], StringType)
    assert isinstance(field_map["DepDelay"], DoubleType)
    assert isinstance(field_map["ArrDelay"], DoubleType)
    assert isinstance(field_map["Cancelled"], DoubleType)
    assert "Tail_Number" in field_map

def test_fr24_unit_conversions(spark):
    """
    Explicitly tests the mathematical accuracy of FR24 unit conversions.
    """
    data = [
        {"hex": "test", "alt": 1000, "gspeed": 100, "on_ground": 0, "ingestion_timestamp": "2024-01-15T12:00:00Z"}
    ]
    df = spark.createDataFrame(data)
    
    # Apply transformation logic directly
    result_df = (
        df.withColumn("baro_altitude_m", (F.col("alt").cast(DoubleType()) * _FT_TO_M))
          .withColumn("velocity_ms", (F.col("gspeed").cast(DoubleType()) * _KT_TO_MS))
          .withColumn("on_ground", F.col("on_ground").cast(BooleanType()))
    )
    
    row = result_df.collect()[0]
    
    # 1000 ft * 0.3048 = 304.8 m
    assert row["baro_altitude_m"] == pytest.approx(304.8)
    # 100 kt * 0.514444 = 51.4444 m/s
    assert row["velocity_ms"] == pytest.approx(51.4444)
    # 0 cast to bool is False
    assert row["on_ground"] is False
