from typing import Any

from pydantic import model_validator


class CleanEmptyLatLngMixin:
    @model_validator(mode="before")
    @classmethod
    def clean_empty_latlng(cls, data: Any) -> Any:
        fixable_fields: list[str] = ["start_latlng", "end_latlng"]
        for field in fixable_fields:
            if isinstance(data.get(field), list) and not data[field]:
                data[field] = None

        return data
