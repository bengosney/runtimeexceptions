from unittest.mock import patch

from django.contrib.auth.models import User

import pytest
from model_bakery import baker

from strava.auth import StravaAuthorization
from strava.commands import ConnectStravaAccount
from strava.models import Runner

ATHLETE = {"id": 12345, "username": "testuser", "firstname": "Test", "lastname": "User"}

AUTHORIZATION = StravaAuthorization.model_validate(
    {
        "access_token": "token",
        "refresh_token": "refresh",
        "expires_at": 1234567890,
        "athlete": ATHLETE,
    }
)


@pytest.fixture
def exchange_code():
    with patch("strava.commands.connect_account.StravaOAuth.exchange_code", return_value=AUTHORIZATION) as mock:
        yield mock


@pytest.mark.django_db
def test_connect_new_user(exchange_code):
    user = ConnectStravaAccount("code")()

    exchange_code.assert_called_once_with("code")
    assert user.username == ATHLETE["username"]
    assert user.first_name == ATHLETE["firstname"]
    assert user.last_name == ATHLETE["lastname"]
    assert not user.has_usable_password()

    runner = Runner.objects.get(strava_id=ATHLETE["id"])
    assert runner.user == user
    assert runner.access_token == AUTHORIZATION.access_token
    assert runner.refresh_token == AUTHORIZATION.refresh_token
    assert runner.access_expires == str(AUTHORIZATION.expires_at)


@pytest.mark.django_db
def test_connect_existing_user(exchange_code):
    existing_user = baker.make(User, username=ATHLETE["username"], first_name="old", last_name="name")

    user = ConnectStravaAccount("code")()

    assert user.pk == existing_user.pk
    assert user.first_name == ATHLETE["firstname"]
    assert user.last_name == ATHLETE["lastname"]
    assert Runner.objects.get(strava_id=ATHLETE["id"]).user == user


@pytest.mark.django_db
def test_connect_updates_existing_runner_tokens(exchange_code):
    baker.make(Runner, strava_id=str(ATHLETE["id"]), access_token="stale", refresh_token="stale")

    ConnectStravaAccount("code")()

    runner = Runner.objects.get(strava_id=ATHLETE["id"])
    assert runner.access_token == AUTHORIZATION.access_token
    assert runner.refresh_token == AUTHORIZATION.refresh_token
