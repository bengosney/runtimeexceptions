import json
from datetime import UTC, datetime
from io import BytesIO

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_not_required
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy as reverse
from django.views.decorators.csrf import csrf_exempt

import polyline
import svgwrite
from PIL import Image, ImageDraw

from strava import stats
from strava.data_models import SummaryActivity
from strava.forms import RunnerSettingsForm
from strava.line import Line
from strava.models import Activity, Animal, Runner, SummaryActivityTriathlon
from strava.tasks.create_event import create_event
from strava.tasks.update_comparison import update_comparison
from strava.tasks.update_triathlon_score import update_triathlon_score

ROUTE_VIEWBOX = (640, 320)

# Below this a polyline has nothing to draw.
MIN_ROUTE_POINTS = 2


def _get_runner(request: HttpRequest) -> Runner | None:
    """
    The signed-in user's runner, or None once the Strava link has gone — in
    which case the session is cleared and the caller should send them to auth.
    """
    try:
        return Runner.objects.get(user=request.user)
    except Runner.DoesNotExist:
        logout(request)
        return None


def _enriched_map(runner: Runner, activities: list[SummaryActivityTriathlon]) -> dict[int, Activity]:
    """
    The local records for these activities, keyed by Strava id.

    These carry the weather we captured at upload time, which the Strava
    activity payload itself does not include.
    """
    ids = [a.id for a in activities if a.id is not None]
    records = Activity.objects.filter(runner=runner, strava_id__in=ids).select_related("weather")
    return {record.strava_id: record for record in records}


def _route(activity) -> dict | None:
    """
    The activity's route as an inline SVG path, so it takes its colour from the
    active theme rather than being baked in as an image.
    """
    if not activity.map or not activity.map.polyline:
        return None

    decoded = [(float(lat), float(lng)) for lat, lng in polyline.decode(activity.map.polyline)]
    if len(decoded) < MIN_ROUTE_POINTS:
        return None

    line = Line(decoded)
    line.fit(ROUTE_VIEWBOX)

    return {
        "path": line.svg_path(),
        "length": round(line.length),
        "width": ROUTE_VIEWBOX[0],
        "height": ROUTE_VIEWBOX[1],
    }


@login_not_required
def index(request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("strava:dashboard"))
    return render(request, "strava/index.html")


@login_not_required
def auth(request: HttpRequest) -> HttpResponseRedirect:
    return HttpResponseRedirect(Runner.get_auth_url(request) or "/")


@login_not_required
def auth_callback(request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
    code = request.GET.get("code", "")

    user = Runner.auth_call_back(code)

    if user is not None:
        login(request, user)
        return HttpResponseRedirect(reverse("strava:activities"))

    return HttpResponse(status=500)


def refresh_token(request: HttpRequest, strava_id: int) -> HttpResponseRedirect:
    runner: Runner = get_object_or_404(Runner, strava_id=strava_id)
    runner.do_refresh_token()

    return HttpResponseRedirect(reverse("strava:activities"))


def dashboard(request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
    runner = _get_runner(request)
    if runner is None:
        return HttpResponseRedirect(reverse("strava:auth"))

    period = stats.clean_period(request.GET.get("period"))
    in_range = stats.in_period(runner.get_activities(), period)
    records = _enriched_map(runner, in_range)

    return render(
        request,
        "strava/dashboard.html",
        {
            "nav": "overview",
            "period": period,
            "periods": list(stats.PERIODS),
            "human_period": stats.HUMAN_PERIODS[period],
            "summary": stats.summarise(in_range, set(records)),
        },
    )


def activities(request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
    runner = _get_runner(request)
    if runner is None:
        return HttpResponseRedirect(reverse("strava:auth"))

    all_activities = list(runner.get_activities())
    records = _enriched_map(runner, all_activities)

    sport = (request.GET.get("sport") or "").lower()
    sports = sorted({a.type.value for a in all_activities if a.type is not None})
    shown = all_activities
    if sport:
        shown = [a for a in all_activities if a.type is not None and a.type.value.lower() == sport]

    refreshlink = reverse("strava:refresh_token", kwargs={"strava_id": int(runner.strava_id)})

    return render(
        request,
        "strava/activities.html",
        {
            "nav": "activities",
            "authlink": reverse("strava:auth"),
            "refreshlink": refreshlink,
            "runner": runner.get_details(),
            "rows": [stats.ActivityRow(a, records.get(a.id)) for a in shown],
            "sports": sports,
            "sport": sport,
        },
    )


def activity(request: HttpRequest, activityid) -> HttpResponseRedirect | HttpResponse:
    runner = _get_runner(request)
    if runner is None:
        return HttpResponseRedirect(reverse("strava:auth"))

    activity = runner.activity(activityid)
    record = Activity.objects.filter(runner=runner, strava_id=activityid).select_related("weather").first()
    speed_kph = (activity.average_speed or 0) * 3.6

    return render(
        request,
        "strava/activity.html",
        {
            "nav": "activities",
            "activity": activity,
            "sport": stats.sport_label(activity),
            "weather": record.weather if record else None,
            "route": _route(activity),
            "speed_kph": speed_kph,
            # The nearest animal either side, so the panel is stable — the line
            # written to Strava picks a random pair from the same two sets.
            "slower": Animal.objects.filter(max_speed__lt=speed_kph).order_by("-max_speed").first(),
            "faster": Animal.objects.filter(max_speed__gt=speed_kph).order_by("max_speed").first(),
        },
    )


def settings(request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
    runner = _get_runner(request)
    if runner is None:
        return HttpResponseRedirect(reverse("strava:auth"))

    enrichment = runner.enrichment

    if request.method == "POST":
        form = RunnerSettingsForm(request.POST, instance=enrichment)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("strava:settings"))
    else:
        form = RunnerSettingsForm(instance=enrichment)

    return render(
        request,
        "strava/settings.html",
        {
            "nav": "settings",
            "runner": runner.get_details(),
            "form": form,
            "token_expires": datetime.fromtimestamp(int(runner.access_expires), tz=UTC),
            "refreshlink": reverse("strava:refresh_token", kwargs={"strava_id": int(runner.strava_id)}),
        },
    )


def trigger_update_activity(request: HttpRequest, activityid: int) -> HttpResponseRedirect | HttpResponse:
    runner = _get_runner(request)
    if runner is None:
        return HttpResponseRedirect(reverse("strava:auth"))

    update_triathlon_score.enqueue(runner.pk, activityid)
    update_comparison.enqueue(runner.pk, activityid)

    response = HttpResponse(status=204)
    response["HX-Refresh"] = "true"
    return response


def activity_svg(request: HttpRequest, activityid: int) -> HttpResponseRedirect | HttpResponse:
    runner = _get_runner(request)
    if runner is None:
        return HttpResponseRedirect(reverse("strava:auth"))

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


def activity_png(request: HttpRequest, activityid: int) -> HttpResponseBadRequest | HttpResponseRedirect | HttpResponse:
    match request.GET.get("theme", "dark"):
        case "dark":
            line_colour = (255, 255, 255, 255)
        case "light":
            line_colour = (0, 0, 0, 255)
        case _:
            return HttpResponseBadRequest("Invalid theme specified.")

    runner = _get_runner(request)
    if runner is None:
        return HttpResponseRedirect(reverse("strava:auth"))

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

    im = im.resize(base_size, resample=Image.Resampling.LANCZOS)

    buffer = BytesIO()
    im.save(buffer, "PNG")

    return HttpResponse(buffer.getvalue(), content_type="image/png")


@login_not_required
@csrf_exempt
def webhook(request: HttpRequest) -> HttpResponse | JsonResponse:
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
