import logging
from datetime import datetime
from typing import Any, Literal

from django.utils.timezone import make_aware

from django_tasks import task
from pydantic import BaseModel

from strava.models import Event, Runner
from strava.tasks.update_activity_weather import update_activity_weather

logger = logging.getLogger(__name__)


class WebHook(BaseModel):
    object_type: Literal["activity", "athlete"]
    object_id: int
    aspect_type: Literal["create", "update", "delete"]
    updates: dict[str, Any] | None = None
    owner_id: str
    subscription_id: int
    event_time: int

    class Config:
        frozen = True


def transform_webhook_data_to_event(webhook: WebHook) -> Event:
    event_time = make_aware(datetime.fromtimestamp(webhook.event_time))
    owner_id = Runner.objects.get(strava_id=webhook.owner_id)
    return Event(
        object_type=webhook.object_type,
        object_id=webhook.object_id,
        aspect_type=webhook.aspect_type,
        updates=webhook.updates,
        owner_id=owner_id,
        subscription_id=webhook.subscription_id,
        event_time=event_time,
    )


@task
def create_event(**kwargs: Any):
    webhook = WebHook.model_validate(kwargs)

    event = transform_webhook_data_to_event(webhook)

    logger.info("Creating event with kwargs: %s", kwargs)
    event = Event.objects.create(**kwargs)
    logger.info("Event created: %d", event.pk)
    update_activity_weather.enqueue(event.pk)
    logger.info("Weather update enqueued for event: %d", event.pk)
