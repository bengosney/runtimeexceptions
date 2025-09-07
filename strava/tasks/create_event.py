import logging
from typing import Any

from django_tasks import task

from strava.commands import UpdateComparison, UpdateTriathlonScore, UpdateWeather
from strava.commands.find_or_create_activity import FindOrCreateActivity
from strava.data_models import EventWebhook
from strava.transformers import webhook_data_to_event

logger = logging.getLogger(__name__)


@task
def create_event(**kwargs: Any) -> int:
    logger.info("Creating event with kwargs: %s", kwargs)
    webhook = EventWebhook.model_validate(kwargs)

    event = webhook_data_to_event(webhook)
    event.save()

    logger.info("Event created: %d", event.pk)

    activity = FindOrCreateActivity(event.owner, event.object_id)()

    UpdateComparison(event.owner, activity.pk)()
    logger.info("Comparison update for runner: %d, activity: %d", event.owner.pk, activity.pk)

    UpdateTriathlonScore(event.owner, activity.pk)()
    logger.info("Triathlon score update for runner: %d, activity: %d", event.owner.pk, activity.pk)

    UpdateWeather(event.owner, activity.pk)()
    logger.info("Weather update for runner: %d, activity: %d", event.owner.pk, activity.pk)

    return event.pk
