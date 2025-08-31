from datetime import datetime, timedelta


class TimeMixin:
    """
    Mixin to add end_date functionality to an activity.
    """

    @property
    def end_date(self) -> datetime | None:
        if self.start_date and self.elapsed_time:
            return self.start_date + timedelta(seconds=self.elapsed_time)
        return None
