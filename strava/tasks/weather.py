from django_tasks import task
from icecream import ic

from strava.models import Activity, Event


@task
def set_weather(update_id: int):
    event = Event.objects.get(id=update_id)
    activity = Activity.find_or_create(event.owner_id, event.object_id)

    ic(activity)
    ic(activity.type)
    if activity.weather and activity.type == "Run":
        print("setting weather for activity", activity.strava_id)
        print(activity.weather.short())
        print(activity.weather.long())
