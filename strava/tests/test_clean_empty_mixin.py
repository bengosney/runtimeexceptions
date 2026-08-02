from pydantic import BaseModel

from strava.mixins import CleanEmptyLatLngMixin


class LatLngModel(CleanEmptyLatLngMixin, BaseModel):
    start_latlng: list[float] | None = None
    end_latlng: list[float] | None = None


def test_clean_empty_latlng_mixin_empty():
    model = LatLngModel.model_validate(
        {
            "start_latlng": [],
            "end_latlng": [],
        }
    )

    assert model.start_latlng is None
    assert model.end_latlng is None


def test_clean_empty_latlng_mixin_none():
    model = LatLngModel.model_validate(
        {
            "start_latlng": None,
            "end_latlng": None,
        }
    )

    assert model.start_latlng is None
    assert model.end_latlng is None


def test_clean_empty_latlng_mixin():
    model = LatLngModel.model_validate(
        {
            "start_latlng": [1, 2],
            "end_latlng": [1, 2],
        }
    )

    assert model.start_latlng == [1, 2]
    assert model.end_latlng == [1, 2]
