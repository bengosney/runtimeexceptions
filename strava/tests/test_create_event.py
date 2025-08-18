from datetime import datetime
from unittest.mock import patch

import pytest
from model_bakery import baker

from strava.models import Event, Runner
from strava.tasks.create_event import create_event as create_event_func


@pytest.mark.django_db
@patch("strava.tasks.create_event.update_activity_weather")
@patch("strava.tasks.create_event.update_triathlon_score")
def test_create_event_success(mock_update_triathlon, mock_update_weather, db):
    runner = baker.make(Runner, strava_id=123)
    kwargs = {
        "event_time": int(datetime.now().timestamp()),
        "owner_id": runner.strava_id,
        "object_type": "activity",
        "object_id": 123,
        "aspect_type": "create",
        "updates": {"key": "value"},
        "subscription_id": 123,
    }
    create_event_func.func(**kwargs)

    event = Event.objects.get(owner=runner, object_id=kwargs["object_id"])
    assert event is not None
    mock_update_weather.enqueue.assert_called_once_with(event.pk)
    mock_update_triathlon.enqueue.assert_called_once_with(event.owner.pk, event.object_id)
