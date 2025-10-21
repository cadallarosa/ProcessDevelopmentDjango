"""
Export FRD Data to Excel for Analysis

This script exports raw FRD data to Excel format so we can analyze
the structure and understand how samples are organized across steps.
"""

import pandas as pd
import os
from frd_importer import FRDImporter


def export_frd_to_excel(frd_file_path: str, output_excel_path: str):
    """
    Export FRD data to Excel with separate sheets for metadata and steps

    Args:
        frd_file_path: Path to .frd file
        output_excel_path: Path for output Excel file
    """
    print(f"Parsing FRD file: {frd_file_path}")
    importer = FRDImporter(frd_file_path)

    # Get experiment info
    exp_info = importer.parse_experiment_info()
    sensor_location = importer.parse_sensor_location()

    # Get all steps
    steps = importer.parse_steps()

    print(f"Found {len(steps)} steps for sensor {sensor_location}")

    # Create DataFrames

    # 1. Experiment metadata sheet
    exp_df = pd.DataFrame([exp_info])

    # 2. Step summary sheet (without time series data)
    step_summary = []
    for step in steps:
        summary = {
            'step_number': step['step_number'],
            'step_name': step.get('step_name', ''),
            'step_type': step.get('step_type', ''),
            'sample_location': step.get('sample_location', ''),
            'sample_id': step.get('sample_id', ''),
            'sample_group': step.get('sample_group', ''),
            'sample_info': step.get('sample_info', ''),
            'well_type': step.get('well_type', ''),
            'concentration': step.get('concentration'),
            'concentration_units': step.get('concentration_units', ''),
            'temperature': step.get('temperature'),
            'start_time': step.get('start_time'),
            'assay_time': step.get('assay_time'),
            'actual_time': step.get('actual_time'),
            'num_time_points': step.get('num_points', 0),
        }
        step_summary.append(summary)

    step_summary_df = pd.DataFrame(step_summary)

    # 3. Time series data for first few steps (sample)
    time_series_sheets = {}
    for i, step in enumerate(steps[:10]):  # Export first 10 steps as examples
        if step.get('num_points', 0) > 0:
            ts_df = pd.DataFrame({
                'time': step['time_data'],
                'response': step['response_data']
            })
            time_series_sheets[f"Step_{step['step_number']}_TimeSeries"] = ts_df

    # Write to Excel
    print(f"Writing to Excel: {output_excel_path}")
    with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
        exp_df.to_excel(writer, sheet_name='Experiment_Info', index=False)
        step_summary_df.to_excel(writer, sheet_name='Step_Summary', index=False)

        for sheet_name, ts_df in time_series_sheets.items():
            ts_df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"[OK] Export complete!")
    print(f"  - Sensor: {sensor_location}")
    print(f"  - Total steps: {len(steps)}")
    print(f"  - Sheets: Experiment_Info, Step_Summary, + {len(time_series_sheets)} time series samples")


def export_all_sensors_summary(experiment_folder: str, output_excel_path: str):
    """
    Export summary of all sensors in experiment to a single Excel file

    Args:
        experiment_folder: Path to folder with FRD files
        output_excel_path: Path for output Excel file
    """
    # Find all FRD files
    frd_files = []
    for file in os.listdir(experiment_folder):
        if file.endswith('.frd') and not file.startswith('HTSettings'):
            frd_files.append(os.path.join(experiment_folder, file))

    frd_files.sort()

    print(f"Found {len(frd_files)} FRD files")

    all_steps = []

    # Parse each file
    for frd_file in frd_files:
        print(f"Processing {os.path.basename(frd_file)}...")
        importer = FRDImporter(frd_file)
        sensor_location = importer.parse_sensor_location()
        steps = importer.parse_steps()

        # Add sensor location to each step
        for step in steps:
            step['sensor_location'] = sensor_location
            step['frd_file'] = os.path.basename(frd_file)
            all_steps.append({
                'sensor_location': sensor_location,
                'frd_file': os.path.basename(frd_file),
                'step_number': step['step_number'],
                'step_name': step.get('step_name', ''),
                'step_type': step.get('step_type', ''),
                'sample_location': step.get('sample_location', ''),
                'sample_id': step.get('sample_id', ''),
                'sample_group': step.get('sample_group', ''),
                'sample_info': step.get('sample_info', ''),
                'well_type': step.get('well_type', ''),
                'concentration': step.get('concentration'),
                'concentration_units': step.get('concentration_units', ''),
                'temperature': step.get('temperature'),
                'start_time': step.get('start_time'),
                'assay_time': step.get('assay_time'),
                'actual_time': step.get('actual_time'),
                'num_time_points': step.get('num_points', 0),
            })

    # Create DataFrame
    df = pd.DataFrame(all_steps)

    # Write to Excel
    print(f"\nWriting to Excel: {output_excel_path}")
    with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='All_Steps', index=False)

        # Also create a pivot showing unique samples per sensor
        sample_pivot = df.groupby(['sensor_location', 'sample_id']).size().reset_index(name='step_count')
        sample_pivot.to_excel(writer, sheet_name='Samples_Per_Sensor', index=False)

    print(f"[OK] Export complete!")
    print(f"  - Total sensors: {df['sensor_location'].nunique()}")
    print(f"  - Total steps: {len(df)}")
    print(f"  - Unique samples: {df['sample_id'].nunique()}")


if __name__ == '__main__':
    # Export single FRD file
    single_frd = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292\251013_001.frd"
    single_output = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292\FRD_Analysis_Single_Sensor.xlsx"

    export_frd_to_excel(single_frd, single_output)

    print("\n" + "="*80 + "\n")

    # Export all sensors summary
    experiment_folder = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292"
    all_sensors_output = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292\FRD_Analysis_All_Sensors.xlsx"

    export_all_sensors_summary(experiment_folder, all_sensors_output)
