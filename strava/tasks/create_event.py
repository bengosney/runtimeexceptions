import logging
from datetime import datetime
from typing import Any

from django.utils.timezone import make_aware

from django_tasks import task

from strava.models import Event, Runner
from strava.tasks.update_activity_weather import update_activity_weather

logger = logging.getLogger(__name__)


@task
def create_event(**kwargs: Any):
    kwargs["event_time"] = make_aware(datetime.fromtimestamp(kwargs["event_time"]))
    kwargs["owner_id"] = Runner.objects.get(strava_id=kwargs["owner_id"])
    logger.info("Creating event with kwargs: %s", kwargs)
    event = Event.objects.create(**kwargs)
    logger.info("Event created: %d", event.pk)
    update_activity_weather.enqueue(event.pk)
    logger.info("Weather update enqueued for event: %d", event.pk)
