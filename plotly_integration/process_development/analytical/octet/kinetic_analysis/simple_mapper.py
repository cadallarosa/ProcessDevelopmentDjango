"""
Simple Sensor Mapper

Creates a straightforward mapping from (FRD file, antibody_id, concentration)
to kinetic parameters directly from the Excel file.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Tuple


def create_simple_sensor_map(excel_path: str) -> Dict[Tuple[str, str, float], Dict]:
    """
    Create simple mapping from (FRD filename, antibody_id, concentration) to sample info

    Args:
        excel_path: Path to Excel results file

    Returns:
        Dictionary with keys: (frd_filename, antibody_id, concentration_nm)
    """
    df = pd.read_excel(excel_path, sheet_name='Result Table')

    sensor_map = {}

    for _, row in df.iterrows():
        # Extract FRD filename from file location
        file_loc = row['File location']
        if pd.isna(file_loc):
            continue

        frd_filename = Path(file_loc).name

        # Get antibody and concentration
        antibody_id = row['Loading Sample ID']
        concentration_nm = row['Conc. (nM)']

        if pd.isna(antibody_id) or pd.isna(concentration_nm):
            continue

        # Create composite key
        key = (frd_filename, antibody_id, concentration_nm)

        # Store sample info
        sensor_map[key] = {
            'frd_file': frd_filename,
            'antibody': antibody_id,
            'analyte': row['Sample ID'],
            'concentration_nm': concentration_nm,
            'sensor_location': row['Sensor Location'],
            'color': row['Color'],
            'kd_m': _safe_float(row['KD (M)']),
            'ka_1_ms': _safe_float(row['ka (1/Ms)']),
            'kdis_1_s': _safe_float(row['kdis (1/s)']),
            'r_squared': _safe_float(row['Full R^2']),
            'loading_response': _safe_float(row['Loading Response']),
        }

    return sensor_map


def _safe_float(value):
    """Safely convert value to float, handling strings like '<1.0E-12'"""
    if pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        # Handle strings like '<1.0E-12' or '>1.0E-6'
        value = value.strip()
        if value.startswith('<') or value.startswith('>'):
            try:
                return float(value[1:])
            except:
                return None
        try:
            return float(value)
        except:
            return None

    return None


def get_all_antibodies(sensor_map: Dict) -> list:
    """Get list of all unique antibodies"""
    antibodies = set()
    for key, info in sensor_map.items():
        antibodies.add(info['antibody'])
    return sorted(list(antibodies))


def get_antibody_kinetics(sensor_map: Dict, antibody_id: str) -> Dict:
    """
    Get averaged kinetic parameters for an antibody

    Args:
        sensor_map: Sensor map dictionary
        antibody_id: Antibody ID

    Returns:
        Dictionary with averaged KD, ka, kdis, R2
    """
    import numpy as np

    kd_values = []
    ka_values = []
    kdis_values = []
    r2_values = []

    for key, info in sensor_map.items():
        if info['antibody'] == antibody_id:
            if info['kd_m'] is not None and info['kd_m'] > 0:
                kd_values.append(info['kd_m'])
            if info['ka_1_ms'] is not None and info['ka_1_ms'] > 0:
                ka_values.append(info['ka_1_ms'])
            if info['kdis_1_s'] is not None and info['kdis_1_s'] > 0:
                kdis_values.append(info['kdis_1_s'])
            if info['r_squared'] is not None:
                r2_values.append(info['r_squared'])

    return {
        'kd_m': np.mean(kd_values) if kd_values else None,
        'ka_1_ms': np.mean(ka_values) if ka_values else None,
        'kdis_1_s': np.mean(kdis_values) if kdis_values else None,
        'r_squared': np.mean(r2_values) if r2_values else None,
    }


def get_antibody_color(sensor_map: Dict, antibody_id: str) -> str:
    """Get color for antibody (first occurrence)"""
    for key, info in sensor_map.items():
        if info['antibody'] == antibody_id:
            return info['color']
    return '#000000'  # Default black


if __name__ == "__main__":
    # Test
    excel_path = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292\Results\ExcelReport_2025_10_15 13_27_15.xlsx"

    sensor_map = create_simple_sensor_map(excel_path)

    print(f"Total entries in sensor map: {len(sensor_map)}")

    antibodies = get_all_antibodies(sensor_map)
    print(f"\nTotal antibodies: {len(antibodies)}")

    # Test lookup
    key = ('251013_001.frd', 'SI-157C11_P5158', 200.0)
    if key in sensor_map:
        print(f"\nTest lookup: {key}")
        print(sensor_map[key])

    # Test kinetics
    print(f"\nKinetics for SI-157C11_P5158:")
    kinetics = get_antibody_kinetics(sensor_map, 'SI-157C11_P5158')
    print(kinetics)
