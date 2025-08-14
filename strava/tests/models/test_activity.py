from unittest.mock import patch

import pytest
from model_bakery import baker

from strava.data_models import DetailedActivity
from strava.models import Activity
from weather.models import Weather


@pytest.mark.django_db
def test_add_weather_no_weather():
    activity: Activity = baker.make(Activity)
    assert not activity.add_weather()


@pytest.mark.django_db
def test_add_weather_integration():
    weather = baker.make(Weather)
    runner = baker.make("strava.Runner", access_expires="9999999999")
    activity = baker.make(Activity, weather=weather, runner=runner)

    with (
        patch.object(runner, "update_activity", return_value="updated") as mock_update,
        patch.object(runner, "activity") as mock_activity,
    ):
        mock_data_in = DetailedActivity.model_validate({"description": "Old description", "name": "Morning Run"})
        mock_activity.return_value = mock_data_in

        activity.add_weather()

        mock_activity.assert_called_once()
        mock_update.assert_called_once()
