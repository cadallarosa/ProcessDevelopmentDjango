# Generated by Django 5.1.4 on 2025-04-28 21:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plotly_integration', '0057_cdsdsmetadata_cdsdstimeseries'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cdsdstimeseries',
            name='metadata',
        ),
        migrations.DeleteModel(
            name='CDSDSMetadata',
        ),
        migrations.DeleteModel(
            name='CDSDSTimeSeries',
        ),
    ]
