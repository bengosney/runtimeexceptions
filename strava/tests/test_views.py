import json
import urllib.parse
from http import HTTPStatus
from unittest.mock import MagicMock, patch

from django.http import Http404
from django.urls import reverse

import pytest
from model_bakery import baker
from pytest_django.asserts import assertInHTML

from strava.data_models import DetailedActivity, SummaryActivity, SummaryAthlete
from strava.models import Runner


@pytest.fixture
def detailed_activity():
    return DetailedActivity.model_validate(
        {
            "id": 101,
            "name": "Test Activity",
            "distance": 1000,
            "map": {"id": "1", "polyline": "_piFps|U_ulLnnqC_mqNvxq`@"},
        }
    )


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def runner(user):
    return baker.make(Runner, user=user, strava_id=123, access_expires=99999999)


def test_index(client):
    response = client.get("/")
    assert response.status_code == HTTPStatus.OK

    login_url = reverse("strava:auth")

    assertInHTML(f'<a class="btn btn-primary" href="{login_url}">Login</a>', response.content.decode("utf-8"))


def test_index_authenticated(auth_client):
    response = auth_client.get("/")
    assert response.status_code == HTTPStatus.FOUND

    activity_url = reverse("strava:activities")
    assert response["Location"] == activity_url


def test_auth(client):
    response = client.get(reverse("strava:auth"))
    assert response.status_code == HTTPStatus.FOUND

    expected = urllib.parse.quote(reverse("strava:auth_callback"), safe="")
    assert expected in response["Location"]


@patch("strava.views.Runner.auth_call_back")
def test_auth_callback(mock_auth_callback, client, user):
    mock_auth_callback.return_value = user
    response = client.get(reverse("strava:auth_callback"), query_params={"code": "test_code"})

    assert response.status_code == HTTPStatus.FOUND
    assert response["Location"] == reverse("strava:activities")
    mock_auth_callback.assert_called_once_with("test_code")


@patch("strava.views.Runner.auth_call_back")
def test_auth_callback_error(mock_auth_callback, client, user):
    mock_auth_callback.return_value = None
    response = client.get(reverse("strava:auth_callback"), query_params={"code": "test_code"})

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


@pytest.mark.django_db
@patch("strava.views.Runner.do_refresh_token")
def test_refresh_token(mock_do_refresh_token, auth_client, runner):
    response = auth_client.get(reverse("strava:refresh_token", kwargs={"strava_id": runner.strava_id}))
    assert response.status_code == HTTPStatus.FOUND
    assert response["Location"] == reverse("strava:activities")


@pytest.mark.django_db
@patch("strava.views.Runner.get_activities")
@patch("strava.views.Runner.get_details")
def test_activities_no_activities(mock_get_details, mock_get_activities, auth_client, runner):
    mock_get_activities.return_value = []
    mock_get_details.return_value = SummaryAthlete.model_validate(
        {"name": "Test Runner", "strava_id": runner.strava_id}
    )
    response = auth_client.get(reverse("strava:activities"))
    assert response.status_code == HTTPStatus.OK

    assertInHTML("No activities found", response.content.decode("utf-8"))


@pytest.mark.django_db
@patch("strava.views.Runner.get_activities")
@patch("strava.views.Runner.get_details")
def test_activities(mock_get_details, mock_get_activities, auth_client, runner):
    activity = SummaryActivity.model_validate({"id": 101, "name": "Test Activity", "distance": 1000})
    mock_get_activities.return_value = [activity]
    mock_get_details.return_value = SummaryAthlete.model_validate(
        {"name": "Test Runner", "strava_id": runner.strava_id}
    )
    response = auth_client.get(reverse("strava:activities"))
    assert response.status_code == HTTPStatus.OK

    url = reverse("strava:activity", kwargs={"activityid": activity.id})
    link = f'<a class="underline hover:text-neutral-300 transition-colors" href="{url}">{activity.name}</a>'
    assertInHTML(link, response.content.decode("utf-8"))


def test_activities_no_runner(auth_client):
    response = auth_client.get(reverse("strava:activities"))
    assert response.status_code == HTTPStatus.FOUND

    login_url = reverse("strava:auth")
    assert response["Location"] == login_url


