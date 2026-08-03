from strava.data_models.openapi import DetailedActivity, SummaryActivity
from strava.mixins import CleanEmptyLatLngMixin, TimeMixin, TriathlonMixin


class SummaryActivityTriathlon(CleanEmptyLatLngMixin, TriathlonMixin, TimeMixin, SummaryActivity):
    pass


class DetailedActivityTriathlon(CleanEmptyLatLngMixin, TriathlonMixin, TimeMixin, DetailedActivity):
    pass
