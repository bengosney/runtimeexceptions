from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from strava.tasks.create_event import create_event as create_event_func


@pytest.fixture
def runner():
    mock_runner = MagicMock()
    mock_runner.pk = 1
    return mock_runner


@pytest.fixture
def event():
    mock_event = MagicMock()
    mock_event.pk = 42
    return mock_event


@patch("strava.tasks.create_event.update_activity_weather")
@patch("strava.tasks.create_event.Event")
@patch("strava.tasks.create_event.Runner")
def test_create_event_success(mock_runner_cls, mock_event_cls, mock_update_weather, runner, event):
    mock_runner_cls.objects.get.return_value = runner
    mock_event_cls.objects.create.return_value = event

    kwargs = {
        "event_time": int(datetime.now().timestamp()),
        "owner_id": "strava123",
        "object_type": "activity",
        "object_id": 123,
        "aspect_type": "create",
        "updates": {"key": "value"},
        "subscription_id": 123,
    }
    # Call the original function via the .func attribute of the Task object
    create_event_func.func(**kwargs)

    mock_runner_cls.objects.get.assert_called_once_with(strava_id=kwargs["owner_id"])
    mock_event_cls.objects.create.assert_called_once()
    mock_update_weather.enqueue.assert_called_once_with(event.pk)
