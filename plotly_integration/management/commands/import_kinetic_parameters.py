"""
Management command to import kinetic parameters from Octet Excel reports

Usage:
    python manage.py import_kinetic_parameters <experiment_name> <excel_path>

Example:
    python manage.py import_kinetic_parameters OE292 "C:\...\ExcelReport_2025_10_15 13_27_15.xlsx"
"""

import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand, CommandError
from plotly_integration.models import OctetKineticsExperiment, OctetKineticsSensor


class Command(BaseCommand):
    help = 'Import kinetic parameters (Ka, Kd, Rmax, R²) from Octet Excel report'

    def add_arguments(self, parser):
        parser.add_argument(
            'experiment_name',
            type=str,
            help='Experiment name (e.g., OE292)'
        )
        parser.add_argument(
            'excel_path',
            type=str,
            help='Path to Excel report file'
        )
        parser.add_argument(
            '--sheet',
            type=str,
            default='Result Table',
            help='Sheet name with kinetic results (default: Result Table)'
        )

    def handle(self, *args, **options):
        experiment_name = options['experiment_name']
        excel_path = options['excel_path']
        sheet_name = options['sheet']

        self.stdout.write(f"\nImporting kinetic parameters for {experiment_name}")
        self.stdout.write(f"Excel file: {excel_path}")
        self.stdout.write(f"Sheet: {sheet_name}\n")

        # Get experiment
        try:
            experiment = OctetKineticsExperiment.objects.get(experiment_name=experiment_name)
            self.stdout.write(self.style.SUCCESS(f"Found experiment: {experiment}"))
        except OctetKineticsExperiment.DoesNotExist:
            raise CommandError(f"Experiment '{experiment_name}' not found in database")

        # Read Excel file
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            self.stdout.write(f"Loaded {len(df)} rows from Excel")
        except Exception as e:
            raise CommandError(f"Error reading Excel file: {e}")

        # Map column names
        column_map = {
            'Loading Sample ID': 'antibody_id',
            'Conc. (nM)': 'concentration_nm',
            'KD (M)': 'kd_m',
            'ka (1/Ms)': 'ka_1_ms',
            'kdis (1/s)': 'kdis_1_s',
            'Rmax': 'rmax',
            'Rmax Error': 'rmax_error',
            'Full R^2': 'r_squared',
            'ka Error': 'ka_error',
            'kdis Error': 'kdis_error',
            'KD Error': 'kd_error',
        }

        # Check required columns
        required_cols = ['Loading Sample ID', 'Conc. (nM)']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise CommandError(f"Missing required columns: {missing_cols}")

        # Update sensors
        updated = 0
        skipped = 0
        errors = []

        # Important: Kinetic parameters are GLOBAL FIT values (same for all concentrations)
        # We'll collect them per antibody and then apply to ALL sensors for that antibody
        antibody_kinetics = {}  # {antibody_id: {kd, ka, kdis, etc}}

        # First pass: collect kinetic parameters from Excel (one set per antibody)
        self.stdout.write("Collecting kinetic parameters from Excel...")

        for idx, row in df.iterrows():
            antibody_id = str(row['Loading Sample ID']).strip()

            # Skip if we already have kinetic data for this antibody
            if antibody_id in antibody_kinetics:
                continue

            # Extract kinetic parameters (these are GLOBAL FIT values)
            kinetics = {}

            # Handle KD
            kd_val = row.get('KD (M)')
            if pd.notna(kd_val):
                if isinstance(kd_val, str):
                    # Handle "<1.0E-12" format
                    if kd_val.startswith('<'):
                        kd_val = float(kd_val[1:])  # Remove '<' and convert
                    else:
                        kd_val = 0.0
                kinetics['kd_m'] = float(kd_val) if kd_val != 0.0 else None

            # Handle ka
            ka_val = row.get('ka (1/Ms)')
            if pd.notna(ka_val):
                if isinstance(ka_val, str) and ka_val.startswith('<'):
                    ka_val = float(ka_val[1:])
                kinetics['ka_1_ms'] = float(ka_val) if ka_val != 0.0 else None

            # Handle kdis
            kdis_val = row.get('kdis (1/s)')
            if pd.notna(kdis_val):
                if isinstance(kdis_val, str) and kdis_val.startswith('<'):
                    kdis_val = float(kdis_val[1:])
                kinetics['kdis_1_s'] = float(kdis_val) if kdis_val != 0.0 else None

            # Handle R² (global fit quality)
            r2_val = row.get('Full R^2')
            if pd.notna(r2_val):
                kinetics['r_squared'] = float(r2_val)

            # Store for this antibody
            if kinetics:
                antibody_kinetics[antibody_id] = kinetics

        self.stdout.write(f"Found kinetic parameters for {len(antibody_kinetics)} antibodies")

        # Second pass: Apply global kinetic parameters to ALL sensors for each antibody
        self.stdout.write("\nApplying kinetic parameters to all sensors...")

        for antibody_id, kinetics in antibody_kinetics.items():
            # Get ALL sensors for this antibody (all concentrations)
            sensors = OctetKineticsSensor.objects.filter(
                experiment=experiment,
                antibody_id=antibody_id
            )

            if not sensors.exists():
                msg = f"No sensors found for antibody: {antibody_id}"
                errors.append(msg)
                skipped += 1
                continue

            # Update all sensors with the same global fit values
            for sensor in sensors:
                # Apply global kinetic parameters
                for field, value in kinetics.items():
                    setattr(sensor, field, value)
                sensor.save()
                updated += 1

            if updated % 10 == 0:
                self.stdout.write(f"Updated {updated} sensors...")

        # Summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"Updated: {updated} sensors"))
        if skipped > 0:
            self.stdout.write(self.style.WARNING(f"Skipped: {skipped} sensors"))

        if errors:
            self.stdout.write("\nErrors:")
            for error in errors[:10]:  # Show first 10 errors
                self.stdout.write(self.style.ERROR(f"  - {error}"))
            if len(errors) > 10:
                self.stdout.write(f"  ... and {len(errors) - 10} more")

        self.stdout.write("="*60 + "\n")
