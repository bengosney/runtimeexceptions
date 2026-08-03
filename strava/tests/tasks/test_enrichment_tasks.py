from urllib.parse import parse_qs

import pytest
from model_bakery import baker

from strava.commands import UpdateComparison, UpdateTriathlonScore
from strava.models import Animal
from strava.tasks.update_comparison import update_comparison
from strava.tasks.update_triathlon_score import update_triathlon_score
from strava.tests.strava_api import ACTIVITY_ID, strava_url
from strava.tests.strava_api import activity as activity_payload

pytestmark = pytest.mark.django_db


def written(strava_api) -> dict[str, str]:
    put = next(call for call in strava_api.calls if call.request.method == "PUT")
    return {field: values[0] for field, values in parse_qs(put.request.body).items()}


def test_update_triathlon_score_writes_to_strava(runner, strava_api):
    strava_api.get(strava_url(f"activities/{ACTIVITY_ID}"), json=activity_payload(description="Felt good"))
    strava_api.put(strava_url(f"activities/{ACTIVITY_ID}"), json=activity_payload())

    update_triathlon_score.func(runner.pk, ACTIVITY_ID)

    marker = UpdateTriathlonScore.MARKER_STRING
    assert written(strava_api)["description"] == f"Felt good {marker}tri%: 0.50.{marker}"


def test_update_comparison_writes_to_strava(runner, strava_api):
    Animal.objects.all().delete()
    baker.make(Animal, name="tortoise", avg_speed=0.3, max_speed=9.0)
    baker.make(Animal, name="greyhound", avg_speed=50.0, max_speed=11.0)

    strava_api.get(strava_url(f"activities/{ACTIVITY_ID}"), json=activity_payload(description="Felt good"))
    strava_api.put(strava_url(f"activities/{ACTIVITY_ID}"), json=activity_payload())

    update_comparison.func(runner.pk, ACTIVITY_ID)

    marker = UpdateComparison.MARKER_STRING
    expected = f"{marker}This was faster than a tortoise but slower than a greyhound.{marker}"
    assert written(strava_api)["description"] == f"Felt good {expected}"


@pytest.mark.parametrize("task", [update_triathlon_score, update_comparison])
def test_an_unknown_runner_is_an_error(task):
    with pytest.raises(Exception, match="does not exist"):
        task.func(0, ACTIVITY_ID)
