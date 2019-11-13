# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-11-12 22:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hia', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Link',
            fields=[
                ('folder_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='hia.Folder')),
                ('url', models.URLField(verbose_name='url')),
            ],
            options={
                'verbose_name': 'Link',
                'verbose_name_plural': 'Links',
            },
            bases=('hia.folder',),
        ),
        migrations.RemoveField(
            model_name='document',
            name='url',
        ),
        migrations.AlterField(
            model_name='document',
            name='file',
            field=models.FileField(default=1, upload_to=b'documents', verbose_name='file'),
            preserve_default=False,
        ),
    ]