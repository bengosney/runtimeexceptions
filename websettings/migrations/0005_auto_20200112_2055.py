# Generated by Django 3.0.2 on 2020-01-12 20:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('websettings', '0004_auto_20200112_2031'),
    ]

    operations = [
        migrations.AlterField(
            model_name='setting',
            name='key',
            field=models.CharField(max_length=250, unique=True),
        ),
        migrations.AlterField(
            model_name='setting',
            name='value',
            field=models.CharField(max_length=250),
        ),
    ]
