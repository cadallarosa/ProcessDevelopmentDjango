"""
Octet Kinetics Analysis Package

Standalone data processing pipeline for Octet kinetics experiments.
Processes FRD files, organizes data by antibody/concentration, and creates visualizations.
"""

__version__ = "1.0.0"

from .frd_parser import FRDParser, parse_frd_file
from .sensor_mapper import SensorMapper
from .data_organizer import KineticsDataOrganizer
from .data_processing import (
    process_sensor_data,
    subtract_reference,
    align_baseline,
    apply_savgol_filter,
    calculate_steady_state_response,
    split_association_dissociation
)
from .visualization import (
    plot_concentration_series,
    plot_comparison,
    plot_affinity_ranking,
    plot_kinetics_heatmap,
    create_interactive_dashboard
)

__all__ = [
    # Parsing
    'FRDParser',
    'parse_frd_file',
    'SensorMapper',
    'KineticsDataOrganizer',

    # Processing
    'process_sensor_data',
    'subtract_reference',
    'align_baseline',
    'apply_savgol_filter',
    'calculate_steady_state_response',
    'split_association_dissociation',

    # Visualization
    'plot_concentration_series',
    'plot_comparison',
    'plot_affinity_ranking',
    'plot_kinetics_heatmap',
    'create_interactive_dashboard',
]
