from collections.abc import Generator
from unittest import mock

from django.test import override_settings

import pytest


@pytest.fixture(autouse=True, scope="module")
def use_strava_settings() -> Generator[None]:
    with override_settings(STRAVA_CLIENT_ID="test_id", STRAVA_SECRET="test_secret"):
        yield


@pytest.fixture
def mock_create(scope="module") -> Generator[mock.Mock]:
    mock_response = mock.Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 123}
    with mock.patch("requests.post", return_value=mock_response) as mock_post:
        yield mock_post


@pytest.fixture
def mock_list(scope="module") -> Generator[mock.Mock]:
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": 123, "callback_url": "https://example.com/webhook"}]
    with mock.patch("requests.get", return_value=mock_response) as mock_get:
        yield mock_get


@pytest.fixture
def mock_list_empty(scope="module") -> Generator[mock.Mock]:
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    with mock.patch("requests.get", return_value=mock_response) as mock_get:
        yield mock_get


@pytest.fixture
def mock_delete(scope="module") -> Generator[mock.Mock]:
    mock_response = mock.Mock()
    mock_response.status_code = 204
    with mock.patch("requests.delete", return_value=mock_response) as mock_delete:
        yield mock_delete
