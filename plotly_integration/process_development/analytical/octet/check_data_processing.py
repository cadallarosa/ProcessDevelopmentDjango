"""
Check if data was processed during import

This script compares raw data from the Excel report with what's stored in the database
to determine if baseline subtraction was applied during import.
"""

import os
import sys
import django
from pathlib import Path
import pandas as pd
import numpy as np

# Setup Django environment
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from plotly_integration.models import (
    OctetExperiment,
    OctetSensorData,
    OctetStepData,
    OctetTimeSeriesData,
)

# Import FRD parser
kinetic_analysis_path = Path(__file__).parent / 'kinetic_analysis'
sys.path.insert(0, str(kinetic_analysis_path))
from frd_parser import FRDParser


def check_excel_data():
    """Load Excel to see what the vendor software shows"""
    excel_path = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292\Results\ExcelReport_2025_10_15 13_27_15.xlsx"

    print("="*80)
    print("CHECKING EXCEL REPORT DATA")
    print("="*80)

    # Load the Excel file
    try:
        # Try loading different sheets
        xl = pd.ExcelFile(excel_path)
        print(f"\nAvailable sheets: {xl.sheet_names}")

        # Load the first sheet
        df = pd.read_excel(excel_path, sheet_name=0)
        print(f"\nFirst sheet columns: {list(df.columns)[:10]}")
        print(f"First sheet shape: {df.shape}")
        print("\nFirst few rows:")
        print(df.head())

    except Exception as e:
        print(f"Error reading Excel: {e}")
        import traceback
        traceback.print_exc()


def check_frd_data():
    """Check raw FRD data"""
    frd_dir = Path(r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292")
    frd_files = sorted(frd_dir.glob("*.frd"))[:3]  # Just check first 3

    print("\n" + "="*80)
    print("CHECKING RAW FRD DATA")
    print("="*80)

    for frd_file in frd_files:
        print(f"\n{frd_file.name}:")
        try:
            parser = FRDParser(str(frd_file))
            cycles = parser.get_all_cycles()

            if cycles:
                cycle = cycles[0]  # First cycle
                print(f"  Antibody: {cycle['antibody_id']}")
                print(f"  Concentration: {cycle['concentration_nm']} nM")

                # Check association step
                if cycle['association_step']:
                    assoc = cycle['association_step']
                    print(f"\n  Association step:")
                    print(f"    Time range: {assoc['time_array'][0]:.1f}s - {assoc['time_array'][-1]:.1f}s")
                    print(f"    Signal range: {assoc['signal_array'].min():.4f} - {assoc['signal_array'].max():.4f} nm")
                    print(f"    First 5 signal values: {assoc['signal_array'][:5]}")

                # Check dissociation step
                if cycle['dissociation_step']:
                    dissoc = cycle['dissociation_step']
                    print(f"\n  Dissociation step:")
                    print(f"    Time range: {dissoc['time_array'][0]:.1f}s - {dissoc['time_array'][-1]:.1f}s")
                    print(f"    Signal range: {dissoc['signal_array'].min():.4f} - {dissoc['signal_array'].max():.4f} nm")
                    print(f"    First 5 signal values: {dissoc['signal_array'][:5]}")
                    print(f"    Last 5 signal values: {dissoc['signal_array'][-5:]}")

        except Exception as e:
            print(f"  Error: {e}")


def check_database_data():
    """Check what's stored in the database"""
    print("\n" + "="*80)
    print("CHECKING DATABASE DATA")
    print("="*80)

    try:
        experiment = OctetExperiment.objects.get(experiment_name="OE292")
        print(f"\nExperiment: {experiment.experiment_name}")
        print(f"Run ID: {experiment.run_id}")

        # Get a single sensor
        sensor = OctetSensorData.objects.filter(experiment=experiment).first()
        print(f"\nFirst sensor:")
        print(f"  Antibody: {sensor.loading_sample_id}")
        print(f"  Concentration: {sensor.concentration} nM")
        print(f"  Location: {sensor.sensor_location}")

        # Check association step
        assoc_step = OctetStepData.objects.filter(
            sensor=sensor,
            step_type='ASSOC'
        ).first()

        if assoc_step:
            print(f"\n  Association step in DB:")
            assoc_data = OctetTimeSeriesData.objects.filter(
                step=assoc_step
            ).order_by('time')

            times = [d.time for d in assoc_data]
            responses = [d.response for d in assoc_data]

            print(f"    Time range: {min(times):.1f}s - {max(times):.1f}s")
            print(f"    Response range: {min(responses):.4f} - {max(responses):.4f} nm")
            print(f"    First 5 response values: {responses[:5]}")
            print(f"    Last 5 response values: {responses[-5:]}")

        # Check dissociation step
        dissoc_step = OctetStepData.objects.filter(
            sensor=sensor,
            step_type='DISSOC'
        ).first()

        if dissoc_step:
            print(f"\n  Dissociation step in DB:")
            dissoc_data = OctetTimeSeriesData.objects.filter(
                step=dissoc_step
            ).order_by('time')

            times = [d.time for d in dissoc_data]
            responses = [d.response for d in dissoc_data]

            print(f"    Time range: {min(times):.1f}s - {max(times):.1f}s")
            print(f"    Response range: {min(responses):.4f} - {max(responses):.4f} nm")
            print(f"    First 5 response values: {responses[:5]}")
            print(f"    Last 5 response values: {responses[-5:]}")

    except OctetExperiment.DoesNotExist:
        print("\nExperiment OE292 not found in database!")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("\n" + "="*80)
    print("DATA PROCESSING VERIFICATION")
    print("="*80)
    print("\nThis script checks if baseline subtraction was applied during import")
    print("by comparing raw FRD data with what's in the database.")

    check_excel_data()
    check_frd_data()
    check_database_data()

    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    print("""
The import script (import_kinetics_data.py) applies processing via process_sensor_data():

Lines 274-279 (Association):
    signal_array = process_sensor_data(
        signal_array,
        time_array,
        baseline_window=(50, 100),
        apply_filter=True
    )

Lines 313-317 (Dissociation):
    signal_array = process_sensor_data(
        signal_array,
        time_array,
        apply_filter=True
    )

This function (signal_processing.py):
1. Baseline alignment - subtracts the average of the baseline window
2. Savitzky-Golay filtering - smooths the data

This means:
- Association: Baseline-aligned to (50-100s window) then filtered
- Dissociation: Baseline-aligned to first points then filtered

The Excel report from the vendor software likely shows:
- Raw data OR vendor-processed data (with reference subtraction)
- Dissociation may reset to 0 at the transition

Our database stores PROCESSED data, not raw data!
    """)


if __name__ == "__main__":
    main()
