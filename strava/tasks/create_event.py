from typing import Any

import structlog
from django_tasks import task

from strava.data_models import EventWebhook
from strava.tasks.update_activity_weather import update_activity_weather
from strava.tasks.update_comparison import update_comparison
from strava.tasks.update_triathlon_score import update_triathlon_score
from strava.transformers import webhook_data_to_event

logger = structlog.get_logger(__name__)


@task
def create_event(**kwargs: Any) -> int:
    logger.info("Creating event with kwargs: %s", kwargs)
    webhook = EventWebhook.model_validate(kwargs)

    event = webhook_data_to_event(webhook)
    event.save()

    logger.info("Event created: %d", event.pk)

    update_comparison.enqueue(event.owner.pk, event.object_id)
    logger.info("Comparison update enqueued for runner: %d, activity: %d", event.owner.pk, event.object_id)

    update_triathlon_score.enqueue(event.owner.pk, event.object_id)
    logger.info("Triathlon score update enqueued for runner: %d, activity: %d", event.owner.pk, event.object_id)

    update_activity_weather.enqueue(event.pk)
    logger.info("Weather update enqueued for event: %d", event.pk)

    return event.pk
