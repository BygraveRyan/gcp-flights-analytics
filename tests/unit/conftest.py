import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_gcs_bucket():
    """Mock GCS bucket for unit tests."""
    bucket = MagicMock()
    bucket.blob.return_value = MagicMock()
    return bucket


@pytest.fixture
def mock_storage_client(mock_gcs_bucket):
    """Mock google-cloud-storage Client."""
    client = MagicMock()
    client.bucket.return_value = mock_gcs_bucket
    return client


@pytest.fixture
def mock_secret_manager_client():
    """Mock Secret Manager client returning a dummy API key."""
    client = MagicMock()
    response = MagicMock()
    response.payload.data.decode.return_value = "test-api-key"
    client.access_secret_version.return_value = response
    return client
