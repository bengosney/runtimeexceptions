# Django
from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class setting(models.Model):
    key = models.CharField(max_length=250, unique=True)
    value = models.CharField(max_length=250, blank=True, default="")

    def __str__(self):
        return f"{self.key}: {self.value}"

    @staticmethod
    def getValue(key, default=""):
        try:
            obj = setting.objects.get(key=key)
        except ObjectDoesNotExist:
            obj = setting(key=key, value=default)
            obj.save()

        return obj.value

    @staticmethod
    def setValue(key, value):
        obj, _ = setting.objects.get_or_create(key=key)
        obj.value = value
        obj.save()
