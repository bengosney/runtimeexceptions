# Django
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy as reverse

# Third Party
import polyline
import svgwrite
from PIL import Image, ImageDraw

# First Party
from strava.line import Line
from strava.models import Runner


def auth(request):
    return HttpResponseRedirect(Runner.get_auth_url(request) or "/")


def auth_callback(request):
    code = request.GET.get("code", "")

    user = Runner.auth_call_back(code)

    if user is not None:
        login(request, user)
        return HttpResponseRedirect(reverse("dashboard"))

    return HttpResponse(status=500)


def refresh_token(request, stravaID):
    runner = get_object_or_404(Runner, stravaID=stravaID)
    runner.do_refresh_token()

    return HttpResponseRedirect(reverse("dashboard"))


def login_page(request):
    return render(
        request,
        "strava/login.html",
        {
            "authlink": reverse("auth"),
        },
    )


@login_required(login_url=reverse("login"))
def dashboard(request):
    runner = request.user.runner
    activities = runner.get_activities()

    return render(
        request,
        "strava/dashboard.html",
        {
            "authlink": reverse("auth"),
            "refreshlink": reverse("refresh_token", args=[13735887]),
            "runner": runner.get_details(),
            "activities": activities,
        },
    )


@login_required(login_url=reverse("login"))
def activity(request, activityid):
    runner = request.user.runner  # type: Runner
    activity = runner.activity(activityid)

    return render(request, "strava/run.html", {"activity": activity})


@login_required(login_url=reverse("login"))
def activity_svg(request, activityid):
    runner = request.user.runner  # type: Runner
    activity = runner.activity(activityid)
    line = activity["map"]["polyline"]
    line = Line(polyline.decode(line))

    base_colour = "#4287f5"
    route_colour = "#b9cded"
    size = (640, 480)

    line.fit(size)

    dwg = svgwrite.Drawing(profile="tiny", size=size)
    dwg.add(dwg.rect(size=size, fill=base_colour))
    dwg.add(dwg.path(d=line, stroke=route_colour, fill="none"))

    response = HttpResponse(content_type="image/svg+xml")
    response.write(dwg.tostring())

    return response


@login_required(login_url=reverse("login"))
def activity_png(request, activityid):
    runner = request.user.runner  # type: Runner
    activity = runner.activity(activityid)
    line = activity["map"]["polyline"]
    line = Line(polyline.decode(line))

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
