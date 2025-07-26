import logging
import time
from collections.abc import Iterable
from http import HTTPStatus
from math import atan2, cos, radians, sin, sqrt
from typing import Any, ClassVar, TypeVar

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.http import Http404
from django.urls import reverse

import requests
from pydantic import BaseModel, ValidationError

from strava.data_models import DetailedActivity, SummaryActivity, SummaryAthlete
from strava.exceptions import StravaError, StravaNotAuthenticatedError, StravaNotFoundError, StravaPaidFeatureError
from weather.models import Weather

logger = logging.getLogger(__name__)

Point = tuple[float, float]

T = TypeVar("T", bound=BaseModel)


class Runner(models.Model):
    strava_id = models.CharField(max_length=200, unique=True)
    access_token = models.CharField(max_length=512)
    access_expires = models.CharField(max_length=512)
    refresh_token = models.CharField(max_length=512)
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.strava_id

    @staticmethod
    def get_auth_url(request):
        url = "https://www.strava.com/api/v3/oauth/authorize"

        redirect_uri = request.build_absolute_uri(reverse("strava:auth_callback"))
        params = {
            "client_id": settings.STRAVA_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "approval_prompt": "auto",
            "scope": "activity:write,activity:read_all,read,profile:write,read_all",
        }

        p = requests.Request("GET", url, params=params).prepare()

        return p.url

    @classmethod
    def auth_call_back(cls, code):
        data = {
            "client_id": settings.STRAVA_CLIENT_ID,
            "client_secret": settings.STRAVA_SECRET,
            "code": code,
            "grant_type": "authorization_code",
        }

        data = cls._make_call("oauth/token", data, method="POST")

        expires = data["expires_at"]

        user, _ = User.objects.update_or_create(
            username=data["athlete"]["username"],
            defaults={
                "username": data["athlete"]["username"],
                "first_name": data["athlete"]["firstname"],
                "last_name": data["athlete"]["lastname"],
            },
        )
        user.set_unusable_password()
        user.save()

        cls.objects.update_or_create(
            strava_id=data["athlete"]["id"],
            defaults={
                "strava_id": data["athlete"]["id"],
                "access_token": data["access_token"],
                "access_expires": expires,
                "refresh_token": data["refresh_token"],
                "user": user,
            },
        )

        return user

    def do_refresh_token(self):
        print("Refreshing token")
        data = {
            "client_id": settings.STRAVA_CLIENT_ID,
            "client_secret": settings.STRAVA_SECRET,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }

        data = self._make_call("oauth/token", data, method="POST")

        self.access_token = data["access_token"]
        self.access_expires = data["expires_at"]
        self.refresh_token = data["refresh_token"]
        self.save()

    @property
    def auth_code(self):
        if int(self.access_expires) < time.time():
            self.do_refresh_token()

        return self.access_token

    @classmethod
    def get_authenticated_athlete(cls):
        pass

    def make_call(
        self,
        path: str,
        args: dict[str, Any] = {},
        method: str = "GET",
    ) -> dict[str, Any]:
        return self._make_call(path, args, method, self.auth_code)

    @staticmethod
    def _make_call(
        path: str,
        args: dict[str, Any] = {},
        method: str = "GET",
        authentication: str | None = None,
    ) -> dict[str, Any]:
        url = f"https://www.strava.com/api/v3/{path}"

        headers = {
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

        if authentication is not None:
            headers["Authorization"] = f"Bearer {authentication}"

        data = requests.request(method, url, headers=headers, data=args)

        if data.status_code == HTTPStatus.OK:
            return data.json()

        if data.status_code == HTTPStatus.UNAUTHORIZED:
            raise StravaNotAuthenticatedError()

        if data.status_code == HTTPStatus.PAYMENT_REQUIRED:
            raise StravaPaidFeatureError()

        if data.status_code == HTTPStatus.NOT_FOUND:
            raise StravaNotFoundError(url)

        raise StravaError(f"Got {data.status_code} from strava")

    def get_details(self) -> SummaryAthlete:
        try:
            return SummaryAthlete.model_validate(self.make_call("athlete"))
        except ValidationError:
            raise Http404("Strava athlete not found or invalid data")

    def get_activities(self) -> Iterable[SummaryActivity]:
        for activity in self.make_call("athlete/activities"):
            try:
                yield SummaryActivity.model_validate(activity)
            except ValidationError:
                pass

    def activity(self, activity_id: int) -> DetailedActivity:
        try:
            return DetailedActivity.model_validate(self.make_call(f"activities/{activity_id}"))
        except ValidationError as e:
            raise Http404("Strava activity not found or invalid data") from e

    def update_activity(self, activity_id, data):
        """
        Updates an activity with the given data.
        """
        return self.make_call(f"activities/{activity_id}", data, method="PUT")

    def distance_from(self):
        pass

    @staticmethod
    def get_distance(point1: Point, point2: Point) -> float:
        r = 6373.0

        lat1, lon1 = map(radians, point1)
        lat2, lon2 = map(radians, point2)

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return r * c


class Activity(models.Model):
    runner = models.ForeignKey(Runner, on_delete=models.CASCADE, related_name="activities", to_field="strava_id")
    strava_id = models.BigIntegerField(unique=True)
    type = models.CharField(max_length=50)
    weather = models.ForeignKey(Weather, on_delete=models.CASCADE, related_name="activities", null=True, blank=True)

    def __str__(self):
        return f"{self.strava_id} {self.type}"

    @classmethod
    def find_or_create(cls, runner: Runner, activity_id: int):
        """
        Finds an activity by ID or fetches it from Strava if not found.
        """
        logger.info("Looking for Activity, strava_id=%d, runner=%s", activity_id, runner)
        try:
            activity = cls.objects.get(strava_id=activity_id, runner=runner)
            logger.info("Found existing Activity: %d", activity.pk)
        except cls.DoesNotExist:
            logger.info("Activity not found, fetching from Strava API, strava_id=%d", activity_id)
            activity_data = runner.activity(activity_id)

            weather: Weather | None = None
            if activity_data.end_latlng:
                logger.debug("activity_data: %s", activity_data)
                lat: float = activity_data.end_latlng.root[0]
                lng: float = activity_data.end_latlng.root[1]
                logger.info("Fetching weather for lat=%f, lng=%f", lat, lng)
                weather = Weather.from_lat_long(lat, lng)

            activity = cls.objects.create(
                strava_id=activity_data.id,
                type=activity_data.type.value if activity_data.type is not None else "",
                runner=runner,
                weather=weather,
            )
            logger.info("Created new Activity: %d", activity.pk)
        return activity

    def add_weather(self):
        """
        Updates the activity description on Strava.
        """
        if not self.weather:
            return False

        data_in: DetailedActivity = self.runner.activity(self.strava_id)

        description = data_in.description or ""
        weather = self.weather.long()
        description = description.replace(weather, "").strip()

        name = data_in.name or ""
        emoji = self.weather.emoji()
        name = name.replace(emoji, "").strip()

        data = {
            "description": "\n\n".join(s for s in [description, weather] if s != ""),
            "name": f"{name} {emoji}",
        }

        response = self.runner.update_activity(self.strava_id, data)
        return response


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
    owner_id = models.ForeignKey(Runner, on_delete=models.CASCADE, related_name="updates", to_field="strava_id")
    subscription_id = models.BigIntegerField()
    updates = models.JSONField(default=dict)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.aspect_type} {self.object_type} {self.object_id}"