@patch("strava.views.Runner.activity")
def test_activity(mock_activity, auth_client, runner):
    activity = DetailedActivity.model_validate({"id": 101, "name": "Test Activity", "distance": 1000})
    mock_activity.return_value = activity
    response = auth_client.get(reverse("strava:activity", kwargs={"activityid": 101}))
    assert response.status_code == HTTPStatus.OK

    assertInHTML(activity.name, response.content.decode("utf-8"))


@patch("strava.views.Runner.activity")
def test_activity_not_found(mock_activity, auth_client, runner):
    mock_activity.side_effect = Http404("Activity not found")
    response = auth_client.get(reverse("strava:activity", kwargs={"activityid": 101}))
    assert response.status_code == HTTPStatus.NOT_FOUND


@patch("strava.views.Runner.activity")
def test_activity_svg_no_path(mock_activity, auth_client, runner):
    activity = DetailedActivity.model_validate({"id": 101, "name": "Test Activity", "distance": 1000})
    mock_activity.return_value = activity
    response = auth_client.get(reverse("strava:activity_svg", kwargs={"activityid": 101}))
    assert response.status_code == HTTPStatus.NOT_FOUND


@patch("strava.views.Runner.activity")
def test_activity_svg(mock_activity, auth_client, runner):
    activity = DetailedActivity.model_validate(
        {
            "id": 101,
            "name": "Test Activity",
            "distance": 1000,
            "map": {"id": "1", "polyline": "_piFps|U_ulLnnqC_mqNvxq`@"},
        }
    )
    mock_activity.return_value = activity
    response = auth_client.get(reverse("strava:activity_svg", kwargs={"activityid": 101}))
    assert response.status_code == HTTPStatus.OK

    assertInHTML(
        '<path d="M 624 471 L 551 257 L 16 9" fill="none" id="route" stroke="#b9cded" />',
        response.content.decode("utf-8"),
    )


# Tests for activity_png view
@patch("strava.views.Runner.activity")
def test_activity_png_dark(mock_activity, auth_client, runner, detailed_activity):
    mock_activity.return_value = detailed_activity
    url = reverse("strava:activity_png", kwargs={"activityid": 101})
    response = auth_client.get(url, {"theme": "dark"})
    assert response.status_code == HTTPStatus.OK
    assert response["Content-Type"] == "image/png"
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"


@patch("strava.views.Runner.activity")
def test_activity_png_light(mock_activity, auth_client, runner, detailed_activity):
    mock_activity.return_value = detailed_activity
    url = reverse("strava:activity_png", kwargs={"activityid": 101})
    response = auth_client.get(url, {"theme": "light"})
    assert response.status_code == HTTPStatus.OK
    assert response["Content-Type"] == "image/png"
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"


@patch("strava.views.Runner.activity")
def test_activity_png_invalid_theme(mock_activity, auth_client, runner, detailed_activity):
    mock_activity.return_value = detailed_activity
    url = reverse("strava:activity_png", kwargs={"activityid": 101})
    response = auth_client.get(url, {"theme": "invalid"})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert b"Invalid theme specified." in response.content


@patch("strava.views.Runner.activity")
def test_activity_png_no_polyline(mock_activity, auth_client, runner):
    activity = DetailedActivity.model_validate({"id": 101, "name": "Test Activity", "distance": 1000, "map": None})
    mock_activity.return_value = activity
    url = reverse("strava:activity_png", kwargs={"activityid": 101})
    response = auth_client.get(url)
    assert response.status_code == HTTPStatus.NOT_FOUND


@patch("strava.views.create_event")
def test_webhook_post(mock_create_event, client):
    mock_enqueue = MagicMock()
    mock_create_event.enqueue = mock_enqueue
    payload = {"foo": "bar"}
    response = client.post(
        reverse("strava:webhook"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == HTTPStatus.OK
    mock_enqueue.assert_called_once_with(**payload)


def test_webhook_get_valid_token(client):
    response = client.get(
        reverse("strava:webhook"),
        data={"hub.verify_token": "STRAVA", "hub.challenge": "abc123"},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"hub.challenge": "abc123"}


def test_webhook_get_invalid_token(client):
    response = client.get(
        reverse("strava:webhook"),
        data={"hub.verify_token": "WRONG", "hub.challenge": "abc123"},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_webhook_method_not_allowed(client):
    response = client.put(reverse("strava:webhook"))
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
