from unittest.mock import patch

from django.core.management.base import CommandError

import pytest
from model_bakery import baker

from strava.commands.find_or_create_activity import FindOrCreateActivity
from strava.models import Activity, Runner


def test_create_subscription(call_command, mock_create, mock_list_empty, mock_delete):
    assert "Successfully created subscription" in call_command("create_subscription")
    assert mock_create.called
    assert mock_list_empty.called
    assert not mock_delete.called


def test_create_subscription_error(call_command, mock_create, mock_list_empty, mock_delete):
    mock_create.side_effect = Exception("API error")
    with pytest.raises(CommandError, match="API error"):
        call_command("create_subscription")
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


def test_create_subscription_existing_no_delete(call_command, mock_create, mock_list, mock_delete, mock_callback_url):
    with patch("strava.webhook.WebhookManager._get_full_url", return_value=mock_callback_url):
        assert "Found existing subscription with callback URL" in call_command("create_subscription")
        assert not mock_create.called
        assert mock_list.called
        assert not mock_delete.called


def test_type_error_if_not_activity_instance():
    runner = baker.prepare(Runner)
    with patch.object(Activity.objects, "get", return_value=None):
        with pytest.raises(TypeError, match=r"Expected Activity instance, got NoneType"):
            FindOrCreateActivity(runner, 123)()
