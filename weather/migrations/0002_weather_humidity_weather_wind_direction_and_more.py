# Generated by Django 5.2.1 on 2025-06-08 19:17

from django.db import migrations, models
import json

def populate_weather_fields(apps, schema_editor):
    Weather = apps.get_model('weather', 'Weather')
    for weather in Weather.objects.all():
        data = weather.other_data or {}
        weather.humidity = data.get('humidity', 0.0)
        weather.wind_direction = data.get('wind', {}).get('deg', 0.0)
        weather.wind_gust = data.get('wind', {}).get('gust', 0.0)
        weather.wind_speed = data.get('wind', {}).get('speed', 0.0)
        weather.save()

class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='weather',
            name='humidity',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='weather',
            name='wind_direction',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='weather',
            name='wind_gust',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='weather',
            name='wind_speed',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
        migrations.RunPython(populate_weather_fields, migrations.RunPython.noop),
    ]
