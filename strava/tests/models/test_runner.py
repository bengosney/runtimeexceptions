from http import HTTPStatus
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.http import Http404
from django.test import RequestFactory

import pytest
from model_bakery import baker
from pydantic import ValidationError

from strava.data_models import DetailedActivity, SummaryActivity, SummaryAthlete
from strava.exceptions import (
    StravaError,
    StravaNotAuthenticatedError,
    StravaNotFoundError,
    StravaPaidFeatureError,
)
from strava.models import Runner


@pytest.mark.django_db
def test_runner_str_method():
    strava_id = "12345"
    runner = baker.make(Runner, strava_id=strava_id)
    assert str(runner) == strava_id


@patch("strava.models.requests.Request")
def test_get_auth_url(requests_mock):
    factory = RequestFactory()
    request = factory.get("/")
    mock_prepared = MagicMock()
    mock_prepared.url = "http://auth.url"
    requests_mock.return_value.prepare.return_value = mock_prepared
    url = Runner.get_auth_url(request)
    assert url == mock_prepared.url


@pytest.mark.django_db
@patch("strava.models.Runner._make_call")
def test_auth_call_back_new_user(mock_make_call):
    athlete = {"id": "stravaid", "username": "testuser", "firstname": "Test", "lastname": "User"}
    mock_make_call.return_value = {
        "expires_at": 1234567890,
        "athlete": athlete,
        "access_token": "token",
        "refresh_token": "refresh",
    }

    user = Runner.auth_call_back("code")
    assert user.username == athlete["username"]
    assert user.first_name == athlete["firstname"]
    assert user.last_name == athlete["lastname"]

    runner = Runner.objects.get(strava_id="stravaid")
    assert getattr(runner, "user", None) == user


@pytest.mark.django_db
@patch("strava.models.Runner._make_call")
def test_auth_call_back_existing_user(mock_make_call):
    athlete = {"id": "stravaid", "username": "testuser", "firstname": "Test", "lastname": "User"}
    mock_make_call.return_value = {
        "expires_at": 1234567890,
        "athlete": athlete,
        "access_token": "token",
        "refresh_token": "refresh",
    }

    existing_user = baker.make(
        User,
        username=athlete["username"],
        first_name="old",
        last_name="name",
    )
    user = Runner.auth_call_back("code")
    assert user.pk == existing_user.pk
    assert user.username == athlete["username"]
    assert user.first_name == athlete["firstname"]
    assert user.last_name == athlete["lastname"]

    runner = Runner.objects.get(strava_id="stravaid")
    assert getattr(runner, "user", None) == user


@pytest.mark.django_db
def test_make_call_calls__make_call():
    runner = baker.make(Runner, access_expires="9999999999")
    from unittest.mock import patch

    with patch.object(Runner, "_make_call", return_value={"result": "ok"}) as mock_make_call:
        result = runner.make_call("some/path", {"foo": "bar"}, method="POST")
        mock_make_call.assert_called_once_with("some/path", {"foo": "bar"}, "POST", runner.auth_code)
        assert result == {"result": "ok"}


@pytest.mark.django_db
@patch("strava.models.Runner._make_call")
def test_do_refresh_token(mock_make_call, settings):
    mock_make_call.return_value = {
        "access_token": "newtoken",
        "expires_at": 1234567890,
        "refresh_token": "newrefresh",
    }
    runner: Runner = baker.make(
        Runner,
        strava_id="12345",
        access_token="token",
        access_expires="0",
        refresh_token="refresh",
    )
    runner.do_refresh_token()
    mock_make_call.assert_called_once_with(
        "oauth/token",
        {
            "client_id": settings.STRAVA_CLIENT_ID,
            "client_secret": settings.STRAVA_SECRET,
            "refresh_token": "refresh",
            "grant_type": "refresh_token",
        },
        method="POST",
    )

    assert runner.access_token == mock_make_call.return_value["access_token"]
    assert runner.access_expires == mock_make_call.return_value["expires_at"]
    assert runner.refresh_token == mock_make_call.return_value["refresh_token"]


@pytest.mark.django_db
@patch.object(Runner, "do_refresh_token")
def test_auth_code_does_not_refresh_if_expired(mock_refresh):
    import time

    runner = baker.make(
        Runner,
        strava_id="12345",
        access_token="token",
        access_expires=str(int(time.time()) - 10000),
        refresh_token="refresh",
    )
    code = runner.auth_code
    assert code == "token"
    mock_refresh.assert_called_once()


@pytest.mark.django_db
@patch.object(Runner, "do_refresh_token")
def test_auth_code_does_not_refresh_if_not_expired(mock_refresh):
    import time

    runner = baker.make(
        Runner,
        strava_id="12345",
        access_token="token",
        access_expires=str(int(time.time()) + 10000),
        refresh_token="refresh",
    )
    code = runner.auth_code
    assert code == "token"
    mock_refresh.assert_not_called()


def test_strava_api_url():
    path = "athlete"
    expected_url = f"https://www.strava.com/api/v3/{path}"
    assert Runner._strava_api_url(path) == expected_url


