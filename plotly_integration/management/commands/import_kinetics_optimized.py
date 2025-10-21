"""
Django Management Command: Import Octet Kinetics Data (Optimized Version)

This script imports kinetics data into the new optimized OctetKinetics models:
- OctetKineticsExperiment (one per experiment)
- OctetKineticsSensor (one per antibody×concentration with JSON time series)

Usage:
    python manage.py import_kinetics_optimized --experiment_name OE292 --data_dir <path>

Features:
- Stores complete time series as JSON (loading, baseline, association, dissociation)
- Tracks all well locations for data integrity
- Automatically identifies reference sensors (0.0 nM)
- Parses HTSettings.efrd for processing parameters
- Uses FRD_Analysis.xlsx for sample mapping

Note: This is a wrapper around the centralized import logic in:
      plotly_integration/process_development/analytical/octet/apps/kinetic_analysis/data_import/
"""

from django.core.management.base import BaseCommand, CommandError
from plotly_integration.process_development.analytical.octet.apps.kinetic_analysis.data_import.import_command import KineticsImporter


class Command(BaseCommand):
    help = 'Import Octet Kinetics data using optimized models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--experiment_name',
            type=str,
            required=True,
            help='Experiment name (e.g., OE292)'
        )
        parser.add_argument(
            '--data_dir',
            type=str,
            required=True,
            help='Path to directory containing FRD files'
        )
        parser.add_argument(
            '--description',
            type=str,
            default='',
            help='Experiment description'
        )
        parser.add_argument(
            '--created_by',
            type=str,
            default='admin',
            help='User importing the data'
        )
        parser.add_argument(
            '--clear_existing',
            action='store_true',
            help='Clear existing data for this experiment before importing'
        )

    def handle(self, *args, **options):
        """Delegate to KineticsImporter"""
        experiment_name = options['experiment_name']
        data_dir = options['data_dir']
        description = options['description']
        created_by = options['created_by']
        clear_existing = options['clear_existing']

        try:
            # Create importer instance with stdout for proper Django command output
            importer = KineticsImporter(
                experiment_name=experiment_name,
                data_dir=data_dir,
                description=description,
                created_by=created_by,
                stdout=self.stdout
            )

            # Run the import
            experiment = importer.import_data(clear_existing=clear_existing)

            self.stdout.write(self.style.SUCCESS(f"\nImport complete: {experiment.experiment_name}"))

        except ValueError as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f"Import failed: {str(e)}")
