# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-12-08 20:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0002_auto_20161204_0759'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='last_edit',
            field=models.CharField(default=None, max_length=21),
        ),
    ]
