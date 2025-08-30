from enum import Enum

from django.core.exceptions import ValidationError
from django.db import models
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.models.expressions import BaseExpression


class EnumListField(models.JSONField):
    """
    A custom field that serializes a list of items from a specified enum.
    """

    def __init__(self, enum_type: type[Enum], *args, **kwargs):
        if not issubclass(enum_type, Enum):
            raise TypeError("enum_type must be a subclass of enum.Enum")
        self.enum_type = enum_type
        super().__init__(*args, **kwargs)

    def to_python(self, value: list[str] | None) -> list[str]:
        value = super().to_python(value)
        if value is None:
            return []

        if not isinstance(value, list):
            raise ValidationError("Value must be a list.")

        valid_choices = [member.value for member in self.enum_type]
        for item in value:
            if not isinstance(item, str) or item not in valid_choices:
                raise ValidationError(f"Invalid choice '{item}'. Must be one of {valid_choices}.")

        return value

    def from_db_value(
        self, value: str | None, expression: BaseExpression, connection: BaseDatabaseWrapper
    ) -> list[str]:
        if value is None:
            return []
        return super().from_db_value(value, expression, connection)

    def get_prep_value(self, value: list[str] | None):
        return super().get_prep_value(self.to_python(value))
