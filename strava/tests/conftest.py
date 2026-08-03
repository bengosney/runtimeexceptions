from collections.abc import Generator
from io import StringIO
from unittest import mock

from django.core.management import call_command as _call_command
from django.test import override_settings

import pytest
import requests_cache
import responses
from model_bakery import baker

from strava.models import Runner
from strava.tests.strava_api import ATHLETE_ID

# Far enough out that the access token never expires mid-test.
NEVER_EXPIRES = "9999999999"


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
def mock_list_exception(scope="module") -> Generator[mock.Mock]:
    mock_response = mock.Mock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"error": "Internal Server Error"}
    with mock.patch("requests.get", return_value=mock_response) as mock_get:
        mock_get.side_effect = Exception("Mocked exception for testing")
        yield mock_get


@pytest.fixture
def mock_delete(scope="module") -> Generator[mock.Mock]:
    mock_response = mock.Mock()
    mock_response.status_code = 204
    with mock.patch("requests.delete", return_value=mock_response) as mock_delete:
        yield mock_delete


@pytest.fixture
def mock_delete_exception(scope="module") -> Generator[mock.Mock]:
    mock_response = mock.Mock()
    mock_response.status_code = 404
    mock_response.json.return_value = {"error": "Not Found"}
    with mock.patch("requests.delete", return_value=mock_response) as mock_delete:
        mock_delete.side_effect = Exception("Mocked exception for testing")
        yield mock_delete


@pytest.fixture(autouse=True, scope="session")
def uninstall_request_cache() -> Generator[None]:
    """
    The app installs a global requests cache on startup, which in tests would
    serve one test's response to another.
    """
    requests_cache.uninstall_cache()
    yield


@pytest.fixture
def strava_api() -> Generator[responses.RequestsMock]:
    """
    Strava, faked at the socket and nowhere else.

    Tests register urls and payloads, so everything from our url building down
    to the json decoding runs for real. A request to an unregistered url fails,
    and a registered response that goes unused fails on the way out.
    """
    with responses.RequestsMock() as mock_api:
        yield mock_api


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def runner(user) -> Runner:
    return baker.make(
        Runner,
        user=user,
        strava_id=str(ATHLETE_ID),
        access_token="access_token",
        refresh_token="refresh_token",
        access_expires=NEVER_EXPIRES,
    )
