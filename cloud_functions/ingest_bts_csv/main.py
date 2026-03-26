import functions_framework
import io
import json
import logging
import zipfile
import csv
import requests
from datetime import datetime, timezone
from google.cloud import bigquery
from google.cloud import storage

# --- Project Constants ---
PROJECT_ID = "flights-analytics-prod"
BRONZE_BUCKET = "flights-bronze-flights-analytics-prod"
REGION = "europe-west2"

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- BTS API Constants ---
BTS_URL = (
    "https://transtats.bts.gov/PREZIP/"
    "On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_{year}_{month}.zip"
)
BTS_STAGING_TABLE = "flights-analytics-prod.flights_staging.raw_bts_flights"
BTS_IDEMPOTENCY_VIEW = "flights-analytics-prod.flights_dw.stg_bts_flights"


@functions_framework.http
def ingest_bts_csv(request: requests.Request) -> tuple[dict, int]:
    """
    HTTP-triggered Cloud Function to ingest BTS On-Time Performance CSV data.

    Accepts year and month as query parameters or JSON body fields.
    Performs an idempotency check before downloading: if data for the requested
    year/month already exists in stg_bts_flights, returns early.

    Args:
        request: The Flask request object.

    Returns:
        Tuple of (JSON response dict, HTTP status code).
    """
    # --- Parse year / month from request ---
    params = request.get_json(silent=True) or request.args
    try:
        year = int(params.get("year", datetime.now(timezone.utc).year))
        month = int(params.get("month", datetime.now(timezone.utc).month))
    except (TypeError, ValueError) as e:
        return {"status": "error", "message": f"Invalid year/month: {e}"}, 400

    logger.info(f"Starting BTS ingestion for {year}-{month:02d}.")

    bq_client = bigquery.Client(project=PROJECT_ID)

    # --- Idempotency check ---
    existing_rows = _check_existing_rows(bq_client, year, month)
    if existing_rows > 0:
        logger.info(f"Data for {year}-{month:02d} already loaded ({existing_rows} rows). Skipping.")
        return {"status": "already_loaded", "rows": existing_rows}, 200

    # --- Download BTS zip ---
    url = BTS_URL.format(year=year, month=month)
    logger.info(f"Downloading BTS data from: {url}")
    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error downloading BTS data: {e}")
        return {"status": "error", "message": str(e)}, e.response.status_code if e.response else 500

    # --- Extract CSV from zip ---
    records = _extract_records_from_zip(response.content, year, month)
    logger.info(f"Extracted {len(records)} records from BTS zip.")

    # --- Upload NDJSON to GCS Bronze ---
    now_utc = datetime.now(timezone.utc)
    blob_name = f"bts/{year}/{month:02d}/bts_{now_utc.strftime('%Y%m%d')}.ndjson"
    gcs_path = f"gs://{BRONZE_BUCKET}/{blob_name}"
    ndjson_content = "\n".join(json.dumps(r) for r in records)

    gcs_client = storage.Client(project=PROJECT_ID)
    bucket = gcs_client.bucket(BRONZE_BUCKET)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(ndjson_content, content_type="application/x-ndjson")
    logger.info(f"Uploaded {len(records)} rows to {gcs_path}")

    # --- Load to BigQuery ---
    rows_loaded = _load_to_bigquery(bq_client, records)
    logger.info(f"Loaded {rows_loaded} rows into {BTS_STAGING_TABLE}.")

    return {
        "status": "success",
        "year": year,
        "month": month,
        "gcs_path": gcs_path,
        "rows_written": len(records),
        "rows_loaded_to_bq": rows_loaded,
    }, 200


def _check_existing_rows(client: bigquery.Client, year: int, month: int) -> int:
    """
    Query stg_bts_flights to check if data for the given year/month already exists.

    Returns the row count (0 if not yet loaded).
    """
    query = """
    SELECT COUNT(*) AS row_count
    FROM `{view}`
    WHERE EXTRACT(YEAR FROM flight_date) = @year
      AND EXTRACT(MONTH FROM flight_date) = @month
    """.format(view=BTS_IDEMPOTENCY_VIEW)

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("year", "INT64", year),
            bigquery.ScalarQueryParameter("month", "INT64", month),
        ]
    )
    result = client.query(query, job_config=job_config).result()
    return next(result)["row_count"]


def _extract_records_from_zip(zip_bytes: bytes, year: int, month: int) -> list[dict]:
    """
    Extract flight records from a BTS zip file and return as a list of dicts.

    Injects ingestion_timestamp into each record.
    """
    ingestion_ts = datetime.now(timezone.utc).isoformat()
    records: list[dict] = []

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        csv_names = [name for name in zf.namelist() if name.endswith(".csv")]
        if not csv_names:
            raise ValueError("No CSV file found in BTS zip archive.")

        with zf.open(csv_names[0]) as csv_file:
            reader = csv.DictReader(io.TextIOWrapper(csv_file, encoding="utf-8-sig"))
            for row in reader:
                row["ingestion_timestamp"] = ingestion_ts
                records.append(dict(row))

    return records


def _load_to_bigquery(client: bigquery.Client, records: list[dict]) -> int:
    """
    Load records into flights_staging.raw_bts_flights using load_table_from_json().

    Returns the number of rows successfully loaded.
    """
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        autodetect=True,
    )
    job = client.load_table_from_json(records, BTS_STAGING_TABLE, job_config=job_config)
    job.result()
    return job.output_rows
