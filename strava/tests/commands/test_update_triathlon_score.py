from urllib.parse import parse_qs

import pytest

from strava.commands import UpdateTriathlonScore
from strava.tests.strava_api import activity as activity_payload
from strava.tests.strava_api import strava_url

pytestmark = pytest.mark.django_db

MARKER = UpdateTriathlonScore.MARKER_STRING

# 5km of the 10km run leg.
SCORE = f"{MARKER}tri%: 0.50.{MARKER}"


def written(strava_api) -> dict[str, str]:
    put = next(call for call in strava_api.calls if call.request.method == "PUT")
    return {field: values[0] for field, values in parse_qs(put.request.body).items()}


def test_writes_the_score_to_the_description(runner, strava_api):
    strava_api.get(strava_url("activities/101"), json=activity_payload(description="Felt good"))
    strava_api.put(strava_url("activities/101"), json=activity_payload())

    UpdateTriathlonScore(runner, 101)()

    assert written(strava_api)["description"] == f"Felt good {SCORE}"


def test_replaces_an_earlier_score(runner, strava_api):
    strava_api.get(
        strava_url("activities/101"), json=activity_payload(description=f"Felt good {MARKER}tri%: 0.10.{MARKER}")
    )
    strava_api.put(strava_url("activities/101"), json=activity_payload())

    UpdateTriathlonScore(runner, 101)()

    assert written(strava_api)["description"] == f"Felt good {SCORE}"


def test_strips_the_score_when_turned_off(runner, strava_api):
    enrichment = runner.enrichment
    enrichment.triathlon_score = False
    enrichment.save()

    strava_api.get(strava_url("activities/101"), json=activity_payload(description=f"Felt good {SCORE}"))
    strava_api.put(strava_url("activities/101"), json=activity_payload())

    UpdateTriathlonScore(runner, 101)()

    assert written(strava_api)["description"] == "Felt good "


def test_the_score_is_always_stripped_from_the_name(runner, strava_api):
    """
    It used to be written to the name; it is removed there whether the
    enrichment is on or off.
    """
    strava_api.get(strava_url("activities/101"), json=activity_payload(name=f"Morning Run {SCORE}"))
    strava_api.put(strava_url("activities/101"), json=activity_payload())

    UpdateTriathlonScore(runner, 101)()

    assert written(strava_api)["name"] == "Morning Run "


def test_writes_nothing_when_already_current(runner, strava_api):
    """
    An unregistered PUT would fail the test, which is the assertion.
    """
    strava_api.get(strava_url("activities/101"), json=activity_payload(description=f"Felt good {SCORE}"))

    UpdateTriathlonScore(runner, 101)()


def test_writes_nothing_when_already_absent_and_turned_off(runner, strava_api):
    enrichment = runner.enrichment
    enrichment.triathlon_score = False
    enrichment.save()

    strava_api.get(strava_url("activities/101"), json=activity_payload(description="Felt good"))

    UpdateTriathlonScore(runner, 101)()


def test_a_swim_scores_against_the_swim_leg(runner, strava_api):
    strava_api.get(strava_url("activities/101"), json=activity_payload(type="Swim", distance=750.0, description=""))
    strava_api.put(strava_url("activities/101"), json=activity_payload())

    UpdateTriathlonScore(runner, 101)()

    assert written(strava_api)["description"] == f" {MARKER}tri%: 0.50.{MARKER}"
