# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-07-31 07:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fitterKakao', '0020_auto_20170731_1634'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bottomclothes',
            name='photo',
            field=models.ImageField(blank=True, upload_to='bot/%Y/%m/%d'),
        ),
    ]
