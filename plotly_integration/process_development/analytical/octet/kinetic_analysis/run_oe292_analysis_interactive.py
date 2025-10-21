"""
Run OE292 Kinetics Analysis - Interactive Version

Display plots directly in IDE instead of saving to HTML files.
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


def main():
    """Main analysis workflow with interactive plots"""

    # Define paths
    base_dir = Path(__file__).parent.parent / "data" / "Kinetics" / "OE292"

    frd_directory = base_dir
    plate_mapping = base_dir / "octet_plate_mapping.csv"
    excel_results = base_dir / "Results" / "ExcelReport_2025_10_15 13_27_15.xlsx"

    print("="*80)
    print("OE292 Kinetics Analysis - Interactive Mode")
    print("="*80)

    # Initialize organizer
    print("\n1. Initializing data organizer...")
    organizer = KineticsDataOrganizer(
        str(frd_directory),
        str(plate_mapping),
        str(excel_results)
    )

    # Load FRD files
    print("\n2. Loading FRD files...")
    num_files = organizer.load_all_frd_files(pattern="251013_*.frd")

    if num_files == 0:
        print("ERROR: No FRD files found!")
        return

    # Organize by antibody
    print("\n3. Organizing data by antibody...")
    organizer.organize_by_antibody(process_data=True)

    # Print summary
    print("\n" + "="*80)
    print(organizer.summary())
    print("="*80)

    # Get antibody list
    antibodies = organizer.get_all_antibodies()

    if not antibodies:
        print("\nERROR: No antibody data organized!")
        return

    print(f"\n4. Creating interactive visualizations...")
    print("\nPlots will open in separate windows. Close each to continue.\n")

    # Plot concentration series for each antibody
    print(f"   Plotting {len(antibodies)} antibodies...")
    for i, antibody in enumerate(antibodies, 1):
        print(f"\n   {i}. {antibody}")
        ab_data = organizer.get_antibody_data(antibody)

        # Create concentration series plot
        fig = plot_concentration_series(
            ab_data,
            antibody,
            show_dissociation=True
        )

        # Show plot
        print(f"      Opening plot for {antibody}...")
        fig.show()

    # Create affinity ranking
    print("\n   Creating affinity ranking plot...")
    fig_ranking = plot_affinity_ranking(organizer.antibody_data, top_n=len(antibodies))
    fig_ranking.show()

    # Create heatmap
    print("\n   Creating response heatmap...")
    fig_heatmap = plot_kinetics_heatmap(organizer.antibody_data, metric='response')
    fig_heatmap.show()

    # Compare antibodies at one concentration
    if len(antibodies) >= 2:
        print("\n   Creating comparison plot...")
        comparison_abs = antibodies[:min(4, len(antibodies))]
        fig_comparison = plot_comparison(
            organizer.antibody_data,
            comparison_abs,
            concentration=100.0  # 100 nM
        )
        fig_comparison.show()

    # Print statistics
    print("\n" + "="*80)
    print("Data Statistics:")
    print("="*80)

    print(f"\nTotal antibodies: {len(antibodies)}")

    # Get KD distribution
    kd_values = []
    for antibody in antibodies:
        ab_data = organizer.get_antibody_data(antibody)
        kd = ab_data['kinetics'].get('kd_m')
        if kd and kd > 0:
            kd_values.append(kd)

    if kd_values:
        import numpy as np
        print(f"\nKD Statistics (n={len(kd_values)}):")
        print(f"  Min KD: {np.min(kd_values):.2e} M  (best affinity)")
        print(f"  Max KD: {np.max(kd_values):.2e} M  (worst affinity)")
        print(f"  Median KD: {np.median(kd_values):.2e} M")

        # Find best binders
        sorted_indices = np.argsort(kd_values)
        print(f"\nTop {min(5, len(kd_values))} Binders (lowest KD):")
        for i in range(min(5, len(kd_values))):
            idx = sorted_indices[i]
            ab = [ab for ab in antibodies if organizer.antibody_data[ab]['kinetics'].get('kd_m') == kd_values[idx]][0]
            print(f"  {i+1}. {ab}: KD = {kd_values[idx]:.2e} M")

    print("\n" + "="*80)
    print("Analysis Complete!")
    print("="*80)

    return organizer


if __name__ == "__main__":
    organizer = main()
