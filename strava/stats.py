"""
Derived figures for the overview screen.

Everything here is computed from the activity list Strava already gives us, so
the dashboard needs no extra API calls beyond the one the activities page makes.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from strava.data_models import ActivityType
from strava.models import SummaryActivityTriathlon

Period = Literal["7d", "30d"]

PERIODS: dict[Period, timedelta] = {
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}

DEFAULT_PERIOD: Period = "30d"

# Wording for the page heading, which reads "Your {human_period}."
HUMAN_PERIODS: dict[Period, str] = {
    "7d": "week",
    "30d": "month",
}


def clean_period(value: str | None) -> Period:
    """
    Coerce a query string value to one of the ranges the chips offer.
    """
    for period in PERIODS:
        if value == period:
            return period
    return DEFAULT_PERIOD


def in_period(activities: Iterable[SummaryActivityTriathlon], period: Period) -> list[SummaryActivityTriathlon]:
    cutoff = datetime.now(tz=UTC) - PERIODS[period]
    return [a for a in activities if a.start_date is not None and a.start_date >= cutoff]


def format_hours(seconds: float) -> str:
    """
    Seconds as h:mm, the form the overview KPI uses.
    """
    total_minutes = round(seconds / 60)
    return f"{total_minutes // 60}:{total_minutes % 60:02d}"


def sport_label(activity) -> str:
    """
    The sport to show for an activity.

    Strava's specific ``sport_type`` is preferred over the coarser ``type``;
    resolved here rather than in a template because a missing value used as a
    filter argument raises rather than rendering empty.
    """
    root = getattr(activity.sport_type, "root", None)
    if root:
        return str(root)
    if activity.type is not None:
        return activity.type.value
    return "Activity"


def bar_width(percentage: float) -> str:
    """
    A CSS width for a progress bar.

    Built here rather than in the template so the decimal separator can never
    be localised into something CSS will not parse.
    """
    return f"{max(0.0, min(100.0, percentage)):.1f}%"


@dataclass(frozen=True)
class ActivityRow:
    """
    One row of the activities list, paired with whatever we stored locally for
    it — currently the weather captured when it was uploaded.
    """

    activity: SummaryActivityTriathlon
    record: object | None = None

    @property
    def sport(self) -> str:
        return sport_label(self.activity)

    @property
    def triathlon_percentage(self) -> float:
        return self.activity.triathlon_percentage()

    @property
    def bar_width(self) -> str:
        return bar_width(self.triathlon_percentage)

    @property
    def is_run(self) -> bool:
        """Runs are picked out in the accent colour, as in the design."""
        return self.activity.type == ActivityType.Run

    @property
    def weather(self):
        return getattr(self.record, "weather", None)

    @property
    def weather_short(self) -> str:
        weather = self.weather
        if weather is None:
            return ""
        return f"{weather.detailed_status} · {weather.temperature:.1f}°C · Wind {weather.wind_short()}"


@dataclass(frozen=True)
class Summary:
    activities: list[SummaryActivityTriathlon]
    enriched: int

    @property
    def count(self) -> int:
        return len(self.activities)

    @property
    def total_distance(self) -> float:
        return sum(a.distance or 0 for a in self.activities)

    @property
    def total_distance_km(self) -> str:
        return f"{self.total_distance / 1000:.2f}"

    @property
    def total_moving_time(self) -> int:
        return sum(a.moving_time or 0 for a in self.activities)

    @property
    def moving_time_hours(self) -> str:
        return format_hours(self.total_moving_time)

    @property
    def average_triathlon_percentage(self) -> float:
        if not self.activities:
            return 0.0
        return sum(a.triathlon_percentage() for a in self.activities) / len(self.activities)

    @property
    def disciplines(self) -> str:
        """
        A short human list of the sports involved, for the KPI footnote.
        """
        names = sorted({a.type.value for a in self.activities if a.type is not None})
        if not names:
            return "No activities in range"
        if len(names) == 1:
            return names[0]
        return f"{', '.join(names[:-1])} and {names[-1]}".lower().capitalize()


def summarise(activities: Sequence[SummaryActivityTriathlon], enriched_ids: set[int]) -> Summary:
    """
    Build the overview figures for an already period-filtered activity list.

    ``enriched_ids`` is the set of Strava activity ids RuntimeExceptions has a
    local record for — the ones whose descriptions we have written to.
    """
    return Summary(
        activities=list(activities),
        enriched=sum(1 for a in activities if a.id in enriched_ids),
    )
