import importlib
from unittest import mock

import humanize
import humanize.filesize
import humanize.lists
import humanize.number
import humanize.time
import pytest

import template_tags.templatetags.humanize as humanize_module


@pytest.fixture
def expected_filters():
    submodules = [humanize.lists, humanize.number, humanize.time, humanize.filesize]
    expected = set()
    for func in humanize.__all__:
        if any(hasattr(submodule, func) for submodule in submodules):
            expected.add(func)
    return expected


def test_init_registers_filters(monkeypatch, settings, expected_filters):
    settings.USE_I18N = True
    settings.LANGUAGE_CODE = "en-us"

    mock_library = mock.MagicMock()
    monkeypatch.setattr("django.template.Library", lambda: mock_library)

    importlib.reload(humanize_module)

    registered_filters = {call.args[0] for call in mock_library.filter.call_args_list}

    assert registered_filters == expected_filters


def test_init_no_i18n(monkeypatch, settings, expected_filters):
    settings.USE_I18N = False
    settings.LANGUAGE_CODE = "en-us"

    mock_library = mock.MagicMock()
    monkeypatch.setattr("django.template.Library", lambda: mock_library)

    importlib.reload(humanize_module)

    registered_filters = {call.args[0] for call in mock_library.filter.call_args_list}

    assert registered_filters == expected_filters


def test_init_handles_missing_locale(monkeypatch, settings, expected_filters):
    settings.USE_I18N = True
    settings.LANGUAGE_CODE = "fr-fr"

    mock_library = mock.MagicMock()
    monkeypatch.setattr("django.template.Library", lambda: mock_library)

    importlib.reload(humanize_module)

    registered_filters = {call.args[0] for call in mock_library.filter.call_args_list}

    assert registered_filters == expected_filters
