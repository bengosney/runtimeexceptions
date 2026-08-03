import datetime
from unittest.mock import patch

import pytest
from model_bakery import baker

from strava.commands.find_or_create_activity import FindOrCreateActivity
from strava.models import Activity
from strava.tests.strava_api import activity as activity_payload
from strava.tests.strava_api import strava_url
from weather.models import Weather

pytestmark = pytest.mark.django_db

ACTIVITY_ID = 101


@pytest.fixture
def weather() -> Weather:
    return baker.make(Weather)


@pytest.fixture
def owm(weather):
    """
    OpenWeatherMap sits behind pyowm rather than requests, so it is the one
    thing here that stays a mock.
    """
    with patch("strava.models.Weather.from_lat_long", return_value=weather) as mock:
        yield mock


def finished(seconds_ago: int) -> str:
    """
    A start date placing the end of the activity this many seconds back.
    """
    ended = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(seconds=seconds_ago)
    return (ended - datetime.timedelta(seconds=1900)).isoformat()


@pytest.mark.parametrize(
    "seconds_ago, expected_weather",
    [
        (0, True),
        (899, True),
        (901, False),
        (1800, False),
    ],
)
def test_weather_is_only_fetched_for_a_recent_activity(runner, strava_api, owm, seconds_ago, expected_weather):
    strava_api.get(strava_url(f"activities/{ACTIVITY_ID}"), json=activity_payload(start_date=finished(seconds_ago)))

    activity = FindOrCreateActivity(runner, ACTIVITY_ID)()

    assert (activity.weather is not None) == expected_weather
    assert owm.called == expected_weather


def test_existing_activity_is_returned_untouched(runner, strava_api):
    """
    Strava is not asked for an activity we already hold; an unregistered GET
    would fail the test.
    """
    existing = baker.make(Activity, runner=runner, strava_id=ACTIVITY_ID)

    assert FindOrCreateActivity(runner, ACTIVITY_ID)() == existing


def test_creates_the_activity_from_what_strava_sends(runner, strava_api, owm, weather):
    strava_api.get(strava_url(f"activities/{ACTIVITY_ID}"), json=activity_payload(start_date=finished(0)))

    result = FindOrCreateActivity(runner, ACTIVITY_ID)()

    created = Activity.objects.get(strava_id=ACTIVITY_ID, runner=runner)
    assert result == created
    assert created.type == "Run"
    assert created.weather == weather


def test_weather_is_taken_from_where_the_activity_ended(runner, strava_api, owm):
    strava_api.get(
        strava_url(f"activities/{ACTIVITY_ID}"),
        json=activity_payload(start_date=finished(0), end_latlng=[51.51, -0.12]),
    )

    FindOrCreateActivity(runner, ACTIVITY_ID)()

    owm.assert_called_once_with(51.51, -0.12)


def test_no_weather_without_an_end_point(runner, strava_api):
    strava_api.get(
        strava_url(f"activities/{ACTIVITY_ID}"),
        json=activity_payload(start_date=finished(0), end_latlng=None),
    )

    result = FindOrCreateActivity(runner, ACTIVITY_ID)()

    assert result.weather is None
    assert result.type == "Run"
