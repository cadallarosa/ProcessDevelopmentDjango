# Generated by Django 5.1.4 on 2025-05-21 19:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plotly_integration', '0068_rename_pdsamples_limspdsamples_delete_dnassignment_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='LimsDnAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dn', models.CharField(max_length=255)),
                ('project_id', models.CharField(max_length=255)),
                ('study_name', models.CharField(max_length=255)),
                ('operator', models.CharField(max_length=255)),
                ('experiment_purpose', models.TextField()),
                ('load_volume', models.FloatField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('status', models.CharField(default='Pending', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'lims_dn_assignment',
            },
        ),
        migrations.DeleteModel(
            name='LimsPDSamples',
        ),
    ]
