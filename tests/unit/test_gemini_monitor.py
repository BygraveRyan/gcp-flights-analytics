import json
import pytest
from unittest.mock import patch, MagicMock
from google.api_core import exceptions as google_exceptions

# Import the function under test
from cloud_functions.gemini_monitor.main import gemini_monitor


def _make_request():
    """Creates a minimal mock Flask request object."""
    mock_request = MagicMock()
    mock_request.get_json.return_value = {}
    return mock_request


def _make_bq_row(table_name: str, row_count: int, last_ts: str | None):
    """Creates a mock BigQuery row."""
    from datetime import datetime, timezone
    row = MagicMock()
    row.table_name = table_name
    row.row_count = row_count
    row.last_ingestion_timestamp = (
        datetime.fromisoformat(last_ts) if last_ts else None
    )
    return row


class TestGeminiMonitorHappyPath:
    """Happy path: BQ returns data, Gemini returns ok status → 200 with status ok."""

    def test_returns_200_with_status_ok(self):
        bq_rows = [
            _make_bq_row("raw_fr24_positions", 1500, "2026-04-01T05:00:00+00:00"),
            _make_bq_row("raw_bts_flights", 200, "2026-04-01T04:00:00+00:00"),
        ]
        gemini_json = json.dumps({"status": "ok", "findings": []})

        mock_bq_client = MagicMock()
        mock_bq_client.query.return_value.result.return_value = iter(bq_rows)

        mock_genai_client = MagicMock()
        mock_genai_client.models.generate_content.return_value.text = gemini_json

        with patch(
            "cloud_functions.gemini_monitor.main.bigquery.Client",
            return_value=mock_bq_client,
        ):
            with patch(
                "cloud_functions.gemini_monitor.main.genai.Client",
                return_value=mock_genai_client,
            ):
                response, status_code = gemini_monitor(_make_request())

        assert status_code == 200
        assert response["status"] == "ok"
        assert "details" in response
        assert len(response["details"]["bq_summary"]) == 2
        assert response["details"]["gemini_findings"] == []

    def test_bq_summary_contains_both_tables(self):
        bq_rows = [
            _make_bq_row("raw_fr24_positions", 800, "2026-04-01T05:00:00+00:00"),
            _make_bq_row("raw_bts_flights", 50, "2026-04-01T04:00:00+00:00"),
        ]
        gemini_json = json.dumps({"status": "ok", "findings": ["All tables ingested normally."]})

        mock_bq_client = MagicMock()
        mock_bq_client.query.return_value.result.return_value = iter(bq_rows)

        mock_genai_client = MagicMock()
        mock_genai_client.models.generate_content.return_value.text = gemini_json

        with patch(
            "cloud_functions.gemini_monitor.main.bigquery.Client",
            return_value=mock_bq_client,
        ):
            with patch(
                "cloud_functions.gemini_monitor.main.genai.Client",
                return_value=mock_genai_client,
            ):
                response, status_code = gemini_monitor(_make_request())

        table_names = [r["table_name"] for r in response["details"]["bq_summary"]]
        assert "raw_fr24_positions" in table_names
        assert "raw_bts_flights" in table_names


class TestGeminiMonitorAnomalyDetected:
    """Anomaly path: Gemini returns anomaly → 200 with status anomaly, WARNING logged."""

    def test_returns_200_with_status_anomaly(self, caplog):
        bq_rows = [
            _make_bq_row("raw_fr24_positions", 0, None),
            _make_bq_row("raw_bts_flights", 300, "2026-04-01T04:00:00+00:00"),
        ]
        findings = ["raw_fr24_positions has 0 rows — ingestion may have failed."]
        gemini_json = json.dumps({"status": "anomaly", "findings": findings})

        mock_bq_client = MagicMock()
        mock_bq_client.query.return_value.result.return_value = iter(bq_rows)

        mock_genai_client = MagicMock()
        mock_genai_client.models.generate_content.return_value.text = gemini_json

        import logging
        with caplog.at_level(logging.WARNING, logger="cloud_functions.gemini_monitor.main"):
            with patch(
                "cloud_functions.gemini_monitor.main.bigquery.Client",
                return_value=mock_bq_client,
            ):
                with patch(
                    "cloud_functions.gemini_monitor.main.genai.Client",
                    return_value=mock_genai_client,
                ):
                    response, status_code = gemini_monitor(_make_request())

        assert status_code == 200
        assert response["status"] == "anomaly"
        assert response["details"]["gemini_findings"] == findings
        # Verify WARNING was logged for both zero rows and anomaly
        warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
        assert any("raw_fr24_positions" in msg for msg in warning_messages)
        assert any("Anomaly detected" in msg for msg in warning_messages)

    def test_anomaly_findings_preserved_in_response(self):
        bq_rows = [
            _make_bq_row("raw_fr24_positions", 0, None),
            _make_bq_row("raw_bts_flights", 0, None),
        ]
        findings = [
            "raw_fr24_positions: 0 rows in last 24h.",
            "raw_bts_flights: 0 rows in last 24h.",
        ]
        gemini_json = json.dumps({"status": "anomaly", "findings": findings})

        mock_bq_client = MagicMock()
        mock_bq_client.query.return_value.result.return_value = iter(bq_rows)

        mock_genai_client = MagicMock()
        mock_genai_client.models.generate_content.return_value.text = gemini_json

        with patch(
            "cloud_functions.gemini_monitor.main.bigquery.Client",
            return_value=mock_bq_client,
        ):
            with patch(
                "cloud_functions.gemini_monitor.main.genai.Client",
                return_value=mock_genai_client,
            ):
                response, status_code = gemini_monitor(_make_request())

        assert status_code == 200
        assert response["status"] == "anomaly"
        assert len(response["details"]["gemini_findings"]) == 2


class TestGeminiMonitorBQError:
    """BQ error path: raises GoogleAPIError → function returns 500."""

    def test_bq_error_returns_500(self):
        mock_bq_client = MagicMock()
        mock_bq_client.query.side_effect = google_exceptions.GoogleAPIError(
            "BigQuery service unavailable"
        )

        with patch(
            "cloud_functions.gemini_monitor.main.bigquery.Client",
            return_value=mock_bq_client,
        ):
            response, status_code = gemini_monitor(_make_request())

        assert status_code == 500
        assert response["status"] == "error"
        assert "BigQuery service unavailable" in response["message"]

    def test_bq_error_does_not_call_gemini(self):
        mock_bq_client = MagicMock()
        mock_bq_client.query.side_effect = google_exceptions.GoogleAPIError(
            "Permission denied"
        )
        mock_genai_client = MagicMock()

        with patch(
            "cloud_functions.gemini_monitor.main.bigquery.Client",
            return_value=mock_bq_client,
        ):
            with patch(
                "cloud_functions.gemini_monitor.main.genai.Client",
                return_value=mock_genai_client,
            ):
                response, status_code = gemini_monitor(_make_request())

        assert status_code == 500
        mock_genai_client.models.generate_content.assert_not_called()
