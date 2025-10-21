"""
FRD File Importer - Import Raw Octet Time Series Data

Parses .frd XML files to extract:
- Experiment metadata
- Sensor information
- Step-level data
- Raw time series data (time, response)
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import base64
import struct
import logging
from datetime import datetime
from django.db import transaction

from plotly_integration.models import (
    OctetExperiment,
    OctetSensorData,
    OctetStepData,
    OctetTimeSeriesData
)

logger = logging.getLogger(__name__)


class FRDImporter:
    """Importer for Octet .frd files"""

    def __init__(self, frd_file_path: str):
        """
        Initialize importer with FRD file path

        Args:
            frd_file_path: Path to .frd file
        """
        self.file_path = frd_file_path
        self.tree = None
        self.root = None
        self._load_xml()

    def _load_xml(self):
        """Load and parse the XML file"""
        try:
            self.tree = ET.parse(self.file_path)
            self.root = self.tree.getroot()
            logger.info(f"Successfully loaded FRD from {self.file_path}")
        except Exception as e:
            logger.error(f"Error loading FRD XML: {e}")
            raise

    def parse_experiment_info(self) -> Dict[str, Any]:
        """
        Extract experiment-level metadata

        Returns:
            Dict with experiment information
        """
        exp_info = self.root.find('.//ExperimentInfo')

        if exp_info is None:
            raise ValueError("No ExperimentInfo found in FRD file")

        info = {}

        # Text fields
        text_fields = [
            'Name', 'ExpDescription', 'RTDVersion', 'RunID', 'ExperimentType',
            'ExperimentSubType', 'StartDateTime', 'MachineName', 'UserName',
            'PlateName', 'SensorName', 'SensorPlate', 'SensorType', 'SensorRole',
            'WritingSW', 'InstrumentType', 'InstrumentSerial', 'IntegrationTime'
        ]

        for field in text_fields:
            elem = exp_info.find(field)
            if elem is not None and elem.text:
                info[field.lower()] = elem.text

        logger.info(f"Parsed experiment info for {info.get('name', 'Unknown')}")
        return info

    def parse_sensor_location(self) -> str:
        """Get sensor location from ExperimentInfo"""
        exp_info = self.root.find('.//ExperimentInfo')
        sensor_name = exp_info.find('SensorName')
        return sensor_name.text if sensor_name is not None else 'Unknown'

    def parse_steps(self) -> List[Dict[str, Any]]:
        """
        Parse all kinetic steps from the FRD file

        Returns:
            List of step dictionaries with metadata and time series data
        """
        steps = []
        step_elements = self.root.findall('.//KineticsData/Step')

        for step_num, step_elem in enumerate(step_elements, 1):
            step_data = self._parse_single_step(step_elem, step_num)
            if step_data:
                steps.append(step_data)

        logger.info(f"Parsed {len(steps)} steps from FRD file")
        return steps

    def _parse_single_step(self, step_elem: ET.Element, step_number: int) -> Optional[Dict[str, Any]]:
        """
        Parse a single step element

        Args:
            step_elem: XML element for the step
            step_number: Sequential step number

        Returns:
            Dict with step data including time series
        """
        try:
            # Parse CommonData
            common_data = step_elem.find('CommonData')
            if common_data is None:
                logger.warning(f"No CommonData in step {step_number}")
                return None

            step_info = {
                'step_number': step_number,
                'sample_location': self._get_text(common_data, 'SampleLocation'),
                'sample_id': self._get_text(common_data, 'SampleID'),
                'sample_group': self._get_text(common_data, 'SampleGroup'),
                'sample_info': self._get_text(common_data, 'SampleInfo'),
                'well_type': self._get_text(common_data, 'WellType'),
                'concentration': self._get_float(common_data, 'Concentration'),
                'concentration_units': self._get_text(common_data, 'ConcentrationUnits'),
                'molar_concentration': self._get_float(common_data, 'MolarConcentration'),
                'molar_conc_units': self._get_text(common_data, 'MolarConcUnits'),
                'temperature': self._get_float(common_data, 'Temperature'),
                'start_time': self._get_float(common_data, 'StartTime'),
                'assay_time': self._get_float(common_data, 'AssayTime'),
            }

            # Parse step-specific fields
            step_info['flow_rate'] = self._get_float(step_elem, 'FlowRate')
            step_info['step_type'] = self._get_text(step_elem, 'StepType')
            step_info['step_name'] = self._get_text(step_elem, 'StepName')
            step_info['step_status'] = self._get_text(step_elem, 'StepStatus')
            step_info['actual_time'] = self._get_float(step_elem, 'ActualTime')
            step_info['cycle_time'] = self._get_float(step_elem, 'CycleTime')

            # Parse time series data
            x_data, y_data = self._parse_time_series(step_elem)
            step_info['time_data'] = x_data
            step_info['response_data'] = y_data
            step_info['num_points'] = len(x_data)

            return step_info

        except Exception as e:
            logger.error(f"Error parsing step {step_number}: {e}")
            return None

    def _parse_time_series(self, step_elem: ET.Element) -> Tuple[np.ndarray, np.ndarray]:
        """
        Parse base64-encoded time series data

        Args:
            step_elem: XML element containing AssayXData and AssayYData

        Returns:
            Tuple of (time_array, response_array)
        """
        x_elem = step_elem.find('AssayXData')
        y_elem = step_elem.find('AssayYData')

        if x_elem is None or y_elem is None:
            logger.warning("No time series data found in step")
            return np.array([]), np.array([])

        # Get number of points
        num_points = int(x_elem.get('Points', 0))

        if num_points == 0:
            return np.array([]), np.array([])

        # Decode base64 data
        x_data = self._decode_base64_floats(x_elem.text, num_points)
        y_data = self._decode_base64_floats(y_elem.text, num_points)

        return x_data, y_data

    def _decode_base64_floats(self, base64_str: str, num_points: int) -> np.ndarray:
        """
        Decode base64-encoded float array

        Args:
            base64_str: Base64 encoded string
            num_points: Expected number of float values

        Returns:
            NumPy array of floats
        """
        if not base64_str:
            return np.array([])

        try:
            # Decode base64
            binary_data = base64.b64decode(base64_str)

            # Unpack as floats (little-endian, 4 bytes each)
            float_format = f'<{num_points}f'  # '<' = little-endian, 'f' = float
            floats = struct.unpack(float_format, binary_data)

            return np.array(floats)

        except Exception as e:
            logger.error(f"Error decoding base64 floats: {e}")
            return np.array([])

    def _get_text(self, parent: ET.Element, tag: str) -> str:
        """Safely get text from XML element"""
        elem = parent.find(tag)
        return elem.text if elem is not None and elem.text else ''

    def _get_float(self, parent: ET.Element, tag: str) -> Optional[float]:
        """Safely get float from XML element"""
        elem = parent.find(tag)
        if elem is not None and elem.text:
            try:
                return float(elem.text)
            except ValueError:
                return None
        return None

    def _get_int(self, parent: ET.Element, tag: str) -> Optional[int]:
        """Safely get int from XML element"""
        elem = parent.find(tag)
        if elem is not None and elem.text:
            try:
                return int(elem.text)
            except ValueError:
                return None
        return None


class FRDDatasetImporter:
    """
    Importer for a complete Octet dataset (multiple FRD files + experiment)

    This class orchestrates importing an entire experiment:
    - Creates OctetExperiment record
    - Imports all sensor data from multiple FRD files
    - Creates time series data records
    """

    def __init__(self, frd_files: List[str], experiment_folder: str):
        """
        Initialize dataset importer

        Args:
            frd_files: List of paths to FRD files
            experiment_folder: Path to experiment folder
        """
        self.frd_files = frd_files
        self.experiment_folder = experiment_folder
        self.experiment = None

    @transaction.atomic
    def import_dataset(self, vendor_settings: Optional[Dict[str, Any]] = None) -> OctetExperiment:
        """
        Import complete dataset into database

        Args:
            vendor_settings: Optional vendor analysis settings from HTSettings

        Returns:
            Created OctetExperiment instance
        """
        if not self.frd_files:
            raise ValueError("No FRD files provided")

        # Parse first file to get experiment metadata
        logger.info(f"Importing dataset from {len(self.frd_files)} FRD files...")
        first_importer = FRDImporter(self.frd_files[0])
        exp_info = first_importer.parse_experiment_info()

        # Create or get experiment
        self.experiment = self._create_experiment(exp_info, vendor_settings)

        # Import each sensor (one per FRD file)
        for frd_file in self.frd_files:
            self._import_sensor_from_frd(frd_file)

        logger.info(f"Successfully imported experiment: {self.experiment.experiment_name}")
        return self.experiment

    def _create_experiment(self, exp_info: Dict[str, Any], vendor_settings: Optional[Dict]) -> OctetExperiment:
        """Create OctetExperiment record"""
        run_id = exp_info.get('runid', '')

        # Try to get existing experiment
        try:
            experiment = OctetExperiment.objects.get(run_id=run_id)
            logger.info(f"Experiment {run_id} already exists, updating...")
            update_fields = []

            # Update vendor settings if provided
            if vendor_settings:
                experiment.vendor_analysis_settings = vendor_settings
                update_fields.append('vendor_analysis_settings')

            if update_fields:
                experiment.save(update_fields=update_fields)

            return experiment

        except OctetExperiment.DoesNotExist:
            # Create new experiment
            logger.info(f"Creating new experiment: {run_id}")

            # Parse datetime
            start_datetime = None
            if exp_info.get('startdatetime'):
                try:
                    start_datetime = datetime.fromisoformat(exp_info['startdatetime'].replace('T', ' '))
                except:
                    pass

            experiment = OctetExperiment.objects.create(
                run_id=run_id,
                experiment_name=exp_info.get('name', 'Unknown'),
                experiment_type=exp_info.get('experimenttype', 'KINETICS'),
                experiment_subtype=exp_info.get('experimentsubtype', ''),
                description=exp_info.get('expdescription', ''),
                start_datetime=start_datetime,
                machine_name=exp_info.get('machinename', ''),
                instrument_type=exp_info.get('instrumenttype', ''),
                instrument_serial=exp_info.get('instrumentserial', ''),
                sensor_type=exp_info.get('sensortype', ''),
                user_name=exp_info.get('username', ''),
                consolidated_file_path='',  # Not from consolidated Excel
                original_folder_path=self.experiment_folder,
                vendor_analysis_settings=vendor_settings,
            )

            return experiment

    def _import_sensor_from_frd(self, frd_file: str):
        """Import sensor data from a single FRD file"""
        logger.info(f"Importing sensor from {frd_file}")

        importer = FRDImporter(frd_file)
        exp_info = importer.parse_experiment_info()
        sensor_location = importer.parse_sensor_location()
        steps = importer.parse_steps()

        if not steps:
            logger.warning(f"No steps found in {frd_file}")
            return

        # Get or create sensor
        sensor, created = OctetSensorData.objects.get_or_create(
            experiment=self.experiment,
            sensor_location=sensor_location,
            defaults={
                'sample_id': steps[0].get('sample_id', ''),
                'sensor_type': exp_info.get('sensortype', ''),
            }
        )

        if created:
            logger.info(f"Created sensor: {sensor_location}")
        else:
            logger.info(f"Sensor {sensor_location} already exists, updating...")

        # Import steps and time series
        self._import_steps_and_timeseries(sensor, steps)

    def _import_steps_and_timeseries(self, sensor: OctetSensorData, steps: List[Dict]):
        """Import step data and time series for a sensor"""

        # Delete existing data for this sensor (to avoid duplicates)
        OctetStepData.objects.filter(sensor=sensor).delete()
        OctetTimeSeriesData.objects.filter(
            run_id=self.experiment.run_id,
            sensor_location=sensor.sensor_location
        ).delete()

        # Import each step
        for step_data in steps:
            # Create step record
            step = OctetStepData.objects.create(
                sensor=sensor,
                step_number=step_data['step_number'],
                step_name=step_data.get('step_name', ''),
                step_type=step_data.get('step_type', ''),
                sample_location=step_data.get('sample_location', ''),
                sample_id=step_data.get('sample_id', ''),
                well_type=step_data.get('well_type', ''),
                concentration=step_data.get('concentration'),
                concentration_units=step_data.get('concentration_units', ''),
                temperature=step_data.get('temperature'),
                start_time=step_data.get('start_time', 0),
                assay_time=step_data.get('assay_time', 0),
            )

            # Bulk create time series data
            time_data = step_data.get('time_data', [])
            response_data = step_data.get('response_data', [])

            if len(time_data) > 0 and len(response_data) > 0:
                time_series_objects = [
                    OctetTimeSeriesData(
                        run_id=self.experiment.run_id,
                        sensor_location=sensor.sensor_location,
                        step_number=step_data['step_number'],
                        step=step,
                        time=float(t),
                        response=float(r)
                    )
                    for t, r in zip(time_data, response_data)
                ]

                # Bulk create in batches
                batch_size = 1000
                for i in range(0, len(time_series_objects), batch_size):
                    batch = time_series_objects[i:i+batch_size]
                    OctetTimeSeriesData.objects.bulk_create(batch)

                logger.info(f"  Imported {len(time_series_objects)} time series points for step {step_data['step_number']}")


def import_octet_kinetics_data(experiment_folder: str, vendor_settings: Optional[Dict] = None) -> OctetExperiment:
    """
    Convenience function to import Octet kinetics data

    Args:
        experiment_folder: Path to folder containing FRD files
        vendor_settings: Optional vendor analysis settings

    Returns:
        Created OctetExperiment instance
    """
    import os

    # Find all FRD files
    frd_files = []
    for file in os.listdir(experiment_folder):
        if file.endswith('.frd') and not file.startswith('HTSettings'):
            frd_files.append(os.path.join(experiment_folder, file))

    if not frd_files:
        raise ValueError(f"No FRD files found in {experiment_folder}")

    frd_files.sort()  # Sort for consistent ordering

    logger.info(f"Found {len(frd_files)} FRD files to import")

    # Create importer and run import
    importer = FRDDatasetImporter(frd_files, experiment_folder)
    return importer.import_dataset(vendor_settings)
