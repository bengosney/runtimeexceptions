import logging
from datetime import datetime
from typing import Any

from django.utils.timezone import make_aware

from django_tasks import task

from strava.data_models import EventWebhook
from strava.models import Event, Runner
from strava.tasks.update_activity_weather import update_activity_weather

logger = logging.getLogger(__name__)


def transform_webhook_data_to_event(event_data: EventWebhook) -> Event:
    event_time = make_aware(datetime.fromtimestamp(event_data.event_time))
    owner_id = Runner.objects.get(strava_id=event_data.owner_id)
    return Event(
        object_type=event_data.object_type,
        object_id=event_data.object_id,
        aspect_type=event_data.aspect_type,
        updates=event_data.updates,
        owner_id=owner_id,
        subscription_id=event_data.subscription_id,
        event_time=event_time,
    )


@task
def create_event(**kwargs: Any):
    webhook = EventWebhook.model_validate(kwargs)

    event = transform_webhook_data_to_event(webhook)

    logger.info("Creating event with kwargs: %s", kwargs)
    event = Event.objects.create(**kwargs)
    logger.info("Event created: %d", event.pk)
    update_activity_weather.enqueue(event.pk)
    logger.info("Weather update enqueued for event: %d", event.pk)
