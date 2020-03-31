# Django
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

# Third Party
from PIL import Image

# Locals
from .models import Runner


def auth(request):
    return HttpResponseRedirect(Runner.getAuthUrl(request))


def auth_callback(request):
    code = request.GET.get('code', '')

    if Runner.authCallBack(code):
        return HttpResponseRedirect(reverse('dashboard'))

    return HttpResponse(status=500)


def refreshToken(request, stravaid):
    runner = get_object_or_404(Runner, stravaID=stravaid)
    runner.refreshToken()

    return HttpResponseRedirect(reverse('dashboard'))


def dashboard(request):
    runner = get_object_or_404(Runner, stravaID=13735887)

    activites = runner.getActivities()

    return render(request, 'strava/dashboard.html', {
        'authlink': reverse('auth'),
        'refreshlink': reverse('refresh_token', args=[13735887]),
        'runner': runner.getDetails(),
        'activites': activites,
    })


def activity(request, activityid):
    runner = get_object_or_404(Runner, stravaID=13735887)
    r = runner.activity(activityid)

    return render(request, 'strava/run.html', {'activity': r})


def activityImage(request, activityid):
    img = Image.new('RGB', (640, 480), color='red')

    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")

    return response
