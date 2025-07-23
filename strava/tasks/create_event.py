import logging
from datetime import datetime
from typing import Any

from django.utils.timezone import make_aware

from django_tasks import task

from strava.models import Event, Runner
from strava.tasks.weather import set_weather

logger = logging.getLogger(__name__)


@task
def create_event(**kwargs: Any):
    kwargs["event_time"] = make_aware(datetime.fromtimestamp(kwargs["event_time"]))
    kwargs["owner_id"] = Runner.objects.get(strava_id=kwargs["owner_id"])
    logger.info("Creating event", extra={"kwargs": kwargs})
    event = Event.objects.create(**kwargs)
    logger.info("Event created", extra={"event": event})
    set_weather.enqueue(event.pk)
    logger.info("Weather set for event", extra={"event_id": event.pk})
