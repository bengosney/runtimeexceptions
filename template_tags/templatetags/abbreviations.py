import re

from django import template

register = template.Library()

_ABBREVIATIONS = {
    "minute": "m",
    "second": "s",
    "hour": "h",
    "day": "d",
    "and": "",
}


@register.filter
def shorten_time(value):
    """Shorten time to a more readable format."""

    def repl(match):
        return _ABBREVIATIONS[match.group(1).lower()]

    regex = r"\b\s(" + "|".join(map(re.escape, _ABBREVIATIONS.keys())) + r")s?\b"
    pattern = re.compile(regex)
    return pattern.sub(repl, value)
