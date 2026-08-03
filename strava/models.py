import time
from typing import ClassVar, Literal, cast

from django.contrib.auth.models import User
from django.db import models

from strava.auth import StravaOAuth
from strava.client import StravaClient
from strava.data_models import DetailedActivity, UpdatableActivity
from strava.utils import MarkedString
from weather.models import Weather


class Runner(models.Model):
    strava_id = models.CharField(max_length=200, unique=True)  # TODO: should be an int
    access_token = models.CharField(max_length=512)
    access_expires = models.CharField(max_length=512)  # TODO: should be an int
    refresh_token = models.CharField(max_length=512)
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.strava_id

    @property
    def client(self) -> StravaClient:
        """
        The Strava API for this runner, refreshing the access token as needed.
        """
        return StravaClient(lambda: self.auth_code)

    def do_refresh_token(self) -> None:
        tokens = StravaOAuth().refresh(self.refresh_token)

        self.access_token = tokens.access_token
        self.access_expires = tokens.expires_at
        self.refresh_token = tokens.refresh_token
        self.save()

    @property
    def auth_code(self) -> str:
        if int(self.access_expires) < time.time():
            self.do_refresh_token()

        return self.access_token

    @property
    def enrichment(self) -> "RunnerSettings":
        """
        The runner's enrichment toggles, created with defaults on first access.
        """
        settings, _ = RunnerSettings.objects.get_or_create(runner=self)
        return settings


class RunnerSettings(models.Model):
    """
    Which lines RuntimeExceptions writes back to Strava for this runner.

    Each field maps to exactly one marked segment of the activity name or
    description, so turning one off removes that segment on the next run
    without disturbing the others.
    """

    runner = models.OneToOneField(Runner, on_delete=models.CASCADE, related_name="enrichment_settings")

    weather_report = models.BooleanField(default=True)
    weather_emoji = models.BooleanField(default=True)
    triathlon_score = models.BooleanField(default=True)
    animal_comparison = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "runner settings"

    def __str__(self):
        return f"Settings for {self.runner}"


class Activity(models.Model):
    MARKER_STRING = "\ufe00\ufe01"

    runner = models.ForeignKey(Runner, on_delete=models.CASCADE, related_name="activities", to_field="strava_id")
    strava_id = models.BigIntegerField(unique=True)
    type = models.CharField(max_length=50)
    weather = models.ForeignKey(Weather, on_delete=models.CASCADE, related_name="activities", null=True, blank=True)

    def __str__(self):
        return f"{self.strava_id} {self.type}"

    def add_weather(self) -> DetailedActivity | Literal[False]:
        """
        Updates the activity description on Strava.

        The report and the title emoji are controlled independently, and a
        disabled one is stripped rather than left behind from an earlier run.
        """
        if not self.weather:
            return False

        runner = cast(Runner, self.runner)
        settings = runner.enrichment

        data_in: DetailedActivity = runner.client.activity(self.strava_id)

        original_description = data_in.description or ""
        weather = MarkedString(self.weather.long(), self.MARKER_STRING)
        description = (
            weather.replace_or_append(original_description)
            if settings.weather_report
            else weather.remove_from_text(original_description)
        )

        original_name = data_in.name or ""
        emoji = MarkedString(self.weather.emoji(), self.MARKER_STRING)
        name = (
            emoji.replace_or_append(original_name) if settings.weather_emoji else emoji.remove_from_text(original_name)
        )

        if description == original_description and name == original_name:
            return False

        data = UpdatableActivity.model_validate(
            {
                "description": description,
                "name": name,
            }
        )

        return runner.client.update_activity(self.strava_id, data)


class Event(models.Model):
    ASPECT_TYPES: ClassVar[dict[str, str]] = {
        "create": "create",
        "update": "update",
        "delete": "delete",
    }

    OBJECT_TYPES: ClassVar[dict[str, str]] = {
        "activity": "activity",
        "athlete": "athlete",
    }

    aspect_type = models.CharField(max_length=128, choices=ASPECT_TYPES)
    event_time = models.DateTimeField()
    object_id = models.BigIntegerField()
    object_type = models.CharField(max_length=128, choices=OBJECT_TYPES)
    owner = models.ForeignKey["Runner"](Runner, on_delete=models.CASCADE, related_name="updates", to_field="strava_id")
    subscription_id = models.BigIntegerField()
    updates = models.JSONField(default=dict)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.aspect_type} {self.object_type} {self.object_id}"


class Animal(models.Model):
    name = models.CharField(max_length=100, unique=True)
    avg_speed = models.FloatField()
    max_speed = models.FloatField()

    def __str__(self):
        return f"{self.name} - {self.avg_speed}"
