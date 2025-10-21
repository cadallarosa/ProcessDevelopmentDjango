# Generated manually to add denormalized fields to OctetTimeSeriesData

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plotly_integration', '0136_octetexperiment_assay_type_octetexperiment_group_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='octettimeseriesdata',
            name='run_id',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Experiment run ID for easy querying (denormalized)',
                max_length=100,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='octettimeseriesdata',
            name='step_number',
            field=models.IntegerField(
                blank=True,
                db_index=True,
                help_text='Step number (1-8) for easy filtering (denormalized)',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='octettimeseriesdata',
            name='sensor_location',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Sensor location (A1, B2, etc.) for easy querying (denormalized)',
                max_length=10,
                null=True
            ),
        ),
        migrations.AddIndex(
            model_name='octettimeseriesdata',
            index=models.Index(
                fields=['run_id', 'sensor_location', 'step_number', 'time'],
                name='octet_time_query_idx'
            ),
        ),
    ]
