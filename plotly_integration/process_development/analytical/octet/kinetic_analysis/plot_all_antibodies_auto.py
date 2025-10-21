"""
Plot All Antibodies in Subplots - Auto Run

Creates a multi-panel figure with one subplot per antibody showing all concentration curves.
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from analyze_oe292 import load_oe292_data
from plot_all_antibodies import plot_all_antibodies_grid, plot_all_antibodies_single_page

if __name__ == "__main__":
    print("Loading OE292 data...")
    organizer = load_oe292_data()

    print("\nCreating grid layout visualization...")
    fig = plot_all_antibodies_grid(organizer, cols=4, show_dissociation=True)

    print("Opening plot in browser...")
    fig.show()

    print("\nVisualization complete!")
    print(f"Showing {len(organizer.get_all_antibodies())} antibodies with concentration series")
