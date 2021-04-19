# Django
from django.contrib import admin

# First Party
from websettings import models


class SettingAdmin(admin.ModelAdmin):
    model = models.setting
    list_display = ("key", "value")
    list_per_page = 25


admin.site.register(models.setting, SettingAdmin)
