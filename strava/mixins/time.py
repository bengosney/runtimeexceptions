from datetime import datetime, timedelta
from typing import TYPE_CHECKING


class TimeMixin:
    """
    Mixin to add end_date functionality to an activity.
    """

    if TYPE_CHECKING:
        start_date: datetime | None = None
        elapsed_time: int | None = None

    @property
    def end_date(self) -> datetime | None:
        if self.start_date and self.elapsed_time:
            return self.start_date + timedelta(seconds=self.elapsed_time)
        return None
