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
        return f"{self.status} at {self.temperature}°C"

    def long(self) -> str:
        """
        Returns a long string representation of the weather.
        """
        return f"{self.detailed_status}, {self.temperature}°C (feels like {self.temperature_feels_like}°C)"

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
