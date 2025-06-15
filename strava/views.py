import json
from datetime import datetime

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_not_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy as reverse
from django.utils.timezone import make_aware
from django.views.decorators.csrf import csrf_exempt

import polyline
import svgwrite
from PIL import Image, ImageDraw

from strava.data_models import SummaryActivity
from strava.line import Line
from strava.models import Event, Runner
from strava.tasks.weather import set_weather


@login_not_required
def index(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("strava:activities"))
    return render(request, "strava/index.html")


@login_not_required
def auth(request):
    return HttpResponseRedirect(Runner.get_auth_url(request) or "/")


@login_not_required
def auth_callback(request):
    code = request.GET.get("code", "")

    user = Runner.auth_call_back(code)

    if user is not None:
        login(request, user)
        return HttpResponseRedirect(reverse("strava:activities"))

    return HttpResponse(status=500)


def refresh_token(request, strava_id):
    runner: Runner = get_object_or_404(Runner, strava_id=strava_id)
    runner.do_refresh_token()

    return HttpResponseRedirect(reverse("strava:activities"))


def activities(request):
    try:
        runner: Runner = request.user.runner
    except ObjectDoesNotExist:
        logout(request)
        return HttpResponseRedirect(reverse("strava:auth"))

    activities = runner.get_activities()

    return render(
        request,
        "strava/activities.html",
        {
            "authlink": reverse("strava:auth"),
            "refreshlink": reverse("strava:refresh_token", args=[13735887]),
            "runner": runner.get_details(),
            "activities": activities,
        },
    )


def activity(request, activityid):
    runner: Runner = request.user.runner
    activity = runner.activity(activityid)

    return render(request, "strava/run.html", {"activity": activity})


def activity_svg(request, activityid):
    runner: Runner = request.user.runner
    activity: SummaryActivity = runner.activity(activityid)
    if not activity.map or not activity.map.polyline:
        raise Http404("Activity does not have a map or polyline data.")

    decoded_line = [(float(lat), float(lng)) for lat, lng in polyline.decode(activity.map.polyline)]
    line = Line(decoded_line)

    route_colour = "#b9cded"
    size = (640, 480)

    line.fit(size)

    animation_time: float = (activity.distance / 1000) if activity.distance else 0

    style = f"""
#route {{
    stroke-dasharray: {line.length};
    stroke-dashoffset: {line.length};
    animation: dash {animation_time * 0.5}s linear forwards;
}}

@keyframes dash {{
    to {{
        stroke-dashoffset: 0;
    }}
}}
"""

    dwg = svgwrite.Drawing(profile="full", size=size)
    dwg.add(dwg.style(style))
    dwg.add(dwg.rect(size=size, fill="none"))
    dwg.add(dwg.path(d=line, stroke=route_colour, fill="none", id="route"))

    response = HttpResponse(content_type="image/svg+xml")
    response.write(dwg.tostring())

    return response


def activity_png(request, activityid):
    runner: Runner = request.user.runner
    activity = runner.activity(activityid)
    if not activity.map or not activity.map.polyline:
        raise Http404("Activity does not have a map or polyline data.")

    decoded_line = [(float(lat), float(lng)) for lat, lng in polyline.decode(activity.map.polyline)]
    line = Line(decoded_line)

    base_colour = "#4287f5"

    im = Image.new("RGB", (640, 480), color=base_colour)
    draw = ImageDraw.Draw(im)

    line.fit(im.size)

    prev = None
    for p in line.coordinates:
        if prev is not None:
            draw.line(prev + p, fill=128)
        prev = p

    response = HttpResponse(content_type="image/png")
    im.save(response, "PNG")  # type: ignore

    return response


@login_not_required
@csrf_exempt
def webhook(request):
    """
    This is the endpoint that Strava will call when there is a webhook event.
    """
    if request.method == "POST":
        payload = json.loads(request.body)
        payload["event_time"] = make_aware(datetime.fromtimestamp(payload["event_time"]))
        payload["owner_id"] = Runner.objects.get(strava_id=payload["owner_id"])
        event = Event.objects.create(**payload)
        set_weather.enqueue(event.pk)

        return HttpResponse(status=200)
    elif request.method == "GET":
        verify_token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if verify_token == "STRAVA":
            return JsonResponse({"hub.challenge": challenge})
        else:
            return HttpResponse(status=403)
    else:
        return HttpResponse(status=405)
