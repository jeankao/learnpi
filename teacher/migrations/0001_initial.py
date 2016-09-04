# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-09-03 10:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Classroom',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('password', models.CharField(max_length=30)),
                ('teacher_id', models.IntegerField(default=0)),
                ('group_open', models.BooleanField(default=True)),
                ('group_size', models.IntegerField(default=4)),
                ('group_show_open', models.BooleanField(default=False)),
                ('group_show_size', models.IntegerField(default=2)),
                ('event_open', models.BooleanField(default=True)),
                ('event_video_open', models.BooleanField(default=True)),
            ],
        ),
    ]
