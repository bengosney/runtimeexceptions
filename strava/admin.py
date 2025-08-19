from typing import ClassVar

from django.contrib import admin, messages
from django.core.management import CommandError, call_command

from strava import models


@admin.register(models.Runner)
class RunnerAdmin(admin.ModelAdmin):
    model = models.Runner
    list_display = ("user", "strava_id", "access_token", "access_expires", "refresh_token")
    list_per_page = 25


@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
    model = models.Event
    list_display = ("aspect_type", "event_time", "owner")
    list_per_page = 25


@admin.register(models.Activity)
class ActivityAdmin(admin.ModelAdmin):
    model = models.Activity
    list_display = ("strava_id", "runner", "weather")
    actions: ClassVar[list[str]] = ["run_create_subscription"]

    @admin.action(description="Run create_subscription management command")
    def run_create_subscription(self, request, queryset):
        try:
            call_command("create_subscription")
            self.message_user(request, "Successfully ran create_subscription command.", messages.SUCCESS)
        except CommandError as e:
            self.message_user(request, f"Error: {e}", messages.ERROR)
        except Exception as e:
            self.message_user(request, f"Unexpected error: {e}", messages.ERROR)
