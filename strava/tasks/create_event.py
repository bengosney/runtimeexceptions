import logging
from typing import Any

from django_tasks import task

from strava.data_models import EventWebhook
from strava.tasks.update_activity_weather import update_activity_weather
from strava.transformers import webhook_data_to_event

logger = logging.getLogger(__name__)


@task
def create_event(**kwargs: Any):
    logger.info("Creating event with kwargs: %s", kwargs)
    webhook = EventWebhook.model_validate(kwargs)

    event = webhook_data_to_event(webhook)
    event.save()

    logger.info("Event created: %d", event.pk)
    update_activity_weather.enqueue(event.pk)
    logger.info("Weather update enqueued for event: %d", event.pk)

    return event
