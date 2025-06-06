from io import StringIO

from django.core.management import call_command as _call_command

import pytest


@pytest.fixture
def call_command():
    def _func(command_name, *args, **kwargs):
        out = StringIO()
        _call_command(
            command_name,
            *args,
            stdout=out,
            stderr=StringIO(),
            **kwargs,
        )
        return out.getvalue()

    return _func


def test_create_subscription(call_command, mock_create, mock_list_empty, mock_delete):
    assert "Successfully created subscription" in call_command("create_subscription")
    assert mock_create.called
    assert mock_list_empty.called
    assert not mock_delete.called


def test_create_subscription_existing(call_command, mock_create, mock_list, mock_delete):
    assert "Successfully created subscription" in call_command("create_subscription")
    assert mock_create.called
    assert mock_list.called
    assert mock_delete.called
    args, _ = mock_delete.call_args
    assert args[0].endswith("123")
