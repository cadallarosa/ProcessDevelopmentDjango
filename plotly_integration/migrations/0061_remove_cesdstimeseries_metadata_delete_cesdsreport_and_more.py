# Generated by Django 5.1.4 on 2025-05-07 05:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plotly_integration', '0060_cesdsreport'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cesdstimeseries',
            name='metadata',
        ),
        migrations.DeleteModel(
            name='CESDSReport',
        ),
        migrations.DeleteModel(
            name='CESDSMetadata',
        ),
        migrations.DeleteModel(
            name='CESDSTimeSeries',
        ),
    ]
