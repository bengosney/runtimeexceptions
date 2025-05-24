from django.apps import AppConfig

import requests_cache


class StravaConfig(AppConfig):
    name = "strava"

    def ready(self) -> None:
        requests_cache.install_cache(cache_name=f"{self.name}_cache", backend="sqlite", expire_after=180)

        return super().ready()
