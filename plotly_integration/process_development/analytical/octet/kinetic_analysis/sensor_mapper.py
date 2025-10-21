"""
Sensor Mapper

Maps sensor locations to antibody samples and concentrations using plate mapping
and Excel results data.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Optional


class SensorMapper:
    """Maps sensor locations to sample information"""

    def __init__(self, plate_mapping_path: str, excel_results_path: str):
        """
        Initialize mapper with plate mapping and results files

        Args:
            plate_mapping_path: Path to octet_plate_mapping.csv
            excel_results_path: Path to Excel results file
        """
        self.plate_mapping_path = Path(plate_mapping_path)
        self.excel_results_path = Path(excel_results_path)

        self.plate_mapping = None
        self.results_df = None
        self.sensor_map = {}

        self._load_data()
        self._create_sensor_map()

    def _load_data(self):
        """Load plate mapping and Excel results"""
        # Load plate mapping
        self.plate_mapping = pd.read_csv(self.plate_mapping_path)

        # Load Excel results (Result Table sheet)
        self.results_df = pd.read_excel(
            self.excel_results_path,
            sheet_name='Result Table'
        )

    def _create_sensor_map(self):
        """
        Create mapping from (sensor_location, antibody, concentration) to sample information

        The key is now a tuple: (sensor_location, antibody_id, concentration_nm)
        because multiple antibodies can be tested on the same sensor location
        """
        self.sensor_map = {}

        for _, row in self.results_df.iterrows():
            sensor_loc = row['Sensor Location']
            antibody = row['Loading Sample ID']
            concentration = row['Conc. (nM)']

            # Skip if essential fields are missing
            if pd.isna(sensor_loc) or pd.isna(antibody) or pd.isna(concentration):
                continue

            # Use composite key: (sensor_location, antibody, concentration)
            key = (sensor_loc, antibody, concentration)

            self.sensor_map[key] = {
                'sensor_location': sensor_loc,
                'antibody': antibody,
                'analyte': row['Sample ID'],
                'concentration_nm': concentration,
                'color': row['Color'],
                'kd_m': row['KD (M)'] if not pd.isna(row['KD (M)']) else None,
                'ka_1_ms': row['ka (1/Ms)'] if not pd.isna(row['ka (1/Ms)']) else None,
                'kdis_1_s': row['kdis (1/s)'] if not pd.isna(row['kdis (1/s)']) else None,
                'r_squared': row['Full R^2'] if not pd.isna(row['Full R^2']) else None,
                'loading_response': row['Loading Response'] if not pd.isna(row['Loading Response']) else None,
            }

    def get_sample_info(self, sensor_location: str, antibody: str = None, concentration: float = None) -> Optional[Dict]:
        """
        Get sample information for a sensor location + antibody + concentration

        Args:
            sensor_location: Sensor location (e.g., 't1A11')
            antibody: Antibody ID (optional, returns first match if not specified)
            concentration: Concentration in nM (optional)

        Returns:
            Dictionary with sample info or None if not found
        """
        if antibody and concentration:
            # Direct lookup with full key
            key = (sensor_location, antibody, concentration)
            return self.sensor_map.get(key)
        else:
            # Find first match with sensor_location
            for key, info in self.sensor_map.items():
                if key[0] == sensor_location:
                    return info
            return None

    def get_antibody_sensors(self, antibody_id: str) -> Dict[float, str]:
        """
        Get all sensor locations for a specific antibody

        Args:
            antibody_id: Antibody identifier (e.g., 'SI-157C11_P5158')

        Returns:
            Dictionary mapping concentration (nM) to sensor location
        """
        sensors = {}
        for sensor_loc, info in self.sensor_map.items():
            if info['antibody'] == antibody_id:
                sensors[info['concentration_nm']] = sensor_loc
        return sensors

    def get_all_antibodies(self) -> list:
        """
        Get list of all unique antibodies

        Returns:
            List of antibody IDs
        """
        antibodies = set()
        for info in self.sensor_map.values():
            if info['antibody']:
                antibodies.add(info['antibody'])
        return sorted(list(antibodies))

    def get_antibody_color(self, antibody_id: str) -> Optional[str]:
        """
        Get color assigned to antibody for plotting

        Args:
            antibody_id: Antibody identifier

        Returns:
            Hex color string or None
        """
        for info in self.sensor_map.values():
            if info['antibody'] == antibody_id:
                return info['color']
        return None

    def get_antibody_kinetics(self, antibody_id: str) -> Dict:
        """
        Get kinetic parameters for antibody

        Args:
            antibody_id: Antibody identifier

        Returns:
            Dictionary with KD, ka, kdis values (averaged across concentrations)
        """
        kd_values = []
        ka_values = []
        kdis_values = []
        r2_values = []

        for info in self.sensor_map.values():
            if info['antibody'] == antibody_id:
                if info['kd_m'] is not None and info['kd_m'] != 0:
                    kd_values.append(info['kd_m'])
                if info['ka_1_ms'] is not None and info['ka_1_ms'] != 0:
                    ka_values.append(info['ka_1_ms'])
                if info['kdis_1_s'] is not None and info['kdis_1_s'] != 0:
                    kdis_values.append(info['kdis_1_s'])
                if info['r_squared'] is not None:
                    r2_values.append(info['r_squared'])

        import numpy as np
        return {
            'kd_m': np.mean(kd_values) if kd_values else None,
            'ka_1_ms': np.mean(ka_values) if ka_values else None,
            'kdis_1_s': np.mean(kdis_values) if kdis_values else None,
            'r_squared': np.mean(r2_values) if r2_values else None,
        }

    def summary(self) -> str:
        """
        Get summary of mapping

        Returns:
            String summary
        """
        antibodies = self.get_all_antibodies()

        summary_lines = [
            f"Sensor Mapping Summary",
            f"Total sensors mapped: {len(self.sensor_map)}",
            f"Unique antibodies: {len(antibodies)}",
            f"\nAntibodies tested:"
        ]

        for antibody in antibodies[:10]:  # Show first 10
            sensors = self.get_antibody_sensors(antibody)
            summary_lines.append(
                f"  {antibody}: {len(sensors)} concentrations"
            )

        if len(antibodies) > 10:
            summary_lines.append(f"  ... and {len(antibodies) - 10} more")

        return "\n".join(summary_lines)


if __name__ == "__main__":
    # Test with OE292 data
    plate_mapping = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292\octet_plate_mapping.csv"
    excel_results = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292\Results\ExcelReport_2025_10_15 13_27_15.xlsx"

    print("Testing Sensor Mapper...")
    mapper = SensorMapper(plate_mapping, excel_results)

    print("\n" + "="*80)
    print(mapper.summary())

    print("\n" + "="*80)
    print("\nExample: SI-157C11_P5158")
    sensors = mapper.get_antibody_sensors('SI-157C11_P5158')
    print(f"Concentrations tested: {sorted(sensors.keys())}")
    print(f"Color: {mapper.get_antibody_color('SI-157C11_P5158')}")

    kinetics = mapper.get_antibody_kinetics('SI-157C11_P5158')
    print(f"\nKinetic Parameters:")
    print(f"  KD: {kinetics['kd_m']:.2e} M" if kinetics['kd_m'] else "  KD: N/A")
    print(f"  ka: {kinetics['ka_1_ms']:.2e} 1/Ms" if kinetics['ka_1_ms'] else "  ka: N/A")
    print(f"  kdis: {kinetics['kdis_1_s']:.2e} 1/s" if kinetics['kdis_1_s'] else "  kdis: N/A")