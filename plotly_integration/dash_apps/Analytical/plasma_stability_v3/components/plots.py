"""
Plot Components
Create SEC chromatogram visualizations
"""

import plotly.graph_objects as go
from dash import dcc, html
from typing import List, Dict
import pandas as pd


def get_y_value_at_time(ts_data: pd.DataFrame, channel: str, target_time: float) -> float:
    """
    Get the y-value at a specific time point from timeseries data.
    Uses linear interpolation if exact time doesn't exist.

    Args:
        ts_data: DataFrame with 'time' and channel columns
        channel: Channel name (e.g., 'channel_1')
        target_time: Target time in minutes

    Returns:
        Y-value at the target time
    """
    if channel not in ts_data.columns:
        return 0

    # Find closest time points
    time_col = ts_data['time']

    # Check if exact time exists
    exact_match = ts_data[time_col == target_time]
    if not exact_match.empty:
        return exact_match[channel].iloc[0]

    # Linear interpolation
    before = ts_data[time_col <= target_time]
    after = ts_data[time_col >= target_time]

    if before.empty or after.empty:
        # Outside range, use closest point
        closest_idx = (time_col - target_time).abs().idxmin()
        return ts_data.loc[closest_idx, channel]

    t1, y1 = before.iloc[-1]['time'], before.iloc[-1][channel]
    t2, y2 = after.iloc[0]['time'], after.iloc[0][channel]

    if t2 == t1:
        return y1

    # Linear interpolation formula
    y_interpolated = y1 + (y2 - y1) * (target_time - t1) / (t2 - t1)
    return y_interpolated


def create_chromatogram_plot(
    condition_name: str,
    sample_data: List[Dict],
    channels: List[str],
    show_shading: bool = False,
    show_drop_lines: bool = False,
    x_axis_range: List[float] = None,
    plot_height: int = 500
) -> dcc.Graph:
    """
    Create an SEC chromatogram plot for one condition

    Args:
        condition_name: Name of the condition (e.g., "Plasma", "Buffer")
        sample_data: List of dicts with {day, timeseries_df, peak_areas}
        channels: List of channel names to plot (e.g., ['channel_1'])
        show_shading: Whether to show peak region shading
        show_drop_lines: Whether to show peak boundary drop lines
        x_axis_range: X-axis range [min, max] in minutes
        plot_height: Plot height in pixels

    Returns:
        dcc.Graph component
    """
    if x_axis_range is None:
        x_axis_range = [4, 12]
    if not sample_data:
        return html.Div(
            f"No data for {condition_name}",
            style={
                'padding': '60px 20px',
                'textAlign': 'center',
                'color': '#9ca3af',
                'backgroundColor': '#f9fafb',
                'borderRadius': '12px',
                'border': '2px dashed #e5e7eb'
            }
        )

    # Create figure
    fig = go.Figure()

    # Color palette
    colors = ['#3b82f6', '#f97316', '#10b981', '#ec4899', '#8b5cf6', '#f59e0b']

    for idx, sample in enumerate(sample_data):
        ts_data = sample['timeseries_df']
        day = sample['day']
        peak_areas = sample.get('peak_areas')

        color = colors[idx % len(colors)]
        day_label = f'D{day}'

        # Plot chromatogram for each channel
        for channel in channels:
            if channel in ts_data.columns:
                fig.add_trace(go.Scatter(
                    x=ts_data['time'],
                    y=ts_data[channel],
                    mode='lines',
                    name=day_label,
                    line=dict(color=color, width=2),
                    showlegend=True,
                    hovertemplate=f'<b>{day_label}</b><br>Time: %{{x:.2f}} min<br>UV280: %{{y:.4f}}<extra></extra>'
                ))

        # Add peak shading if requested and peak data available
        if show_shading and peak_areas:
            # Monomer region (main peak)
            fig.add_vrect(
                x0=peak_areas['main_start'],
                x1=peak_areas['main_end'],
                fillcolor=color,
                opacity=0.15,
                line_width=0,
                annotation_text="Monomer" if idx == 0 else "",
                annotation_position="top left"
            )

        # Add drop lines if requested and peak data available
        if show_drop_lines and peak_areas and channel in ts_data.columns:
            # Define peak regions to show drop lines for
            peak_regions = [
                ('main_start', 'main_end', 'Monomer'),
                ('hmw_start', 'hmw_end', 'HMW'),
                ('lmw_start', 'lmw_end', 'LMW')
            ]

            for start_key, end_key, peak_name in peak_regions:
                # Check if this peak region exists in the data
                if start_key in peak_areas and end_key in peak_areas:
                    start_time = peak_areas[start_key]
                    end_time = peak_areas[end_key]

                    # Skip if times are None or invalid
                    if start_time is None or end_time is None:
                        continue

                    # Get y-values at the drop line positions
                    y_start = get_y_value_at_time(ts_data, channel, start_time)
                    y_end = get_y_value_at_time(ts_data, channel, end_time)

                    # Add start drop line
                    fig.add_shape(
                        type='line',
                        x0=start_time,
                        x1=start_time,
                        y0=0,
                        y1=y_start,
                        line=dict(color=color, width=2, dash='dot'),
                        opacity=0.7,
                        layer='below'
                    )

                    # Add invisible scatter point for hover text on start line
                    fig.add_trace(go.Scatter(
                        x=[start_time],
                        y=[y_start / 2],  # Middle of the line
                        mode='markers',
                        marker=dict(size=0.1, color=color, opacity=0),
                        showlegend=False,
                        hovertemplate=f'<b>{day_label} - {peak_name} Start</b><br>Time: {start_time:.2f} min<extra></extra>'
                    ))

                    # Add end drop line
                    fig.add_shape(
                        type='line',
                        x0=end_time,
                        x1=end_time,
                        y0=0,
                        y1=y_end,
                        line=dict(color=color, width=2, dash='dot'),
                        opacity=0.7,
                        layer='below'
                    )

                    # Add invisible scatter point for hover text on end line
                    fig.add_trace(go.Scatter(
                        x=[end_time],
                        y=[y_end / 2],  # Middle of the line
                        mode='markers',
                        marker=dict(size=0.1, color=color, opacity=0),
                        showlegend=False,
                        hovertemplate=f'<b>{day_label} - {peak_name} End</b><br>Time: {end_time:.2f} min<extra></extra>'
                    ))

    # Update layout
    fig.update_layout(
        title={
            'text': f"<b>{condition_name} - Stability</b>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16, 'color': '#374151', 'family': 'Arial'}
        },
        xaxis_title="Time (Minutes)",
        yaxis_title="UV280 (AU)",
        template='plotly_white',
        height=plot_height,
        showlegend=True,
        legend=dict(
            x=0.98,  # Inside plot area, right side
            y=0.98,  # Top of plot area
            xanchor='right',
            yanchor='top',
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='#e5e7eb',
            borderwidth=1
        ),
        hovermode='closest',
        margin=dict(l=60, r=60, t=60, b=20),  # Reduced right and bottom margins
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    # Style axes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='#f3f4f6',
        zeroline=False,
        showline=True,
        linewidth=1,
        linecolor='#d1d5db',
        range=x_axis_range
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='#f3f4f6',
        zeroline=False,
        showline=True,
        linewidth=1,
        linecolor='#d1d5db'
    )

    return dcc.Graph(
        figure=fig,
        config={
            'displayModeBar': 'hover',
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }
    )


