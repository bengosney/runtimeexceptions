# Standard Library
import time
from math import atan2, cos, radians, sin, sqrt

# Django
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

# Third Party
import requests

# First Party
from strava.exceptions import StravaGenericError, StravaNotAuthenticated, StravaPaidFeature
from websettings.models import setting


class Runner(models.Model):
    stravaID = models.CharField(max_length=200, unique=True)
    access_token = models.CharField(max_length=512)
    access_expires = models.CharField(max_length=512)
    refresh_token = models.CharField(max_length=512)
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.stravaID

    @staticmethod
    def get_auth_url(request):
        url = "https://www.strava.com/api/v3/oauth/authorize"

        redirect_uri = request.build_absolute_uri(reverse("auth_callback"))
        params = {
            "client_id": setting.getValue("client_id"),
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
            "client_id": setting.getValue("client_id"),
            "client_secret": setting.getValue("client_secret"),
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
            stravaID=data["athlete"]["id"],
            defaults={
                "stravaID": data["athlete"]["id"],
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
            "client_id": setting.getValue("client_id"),
            "client_secret": setting.getValue("client_secret"),
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
        if int(self.access_expires) < time.time():  # timezone.now():
            self.do_refresh_token()

        return self.access_token

    @classmethod
    def get_authenticated_athlete(cls):
        pass

    def make_call(self, path, args={}, method="GET"):
        return self._make_call(path, args, method, self.auth_code)

    @staticmethod
    def _make_call(path, args={}, method="GET", authentication=None):
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

        if data.status_code == 200:
            return data.json()

        if data.status_code == 401:
            raise StravaNotAuthenticated()

        if data.status_code == 402:
            raise StravaPaidFeature()

        if data.status_code == 404:
            raise StravaGenericError(f"404 - {url}")

        raise StravaGenericError(f"Got {data.status_code} from strava")

    def get_details(self):
        return self.make_call("athlete")

    def get_activities(self):
        return self.make_call("athlete/activities")

    def activity(self, activityID):
        return self.make_call(f"activities/{activityID}")

    def distance_from(self):
        pass

    @staticmethod
    def get_distance(point1, point2):
        R = 6373.0

        lat1 = radians(point1[0])
        lon1 = radians(point1[1])
        lat2 = radians(point2[0])
        lon2 = radians(point2[1])

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        R * c

        return None


class Renamer(models.Model):
    lat = models.FloatField()
    lng = models.FloatField()
    name = models.CharField(max_length=200)
    number = models.IntegerField()

    def __str__(self):
        return self.name
