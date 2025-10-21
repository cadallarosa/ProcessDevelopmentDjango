"""
Parse HTSettings.efrd to extract analysis parameters
"""

import xml.etree.ElementTree as ET
from pathlib import Path


def parse_ht_settings(ht_settings_path):
    """Parse HTSettings.efrd XML file"""

    tree = ET.parse(ht_settings_path)
    root = tree.getroot()

    settings = {}

    # Get kinetic fit parameters
    kinetic_fit = root.find('.//KineticFitParams')

    if kinetic_fit is not None:
        settings['fit_type'] = kinetic_fit.find('FitType').text if kinetic_fit.find('FitType') is not None else None
        settings['binding_model'] = kinetic_fit.find('BindingModel').text if kinetic_fit.find('BindingModel') is not None else None
        settings['steps_to_analyze'] = kinetic_fit.find('StepsToAnalyze').text if kinetic_fit.find('StepsToAnalyze') is not None else None

        # Association window
        settings['assoc_start_time'] = float(kinetic_fit.find('AssocStartTime').text) if kinetic_fit.find('AssocStartTime') is not None else None
        settings['assoc_end_time'] = float(kinetic_fit.find('AssocEndTime').text) if kinetic_fit.find('AssocEndTime') is not None else None

        # Dissociation window
        settings['dissoc_start_time'] = float(kinetic_fit.find('DissocStartTime').text) if kinetic_fit.find('DissocStartTime') is not None else None
        settings['dissoc_end_time'] = float(kinetic_fit.find('DissocEndTime').text) if kinetic_fit.find('DissocEndTime') is not None else None

        # Data points
        settings['assoc_start_pt'] = int(kinetic_fit.find('AssocStartPt').text) if kinetic_fit.find('AssocStartPt') is not None else None
        settings['assoc_end_pt'] = int(kinetic_fit.find('AssocEndPt').text) if kinetic_fit.find('AssocEndPt') is not None else None
        settings['dissoc_start_pt'] = int(kinetic_fit.find('DissocStartPt').text) if kinetic_fit.find('DissocStartPt') is not None else None
        settings['dissoc_end_pt'] = int(kinetic_fit.find('DissocEndPt').text) if kinetic_fit.find('DissocEndPt') is not None else None

        # Sampling rate
        settings['delta_t'] = float(kinetic_fit.find('DeltaT').text) if kinetic_fit.find('DeltaT') is not None else None

        # Fit grouping
        settings['fit_group_by'] = kinetic_fit.find('FitGroupBy').text if kinetic_fit.find('FitGroupBy') is not None else None
        settings['rmax_unlink'] = kinetic_fit.find('RmaxUnlink').text if kinetic_fit.find('RmaxUnlink') is not None else None

    # Get workspace settings
    workspace = root.find('.//WorkspaceSettings')
    if workspace is not None:
        settings['analysis_type'] = workspace.find('AnalysisType').text if workspace.find('AnalysisType') is not None else None

    # Get experiment info
    exp_settings = root.find('.//ExperimentSettings')
    if exp_settings is not None:
        settings['run_id'] = exp_settings.find('RunID').text if exp_settings.find('RunID') is not None else None
        settings['num_sample_plates'] = int(exp_settings.find('NumSamplePlates').text) if exp_settings.find('NumSamplePlates') is not None else None

    return settings


def print_settings(settings):
    """Print settings in readable format"""
    print("HTSettings.efrd Analysis Parameters")
    print("=" * 60)

    print("\nGeneral:")
    print(f"  Analysis Type: {settings.get('analysis_type')}")
    print(f"  Run ID: {settings.get('run_id')}")
    print(f"  Sample Plates: {settings.get('num_sample_plates')}")

    print("\nFitting:")
    print(f"  Fit Type: {settings.get('fit_type')}")
    print(f"  Binding Model: {settings.get('binding_model')}")
    print(f"  Steps to Analyze: {settings.get('steps_to_analyze')}")
    print(f"  Fit Group By: {settings.get('fit_group_by')}")
    print(f"  Rmax Unlink: {settings.get('rmax_unlink')}")

    print("\nAssociation Window:")
    print(f"  Start Time: {settings.get('assoc_start_time')} s")
    print(f"  End Time: {settings.get('assoc_end_time')} s")
    print(f"  Start Point: {settings.get('assoc_start_pt')}")
    print(f"  End Point: {settings.get('assoc_end_pt')}")

    print("\nDissociation Window:")
    print(f"  Start Time: {settings.get('dissoc_start_time')} s")
    print(f"  End Time: {settings.get('dissoc_end_time')} s")
    print(f"  Start Point: {settings.get('dissoc_start_pt')}")
    print(f"  End Point: {settings.get('dissoc_end_pt')}")

    print("\nSampling:")
    print(f"  Delta T: {settings.get('delta_t')} s")
    print(f"  Sampling Rate: {1/settings.get('delta_t', 0.2):.1f} Hz")


if __name__ == "__main__":
    ht_path = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292\HTSettings.efrd"

    settings = parse_ht_settings(ht_path)
    print_settings(settings)
