import functions_framework
import logging
import json
from typing import Any
from datetime import datetime, timezone
from google.cloud import bigquery
from google.api_core import exceptions as google_exceptions
from google import genai

# --- Project Constants ---
PROJECT_ID = "flights-analytics-prod"
GEMINI_MODEL = "gemini-2.5-pro"

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# BigQuery query to check last 24h pipeline health
_HEALTH_QUERY = """
SELECT
    'raw_fr24_positions' AS table_name,
    COUNT(*) AS row_count,
    MAX(ingestion_timestamp) AS last_ingestion_timestamp
FROM `flights-analytics-prod.flights_staging.raw_fr24_positions`
WHERE ingestion_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
UNION ALL
SELECT
    'raw_bts_flights' AS table_name,
    COUNT(*) AS row_count,
    MAX(ingestion_timestamp) AS last_ingestion_timestamp
FROM `flights-analytics-prod.flights_staging.raw_bts_flights`
WHERE ingestion_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
"""


def _query_pipeline_health(bq_client: bigquery.Client) -> list[dict[str, Any]]:
    """Queries BigQuery for a last-24h pipeline health summary."""
    query_job = bq_client.query(_HEALTH_QUERY)
    rows = query_job.result()
    results = []
    for row in rows:
        results.append({
            "table_name": row.table_name,
            "row_count": row.row_count,
            "last_ingestion_timestamp": (
                row.last_ingestion_timestamp.isoformat()
                if row.last_ingestion_timestamp is not None
                else None
            ),
            "zero_rows": row.row_count == 0,
        })
    return results


def _build_prompt(summary: list[dict[str, Any]]) -> str:
    """Builds the Gemini prompt from the pipeline health summary."""
    summary_str = json.dumps(summary, indent=2)
    return (
        "You are a data pipeline monitor. "
        f"Here is the last 24h pipeline summary: {summary_str}. "
        "Are there any anomalies? "
        'Reply with JSON: {"status": "ok"|"anomaly", "findings": [list of findings]}'
    )


@functions_framework.http
def gemini_monitor(request: Any) -> tuple[dict[str, Any], int]:
    """
    HTTP-triggered Cloud Function that queries BigQuery for pipeline health
    metrics and passes them to Gemini 2.5 Pro for anomaly analysis.

    Args:
        request: The Flask request object. The request body is not used.

    Returns:
        A tuple containing a JSON response dictionary and an HTTP status code.
    """
    logger.info("Starting Gemini pipeline monitor.")

    try:
        # 1. Query BigQuery for last-24h health summary
        bq_client = bigquery.Client(project=PROJECT_ID)
        health_summary = _query_pipeline_health(bq_client)
        logger.info(f"Pipeline health summary retrieved: {health_summary}")

        # 2. Flag any zero-row tables before calling Gemini
        zero_row_tables = [r["table_name"] for r in health_summary if r["zero_rows"]]
        if zero_row_tables:
            logger.warning(f"Zero rows detected in tables: {zero_row_tables}")

        # 3. Build prompt and call Gemini 2.5 Pro via google-genai SDK
        prompt = _build_prompt(health_summary)
        genai_client = genai.Client()
        gemini_response = genai_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        raw_text = gemini_response.text.strip()
        logger.info(f"Gemini raw response: {raw_text}")

        # 4. Parse Gemini's JSON response
        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        gemini_result = json.loads(raw_text)
        status = gemini_result.get("status", "ok")
        findings = gemini_result.get("findings", [])

        # 5. Log anomalies at WARNING level
        if status == "anomaly":
            logger.warning(f"Anomaly detected by Gemini. Findings: {findings}")
        else:
            logger.info("Gemini reports pipeline status: ok")

        return {
            "status": status,
            "summary": f"Pipeline health check completed at {datetime.now(timezone.utc).isoformat()}",
            "details": {
                "bq_summary": health_summary,
                "gemini_findings": findings,
            },
        }, 200

    except google_exceptions.GoogleAPIError as e:
        logger.error(f"Google API error in gemini_monitor: {e}")
        return {"status": "error", "message": str(e)}, 500
    except Exception as e:
        logger.error(f"Unexpected error in gemini_monitor: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}, 500
