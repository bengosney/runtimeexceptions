from http import HTTPStatus
from urllib.parse import parse_qs

import pytest
from pydantic import ValidationError

from strava.client import StravaClient
from strava.data_models import UpdatableActivity
from strava.exceptions import (
    StravaError,
    StravaNotAuthenticatedError,
    StravaNotFoundError,
    StravaPaidFeatureError,
)
from strava.tests.strava_api import ACTIVITY_DISTANCE_M, ACTIVITY_ID, ATHLETE, activity, strava_url


@pytest.fixture
def client() -> StravaClient:
    return StravaClient(lambda: "token")


def test_calls_the_documented_url(client, strava_api):
    strava_api.get(strava_url("athlete"), json=ATHLETE)

    client.athlete()

    assert strava_api.calls[0].request.url == strava_url("athlete")


def test_sends_the_token_as_a_bearer_header(client, strava_api):
    strava_api.get(strava_url("athlete"), json=ATHLETE)

    client.athlete()

    assert strava_api.calls[0].request.headers["Authorization"] == "Bearer token"
    assert strava_api.calls[0].request.headers["Accept"] == "application/json"


def test_the_token_is_read_once_per_call(strava_api):
    tokens = iter(["first", "second"])
    client = StravaClient(lambda: next(tokens))
    strava_api.get(strava_url("athlete"), json=ATHLETE)

    client.athlete()
    client.athlete()

    sent = [call.request.headers["Authorization"] for call in strava_api.calls]
    assert sent == ["Bearer first", "Bearer second"]


@pytest.mark.parametrize(
    "status_code, exception_type",
    [
        (HTTPStatus.UNAUTHORIZED, StravaNotAuthenticatedError),
        (HTTPStatus.PAYMENT_REQUIRED, StravaPaidFeatureError),
        (HTTPStatus.NOT_FOUND, StravaNotFoundError),
        (HTTPStatus.INTERNAL_SERVER_ERROR, StravaError),
    ],
)
def test_errors(client, strava_api, status_code, exception_type):
    strava_api.get(strava_url("athlete"), status=status_code)

    with pytest.raises(exception_type):
        client.athlete()


def test_athlete(client, strava_api):
    strava_api.get(strava_url("athlete"), json=ATHLETE)

    athlete = client.athlete()

    assert athlete.id == ATHLETE["id"]
    assert athlete.firstname == ATHLETE["firstname"]
    assert athlete.city == ATHLETE["city"]


def test_athlete_unreadable(client, strava_api):
    strava_api.get(strava_url("athlete"), json={"id": "not an id"})

    with pytest.raises(ValidationError):
        client.athlete()


def test_activities(client, strava_api):
    strava_api.get(strava_url("athlete/activities"), json=[activity(), activity(id=102, name="Evening Ride")])

    activities = list(client.activities())

    assert [a.name for a in activities] == ["Morning Run", "Evening Ride"]
    assert activities[0].distance == ACTIVITY_DISTANCE_M
    assert activities[0].triathlon_percentage() == pytest.approx(50.0)


def test_activities_skips_the_unreadable(client, strava_api):
    strava_api.get(strava_url("athlete/activities"), json=[activity(distance="not a distance"), activity(id=102)])

    activities = list(client.activities())

    assert [a.id for a in activities] == [102]


def test_activity(client, strava_api):
    strava_api.get(strava_url("activities/101"), json=activity(description="A good one"))

    detail = client.activity(101)

    assert detail.id == ACTIVITY_ID
    assert detail.description == "A good one"
    assert detail.end_date is not None


def test_activity_unreadable(client, strava_api):
    strava_api.get(strava_url("activities/101"), json=activity(distance="not a distance"))

    with pytest.raises(ValidationError):
        client.activity(101)


def test_update_activity(client, strava_api):
    strava_api.put(strava_url("activities/101"), json=activity(name="Renamed", description="Rewritten"))

    updated = client.update_activity(101, UpdatableActivity(name="Renamed", description="Rewritten"))

    assert updated.name == "Renamed"
    request = strava_api.calls[0].request
    assert request.method == "PUT"
    assert parse_qs(request.body) == {"description": ["Rewritten"], "name": ["Renamed"]}


def test_update_activity_sends_only_what_was_set(client, strava_api):
    strava_api.put(strava_url("activities/101"), json=activity(name="Renamed"))

    client.update_activity(101, UpdatableActivity(name="Renamed"))

    assert parse_qs(strava_api.calls[0].request.body) == {"name": ["Renamed"]}


def test_empty_latlng_is_cleaned_away(client, strava_api):
    strava_api.get(strava_url("activities/101"), json=activity(start_latlng=[], end_latlng=[]))

    detail = client.activity(101)

    assert detail.start_latlng is None
    assert detail.end_latlng is None
