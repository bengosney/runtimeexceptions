import pytest
from model_bakery import baker

from strava.data_models import EventWebhook
from strava.models import Event, Runner
from strava.transformers import webhook_data_to_event

OBJECT_TYPE = "activity"
OBJECT_ID = 123
ASPECT_TYPE = "create"
UPDATES = {"foo": "bar"}
OWNER_ID = "456"
SUBSCRIPTION_ID = 789
EVENT_TIME = 1620000000


@pytest.fixture
def webhook_data():
    return {
        "object_type": OBJECT_TYPE,
        "object_id": OBJECT_ID,
        "aspect_type": ASPECT_TYPE,
        "updates": UPDATES,
        "owner_id": OWNER_ID,
        "subscription_id": SUBSCRIPTION_ID,
        "event_time": EVENT_TIME,
    }


def test_webhook_valid(webhook_data):
    webhook = EventWebhook.model_validate(webhook_data)
    assert webhook.object_type == OBJECT_TYPE
    assert webhook.object_id == OBJECT_ID
    assert webhook.aspect_type == ASPECT_TYPE
    assert webhook.updates == UPDATES
    assert webhook.owner_id == int(OWNER_ID)
    assert webhook.subscription_id == SUBSCRIPTION_ID
    assert webhook.event_time == EVENT_TIME


@pytest.mark.django_db
def test_transform_webhook_data_to_event(webhook_data):
    runner = baker.make(Runner, strava_id=OWNER_ID)

    event = webhook_data_to_event(EventWebhook.model_validate(webhook_data))

    assert isinstance(event, Event)
    assert event.object_type == OBJECT_TYPE
    assert event.object_id == OBJECT_ID
    assert event.aspect_type == ASPECT_TYPE
    assert event.updates == UPDATES
    assert event.owner == runner
    assert event.subscription_id == SUBSCRIPTION_ID
    assert event.event_time.timestamp() == EVENT_TIME
