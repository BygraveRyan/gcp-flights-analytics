import functions_framework
import logging
import json
import requests
from datetime import datetime, timezone
from flask import Request
from google.cloud import bigquery
from google.cloud import storage
from google.cloud import secretmanager

# --- Project Constants ---
PROJECT_ID = "flights-analytics-prod"
BRONZE_BUCKET = "flights-bronze-flights-analytics-prod"
REGION = "europe-west2"

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FlightRadar24 API Constants ---
# API v1 Endpoint: https://fr24api.flightradar24.com/api/live/flight-positions/full
# Bounds format: north, south, west, east
# Original OpenSky Bounding box: lamin=49.0, lomin=-8.5, lamax=61.5, lomax=10.5
FR24_URL = "https://fr24api.flightradar24.com/api/live/flight-positions/full"
FR24_BOUNDS = "61.5,49.0,-8.5,10.5"
FR24_SECRET_ID = "fr24-api-key"

def _get_secret(project_id: str, secret_id: str, version_id: str = "latest") -> str:
    """Retrieves a secret from Google Cloud Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

@functions_framework.http
def ingest_fr24(request: Request) -> tuple[dict, int]:
    """
    HTTP-triggered Cloud Function to ingest live flight data from FlightRadar24.
    Fetches raw flight positions, converts to NDJSON, and uploads to GCS Bronze.

    Args:
        request: The Flask request object. The request body is not used.

    Returns:
        A tuple containing a JSON response dictionary and an HTTP status code.
    """
    logger.info("Starting FlightRadar24 data ingestion.")

    try:
        # 1. Get current timestamp for paths and records
        now_utc = datetime.now(timezone.utc)
        fetch_timestamp_iso = now_utc.isoformat()

        # 2. Retrieve FR24 API Key
        api_key = _get_secret(PROJECT_ID, FR24_SECRET_ID)

        # 3. Fetch data from FlightRadar24 API v1
        headers = {
            "Accept-Version": "v1",
            "Authorization": f"Bearer {api_key}"
        }
        params = {
            "bounds": FR24_BOUNDS
        }

        logger.info(f"Requesting FR24 positions for bounds: {FR24_BOUNDS}")
        with requests.get(FR24_URL, headers=headers, params=params, timeout=60) as response:
            response.raise_for_status()
            api_response = response.json()

        # 4. Process the data into NDJSON (Complete Raw Response)
        # FR24 response format is {"data": [...], "meta": {...}}
        flights = api_response.get("data", [])
        rows_written = 0
        gcs_path = None

        if flights:
            ndjson_lines = []
            for flight in flights:
                # Inject ingestion metadata into each record
                record = flight.copy()
                record["ingestion_timestamp"] = fetch_timestamp_iso
                ndjson_lines.append(json.dumps(record))

            ndjson_content = "\n".join(ndjson_lines)
            rows_written = len(flights)

            # 5. Construct GCS destination path
            # fr24/{year}/{month:02d}/{day:02d}/positions_{YYYYMMDD_HHMMSS}.ndjson
            blob_name = (
                f"fr24/{now_utc.year}/{now_utc.month:02d}/{now_utc.day:02d}/"
                f"positions_{now_utc.strftime('%Y%m%d_%H%M%S')}.ndjson"
            )
            gcs_path = f"gs://{BRONZE_BUCKET}/{blob_name}"

            # 6. Upload to GCS Bronze
            logger.info(f"Uploading {rows_written} raw records to {gcs_path}")
            gcs_client = storage.Client(project=PROJECT_ID)
            bucket = gcs_client.bucket(BRONZE_BUCKET)
            blob = bucket.blob(blob_name)
            blob.upload_from_string(ndjson_content, content_type="application/x-ndjson")

            # 7. Load records to BigQuery staging
            bq_table = f"{PROJECT_ID}.flights_staging.raw_fr24_positions"
            records_for_bq = [flight | {"ingestion_timestamp": fetch_timestamp_iso} for flight in flights]
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                autodetect=True,
            )
            bq_client = bigquery.Client(project=PROJECT_ID)
            job = bq_client.load_table_from_json(records_for_bq, bq_table, job_config=job_config)
            job.result()
            rows_loaded_to_bq = job.output_rows
            logger.info(f"Loaded {rows_loaded_to_bq} rows into {bq_table}.")
        else:
            logger.info("FR24 API returned no flights for these bounds. Nothing to write.")
            rows_loaded_to_bq = 0

        # 8. Return success response
        return {
            "status": "success",
            "gcs_path": gcs_path,
            "rows_written": rows_written,
            "rows_loaded_to_bq": rows_loaded_to_bq,
            "fetch_timestamp": fetch_timestamp_iso,
        }, 200

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error from FR24 API: {e}")
        return {"status": "error", "message": str(e)}, e.response.status_code if e.response else 500
    except Exception as e:
        logger.error(f"Unexpected error in ingest_fr24: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}, 500
