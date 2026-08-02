from typing import TYPE_CHECKING

from strava.data_models import ActivityType

SWIM_DISTANCE: int = 1500
RIDE_DISTANCE: int = 40000
RUN_DISTANCE: int = 10000

TRIATHLON_DISTANCES = {
    ActivityType.Swim: SWIM_DISTANCE,
    ActivityType.Ride: RIDE_DISTANCE,
    ActivityType.Run: RUN_DISTANCE,
}


class TriathlonMixin:
    if TYPE_CHECKING:
        distance: float | None = None
        type: ActivityType | None = None

    def triathlon_percentage(self, precision: int = 2) -> float:
        if self.type is None:
            return 0
        try:
            return round(((self.distance or 0) / TRIATHLON_DISTANCES[self.type]) * 100, precision)
        except KeyError:
            return 0
