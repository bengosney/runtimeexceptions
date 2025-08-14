import logging

from strava.models import Activity, Runner, Weather

logger = logging.getLogger(__name__)


class FindOrCreateActivity:
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
            activity_data = self.runner.activity(self.activity_id)
            assert activity_data.id is not None, "Activity data should not be None"

            weather: Weather | None = None
            if activity_data.end_latlng:
                logger.debug(f"activity_data: {activity_data=}")
                lat: float = activity_data.end_latlng.root[0]
                lng: float = activity_data.end_latlng.root[1]
                logger.info(f"Fetching weather for lat={lat}, lng={lng}")
                weather = Weather.from_lat_long(lat, lng)

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
