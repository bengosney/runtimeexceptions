from django_tasks import task

from strava.models import Activity, Event
from strava.types import ActivityType

valid_activity_types = [
    ActivityType.RUN.value,
    ActivityType.RIDE.value,
    ActivityType.TRAILRUN.value,
    ActivityType.WALK.value,
]


@task
def set_weather(update_id: int):
    event = Event.objects.get(id=update_id)
    if getattr(event, "aspect_type", None) != Event.ASPECT_TYPES["create"]:
        return

    activity = Activity.find_or_create(event.owner_id, event.object_id)

    if activity.weather and activity.type in valid_activity_types:
        print("setting weather for activity", activity.strava_id)
        activity.add_weather()
