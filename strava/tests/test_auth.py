from http import HTTPStatus
from urllib.parse import parse_qs, urlparse

import pytest

from strava.auth import StravaOAuth
from strava.exceptions import StravaNotAuthenticatedError
from strava.tests.strava_api import ATHLETE, AUTHORIZATION, TOKENS, strava_url

REDIRECT_URI = "https://example.com/strava/callback"


def test_authorization_url(settings):
    url = StravaOAuth().authorization_url(REDIRECT_URI)

    assert url is not None
    assert url.startswith(strava_url("oauth/authorize"))

    query = parse_qs(urlparse(url).query)
    assert query["client_id"] == [settings.STRAVA_CLIENT_ID]
    assert query["redirect_uri"] == [REDIRECT_URI]
    assert query["response_type"] == ["code"]
    assert query["approval_prompt"] == ["auto"]


def test_authorization_url_asks_for_the_scopes_the_app_needs():
    url = StravaOAuth().authorization_url(REDIRECT_URI)

    assert url is not None
    scopes = set(parse_qs(urlparse(url).query)["scope"][0].split(","))

    # Reading activities to enrich them, writing the enrichment back.
    assert {"activity:read_all", "activity:write"} <= scopes


def test_exchange_code(strava_api, settings):
    strava_api.post(strava_url("oauth/token"), json=AUTHORIZATION)

    authorization = StravaOAuth().exchange_code("a_code")

    assert authorization.access_token == TOKENS["access_token"]
    assert authorization.refresh_token == TOKENS["refresh_token"]
    assert authorization.expires_at == TOKENS["expires_at"]
    assert authorization.athlete.id == ATHLETE["id"]
    assert authorization.athlete.username == ATHLETE["username"]

    assert parse_qs(strava_api.calls[0].request.body) == {
        "client_id": [settings.STRAVA_CLIENT_ID],
        "client_secret": [settings.STRAVA_SECRET],
        "code": ["a_code"],
        "grant_type": ["authorization_code"],
    }


def test_exchange_code_is_unauthenticated(strava_api):
    """
    The code is the credential at this point, so no bearer token is sent.
    """
    strava_api.post(strava_url("oauth/token"), json=AUTHORIZATION)

    StravaOAuth().exchange_code("a_code")

    assert "Authorization" not in strava_api.calls[0].request.headers


def test_refresh(strava_api, settings):
    strava_api.post(strava_url("oauth/token"), json=TOKENS)

    tokens = StravaOAuth().refresh("old_refresh_token")

    assert tokens.access_token == TOKENS["access_token"]
    assert tokens.refresh_token == TOKENS["refresh_token"]
    assert tokens.expires_at == TOKENS["expires_at"]

    assert parse_qs(strava_api.calls[0].request.body) == {
        "client_id": [settings.STRAVA_CLIENT_ID],
        "client_secret": [settings.STRAVA_SECRET],
        "refresh_token": ["old_refresh_token"],
        "grant_type": ["refresh_token"],
    }


def test_refresh_rejected(strava_api):
    strava_api.post(strava_url("oauth/token"), status=HTTPStatus.UNAUTHORIZED)

    with pytest.raises(StravaNotAuthenticatedError):
        StravaOAuth().refresh("stale_refresh_token")
