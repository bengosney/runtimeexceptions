from datetime import UTC, datetime
from urllib.parse import parse_qs

import pytest
from model_bakery import baker

from strava.models import Activity, Runner
from strava.tests.strava_api import activity as activity_payload
from strava.tests.strava_api import strava_url
from weather.models import Weather

pytestmark = pytest.mark.django_db

MARKER = Activity.MARKER_STRING


@pytest.fixture
def weather() -> Weather:
    return baker.make(
        Weather,
        timestamp=datetime(2026, 1, 1, 8, 0, tzinfo=UTC),
        status="Rain",
        detailed_status="light rain",
        temperature=8.0,
        temperature_feels_like=6.0,
        humidity=80.0,
        wind_speed=5.0,
        wind_direction=180.0,
        wind_gust=8.0,
        other_data={"weather_icon_name": "10d"},
    )


@pytest.fixture
def activity(runner, weather) -> Activity:
    return baker.make(Activity, weather=weather, runner=runner, strava_id=101, type="Run")


def written(strava_api) -> dict[str, str]:
    """
    The fields sent in the PUT, unwrapped from the form encoding.
    """
    put = next(call for call in strava_api.calls if call.request.method == "PUT")
    return {field: values[0] for field, values in parse_qs(put.request.body).items()}


def test_add_weather_no_weather():
    assert not baker.make(Activity, weather=None).add_weather()


def test_add_weather_writes_the_report_and_the_emoji(activity, weather, strava_api):
    strava_api.get(strava_url("activities/101"), json=activity_payload(name="Morning Run", description="Felt good"))
    strava_api.put(strava_url("activities/101"), json=activity_payload())

    activity.add_weather()

    sent = written(strava_api)
    assert sent["description"] == f"Felt good {MARKER}{weather.long()}{MARKER}"
    assert sent["name"] == f"Morning Run {MARKER}{weather.emoji()}{MARKER}"


def test_add_weather_replaces_an_earlier_report(activity, weather, strava_api):
    already_written = f"Felt good {MARKER}stale weather{MARKER}"
    strava_api.get(strava_url("activities/101"), json=activity_payload(description=already_written))
    strava_api.put(strava_url("activities/101"), json=activity_payload())

    activity.add_weather()

    sent = written(strava_api)
    assert "stale weather" not in sent["description"]
    assert sent["description"] == f"Felt good {MARKER}{weather.long()}{MARKER}"


def test_add_weather_leaves_the_rest_of_the_description_alone(activity, strava_api):
    strava_api.get(strava_url("activities/101"), json=activity_payload(description="Ran with the club"))
    strava_api.put(strava_url("activities/101"), json=activity_payload())

    activity.add_weather()

    assert written(strava_api)["description"].startswith("Ran with the club ")


def test_add_weather_strips_a_disabled_report(activity, runner, strava_api):
    enrichment = runner.enrichment
    enrichment.weather_report = False
    enrichment.save()

    already_written = f"Felt good {MARKER}old weather{MARKER}"
    strava_api.get(strava_url("activities/101"), json=activity_payload(description=already_written))
    strava_api.put(strava_url("activities/101"), json=activity_payload())

    activity.add_weather()

    assert written(strava_api)["description"] == "Felt good "


def test_add_weather_strips_a_disabled_emoji(activity, runner, weather, strava_api):
    enrichment = runner.enrichment
    enrichment.weather_emoji = False
    enrichment.save()

    strava_api.get(
        strava_url("activities/101"),
        json=activity_payload(name=f"Morning Run {MARKER}old emoji{MARKER}"),
    )
    strava_api.put(strava_url("activities/101"), json=activity_payload())

    activity.add_weather()

    sent = written(strava_api)
    assert sent["name"] == "Morning Run "
    assert sent["description"] == f" {MARKER}{weather.long()}{MARKER}"


def test_add_weather_writes_nothing_when_already_current(activity, weather, strava_api):
    """
    Reprocessing an activity should not churn it on Strava; an unregistered
    PUT would fail the test.
    """
    strava_api.get(
        strava_url("activities/101"),
        json=activity_payload(
            description=f"Felt good {MARKER}{weather.long()}{MARKER}",
            name=f"Morning Run {MARKER}{weather.emoji()}{MARKER}",
        ),
    )

    assert activity.add_weather() is False


def test_add_weather_uses_the_runners_own_token(activity, runner, strava_api):
    strava_api.get(strava_url("activities/101"), json=activity_payload())
    strava_api.put(strava_url("activities/101"), json=activity_payload())

    activity.add_weather()

    assert isinstance(runner, Runner)
    assert strava_api.calls[0].request.headers["Authorization"] == f"Bearer {runner.access_token}"
