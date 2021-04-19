# Standard Library
import time
from pprint import pprint

# Third Party
import requests

# First Party
from strava.models import Token
from websettings.models import setting


class api:
    basePath = "https://www.strava.com/api/v3/"

    @staticmethod
    def _getHeaders():
        return {
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    @classmethod
    def _getAccessToken(cls):
        access = Token.getValue("access")
        print("----------- getting token -----------")

        if access is None:
            refresh = Token.getValue("refresh")
            data = {
                "client_id": setting.getValue("client_id"),
                "client_secret": setting.getValue("client_secret"),
                "grant_type": "refresh_token",
                "refresh_token": refresh,
            }

            headers = cls._getHeaders()

            url = "https://www.strava.com/api/v3/oauth/token"
            response = requests.request("POST", url, headers=headers, data=data)
            response_data = response.json()
            pprint(response_data)
            access = response_data["access_token"]
            Token.setToken("access", access, response_data["expires_at"])
            Token.setToken("refresh", response_data["refresh_token"], time.time() + (86400 * 365))

        return access

    @classmethod
    def req(cls, path):
        url = f"{cls.basePath}{path}"

        token = cls._getAccessToken()
        headers = cls._getHeaders()
        headers["Authorization"] = f"Bearer {token}"

        response = requests.request("GET", url, headers=headers)

        return response.json()
