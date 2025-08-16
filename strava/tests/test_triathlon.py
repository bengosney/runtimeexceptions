from strava.data_models import ActivityType
from strava.mixins.triathlon import RIDE_DISTANCE, RUN_DISTANCE, SWIM_DISTANCE, TriathlonMixin

FIFTY_PERCENT = 50
THIRTY_THREE_PERCENT = 33.33


class DummyActivity(TriathlonMixin):
    def __init__(self, distance, type_):
        self.distance = distance
        self.type = type_


def test_triathlon_percentage_swim():
    activity = DummyActivity(SWIM_DISTANCE // 2, ActivityType.Swim)
    assert activity.triathlon_percentage() == FIFTY_PERCENT


def test_triathlon_percentage_bike():
    activity = DummyActivity(RIDE_DISTANCE // 2, ActivityType.Ride)
    assert activity.triathlon_percentage() == FIFTY_PERCENT


def test_triathlon_percentage_run():
    activity = DummyActivity(RUN_DISTANCE // 2, ActivityType.Run)
    assert activity.triathlon_percentage() == FIFTY_PERCENT


def test_triathlon_percentage_run_third():
    activity = DummyActivity(RUN_DISTANCE // 3, ActivityType.Run)
    assert activity.triathlon_percentage() == THIRTY_THREE_PERCENT


def test_triathlon_percentage_none_distance():
    activity = DummyActivity(None, ActivityType.Run)
    assert activity.triathlon_percentage() == 0


def test_triathlon_percentage_none_type():
    activity = DummyActivity(1000, None)
    assert activity.triathlon_percentage() == 0


def test_triathlon_percentage_invalid_type():
    class FakeType:
        pass

    activity = DummyActivity(1000, FakeType())
    assert activity.triathlon_percentage() == 0
