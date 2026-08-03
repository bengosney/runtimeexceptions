from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from strava.client import TIMEOUT, StravaClient, api_request, api_url
from strava.data_models import SummaryAthlete, UpdatableActivity
from strava.data_models.triathlon import DetailedActivityTriathlon, SummaryActivityTriathlon
from strava.exceptions import (
    StravaError,
    StravaNotAuthenticatedError,
    StravaNotFoundError,
    StravaPaidFeatureError,
)


@pytest.fixture
def client() -> StravaClient:
    return StravaClient(lambda: "token")


def invalid_data() -> ValidationError:
    return ValidationError.from_exception_data(title="Invalid data", line_errors=[])


def test_api_url():
    assert api_url("athlete") == "https://www.strava.com/api/v3/athlete"


def test_api_request(mock_strava_request):
    mock_strava_request.return_value = MagicMock()
    mock_strava_request.return_value.json.return_value = {"key": "value"}
    mock_strava_request.return_value.status_code = HTTPStatus.OK

    assert api_request("test") == {"key": "value"}


def test_api_request_without_a_token_is_unauthenticated(mock_strava_request):
    mock_strava_request.return_value.status_code = HTTPStatus.OK

    api_request("test")

    assert "Authorization" not in mock_strava_request.call_args.kwargs["headers"]


def test_api_request_authorized(mock_strava_request):
    mock_strava_request.return_value.status_code = HTTPStatus.OK

    api_request("test", token="token")

    mock_strava_request.assert_called_once_with(
        "GET",
        api_url("test"),
        headers={
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Authorization": "Bearer token",
        },
        data={},
        timeout=TIMEOUT,
    )


@pytest.mark.parametrize(
    "status_code, exception_type",
    [
        (HTTPStatus.UNAUTHORIZED, StravaNotAuthenticatedError),
        (HTTPStatus.PAYMENT_REQUIRED, StravaPaidFeatureError),
        (HTTPStatus.NOT_FOUND, StravaNotFoundError),
        (HTTPStatus.INTERNAL_SERVER_ERROR, StravaError),
    ],
)
def test_api_request_errors(mock_strava_request, status_code, exception_type):
    mock_strava_request.return_value.status_code = status_code

    with pytest.raises(exception_type):
        api_request("test")


def test_request_sends_the_current_token(client, mock_strava_request):
    mock_strava_request.return_value.status_code = HTTPStatus.OK

    client.request("test")

    assert mock_strava_request.call_args.kwargs["headers"]["Authorization"] == "Bearer token"


def test_token_is_fetched_per_call(mock_strava_request):
    mock_strava_request.return_value.status_code = HTTPStatus.OK
    tokens = iter(["first", "second"])
    client = StravaClient(lambda: next(tokens))

    client.request("test")
    client.request("test")

    sent = [call.kwargs["headers"]["Authorization"] for call in mock_strava_request.call_args_list]
    assert sent == ["Bearer first", "Bearer second"]


def test_athlete(client, mock_strava_request):
    data = {"key": "value"}
    mock_strava_request.return_value.json.return_value = data
    mock_strava_request.return_value.status_code = HTTPStatus.OK

    assert client.athlete() == SummaryAthlete.model_validate(data)


def test_athlete_not_found(client, mock_strava_request):
    mock_strava_request.return_value.status_code = HTTPStatus.NOT_FOUND

    with pytest.raises(StravaNotFoundError):
        client.athlete()


def test_athlete_invalid(client, mock_strava_request):
    mock_strava_request.return_value.json.return_value = {"key": "value"}
    mock_strava_request.return_value.status_code = HTTPStatus.OK

    with (
        patch("strava.client.SummaryAthlete.model_validate", side_effect=invalid_data()),
        pytest.raises(ValidationError),
    ):
        client.athlete()


def test_activities(client, mock_strava_request):
    data = [{"key": "value"}]
    mock_strava_request.return_value.json.return_value = data
    mock_strava_request.return_value.status_code = HTTPStatus.OK

    assert list(client.activities()) == [SummaryActivityTriathlon.model_validate(item) for item in data]


def test_activities_skips_the_unreadable(client, mock_strava_request):
    mock_strava_request.return_value.json.return_value = [{"key": "value"}]
    mock_strava_request.return_value.status_code = HTTPStatus.OK

    with patch("strava.client.SummaryActivityTriathlon.model_validate", side_effect=invalid_data()):
        assert list(client.activities()) == []


def test_activity(client, mock_strava_request):
    data = {"name": "Test Activity"}
    mock_strava_request.return_value.json.return_value = data
    mock_strava_request.return_value.status_code = HTTPStatus.OK

    activity = client.activity(1)

    assert activity == DetailedActivityTriathlon.model_validate(data)
    assert activity.name == data["name"]


def test_activity_invalid(client, mock_strava_request):
    mock_strava_request.return_value.json.return_value = {"key": "value"}
    mock_strava_request.return_value.status_code = HTTPStatus.OK

    with (
        patch("strava.client.DetailedActivityTriathlon.model_validate", side_effect=invalid_data()),
        pytest.raises(ValidationError),
    ):
        client.activity(1)


def test_update_activity(client):
    activity_id = 1
    data = UpdatableActivity(name="New Activity")

    with patch.object(StravaClient, "request", return_value={"name": "New Activity"}) as mock_request:
        updated = client.update_activity(activity_id, data)

    mock_request.assert_called_once_with(
        f"activities/{activity_id}",
        data.model_dump(),
        method="PUT",
    )
    assert updated.name == "New Activity"
