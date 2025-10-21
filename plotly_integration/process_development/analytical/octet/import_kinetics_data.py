"""
Import Octet Kinetics Data to Database

Standalone script to import FRD kinetics files into Django database.
Follows the existing import pattern used in the codebase.

Usage:
    python import_kinetics_data.py
"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

# Now import Django models
from django.db import transaction
from django.utils import timezone
from plotly_integration.models import (
    OctetExperiment,
    OctetSensorData,
    OctetStepData,
    OctetTimeSeriesData,
    OctetKineticAnalysis
)

# Import analysis modules
kinetic_analysis_path = Path(__file__).parent / 'kinetic_analysis'
sys.path.insert(0, str(kinetic_analysis_path))

from frd_parser import FRDParser
from simple_mapper import create_simple_sensor_map
# Note: Signal processing is now done in the dashboard, not during import

import pandas as pd
import numpy as np


class KineticsDataImporter:
    """Import kinetics FRD files to database"""

    def __init__(self, frd_directory, excel_results_path, experiment_name, description=''):
        self.frd_directory = Path(frd_directory)
        self.excel_results_path = Path(excel_results_path)
        self.experiment_name = experiment_name
        self.description = description

        self.sensor_map = None
        self.experiment = None

        # Counters
        self.sensor_count = 0
        self.step_count = 0
        self.timeseries_count = 0

    def load_sensor_map(self):
        """Load sensor mapping from Excel"""
        print("Loading sensor map from Excel...")
        self.sensor_map = create_simple_sensor_map(str(self.excel_results_path))
        print(f"  [OK] Loaded {len(self.sensor_map)} sensor entries\n")

    def create_experiment(self, clear_existing=False):
        """Create or update experiment record"""
        # Parse first FRD for metadata
        frd_files = sorted(self.frd_directory.glob("*.frd"))
        if not frd_files:
            raise ValueError(f"No FRD files found in {self.frd_directory}")

        first_parser = FRDParser(str(frd_files[0]))
        exp_info = first_parser.get_experiment_info()

        # Clear existing if requested
        if clear_existing:
            existing = OctetExperiment.objects.filter(experiment_name=self.experiment_name)
            if existing.exists():
                print(f"[WARNING] Deleting existing experiment: {self.experiment_name}")
                existing.delete()
                print("  [OK] Deleted\n")

        # Create experiment
        print("Creating experiment record...")
        with transaction.atomic():
            self.experiment = OctetExperiment.objects.create(
                run_id=exp_info.get('run_id', f"{self.experiment_name}_{timezone.now().strftime('%Y%m%d')}"),
                experiment_name=self.experiment_name,
                experiment_type='KINETICS',
                experiment_subtype='KBASIC',
                description=self.description,
                experiment_datetime=exp_info.get('start_datetime', ''),
                start_datetime=timezone.now(),
                machine_name=exp_info.get('machine_name', ''),
                instrument_type=exp_info.get('instrument_type', ''),
                instrument_serial=exp_info.get('instrument_serial', ''),
                sensor_type=exp_info.get('sensor_type', ''),
                molar_conc_units='nM',
                user_name='',
                consolidated_file_path=str(self.excel_results_path),
                original_folder_path=str(self.frd_directory),
                imported_by='import_kinetics_data.py',
            )
        print(f"  [OK] Created: {self.experiment.experiment_name}\n")

    def import_frd_files(self):
        """Import all FRD files"""
        frd_files = sorted(self.frd_directory.glob("*.frd"))
        total_files = len(frd_files)

        print(f"{'='*80}")
        print(f"Processing {total_files} FRD files...")
        print(f"{'='*80}\n")

        for frd_idx, frd_file in enumerate(frd_files, 1):
            print(f"[{frd_idx}/{total_files}] {frd_file.name}")

            try:
                parser = FRDParser(str(frd_file))
                cycles = parser.get_all_cycles()

                print(f"  Found {len(cycles)} cycles")

                for cycle_idx, cycle in enumerate(cycles, 1):
                    self._process_cycle(cycle, frd_file.name)

                print(f"  [OK] Complete\n")

            except Exception as e:
                print(f"  [ERROR] {e}\n")
                continue

    def _process_cycle(self, cycle, frd_filename):
        """Process a single experimental cycle"""
        # Get sensor info from map
        antibody_id = cycle['antibody_id']
        concentration_nm = cycle['concentration_nm']
        key = (frd_filename, antibody_id, concentration_nm)

        sensor_info = self.sensor_map.get(key)
        if sensor_info is None:
            return

        # Create or get sensor record
        with transaction.atomic():
            sensor, created = OctetSensorData.objects.get_or_create(
                experiment=self.experiment,
                sensor_location=sensor_info['sensor_location'],
                loading_sample_id=antibody_id,
                concentration=concentration_nm,
                defaults={
                    'sensor_type': self.experiment.sensor_type,
                    'sample_id': sensor_info['analyte'],
                    'concentration_units': 'nM',
                    
                    
                }
            )

            if created:
                self.sensor_count += 1

            # Import kinetic analysis results
            if sensor_info['kd_m'] is not None:
                OctetKineticAnalysis.objects.get_or_create(
                    sensor=sensor,
                    defaults={
                        'analysis_method': '1_TO_1_BINDING',
                        'KD': sensor_info['kd_m'],
                        'kon': sensor_info['ka_1_ms'],
                        'koff': sensor_info['kdis_1_s'],
                        
                    }
                )

            # Create steps and time series
            self._create_steps(sensor, cycle, sensor_info)

    def _create_steps(self, sensor, cycle, sensor_info):
        """Create step data for a cycle"""
        antibody_id = cycle['antibody_id']
        concentration_nm = cycle['concentration_nm']

        # Track cumulative time offset for this sensor
        # Each new antibody/concentration combo resets to 0
        time_offset = 0

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
            self.step_count += 1

            if len(loading['time_array']) > 0:
                # Normalize to start at current offset (0 for first step)
                time_array = loading['time_array'].copy()
                time_array = time_array - time_array[0] + time_offset

                self.timeseries_count += self._create_timeseries(
                    loading_step,
                    time_array,
                    loading['signal_array'],
                    sensor_info['sensor_location'],
                    1
                )

                # Update offset for next step
                time_offset = time_array[-1]

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
            self.step_count += 1

            if len(baseline['time_array']) > 0:
                # Continue from loading
                time_array = baseline['time_array'].copy()
                time_array = time_array - time_array[0] + time_offset

                self.timeseries_count += self._create_timeseries(
                    baseline_step,
                    time_array,
                    baseline['signal_array'],
                    sensor_info['sensor_location'],
                    2
                )

                # Update offset
                time_offset = time_array[-1]

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
            self.step_count += 1

            # Get raw signal data - NO PROCESSING
            time_array = assoc['time_array'].copy()
            signal_array = assoc['signal_array'].copy()

            # Continue from baseline (maintain cumulative time)
            time_array = time_array - time_array[0] + time_offset

            # Store RAW signal data (no processing applied)
            self.timeseries_count += self._create_timeseries(
                assoc_step,
                time_array,
                signal_array,
                sensor_info['sensor_location'],
                3
            )

            # Update offset
            time_offset = time_array[-1]

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
            self.step_count += 1

            # Get raw signal data - NO PROCESSING
            time_array = dissoc['time_array'].copy()
            signal_array = dissoc['signal_array'].copy()

            # Continue from association (maintain cumulative time)
            time_array = time_array - time_array[0] + time_offset

            # Store RAW signal data (no processing applied)
            self.timeseries_count += self._create_timeseries(
                dissoc_step,
                time_array,
                signal_array,
                sensor_info['sensor_location'],
                4
            )

    def _create_timeseries(self, step, time_array, signal_array, sensor_location, step_number):
        """Create time series data points in bulk"""
        points = []

        for time_val, signal_val in zip(time_array, signal_array):
            points.append(
                OctetTimeSeriesData(
                    step=step,
                    run_id=self.experiment.run_id,
                    sensor_location=sensor_location,
                    step_number=step_number,
                    time=float(time_val),
                    response=float(signal_val),
                )
            )

        # Bulk create for efficiency
        OctetTimeSeriesData.objects.bulk_create(points, batch_size=1000)

        return len(points)

    def print_summary(self):
        """Print import summary"""
        print(f"\n{'='*80}")
        print("[OK] IMPORT COMPLETE")
        print(f"{'='*80}")
        print(f"Experiment:         {self.experiment.experiment_name}")
        print(f"Run ID:             {self.experiment.run_id}")
        print(f"Sensors imported:   {self.sensor_count}")
        print(f"Steps created:      {self.step_count}")
        print(f"Time series points: {self.timeseries_count:,}")
        print(f"{'='*80}\n")

    def run(self, clear_existing=False):
        """Run full import process"""
        try:
            self.load_sensor_map()
            self.create_experiment(clear_existing=clear_existing)
            self.import_frd_files()
            self.print_summary()
            return True
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main import function"""
    print(f"\n{'='*80}")
    print("OCTET KINETICS DATA IMPORT")
    print(f"{'='*80}\n")

    # Configuration
    frd_dir = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292"
    excel_results = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292\Results\ExcelReport_2025_10_15 13_27_15.xlsx"

    experiment_name = "OE292"
    description = "Kinetics experiment: 24 antibodies vs hsCD3d/e_Acro_CDD-H52W1"

    # Create importer
    importer = KineticsDataImporter(
        frd_directory=frd_dir,
        excel_results_path=excel_results,
        experiment_name=experiment_name,
        description=description
    )

    # Run import (clear existing data for this experiment)
    success = importer.run(clear_existing=True)

    if success:
        print("[OK] Data ready for Dash app!")
    else:
        print("[ERROR] Import failed!")


if __name__ == "__main__":
    main()




