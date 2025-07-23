import logging

from django_tasks import task

from strava.models import Activity, Event
from strava.types import ActivityType

logger = logging.getLogger(__name__)

valid_activity_types = [
    ActivityType.RUN.value,
    ActivityType.RIDE.value,
    ActivityType.TRAILRUN.value,
    ActivityType.WALK.value,
]


@task
def set_weather(update_id: int):
    event = Event.objects.get(id=update_id)
    logger.info(
        "Setting weather for event",
        extra={
            "event": event,
            "aspect_type": getattr(event, "aspect_type", None),
        },
    )
    if getattr(event, "aspect_type", None) != Event.ASPECT_TYPES["create"]:
        logger.info("Event is not a create event, skipping weather update")
        return

    activity = Activity.find_or_create(event.owner_id, event.object_id)
    logger.info(
        "Found or created activity",
        extra={
            "activity": activity,
            "weather": activity.weather,
            "type": activity.type,
        },
    )

    if activity.weather and activity.type in valid_activity_types:
        logger.info("Setting weather for activity", extra={"activity": activity})
        activity.add_weather()
