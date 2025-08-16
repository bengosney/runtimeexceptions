from typing import Any

from pydantic import model_validator


class CleanEmptyLatLngMixin:
    @model_validator(mode="before")
    @classmethod
    def clean_empty_latlng(cls, data: Any) -> Any:
        fixable_fields: list[str] = ["start_latlng", "end_latlng"]
        _data = dict(data)
        for field in fixable_fields:
            if isinstance(_data.get(field), list) and not _data[field]:
                _data[field] = None

        return _data
