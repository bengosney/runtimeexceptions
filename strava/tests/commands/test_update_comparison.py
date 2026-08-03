from urllib.parse import parse_qs

import pytest
from model_bakery import baker

from strava.commands import UpdateComparison
from strava.models import Animal
from strava.tests.strava_api import activity as activity_payload
from strava.tests.strava_api import strava_url

pytestmark = pytest.mark.django_db

MARKER = UpdateComparison.MARKER_STRING

# The sample activity averages 2.78 m/s, which is a shade over 10 km/h.
ACTIVITY_KPH = 10.008


@pytest.fixture(autouse=True)
def only_the_animals_named_here():
    """
    A data migration seeds the full menagerie; these tests name their own so
    the pair either side of the pace is knowable.
    """
    Animal.objects.all().delete()


@pytest.fixture
def animals() -> tuple[Animal, Animal]:
    slower = baker.make(Animal, name="tortoise", avg_speed=0.3, max_speed=ACTIVITY_KPH - 1)
    faster = baker.make(Animal, name="greyhound", avg_speed=50.0, max_speed=ACTIVITY_KPH + 1)
    return slower, faster


def written(strava_api) -> dict[str, str]:
    put = next(call for call in strava_api.calls if call.request.method == "PUT")
    return {field: values[0] for field, values in parse_qs(put.request.body).items()}


def test_writes_the_comparison(runner, animals, strava_api):
    strava_api.get(strava_url("activities/101"), json=activity_payload(description="Felt good"))
    strava_api.put(strava_url("activities/101"), json=activity_payload())

    UpdateComparison(runner, 101)()

    expected = f"{MARKER}This was faster than a tortoise but slower than a greyhound.{MARKER}"
    assert written(strava_api)["description"] == f"Felt good {expected}"


def test_replaces_an_earlier_comparison(runner, animals, strava_api):
    already_written = f"Felt good {MARKER}This was faster than a snail but slower than a hare.{MARKER}"
    strava_api.get(strava_url("activities/101"), json=activity_payload(description=already_written))
    strava_api.put(strava_url("activities/101"), json=activity_payload())

    UpdateComparison(runner, 101)()

    description = written(strava_api)["description"]
    assert "snail" not in description
    assert "tortoise" in description


def test_strips_the_comparison_when_turned_off(runner, animals, strava_api):
    enrichment = runner.enrichment
    enrichment.animal_comparison = False
    enrichment.save()

    already_written = f"Felt good {MARKER}This was faster than a tortoise but slower than a greyhound.{MARKER}"
    strava_api.get(strava_url("activities/101"), json=activity_payload(description=already_written))
    strava_api.put(strava_url("activities/101"), json=activity_payload())

    UpdateComparison(runner, 101)()

    assert written(strava_api)["description"] == "Felt good "


def test_writes_nothing_when_turned_off_and_already_absent(runner, animals, strava_api):
    """
    An unregistered PUT would fail the test, which is the assertion.
    """
    enrichment = runner.enrichment
    enrichment.animal_comparison = False
    enrichment.save()

    strava_api.get(strava_url("activities/101"), json=activity_payload(description="Felt good"))

    UpdateComparison(runner, 101)()


def test_writes_nothing_without_an_animal_on_each_side(runner, strava_api):
    baker.make(Animal, name="tortoise", avg_speed=0.3, max_speed=ACTIVITY_KPH - 1)

    strava_api.get(strava_url("activities/101"), json=activity_payload(description="Felt good"))

    UpdateComparison(runner, 101)()


def test_writes_nothing_without_a_speed(runner, animals, strava_api):
    strava_api.get(strava_url("activities/101"), json=activity_payload(average_speed=None))

    UpdateComparison(runner, 101)()


def test_the_animals_chosen_sit_either_side_of_the_pace(runner, strava_api):
    baker.make(Animal, name="way slower", avg_speed=0.3, max_speed=1.0)
    baker.make(Animal, name="just slower", avg_speed=5.0, max_speed=ACTIVITY_KPH - 0.1)
    baker.make(Animal, name="just faster", avg_speed=15.0, max_speed=ACTIVITY_KPH + 0.1)

    strava_api.get(strava_url("activities/101"), json=activity_payload(description=""))
    strava_api.put(strava_url("activities/101"), json=activity_payload())

    UpdateComparison(runner, 101)()

    description = written(strava_api)["description"]
    slower, faster = description.split(" but slower than a ")
    assert slower.endswith(("way slower", "just slower"))
    assert faster.startswith("just faster")
