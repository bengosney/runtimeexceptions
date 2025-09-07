import logging

from django_tasks import task

from strava.commands.find_or_create_activity import FindOrCreateActivity
from strava.commands.update_weather import UpdateWeather
from strava.data_models import ActivityType
from strava.models import Event

logger = logging.getLogger(__name__)

valid_activity_types: list[str] = [
    ActivityType.Run.value,
    ActivityType.Ride.value,
    ActivityType.Walk.value,
]


@task
def update_activity_weather(update_id: int):
    event = Event.objects.get(id=update_id)
    assert isinstance(event, Event)

    logger.info("Setting weather for event: %d with aspect_type: %s", event.pk, getattr(event, "aspect_type", None))

    find_or_create_activity = FindOrCreateActivity(event.owner, event.object_id)
    activity = find_or_create_activity()
    logger.info("Found or created activity: %d for event: %d", activity.pk, event.pk)

    UpdateWeather(event.owner, activity.pk)()
