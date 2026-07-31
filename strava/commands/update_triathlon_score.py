import logging
from typing import cast

from strava.data_models import UpdatableActivity
from strava.models import Runner
from strava.utils import MarkedString

logger = logging.getLogger(__name__)


class UpdateTriathlonScore:
    MARKER_STRING = "\ufe01\ufe02"

    runner: Runner
    activity_id: int

    def __init__(self, runner: Runner, activity_id: int):
        self.runner = runner
        self.activity_id = activity_id

    def __call__(self):
        runner = cast(Runner, self.runner)
        logger.info("Updating triathlon score for activity: %d", self.activity_id)
        activity = runner.activity(self.activity_id)
        logger.debug("Activity data: %s", activity)

        score: float = activity.triathlon_percentage() / 100
        score_string = MarkedString(f"tri%: {score:.2f}.", self.MARKER_STRING)
        logger.debug("Score string: %s", score_string)

        original_description = activity.description or ""
        description = (
            score_string.replace_or_append(original_description)
            if runner.enrichment.triathlon_score
            else score_string.remove_from_text(original_description)
        )

        # The score has never belonged in the name; strip it either way.
        name = score_string.remove_from_text(activity.name or "")

        if description == original_description and name == (activity.name or ""):
            logger.info("Triathlon score already up to date for activity: %d", self.activity_id)
            return

        update = UpdatableActivity(name=name, description=description)
        runner.update_activity(self.activity_id, update)
        logger.info("Updated triathlon score for activity: %d", self.activity_id)
