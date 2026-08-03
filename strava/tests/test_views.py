import json
import urllib.parse
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from unittest.mock import MagicMock, patch

from django.urls import reverse

import pytest
from pytest_django.asserts import assertInHTML

from strava.models import RunnerSettings
from strava.tests.strava_api import ATHLETE, AUTHORIZATION, POINT_POLYLINE, TOKENS, strava_url
from strava.tests.strava_api import activity as activity_payload


def strava_has_activities(strava_api, *activities) -> None:
    strava_api.get(strava_url("athlete/activities"), json=list(activities))


def strava_has_a_profile(strava_api) -> None:
    strava_api.get(strava_url("athlete"), json=ATHLETE)


def test_index(client):
    response = client.get("/")
    assert response.status_code == HTTPStatus.OK

    login_url = reverse("strava:auth")

    assertInHTML(
        f'<a href="{login_url}" class="re-btn re-btn--accent re-btn--lg">Connect with Strava</a>',
        response.content.decode("utf-8"),
    )


def test_index_authenticated(auth_client):
    response = auth_client.get("/")
    assert response.status_code == HTTPStatus.FOUND

    assert response["Location"] == reverse("strava:dashboard")


def test_auth(client):
    response = client.get(reverse("strava:auth"))
    assert response.status_code == HTTPStatus.FOUND

    expected = urllib.parse.quote(reverse("strava:auth_callback"), safe="")
    assert expected in response["Location"]


def test_auth_sends_an_absolute_callback_url(client):
    response = client.get(reverse("strava:auth"))

    redirect_uri = urllib.parse.parse_qs(urllib.parse.urlparse(response["Location"]).query)["redirect_uri"][0]
    assert redirect_uri.startswith("http://testserver")
    assert redirect_uri.endswith(reverse("strava:auth_callback"))


@pytest.mark.django_db
def test_auth_callback(strava_api, client):
    strava_api.post(strava_url("oauth/token"), json=AUTHORIZATION)

    response = client.get(reverse("strava:auth_callback"), query_params={"code": "test_code"})

    assert response.status_code == HTTPStatus.FOUND
    assert response["Location"] == reverse("strava:activities")


@pytest.mark.django_db
def test_auth_callback_signs_the_runner_in(strava_api, client):
    strava_api.post(strava_url("oauth/token"), json=AUTHORIZATION)

    client.get(reverse("strava:auth_callback"), query_params={"code": "test_code"})

    assert client.session.get("_auth_user_id") is not None


@pytest.mark.django_db
def test_refresh_token(strava_api, auth_client, runner):
    strava_api.post(strava_url("oauth/token"), json=TOKENS)

    response = auth_client.get(reverse("strava:refresh_token", kwargs={"strava_id": runner.strava_id}))

    assert response.status_code == HTTPStatus.FOUND
    assert response["Location"] == reverse("strava:activities")

    runner.refresh_from_db()
    assert runner.access_token == TOKENS["access_token"]


@pytest.mark.django_db
def test_activities_no_activities(strava_api, auth_client, runner):
    strava_has_activities(strava_api)
    strava_has_a_profile(strava_api)

    response = auth_client.get(reverse("strava:activities"))
    assert response.status_code == HTTPStatus.OK

    assertInHTML("No activities found", response.content.decode("utf-8"))


@pytest.mark.django_db
def test_activities(strava_api, auth_client, runner):
    strava_has_activities(strava_api, activity_payload(name="Test Activity"))
    strava_has_a_profile(strava_api)

    response = auth_client.get(reverse("strava:activities"))
    assert response.status_code == HTTPStatus.OK

    content = response.content.decode("utf-8")
    assert reverse("strava:activity", kwargs={"activityid": 101}) in content
    assertInHTML('<div class="re-row__name">Test Activity</div>', content)


@pytest.mark.django_db
def test_activities_filtered_by_sport(strava_api, auth_client, runner):
    strava_has_activities(
        strava_api,
        activity_payload(id=101, name="A Run", type="Run", sport_type="Run"),
        activity_payload(id=102, name="A Ride", type="Ride", sport_type="Ride"),
    )
    strava_has_a_profile(strava_api)

    content = auth_client.get(reverse("strava:activities"), {"sport": "ride"}).content.decode("utf-8")

    assert "A Ride" in content
    assert "A Run" not in content


@pytest.mark.django_db
def test_dashboard(strava_api, auth_client, runner):
    strava_has_activities(strava_api, activity_payload(start_date=datetime.now(tz=UTC).isoformat()))

    response = auth_client.get(reverse("strava:dashboard"))
    assert response.status_code == HTTPStatus.OK

    summary = response.context["summary"]
    assert summary.count == 1
    assert summary.total_distance_km == "5.00"
    assert summary.moving_time_hours == "0:30"
    # 5 km of the 10 km run leg.
    assert summary.average_triathlon_percentage == pytest.approx(50.0)
    assert summary.enriched == 0


@pytest.mark.django_db
@pytest.mark.parametrize("period, expected", [("7d", 0), ("30d", 1), ("all", 1)])
def test_dashboard_period_filters_by_date(strava_api, auth_client, runner, period, expected):
    strava_has_activities(
        strava_api,
        activity_payload(
            name="Old Activity",
            start_date=(datetime.now(tz=UTC) - timedelta(days=20)).isoformat(),
        ),
    )

    response = auth_client.get(reverse("strava:dashboard"), {"period": period})

    assert response.context["summary"].count == expected


@pytest.mark.django_db
def test_settings_shows_defaults(strava_api, auth_client, runner):
    strava_has_a_profile(strava_api)

    response = auth_client.get(reverse("strava:settings"))
    assert response.status_code == HTTPStatus.OK

    settings = RunnerSettings.objects.get(runner=runner)
    assert settings.weather_report
    assert settings.animal_comparison


