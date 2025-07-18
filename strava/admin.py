from django.contrib import admin

from strava import models


@admin.register(models.Runner)
class RunnerAdmin(admin.ModelAdmin):
    model = models.Runner
    list_display = ("user", "strava_id", "access_token", "access_expires", "refresh_token")
    list_per_page = 25


@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
    model = models.Event
    list_display = ("aspect_type", "event_time", "owner_id")
    list_per_page = 25


@admin.register(models.Activity)
class ActivityAdmin(admin.ModelAdmin):
    model = models.Activity
    list_display = ("strava_id", "runner", "weather")
