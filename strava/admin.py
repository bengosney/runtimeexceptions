# Django
from django.contrib import admin

# Locals
from . import models


class RunnerAdmin(admin.ModelAdmin):
    model = models.Runner
    list_display = ('stravaID', 'access_token', 'access_expires', 'refresh_token')
    list_per_page = 25


admin.site.register(models.Runner, RunnerAdmin)
