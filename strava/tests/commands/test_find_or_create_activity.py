import datetime
from unittest.mock import patch

import pytest
from model_bakery import baker

from strava.commands.find_or_create_activity import FindOrCreateActivity
from strava.data_models import LatLng
from strava.models import DetailedActivityTriathlon, Runner
from weather.models import Weather


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
