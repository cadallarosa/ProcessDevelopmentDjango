"""
HTSettings Parser - Extract Vendor Analysis Settings

Parses HTSettings.efrd XML files to extract:
- Kinetic fitting parameters (binding model, time ranges)
- Preprocessing/alignment settings
- Reference well configurations
- Sample reference groupings
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class HTSettingsParser:
    """Parser for Octet HTSettings.efrd files"""

    def __init__(self, file_path: str):
        """
        Initialize parser with HTSettings.efrd file path

        Args:
            file_path: Path to HTSettings.efrd file
        """
        self.file_path = file_path
        self.tree = None
        self.root = None
        self._load_xml()

    def _load_xml(self):
        """Load and parse the XML file"""
        try:
            self.tree = ET.parse(self.file_path)
            self.root = self.tree.getroot()
            logger.info(f"Successfully loaded HTSettings from {self.file_path}")
        except Exception as e:
            logger.error(f"Error loading HTSettings XML: {e}")
            raise

    def parse_all(self) -> Dict[str, Any]:
        """
        Parse all settings and return structured dictionary

        Returns:
            Dictionary with all vendor analysis settings
        """
        return {
            'analysis_type': self._get_analysis_type(),
            'run_id': self._get_run_id(),
            'kinetic_params': self._parse_kinetic_params(),
            'preprocessing': self._parse_preprocessing(),
            'reference_wells': self._parse_reference_wells(),
        }

    def _get_analysis_type(self) -> Optional[str]:
        """Get analysis type (Kinetic, Quantitation, etc.)"""
        elem = self.root.find('.//WorkspaceSettings/AnalysisType')
        return elem.text if elem is not None else None

    def _get_run_id(self) -> Optional[str]:
        """Get experiment run ID"""
        elem = self.root.find('.//ExperimentSettings/RunID')
        return elem.text if elem is not None else None

    def _parse_kinetic_params(self) -> Dict[str, Any]:
        """
        Parse kinetic fitting parameters

        Returns:
            Dict with kinetic analysis parameters
        """
        params = {}

        # Find KineticFitParams section
        kinetic_fit = self.root.find('.//KineticFitParams')

        if kinetic_fit is None:
            logger.warning("No KineticFitParams found in HTSettings")
            return params

        # Extract key parameters
        field_map = {
            'FitType': 'fit_type',
            'BindingModel': 'binding_model',
            'StepsToAnalyze': 'steps_to_analyze',
            'FitGroupBy': 'fit_group_by',
            'RmaxUnlink': 'rmax_unlink',
            'AssocStartTime': 'assoc_start_time',
            'AssocEndTime': 'assoc_end_time',
            'DissocStartTime': 'dissoc_start_time',
            'DissocEndTime': 'dissoc_end_time',
            'AssocStartPt': 'assoc_start_pt',
            'AssocEndPt': 'assoc_end_pt',
            'DissocStartPt': 'dissoc_start_pt',
            'DissocEndPt': 'dissoc_end_pt',
            'DeltaT': 'delta_t',
        }

        for xml_field, param_name in field_map.items():
            elem = kinetic_fit.find(f'.//{xml_field}')
            if elem is not None and elem.text:
                # Try to convert to appropriate type
                try:
                    # Try float first
                    if '.' in elem.text or 'e' in elem.text.lower():
                        params[param_name] = float(elem.text)
                    # Try int
                    elif elem.text.isdigit():
                        params[param_name] = int(elem.text)
                    # Boolean
                    elif elem.text.lower() in ('true', 'false'):
                        params[param_name] = elem.text.lower() == 'true'
                    # String
                    else:
                        params[param_name] = elem.text
                except ValueError:
                    params[param_name] = elem.text

        logger.info(f"Parsed {len(params)} kinetic parameters")
        return params

    def _parse_preprocessing(self) -> Dict[str, Any]:
        """
        Parse preprocessing and alignment settings

        Returns:
            Dict with preprocessing parameters
        """
        preproc = {}

        # Find AlignmentSettings section
        alignment = self.root.find('.//AlignmentSettings')

        if alignment is None:
            logger.warning("No AlignmentSettings found in HTSettings")
            return preproc

        field_map = {
            'AlignYCorrection': 'align_y_correction',
            'AlignYStart': 'align_y_start',
            'AlignYEnd': 'align_y_end',
            'InterstepCorrection': 'interstep_correction',
            'InterstepCorrectionTime': 'interstep_correction_time',
            'SavitzkyGolayFilter': 'savitzky_golay_filter',
        }

        for xml_field, param_name in field_map.items():
            elem = alignment.find(f'.//{xml_field}')
            if elem is not None and elem.text:
                try:
                    if '.' in elem.text:
                        preproc[param_name] = float(elem.text)
                    elif elem.text.isdigit():
                        preproc[param_name] = int(elem.text)
                    elif elem.text.lower() in ('true', 'false'):
                        preproc[param_name] = elem.text.lower() == 'true'
                    else:
                        preproc[param_name] = elem.text
                except ValueError:
                    preproc[param_name] = elem.text

        logger.info(f"Parsed {len(preproc)} preprocessing parameters")
        return preproc

    def _parse_reference_wells(self) -> Dict[str, Any]:
        """
        Parse reference well configurations

        Returns:
            Dict with reference well settings
        """
        ref_config = {
            'sample_reference': [],
            'sensor_reference': []
        }

        # Parse sample reference wells
        sample_ref = self.root.find('.//SampleReference')
        if sample_ref is not None:
            for plate in sample_ref.findall('.//Plate'):
                plate_idx = plate.get('Index', '0')
                plate_size = plate.get('Size', '96')

                ref_wells_elem = plate.find('RefWells')
                ref_wells = ref_wells_elem.text if ref_wells_elem is not None and ref_wells_elem.text else ''

                # Parse RefGroups
                ref_groups = []
                for group in plate.findall('.//RefGroup'):
                    ref_wells_elem = group.find('RefWells')
                    related_wells_elem = group.find('RelatedWells')

                    ref_group = {
                        'ref_wells': ref_wells_elem.text if ref_wells_elem is not None and ref_wells_elem.text else '',
                        'related_wells': related_wells_elem.text if related_wells_elem is not None and related_wells_elem.text else ''
                    }
                    ref_groups.append(ref_group)

                plate_config = {
                    'plate_index': int(plate_idx),
                    'plate_size': int(plate_size),
                    'ref_wells': ref_wells,
                    'ref_groups': ref_groups
                }
                ref_config['sample_reference'].append(plate_config)

        logger.info(f"Parsed reference well configurations")
        return ref_config

    def get_analysis_template_params(self) -> Dict[str, Any]:
        """
        Extract parameters suitable for OctetAnalysisTemplate

        Returns:
            Dict formatted for OctetAnalysisTemplate.parameters field
        """
        kinetic_params = self._parse_kinetic_params()
        preprocessing = self._parse_preprocessing()

        # Combine into template-friendly format
        template_params = {
            # Kinetic fitting
            'binding_model': kinetic_params.get('binding_model', 'FastOne2One'),
            'fit_type': kinetic_params.get('fit_type', 'Global'),
            'assoc_start_time': kinetic_params.get('assoc_start_time', 0),
            'assoc_end_time': kinetic_params.get('assoc_end_time', 180),
            'dissoc_start_time': kinetic_params.get('dissoc_start_time', 0),
            'dissoc_end_time': kinetic_params.get('dissoc_end_time', 60),
            'rmax_unlink': kinetic_params.get('rmax_unlink', 'Sensor'),

            # Preprocessing
            'align_y_correction': preprocessing.get('align_y_correction', 'AverageBaseline'),
            'align_y_start': preprocessing.get('align_y_start', 50),
            'align_y_end': preprocessing.get('align_y_end', 100),
            'interstep_correction': preprocessing.get('interstep_correction', 'Dissociation'),
            'savitzky_golay_filter': preprocessing.get('savitzky_golay_filter', True),
        }

        return template_params


def parse_htsettings(file_path: str) -> Dict[str, Any]:
    """
    Convenience function to parse HTSettings file

    Args:
        file_path: Path to HTSettings.efrd file

    Returns:
        Dictionary with all vendor analysis settings
    """
    parser = HTSettingsParser(file_path)
    return parser.parse_all()
