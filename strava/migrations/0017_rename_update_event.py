# Generated by Django 5.2.1 on 2025-06-07 18:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('strava', '0016_activity'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Update',
            new_name='Event',
        ),
    ]
