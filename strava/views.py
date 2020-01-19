from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404

from datetime import datetime

from .models import Runner

from websettings.models import setting

import requests
from pprint import pprint

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

    assert True == False
    
    return render(request, 'strava/dashboard.html', {
        'authlink': reverse('auth'),
        'refreshlink': reverse('refresh_token', args=[13735887]),
        'activites': activites,
    })


def run(request, runid):
    runner = get_object_or_404(Runner, stravaID=13735887)
    r = runner.run(runid)    
    
    return render(request, 'strava/run.html', {'run': r})
