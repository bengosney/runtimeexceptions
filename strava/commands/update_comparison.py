from typing import cast

import structlog

from strava.data_models import UpdatableActivity
from strava.models import Animal, DetailedActivityTriathlon, Runner
from strava.utils import MarkedString

logger = structlog.get_logger(__name__)


class UpdateComparison:
    MARKER_STRING = "\ufe03\ufe04"

    runner: Runner
    activity_id: int

    def __init__(self, runner: Runner, activity_id: int):
        self.runner = runner
        self.activity_id = activity_id

    def __call__(self):
        runner = cast(Runner, self.runner)
        logger.info("Updating comparison for activity: %d", self.activity_id)
        activity = runner.activity(self.activity_id)
        logger.debug("Activity data: %s", activity)

        slower = self.get_slower(activity)
        faster = self.get_faster(activity)

        if faster is None or slower is None:
            logger.warning("Could not determine both faster and slower animals.")
            return

        score_string = MarkedString(
            f"This was faster than a {slower.name} but slower than a {faster.name}.", self.MARKER_STRING
        )
        logger.debug("Score string: %s", score_string)
        update = UpdatableActivity(
            description=score_string.replace_or_append(activity.description or ""),
        )
        runner.update_activity(self.activity_id, update)
        logger.info("Updated comparison for activity: %d", self.activity_id)

    def get_faster(self, activity: DetailedActivityTriathlon) -> Animal | None:
        if kph := self.get_kph(activity):
            animals = Animal.objects.filter(max_speed__gt=kph).order_by("?")
            if animals.exists():
                return animals.first()
        return None

    def get_slower(self, activity: DetailedActivityTriathlon) -> Animal | None:
        if kph := self.get_kph(activity):
            animals = Animal.objects.filter(max_speed__lt=kph).order_by("?")
            if animals.exists():
                return animals.first()
        return None

    def get_kph(self, activity: DetailedActivityTriathlon) -> float | None:
        return activity.average_speed * 3.6 if activity.average_speed else None
