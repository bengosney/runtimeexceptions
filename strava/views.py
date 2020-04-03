# Django
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy as reverse

# Third Party
from PIL import Image

# Locals
from .models import Runner


def auth(request):
    return HttpResponseRedirect(Runner.get_auth_url(request))


def auth_callback(request):
    code = request.GET.get('code', '')

    user = Runner.auth_call_back(code)

    if user is not None:
        login(request, user)
        return HttpResponseRedirect(reverse('dashboard'))

    return HttpResponse(status=500)


def refresh_token(request, stravaid):
    runner = get_object_or_404(Runner, stravaID=stravaid)
    runner.do_refresh_token()

    return HttpResponseRedirect(reverse('dashboard'))


def login_page(request):
    return render(request, 'strava/login.html', {
        'authlink': reverse('auth'),
    })


@login_required(login_url=reverse('login'))
def dashboard(request):
    runner = get_object_or_404(Runner, stravaID=13735887)
    activites = runner.get_activities()

    return render(request, 'strava/dashboard.html', {
        'authlink': reverse('auth'),
        'refreshlink': reverse('refresh_token', args=[13735887]),
        'runner': runner.get_details(),
        'activites': activites,
    })


@login_required(login_url=reverse('login'))
def activity(request, activityid):
    runner = get_object_or_404(Runner, stravaID=13735887)
    r = runner.activity(activityid)

    return render(request, 'strava/run.html', {'activity': r})


@login_required(login_url=reverse('login'))
def activity_image(request, activityid):
    img = Image.new('RGB', (640, 480), color='red')

    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")

    return response
