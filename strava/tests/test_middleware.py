from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseRedirect

import pytest

from strava.exceptions import StravaNotAuthenticatedError
from strava.middleware import NotAuthenticated


@pytest.fixture
def request_factory(rf):
    """Fixture to provide a request factory with a proper name."""
    return rf


def test_no_exception_returns_response(request_factory):
    get_response = mock.MagicMock()
    request = request_factory.get("/")
    request.user = AnonymousUser()

    middleware = NotAuthenticated(get_response)
    response = middleware(request)

    assert get_response.return_value == response


def test_redirect_to_login_on_strava_not_authenticated(mocker, request_factory):
    get_response = mock.MagicMock()
    request = request_factory.get("/")
    request.user = AnonymousUser()

    mock_logout = mocker.patch("strava.middleware.logout")
    mock_reverse = mocker.patch("strava.middleware.reverse_lazy", return_value="/login/")

    middleware = NotAuthenticated(get_response)
    response = middleware.process_exception(request, StravaNotAuthenticatedError("Not authenticated"))

    assert response.status_code == HttpResponseRedirect.status_code
    assert response.url == mock_reverse.return_value
    mock_logout.assert_called_once_with(request)
    mock_reverse.assert_called_once_with("strava:login")


def test_process_exception_ignores_other_exceptions(request_factory, mocker):
    get_response = mock.MagicMock()
    request = request_factory.get("/")
    request.user = AnonymousUser()

    mock_logout = mocker.patch("strava.middleware.logout")
    mock_reverse = mocker.patch("strava.middleware.reverse_lazy", return_value="/login/")

    middleware = NotAuthenticated(get_response)
    response = middleware.process_exception(request, Exception("Other"))

    assert response is None
    mock_logout.assert_not_called()
    mock_reverse.assert_not_called()
