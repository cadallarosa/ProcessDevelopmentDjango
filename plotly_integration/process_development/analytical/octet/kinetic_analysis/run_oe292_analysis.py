"""
Run OE292 Kinetics Analysis

Main script to process and analyze OE292 experiment data.
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
    """Main analysis workflow"""

    # Define paths
    base_dir = Path(__file__).parent.parent / "data" / "Kinetics" / "OE292"

    frd_directory = base_dir
    plate_mapping = base_dir / "octet_plate_mapping.csv"
    excel_results = base_dir / "Results" / "ExcelReport_2025_10_15 13_27_15.xlsx"

    print("="*80)
    print("OE292 Kinetics Analysis")
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

    # Get antibody list
    antibodies = organizer.get_all_antibodies()

    if not antibodies:
        print("\nERROR: No antibody data organized!")
        return

    print(f"\n4. Creating visualizations...")

    # Create output directory
    output_dir = base_dir / "analysis_output"
    output_dir.mkdir(exist_ok=True)

    # Plot first few antibodies
    print("\n   a. Creating concentration series plots...")
    for i, antibody in enumerate(antibodies[:5]):  # First 5 antibodies
        print(f"      - {antibody}")
        ab_data = organizer.get_antibody_data(antibody)

        fig = plot_concentration_series(
            ab_data,
            antibody,
            show_dissociation=True
        )

        # Save HTML
        output_file = output_dir / f"{antibody}_binding_curves.html"
        fig.write_html(str(output_file))

    # Create affinity ranking
    print("\n   b. Creating affinity ranking plot...")
    fig_ranking = plot_affinity_ranking(organizer.antibody_data, top_n=15)
    fig_ranking.write_html(str(output_dir / "affinity_ranking.html"))

    # Create heatmap
    print("\n   c. Creating response heatmap...")
    fig_heatmap = plot_kinetics_heatmap(organizer.antibody_data, metric='response')
    fig_heatmap.write_html(str(output_dir / "response_heatmap.html"))

    # Compare antibodies at one concentration
    print("\n   d. Creating comparison plot...")
    comparison_abs = antibodies[:4]  # First 4 antibodies
    fig_comparison = plot_comparison(
        organizer.antibody_data,
        comparison_abs,
        concentration=100.0  # 100 nM
    )
    fig_comparison.write_html(str(output_dir / "antibody_comparison_100nM.html"))

    print("\n" + "="*80)
    print("Analysis Complete!")
    print(f"\nOutput files saved to: {output_dir}")
    print("\nGenerated files:")
    print(f"  - Individual binding curves for first 5 antibodies")
    print(f"  - affinity_ranking.html")
    print(f"  - response_heatmap.html")
    print(f"  - antibody_comparison_100nM.html")
    print("="*80)

    # Print some statistics
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
        print(f"\nTop 5 Binders (lowest KD):")
        for i in range(min(5, len(kd_values))):
            idx = sorted_indices[i]
            ab = [ab for ab in antibodies if organizer.antibody_data[ab]['kinetics'].get('kd_m') == kd_values[idx]][0]
            print(f"  {i+1}. {ab}: KD = {kd_values[idx]:.2e} M")

    return organizer


if __name__ == "__main__":
    organizer = main()
