# Cloud Functions Gen2 — Project Context
# flights-analytics-prod | europe-west2 | Python 3.12

## PROJECT CONSTANTS
Always hardcode these — never use environment variables for project config:

```python
PROJECT_ID    = "flights-analytics-prod"
BRONZE_BUCKET = "flights-bronze-flights-analytics-prod"
REGION        = "europe-west2"
```

## FUNCTION CONFIGURATIONS

```
fn-ingest-bts-csv:
  entry_point: ingest_bts_csv
  timeout:     540s
  memory:      512Mi
  trigger:     HTTP (no-allow-unauthenticated)
  runtime:     python312

fn-ingest-fr24:
  entry_point: ingest_fr24
  timeout:     120s
  memory:      256Mi
  trigger:     HTTP (no-allow-unauthenticated)
  runtime:     python312
```

## REQUIRED IMPORTS (both functions)

```python
import functions_framework
import logging
from datetime import datetime, timezone
from google.cloud import storage
```

## LOGGING CONVENTION

Always at module level, before any function definitions:

```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

## HTTP ENTRY POINT PATTERN

Always use @functions_framework.http decorator.
Always parse request JSON safely with silent=True.
Always return a dict + HTTP status code tuple:

```python
@functions_framework.http
def function_name(request):
    request_json = request.get_json(silent=True) or {}
    try:
        # logic here
        return {"status": "success", "key": value}, 200
    except SpecificException as e:
        logger.error(f"Specific error: {e}")
        return {"status": "error", "message": str(e)}, 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}, 500
```

## GCS CLIENT PATTERN

Always initialise inside the function, not at module level:

```python
gcs_client = storage.Client(project=PROJECT_ID)
bucket = gcs_client.bucket(BUCKET_NAME)
blob = bucket.blob(blob_name)
```

## GCS WRITE PATTERNS

Use upload_from_file for binary/streaming content (ZIP files):

```python
with io.BytesIO(response.content) as buffer:
    blob.upload_from_file(buffer, content_type="application/zip")
```

Use upload_from_string for text content (NDJSON):

```python
blob.upload_from_string(content, content_type="application/x-ndjson")
```

## GCS PATH CONVENTIONS

Bronze paths must always follow this pattern:

```
bts/{year}/{month:02d}/raw_{YYYYMMDD}.zip
fr24/{year}/{month:02d}/{day:02d}/positions_{YYYYMMDD_HHMMSS}.ndjson
```

Always derive dates from datetime.now(timezone.utc) — never system local time.

## ERROR HANDLING RULES

- Always catch specific exceptions before generic Exception
- Always log with logger.error() not print()
- Always include exc_info=True on unexpected exceptions
- Never let a function return 200 on a failed operation
- HTTP errors from external APIs: catch requests.HTTPError separately

## RESPONSE SHAPE CONVENTION

Success response must always include:

```python
# BTS function
{
    "status":        "success",
    "gcs_path":      "gs://bucket/path/to/file",
    "bytes_written": int,
    "year":          int,
    "month":         int
}

# FR24 function
{
    "status":           "success",
    "gcs_path":         "gs://bucket/path/to/file",
    "rows_written":     int,
    "fetch_timestamp":  str   # ISO format UTC
}
```

Error response must always include:

```python
{
    "status":  "error",
    "message": str(e)
}
```

## REQUIREMENTS.TXT CONVENTION

Always pin exact versions compatible with Python 3.12 and CF Gen2:

```
functions-framework==3.8.1
google-cloud-storage==2.18.2
requests==2.32.3
```

## EXTERNAL API PATTERNS

### BTS Download

- Always use requests.get() with timeout=300 and stream=True
- Call response.raise_for_status() immediately after get()
- URL pattern:

```
https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip
```

### FR24 API

- Always use requests.get() with timeout=60
- Bounding box covers UK + NW Europe:

```
61.5,49.0,-8.5,10.5
```

- Full URL:

```
https://fr24api.flightradar24.com/api/live/flight-positions/full
```

- Response `data` array contains raw flight position objects.
- Always handle empty data array gracefully — return 200 with rows_written=0

## WHAT NOT TO DO

- Never use os.environ for PROJECT_ID or bucket names
- Never initialise GCS client at module level
- Never return plain strings — always return dict + status code tuple
- Never use print() — always use logger
- Never hardcode credentials of any kind
- Never set --allow-unauthenticated on deployment
