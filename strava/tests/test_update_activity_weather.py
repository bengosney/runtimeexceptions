from unittest.mock import patch

import pytest
from model_bakery import baker

from strava.models import Activity, Event, Runner, Weather
from strava.tasks.update_activity_weather import update_activity_weather, valid_activity_types


@pytest.fixture
def runner():
    return baker.make(Runner)


@pytest.fixture
def event(runner):
    return baker.make(Event, owner=runner, aspect_type=Event.ASPECT_TYPES["create"])


@pytest.fixture
def weather():
    return baker.make(Weather)


@pytest.mark.django_db
@patch("strava.tasks.update_activity_weather.FindOrCreateActivity")
@pytest.mark.parametrize("activity_type", valid_activity_types)
def test_update_activity_weather_sets_weather(mock_find_or_create, runner, weather, mocker, activity_type):
    event = baker.make(
        Event,
        owner=runner,
        aspect_type=Event.ASPECT_TYPES["create"],
    )
    activity = baker.make(Activity, runner=runner, weather=weather, type=activity_type)

    mocker.patch.object(activity, "add_weather")
    mock_find_or_create.return_value = lambda: activity
    update_activity_weather.func(event.pk)
    activity.add_weather.assert_called_once()


@pytest.mark.django_db
@patch("strava.tasks.update_activity_weather.FindOrCreateActivity")
def test_update_activity_weather_skips_non_create(mock_find_or_create):
    event = baker.make(Event, aspect_type=Event.ASPECT_TYPES["update"])
    update_activity_weather.func(event.pk)
    mock_find_or_create.assert_not_called()


@pytest.mark.django_db
@patch("strava.tasks.update_activity_weather.FindOrCreateActivity")
def test_update_activity_weather_skips_if_no_weather(mock_find_or_create, event, mocker):
    activity = baker.make(Activity, weather=None, type=valid_activity_types[0])
    mocker.patch.object(activity, "add_weather")
    mock_find_or_create.return_value = lambda: activity

    update_activity_weather.func(event.pk)

    mock_find_or_create.assert_called_once()
    activity.add_weather.assert_not_called()


@pytest.mark.django_db
@patch("strava.tasks.update_activity_weather.FindOrCreateActivity")
def test_update_activity_weather_skips_if_invalid_type(mock_find_or_create, event, mocker, weather):
    activity = baker.make(Activity, type="swim", weather=weather)
    mocker.patch.object(activity, "add_weather")
    mock_find_or_create.return_value = lambda: activity

    update_activity_weather.func(event.pk)

    mock_find_or_create.assert_called_once()
    activity.add_weather.assert_not_called()
