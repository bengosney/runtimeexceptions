from http import HTTPStatus

from django.contrib.auth.models import User

import pytest
from model_bakery import baker

from strava.commands import ConnectStravaAccount
from strava.exceptions import StravaNotAuthenticatedError
from strava.models import Runner
from strava.tests.strava_api import ATHLETE, AUTHORIZATION, TOKENS, strava_url

pytestmark = pytest.mark.django_db


def test_connect_new_user(strava_api):
    strava_api.post(strava_url("oauth/token"), json=AUTHORIZATION)

    user = ConnectStravaAccount("a_code")()

    assert user.username == ATHLETE["username"]
    assert user.first_name == ATHLETE["firstname"]
    assert user.last_name == ATHLETE["lastname"]
    assert not user.has_usable_password()


def test_connect_stores_the_tokens(strava_api):
    strava_api.post(strava_url("oauth/token"), json=AUTHORIZATION)

    ConnectStravaAccount("a_code")()

    runner = Runner.objects.get(strava_id=ATHLETE["id"])
    assert runner.access_token == TOKENS["access_token"]
    assert runner.refresh_token == TOKENS["refresh_token"]
    assert runner.access_expires == str(TOKENS["expires_at"])


def test_connect_sends_the_code(strava_api):
    strava_api.post(strava_url("oauth/token"), json=AUTHORIZATION)

    ConnectStravaAccount("a_code")()

    assert "code=a_code" in strava_api.calls[0].request.body


def test_connect_links_the_runner_to_the_user(strava_api):
    strava_api.post(strava_url("oauth/token"), json=AUTHORIZATION)

    user = ConnectStravaAccount("a_code")()

    assert Runner.objects.get(strava_id=ATHLETE["id"]).user == user


def test_connect_existing_user(strava_api):
    strava_api.post(strava_url("oauth/token"), json=AUTHORIZATION)
    existing_user = baker.make(User, username=ATHLETE["username"], first_name="old", last_name="name")

    user = ConnectStravaAccount("a_code")()

    assert user.pk == existing_user.pk
    assert user.first_name == ATHLETE["firstname"]
    assert user.last_name == ATHLETE["lastname"]
    assert User.objects.count() == 1


def test_reconnecting_replaces_stale_tokens(strava_api):
    """
    Reconnecting is how a runner recovers from a revoked token, so the new
    ones have to win rather than be left alongside the old.
    """
    strava_api.post(strava_url("oauth/token"), json=AUTHORIZATION)
    baker.make(Runner, strava_id=str(ATHLETE["id"]), access_token="stale", refresh_token="stale")

    ConnectStravaAccount("a_code")()

    runner = Runner.objects.get(strava_id=ATHLETE["id"])
    assert runner.access_token == TOKENS["access_token"]
    assert runner.refresh_token == TOKENS["refresh_token"]
    assert Runner.objects.count() == 1


def test_connect_rejected_by_strava(strava_api):
    strava_api.post(strava_url("oauth/token"), status=HTTPStatus.UNAUTHORIZED)

    with pytest.raises(StravaNotAuthenticatedError):
        ConnectStravaAccount("a_bad_code")()

    assert not User.objects.exists()
    assert not Runner.objects.exists()
