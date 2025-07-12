from unittest import mock

from django.test import override_settings

import pytest

from weather.models import Weather


@pytest.mark.django_db
@override_settings(OWM_API_KEY="fake-key")
@mock.patch("weather.models.Weather.objects.create")
@mock.patch("weather.models.pyowm.OWM")
def test_get_weather_returns_expected_string(mock_owm_class, mock_create):
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
    mock_weather.reference_time.return_value = "2024-07-12 00:00:00+00:00"

    mock_create.return_value = mock.Mock(spec=Weather)

    Weather.from_lat_long(0, 0)

    mock_owm_class.assert_called_once_with("fake-key")

    mock_owm_instance.weather_manager.assert_called_once_with()
    mock_weather_manager.weather_at_coords.assert_called_once_with(0, 0)
    mock_weather.temperature.assert_called_once_with("celsius")
    mock_create.assert_called()


@pytest.mark.parametrize(
    "weather_icon,expected_emoji,name",
    [
        ("01d", "\U0001f323", "clear sky"),
        ("02d", "\U0001f324", "few clouds"),
        ("03d", "\U0001f325", "scattered clouds"),
        ("04d", "\U00002601", "broken clouds"),
        ("09d", "\U0001f326", "shower rain"),
        ("10d", "\U0001f327", "rain"),
        ("11d", "\U0001f329", "thunderstorm"),
        ("13d", "\U0001f328", "snow"),
        ("50d", "\U0001f32b", "mist"),
    ],
)
def test_emoji(weather_icon, expected_emoji, name):
    weather = Weather(
        latitude=0.0,
        longitude=0.0,
        timestamp=None,
        status="",
        detailed_status="",
        temperature=0.0,
        temperature_feels_like=0.0,
        humidity=0.0,
        wind_speed=0.0,
        wind_direction=0.0,
        wind_gust=0.0,
        other_data={"weather_icon_name": f"{weather_icon}d"} if weather_icon else {},
    )
    assert weather.emoji() == f"{expected_emoji}", (
        f"Expected emoji for {name} to be {expected_emoji}, got {weather.emoji()}"
    )
