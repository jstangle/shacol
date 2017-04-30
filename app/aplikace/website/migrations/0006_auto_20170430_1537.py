# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-30 13:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0005_auto_20170430_1158'),
    ]

    operations = [
        migrations.AddField(
            model_name='collision',
            name='total_memory',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='collision',
            name='coll_hash',
            field=models.CharField(max_length=60),
        ),
        migrations.AlterField(
            model_name='collision',
            name='git_revision',
            field=models.CharField(max_length=30),
        ),
        migrations.AlterField(
            model_name='collision',
            name='input_hash',
            field=models.CharField(max_length=60),
        ),
    ]