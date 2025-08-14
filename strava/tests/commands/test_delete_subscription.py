from django.core.management.base import CommandError

import pytest


def test_delete(call_command, mock_delete, settings):
    id = 123
    output = call_command("delete_subscription", id)
    mock_delete.assert_called_once_with(
        f"https://www.strava.com/api/v3/push_subscriptions/{id}",
        params={"client_id": settings.STRAVA_CLIENT_ID, "client_secret": settings.STRAVA_SECRET},
    )

    expected_output: str = f"Successfully deleted subscription with ID {id}\n"
    assert output == expected_output


def test_delete_exception(call_command, mock_delete_exception):
    with pytest.raises(CommandError):
        call_command("delete_subscription", 123)
    mock_delete_exception.assert_called_once()
