# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-06 05:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newsitem',
            name='featured_image',
            field=models.CharField(blank=True, default='', max_length=1048, null=True),
        ),
        migrations.AlterField(
            model_name='newsitem',
            name='link',
            field=models.CharField(blank=True, default='', max_length=1048, null=True),
        ),
        migrations.AlterField(
            model_name='newsitem',
            name='news_site',
            field=models.CharField(blank=True, default='', max_length=1048, null=True),
        ),
        migrations.AlterField(
            model_name='newsitem',
            name='title',
            field=models.CharField(max_length=1048),
        ),
        migrations.AlterField(
            model_name='redditsubmission',
            name='link',
            field=models.CharField(blank=True, default='', max_length=1048, null=True),
        ),
        migrations.AlterField(
            model_name='redditsubmission',
            name='permalink',
            field=models.CharField(max_length=1048),
        ),
        migrations.AlterField(
            model_name='redditsubmission',
            name='thumbnail',
            field=models.CharField(blank=True, default='', max_length=1048, null=True),
        ),
        migrations.AlterField(
            model_name='redditsubmission',
            name='title',
            field=models.CharField(blank=True, default='', max_length=1048, null=True),
        ),
        migrations.AlterField(
            model_name='subreddit',
            name='name',
            field=models.CharField(max_length=1048),
        ),
        migrations.AlterField(
            model_name='twitteruser',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='twitteruser',
            name='profile_image',
            field=models.CharField(max_length=1048),
        ),
        migrations.AlterField(
            model_name='twitteruser',
            name='screen_name',
            field=models.CharField(max_length=255),
        ),
    ]
