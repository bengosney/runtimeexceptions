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
    logger.debug("Creating event: %s", kwargs)
    event = Event.objects.create(**kwargs)
    set_weather.enqueue(event.pk)
