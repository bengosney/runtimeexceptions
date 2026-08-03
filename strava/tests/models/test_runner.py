import time
from http import HTTPStatus
from unittest.mock import patch

import pytest
from model_bakery import baker

from strava.auth import StravaTokens
from strava.models import Runner, RunnerSettings

EXPIRES_AT = 1234567890


@pytest.mark.django_db
def test_runner_str_method():
    strava_id = "12345"
    runner = baker.make(Runner, strava_id=strava_id)
    assert str(runner) == strava_id


@pytest.mark.django_db
@patch("strava.models.StravaOAuth.refresh")
def test_do_refresh_token(mock_refresh):
    mock_refresh.return_value = StravaTokens(
        access_token="newtoken",
        refresh_token="newrefresh",
        expires_at=EXPIRES_AT,
    )
    runner: Runner = baker.make(
        Runner,
        strava_id="12345",
        access_token="token",
        access_expires="0",
        refresh_token="refresh",
    )

    runner.do_refresh_token()

    mock_refresh.assert_called_once_with("refresh")
    assert runner.access_token == "newtoken"
    assert runner.access_expires == EXPIRES_AT
    assert runner.refresh_token == "newrefresh"

    runner.refresh_from_db()
    assert runner.access_token == "newtoken"


@pytest.mark.django_db
@patch.object(Runner, "do_refresh_token")
def test_auth_code_refreshes_if_expired(mock_refresh):
    runner = baker.make(
        Runner,
        strava_id="12345",
        access_token="token",
        access_expires=str(int(time.time()) - 10000),
        refresh_token="refresh",
    )
    code = runner.auth_code
    assert code == "token"
    mock_refresh.assert_called_once()


@pytest.mark.django_db
@patch.object(Runner, "do_refresh_token")
def test_auth_code_does_not_refresh_if_not_expired(mock_refresh):
    runner = baker.make(
        Runner,
        strava_id="12345",
        access_token="token",
        access_expires=str(int(time.time()) + 10000),
        refresh_token="refresh",
    )
    code = runner.auth_code
    assert code == "token"
    mock_refresh.assert_not_called()


@pytest.mark.django_db
def test_client_authenticates_as_the_runner(mock_strava_request):
    mock_strava_request.return_value.status_code = HTTPStatus.OK
    runner: Runner = baker.make(Runner, access_token="token", access_expires="9999999999")

    runner.client.request("test")

    assert mock_strava_request.call_args.kwargs["headers"]["Authorization"] == "Bearer token"


@pytest.mark.django_db
@patch.object(Runner, "do_refresh_token")
def test_client_refreshes_an_expired_token(mock_refresh, mock_strava_request):
    mock_strava_request.return_value.status_code = HTTPStatus.OK
    runner: Runner = baker.make(Runner, access_token="token", access_expires="0")

    runner.client.request("test")

    mock_refresh.assert_called_once()


@pytest.mark.django_db
def test_enrichment_creates_settings_on_first_access():
    runner: Runner = baker.make(Runner)

    enrichment = runner.enrichment

    assert isinstance(enrichment, RunnerSettings)
    assert runner.enrichment.pk == enrichment.pk
