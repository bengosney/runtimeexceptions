import logging

from django_tasks import task

from strava.commands.find_or_create_activity import FindOrCreateActivity
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
    if getattr(event, "aspect_type", None) != Event.ASPECT_TYPES["create"]:
        logger.info(f"Event is not a {Event.ASPECT_TYPES['create']} event, skipping weather update")
        return

    find_or_create_activity = FindOrCreateActivity(event.owner, event.object_id)
    activity = find_or_create_activity()
    logger.info("Found or created activity: %d for event: %d", activity.pk, event.pk)

    if activity.weather and activity.type in valid_activity_types:
        logger.info("Setting weather for activity: %d", activity.pk)
        activity.add_weather()
