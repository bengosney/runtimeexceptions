import logging
from collections.abc import Callable, Iterable
from http import HTTPStatus
from typing import Any

import requests
from pydantic import ValidationError

from strava.data_models import SummaryAthlete, UpdatableActivity
from strava.data_models.triathlon import DetailedActivityTriathlon, SummaryActivityTriathlon
from strava.exceptions import StravaError, StravaNotAuthenticatedError, StravaNotFoundError, StravaPaidFeatureError

logger = logging.getLogger(__name__)

API_ROOT = "https://www.strava.com/api/v3"
TIMEOUT = 30


def api_url(path: str) -> str:
    return f"{API_ROOT}/{path}"


def _headers(token: str | None) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Cache-Control": "no-cache",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    if token is not None:
        headers["Authorization"] = f"Bearer {token}"

    return headers


def api_request(
    path: str,
    data: dict[str, Any] | None = None,
    method: str = "GET",
    token: str | None = None,
) -> Any:
    """
    A single call to the Strava API, decoded from JSON.

    Anything other than a 200 becomes one of the StravaError subclasses, so
    callers never have to look at status codes.
    """
    url = api_url(path)

    response = requests.request(method, url, headers=_headers(token), data=data or {}, timeout=TIMEOUT)

    if response.status_code == HTTPStatus.OK:
        return response.json()

    if response.status_code == HTTPStatus.UNAUTHORIZED:
        raise StravaNotAuthenticatedError()

    if response.status_code == HTTPStatus.PAYMENT_REQUIRED:
        raise StravaPaidFeatureError()

    if response.status_code == HTTPStatus.NOT_FOUND:
        raise StravaNotFoundError(url)

    raise StravaError(f"Got {response.status_code} from strava, {response.text}")


class StravaClient:
    """
    The Strava API as seen by one authenticated athlete.

    The access token is fetched per call rather than held, so a token that
    expires mid-session is refreshed by whoever supplied it.

    Failures surface as StravaError subclasses, and payloads that do not fit
    the data models as a pydantic ValidationError. Turning either into an HTTP
    response is the caller's job.
    """

    def __init__(self, token: Callable[[], str]):
        self._token = token

    def request(self, path: str, data: dict[str, Any] | None = None, method: str = "GET") -> Any:
        return api_request(path, data, method, self._token())

    def athlete(self) -> SummaryAthlete:
        return SummaryAthlete.model_validate(self.request("athlete"))

    def activities(self) -> Iterable[SummaryActivityTriathlon]:
        """
        The athlete's recent activities, skipping any we cannot read.

        One unreadable activity should not cost the caller the whole list.
        """
        for activity in self.request("athlete/activities"):
            try:
                yield SummaryActivityTriathlon.model_validate(activity)
            except ValidationError:
                logger.exception("Model %s failed to validate with data %s", SummaryActivityTriathlon, activity)

    def activity(self, activity_id: int) -> DetailedActivityTriathlon:
        return DetailedActivityTriathlon.model_validate(self.request(f"activities/{activity_id}"))

    def update_activity(self, activity_id: int, data: UpdatableActivity) -> DetailedActivityTriathlon:
        result = self.request(f"activities/{activity_id}", data.model_dump(), method="PUT")
        return DetailedActivityTriathlon.model_validate(result)
