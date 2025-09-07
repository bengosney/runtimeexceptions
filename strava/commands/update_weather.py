import logging
from typing import ClassVar, cast

from strava.data_models import ActivityType, UpdatableActivity
from strava.models import Activity, Runner
from strava.utils import MarkedString

logger = logging.getLogger(__name__)


class UpdateWeather:
    MARKER_STRING = "\ufe00\ufe01"
    VALID_ACTIVITY_TYPES: ClassVar[list[str]] = [
        ActivityType.Run.value,
        ActivityType.Ride.value,
        ActivityType.Walk.value,
    ]

    def __init__(self, runner: Runner, activity_id: int):
        self.runner = runner
        self.activity_id = activity_id

    def __call__(self):
        runner = cast(Runner, self.runner)
        logger.info("Updating weather for activity: %d", self.activity_id)
        strava_activity = runner.activity(self.activity_id)

        activity = Activity.objects.filter(strava_id=strava_activity.id).first()

        if activity.type in self.VALID_ACTIVITY_TYPES and activity.weather:
            logger.info("Setting weather for activity: %d", activity.pk)

            emoji = MarkedString(activity.weather.emoji(), self.MARKER_STRING)
            name = emoji.replace_or_append(strava_activity.name or "")

            weather = MarkedString(activity.weather.long(), self.MARKER_STRING)
            description = weather.replace_or_append(strava_activity.description or "")

            update = UpdatableActivity(
                name=name,
                description=description,
            )
            runner.update_activity(self.activity_id, update)
