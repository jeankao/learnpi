# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-09-10 23:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='swork',
            name='code',
            field=models.TextField(default='code'),
            preserve_default=False,
        ),
    ]