@pytest.mark.django_db
def test_settings_saves_toggles(auth_client, runner):
    # Unchecked boxes are absent from the POST, so only the two named stay on.
    response = auth_client.post(
        reverse("strava:settings"),
        {"weather_report": "on", "triathlon_score": "on"},
    )
    assert response.status_code == HTTPStatus.FOUND

    settings = RunnerSettings.objects.get(runner=runner)
    assert settings.weather_report
    assert settings.triathlon_score
    assert not settings.weather_emoji
    assert not settings.animal_comparison


def test_activities_no_runner(auth_client):
    response = auth_client.get(reverse("strava:activities"))
    assert response.status_code == HTTPStatus.FOUND

    login_url = reverse("strava:auth")
    assert response["Location"] == login_url


@pytest.mark.django_db
def test_activity(strava_api, auth_client, runner):
    strava_api.get(strava_url("activities/101"), json=activity_payload(name="Test Activity"))

    response = auth_client.get(reverse("strava:activity", kwargs={"activityid": 101}))
    assert response.status_code == HTTPStatus.OK

    assertInHTML("Test Activity", response.content.decode("utf-8"))


@pytest.mark.django_db
def test_activity_without_a_route(strava_api, auth_client, runner):
    strava_api.get(strava_url("activities/101"), json=activity_payload(map=None))

    response = auth_client.get(reverse("strava:activity", kwargs={"activityid": 101}))

    assert response.status_code == HTTPStatus.OK
    assert response.context["route"] is None


@pytest.mark.django_db
def test_a_route_of_one_point_is_not_drawn(strava_api, auth_client, runner):
    strava_api.get(
        strava_url("activities/101"),
        json=activity_payload(map={"id": "a101", "polyline": POINT_POLYLINE}),
    )

    response = auth_client.get(reverse("strava:activity", kwargs={"activityid": 101}))

    assert response.status_code == HTTPStatus.OK
    assert response.context["route"] is None


@pytest.mark.django_db
def test_profile_unreadable_is_not_found(strava_api, auth_client, runner):
    strava_api.get(strava_url("athlete"), json={"id": "not an id"})

    response = auth_client.get(reverse("strava:settings"))

    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_activity_unreadable_is_not_found(strava_api, auth_client, runner):
    strava_api.get(strava_url("activities/101"), json=activity_payload(distance="not a distance"))

    response = auth_client.get(reverse("strava:activity", kwargs={"activityid": 101}))

    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_activity_missing_at_strava(strava_api, auth_client, runner):
    strava_api.get(strava_url("activities/101"), status=HTTPStatus.NOT_FOUND)

    with pytest.raises(Exception, match="Resource not found"):
        auth_client.get(reverse("strava:activity", kwargs={"activityid": 101}))


@pytest.mark.django_db
def test_expired_token_is_refreshed_before_a_view_renders(strava_api, auth_client, runner):
    runner.access_expires = "0"
    runner.save()

    strava_api.post(strava_url("oauth/token"), json=TOKENS)
    strava_api.get(strava_url("activities/101"), json=activity_payload())

    response = auth_client.get(reverse("strava:activity", kwargs={"activityid": 101}))

    assert response.status_code == HTTPStatus.OK
    runner.refresh_from_db()
    assert runner.access_token == TOKENS["access_token"]


@pytest.mark.django_db
def test_activity_svg_no_path(strava_api, auth_client, runner):
    strava_api.get(strava_url("activities/101"), json=activity_payload(map=None))

    response = auth_client.get(reverse("strava:activity_svg", kwargs={"activityid": 101}))
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_activity_svg(strava_api, auth_client, runner):
    strava_api.get(strava_url("activities/101"), json=activity_payload())

    response = auth_client.get(reverse("strava:activity_svg", kwargs={"activityid": 101}))
    assert response.status_code == HTTPStatus.OK

    assertInHTML(
        '<path d="M 624 471 L 551 257 L 16 9" fill="none" id="route" stroke="#b9cded" />',
        response.content.decode("utf-8"),
    )


@pytest.mark.django_db
@pytest.mark.parametrize("theme", ["dark", "light"])
def test_activity_png(strava_api, auth_client, runner, theme):
    strava_api.get(strava_url("activities/101"), json=activity_payload())

    response = auth_client.get(reverse("strava:activity_png", kwargs={"activityid": 101}), {"theme": theme})

    assert response.status_code == HTTPStatus.OK
    assert response["Content-Type"] == "image/png"
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.django_db
def test_activity_png_invalid_theme(auth_client, runner):
    """
    The theme is rejected before Strava is asked for anything.
    """
    response = auth_client.get(reverse("strava:activity_png", kwargs={"activityid": 101}), {"theme": "invalid"})

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert b"Invalid theme specified." in response.content


@pytest.mark.django_db
def test_activity_png_no_polyline(strava_api, auth_client, runner):
    strava_api.get(strava_url("activities/101"), json=activity_payload(map=None))

    response = auth_client.get(reverse("strava:activity_png", kwargs={"activityid": 101}))

    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_trigger_update_activity_enqueues_both_enrichments(auth_client, runner):
    with (
        patch("strava.views.update_triathlon_score") as mock_score,
        patch("strava.views.update_comparison") as mock_comparison,
    ):
        response = auth_client.get(reverse("strava:trigger_update_activity", kwargs={"activityid": 101}))

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response["HX-Refresh"] == "true"
    mock_score.enqueue.assert_called_once_with(runner.pk, 101)
    mock_comparison.enqueue.assert_called_once_with(runner.pk, 101)


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
