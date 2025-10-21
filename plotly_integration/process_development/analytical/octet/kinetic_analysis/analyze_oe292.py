"""
OE292 Analysis - Simple API

Easy-to-use functions to load and visualize OE292 data.
Use this in interactive Python sessions or notebooks.
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from data_organizer import KineticsDataOrganizer
from visualization import (
    plot_concentration_series,
    plot_comparison,
    plot_affinity_ranking,
    plot_kinetics_heatmap
)


def load_oe292_data():
    """
    Load OE292 experiment data

    Returns:
        KineticsDataOrganizer: Organizer with loaded data
    """
    # Define paths
    base_dir = Path(__file__).parent.parent / "data" / "Kinetics" / "OE292"

    frd_directory = base_dir
    plate_mapping = base_dir / "octet_plate_mapping.csv"
    excel_results = base_dir / "Results" / "ExcelReport_2025_10_15 13_27_15.xlsx"

    print("Loading OE292 data...")

    # Initialize organizer
    organizer = KineticsDataOrganizer(
        str(frd_directory),
        str(plate_mapping),
        str(excel_results)
    )

    # Load FRD files
    organizer.load_all_frd_files(pattern="251013_*.frd")

    # Organize by antibody
    organizer.organize_by_antibody(process_data=True)

    print(f"\nLoaded {len(organizer.get_all_antibodies())} antibodies")

    return organizer


def plot_antibody(organizer, antibody_id, show=True):
    """
    Plot concentration series for one antibody

    Args:
        organizer: KineticsDataOrganizer
        antibody_id: Antibody ID (e.g., 'SI-157X66_P5568')
        show: Whether to display the plot

    Returns:
        Plotly figure
    """
    ab_data = organizer.get_antibody_data(antibody_id)

    if ab_data is None:
        print(f"Antibody {antibody_id} not found!")
        return None

    fig = plot_concentration_series(ab_data, antibody_id, show_dissociation=True)

    if show:
        fig.show()

    return fig


def plot_all_antibodies(organizer, show=True):
    """
    Plot concentration series for all antibodies

    Args:
        organizer: KineticsDataOrganizer
        show: Whether to display plots

    Returns:
        List of Plotly figures
    """
    antibodies = organizer.get_all_antibodies()
    figures = []

    for antibody in antibodies:
        print(f"Plotting {antibody}...")
        fig = plot_antibody(organizer, antibody, show=show)
        figures.append(fig)

    return figures


def compare_antibodies(organizer, antibody_ids, concentration=100.0, show=True):
    """
    Compare multiple antibodies at same concentration

    Args:
        organizer: KineticsDataOrganizer
        antibody_ids: List of antibody IDs
        concentration: Concentration in nM (default: 100.0)
        show: Whether to display the plot

    Returns:
        Plotly figure
    """
    fig = plot_comparison(
        organizer.antibody_data,
        antibody_ids,
        concentration=concentration
    )

    if show:
        fig.show()

    return fig


def plot_ranking(organizer, top_n=None, show=True):
    """
    Plot affinity ranking

    Args:
        organizer: KineticsDataOrganizer
        top_n: Number of top antibodies to show (None = all)
        show: Whether to display the plot

    Returns:
        Plotly figure
    """
    fig = plot_affinity_ranking(organizer.antibody_data, top_n=top_n)

    if show:
        fig.show()

    return fig


def plot_heatmap(organizer, metric='response', show=True):
    """
    Plot heatmap of responses or kinetic parameters

    Args:
        organizer: KineticsDataOrganizer
        metric: 'response', 'kd_m', 'ka_1_ms', or 'kdis_1_s'
        show: Whether to display the plot

    Returns:
        Plotly figure
    """
    fig = plot_kinetics_heatmap(organizer.antibody_data, metric=metric)

    if show:
        fig.show()

    return fig


def get_antibody_summary(organizer, antibody_id):
    """
    Get summary of antibody data

    Args:
        organizer: KineticsDataOrganizer
        antibody_id: Antibody ID

    Returns:
        Dictionary with summary info
    """
    ab_data = organizer.get_antibody_data(antibody_id)

    if ab_data is None:
        return None

    concentrations = sorted(ab_data['concentrations'].keys())
    kinetics = ab_data['kinetics']

    summary = {
        'antibody_id': antibody_id,
        'num_concentrations': len(concentrations),
        'concentrations_nm': concentrations,
        'color': ab_data['color'],
        'kd_m': kinetics.get('kd_m'),
        'ka_1_ms': kinetics.get('ka_1_ms'),
        'kdis_1_s': kinetics.get('kdis_1_s'),
        'r_squared': kinetics.get('r_squared'),
    }

    return summary


def print_summary(organizer):
    """
    Print summary of all antibodies

    Args:
        organizer: KineticsDataOrganizer
    """
    antibodies = organizer.get_all_antibodies()

    print("="*80)
    print(f"OE292 Data Summary - {len(antibodies)} Antibodies")
    print("="*80)

    for antibody in antibodies:
        summary = get_antibody_summary(organizer, antibody)

        print(f"\n{antibody}")
        print(f"  Concentrations: {len(summary['concentrations_nm'])}")

        if summary['kd_m']:
            print(f"  KD = {summary['kd_m']:.2e} M")
            print(f"  ka = {summary['ka_1_ms']:.2e} 1/Ms")
            print(f"  kdis = {summary['kdis_1_s']:.2e} 1/s")
            print(f"  R² = {summary['r_squared']:.3f}")
        else:
            print("  Kinetics: N/A")

    print("\n" + "="*80)


# Example usage
if __name__ == "__main__":
    # Load data
    organizer = load_oe292_data()

    # Print summary
    print_summary(organizer)

    # Get antibody list
    antibodies = organizer.get_all_antibodies()

    if antibodies:
        # Plot first antibody
        print(f"\nPlotting {antibodies[0]}...")
        plot_antibody(organizer, antibodies[0])

        # Plot ranking
        print("\nPlotting affinity ranking...")
        plot_ranking(organizer)

        # Plot heatmap
        print("\nPlotting response heatmap...")
        plot_heatmap(organizer)

        # Compare antibodies if we have multiple
        if len(antibodies) >= 2:
            print("\nComparing antibodies at 100 nM...")
            compare_antibodies(organizer, antibodies[:2], concentration=100.0)
