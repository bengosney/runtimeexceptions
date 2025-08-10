import pytest
from model_bakery import baker

from strava.models import Event


@pytest.mark.django_db
def test_str():
    event = baker.make(Event)
    assert str(event) == f"{event.aspect_type} {event.object_type} {event.object_id}"
