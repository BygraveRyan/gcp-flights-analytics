"""
Unit tests for the ingest_bts_csv Cloud Function.

Mocks all external I/O (requests, GCS, BigQuery) so tests run without
any real GCP credentials or network access.
"""
import csv
import io
import json
import sys
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Make the Cloud Function importable without a package __init__.py
# ---------------------------------------------------------------------------
_CF_DIR = Path(__file__).parents[2] / "cloud_functions" / "ingest_bts_csv"
if str(_CF_DIR) not in sys.path:
    sys.path.insert(0, str(_CF_DIR))

import main  # noqa: E402  (must come after sys.path manipulation)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bts_zip(rows: list[dict]) -> bytes:
    """Build an in-memory BTS-style zip containing one CSV file."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        csv_buf = io.StringIO()
        if rows:
            writer = csv.DictWriter(csv_buf, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        else:
            # Empty CSV — just a header row
            csv_buf.write("FlightDate,Carrier,FlightNum\n")
        zf.writestr("bts_data.csv", csv_buf.getvalue())
    buf.seek(0)
    return buf.read()


def _make_mock_request(body: dict | None = None) -> MagicMock:
    """Return a minimal Flask-style request mock."""
    mock_req = MagicMock()
    mock_req.get_json.return_value = body or {"year": 2024, "month": 1}
    mock_req.args = {}
    return mock_req


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

class TestIngestBtsCsv:
    """Tests for the ingest_bts_csv HTTP Cloud Function."""

    # ------------------------------------------------------------------
    # Test 1 — Happy path: successful download + GCS upload
    # ------------------------------------------------------------------
    @patch("main.storage")
    @patch("main.bigquery")
    @patch("main.requests")
    def test_happy_path_returns_success_with_row_count(
        self, mock_requests, mock_bigquery, mock_storage
    ):
        """
        Given a valid year/month, a successful BTS download, and no existing data,
        the function should upload NDJSON to GCS and return 200 with rows_written > 0.
        """
        # --- Arrange ---
        sample_rows = [
            {"FlightDate": "2024-01-15", "Carrier": "AA", "FlightNum": "100"},
            {"FlightDate": "2024-01-15", "Carrier": "BA", "FlightNum": "200"},
        ]
        zip_bytes = _make_bts_zip(sample_rows)

        # Idempotency check returns 0 (no existing rows)
        mock_bq_client = MagicMock()
        mock_bigquery.Client.return_value = mock_bq_client
        mock_query_result = MagicMock()
        mock_query_result.__iter__ = MagicMock(
            return_value=iter([{"row_count": 0}])
        )
        mock_bq_client.query.return_value.result.return_value = mock_query_result

        # BigQuery load job
        mock_load_job = MagicMock()
        mock_load_job.output_rows = len(sample_rows)
        mock_bq_client.load_table_from_json.return_value = mock_load_job

        # HTTP download returns zip bytes
        mock_http_response = MagicMock()
        mock_http_response.content = zip_bytes
        mock_http_response.raise_for_status.return_value = None
        mock_requests.get.return_value = mock_http_response
        mock_requests.exceptions.HTTPError = __import__(
            "requests"
        ).exceptions.HTTPError

        # GCS mocks
        mock_gcs_client = MagicMock()
        mock_storage.Client.return_value = mock_gcs_client
        mock_blob = MagicMock()
        mock_gcs_client.bucket.return_value.blob.return_value = mock_blob

        request = _make_mock_request({"year": 2024, "month": 1})

        # --- Act ---
        response_body, status_code = main.ingest_bts_csv(request)

        # --- Assert ---
        assert status_code == 200
        assert response_body["status"] == "success"
        assert response_body["rows_written"] == len(sample_rows)
        assert response_body["gcs_path"].startswith("gs://flights-bronze-flights-analytics-prod/bts/")
        mock_blob.upload_from_string.assert_called_once()

    # ------------------------------------------------------------------
    # Test 2 — Empty/zero-row CSV: returns 200 with 0 rows, no GCS upload
    # ------------------------------------------------------------------
    @patch("main.storage")
    @patch("main.bigquery")
    @patch("main.requests")
    def test_empty_csv_returns_200_zero_rows_no_gcs_upload(
        self, mock_requests, mock_bigquery, mock_storage
    ):
        """
        When the downloaded zip contains no data rows, the function should
        return 200 with rows_written == 0 and skip the GCS upload.
        """
        # --- Arrange ---
        zip_bytes = _make_bts_zip([])  # empty CSV — header only

        mock_bq_client = MagicMock()
        mock_bigquery.Client.return_value = mock_bq_client
        mock_query_result = MagicMock()
        mock_query_result.__iter__ = MagicMock(
            return_value=iter([{"row_count": 0}])
        )
        mock_bq_client.query.return_value.result.return_value = mock_query_result

        mock_load_job = MagicMock()
        mock_load_job.output_rows = 0
        mock_bq_client.load_table_from_json.return_value = mock_load_job

        mock_http_response = MagicMock()
        mock_http_response.content = zip_bytes
        mock_http_response.raise_for_status.return_value = None
        mock_requests.get.return_value = mock_http_response
        mock_requests.exceptions.HTTPError = __import__(
            "requests"
        ).exceptions.HTTPError

        mock_gcs_client = MagicMock()
        mock_storage.Client.return_value = mock_gcs_client

        request = _make_mock_request({"year": 2024, "month": 1})

        # --- Act ---
        response_body, status_code = main.ingest_bts_csv(request)

        # --- Assert ---
        assert status_code == 200
        assert response_body["rows_written"] == 0
        # GCS client should not have been used for upload (no rows → no blob)
        mock_gcs_client.bucket.assert_not_called()

    # ------------------------------------------------------------------
    # Test 3 — HTTP error from source: returns appropriate error status code
    # ------------------------------------------------------------------
    @patch("main.storage")
    @patch("main.bigquery")
    @patch("main.requests")
    def test_http_error_from_source_returns_upstream_status(
        self, mock_requests, mock_bigquery, mock_storage
    ):
        """
        When the BTS download returns a 404, the function should propagate
        that status code in an error response (not 500).
        """
        import requests as real_requests

        # --- Arrange ---
        mock_bq_client = MagicMock()
        mock_bigquery.Client.return_value = mock_bq_client
        mock_query_result = MagicMock()
        mock_query_result.__iter__ = MagicMock(
            return_value=iter([{"row_count": 0}])
        )
        mock_bq_client.query.return_value.result.return_value = mock_query_result

        # Build a real HTTPError with a fake response attached
        fake_response = MagicMock()
        fake_response.status_code = 404
        http_err = real_requests.exceptions.HTTPError(
            "404 Not Found", response=fake_response
        )
        mock_requests.get.return_value.raise_for_status.side_effect = http_err
        mock_requests.exceptions.HTTPError = real_requests.exceptions.HTTPError

        request = _make_mock_request({"year": 2024, "month": 1})

        # --- Act ---
        response_body, status_code = main.ingest_bts_csv(request)

        # --- Assert ---
        assert status_code == 404
        assert response_body["status"] == "error"
        assert "message" in response_body

    # ------------------------------------------------------------------
    # Test 4 — Unexpected exception: returns 500
    # ------------------------------------------------------------------
    @patch("main.storage")
    @patch("main.bigquery")
    @patch("main.requests")
    def test_unexpected_exception_returns_500(
        self, mock_requests, mock_bigquery, mock_storage
    ):
        """
        When an unexpected exception is raised (e.g., corrupted zip),
        the function should catch it and return a 500 error response.
        """
        import requests as real_requests

        # --- Arrange ---
        mock_bq_client = MagicMock()
        mock_bigquery.Client.return_value = mock_bq_client
        mock_query_result = MagicMock()
        mock_query_result.__iter__ = MagicMock(
            return_value=iter([{"row_count": 0}])
        )
        mock_bq_client.query.return_value.result.return_value = mock_query_result

        mock_http_response = MagicMock()
        mock_http_response.raise_for_status.return_value = None
        # Return garbage bytes that are not a valid zip
        mock_http_response.content = b"not-a-valid-zip"
        mock_requests.get.return_value = mock_http_response
        mock_requests.exceptions.HTTPError = real_requests.exceptions.HTTPError

        request = _make_mock_request({"year": 2024, "month": 1})

        # --- Act ---
        response_body, status_code = main.ingest_bts_csv(request)

        # --- Assert ---
        assert status_code == 500
        assert response_body["status"] == "error"
        assert "message" in response_body
