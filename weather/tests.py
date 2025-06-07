from unittest import mock

from django.test import override_settings

import pytest

from weather.models import Weather


@pytest.mark.django_db
@override_settings(OWM_API_KEY="fake-key")
@mock.patch("weather.models.pyowm.OWM")
def test_get_weather_returns_expected_string(mock_owm_class):
    mock_owm_instance = mock.Mock(name="OWMInstance")
    mock_weather_manager = mock.Mock(name="WeatherManager")
    mock_observation = mock.Mock(name="Observation")
    mock_weather = mock.Mock(name="Weather")

    mock_owm_class.return_value = mock_owm_instance
    mock_owm_instance.weather_manager.return_value = mock_weather_manager
    mock_weather_manager.weather_at_coords.return_value = mock_observation
    mock_observation.weather = mock_weather

    mock_weather.detailed_status = "clear sky"
    mock_weather.temperature.return_value = {"temp": 20.0, "feels_like": 21.5}

    weather = Weather.from_lat_long(0, 0)

    assert weather.short == "Clear sky - 21.5°C"

    mock_owm_class.assert_called_once_with("fake-key")

    mock_owm_instance.weather_manager.assert_called_once_with()
    mock_weather_manager.weather_at_coords.assert_called_once_with(0, 0)
    mock_weather.temperature.assert_called_once_with("celsius")
