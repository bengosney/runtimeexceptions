from enum import Enum

from django.core.exceptions import ValidationError

import pytest

from strava.fields import EnumListField


class ActivityType(Enum):
    WALK = "walk"
    RUN = "run"
    SWIM = "swim"
    BIKE = "bike"


@pytest.fixture
def enum_list_field():
    return EnumListField(enum_type=ActivityType)


def test_to_python_method_on_valid_list(enum_list_field):
    """Tests that to_python handles a valid list correctly."""
    valid_list = [ActivityType.WALK.value, ActivityType.RUN.value]
    result = enum_list_field.to_python(valid_list)
    assert result == valid_list


def test_to_python_method_on_invalid_list(enum_list_field):
    """Tests that to_python raises a ValidationError for an invalid list."""
    invalid_list = [ActivityType.BIKE.value, "hike"]
    with pytest.raises(ValidationError, match="Invalid choice 'hike'"):
        enum_list_field.to_python(invalid_list)


def test_to_python_method_on_none(enum_list_field):
    """Tests that to_python returns an empty list for None."""
    result = enum_list_field.to_python(None)
    assert result == []


def test_to_python_method_on_non_list_input(enum_list_field):
    """Tests that to_python raises an error for non-list input."""
    with pytest.raises(ValidationError, match="Value must be a list."):
        enum_list_field.to_python("a_string")


def test_get_prep_value_method(enum_list_field):
    """Tests that get_prep_value serializes a list to a JSON string."""
    valid_list = [ActivityType.WALK.value, ActivityType.SWIM.value]
    result = enum_list_field.get_prep_value(valid_list)
    assert result == ["walk", "swim"]


def test_from_db_value_method(enum_list_field):
    """Tests that from_db_value deserializes a JSON string back to a list."""
    json_string = '["run", "bike"]'
    result = enum_list_field.from_db_value(json_string, None, None)
    assert result == [ActivityType.RUN.value, ActivityType.BIKE.value]


def test_from_db_value_method_on_none(enum_list_field):
    """Tests that from_db_value returns an empty list for None."""
    result = enum_list_field.from_db_value(None, None, None)
    assert result == []


def test_invalid_enum_type_on_init():
    """Tests that the field raises an error if initialized with a non-enum type."""
    with pytest.raises(TypeError, match="enum_type must be a subclass of enum.Enum"):
        EnumListField(enum_type=str)  # ty: ignore[invalid-argument-type] this is what I'm testings
