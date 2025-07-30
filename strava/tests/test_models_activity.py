from unittest.mock import patch

import pytest
from model_bakery import baker

from strava.commands.find_or_create_activity import FindOrCreateActivity
from strava.data_models import DetailedActivity
from strava.models import Activity, Runner
from weather.models import Weather


@pytest.fixture
def runner():
    return baker.make(Runner)


@pytest.fixture
def activity_data():
    activity_json = {
        "id": 12345,
        "type": "Run",
        "end_latlng": [51.5, -0.1],
        "name": "Morning Run",
        "description": "",
    }
    return DetailedActivity.model_validate(activity_json)


@pytest.fixture
def weather():
    return baker.make(Weather)


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
