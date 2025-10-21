"""
FRD File Parser

Parses Octet FRD (ForteBio Raw Data) XML files to extract time-series sensor data.
"""

import xml.etree.ElementTree as ET
import base64
import struct
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class FRDParser:
    """Parser for Octet FRD (XML) files"""

    def __init__(self, frd_path: str):
        """
        Initialize parser with FRD file path

        Args:
            frd_path: Path to .frd file
        """
        self.frd_path = Path(frd_path)
        self.tree = None
        self.root = None
        self._parse_xml()

    def _parse_xml(self):
        """Parse XML file"""
        self.tree = ET.parse(self.frd_path)
        self.root = self.tree.getroot()

    def get_experiment_info(self) -> Dict:
        """
        Extract experiment metadata

        Returns:
            dict: Experiment information
        """
        exp_info = self.root.find('ExperimentInfo')
        if exp_info is None:
            return {}

        info = {
            'name': exp_info.get('Name'),
            'run_id': exp_info.findtext('RunID'),
            'experiment_type': exp_info.findtext('ExperimentType'),
            'start_datetime': exp_info.findtext('StartDateTime'),
            'machine_name': exp_info.findtext('MachineName'),
            'instrument_type': exp_info.findtext('InstrumentType'),
            'instrument_serial': exp_info.findtext('InstrumentSerial'),
            'sensor_type': exp_info.findtext('SensorType'),
            'sensor_plate': exp_info.findtext('SensorPlate'),
        }
        return info

    def _decode_base64_array(self, base64_string: str) -> np.ndarray:
        """
        Decode Base64 encoded binary array to numpy array

        Args:
            base64_string: Base64 encoded string

        Returns:
            numpy array of float values
        """
        if not base64_string:
            return np.array([])

        # Decode base64 to binary
        binary_data = base64.b64decode(base64_string)

        # Unpack binary data as floats (4 bytes each, little-endian)
        num_floats = len(binary_data) // 4
        float_values = struct.unpack(f'<{num_floats}f', binary_data)

        return np.array(float_values)

    def get_sensor_location(self) -> Optional[str]:
        """
        Extract sensor location from experiment info

        Returns:
            Sensor location string (e.g., 't1A11') or None
        """
        # Sensor location is encoded in the experiment
        # For kinetics data, it's typically in the step data
        steps = self.get_all_steps()
        if steps:
            # Get from first step's common data
            first_step = steps[0]
            return first_step.get('sensor_location')
        return None

    def get_all_steps(self) -> List[Dict]:
        """
        Extract all experimental steps with time-series data

        Returns:
            List of step dictionaries containing metadata and data arrays
        """
        steps = []
        kinetics_data = self.root.find('KineticsData')

        if kinetics_data is None:
            return steps

        for step_elem in kinetics_data.findall('Step'):
            step_data = self._parse_step(step_elem)
            if step_data:
                steps.append(step_data)

        return steps

    def _parse_step(self, step_elem: ET.Element) -> Optional[Dict]:
        """
        Parse individual step element

        Args:
            step_elem: XML element for step

        Returns:
            Dictionary with step data
        """
        common_data = step_elem.find('CommonData')
        if common_data is None:
            return None

        # Extract metadata
        step_info = {
            # Common metadata
            'sample_location': common_data.findtext('SampleLocation'),
            'sample_id': common_data.findtext('SampleID'),
            'sample_group': common_data.findtext('SampleGroup'),
            'sample_row': common_data.findtext('SampleRow'),
            'sample_plate': common_data.findtext('SamplePlate'),
            'well_type': common_data.findtext('WellType'),
            'concentration': self._safe_float(common_data.findtext('Concentration')),
            'concentration_units': common_data.findtext('ConcentrationUnits'),
            'molar_concentration': self._safe_float(common_data.findtext('MolarConcentration')),
            'molar_conc_units': common_data.findtext('MolarConcUnits'),
            'temperature': self._safe_float(common_data.findtext('Temperature')),
            'start_time': self._safe_float(common_data.findtext('StartTime')),
            'assay_time': self._safe_float(common_data.findtext('AssayTime')),

            # Step-specific
            'step_type': step_elem.findtext('StepType'),
            'step_name': step_elem.findtext('StepName'),
            'step_status': step_elem.findtext('StepStatus'),
            'actual_time': self._safe_float(step_elem.findtext('ActualTime')),
            'cycle_time': self._safe_float(step_elem.findtext('CycleTime')),
            'flow_rate': self._safe_float(step_elem.findtext('FlowRate')),
        }

        # Extract time-series data
        x_data_elem = step_elem.find('AssayXData')
        y_data_elem = step_elem.find('AssayYData')

        if x_data_elem is not None and y_data_elem is not None:
            x_base64 = x_data_elem.text
            y_base64 = y_data_elem.text

            step_info['time_array'] = self._decode_base64_array(x_base64)
            step_info['signal_array'] = self._decode_base64_array(y_base64)
            step_info['num_points'] = int(x_data_elem.get('Points', 0))
        else:
            step_info['time_array'] = np.array([])
            step_info['signal_array'] = np.array([])
            step_info['num_points'] = 0

        return step_info

    def _safe_float(self, value: Optional[str]) -> Optional[float]:
        """Safely convert string to float"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def get_association_step(self) -> Optional[Dict]:
        """
        Get the association step data (analyte binding)

        Returns:
            Step dictionary for association phase
        """
        steps = self.get_all_steps()
        for step in steps:
            if step['step_type'] in ['ASSOCIATION', 'ASSOC']:
                return step
        return None

    def get_dissociation_step(self) -> Optional[Dict]:
        """
        Get the dissociation step data

        Returns:
            Step dictionary for dissociation phase
        """
        steps = self.get_all_steps()
        for step in steps:
            if step['step_type'] in ['DISSOCIATION', 'DISSOC']:
                return step
        return None

    def get_loading_step(self) -> Optional[Dict]:
        """
        Get the loading step data (antibody loading onto sensor)

        Returns:
            Step dictionary for loading phase
        """
        steps = self.get_all_steps()
        for step in steps:
            if step['step_type'] == 'LOADING':
                return step
        return None

    def get_baseline_step(self) -> Optional[Dict]:
        """
        Get the baseline step data (buffer equilibration before association)

        Returns:
            Step dictionary for baseline phase
        """
        steps = self.get_all_steps()
        for step in steps:
            if step['step_name'] == 'Baseline' or step['well_type'] == 'BUFFER':
                # Get the baseline step that comes after loading
                if step.get('start_time', 0) > 100000:  # After loading
                    return step
        return None

    def get_all_cycles(self) -> List[Dict]:
        """
        Get all experimental cycles (Loading → Baseline → Association → Dissociation)

        Each cycle represents one antibody test

        Returns:
            List of cycle dictionaries, each containing:
                - loading_step
                - baseline_step
                - association_step
                - dissociation_step
                - antibody_id
                - time_array
                - signal_array
        """
        steps = self.get_all_steps()
        cycles = []

        i = 0
        while i < len(steps):
            # Look for loading step
            if steps[i]['step_type'] == 'LOADING':
                loading_step = steps[i]
                antibody_id = loading_step['sample_id']

                # Next should be baseline
                baseline_step = steps[i+1] if i+1 < len(steps) and steps[i+1]['step_type'] == 'BASELINE' else None

                # Then association
                assoc_step = steps[i+2] if i+2 < len(steps) and steps[i+2]['step_type'] in ['ASSOC', 'ASSOCIATION'] else None

                # Then dissociation
                dissoc_step = steps[i+3] if i+3 < len(steps) and steps[i+3]['step_type'] in ['DISASSOC', 'DISSOCIATION'] else None

                if assoc_step:
                    # Build binding curve
                    time_array = assoc_step['time_array'].copy()
                    signal_array = assoc_step['signal_array'].copy()

                    if dissoc_step:
                        dissoc_time = dissoc_step['time_array'] + time_array[-1]
                        time_array = np.concatenate([time_array, dissoc_time])
                        signal_array = np.concatenate([signal_array, dissoc_step['signal_array']])

                    cycle = {
                        'loading_step': loading_step,
                        'baseline_step': baseline_step,
                        'association_step': assoc_step,
                        'dissociation_step': dissoc_step,
                        'antibody_id': antibody_id,
                        'analyte_id': assoc_step['sample_id'],
                        'concentration_nm': assoc_step['molar_concentration'],
                        'time_array': time_array,
                        'signal_array': signal_array,
                    }
                    cycles.append(cycle)

            i += 1

        return cycles

    def get_binding_curve(self) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """
        Get complete binding curve (association + dissociation) for FIRST cycle

        Returns:
            tuple: (time_array, signal_array, metadata)
        """
        cycles = self.get_all_cycles()
        if not cycles:
            return np.array([]), np.array([]), {}

        first_cycle = cycles[0]
        metadata = {
            'sample_id': first_cycle['analyte_id'],
            'antibody_id': first_cycle['antibody_id'],
            'concentration_nm': first_cycle['concentration_nm'],
        }

        return first_cycle['time_array'], first_cycle['signal_array'], metadata

    def summary(self) -> str:
        """
        Get summary of FRD file contents

        Returns:
            String summary
        """
        exp_info = self.get_experiment_info()
        steps = self.get_all_steps()

        summary_lines = [
            f"FRD File: {self.frd_path.name}",
            f"Experiment: {exp_info.get('name', 'Unknown')}",
            f"Type: {exp_info.get('experiment_type', 'Unknown')}",
            f"Sensor Type: {exp_info.get('sensor_type', 'Unknown')}",
            f"Start Time: {exp_info.get('start_datetime', 'Unknown')}",
            f"\nSteps ({len(steps)}):"
        ]

        for i, step in enumerate(steps, 1):
            summary_lines.append(
                f"  {i}. {step['step_name']} ({step['step_type']}) - "
                f"{step['sample_id']} - {step['num_points']} points"
            )

        return "\n".join(summary_lines)


# Convenience function
def parse_frd_file(frd_path: str) -> FRDParser:
    """
    Parse FRD file and return parser object

    Args:
        frd_path: Path to FRD file

    Returns:
        FRDParser object
    """
    return FRDParser(frd_path)


if __name__ == "__main__":
    # Test with OE292 data
    import sys

    test_file = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292\251013_001.frd"

    print("Testing FRD Parser...")
    parser = FRDParser(test_file)

    print("\n" + "="*80)
    print(parser.summary())

    print("\n" + "="*80)
    print("\nAssociation Step:")
    assoc = parser.get_association_step()
    if assoc:
        print(f"  Sample: {assoc['sample_id']}")
        print(f"  Concentration: {assoc['molar_concentration']} {assoc['molar_conc_units']}")
        print(f"  Time points: {len(assoc['time_array'])}")
        print(f"  Duration: {assoc['actual_time']} seconds")

    print("\nBinding Curve:")
    time, signal, meta = parser.get_binding_curve()
    print(f"  Total points: {len(time)}")
    print(f"  Time range: {time[0]:.1f} - {time[-1]:.1f} seconds")
    print(f"  Signal range: {signal.min():.2f} - {signal.max():.2f} nm")