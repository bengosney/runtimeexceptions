import pytest

from template_tags.templatetags.abbreviations import shorten_time


@pytest.mark.parametrize(
    "value, expected",
    [
        ("1 minute", "1m"),
        ("2 seconds", "2s"),
        ("3 hours", "3h"),
        ("4 days", "4d"),
        ("5 minutes and 6 seconds", "5m 6s"),
        ("10 minutes and 20 seconds", "10m 20s"),
        ("1 hour 5 minutes and 6 seconds", "1h 5m 6s"),
        ("1 minute and 2 seconds", "1m 2s"),
    ],
)
def test_shorten_time(value, expected):
    assert shorten_time(value) == expected
