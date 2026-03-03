import pytest
from unittest.mock import patch, MagicMock
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
from spark_jobs.bronze_to_silver import process_bts_bronze, BTS_SCHEMA

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
        # Mock the write operation to avoid GCS interaction
        # We need to mock the chain: write -> mode -> partitionBy -> parquet
        mock_write = MagicMock()
        mock_mode = MagicMock(return_value=mock_write)
        mock_partition = MagicMock(return_value=mock_write)
        
        # Patching the write property on the DataFrame returned by transformations is tricky
        # because transformations create new DataFrames.
        # Instead, we will verify the output by inspecting the logic, 
        # or we can refactor the job to return the DF. 
        # Since we can't refactor without modifying the original file, 
        # we will rely on the fact that process_bts_bronze returns row_count.
        
        # However, to inspect the actual data, we can intercept the write in the mock.
        # But for this unit test, we'll trust the return count and the fact it runs without error.
        
        # We need to patch the write attribute of the DataFrame class itself or the instance.
        # A simpler approach for this specific test is to mock the `parquet` method.
        
        with patch("pyspark.sql.DataFrameWriter.parquet") as mock_parquet:
            
            # 3. Run the function
            row_count = process_bts_bronze(spark, "20240115")
            
            # 4. Assertions
            
            # Expected count: 
            # - Row 1: Valid -> Kept
            # - Row 2: Cancelled -> Kept
            # - Row 3: Null FlightDate -> Dropped
            # - Row 4: Duplicate of Row 1 -> Dropped
            # Total expected: 2
            assert row_count == 2
            
            # Verify read was called with correct path pattern
            mock_read.assert_called_once()
            call_args = mock_read.call_args
            assert "gs://flights-bronze-flights-analytics-prod/bts/2024/01/*.zip" in call_args[0][0]

def test_schema_definition():
    """
    Verifies the BTS_SCHEMA contains critical columns with correct types.
    """
    field_map = {f.name: f.dataType for f in BTS_SCHEMA.fields}
    
    assert isinstance(field_map["FlightDate"], StringType)
    assert isinstance(field_map["DepDelay"], DoubleType)
    assert isinstance(field_map["ArrDelay"], DoubleType)
    assert isinstance(field_map["Cancelled"], DoubleType) # Source CSV often has doubles for flags
    assert "Tail_Number" in field_map
```

<!--
[PROMPT_SUGGESTION]Generate the SQL for `bigquery/ddl/create_views.sql` to support the Looker Studio dashboard as described in Phase 11.[/PROMPT_SUGGESTION]
[PROMPT_SUGGESTION]Refactor `spark_jobs/bronze_to_silver.py` to accept input/output paths as arguments to make it more testable and reusable.[/PROMPT_SUGGESTION]
-->