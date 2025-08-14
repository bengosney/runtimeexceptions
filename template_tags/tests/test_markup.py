import pytest

from template_tags.templatetags import markup


@pytest.mark.parametrize(
    "value, expected",
    [
        ("hello world", "hello\xa0world"),
        ("one space", "one\xa0space"),
        ("multiple  spaces", "multiple\xa0\xa0spaces"),
        ("", ""),
    ],
)
def test_nbsp_with_string(value, expected):
    assert markup.nbsp(value) == expected
