"""
Plot All Antibodies in Subplots

Creates a multi-panel figure with one subplot per antibody showing all concentration curves.
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from analyze_oe292 import load_oe292_data
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np


def plot_all_antibodies_grid(organizer, cols=4, show_dissociation=True):
    """
    Create subplot grid with all antibodies

    Args:
        organizer: KineticsDataOrganizer
        cols: Number of columns in grid
        show_dissociation: Whether to show dissociation phase

    Returns:
        Plotly figure
    """
    antibodies = organizer.get_all_antibodies()
    n_antibodies = len(antibodies)

    # Calculate rows needed
    rows = int(np.ceil(n_antibodies / cols))

    # Create subplots
    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=[f'{ab}<br>KD={organizer.antibody_data[ab]["kinetics"]["kd_m"]:.2e}M'
                       if organizer.antibody_data[ab]["kinetics"]["kd_m"]
                       else ab
                       for ab in antibodies],
        vertical_spacing=0.08,
        horizontal_spacing=0.05,
        x_title='Time (s)',
        y_title='Response (nm)'
    )

    # Plot each antibody
    for idx, antibody in enumerate(antibodies):
        row = (idx // cols) + 1
        col = (idx % cols) + 1

        ab_data = organizer.get_antibody_data(antibody)
        concentrations = sorted(ab_data['concentrations'].keys())
        color = ab_data['color']

        # Plot each concentration
        for conc_idx, conc in enumerate(concentrations):
            data = ab_data['concentrations'][conc]
            time = data['time']
            signal = data['signal']

            # Truncate to association only if requested
            if not show_dissociation:
                mask = time <= 180
                time = time[mask]
                signal = signal[mask]

            # Create color gradient from light to dark based on concentration
            # Use the antibody's base color but vary opacity
            opacity = 0.3 + (conc_idx / len(concentrations)) * 0.7

            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=signal,
                    mode='lines',
                    name=f'{conc} nM',
                    line=dict(color=color, width=1.5),
                    opacity=opacity,
                    showlegend=(idx == 0),  # Only show legend for first antibody
                    legendgroup=f'{conc}',
                    hovertemplate=f'<b>{antibody}</b><br>' +
                                  f'{conc} nM<br>' +
                                  'Time: %{x:.1f}s<br>' +
                                  'Response: %{y:.2f} nm<br>' +
                                  '<extra></extra>'
                ),
                row=row,
                col=col
            )

        # Add vertical line at dissociation start if showing full curve
        if show_dissociation:
            fig.add_vline(
                x=180,
                line_dash="dash",
                line_color="gray",
                line_width=0.5,
                row=row,
                col=col
            )

    # Update layout
    fig.update_layout(
        title=f'OE292 Kinetics: {n_antibodies} Antibodies x 7 Concentrations',
        height=300 * rows,
        width=400 * cols,
        template='plotly_white',
        hovermode='closest'
    )

    # Update all x and y axes
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

    return fig


def plot_all_antibodies_single_page(organizer, show_dissociation=True):
    """
    Create a single scrollable page with all antibodies stacked vertically

    Args:
        organizer: KineticsDataOrganizer
        show_dissociation: Whether to show dissociation phase

    Returns:
        Plotly figure
    """
    antibodies = organizer.get_all_antibodies()
    n_antibodies = len(antibodies)

    # Create subplots - all in one column
    fig = make_subplots(
        rows=n_antibodies,
        cols=1,
        subplot_titles=[f'{ab} (KD={organizer.antibody_data[ab]["kinetics"]["kd_m"]:.2e} M, R²={organizer.antibody_data[ab]["kinetics"]["r_squared"]:.3f})'
                       if organizer.antibody_data[ab]["kinetics"]["kd_m"]
                       else ab
                       for ab in antibodies],
        vertical_spacing=0.02,
        shared_xaxes=True,
    )

    # Plot each antibody
    for idx, antibody in enumerate(antibodies, 1):
        ab_data = organizer.get_antibody_data(antibody)
        concentrations = sorted(ab_data['concentrations'].keys())

        # Plot each concentration
        for conc in concentrations:
            data = ab_data['concentrations'][conc]
            time = data['time']
            signal = data['signal']

            # Truncate to association only if requested
            if not show_dissociation:
                mask = time <= 180
                time = time[mask]
                signal = signal[mask]

            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=signal,
                    mode='lines',
                    name=f'{conc} nM',
                    line=dict(width=2),
                    showlegend=(idx == 1),  # Only show legend for first antibody
                    legendgroup=f'{conc}',
                    hovertemplate=f'<b>{antibody}</b><br>' +
                                  f'{conc} nM<br>' +
                                  'Time: %{x:.1f}s<br>' +
                                  'Response: %{y:.2f} nm<br>' +
                                  '<extra></extra>'
                ),
                row=idx,
                col=1
            )

        # Add vertical line at dissociation start
        if show_dissociation:
            fig.add_vline(
                x=180,
                line_dash="dash",
                line_color="gray",
                line_width=1,
                row=idx,
                col=1
            )

    # Update layout
    fig.update_layout(
        title=f'OE292 Kinetics: {n_antibodies} Antibodies x 7 Concentrations',
        height=250 * n_antibodies,  # Each subplot gets 250px
        template='plotly_white',
        hovermode='closest',
        showlegend=True
    )

    # Update axes
    fig.update_xaxes(title_text='Time (s)', row=n_antibodies, col=1)
    fig.update_yaxes(title_text='Response (nm)')

    return fig


if __name__ == "__main__":
    print("Loading OE292 data...")
    organizer = load_oe292_data()

    print("\nCreating subplot visualization...")
    print("Choose layout:")
    print("  1. Grid layout (4 columns)")
    print("  2. Single column (scrollable)")

    layout_choice = input("\nEnter choice (1 or 2) [default=1]: ").strip() or "1"

    if layout_choice == "2":
        print("\nCreating single column layout...")
        fig = plot_all_antibodies_single_page(organizer, show_dissociation=True)
    else:
        print("\nCreating grid layout...")
        fig = plot_all_antibodies_grid(organizer, cols=4, show_dissociation=True)

    print("Opening plot...")
    fig.show()

    # Optionally save
    save = input("\nSave to HTML? (y/n) [default=n]: ").strip().lower()
    if save == 'y':
        output_path = Path(__file__).parent.parent / "data" / "Kinetics" / "OE292" / "analysis_output" / "all_antibodies_subplots.html"
        fig.write_html(str(output_path))
        print(f"Saved to: {output_path}")
