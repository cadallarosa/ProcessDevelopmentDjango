# Generated by Django 5.1.4 on 2025-04-16 16:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plotly_integration', '0053_glycanreport_department_glycanreport_project_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='MassCheckReport',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('report_name', models.CharField(blank=True, max_length=255, null=True)),
                ('user_id', models.CharField(blank=True, max_length=255, null=True)),
                ('project_id', models.CharField(blank=True, max_length=255, null=True)),
                ('department', models.IntegerField(blank=True, null=True)),
                ('comments', models.TextField(blank=True, null=True)),
                ('selected_result_ids', models.TextField(help_text='Comma-separated UUIDs of MassCheckResult')),
                ('selected_result_names', models.TextField(help_text='Optional: comma-separated component_name values')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'mass_check_report',
            },
        ),
        migrations.CreateModel(
            name='MassCheckResult',
            fields=[
                ('result_id', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('result_name', models.TextField()),
                ('project_id', models.TextField(blank=True, null=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'mass_check_result',
            },
        ),
        migrations.CreateModel(
            name='MassCheckComponent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('protein_name', models.TextField()),
                ('expected_mass_da', models.FloatField(blank=True, null=True)),
                ('observed_mass_da', models.FloatField(blank=True, null=True)),
                ('mass_error_mda', models.FloatField(blank=True, null=True)),
                ('mass_error_ppm', models.FloatField(blank=True, null=True)),
                ('observed_rt_min', models.FloatField(blank=True, null=True)),
                ('response', models.FloatField(blank=True, null=True)),
                ('result', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='components', to='plotly_integration.masscheckresult')),
            ],
            options={
                'db_table': 'mass_check_component',
            },
        ),
    ]
