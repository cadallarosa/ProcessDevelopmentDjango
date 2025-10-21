"""
Management command to import kinetic parameters from Octet Excel reports

IMPORTANT:
- Kinetic parameters (KD, Ka, Kdis, R²) are GLOBAL FIT values - same for all concentrations
- Rmax is concentration-specific and will only be imported for concentrations in the Excel file

Usage:
    python manage.py import_kinetic_parameters_v2 <experiment_name> <excel_path>

Example:
    python manage.py import_kinetic_parameters_v2 OE292 "C:\...\ExcelReport_2025_10_15 13_27_15.xlsx"
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

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"Importing kinetic parameters for {experiment_name}")
        self.stdout.write(f"Excel file: {excel_path}")
        self.stdout.write(f"Sheet: {sheet_name}")
        self.stdout.write(f"{'='*60}\n")

        # Get experiment
        try:
            experiment = OctetKineticsExperiment.objects.get(experiment_name=experiment_name)
            self.stdout.write(self.style.SUCCESS(f"[OK] Found experiment: {experiment}"))
        except OctetKineticsExperiment.DoesNotExist:
            raise CommandError(f"Experiment '{experiment_name}' not found in database")

        # Read Excel file
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            self.stdout.write(f"[OK] Loaded {len(df)} rows from Excel\n")
        except Exception as e:
            raise CommandError(f"Error reading Excel file: {e}")

        # Check required columns
        required_cols = ['Loading Sample ID', 'Conc. (nM)']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise CommandError(f"Missing required columns: {missing_cols}")

        # Statistics
        global_updated = 0  # Global kinetic parameters
        rmax_updated = 0    # Rmax (concentration-specific)
        errors = []

        # STEP 1: Collect GLOBAL kinetic parameters (KD, Ka, Kdis, R²) per antibody
        self.stdout.write("Step 1: Collecting global kinetic parameters (KD, Ka, Kdis, R²)...")

        antibody_kinetics = {}  # {antibody_id: {kd, ka, kdis, r2}}

        for idx, row in df.iterrows():
            antibody_id = str(row['Loading Sample ID']).strip()

            # Skip if we already have kinetic data for this antibody
            if antibody_id in antibody_kinetics:
                continue

            # Extract GLOBAL kinetic parameters
            kinetics = {}

            # KD and error
            kd_val = row.get('KD (M)')
            if pd.notna(kd_val):
                if isinstance(kd_val, str) and kd_val.startswith('<'):
                    kd_val = float(kd_val[1:])
                elif isinstance(kd_val, str):
                    kd_val = 0.0
                if kd_val != 0.0:
                    kinetics['kd_m'] = float(kd_val)

            kd_error_val = row.get('KD Error')
            if pd.notna(kd_error_val) and kd_error_val != 0.0:
                kinetics['kd_error'] = float(kd_error_val)

            # Ka and error
            ka_val = row.get('ka (1/Ms)')
            if pd.notna(ka_val):
                if isinstance(ka_val, str) and ka_val.startswith('<'):
                    ka_val = float(ka_val[1:])
                if ka_val != 0.0:
                    kinetics['ka_1_ms'] = float(ka_val)

            ka_error_val = row.get('ka Error')
            if pd.notna(ka_error_val) and ka_error_val != 0.0:
                kinetics['ka_error'] = float(ka_error_val)

            # Kdis and error
            kdis_val = row.get('kdis (1/s)')
            if pd.notna(kdis_val):
                if isinstance(kdis_val, str) and kdis_val.startswith('<'):
                    kdis_val = float(kdis_val[1:])
                if kdis_val != 0.0:
                    kinetics['kdis_1_s'] = float(kdis_val)

            kdis_error_val = row.get('kdis Error')
            if pd.notna(kdis_error_val) and kdis_error_val != 0.0:
                kinetics['kdis_error'] = float(kdis_error_val)

            # R² (global fit quality)
            r2_val = row.get('Full R^2')
            if pd.notna(r2_val) and r2_val != 0.0:
                kinetics['r_squared'] = float(r2_val)

            # SSG parameters (steady-state global)
            ssg_kd_val = row.get('SSG KD')
            if pd.notna(ssg_kd_val) and ssg_kd_val != 0.0:
                kinetics['ssg_kd'] = float(ssg_kd_val)

            ssg_rmax_val = row.get('SSG Rmax')
            if pd.notna(ssg_rmax_val) and ssg_rmax_val != 0.0:
                kinetics['ssg_rmax'] = float(ssg_rmax_val)

            ssg_r2_val = row.get('SSG R^2')
            if pd.notna(ssg_r2_val) and ssg_r2_val != 0.0:
                kinetics['ssg_r_squared'] = float(ssg_r2_val)

            if kinetics:
                antibody_kinetics[antibody_id] = kinetics

        self.stdout.write(f"  - Found kinetic parameters for {len(antibody_kinetics)} antibodies\n")

        # STEP 2: Apply global kinetic parameters to ALL sensors for each antibody
        self.stdout.write("Step 2: Applying global kinetic parameters to all sensors...")

        for antibody_id, kinetics in antibody_kinetics.items():
            # Get ALL sensors for this antibody (all concentrations)
            sensors = OctetKineticsSensor.objects.filter(
                experiment=experiment,
                antibody_id=antibody_id
            )

            if not sensors.exists():
                errors.append(f"No sensors found for antibody: {antibody_id}")
                continue

            # Update all sensors with the same global fit values
            sensors.update(**kinetics)
            global_updated += sensors.count()

            if global_updated % 20 == 0:
                self.stdout.write(f"  - Updated {global_updated} sensors...")

        self.stdout.write(f"  - Applied global kinetics to {global_updated} sensors\n")

        # STEP 3: Import concentration-specific parameters
        self.stdout.write("Step 3: Importing concentration-specific parameters (Response, Rmax, kobs, Req, RSS)...")

        for idx, row in df.iterrows():
            antibody_id = str(row['Loading Sample ID']).strip()
            concentration_nm = float(row['Conc. (nM)'])

            # Find sensor with this exact concentration (with tolerance)
            try:
                sensor = OctetKineticsSensor.objects.get(
                    experiment=experiment,
                    antibody_id=antibody_id,
                    concentration_nm__gte=concentration_nm - 0.01,
                    concentration_nm__lte=concentration_nm + 0.01
                )

                # Collect concentration-specific parameters
                updates = {}

                # Response
                response_val = row.get('Response')
                if pd.notna(response_val) and response_val != 0.0:
                    updates['response'] = float(response_val)

                # Rmax and error
                rmax_val = row.get('Rmax')
                if pd.notna(rmax_val) and rmax_val != 0.0:
                    updates['rmax'] = float(rmax_val)

                rmax_error_val = row.get('Rmax Error')
                if pd.notna(rmax_error_val) and rmax_error_val != 0.0:
                    updates['rmax_error'] = float(rmax_error_val)

                # kobs and error
                kobs_val = row.get('kobs (1/s)')
                if pd.notna(kobs_val) and kobs_val != 0.0:
                    updates['kobs'] = float(kobs_val)

                kobs_error_val = row.get('kobs Error')
                if pd.notna(kobs_error_val) and kobs_error_val != 0.0:
                    updates['kobs_error'] = float(kobs_error_val)

                # Req
                req_val = row.get('Req')
                if pd.notna(req_val) and req_val != 0.0:
                    updates['req'] = float(req_val)

                # Req/Rmax(%)
                req_rmax_val = row.get('Req/Rmax(%)')
                if pd.notna(req_rmax_val) and req_rmax_val != 0.0:
                    updates['req_rmax_percent'] = float(req_rmax_val)

                # RSS
                rss_val = row.get('RSS')
                if pd.notna(rss_val) and rss_val != 0.0:
                    updates['rss'] = float(rss_val)

                # Apply updates if we have any
                if updates:
                    for field, value in updates.items():
                        setattr(sensor, field, value)
                    sensor.save(update_fields=list(updates.keys()))
                    rmax_updated += 1

                    if rmax_updated % 20 == 0:
                        self.stdout.write(f"  - Updated {rmax_updated} sensors...")

            except OctetKineticsSensor.DoesNotExist:
                # This is OK - concentration might not be in database
                pass
            except Exception as e:
                errors.append(f"Error updating parameters for {antibody_id} @ {concentration_nm} nM: {e}")

        self.stdout.write(f"  - Updated {rmax_updated} sensors with concentration-specific parameters\n")

        # Summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"[OK] Global kinetics updated: {global_updated} sensors"))
        self.stdout.write(self.style.SUCCESS(f"[OK] Concentration-specific parameters updated: {rmax_updated} sensors"))

        if errors:
            self.stdout.write(self.style.WARNING(f"\n[WARNING] Warnings: {len(errors)}"))
            for error in errors[:5]:
                self.stdout.write(f"  - {error}")
            if len(errors) > 5:
                self.stdout.write(f"  ... and {len(errors) - 5} more")

        self.stdout.write("="*60 + "\n")
