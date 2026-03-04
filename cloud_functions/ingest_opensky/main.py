import functions_framework
import logging
import json
import requests
from datetime import datetime, timezone
from google.cloud import storage
from typing import Tuple, Dict, Any

# --- Project Constants ---
# Per GEMINI.md and cloud_functions/GEMINI.md, these are hardcoded.
PROJECT_ID = "flights-analytics-prod"
BRONZE_BUCKET = "flights-bronze-flights-analytics-prod"
REGION = "europe-west2"

# --- Logging Configuration ---
# Per cloud_functions/GEMINI.md, configured at module level.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- OpenSky API Constants ---
# Per cloud_functions/GEMINI.md
OPENSKY_URL = "https://opensky-network.org/api/states/all?lamin=49.0&lomin=-8.5&lamax=61.5&lomax=10.5"
OPENSKY_COLUMNS = [
    "icao24", "callsign", "origin_country", "time_position",
    "last_contact", "longitude", "latitude", "baro_altitude",
    "on_ground", "velocity", "true_track", "vertical_rate",
    "sensors", "geo_altitude", "squawk", "spi",
    "position_source", "category"
]


@functions_framework.http
def ingest_opensky(request: functions_framework.Request) -> Tuple[Dict[str, Any], int]:
    """
    HTTP-triggered Cloud Function to ingest live flight data from OpenSky Network.

    This function fetches current flight state vectors, converts them to NDJSON,
    and uploads the result to the GCS Bronze bucket.

    Args:
        request: The Flask request object. The request body is not used.

    Returns:
        A tuple containing a JSON response dictionary and an HTTP status code.
    """
    logger.info("Received request for OpenSky data ingestion.")

    try:
        # 1. Get current timestamp for paths and records
        now_utc = datetime.now(timezone.utc)
        fetch_timestamp_iso = now_utc.isoformat()

        # 2. Fetch data from OpenSky Network API
        logger.info(f"Fetching data from OpenSky Network API: {OPENSKY_URL}")
        with requests.get(OPENSKY_URL, timeout=60) as response:
            response.raise_for_status()
            api_response = response.json()

        # 3. Process the state vectors into NDJSON
        states = api_response.get("states")
        rows_written = 0
        gcs_path = None

        if states:
            # Convert list of lists to list of dicts
            records = [dict(zip(OPENSKY_COLUMNS, state)) for state in states]
            ndjson_content = "\n".join(json.dumps(record) for record in records)
            rows_written = len(records)

            # 4. Construct GCS destination path
            blob_name = (
                f"opensky/{now_utc.year}/{now_utc.month:02d}/{now_utc.day:02d}/"
                f"states_{now_utc.strftime('%Y%m%d_%H%M%S')}.ndjson"
            )
            gcs_path = f"gs://{BRONZE_BUCKET}/{blob_name}"

            # 5. Upload to GCS
            logger.info(f"Uploading {rows_written} rows to {gcs_path}")
            gcs_client = storage.Client(project=PROJECT_ID)
            bucket = gcs_client.bucket(BRONZE_BUCKET)
            blob = bucket.blob(blob_name)
            blob.upload_from_string(ndjson_content, content_type="application/x-ndjson")
        else:
            logger.info("OpenSky API returned no state vectors. Nothing to write.")

        # 6. Return success response
        success_payload = {
            "status": "success",
            "gcs_path": gcs_path,
            "rows_written": rows_written,
            "fetch_timestamp": fetch_timestamp_iso,
        }
        return success_payload, 200

    except requests.exceptions.HTTPError as e:
        error_message = f"HTTP Error fetching data from OpenSky API: {e}"
        logger.error(error_message)
        return {"status": "error", "message": str(e)}, e.response.status_code if e.response else 500
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}, 500

