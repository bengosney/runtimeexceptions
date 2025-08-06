from collections.abc import Generator
from io import StringIO
from unittest import mock

from django.core.management import call_command as _call_command
from django.test import override_settings

import pytest


@pytest.fixture
def call_command():
    def _func(command_name, *args, **kwargs):
        out = StringIO()
        _call_command(
            command_name,
            *args,
            stdout=out,
            stderr=StringIO(),
            **kwargs,
        )
        return out.getvalue()

    return _func


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
def mock_callback_url(scope="module") -> str:
    return "https://example.com/webhook"


@pytest.fixture
def mock_list(mock_callback_url, scope="module") -> Generator[mock.Mock]:
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": 123, "callback_url": mock_callback_url}]
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
