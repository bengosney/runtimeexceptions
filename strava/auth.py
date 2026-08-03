from django.conf import settings

import requests
from pydantic import BaseModel

from strava.client import api_request, api_url


class StravaTokens(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: int


class AuthenticatedAthlete(BaseModel):
    id: int
    username: str
    firstname: str = ""
    lastname: str = ""


class StravaAuthorization(StravaTokens):
    athlete: AuthenticatedAthlete


class StravaOAuth:
    """
    The Strava OAuth handshake.

    Knows nothing about our users or runners; it deals only in codes and
    tokens, and leaves storing them to the caller.
    """

    SCOPES = "activity:write,activity:read_all,read,profile:write,read_all"

    def authorization_url(self, redirect_uri: str) -> str | None:
        params = {
            "client_id": settings.STRAVA_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "approval_prompt": "auto",
            "scope": self.SCOPES,
        }

        return requests.Request("GET", api_url("oauth/authorize"), params=params).prepare().url

    def exchange_code(self, code: str) -> StravaAuthorization:
        data = self._token_request(code=code, grant_type="authorization_code")
        return StravaAuthorization.model_validate(data)

    def refresh(self, refresh_token: str) -> StravaTokens:
        data = self._token_request(refresh_token=refresh_token, grant_type="refresh_token")
        return StravaTokens.model_validate(data)

    def _token_request(self, **data: str) -> dict:
        return api_request(
            "oauth/token",
            {
                "client_id": settings.STRAVA_CLIENT_ID,
                "client_secret": settings.STRAVA_SECRET,
                **data,
            },
            method="POST",
        )
