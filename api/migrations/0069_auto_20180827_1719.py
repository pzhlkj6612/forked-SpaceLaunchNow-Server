# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-08-27 17:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0068_auto_20180826_2333'),
    ]

    operations = [
        migrations.CreateModel(
            name='LandingLocation',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, default='', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='LandingType',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, default='', max_length=255)),
                ('description', models.CharField(blank=True, max_length=2048, null=True)),
            ],
        ),
        migrations.AlterModelOptions(
            name='orbiter',
            options={'ordering': ['name'], 'verbose_name': 'Spacecraft', 'verbose_name_plural': 'Spacecraft'},
        ),
        migrations.AddField(
            model_name='orbiter',
            name='human_rated',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='launch',
            name='landing_location',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='launch', to='api.LandingLocation'),
        ),
        migrations.AlterField(
            model_name='launch',
            name='landing_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='launch', to='api.LandingType'),
        ),
    ]
