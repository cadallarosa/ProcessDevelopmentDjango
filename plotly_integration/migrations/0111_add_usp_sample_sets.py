# Generated manually for USP Sample Sets

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('plotly_integration', '0110_remove_unused_usp_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='UspSampleSet',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('set_name', models.CharField(max_length=200, unique=True)),
                ('project_id', models.CharField(max_length=100)),
                ('reactor_type', models.CharField(max_length=50)),
                ('experiment_number', models.IntegerField(blank=True, null=True)),
                ('culture_duration', models.IntegerField(blank=True, null=True)),
                ('vessel_type', models.CharField(blank=True, max_length=50, null=True)),
                ('cell_line', models.CharField(blank=True, max_length=100, null=True)),
                ('sample_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'usp_sample_sets',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='UspAnalysisRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('analysis_type', models.CharField(max_length=50)),
                ('requested_by', models.CharField(max_length=100)),
                ('requested_at', models.DateTimeField(auto_now_add=True)),
                ('priority', models.IntegerField(default=1)),
                ('status', models.CharField(default='requested', max_length=50)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('sample_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='analysis_requests', to='plotly_integration.uspsampleset')),
            ],
            options={
                'db_table': 'usp_analysis_requests',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='UspSampleSetMembership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('sample', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='plotly_integration.limsupstreamsamples')),
                ('sample_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='plotly_integration.uspsampleset')),
            ],
            options={
                'db_table': 'usp_sample_set_membership',
                'managed': True,
            },
        ),
        migrations.AlterUniqueTogether(
            name='uspsampleset',
            unique_together={('project_id', 'reactor_type', 'experiment_number')},
        ),
        migrations.AlterUniqueTogether(
            name='uspsamplesetmembership',
            unique_together={('sample_set', 'sample')},
        ),
    ]