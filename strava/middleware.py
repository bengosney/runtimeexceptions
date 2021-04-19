# Django
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy as reverse

# First Party
from strava.exceptions import StravaNotAuthenticated


class NotAuthenticated:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, StravaNotAuthenticated):
            logout(request)
            return HttpResponseRedirect(reverse("login"))
