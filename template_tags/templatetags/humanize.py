from contextlib import suppress

from django import template
from django.conf import settings

import humanize
import humanize.filesize
import humanize.lists
import humanize.number
import humanize.time

register = template.Library()


def init():
    if settings.USE_I18N and settings.LANGUAGE_CODE:
        locale = settings.LANGUAGE_CODE.replace("-", "_")
        with suppress(FileNotFoundError):
            humanize.activate(locale)

    submodules = [humanize.lists, humanize.number, humanize.time, humanize.filesize]
    for func in humanize.__all__:
        if any(hasattr(submodule, func) for submodule in submodules):
            register.filter(func, getattr(humanize, func))


init()
