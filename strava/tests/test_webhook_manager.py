from unittest import mock

from django.test import override_settings
from django.urls import reverse

import pytest

from strava.webhook import WebhookManager


@pytest.fixture
def manager() -> WebhookManager:
    return WebhookManager()


def test_create_subscription_success(manager, mock_create):
    result = manager.create_subscription()
    assert result == {"id": 123}
    assert mock_create.called
    _, kwargs = mock_create.call_args
    assert kwargs["data"]["client_id"] == "test_id"
    assert kwargs["data"]["client_secret"] == "test_secret"
    assert kwargs["data"]["callback_url"].endswith(reverse("strava:webhook"))
    assert kwargs["data"]["verify_token"] == "STRAVA"


def test_list_subscriptions_success(manager, mock_list):
    result = manager.list_subscriptions()
    assert result == [{"id": 123, "callback_url": "https://example.com/webhook"}]
    assert mock_list.called
    _, kwargs = mock_list.call_args
    assert kwargs["params"]["client_id"] == "test_id"
    assert kwargs["params"]["client_secret"] == "test_secret"


def test_list_subscriptions_failure(manager):
    mock_response = mock.Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    with mock.patch("requests.get", return_value=mock_response):
        with pytest.raises(Exception) as excinfo:
            manager.list_subscriptions()
        assert "Bad Request" in str(excinfo.value)


def test_delete_subscription_success(manager, mock_delete):
    subscription_id = 123
    manager.delete_subscription(subscription_id)
    assert mock_delete.called
    args, kwargs = mock_delete.call_args
    assert kwargs["params"]["client_id"] == "test_id"
    assert kwargs["params"]["client_secret"] == "test_secret"
    assert args[0].endswith(str(subscription_id))


def test_delete_subscription_failure(manager):
    mock_response = mock.Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    with mock.patch("requests.delete", return_value=mock_response):
        with pytest.raises(Exception) as excinfo:
            manager.delete_subscription(123)
        assert "Bad Request" in str(excinfo.value)


def test_create_subscription_failure(manager):
    mock_response = mock.Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    with mock.patch("requests.post", return_value=mock_response):
        with pytest.raises(Exception) as excinfo:
            manager.create_subscription()
        assert "Bad Request" in str(excinfo.value)


def test_get_url_reads_ngrok_file(manager, tmp_path):
    ngrok_url = "https://abc123.ngrok.io"
    base_dir = tmp_path
    ngrok_file = base_dir / ".ngrok"
    ngrok_file.write_text(ngrok_url)
    with override_settings(BASE_DIR=str(base_dir), BASE_URL="https://example.com"):
        with mock.patch("builtins.open", mock.mock_open(read_data=ngrok_url)) as m:
            result = manager._get_url()
            m.assert_called_once_with(f"{base_dir}/.ngrok")
            assert result == ngrok_url


def test_get_url_file_not_found(manager):
    with override_settings(BASE_DIR="/fake/dir", BASE_URL="https://example.com"):
        with mock.patch("builtins.open", side_effect=FileNotFoundError):
            result = manager._get_url()
            assert result == "https://example.com"
