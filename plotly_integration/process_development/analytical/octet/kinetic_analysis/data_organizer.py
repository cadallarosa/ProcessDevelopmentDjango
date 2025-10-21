"""
Data Organizer

Organizes Octet kinetics data by antibody with concentration series.
Combines data from multiple FRD files into structured format for analysis.
"""

import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from frd_parser import FRDParser
from signal_processing import process_sensor_data
from simple_mapper import create_simple_sensor_map, get_antibody_kinetics, get_antibody_color


class KineticsDataOrganizer:
    """Organizes kinetics data by antibody and concentration"""

    def __init__(self,
                 frd_directory: str,
                 plate_mapping_path: str,
                 excel_results_path: str):
        """
        Initialize organizer

        Args:
            frd_directory: Directory containing FRD files
            plate_mapping_path: Path to plate mapping CSV
            excel_results_path: Path to Excel results file
        """
        self.frd_directory = Path(frd_directory)
        self.plate_mapping_path = plate_mapping_path
        self.excel_results_path = excel_results_path

        # Create simple sensor map
        self.sensor_map = create_simple_sensor_map(excel_results_path)

        # Data storage
        self.antibody_data = {}  # Organized by antibody
        self.raw_data = []  # List of all parsed FRD data

    def load_all_frd_files(self, pattern: str = "*.frd") -> int:
        """
        Load all FRD files from directory

        Args:
            pattern: Glob pattern for FRD files

        Returns:
            Number of files loaded
        """
        frd_files = sorted(self.frd_directory.glob(pattern))

        print(f"Found {len(frd_files)} FRD files")

        for frd_file in frd_files:
            print(f"  Loading {frd_file.name}...")
            try:
                parser = FRDParser(str(frd_file))
                self.raw_data.append({
                    'file_path': frd_file,
                    'file_name': frd_file.name,
                    'parser': parser,
                })
            except Exception as e:
                print(f"    Error loading {frd_file.name}: {e}")

        print(f"Loaded {len(self.raw_data)} FRD files successfully")
        return len(self.raw_data)

    def organize_by_antibody(self,
                             process_data: bool = True,
                             reference_correction: bool = False):
        """
        Organize all loaded data by antibody and concentration

        Args:
            process_data: Whether to apply data processing
            reference_correction: Whether to apply reference subtraction
        """
        print("\nOrganizing data by antibody...")

        for frd_data in self.raw_data:
            parser = frd_data['parser']
            file_name = frd_data['file_name']

            # Get ALL cycles from this FRD file
            cycles = parser.get_all_cycles()

            if not cycles:
                print(f"  Warning: No cycles found in {file_name}")
                continue

            print(f"  Processing {file_name}: {len(cycles)} cycles...")

            # Process each cycle
            for cycle in cycles:
                antibody_id = cycle['antibody_id']
                concentration_nm = cycle['concentration_nm']

                # Look up in sensor map using (frd_file, antibody, concentration)
                key = (file_name, antibody_id, concentration_nm)
                sample_info = self.sensor_map.get(key)

                if sample_info is None:
                    # This can happen if Excel doesn't have all combinations
                    continue

                antibody = sample_info['antibody']
                concentration = sample_info['concentration_nm']

                # Initialize antibody entry if needed
                if antibody not in self.antibody_data:
                    self.antibody_data[antibody] = {
                        'concentrations': {},
                        'color': get_antibody_color(self.sensor_map, antibody),
                        'kinetics': get_antibody_kinetics(self.sensor_map, antibody)
                    }

                # Get binding curve from cycle
                time = cycle['time_array']
                signal = cycle['signal_array']

                # Process if requested
                if process_data:
                    signal = process_sensor_data(
                        signal,
                        time,
                        reference_signal=None,  # TODO: Add reference handling
                        baseline_window=(50, 100),
                        apply_filter=True
                    )

                # Store data
                self.antibody_data[antibody]['concentrations'][concentration] = {
                    'time': time,
                    'signal': signal,
                    'metadata': {
                        'antibody_id': antibody_id,
                        'analyte_id': cycle['analyte_id'],
                        'concentration_nm': concentration_nm,
                    },
                    'sensor_location': sample_info['sensor_location'],
                    'sample_info': sample_info,
                    'frd_file': file_name
                }

        print(f"Organized data for {len(self.antibody_data)} antibodies")

        for antibody, data in list(self.antibody_data.items())[:5]:
            num_conc = len(data['concentrations'])
            print(f"  {antibody}: {num_conc} concentrations")

    def _extract_sensor_location(self, step_data: Dict) -> Optional[str]:
        """
        Extract sensor location from step data

        The sensor location format is like 't1A11' where:
        - t1 = tip plate 1
        - A11 = well position

        Args:
            step_data: Step dictionary from parser

        Returns:
            Sensor location string
        """
        # Try to construct from sample location and row
        sample_loc = step_data.get('sample_location')
        sample_row = step_data.get('sample_row')
        sample_plate = step_data.get('sample_plate')

        if sample_loc and sample_row and sample_plate:
            # Format: t{plate}{row}{location}
            return f"t{sample_plate}{sample_row}{sample_loc}"

        return None

    def get_antibody_data(self, antibody_id: str) -> Optional[Dict]:
        """
        Get all data for a specific antibody

        Args:
            antibody_id: Antibody identifier

        Returns:
            Dictionary with concentration series data
        """
        return self.antibody_data.get(antibody_id)

    def get_all_antibodies(self) -> List[str]:
        """
        Get list of all antibodies

        Returns:
            Sorted list of antibody IDs
        """
        return sorted(self.antibody_data.keys())

    def get_concentration_series(self, antibody_id: str) -> List[float]:
        """
        Get sorted list of concentrations tested for antibody

        Args:
            antibody_id: Antibody identifier

        Returns:
            Sorted list of concentrations (nM)
        """
        if antibody_id not in self.antibody_data:
            return []

        concentrations = list(self.antibody_data[antibody_id]['concentrations'].keys())
        return sorted(concentrations)

    def summary(self) -> str:
        """
        Get summary of organized data

        Returns:
            String summary
        """
        summary_lines = [
            f"Kinetics Data Summary",
            f"Total FRD files loaded: {len(self.raw_data)}",
            f"Antibodies: {len(self.antibody_data)}",
            f"\nAntibodies with concentration series:"
        ]

        for antibody in sorted(self.antibody_data.keys())[:10]:
            concentrations = self.get_concentration_series(antibody)
            kinetics = self.antibody_data[antibody]['kinetics']

            summary_lines.append(
                f"  {antibody}: {len(concentrations)} concentrations"
            )

            if kinetics['kd_m']:
                summary_lines.append(
                    f"    KD = {kinetics['kd_m']:.2e} M, R² = {kinetics['r_squared']:.3f}"
                )

        if len(self.antibody_data) > 10:
            summary_lines.append(f"  ... and {len(self.antibody_data) - 10} more")

        return "\n".join(summary_lines)


if __name__ == "__main__":
    # Test with OE292 data
    frd_dir = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292"
    plate_mapping = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292\octet_plate_mapping.csv"
    excel_results = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292\Results\ExcelReport_2025_10_15 13_27_15.xlsx"

    print("Testing Data Organizer...")

    organizer = KineticsDataOrganizer(frd_dir, plate_mapping, excel_results)

    # Load FRD files
    organizer.load_all_frd_files(pattern="251013_*.frd")

    # Organize by antibody
    organizer.organize_by_antibody(process_data=True)

    print("\n" + "="*80)
    print(organizer.summary())

    # Show example antibody
    print("\n" + "="*80)
    antibodies = organizer.get_all_antibodies()
    if antibodies:
        example_ab = antibodies[0]
        print(f"\nExample: {example_ab}")
        concentrations = organizer.get_concentration_series(example_ab)
        print(f"Concentrations: {concentrations}")

        ab_data = organizer.get_antibody_data(example_ab)
        print(f"Color: {ab_data['color']}")
        print(f"KD: {ab_data['kinetics']['kd_m']:.2e} M" if ab_data['kinetics']['kd_m'] else "KD: N/A")
