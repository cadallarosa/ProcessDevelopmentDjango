"""
Method-Based Sensor Mapper

Creates sensor mapping from experimental method file (oe292_method.xlsx)
instead of vendor-processed Excel results.

This allows us to:
1. Import reference wells (not present in results)
2. Map directly from FRD cycles to expected sensors
3. Avoid dependency on vendor's data processing
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, List


def create_method_sensor_map(method_excel_path: str) -> Dict[Tuple[str, str, float], Dict]:
    """
    Create sensor mapping from method Excel file

    The method file contains:
    - SamplePlate1: Plate layout with well IDs
    - AssaySteps: Which wells are used for each step per cycle
    - Loaded Proteins: Antibody info

    Args:
        method_excel_path: Path to oe292_method.xlsx

    Returns:
        Dictionary with keys: (frd_filename, antibody_id, concentration_nm)
        Values contain sensor info including reference well designation
    """
    # Read relevant sheets
    sample_plate = pd.read_excel(method_excel_path, sheet_name='SamplePlate1')
    assay_steps = pd.read_excel(method_excel_path, sheet_name='AssaySteps')

    # Create well lookup: well -> sample info
    well_lookup = {}
    for _, row in sample_plate.iterrows():
        well = row['Well']
        well_lookup[well] = {
            'id': row['ID'],
            'group': row['Group'],
            'concentration_m': row['Molar Concentration (M)'],
            'is_reference': row['Group'] == 'Buffer' and row['ID'] == 'Octet Buffer',
            'is_sample': row['Group'] == 'Sample',
            'is_load': row['Group'] == 'Load',
        }

    # Map FRD files to sensor locations
    # Each FRD file = 1 sensor with multiple cycles
    # File numbering: 251013_001.frd through 251013_016.frd (16 sensors)
    frd_files = [f"251013_{i:03d}.frd" for i in range(1, 17)]

    # Sensor locations on Octet 16-channel instrument
    # t1 = Tray 1, Columns 11-12, Rows A-H
    sensor_locations = [
        't1A11', 't1B11', 't1C11', 't1D11', 't1E11', 't1F11', 't1G11', 't1H11',  # Column 11
        't1A12', 't1B12', 't1C12', 't1D12', 't1E12', 't1F12', 't1G12', 't1H12',  # Column 12
    ]

    sensor_map = {}

    # Process assay steps to get loading info per cycle
    cycle_columns = [c for c in assay_steps.columns if c != 'Cycle']

    for cycle_num, cycle_col in enumerate(cycle_columns, 1):
        # Get the loading well for this cycle
        loading_well = assay_steps.loc[assay_steps['Cycle'] == 'Loading', cycle_col].values[0]
        loading_info = well_lookup.get(loading_well)

        if not loading_info or not loading_info['is_load']:
            continue

        antibody_id = loading_info['id']

        # Get association well (contains analyte at different concentrations)
        assoc_well = assay_steps.loc[assay_steps['Cycle'] == 'Association', cycle_col].values[0]
        assoc_info = well_lookup.get(assoc_well)

        if not assoc_info or not assoc_info['is_sample']:
            continue

        analyte_id = assoc_info['id']
        concentration_m = assoc_info['concentration_m']
        concentration_nm = concentration_m * 1e9  # Convert M to nM

        # Get baseline well (reference)
        baseline_well = assay_steps.loc[assay_steps['Cycle'] == 'Baseline', cycle_col].values[0]
        baseline_info = well_lookup.get(baseline_well)

        # Map to FRD file and sensor location
        frd_filename = frd_files[cycle_num - 1]
        sensor_location = sensor_locations[cycle_num - 1]

        # Create composite key
        key = (frd_filename, antibody_id, concentration_nm)

        # Store sensor info
        sensor_map[key] = {
            'frd_file': frd_filename,
            'sensor_location': sensor_location,
            'antibody': antibody_id,
            'analyte': analyte_id,
            'concentration_nm': concentration_nm,
            'loading_well': loading_well,
            'baseline_well': baseline_well,
            'association_well': assoc_well,
            'cycle_number': cycle_num,
            'is_sample': True,
            'is_reference': False,
            'reference_well': baseline_well,  # Reference well for this sensor
        }

    # Add reference well entries
    # Reference wells are measured in the FRD files during baseline/dissociation steps
    # They need to be imported so we can do reference subtraction
    reference_wells = ['A1', 'A3']  # From SamplePlate1

    for ref_well in reference_wells:
        ref_info = well_lookup.get(ref_well)
        if ref_info and ref_info['is_reference']:
            # Reference wells appear in multiple FRD files
            # We'll create one entry per FRD file to capture all reference data
            for frd_idx, frd_filename in enumerate(frd_files, 1):
                sensor_location = sensor_locations[frd_idx - 1]

                key = (frd_filename, ref_info['id'], 0.0)  # Concentration = 0 for buffer

                sensor_map[key] = {
                    'frd_file': frd_filename,
                    'sensor_location': sensor_location + '_ref',  # Mark as reference
                    'antibody': ref_info['id'],
                    'analyte': 'Buffer',
                    'concentration_nm': 0.0,
                    'loading_well': None,
                    'baseline_well': ref_well,
                    'association_well': ref_well,
                    'cycle_number': frd_idx,
                    'is_sample': False,
                    'is_reference': True,
                    'reference_well': None,  # References don't have references
                }

    return sensor_map


def get_reference_well_for_sensor(sensor_map: Dict, frd_file: str, antibody_id: str, concentration_nm: float) -> str:
    """
    Get the reference well ID for a given sensor

    Args:
        sensor_map: Sensor mapping dictionary
        frd_file: FRD filename
        antibody_id: Antibody ID
        concentration_nm: Concentration in nM

    Returns:
        Reference well ID (e.g., 'A1') or None
    """
    key = (frd_file, antibody_id, concentration_nm)
    sensor_info = sensor_map.get(key)
    if sensor_info:
        return sensor_info.get('reference_well')
    return None


def get_all_reference_sensors(sensor_map: Dict) -> List[Dict]:
    """
    Get list of all reference sensor entries

    Args:
        sensor_map: Sensor mapping dictionary

    Returns:
        List of reference sensor info dicts
    """
    references = []
    for key, info in sensor_map.items():
        if info['is_reference']:
            references.append(info)
    return references


def get_all_sample_sensors(sensor_map: Dict) -> List[Dict]:
    """
    Get list of all sample sensor entries

    Args:
        sensor_map: Sensor mapping dictionary

    Returns:
        List of sample sensor info dicts
    """
    samples = []
    for key, info in sensor_map.items():
        if info['is_sample']:
            samples.append(info)
    return samples


if __name__ == "__main__":
    # Test
    method_path = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292\oe292_method.xlsx"

    print("Creating sensor map from method file...")
    sensor_map = create_method_sensor_map(method_path)

    print(f"\nTotal entries in sensor map: {len(sensor_map)}")

    # Count samples vs references
    samples = get_all_sample_sensors(sensor_map)
    references = get_all_reference_sensors(sensor_map)

    print(f"Sample sensors: {len(samples)}")
    print(f"Reference sensors: {len(references)}")

    # Show first few samples
    print("\nFirst 3 sample sensors:")
    for i, sample in enumerate(samples[:3], 1):
        print(f"{i}. {sample['antibody']} @ {sample['concentration_nm']} nM")
        print(f"   FRD: {sample['frd_file']}, Location: {sample['sensor_location']}")
        print(f"   Reference well: {sample['reference_well']}")

    # Show first reference
    if references:
        print("\nFirst reference sensor:")
        ref = references[0]
        print(f"   {ref['antibody']}")
        print(f"   FRD: {ref['frd_file']}, Location: {ref['sensor_location']}")
        print(f"   Well: {ref['baseline_well']}")
