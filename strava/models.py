# Standard Library
import time
from math import atan2, cos, radians, sin, sqrt
from pprint import pprint

# Django
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

# Third Party
import requests

# First Party
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

        redirect_uri = request.build_absolute_uri(reverse('auth_callback'))
        params = {'client_id': setting.getValue('client_id'),
                  'redirect_uri': redirect_uri, 'response_type': 'code',
                  'approval_prompt': 'auto', 'scope':
                      'activity:write,activity:read_all,read,profile:write,read_all', }

        p = requests.Request('GET', url, params=params).prepare()

        return p.url

    @classmethod
    def auth_call_back(cls, code):
        url = "https://www.strava.com/api/v3/oauth/token"
        data = {
            'client_id': setting.getValue('client_id'),
            'client_secret': setting.getValue('client_secret'),
            'code': code,
            'grant_type': 'authorization_code',
        }

        headers = {
            'Accept': "application/json",
            'Cache-Control': "no-cache",
            'Accept-Encoding': "gzip, deflate",
            'Connection': "keep-alive",
        }

        response = requests.request("POST", url, headers=headers, data=data)

        data = response.json()

        if response.status_code != 200:
            pprint(response)
            return None

        expires = data['expires_at']  # make_aware(datetime.fromtimestamp(data['expires_at']))

        cls.objects.update_or_create(
            stravaID=data['athlete']['id'],
            defaults={
                'stravaID': data['athlete']['id'],
                'access_token': data['access_token'],
                'access_expires': expires,
                'refresh_token': data['refresh_token'],
            }
        )

        user, _ = User.objects.update_or_create(
            username=data['athlete']['username'],
            defaults={
                'username': data['athlete']['username'],
                'first_name': data['athlete']['firstname'],
                'last_name': data['athlete']['lastname'],
            }
        )
        user.set_unusable_password()
        user.save()

        return user

    def do_refresh_token(self):
        print("Refreshing token")
        url = 'https://www.strava.com/api/v3/oauth/token'
        data = {
            'client_id': setting.getValue('client_id'),
            'client_secret': setting.getValue('client_secret'),
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token',
        }

        headers = {
            'Accept': "application/json",
            'Cache-Control': "no-cache",
            'Accept-Encoding': "gzip, deflate",
            'Connection': "keep-alive",
        }

        response = requests.request("POST", url, headers=headers, data=data)

        data = response.json()

        if response.status_code != 200:
            return False

        self.access_token = data['access_token']
        self.access_expires = data['expires_at']  # str(datetime.fromtimestamp(data['expires_at']))
        self.refresh_token = data['refresh_token']
        self.save()

    @property
    def auth_code(self):
        if int(self.access_expires) < time.time():  # timezone.now():
            self.do_refresh_token()

        return self.access_token

    @classmethod
    def get_authenticated_athlete(cls):
        pass

    # @lru_cache(512)
    def make_call(self, path, args={}):
        url = f'https://www.strava.com/api/v3/{path}'

        headers = {
            'Accept': "application/json",
            'Cache-Control': "no-cache",
            'Accept-Encoding': "gzip, deflate",
            'Connection': "keep-alive",
            'Authorization': f"Bearer {self.auth_code}"
        }

        data = requests.get(url, headers=headers)

        if data.status_code == 200:
            return data.json()

        return None

    def get_details(self):
        return self.make_call('athlete')

    def get_activities(self):
        return self.make_call('athlete/activities')

    def activity(self, activityID):
        return self.make_call(f'activities/{activityID}') | []

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
