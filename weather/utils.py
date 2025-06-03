from django.conf import settings

import pyowm


def get_weather(lat: float, long: float) -> str:
    owm = pyowm.OWM(settings.OWM_API_KEY).weather_manager()
    observation = owm.weather_at_coords(lat, long)
    weather = observation.weather  # type: ignore
    temperature = weather.temperature("celsius")

    return f"{weather.detailed_status.capitalize()} - {temperature['feels_like']}°C"
