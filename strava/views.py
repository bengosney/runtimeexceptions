import json

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_not_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy as reverse
from django.views.decorators.csrf import csrf_exempt

import polyline
import svgwrite
from PIL import Image, ImageDraw

from strava.data_models import SummaryActivity
from strava.line import Line
from strava.models import Runner
from strava.tasks.create_event import create_event
from strava.tasks.update_comparison import update_comparison
from strava.tasks.update_triathlon_score import update_triathlon_score


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
    refreshlink = reverse("strava:refresh_token", kwargs={"strava_id": int(runner.strava_id)})

    return render(
        request,
        "strava/activities.html",
        {
            "authlink": reverse("strava:auth"),
            "refreshlink": refreshlink,
            "runner": runner.get_details(),
            "activities": activities,
        },
    )


def activity(request, activityid):
    runner: Runner = request.user.runner
    activity = runner.activity(activityid)

    return render(request, "strava/activity.html", {"activity": activity})


def trigger_update_activity(request, activityid):
    runner: Runner = request.user.runner

    update_triathlon_score.enqueue(runner.id, activityid)
    update_comparison.enqueue(runner.id, activityid)

    response = HttpResponse(status=204)
    response["HX-Refresh"] = "true"
    return response


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
    match request.GET.get("theme", "dark"):
        case "dark":
            line_colour = (255, 255, 255, 255)
        case "light":
            line_colour = (0, 0, 0, 255)
        case _:
            return HttpResponseBadRequest("Invalid theme specified.")

    runner: Runner = request.user.runner
    activity = runner.activity(activityid)
    if not activity.map or not activity.map.polyline:
        raise Http404("Activity does not have a map or polyline data.")

    decoded_line = [(float(lat), float(lng)) for lat, lng in polyline.decode(activity.map.polyline)]
    line = Line(decoded_line)

    scale = 4
    base_size = (640, 480)
    high_res_size = (base_size[0] * scale, base_size[1] * scale)

    im = Image.new("RGBA", high_res_size, color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    line.fit(im.size)

    prev = None
    for p in line.coordinates:
        if prev is not None:
            draw.line(prev + p, fill=line_colour, width=scale)
        prev = p

    im = im.resize(base_size, resample=Image.LANCZOS)  # type: ignore

    response = HttpResponse(content_type="image/png")
    im.save(response, "PNG")  # type: ignore

    return response


@login_not_required
@csrf_exempt
def webhook(request):
    """
    This is the endpoint that Strava will call when there is a webhook event.
    """
    match request.method:
        case "POST":
            payload = json.loads(request.body)
            create_event.enqueue(**payload)

            return HttpResponse(status=200)
        case "GET":
            verify_token = request.GET.get("hub.verify_token")
            challenge = request.GET.get("hub.challenge")

            if verify_token == "STRAVA":
                return JsonResponse({"hub.challenge": challenge})
            else:
                return HttpResponse(status=403)
        case _:
            return HttpResponse(status=405)
