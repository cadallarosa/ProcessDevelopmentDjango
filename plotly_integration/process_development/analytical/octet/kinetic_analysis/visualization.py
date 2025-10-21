"""
Visualization Module

Create interactive Plotly visualizations for Octet kinetics data.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Optional


def plot_concentration_series(antibody_data: Dict,
                               antibody_id: str,
                               show_dissociation: bool = True) -> go.Figure:
    """
    Plot binding curves for all concentrations of one antibody

    Args:
        antibody_data: Dictionary from KineticsDataOrganizer
        antibody_id: Antibody identifier
        show_dissociation: Whether to show dissociation phase

    Returns:
        Plotly figure
    """
    concentrations = sorted(antibody_data['concentrations'].keys())
    color = antibody_data['color']

    fig = go.Figure()

    # Plot each concentration
    for conc in concentrations:
        data = antibody_data['concentrations'][conc]
        time = data['time']
        signal = data['signal']

        # Truncate to association only if requested
        if not show_dissociation:
            mask = time <= 180
            time = time[mask]
            signal = signal[mask]

        fig.add_trace(go.Scatter(
            x=time,
            y=signal,
            mode='lines',
            name=f'{conc} nM',
            line=dict(width=2),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                          'Time: %{x:.1f}s<br>' +
                          'Response: %{y:.2f} nm<br>' +
                          '<extra></extra>'
        ))

    # Add vertical line at association/dissociation transition
    if show_dissociation:
        fig.add_vline(
            x=180,
            line_dash="dash",
            line_color="gray",
            annotation_text="Dissociation",
            annotation_position="top"
        )

    # Get kinetic parameters
    kinetics = antibody_data['kinetics']
    kd_text = f"KD = {kinetics['kd_m']:.2e} M" if kinetics['kd_m'] else "KD = N/A"
    ka_text = f"ka = {kinetics['ka_1_ms']:.2e} 1/Ms" if kinetics['ka_1_ms'] else "ka = N/A"
    kdis_text = f"kdis = {kinetics['kdis_1_s']:.2e} 1/s" if kinetics['kdis_1_s'] else "kdis = N/A"
    r2_text = f"R² = {kinetics['r_squared']:.3f}" if kinetics['r_squared'] else "R² = N/A"

    fig.update_layout(
        title=f'{antibody_id}<br><sub>{kd_text} | {ka_text} | {kdis_text} | {r2_text}</sub>',
        xaxis_title='Time (s)',
        yaxis_title='Response (nm)',
        hovermode='closest',
        template='plotly_white',
        height=600,
        showlegend=True,
        legend=dict(
            title='Concentration',
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        )
    )

    return fig


def plot_comparison(antibody_data_dict: Dict,
                   antibody_ids: List[str],
                   concentration: float) -> go.Figure:
    """
    Compare multiple antibodies at same concentration

    Args:
        antibody_data_dict: Dictionary of all antibody data
        antibody_ids: List of antibody IDs to compare
        concentration: Concentration to compare (nM)

    Returns:
        Plotly figure
    """
    fig = go.Figure()

    for antibody_id in antibody_ids:
        if antibody_id not in antibody_data_dict:
            continue

        antibody_data = antibody_data_dict[antibody_id]

        if concentration not in antibody_data['concentrations']:
            continue

        data = antibody_data['concentrations'][concentration]
        color = antibody_data['color']

        fig.add_trace(go.Scatter(
            x=data['time'],
            y=data['signal'],
            mode='lines',
            name=antibody_id,
            line=dict(color=color, width=2),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                          'Time: %{x:.1f}s<br>' +
                          'Response: %{y:.2f} nm<br>' +
                          '<extra></extra>'
        ))

    fig.update_layout(
        title=f'Antibody Comparison at {concentration} nM',
        xaxis_title='Time (s)',
        yaxis_title='Response (nm)',
        hovermode='closest',
        template='plotly_white',
        height=600,
        showlegend=True
    )

    return fig


def plot_affinity_ranking(antibody_data_dict: Dict,
                          top_n: Optional[int] = None) -> go.Figure:
    """
    Rank antibodies by affinity (KD)

    Args:
        antibody_data_dict: Dictionary of all antibody data
        top_n: Show only top N antibodies (None = all)

    Returns:
        Plotly figure
    """
    # Extract KD values
    antibodies = []
    kd_values = []
    colors = []

    for antibody_id, data in antibody_data_dict.items():
        kd = data['kinetics'].get('kd_m')
        if kd and kd > 0:
            antibodies.append(antibody_id)
            kd_values.append(kd)
            colors.append(data['color'])

    # Sort by KD (lowest = best affinity)
    sorted_indices = np.argsort(kd_values)
    antibodies = [antibodies[i] for i in sorted_indices]
    kd_values = [kd_values[i] for i in sorted_indices]
    colors = [colors[i] for i in sorted_indices]

    # Limit to top N
    if top_n:
        antibodies = antibodies[:top_n]
        kd_values = kd_values[:top_n]
        colors = colors[:top_n]

    # Create bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=antibodies,
            y=kd_values,
            marker_color=colors,
            text=[f'{kd:.2e} M' for kd in kd_values],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>KD = %{y:.2e} M<extra></extra>'
        )
    ])

    fig.update_layout(
        title='Antibody Affinity Ranking (KD)',
        xaxis_title='Antibody',
        yaxis_title='KD (M)',
        yaxis_type='log',
        template='plotly_white',
        height=600,
        xaxis_tickangle=-45
    )

    return fig


def plot_kinetics_heatmap(antibody_data_dict: Dict,
                          metric: str = 'kd_m') -> go.Figure:
    """
    Create heatmap of steady-state responses across antibodies and concentrations

    Args:
        antibody_data_dict: Dictionary of all antibody data
        metric: Which metric to plot ('kd_m', 'ka_1_ms', 'kdis_1_s', or 'response')

    Returns:
        Plotly figure
    """
    antibodies = sorted(antibody_data_dict.keys())

    # Get all unique concentrations
    all_concentrations = set()
    for data in antibody_data_dict.values():
        all_concentrations.update(data['concentrations'].keys())
    concentrations = sorted(list(all_concentrations))

    # Build matrix
    matrix = np.zeros((len(antibodies), len(concentrations)))

    for i, antibody_id in enumerate(antibodies):
        data = antibody_data_dict[antibody_id]

        for j, conc in enumerate(concentrations):
            if conc in data['concentrations']:
                if metric == 'response':
                    # Use max signal as response
                    signal = data['concentrations'][conc]['signal']
                    matrix[i, j] = np.max(signal)
                elif metric in data['kinetics']:
                    matrix[i, j] = data['kinetics'][metric] or 0

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=[f'{c} nM' for c in concentrations],
        y=antibodies,
        colorscale='Viridis',
        hovertemplate='Antibody: %{y}<br>Conc: %{x}<br>Value: %{z:.2e}<extra></extra>'
    ))

    metric_titles = {
        'kd_m': 'KD (M)',
        'ka_1_ms': 'ka (1/Ms)',
        'kdis_1_s': 'kdis (1/s)',
        'response': 'Max Response (nm)'
    }

    fig.update_layout(
        title=f'Kinetics Heatmap: {metric_titles.get(metric, metric)}',
        xaxis_title='Concentration',
        yaxis_title='Antibody',
        template='plotly_white',
        height=800
    )

    return fig


def create_interactive_dashboard(antibody_data_dict: Dict) -> go.Figure:
    """
    Create multi-panel interactive dashboard

    Args:
        antibody_data_dict: Dictionary of all antibody data

    Returns:
        Plotly figure with subplots
    """
    # Get first antibody for initial display
    antibodies = sorted(antibody_data_dict.keys())
    if not antibodies:
        return go.Figure()

    first_antibody = antibodies[0]
    first_data = antibody_data_dict[first_antibody]

    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            f'{first_antibody} - Binding Curves',
            'Affinity Ranking',
            'Kinetics Parameters',
            'Response Heatmap'
        ),
        specs=[
            [{"type": "scatter"}, {"type": "bar"}],
            [{"type": "table"}, {"type": "heatmap"}]
        ]
    )

    # Panel 1: Binding curves for first antibody
    concentrations = sorted(first_data['concentrations'].keys())
    for conc in concentrations:
        data = first_data['concentrations'][conc]
        fig.add_trace(
            go.Scatter(
                x=data['time'],
                y=data['signal'],
                mode='lines',
                name=f'{conc} nM',
                showlegend=True
            ),
            row=1, col=1
        )

    # Panel 2: Affinity ranking (simplified)
    kd_values = []
    ab_names = []
    for ab in antibodies[:10]:  # Top 10
        kd = antibody_data_dict[ab]['kinetics'].get('kd_m')
        if kd:
            kd_values.append(kd)
            ab_names.append(ab)

    if kd_values:
        sorted_idx = np.argsort(kd_values)
        fig.add_trace(
            go.Bar(
                x=[ab_names[i] for i in sorted_idx],
                y=[kd_values[i] for i in sorted_idx],
                showlegend=False
            ),
            row=1, col=2
        )

    # Panel 3: Parameters table
    kinetics = first_data['kinetics']
    fig.add_trace(
        go.Table(
            header=dict(values=['Parameter', 'Value']),
            cells=dict(values=[
                ['KD (M)', 'ka (1/Ms)', 'kdis (1/s)', 'R²'],
                [
                    f"{kinetics['kd_m']:.2e}" if kinetics['kd_m'] else 'N/A',
                    f"{kinetics['ka_1_ms']:.2e}" if kinetics['ka_1_ms'] else 'N/A',
                    f"{kinetics['kdis_1_s']:.2e}" if kinetics['kdis_1_s'] else 'N/A',
                    f"{kinetics['r_squared']:.3f}" if kinetics['r_squared'] else 'N/A',
                ]
            ])
        ),
        row=2, col=1
    )

    fig.update_layout(
        height=1000,
        showlegend=True,
        template='plotly_white'
    )

    return fig


if __name__ == "__main__":
    print("Visualization module loaded.")
    print("Use with KineticsDataOrganizer to create plots.")