def create_trend_plot(molecule_id: str, conditions_data: Dict[str, List[Dict]]) -> dcc.Graph:
    """
    Create a trend plot showing monomer % over time for all conditions

    Args:
        molecule_id: Molecule identifier for title
        conditions_data: Dict mapping condition name to list of sample data

    Returns:
        dcc.Graph component
    """
    fig = go.Figure()

    # Color palette for different conditions
    colors = ['#ec4899', '#10b981', '#3b82f6', '#f59e0b', '#8b5cf6']

    for idx, (condition, samples) in enumerate(sorted(conditions_data.items())):
        if not samples:
            continue

        days = [s['day'] for s in samples]
        monomer_pcts = [s.get('peak_areas', {}).get('monomer_pct', 0) for s in samples]

        fig.add_trace(go.Scatter(
            x=days,
            y=monomer_pcts,
            mode='lines+markers',
            name=condition,
            line=dict(color=colors[idx % len(colors)], width=3),
            marker=dict(size=10, symbol='circle'),
            hovertemplate=f'<b>{condition}</b><br>Day %{{x}}<br>Monomer: %{{y:.2f}}%<extra></extra>'
        ))

    fig.update_layout(
        title={
            'text': f"<b>{molecule_id} - Stability Trend</b>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16, 'color': '#374151', 'family': 'Arial'}
        },
        xaxis_title="Day",
        yaxis_title="Monomer (%)",
        template='plotly_white',
        height=400,
        showlegend=True,
        legend=dict(
            x=0.98,  # Inside plot area, right side
            y=0.98,  # Top of plot area
            xanchor='right',
            yanchor='top',
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='#e5e7eb',
            borderwidth=1
        ),
        hovermode='x unified',
        margin=dict(l=60, r=60, t=60, b=20),  # Reduced right and bottom margins
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    # Style axes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='#f3f4f6',
        zeroline=False,
        showline=True,
        linewidth=1,
        linecolor='#d1d5db'
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='#f3f4f6',
        zeroline=False,
        showline=True,
        linewidth=1,
        linecolor='#d1d5db',
        range=[0, 100]
    )

    return dcc.Graph(
        figure=fig,
        config={
            'displayModeBar': 'hover',
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }
    )
