import time

import pytest
from model_bakery import baker

from strava.models import Runner, RunnerSettings
from strava.tests.strava_api import ATHLETE, TOKENS, strava_url

pytestmark = pytest.mark.django_db

EXPIRED = str(int(time.time()) - 10_000)
VALID = str(int(time.time()) + 10_000)


def make_runner(
    strava_id: str = "12345",
    access_token: str = "access_token",
    refresh_token: str = "refresh_token",
    access_expires: str = VALID,
) -> Runner:
    return baker.make(
        Runner,
        strava_id=strava_id,
        access_token=access_token,
        refresh_token=refresh_token,
        access_expires=access_expires,
    )


def test_runner_str_method():
    assert str(make_runner(strava_id="12345")) == "12345"


def test_a_valid_token_is_used_as_is(strava_api):
    strava_api.get(strava_url("athlete"), json=ATHLETE)
    runner = make_runner(access_expires=VALID)

    runner.client.athlete()

    assert strava_api.calls[0].request.headers["Authorization"] == "Bearer access_token"


def test_an_expired_token_is_refreshed_before_the_call(strava_api):
    strava_api.post(strava_url("oauth/token"), json=TOKENS)
    strava_api.get(strava_url("athlete"), json=ATHLETE)
    runner = make_runner(access_expires=EXPIRED)

    runner.client.athlete()

    refresh, athlete = strava_api.calls
    assert refresh.request.url == strava_url("oauth/token")
    assert athlete.request.headers["Authorization"] == f"Bearer {TOKENS['access_token']}"


def test_refreshed_tokens_are_saved(strava_api):
    strava_api.post(strava_url("oauth/token"), json=TOKENS)
    runner = make_runner(access_expires=EXPIRED)

    runner.do_refresh_token()
    runner.refresh_from_db()

    assert runner.access_token == TOKENS["access_token"]
    assert runner.refresh_token == TOKENS["refresh_token"]
    assert runner.access_expires == str(TOKENS["expires_at"])


def test_the_stored_refresh_token_is_the_one_sent(strava_api):
    strava_api.post(strava_url("oauth/token"), json=TOKENS)
    runner = make_runner(access_expires=EXPIRED, refresh_token="the_stored_one")

    runner.do_refresh_token()

    assert "refresh_token=the_stored_one" in strava_api.calls[0].request.body


def test_enrichment_is_created_on_first_access():
    runner = make_runner()

    enrichment = runner.enrichment

    assert isinstance(enrichment, RunnerSettings)
    assert enrichment.weather_report
    assert enrichment.animal_comparison


def test_settings_str_method():
    runner = make_runner(strava_id="12345")

    assert str(runner.enrichment) == "Settings for 12345"


def test_enrichment_is_stable_across_accesses():
    runner = make_runner()

    assert runner.enrichment.pk == runner.enrichment.pk
    assert RunnerSettings.objects.filter(runner=runner).count() == 1
