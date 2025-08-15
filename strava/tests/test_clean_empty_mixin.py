from strava.mixins import CleanEmptyLatLngMixin


def test_clean_empty_latlng_mixin_empty():
    data = {
        "start_latlng": [],
        "end_latlng": [],
    }

    data = CleanEmptyLatLngMixin.clean_empty_latlng(data)  # ty: ignore[call-non-callable]

    assert data["start_latlng"] is None
    assert data["end_latlng"] is None


def test_clean_empty_latlng_mixin_none():
    data = {
        "start_latlng": None,
        "end_latlng": None,
    }

    data = CleanEmptyLatLngMixin.clean_empty_latlng(data)  # ty: ignore[call-non-callable]

    assert data["start_latlng"] is None
    assert data["end_latlng"] is None


def test_clean_empty_latlng_mixin():
    data = {
        "start_latlng": [1, 2],
        "end_latlng": [1, 2],
    }

    data = CleanEmptyLatLngMixin.clean_empty_latlng(data)  # ty: ignore[call-non-callable]

    assert data["start_latlng"] == [1, 2]
    assert data["end_latlng"] == [1, 2]