def test__make_call(mock_strava_request):
    mock_strava_request.return_value = MagicMock()
    mock_strava_request.return_value.json.return_value = {"key": "value"}
    mock_strava_request.return_value.status_code = HTTPStatus.OK
    response = Runner._make_call("test")
    assert response == {"key": "value"}


def test__make_call_authorized(mock_strava_request):
    mock_strava_request.return_value = MagicMock()
    mock_strava_request.return_value.status_code = HTTPStatus.OK
    Runner._make_call("test", authentication="token")
    mock_strava_request.assert_called_once_with(
        "GET",
        Runner._strava_api_url("test"),
        headers={
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Authorization": "Bearer token",
        },
        data={},
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
def test__make_call_unauthorized(mock_strava_request, status_code, exception_type):
    mock_strava_request.return_value = MagicMock()
    mock_strava_request.return_value.json.return_value = {"key": "value"}
    mock_strava_request.return_value.status_code = status_code
    with pytest.raises(exception_type):
        Runner._make_call("test")


@pytest.mark.django_db
def test_get_details(mock_strava_request):
    data = {"key": "value"}
    mock_strava_request.return_value.json.return_value = data
    mock_strava_request.return_value.status_code = HTTPStatus.OK
    runner: Runner = baker.make(Runner, access_expires="9999999999")
    details = runner.get_details()
    assert details == SummaryAthlete.model_validate(data)


@pytest.mark.django_db
def test_get_details_not_found(mock_strava_request):
    mock_strava_request.return_value.status_code = HTTPStatus.NOT_FOUND
    runner: Runner = baker.make(Runner, access_expires="9999999999")
    with pytest.raises(StravaNotFoundError):
        runner.get_details()


@pytest.mark.django_db
def test_get_details_invalid(mock_strava_request):
    data = {"key": "value"}
    mock_strava_request.return_value.json.return_value = data
    mock_strava_request.return_value.status_code = HTTPStatus.OK
    runner: Runner = baker.make(Runner, access_expires="9999999999")
    with patch("strava.models.SummaryAthlete.model_validate") as mock_validate:
        mock_validate.side_effect = ValidationError.from_exception_data(title="Invalid data", line_errors=[])
        with pytest.raises(Http404):
            runner.get_details()


@pytest.mark.django_db
def test_get_activities(mock_strava_request):
    data = [{"key": "value"}]
    mock_strava_request.return_value.json.return_value = data
    mock_strava_request.return_value.status_code = HTTPStatus.OK
    runner: Runner = baker.make(Runner, access_expires="9999999999")
    activities = runner.get_activities()
    assert list(activities) == [SummaryActivity.model_validate(item) for item in data]


@pytest.mark.django_db
def test_get_activities_invalid(mock_strava_request):
    data = [{"key": "value"}]
    mock_strava_request.return_value.json.return_value = data
    mock_strava_request.return_value.status_code = HTTPStatus.OK
    runner: Runner = baker.make(Runner, access_expires="9999999999")
    with patch("strava.models.SummaryActivity.model_validate") as mock_validate:
        mock_validate.side_effect = ValidationError.from_exception_data(title="Invalid data", line_errors=[])
        assert list(runner.get_activities()) == []


@pytest.mark.django_db
def test_activity(mock_strava_request):
    data = {"key": "value"}
    mock_strava_request.return_value.json.return_value = data
    mock_strava_request.return_value.status_code = HTTPStatus.OK
    runner: Runner = baker.make(Runner, access_expires="9999999999")
    activity = runner.activity(1)
    assert activity == DetailedActivity.model_validate(data)


@pytest.mark.django_db
def test_activity_invalid(mock_strava_request):
    mock_strava_request.return_value.json.return_value = {"key": "value"}
    mock_strava_request.return_value.status_code = HTTPStatus.OK

    runner: Runner = baker.make(Runner, access_expires="9999999999")
    with patch("strava.models.DetailedActivity.model_validate") as mock_validate:
        mock_validate.side_effect = ValidationError.from_exception_data(title="Invalid data", line_errors=[])
        with pytest.raises(Http404):
            runner.activity(1)


@pytest.mark.django_db
@patch("strava.models.Runner.make_call")
def test_update_activity(mock_make_call):
    id = 1
    data = DetailedActivity(name="New Activity")
    mock_make_call.return_value = data
    runner: Runner = baker.make(Runner, access_expires="9999999999")
    runner.update_activity(id, data)
    mock_make_call.assert_called_once_with(
        f"activities/{id}",
        data.model_dump(),
        method="PUT",
    )


def test_get_distance_zero():
    point = (0.0, 0.0)
    assert Runner.get_distance(point, point) == pytest.approx(0.0)


def test_get_distance_known():
    point1 = (0.0, 0.0)
    point2 = (0.0, 1.0)
    expected_km = 6373.0 * 2 * 3.141592653589793 / 360
    assert Runner.get_distance(point1, point2) == pytest.approx(expected_km, rel=1e-3)


def test_get_distance_antipodal():
    point1 = (0.0, 0.0)
    point2 = (0.0, 180.0)
    expected_km = 6373.0 * 3.141592653589793
    assert Runner.get_distance(point1, point2) == pytest.approx(expected_km, rel=1e-3)
