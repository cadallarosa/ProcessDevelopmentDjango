# Generated by Django 5.1.4 on 2025-04-28 18:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plotly_integration', '0056_aktanodeids'),
    ]

    operations = [
        migrations.CreateModel(
            name='CDSDSMetadata',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_file_name', models.CharField(max_length=255)),
                ('sample_id_full', models.CharField(max_length=255)),
                ('sample_id_clean', models.CharField(max_length=255)),
                ('sample_prefix', models.CharField(max_length=10)),
                ('data_file_path', models.TextField()),
                ('method_path', models.TextField()),
                ('user_name', models.CharField(max_length=255)),
                ('acquisition_datetime', models.DateTimeField(blank=True, null=True)),
                ('sampling_rate', models.FloatField()),
                ('total_data_points', models.IntegerField()),
                ('x_axis_title', models.CharField(max_length=255)),
                ('y_axis_title', models.CharField(max_length=255)),
                ('x_axis_multiplier', models.FloatField()),
                ('y_axis_multiplier', models.FloatField()),
                ('sample_set_name', models.CharField(max_length=255)),
                ('sample_set_id', models.BigIntegerField()),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='CDSDSTimeSeries',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_min', models.FloatField()),
                ('channel_1', models.FloatField()),
                ('channel_2', models.FloatField()),
                ('channel_3', models.FloatField()),
                ('metadata', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='time_series', to='plotly_integration.cdsdsmetadata')),
            ],
        ),
    ]
