from http import HTTPStatus
from urllib.parse import parse_qs, urlparse

import pytest

from strava.auth import StravaOAuth
from strava.exceptions import StravaNotAuthenticatedError

ATHLETE_ID = 12345

TOKEN_RESPONSE = {
    "access_token": "token",
    "refresh_token": "refresh",
    "expires_at": 1234567890,
}

AUTHORIZATION_RESPONSE = TOKEN_RESPONSE | {
    "athlete": {"id": ATHLETE_ID, "username": "testuser", "firstname": "Test", "lastname": "User"}
}


def test_authorization_url(settings):
    url = StravaOAuth().authorization_url("http://example.com/callback")

    assert url is not None
    query = parse_qs(urlparse(url).query)
    assert query["redirect_uri"] == ["http://example.com/callback"]
    assert query["client_id"] == [settings.STRAVA_CLIENT_ID]
    assert query["scope"] == [StravaOAuth.SCOPES]
    assert query["response_type"] == ["code"]


def test_exchange_code(mock_strava_request, settings):
    mock_strava_request.return_value.json.return_value = AUTHORIZATION_RESPONSE
    mock_strava_request.return_value.status_code = HTTPStatus.OK

    authorization = StravaOAuth().exchange_code("code")

    assert authorization.access_token == "token"
    assert authorization.refresh_token == "refresh"
    assert authorization.expires_at == AUTHORIZATION_RESPONSE["expires_at"]
    assert authorization.athlete.id == ATHLETE_ID
    assert authorization.athlete.username == "testuser"

    assert mock_strava_request.call_args.kwargs["data"] == {
        "client_id": settings.STRAVA_CLIENT_ID,
        "client_secret": settings.STRAVA_SECRET,
        "code": "code",
        "grant_type": "authorization_code",
    }


def test_refresh(mock_strava_request, settings):
    mock_strava_request.return_value.json.return_value = TOKEN_RESPONSE
    mock_strava_request.return_value.status_code = HTTPStatus.OK

    tokens = StravaOAuth().refresh("old_refresh")

    assert tokens.access_token == "token"
    assert tokens.refresh_token == "refresh"
    assert tokens.expires_at == TOKEN_RESPONSE["expires_at"]

    assert mock_strava_request.call_args.kwargs["data"] == {
        "client_id": settings.STRAVA_CLIENT_ID,
        "client_secret": settings.STRAVA_SECRET,
        "refresh_token": "old_refresh",
        "grant_type": "refresh_token",
    }


def test_refresh_rejected(mock_strava_request):
    mock_strava_request.return_value.status_code = HTTPStatus.UNAUTHORIZED

    with pytest.raises(StravaNotAuthenticatedError):
        StravaOAuth().refresh("old_refresh")
