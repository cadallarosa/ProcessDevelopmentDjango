# Generated migration to add fields from Excel template

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plotly_integration', '0129_add_usp_experiment_enhancements'),
    ]

    operations = [
        # Add fields to USPSeedTrain model
        migrations.AddField(
            model_name='uspseedtrain',
            name='bank_age',
            field=models.CharField(max_length=50, blank=True, null=True, help_text='e.g., P4, P5'),
        ),
        migrations.AddField(
            model_name='uspseedtrain',
            name='pool_or_clone',
            field=models.CharField(max_length=50, blank=True, null=True, choices=[('Pool', 'Pool'), ('Clone', 'Clone')]),
        ),
        migrations.AddField(
            model_name='uspseedtrain',
            name='program',
            field=models.CharField(max_length=100, blank=True, null=True, help_text='e.g., SI-49T5, 205X1'),
        ),
        migrations.AddField(
            model_name='uspseedtrain',
            name='clone',
            field=models.CharField(max_length=100, blank=True, null=True, help_text='e.g., 1B2, 25H8'),
        ),
        migrations.AddField(
            model_name='uspseedtrain',
            name='media_lot',
            field=models.CharField(max_length=100, blank=True, null=True, help_text='Media lot number'),
        ),

        # Add fields to USPVessel model
        migrations.AddField(
            model_name='uspvessel',
            name='vessel_size',
            field=models.CharField(max_length=50, blank=True, null=True, help_text='e.g., 125 mL, 1L, 2L'),
        ),
        migrations.AddField(
            model_name='uspvessel',
            name='pool_or_clone',
            field=models.CharField(max_length=50, blank=True, null=True, choices=[('Pool', 'Pool'), ('Clone', 'Clone')]),
        ),
        migrations.AddField(
            model_name='uspvessel',
            name='program',
            field=models.CharField(max_length=100, blank=True, null=True, help_text='e.g., SI-49T5, 205X1'),
        ),
        migrations.AddField(
            model_name='uspvessel',
            name='clone',
            field=models.CharField(max_length=100, blank=True, null=True, help_text='e.g., 1B2, 25H8'),
        ),
        migrations.AddField(
            model_name='uspvessel',
            name='status',
            field=models.CharField(max_length=50, blank=True, null=True, choices=[
                ('Active', 'Active'),
                ('Archived', 'Archived'),
                ('Complete', 'Complete'),
            ]),
        ),
    ]
