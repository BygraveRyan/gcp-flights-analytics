import json
import os
import uuid
from datetime import datetime

from flask import Request
from google import genai
from google.cloud import bigquery


def run_gemini_monitor(request: Request) -> tuple[str, int]:
    """
    HTTP-triggered Cloud Function to generate AI-powered pipeline monitoring summaries.

    Queries BigQuery for today's pipeline statistics, calls Gemini 2.5 Pro for
    a 3-sentence natural-language summary, and inserts the result into pipeline_run_log.

    Args:
        request: Flask request object (unused, but required by Cloud Functions framework).

    Returns:
        Tuple of (JSON response, HTTP status code).
    """
    project_id = os.environ.get("GCP_PROJECT")
    if not project_id:
        return json.dumps({"error": "GCP_PROJECT environment variable not set"}), 400

    # Initialize BigQuery client
    bq_client = bigquery.Client(project=project_id)

    # Query BigQuery for today's pipeline stats
    stats = _fetch_pipeline_stats(bq_client, project_id)

    # Call Gemini for summary
    gemini_summary = _generate_gemini_summary(stats, project_id)

    # Insert result into pipeline_run_log
    run_id = str(uuid.uuid4())
    run_timestamp = datetime.utcnow()

    _insert_pipeline_log(
        bq_client,
        project_id,
        run_id=run_id,
        run_date=run_timestamp.date(),
        run_timestamp=run_timestamp,
        total_rows_loaded=stats["total_flights_loaded"],
        gemini_summary=gemini_summary,
    )

    return json.dumps({
        "status": "success",
        "run_id": run_id,
        "summary": gemini_summary,
        "stats": stats,
    }), 200


def _fetch_pipeline_stats(client: bigquery.Client, project_id: str) -> dict[str, int | float | list[tuple[str, int]]]:
    """
    Fetch today's pipeline statistics from BigQuery.

    Returns a dict with:
      - total_flights_loaded: count of rows in fact_flights for today
      - pipeline_run_log_rows: count of rows in pipeline_run_log for today
      - avg_arr_delay: average arr_delay_minutes
      - severe_delay_count: count of rows where delay_category = 'Severe'
      - cancellation_count: count of cancelled flights
      - top_3_carriers: list of (carrier_code, flight_count) tuples
    """
    query = """
    WITH today_flights AS (
      SELECT
        COUNT(*) AS total_flights,
        ROUND(AVG(arr_delay_minutes), 2) AS avg_arr_delay,
        COUNTIF(delay_category = 'Severe') AS severe_delay_count,
        COUNTIF(is_cancelled = TRUE) AS cancellation_count
      FROM
        `{project_id}.flights_dw.fact_flights`
      WHERE
        flight_date = CURRENT_DATE()
    ),
    carrier_volumes AS (
      SELECT
        carrier_code,
        COUNT(*) AS flight_count
      FROM
        `{project_id}.flights_dw.fact_flights`
      WHERE
        flight_date = CURRENT_DATE()
      GROUP BY
        carrier_code
      ORDER BY
        flight_count DESC
      LIMIT 3
    ),
    run_log_count AS (
      SELECT
        COUNT(*) AS log_rows
      FROM
        `{project_id}.flights_dw.pipeline_run_log`
      WHERE
        run_date = CURRENT_DATE()
    )
    SELECT
      today_flights.total_flights,
      today_flights.avg_arr_delay,
      today_flights.severe_delay_count,
      today_flights.cancellation_count,
      run_log_count.log_rows AS pipeline_run_log_rows,
      ARRAY_AGG(STRUCT(carrier_volumes.carrier_code, carrier_volumes.flight_count)) AS top_3_carriers
    FROM
      today_flights, run_log_count, carrier_volumes
    GROUP BY
      today_flights.total_flights,
      today_flights.avg_arr_delay,
      today_flights.severe_delay_count,
      today_flights.cancellation_count,
      run_log_count.log_rows
    """.format(project_id=project_id)

    result = client.query(query).result()
    row = next(result)

    top_3_carriers_list: list[tuple[str, int]] = [
        (item["carrier_code"], item["flight_count"]) for item in row["top_3_carriers"]
    ]

    return {
        "total_flights_loaded": row["total_flights"] or 0,
        "pipeline_run_log_rows": row["pipeline_run_log_rows"] or 0,
        "avg_arr_delay": row["avg_arr_delay"] or 0.0,
        "severe_delay_count": row["severe_delay_count"] or 0,
        "cancellation_count": row["cancellation_count"] or 0,
        "top_3_carriers": top_3_carriers_list,
    }


def _generate_gemini_summary(stats: dict[str, int | float | list[tuple[str, int]]], project_id: str) -> str:
    """
    Call Gemini 2.5 Pro to generate a 3-sentence pipeline summary.

    Returns the generated summary text.
    """
    client = genai.Client(vertexai=True, project=project_id, location="europe-west2")

    top_carriers_str = ", ".join([f"{code} ({count})" for code, count in stats["top_3_carriers"]])

    prompt = f"""
Summarize the following flight pipeline statistics in exactly 3 sentences:

- Total flights loaded today: {stats['total_flights_loaded']}
- Average arrival delay: {stats['avg_arr_delay']} minutes
- Severe delays (>120 min): {stats['severe_delay_count']}
- Cancelled flights: {stats['cancellation_count']}
- Pipeline runs logged today: {stats['pipeline_run_log_rows']}
- Top 3 carriers by volume: {top_carriers_str}

Sentence 1: Provide an operational overview with key numbers.
Sentence 2: Highlight delay and cancellation patterns.
Sentence 3: Provide one actionable insight for operations.

Keep it concise and professional.
""".strip()

    response = client.models.generate_content(model="gemini-2.5-pro", contents=prompt)
    return response.text


def _insert_pipeline_log(
    client: bigquery.Client,
    project_id: str,
    run_id: str,
    run_date: object,  # datetime.date
    run_timestamp: object,  # datetime
    total_rows_loaded: int,
    gemini_summary: str,
) -> None:
    """
    Insert a row into pipeline_run_log with the monitoring results.
    """
    query = """
    INSERT INTO `{project_id}.flights_dw.pipeline_run_log`
    (run_id, run_date, run_timestamp, source, total_rows_loaded, gemini_summary, pipeline_status, created_at)
    VALUES (@run_id, @run_date, @run_timestamp, @source, @total_rows_loaded, @gemini_summary, @pipeline_status, @created_at)
    """.format(project_id=project_id)

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("run_id", "STRING", run_id),
            bigquery.ScalarQueryParameter("run_date", "DATE", run_date),
            bigquery.ScalarQueryParameter("run_timestamp", "TIMESTAMP", run_timestamp),
            bigquery.ScalarQueryParameter("source", "STRING", "gemini_monitor"),
            bigquery.ScalarQueryParameter("total_rows_loaded", "INT64", total_rows_loaded),
            bigquery.ScalarQueryParameter("gemini_summary", "STRING", gemini_summary),
            bigquery.ScalarQueryParameter("pipeline_status", "STRING", "SUCCESS"),
            bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", run_timestamp),
        ]
    )

    client.query(query, job_config=job_config).result()
