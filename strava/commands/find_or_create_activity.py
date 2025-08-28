import datetime
import logging
from typing import cast

from strava.models import Activity, DetailedActivityTriathlon, Runner, Weather

logger = logging.getLogger(__name__)


class FindOrCreateActivity:
    RECENT_ACTIVITY_THRESHOLD_SECONDS = 900

    runner: Runner
    activity_id: int

    def __init__(self, runner: Runner, activity_id: int):
        self.runner = runner
        self.activity_id = activity_id
        logger.debug(f"Initialized FindOrCreateActivity with runner={runner} and activity_id={activity_id}")

    def __call__(self) -> Activity:
        logger.info(f"Looking for Activity with strava_id={self.activity_id} and runner={self.runner}")
        try:
            activity = Activity.objects.get(strava_id=self.activity_id, runner=self.runner)
            logger.info(f"Found existing Activity: {activity}")
        except Activity.DoesNotExist:
            logger.info(f"Activity not found, fetching from Strava API: strava_id={self.activity_id}")

            activity_data = cast(DetailedActivityTriathlon, self.runner.activity(self.activity_id))
            assert activity_data.id is not None, "Activity data should not be None"

            weather: Weather | None = None

            tz = getattr(activity_data.start_date, "tzinfo", None)
            now = datetime.datetime.now(tz=tz)

            if (
                activity_data.end_latlng
                and activity_data.start_date
                and abs((now - activity_data.start_date).total_seconds()) <= self.RECENT_ACTIVITY_THRESHOLD_SECONDS
            ):
                logger.debug(f"activity_data: {activity_data=}")
                lat: float = activity_data.end_latlng.root[0]
                lng: float = activity_data.end_latlng.root[1]
                logger.info(f"Fetching weather for lat={lat}, lng={lng}")
                weather = Weather.from_lat_long(lat, lng)
            else:
                logger.info(
                    f"Not setting weather strava_id={self.activity_id}, "
                    f"end_latlng: {activity_data.end_latlng}, "
                    f"start_date: {activity_data.start_date}, "
                    f"diff: {abs((now - activity_data.start_date).total_seconds())}"
                )

            activity = Activity.objects.create(
                strava_id=activity_data.id,
                type=activity_data.type.value if activity_data.type is not None else "",
                runner=self.runner,
                weather=weather,
            )
            logger.info(f"Created new Activity: {activity}")

        if not isinstance(activity, Activity):
            raise TypeError(f"Expected Activity instance, got {type(activity).__name__}")
        return activity
