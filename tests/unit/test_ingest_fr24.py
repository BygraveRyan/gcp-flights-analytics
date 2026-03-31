import json
import pytest
from unittest.mock import MagicMock, patch


class TestIngestFr24:
    """Unit tests for the fn-ingest-fr24 Cloud Function."""

    SAMPLE_FR24_RESPONSE = {
        "data": [
            {
                "fr24_id": "abc123",
                "callsign": "BAW123",
                "lat": 51.5,
                "lon": -0.1,
                "alt": 35000,
                "gspeed": 450,
                "vspeed": 0,
                "on_ground": False,
                "icao24": "400BE3",
            }
        ],
        "meta": {"count": 1},
    }

    def _make_request(self):
        req = MagicMock()
        req.get_json.return_value = {}
        return req

    @patch("cloud_functions.ingest_fr24.main.storage.Client")
    @patch("cloud_functions.ingest_fr24.main.secretmanager.SecretManagerServiceClient")
    @patch("cloud_functions.ingest_fr24.main.requests.get")
    def test_success_writes_ndjson_to_gcs(
        self, mock_get, mock_sm_class, mock_storage_class
    ):
        # Arrange
        mock_sm_client = MagicMock()
        secret_resp = MagicMock()
        secret_resp.payload.data.decode.return_value = "test-key"
        mock_sm_client.access_secret_version.return_value = secret_resp
        mock_sm_class.return_value = mock_sm_client

        mock_resp = MagicMock()
        mock_resp.json.return_value = self.SAMPLE_FR24_RESPONSE
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_get.return_value = mock_resp

        mock_blob = MagicMock()
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_storage_class.return_value.bucket.return_value = mock_bucket

        from cloud_functions.ingest_fr24.main import ingest_fr24

        # Act
        body, status = ingest_fr24(self._make_request())

        # Assert
        assert status == 200
        assert body["status"] == "success"
        assert body["rows_written"] == 1
        assert body["gcs_path"] is not None
        mock_blob.upload_from_string.assert_called_once()
        content = mock_blob.upload_from_string.call_args[0][0]
        record = json.loads(content.split("\n")[0])
        assert record["callsign"] == "BAW123"
        assert "ingestion_timestamp" in record

    @patch("cloud_functions.ingest_fr24.main.storage.Client")
    @patch("cloud_functions.ingest_fr24.main.secretmanager.SecretManagerServiceClient")
    @patch("cloud_functions.ingest_fr24.main.requests.get")
    def test_empty_response_returns_200_with_zero_rows(
        self, mock_get, mock_sm_class, mock_storage_class
    ):
        mock_sm_client = MagicMock()
        secret_resp = MagicMock()
        secret_resp.payload.data.decode.return_value = "test-key"
        mock_sm_client.access_secret_version.return_value = secret_resp
        mock_sm_class.return_value = mock_sm_client

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [], "meta": {"count": 0}}
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_get.return_value = mock_resp

        from cloud_functions.ingest_fr24.main import ingest_fr24

        body, status = ingest_fr24(self._make_request())

        assert status == 200
        assert body["status"] == "success"
        assert body["rows_written"] == 0
        assert body["gcs_path"] is None
        mock_storage_class.return_value.bucket.return_value.blob.return_value.upload_from_string.assert_not_called()

    @patch("cloud_functions.ingest_fr24.main.secretmanager.SecretManagerServiceClient")
    @patch("cloud_functions.ingest_fr24.main.requests.get")
    def test_http_error_returns_error_status(self, mock_get, mock_sm_class):
        import requests

        mock_sm_client = MagicMock()
        secret_resp = MagicMock()
        secret_resp.payload.data.decode.return_value = "test-key"
        mock_sm_client.access_secret_version.return_value = secret_resp
        mock_sm_class.return_value = mock_sm_client

        http_error_response = MagicMock()
        http_error_response.status_code = 401
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=http_error_response
        )
        mock_get.return_value = mock_resp

        from cloud_functions.ingest_fr24.main import ingest_fr24

        body, status = ingest_fr24(self._make_request())

        assert status == 401
        assert body["status"] == "error"
