from enum import StrEnum
from typing import Self

from django.conf import settings
from django.db import models

import pyowm
from pyowm.weatherapi25.weather import Weather as PyOWMWeather


class Weather(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField()

    status = models.CharField(max_length=100)
    detailed_status = models.CharField(max_length=200)

    temperature = models.FloatField()
    temperature_feels_like = models.FloatField()
    humidity = models.FloatField()
    wind_speed = models.FloatField()
    wind_direction = models.FloatField()
    wind_gust = models.FloatField()

    other_data = models.JSONField(default=dict)

    def __str__(self) -> str:
        return self.detailed_status

    def short(self) -> str:
        """
        Returns a short string representation of the weather.
        """
        return f"{self.status} {self.temperature}°C"

    def long(self) -> str:
        """
        Returns a long string representation of the weather.
        """
        return f"{self.detailed_status}, {self.temperature_celsius()}, {self.humidity_percentage()}, {self.wind()}"

    def temperature_celsius(self) -> str:
        """
        Returns the temperature in Celsius.
        """
        return f"{self.temperature:.1f}°C feels like {self.temperature_feels_like:.1f}°C"

    def humidity_percentage(self) -> str:
        """
        Returns the humidity as a percentage.
        """
        return f"Humidity {self.humidity:.0f}%"

    @staticmethod
    def degrees_to_cardinal(d):
        """
        Converts degrees to cardinal direction.
        """
        dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        ix = round(d / (360.0 / len(dirs)))
        return dirs[ix % len(dirs)]

    @staticmethod
    def mps_to_kph(meters_per_second):
        """
        Converts meters per second to miles per hour.
        """
        return meters_per_second * 3.6

    def wind(self) -> str:
        """
        Returns the wind speed and direction.
        """
        speed = self.mps_to_kph(self.wind_speed)
        direction = self.degrees_to_cardinal(self.wind_direction)
        gusts = self.mps_to_kph(self.wind_gust)
        return f"Wind {speed:.1f}km/h from {direction}, gusting up to {gusts:.1f}km/h"

    class Emojis(StrEnum):
        CLEAR_SKY = "\U0001f323"
        FEW_CLOUDS = "\U0001f324"
        SCATTERED_CLOUDS = "\U0001f325"
        BROKEN_CLOUDS = "\U00002601"
        SHOWER_RAIN = "\U0001f326"
        RAIN = "\U0001f327"
        THUNDERSTORM = "\U0001f329"
        SNOW = "\U0001f328"
        MIST = "\U0001f32b"

    def emoji(self) -> str:  # noqa: PLR0911
        """
        Returns an emoji representation of the weather status.
        """
        weather_id = int(self.other_data.get("weather_icon_name", "0")[:2])

        match weather_id:
            case 1:
                return self.Emojis.CLEAR_SKY
            case 2:
                return self.Emojis.FEW_CLOUDS
            case 3:
                return self.Emojis.SCATTERED_CLOUDS
            case 4:
                return self.Emojis.BROKEN_CLOUDS
            case 9:
                return self.Emojis.SHOWER_RAIN
            case 10:
                return self.Emojis.RAIN
            case 11:
                return self.Emojis.THUNDERSTORM
            case 13:
                return self.Emojis.SNOW
            case 50:
                return self.Emojis.MIST
            case _:
                return ""

    @classmethod
    def from_lat_long(cls, latitude: float, longitude: float) -> Self:
        """
        Fetches the weather data for the given latitude and longitude.
        """
        owm = pyowm.OWM(settings.OWM_API_KEY).weather_manager()
        observation = owm.weather_at_coords(latitude, longitude)
        if not observation:
            raise ValueError(f"No weather data found for coordinates: {latitude}, {longitude}")
        weather: PyOWMWeather = observation.weather

        weather_instance = cls.objects.create(
            latitude=latitude,
            longitude=longitude,
            timestamp=weather.reference_time("iso"),
            status=weather.status,
            detailed_status=weather.detailed_status.capitalize(),
            temperature=weather.temperature("celsius")["temp"],
            temperature_feels_like=weather.temperature("celsius")["feels_like"],
            humidity=weather.humidity,
            wind_speed=weather.wnd.get("speed", 0.0),
            wind_direction=weather.wnd.get("deg", 0.0),
            wind_gust=weather.wnd.get("gust", 0.0),
            other_data=weather.to_dict(),
        )

        return weather_instance
