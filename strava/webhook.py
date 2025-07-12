from http import HTTPStatus

from django.conf import settings
from django.urls import reverse

import requests

from strava.exceptions import StravaWebhookError


class WebhookManager:
    def _get_url(self) -> str:
        try:
            with open(f"{settings.BASE_DIR}/.ngrok") as f:
                return f.read().strip()
        except FileNotFoundError:
            return f"https://{settings.DOMAIN}"

    def _get_full_url(self) -> str:
        path = reverse("strava:webhook")
        return f"{self._get_url()}{path}"

    def create_subscription(self):
        """
        Create a Strava subscription for webhooks.
        """
        url = "https://www.strava.com/api/v3/push_subscriptions"
        data = {
            "client_id": settings.STRAVA_CLIENT_ID,
            "client_secret": settings.STRAVA_SECRET,
            "callback_url": self._get_full_url(),
            "verify_token": "STRAVA",
        }

        print(f"Creating Strava subscription with callback URL: {data['callback_url']}")

        response = requests.post(url, data=data)
        if response.status_code != HTTPStatus.CREATED:
            raise StravaWebhookError(response.text)

        return response.json()

    def list_subscriptions(self):
        """
        List all Strava subscriptions.
        """
        url = "https://www.strava.com/api/v3/push_subscriptions"
        params = {
            "client_id": settings.STRAVA_CLIENT_ID,
            "client_secret": settings.STRAVA_SECRET,
        }

        response = requests.get(url, params=params)
        if response.status_code != HTTPStatus.OK:
            raise StravaWebhookError(response.text)

        return response.json()

    def delete_subscription(self, subscription_id: int):
        """
        Delete a Strava subscription by ID.
        """
        url = f"https://www.strava.com/api/v3/push_subscriptions/{subscription_id}"
        params = {
            "client_id": settings.STRAVA_CLIENT_ID,
            "client_secret": settings.STRAVA_SECRET,
        }

        response = requests.delete(url, params=params)
        if response.status_code != HTTPStatus.NO_CONTENT:
            raise StravaWebhookError(response.text)
