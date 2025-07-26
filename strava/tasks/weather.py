import logging

from django_tasks import task

from strava.data_models import ActivityType
from strava.models import Activity, Event

logger = logging.getLogger(__name__)

valid_activity_types = [
    ActivityType.Run.value,
    ActivityType.Ride.value,
    ActivityType.Walk.value,
]


@task
def set_weather(update_id: int):
    event = Event.objects.get(id=update_id)
    logger.info("Setting weather for event: %d with aspect_type: %s", event.pk, getattr(event, "aspect_type", None))
    if getattr(event, "aspect_type", None) != Event.ASPECT_TYPES["create"]:
        logger.info(f"Event is not a {Event.ASPECT_TYPES['create']} event, skipping weather update")
        return

    activity = Activity.find_or_create(event.owner_id, event.object_id)
    logger.info("Found or created activity: %d for event: %d", activity.pk, event.pk)

    if activity.weather and activity.type in valid_activity_types:
        logger.info("Setting weather for activity: %d", activity.pk)
        activity.add_weather()
