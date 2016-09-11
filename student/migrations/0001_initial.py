# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-09-10 22:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import student.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Assistant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.IntegerField(default=0)),
                ('classroom_id', models.IntegerField(default=0)),
                ('lesson', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Enroll',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.IntegerField(default=0)),
                ('classroom_id', models.IntegerField(default=0)),
                ('seat', models.IntegerField(default=0)),
                ('group', models.IntegerField(default=0)),
                ('group_show', models.IntegerField(default=0)),
                ('certificate1', models.BooleanField(default=False)),
                ('certificate1_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('certificate2', models.BooleanField(default=False)),
                ('certificate2_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('certificate3', models.BooleanField(default=False)),
                ('certificate3_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('certificate4', models.BooleanField(default=False)),
                ('certificate4_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('score_memo1', models.IntegerField(default=0)),
                ('score_memo2', models.IntegerField(default=0)),
                ('score_memo3', models.IntegerField(default=0)),
                ('score_memo4', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='EnrollGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('classroom_id', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='SWork',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.IntegerField(default=0)),
                ('index', models.IntegerField()),
                ('picture', models.ImageField(default=b'/static/pic/null.jpg', upload_to=student.models.upload_path_handler)),
                ('memo', models.TextField()),
                ('publication_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('score', models.IntegerField(default=-1)),
                ('scorer', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Work',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(default=0)),
                ('index', models.IntegerField()),
                ('number', models.CharField(max_length=30, unique=True)),
                ('memo', models.TextField()),
                ('publication_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('score', models.IntegerField(default=-1)),
                ('scorer', models.IntegerField(default=0)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='enroll',
            unique_together=set([('student_id', 'classroom_id')]),
        ),
    ]
