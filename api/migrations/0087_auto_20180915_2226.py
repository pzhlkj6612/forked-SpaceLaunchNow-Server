# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-16 02:26
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0086_auto_20180914_1405'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='launch',
            name='isoend',
        ),
        migrations.RemoveField(
            model_name='launch',
            name='isonet',
        ),
        migrations.RemoveField(
            model_name='launch',
            name='isostart',
        ),
        migrations.RemoveField(
            model_name='launch',
            name='netstamp',
        ),
        migrations.RemoveField(
            model_name='launch',
            name='westamp',
        ),
        migrations.RemoveField(
            model_name='launch',
            name='wsstamp',
        ),
    ]
