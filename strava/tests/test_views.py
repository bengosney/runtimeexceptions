import urllib.parse
from http import HTTPStatus
from unittest.mock import patch

from django.http import Http404
from django.urls import reverse

import pytest
from model_bakery import baker
from pytest_django.asserts import assertInHTML

from strava.data_models import DetailedActivity, SummaryActivity, SummaryAthlete
from strava.models import Runner


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
