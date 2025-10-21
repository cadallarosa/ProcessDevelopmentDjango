"""
Django Management Command: Import Octet Kinetics Data

Usage:
    python manage.py import_octet_kinetics <path_to_experiment_folder>

Example:
    python manage.py import_octet_kinetics "C:/path/to/OE292"

This command imports raw Octet kinetics data from FRD files and HTSettings.efrd
"""

from django.core.management.base import BaseCommand, CommandError
import os
import logging

from plotly_integration.process_development.analytical.octet.data_import.htsettings_parser import (
    HTSettingsParser
)
from plotly_integration.process_development.analytical.octet.data_import.frd_importer import (
    import_octet_kinetics_data
)
from plotly_integration.models import OctetAnalysisTemplate

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import Octet kinetics data from FRD files and HTSettings.efrd'

    def add_arguments(self, parser):
        parser.add_argument(
            'experiment_folder',
            type=str,
            help='Path to experiment folder containing FRD files and HTSettings.efrd'
        )
        parser.add_argument(
            '--create-template',
            action='store_true',
            help='Create an OctetAnalysisTemplate from HTSettings parameters'
        )
        parser.add_argument(
            '--template-name',
            type=str,
            default='Kinetics Default',
            help='Name for the created analysis template'
        )

    def handle(self, *args, **options):
        experiment_folder = options['experiment_folder']
        create_template = options['create_template']
        template_name = options['template_name']

        # Validate folder exists
        if not os.path.exists(experiment_folder):
            raise CommandError(f"Folder does not exist: {experiment_folder}")

        if not os.path.isdir(experiment_folder):
            raise CommandError(f"Path is not a directory: {experiment_folder}")

        self.stdout.write(self.style.SUCCESS(f"\n{'='*80}"))
        self.stdout.write(self.style.SUCCESS(f"OCTET KINETICS DATA IMPORT"))
        self.stdout.write(self.style.SUCCESS(f"{'='*80}\n"))
        self.stdout.write(f"Experiment folder: {experiment_folder}\n")

        # Step 1: Check for HTSettings.efrd
        htsettings_path = os.path.join(experiment_folder, 'HTSettings.efrd')
        vendor_settings = None

        if os.path.exists(htsettings_path):
            self.stdout.write(self.style.WARNING("Step 1: Parsing HTSettings.efrd..."))
            try:
                parser = HTSettingsParser(htsettings_path)
                vendor_settings = parser.parse_all()

                self.stdout.write(self.style.SUCCESS(f"  [OK] Parsed vendor settings"))
                self.stdout.write(f"    - Analysis type: {vendor_settings.get('analysis_type')}")
                self.stdout.write(f"    - Run ID: {vendor_settings.get('run_id')}")

                kinetic_params = vendor_settings.get('kinetic_params', {})
                if kinetic_params:
                    self.stdout.write(f"    - Binding model: {kinetic_params.get('binding_model')}")
                    self.stdout.write(f"    - Association: {kinetic_params.get('assoc_start_time')}-{kinetic_params.get('assoc_end_time')}s")
                    self.stdout.write(f"    - Dissociation: {kinetic_params.get('dissoc_start_time')}-{kinetic_params.get('dissoc_end_time')}s")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  [ERROR] Error parsing HTSettings: {e}"))
                vendor_settings = None
        else:
            self.stdout.write(self.style.WARNING("Step 1: No HTSettings.efrd found, skipping..."))

        # Step 2: Count FRD files
        self.stdout.write(self.style.WARNING("\nStep 2: Scanning for FRD files..."))
        frd_files = []
        for file in os.listdir(experiment_folder):
            if file.endswith('.frd') and not file.startswith('HTSettings'):
                frd_files.append(file)

        if not frd_files:
            raise CommandError(f"No FRD files found in {experiment_folder}")

        self.stdout.write(self.style.SUCCESS(f"  [OK] Found {len(frd_files)} FRD files"))
        for frd in sorted(frd_files)[:5]:  # Show first 5
            self.stdout.write(f"    - {frd}")
        if len(frd_files) > 5:
            self.stdout.write(f"    ... and {len(frd_files) - 5} more")

        # Step 3: Import data
        self.stdout.write(self.style.WARNING("\nStep 3: Importing experiment data..."))
        try:
            experiment = import_octet_kinetics_data(experiment_folder, vendor_settings)

            self.stdout.write(self.style.SUCCESS(f"  [OK] Successfully imported experiment"))
            self.stdout.write(f"    - Experiment ID: {experiment.id}")
            self.stdout.write(f"    - Name: {experiment.experiment_name}")
            self.stdout.write(f"    - Run ID: {experiment.run_id}")
            self.stdout.write(f"    - Type: {experiment.experiment_type}/{experiment.experiment_subtype}")

            # Count imported records
            from plotly_integration.models import OctetSensorData, OctetStepData, OctetTimeSeriesData

            sensor_count = OctetSensorData.objects.filter(experiment=experiment).count()
            step_count = OctetStepData.objects.filter(sensor__experiment=experiment).count()
            timeseries_count = OctetTimeSeriesData.objects.filter(run_id=experiment.run_id).count()

            self.stdout.write(f"    - Sensors: {sensor_count}")
            self.stdout.write(f"    - Steps: {step_count}")
            self.stdout.write(f"    - Time series points: {timeseries_count:,}")

        except Exception as e:
            raise CommandError(f"Error importing data: {e}")

        # Step 4: Create analysis template (optional)
        if create_template and vendor_settings:
            self.stdout.write(self.style.WARNING("\nStep 4: Creating analysis template..."))
            try:
                parser = HTSettingsParser(htsettings_path)
                template_params = parser.get_analysis_template_params()

                template, created = OctetAnalysisTemplate.objects.update_or_create(
                    template_name=template_name,
                    analysis_type='KINETICS',
                    defaults={
                        'parameters': template_params,
                        'description': f'Auto-generated from {experiment.experiment_name} HTSettings',
                        'is_default': False,
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f"  [OK] Created new template: {template_name}"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"  [OK] Updated existing template: {template_name}"))

                self.stdout.write(f"    - Parameters: {len(template_params)} settings")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  [ERROR] Error creating template: {e}"))

        # Summary
        self.stdout.write(self.style.SUCCESS(f"\n{'='*80}"))
        self.stdout.write(self.style.SUCCESS(f"IMPORT COMPLETE"))
        self.stdout.write(self.style.SUCCESS(f"{'='*80}\n"))
        self.stdout.write(f"Experiment '{experiment.experiment_name}' has been imported successfully!")
        self.stdout.write(f"You can now analyze this data in the Octet Kinetics app.\n")
