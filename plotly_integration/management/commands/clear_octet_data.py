"""
Django management command to clear all Octet data from database
"""
from django.core.management.base import BaseCommand
from plotly_integration.models import OctetExperiment


class Command(BaseCommand):
    help = 'Clear all Octet data from database (experiments and all related records)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all Octet data'
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                '\n' + '='*70
            ))
            self.stdout.write(self.style.WARNING(
                'WARNING: This will delete ALL Octet data from the database!'
            ))
            self.stdout.write(self.style.WARNING(
                '='*70 + '\n'
            ))
            self.stdout.write(
                'This includes:\n'
                '  - All experiments\n'
                '  - All sensor data\n'
                '  - All step data\n'
                '  - All time series data (~100,000+ records per experiment)\n'
                '  - All layout and sequence data\n'
            )
            self.stdout.write(self.style.WARNING(
                '\nUse --confirm to proceed with deletion.\n'
            ))
            return

        # Get counts before deletion
        from plotly_integration.models import (
            OctetSensorData, OctetStepData, OctetTimeSeriesData,
            OctetSensorLayout, OctetSampleLayout, OctetStepSequence
        )

        exp_count = OctetExperiment.objects.count()
        sensor_count = OctetSensorData.objects.count()
        step_count = OctetStepData.objects.count()
        ts_count = OctetTimeSeriesData.objects.count()
        sensor_layout_count = OctetSensorLayout.objects.count()
        sample_layout_count = OctetSampleLayout.objects.count()
        sequence_count = OctetStepSequence.objects.count()

        if exp_count == 0:
            self.stdout.write(self.style.SUCCESS(
                '\nNo Octet data found in database. Nothing to delete.\n'
            ))
            return

        self.stdout.write('\n' + '='*70)
        self.stdout.write('DELETING OCTET DATA')
        self.stdout.write('='*70 + '\n')

        self.stdout.write(f'Experiments: {exp_count}')
        self.stdout.write(f'Sensors: {sensor_count}')
        self.stdout.write(f'Steps: {step_count}')
        self.stdout.write(f'Time Series Points: {ts_count:,}')
        self.stdout.write(f'Sensor Layout Entries: {sensor_layout_count}')
        self.stdout.write(f'Sample Layout Entries: {sample_layout_count}')
        self.stdout.write(f'Step Sequence Entries: {sequence_count}')
        self.stdout.write(f'Total Records: {exp_count + sensor_count + step_count + ts_count + sensor_layout_count + sample_layout_count + sequence_count:,}\n')

        # Delete all (cascade will handle related records)
        self.stdout.write('Deleting all Octet experiments (cascade delete)...')
        OctetExperiment.objects.all().delete()

        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('[SUCCESS] All Octet data cleared'))
        self.stdout.write('='*70 + '\n')

        # Verify deletion
        remaining = OctetExperiment.objects.count()
        if remaining == 0:
            self.stdout.write(self.style.SUCCESS(
                'Verification: No Octet experiments remain in database.\n'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f'Warning: {remaining} experiments still remain in database!\n'
            ))
