"""
Django Management Command: Import Octet Kinetics Data (Optimized Version)

This script imports kinetics data into the new optimized OctetKinetics models:
- OctetKineticsExperiment (one per experiment)
- OctetKineticsSensor (one per antibody×concentration with JSON time series)

Usage:
    python manage.py import_kinetics --experiment_name OE292 --data_dir <path>

Features:
- Stores complete time series as JSON (loading, baseline, association, dissociation)
- Tracks all well locations for data integrity
- Automatically identifies reference sensors (0.0 nM)
- Parses HTSettings.efrd for processing parameters
- Uses FRD_Analysis.xlsx for sample mapping
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import pandas as pd

from plotly_integration.models import OctetKineticsExperiment, OctetKineticsSensor


class KineticsImporter:
    """Import logic for Octet Kinetics data"""

    def __init__(self, experiment_name, data_dir, description='', created_by='admin', stdout=None):
        self.experiment_name = experiment_name
        self.data_dir = Path(data_dir)
        self.description = description
        self.created_by = created_by
        self.stdout = stdout or sys.stdout

    def log(self, message, style=None):
        """Print message with optional style"""
        if hasattr(self.stdout, 'write'):
            if style and hasattr(self.stdout, 'style'):
                self.stdout.write(getattr(self.stdout.style, style.upper())(message))
            else:
                self.stdout.write(message)
        else:
            print(message)

    def import_data(self, clear_existing=False):
        """Main import process"""

        # Validate data directory
        if not self.data_dir.exists():
            raise ValueError(f"Data directory not found: {self.data_dir}")

        self.log("=" * 80)
        self.log(f"OCTET KINETICS DATA IMPORT: {self.experiment_name}", 'success')
        self.log("=" * 80)
        self.log(f"Data directory: {self.data_dir}")
        self.log(f"Created by: {self.created_by}")

        # Check for required files
        analysis_excel = self.data_dir / "FRD_Analysis.xlsx"
        ht_settings = self.data_dir / "HTSettings.efrd"

        if not analysis_excel.exists():
            raise ValueError(f"FRD_Analysis.xlsx not found in {self.data_dir}")

        if not ht_settings.exists():
            self.log("HTSettings.efrd not found - using defaults", 'warning')

        # Clear existing data if requested
        if clear_existing:
            existing = OctetKineticsExperiment.objects.filter(experiment_name=self.experiment_name)
            if existing.exists():
                sensors_count = OctetKineticsSensor.objects.filter(
                    experiment__experiment_name=self.experiment_name
                ).count()
                self.log(f"Deleting existing experiment and {sensors_count} sensors...", 'warning')
                existing.delete()
                self.log("Existing data cleared", 'success')

        # Load FRD Analysis Excel
        self.log("\n" + "=" * 80)
        self.log("LOADING FRD_Analysis.xlsx")
        self.log("=" * 80)

        xl_file = pd.ExcelFile(analysis_excel)
        df_all_cycles = pd.read_excel(xl_file, sheet_name='All_Cycles')

        self.log(f"Total cycles: {len(df_all_cycles)}")
        self.log(f"Unique antibodies: {df_all_cycles['Antibody_ID'].nunique()}")
        self.log(f"Unique concentrations: {df_all_cycles['Concentration_nM'].nunique()}")

        # Parse HTSettings
        ht_params = self._parse_ht_settings(ht_settings)

        # Create experiment
        experiment = self._create_experiment(ht_params, analysis_excel, ht_settings)

        # Import sensors
        sensors_created, errors = self._import_sensors(experiment, df_all_cycles)

        # Link reference sensors
        self._link_reference_sensors(experiment)

        # Print summary
        self._print_summary(experiment, sensors_created, errors)

        return experiment

    def _parse_ht_settings(self, ht_settings):
        """Parse HTSettings.efrd file"""
        ht_params = {}

        if ht_settings.exists():
            self.log("\n" + "=" * 80)
            self.log("PARSING HTSettings.efrd")
            self.log("=" * 80)

            # Import parser from same module
            from .htsettings_parser import parse_ht_settings
            ht_params = parse_ht_settings(str(ht_settings))

            self.log(f"Binding Model: {ht_params.get('binding_model')}")
            self.log(f"Association: {ht_params.get('assoc_start_time')}-{ht_params.get('assoc_end_time')} s")
            self.log(f"Dissociation: {ht_params.get('dissoc_start_time')}-{ht_params.get('dissoc_end_time')} s")

        return ht_params

    def _create_experiment(self, ht_params, analysis_excel, ht_settings):
        """Create OctetKineticsExperiment record"""
        self.log("\n" + "=" * 80)
        self.log("CREATING EXPERIMENT")
        self.log("=" * 80)

        with transaction.atomic():
            experiment = OctetKineticsExperiment.objects.create(
                run_id=ht_params.get('run_id', f"{self.experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                experiment_name=self.experiment_name,
                description=self.description,
                experiment_type='KINETICS',
                experiment_subtype='KBASIC',
                start_datetime=datetime.now(),

                # HTSettings parameters
                binding_model=ht_params.get('binding_model', 'FastOne2One'),
                fit_type=ht_params.get('fit_type', 'Global'),
                steps_to_analyze=ht_params.get('steps_to_analyze', 'Both'),

                assoc_start_time=ht_params.get('assoc_start_time', 0.0),
                assoc_end_time=ht_params.get('assoc_end_time', 180.0),
                assoc_start_pt=ht_params.get('assoc_start_pt', 0),
                assoc_end_pt=ht_params.get('assoc_end_pt', 900),

                dissoc_start_time=ht_params.get('dissoc_start_time', 0.0),
                dissoc_end_time=ht_params.get('dissoc_end_time', 60.0),
                dissoc_start_pt=ht_params.get('dissoc_start_pt', 0),
                dissoc_end_pt=ht_params.get('dissoc_end_pt', 300),

                delta_t=ht_params.get('delta_t', 0.2),
                sampling_rate_hz=1.0 / ht_params.get('delta_t', 0.2) if ht_params.get('delta_t') else 5.0,

                fit_group_by=ht_params.get('fit_group_by', 'Color'),
                rmax_unlink=ht_params.get('rmax_unlink', 'Sensor'),

                concentration_units='nM',
                response_units='nm',

                original_folder_path=str(self.data_dir),
                ht_settings_path=str(ht_settings) if ht_settings.exists() else '',
                analysis_excel_path=str(analysis_excel),

                imported_by=self.created_by
            )

            self.log(f"Created experiment: {experiment}", 'success')
            return experiment

    def _import_sensors(self, experiment, df_all_cycles):
        """Import sensor data from FRD files"""
        self.log("\n" + "=" * 80)
        self.log("IMPORTING SENSORS")
        self.log("=" * 80)

        # Import FRD parser from same module
        from .frd_parser import FRDParser

        sensors_created = 0
        errors = []

        # Group by unique sensor (antibody × concentration)
        grouped = df_all_cycles.groupby(['Antibody_ID', 'Concentration_nM'])
        total_sensors = len(grouped)

        self.log(f"Importing {total_sensors} sensors...")

        for idx, ((antibody_id, concentration_nm), group) in enumerate(grouped, 1):
            # Use first row for this sensor
            row = group.iloc[0]

            try:
                # Parse FRD file to get time series data
                frd_path = self.data_dir / row['FRD_File']

                if not frd_path.exists():
                    errors.append(f"FRD file not found: {frd_path}")
                    continue

                parser = FRDParser(str(frd_path))
                cycles = parser.get_all_cycles()

                # Find the cycle for this antibody
                cycle_number = int(row['Cycle_Number'])
                if cycle_number > len(cycles):
                    errors.append(f"Cycle {cycle_number} not found in {row['FRD_File']}")
                    continue

                cycle = cycles[cycle_number - 1]  # 0-indexed

                # Extract time series from cycle
                loading_step = cycle.get('loading_step', {})
                baseline_step = cycle.get('baseline_step', {})
                assoc_step = cycle.get('association_step', {})
                dissoc_step = cycle.get('dissociation_step', {})

                # Convert to JSON format
                loading_data = {}
                if loading_step and 'time_array' in loading_step:
                    loading_data = {
                        'time': loading_step['time_array'].tolist(),
                        'response': loading_step['signal_array'].tolist()
                    }

                baseline_data = {}
                if baseline_step and 'time_array' in baseline_step:
                    baseline_data = {
                        'time': baseline_step['time_array'].tolist(),
                        'response': baseline_step['signal_array'].tolist()
                    }

                association_data = {}
                if assoc_step and 'time_array' in assoc_step:
                    association_data = {
                        'time': assoc_step['time_array'].tolist(),
                        'response': assoc_step['signal_array'].tolist()
                    }

                dissociation_data = {}
                if dissoc_step and 'time_array' in dissoc_step:
                    dissociation_data = {
                        'time': dissoc_step['time_array'].tolist(),
                        'response': dissoc_step['signal_array'].tolist()
                    }

                # Create sensor
                sensor = OctetKineticsSensor.objects.create(
                    experiment=experiment,

                    # Sensor identification
                    sensor_location=cycle.get('sensor_location', ''),
                    frd_file=row['FRD_File'],
                    frd_number=int(row['FRD_Number']),
                    cycle_number=cycle_number,

                    # Sample identification
                    antibody_id=antibody_id,
                    analyte_id=str(row['Analyte_ID']),
                    concentration_nm=float(concentration_nm),

                    # Well locations
                    loading_sample=str(row['Loading_Sample']),
                    loading_well=str(row['Loading_Well']),
                    baseline_sample=str(row.get('Baseline_Sample', '')),
                    baseline_well=str(row.get('Baseline_Well', '')),
                    association_sample=str(row.get('Association_Sample', '')),
                    association_well=str(row.get('Association_Well', '')),
                    dissociation_well=str(row.get('Dissociation_Well', '')),

                    # Reference tracking
                    is_reference=(concentration_nm == 0.0),

                    # Data point counts
                    loading_points=int(row.get('Loading_Points', 0)),
                    baseline_points=int(row.get('Baseline_Points', 0)),
                    association_points=int(row.get('Association_Points', 0)),
                    dissociation_points=int(row.get('Dissociation_Points', 0)),
                    total_points=int(row.get('Total_Points', 0)),

                    # Time series data (JSON)
                    loading_data=loading_data,
                    baseline_data=baseline_data,
                    association_data=association_data,
                    dissociation_data=dissociation_data,

                    # Time ranges
                    assoc_time_start=float(row.get('Assoc_Time_Start', 0.0)),
                    assoc_time_end=float(row.get('Assoc_Time_End', 0.0))
                )

                sensors_created += 1

                # Progress reporting
                if sensors_created % 10 == 0 or sensors_created == total_sensors:
                    self.log(f"  Progress: {sensors_created}/{total_sensors} ({100*sensors_created//total_sensors}%)")

            except Exception as e:
                error_msg = f"Error importing {antibody_id} @ {concentration_nm} nM: {str(e)}"
                errors.append(error_msg)
                self.log(f"  [{idx}/{total_sensors}] {error_msg}", 'error')
                continue

        return sensors_created, errors

    def _link_reference_sensors(self, experiment):
        """Link sample sensors to their reference sensors"""
        self.log("\n" + "=" * 80)
        self.log("LINKING REFERENCE SENSORS")
        self.log("=" * 80)

        # For each antibody, find its reference sensor (0.0 nM) and link it
        for antibody_id in OctetKineticsSensor.objects.filter(
            experiment=experiment
        ).values_list('antibody_id', flat=True).distinct():

            # Find reference for this antibody
            try:
                ref_sensor = OctetKineticsSensor.objects.get(
                    experiment=experiment,
                    antibody_id=antibody_id,
                    concentration_nm=0.0
                )

                # Link all non-reference sensors to this reference
                sample_sensors = OctetKineticsSensor.objects.filter(
                    experiment=experiment,
                    antibody_id=antibody_id,
                    is_reference=False
                )

                sample_sensors.update(reference_sensor=ref_sensor)
                self.log(f"  Linked {sample_sensors.count()} samples to reference: {antibody_id}")

            except OctetKineticsSensor.DoesNotExist:
                self.log(f"  No reference sensor found for {antibody_id}", 'warning')

    def _print_summary(self, experiment, sensors_created, errors):
        """Print import summary"""
        self.log("\n" + "=" * 80)
        self.log("IMPORT COMPLETE", 'success')
        self.log("=" * 80)
        self.log(f"Experiment: {experiment.experiment_name}")
        self.log(f"Sensors created: {sensors_created}")
        self.log(f"Reference sensors: {OctetKineticsSensor.objects.filter(experiment=experiment, is_reference=True).count()}")
        self.log(f"Sample sensors: {OctetKineticsSensor.objects.filter(experiment=experiment, is_reference=False).count()}")

        if errors:
            self.log("\n" + "=" * 80)
            self.log(f"ERRORS ({len(errors)})", 'warning')
            self.log("=" * 80)
            for error in errors[:10]:  # Show first 10 errors
                self.log(f"  {error}", 'error')
            if len(errors) > 10:
                self.log(f"  ... and {len(errors) - 10} more errors", 'warning')

        self.log("")


# Standalone function for external use
def import_kinetics_data(experiment_name, data_dir, description='', created_by='admin', clear_existing=False):
    """
    Import Octet kinetics data from FRD files

    Args:
        experiment_name: Name for the experiment (e.g., 'OE292')
        data_dir: Path to directory containing FRD files and FRD_Analysis.xlsx
        description: Optional experiment description
        created_by: Username of person importing
        clear_existing: Whether to delete existing data for this experiment

    Returns:
        OctetKineticsExperiment object
    """
    importer = KineticsImporter(experiment_name, data_dir, description, created_by)
    return importer.import_data(clear_existing=clear_existing)
