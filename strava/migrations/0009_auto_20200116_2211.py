# Generated by Django 3.0.2 on 2020-01-16 22:11

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('strava', '0008_auto_20200116_2132'),
    ]

    operations = [
        migrations.AlterField(
            model_name='runner',
            name='access_expires',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]
