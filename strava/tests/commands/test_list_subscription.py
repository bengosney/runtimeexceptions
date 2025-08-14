from django.core.management.base import CommandError

import pytest


def test_list(call_command, mock_list):
    output = call_command("list_subscriptions")
    mock_list.assert_called_once()

    expected_output: str = "Subscriptions:\n"
    for item in mock_list.return_value.json():
        expected_output += f"ID: {item['id']}, Callback URL: {item['callback_url']}\n"

    assert output == expected_output


def test_list_exception(call_command, mock_list_exception):
    with pytest.raises(CommandError):
        call_command("list_subscriptions")
    mock_list_exception.assert_called_once()
