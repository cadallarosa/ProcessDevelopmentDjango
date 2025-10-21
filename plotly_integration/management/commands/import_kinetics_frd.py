"""
Django Management Command: Import Kinetics FRD Files

Imports Octet kinetics FRD files and Excel results into the database.

Usage:
    python manage.py import_kinetics_frd \
        --frd-dir "path/to/OE292" \
        --excel-results "path/to/ExcelReport.xlsx" \
        --experiment-name "OE292" \
        --description "OE292 kinetics experiment"
"""

import sys
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
import pandas as pd
import numpy as np

# Add kinetic_analysis to path
kinetic_analysis_path = Path(__file__).parent.parent.parent / 'process_development' / 'analytical' / 'octet' / 'kinetic_analysis'
sys.path.insert(0, str(kinetic_analysis_path))

from frd_parser import FRDParser
from simple_mapper import create_simple_sensor_map
from signal_processing import process_sensor_data

from plotly_integration.models import (
    OctetExperiment,
    OctetSensorData,
    OctetStepData,
    OctetTimeSeriesData,
    OctetKineticAnalysis
)


class Command(BaseCommand):
    help = 'Import Octet kinetics FRD files into database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--frd-dir',
            type=str,
            required=True,
            help='Directory containing FRD files'
        )
        parser.add_argument(
            '--excel-results',
            type=str,
            required=True,
            help='Path to Excel results file with kinetic parameters'
        )
        parser.add_argument(
            '--experiment-name',
            type=str,
            required=True,
            help='Name for this experiment (e.g., OE292)'
        )
        parser.add_argument(
            '--description',
            type=str,
            default='',
            help='Optional description of experiment'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Delete existing experiment with same name before importing'
        )

    def handle(self, *args, **options):
        frd_dir = Path(options['frd_dir'])
        excel_results_path = Path(options['excel_results'])
        experiment_name = options['experiment_name']
        description = options['description']
        clear_existing = options['clear_existing']

        # Validate paths
        if not frd_dir.exists():
            raise CommandError(f"FRD directory not found: {frd_dir}")
        if not excel_results_path.exists():
            raise CommandError(f"Excel results file not found: {excel_results_path}")

        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"Importing Octet Kinetics Experiment: {experiment_name}")
        self.stdout.write(f"{'='*80}\n")

        # Load sensor map from Excel
        self.stdout.write("Loading sensor map from Excel...")
        sensor_map = create_simple_sensor_map(str(excel_results_path))
        self.stdout.write(f"  Loaded {len(sensor_map)} sensor entries\n")

        # Find all FRD files
        frd_files = sorted(frd_dir.glob("*.frd"))
        if not frd_files:
            raise CommandError(f"No FRD files found in {frd_dir}")

        self.stdout.write(f"Found {len(frd_files)} FRD files\n")

        # Parse first FRD to get experiment metadata
        first_parser = FRDParser(str(frd_files[0]))
        exp_info = first_parser.get_experiment_info()

        # Clear existing if requested
        if clear_existing:
            existing = OctetExperiment.objects.filter(experiment_name=experiment_name)
            if existing.exists():
                self.stdout.write(f"Deleting existing experiment: {experiment_name}")
                existing.delete()
                self.stdout.write(self.style.WARNING("  Deleted existing data\n"))

        # Create experiment record
        with transaction.atomic():
            self.stdout.write("Creating experiment record...")

            experiment = OctetExperiment.objects.create(
                run_id=exp_info.get('run_id', f"{experiment_name}_{timezone.now().strftime('%Y%m%d')}"),
                experiment_name=experiment_name,
                experiment_type='KINETICS',
                experiment_subtype='KBASIC',
                description=description,
                experiment_datetime=exp_info.get('start_datetime', ''),
                start_datetime=timezone.now(),
                machine_name=exp_info.get('machine_name', ''),
                instrument_type=exp_info.get('instrument_type', ''),
                instrument_serial=exp_info.get('instrument_serial', ''),
                sensor_type=exp_info.get('sensor_type', ''),
                assay_type='KINETICS',
                group='',
                upfb_number='',
            )

            self.stdout.write(self.style.SUCCESS(f"  Created: {experiment.experiment_name}\n"))

        # Process each FRD file
        sensor_count = 0
        step_count = 0
        timeseries_count = 0

        for frd_idx, frd_file in enumerate(frd_files, 1):
            self.stdout.write(f"[{frd_idx}/{len(frd_files)}] Processing {frd_file.name}...")

            try:
                parser = FRDParser(str(frd_file))
                cycles = parser.get_all_cycles()

                self.stdout.write(f"  Found {len(cycles)} cycles")

                for cycle in cycles:
                    # Get sensor info from map
                    antibody_id = cycle['antibody_id']
                    concentration_nm = cycle['concentration_nm']
                    key = (frd_file.name, antibody_id, concentration_nm)

                    sensor_info = sensor_map.get(key)
                    if sensor_info is None:
                        continue

                    # Create or get sensor record
                    with transaction.atomic():
                        sensor, created = OctetSensorData.objects.get_or_create(
                            experiment=experiment,
                            sensor_location=sensor_info['sensor_location'],
                            loading_sample_id=antibody_id,
                            concentration=concentration_nm,
                            defaults={
                                'sensor_type': exp_info.get('sensor_type', ''),
                                'sample_id': sensor_info['analyte'],
                                'concentration_units': 'nM',
                                'color': sensor_info['color'],
                                'frd_file': frd_file.name,
                            }
                        )

                        if created:
                            sensor_count += 1

                        # Import kinetic analysis results
                        if sensor_info['kd_m'] is not None:
                            OctetKineticAnalysis.objects.get_or_create(
                                sensor=sensor,
                                defaults={
                                    'analysis_method': '1_TO_1_BINDING',
                                    'KD': sensor_info['kd_m'],
                                    'kon': sensor_info['ka_1_ms'],
                                    'koff': sensor_info['kdis_1_s'],
                                    'r_squared': sensor_info['r_squared'],
                                }
                            )

                        # Create step data
                        # 1. Loading step
                        if cycle['loading_step']:
                            loading = cycle['loading_step']
                            loading_step = OctetStepData.objects.create(
                                sensor=sensor,
                                step_number=1,
                                step_name='Loading',
                                step_type='LOADING',
                                sample_id=antibody_id,
                                start_time=loading.get('start_time'),
                                actual_time=loading.get('actual_time'),
                            )
                            step_count += 1

                            # Store loading time series if available
                            if len(loading['time_array']) > 0:
                                timeseries_count += self._create_timeseries(
                                    loading_step,
                                    loading['time_array'],
                                    loading['signal_array'],
                                    experiment.run_id,
                                    sensor_info['sensor_location'],
                                    1
                                )

                        # 2. Baseline step
                        if cycle['baseline_step']:
                            baseline = cycle['baseline_step']
                            baseline_step = OctetStepData.objects.create(
                                sensor=sensor,
                                step_number=2,
                                step_name='Baseline',
                                step_type='BASELINE',
                                sample_id=baseline.get('sample_id', ''),
                                start_time=baseline.get('start_time'),
                                actual_time=baseline.get('actual_time'),
                            )
                            step_count += 1

                            if len(baseline['time_array']) > 0:
                                timeseries_count += self._create_timeseries(
                                    baseline_step,
                                    baseline['time_array'],
                                    baseline['signal_array'],
                                    experiment.run_id,
                                    sensor_info['sensor_location'],
                                    2
                                )

                        # 3. Association step
                        if cycle['association_step']:
                            assoc = cycle['association_step']
                            assoc_step = OctetStepData.objects.create(
                                sensor=sensor,
                                step_number=3,
                                step_name='Association',
                                step_type='ASSOC',
                                sample_id=assoc.get('sample_id', ''),
                                concentration=str(concentration_nm),
                                concentration_units='nM',
                                start_time=assoc.get('start_time'),
                                actual_time=assoc.get('actual_time'),
                            )
                            step_count += 1

                            # Process signal data
                            time_array = assoc['time_array']
                            signal_array = assoc['signal_array']

                            # Apply baseline alignment and filtering
                            signal_array = process_sensor_data(
                                signal_array,
                                time_array,
                                baseline_window=(50, 100),
                                apply_filter=True
                            )

                            timeseries_count += self._create_timeseries(
                                assoc_step,
                                time_array,
                                signal_array,
                                experiment.run_id,
                                sensor_info['sensor_location'],
                                3
                            )

                        # 4. Dissociation step
                        if cycle['dissociation_step']:
                            dissoc = cycle['dissociation_step']
                            dissoc_step = OctetStepData.objects.create(
                                sensor=sensor,
                                step_number=4,
                                step_name='Dissociation',
                                step_type='DISSOC',
                                sample_id=dissoc.get('sample_id', ''),
                                start_time=dissoc.get('start_time'),
                                actual_time=dissoc.get('actual_time'),
                            )
                            step_count += 1

                            # Process signal data
                            time_array = dissoc['time_array']
                            signal_array = dissoc['signal_array']

                            signal_array = process_sensor_data(
                                signal_array,
                                time_array,
                                apply_filter=True
                            )

                            # Offset time to continue from association
                            if cycle['association_step']:
                                time_offset = cycle['association_step']['time_array'][-1]
                                time_array = time_array + time_offset

                            timeseries_count += self._create_timeseries(
                                dissoc_step,
                                time_array,
                                signal_array,
                                experiment.run_id,
                                sensor_info['sensor_location'],
                                4
                            )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Error processing {frd_file.name}: {e}"))
                continue

        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(self.style.SUCCESS("Import Complete!"))
        self.stdout.write(f"{'='*80}")
        self.stdout.write(f"Experiment: {experiment.experiment_name}")
        self.stdout.write(f"Sensors imported: {sensor_count}")
        self.stdout.write(f"Steps created: {step_count}")
        self.stdout.write(f"Time series points: {timeseries_count}")
        self.stdout.write(f"{'='*80}\n")

    def _create_timeseries(self, step, time_array, signal_array, run_id, sensor_location, step_number):
        """Create time series data points in bulk"""
        points = []

        for time_val, signal_val in zip(time_array, signal_array):
            points.append(
                OctetTimeSeriesData(
                    step=step,
                    run_id=run_id,
                    sensor_location=sensor_location,
                    step_number=step_number,
                    time=float(time_val),
                    signal=float(signal_val),
                )
            )

        # Bulk create for efficiency
        OctetTimeSeriesData.objects.bulk_create(points, batch_size=1000)

        return len(points)
