import datetime
from unittest.mock import patch

import pytest
from model_bakery import baker

from strava.commands.find_or_create_activity import FindOrCreateActivity
from strava.data_models import ActivityType, DetailedActivity, LatLng
from strava.models import Activity, DetailedActivityTriathlon, Runner
from weather.models import Weather


@pytest.fixture
def runner():
    return baker.make(Runner)


@pytest.fixture
def activity_data():
    return DetailedActivity(
        id=12345,
        type=ActivityType.Run,
        end_latlng=LatLng([51.5, -0.1]),
        name="Morning Run",
        description="",
        start_date=datetime.datetime.now(tz=datetime.UTC),
    )


@pytest.fixture
def weather():
    return baker.make(Weather)


@pytest.mark.parametrize(
    "delta,should_fetch_weather",
    [
        (datetime.timedelta(seconds=0), True),
        (datetime.timedelta(seconds=899), True),
        (datetime.timedelta(seconds=901), False),
        (datetime.timedelta(seconds=1800), False),
    ],
)
@pytest.mark.django_db
@patch("strava.models.Weather.from_lat_long")
@patch("strava.models.Runner.activity")
def test_time_checking(mock_activity, mock_weather, monkeypatch, delta, should_fetch_weather):
    now = datetime.datetime.now(tz=datetime.UTC)
    start_date = now - delta

    mock_activity.return_value = DetailedActivityTriathlon(id=123, start_date=start_date, end_latlng=LatLng([1.0, 2.0]))
    mock_weather.return_value = baker.make(Weather)

    runner = baker.make(Runner)
    find_or_create = FindOrCreateActivity(runner, 123)
    find_or_create()
    if should_fetch_weather:
        mock_weather.assert_called_once()
    else:
        mock_weather.assert_not_called()


@pytest.mark.django_db
def test_find_or_create_existing_activity(runner):
    activity = baker.make(Activity, runner=runner, strava_id=12345)
    find_or_create_activity = FindOrCreateActivity(runner, 12345)

    result = find_or_create_activity()
    assert result == activity


@pytest.mark.django_db
@patch("strava.models.Weather.from_lat_long")
def test_find_or_create_creates_new_activity(mock_weather, runner, activity_data, weather):
    mock_weather.return_value = weather
    # Patch runner.activity to return our dummy activity_data
    runner.activity = lambda activity_id: activity_data
    find_or_create_activity = FindOrCreateActivity(runner, 12345)
    result = find_or_create_activity()
    created = Activity.objects.get(strava_id=12345, runner=runner)
    assert result == created
    assert created.weather == weather  # type: ignore[attr-defined]
    assert created.type == activity_data.type.value  # type: ignore[attr-defined]
    mock_weather.assert_called_once_with(51.5, -0.1)


@pytest.mark.django_db
def test_find_or_create_no_end_latlng(runner, activity_data):
    activity_data.end_latlng = None
    runner.activity = lambda activity_id: activity_data
    find_or_create_activity = FindOrCreateActivity(runner, 12345)
    result = find_or_create_activity()
    created = Activity.objects.get(strava_id=12345, runner=runner)
    assert result == created
    assert created.weather is None  # type: ignore[attr-defined]
    assert created.type == activity_data.type.value  # type: ignore[attr-defined]
