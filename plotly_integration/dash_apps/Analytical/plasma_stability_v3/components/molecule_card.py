"""
Molecule Card Component
Creates DBC card layout for each molecule with image, plots, and table
"""

from dash import html
import dash_bootstrap_components as dbc
from typing import Dict, List

from .plots import create_chromatogram_plot, create_trend_plot
from .tables import create_results_table


def create_molecule_card(
    molecule_id: str,
    molecule_image_url: str,
    conditions_data: Dict[str, List[Dict]],
    channels: List[str],
    show_shading: bool = False,
    show_drop_lines: bool = False,
    show_trend: bool = True,
    x_axis_range: List[float] = None,
    image_height: int = 350,
    plot_height: int = 500
) -> dbc.Card:
    """
    Create a comprehensive card for one molecule showing:
    - Left column: Molecule image, trend plot (optional), summary table
    - Right column: Chromatogram plots for each condition

    Args:
        molecule_id: Molecule identifier
        molecule_image_url: URL to molecule structure image
        conditions_data: Dict mapping condition name to list of sample data
                        Each sample: {day, timeseries_df, peak_areas}
        channels: List of channel names to plot
        show_shading: Whether to show peak region shading
        show_drop_lines: Whether to show peak boundary drop lines
        show_trend: Whether to show stability trend plot
        x_axis_range: X-axis range [min, max] in minutes
        image_height: Molecule image height in pixels
        plot_height: Plot height in pixels

    Returns:
        dbc.Card component
    """
    if x_axis_range is None:
        x_axis_range = [4, 12]
    # Create individual condition plots
    condition_plots = []
    for condition in sorted(conditions_data.keys()):
        samples = conditions_data[condition]
        plot = create_chromatogram_plot(
            condition_name=condition,
            sample_data=samples,
            channels=channels,
            show_shading=show_shading,
            show_drop_lines=show_drop_lines,
            x_axis_range=x_axis_range,
            plot_height=plot_height
        )
        condition_plots.append(
            dbc.Col(plot, md=6 if len(conditions_data) == 2 else 12)
        )

    # Create results table
    results_table = create_results_table(conditions_data)

    # Create trend plot (optional)
    trend_plot = create_trend_plot(molecule_id, conditions_data) if show_trend else None

    # Left column content (stacked vertically)
    left_column_items = [
        # Molecule image (larger)
        html.Div([
            html.Img(
                src=molecule_image_url,
                style={
                    'width': '100%',
                    'maxWidth': '350px',
                    'height': f'{image_height}px',
                    'objectFit': 'contain',
                    'borderRadius': '12px',
                    'border': '2px solid #e5e7eb',
                    'boxShadow': '0 4px 12px rgba(0,0,0,0.1)',
                    'backgroundColor': 'white'
                }
            )
        ], style={
            'display': 'flex',
            'justifyContent': 'center',
            'marginBottom': '12px'
        })
    ]

    # Add trend plot if enabled
    if show_trend and trend_plot:
        left_column_items.append(
            html.Div([
                html.H4(
                    "Stability Trend",
                    style={
                        'margin': '0 0 8px 0',
                        'color': '#374151',
                        'fontSize': '16px',
                        'fontWeight': '700',
                        'fontFamily': 'Arial, sans-serif'
                    }
                ),
                trend_plot
            ], style={'marginBottom': '12px'})
        )

    # Add results table
    left_column_items.append(
        html.Div([
            html.H4(
                "Change in Monomer by SEC",
                style={
                    'margin': '0 0 8px 0',
                    'color': '#374151',
                    'fontSize': '16px',
                    'fontWeight': '700',
                    'fontFamily': 'Arial, sans-serif'
                }
            ),
            results_table
        ])
    )

    # Build card with side-by-side layout
    card_content = dbc.Card(
        [
            dbc.CardBody([
                # Header with molecule ID
                html.Div([
                    html.H2(
                        molecule_id,
                        style={
                            'margin': '0',
                            'color': '#2563eb',
                            'fontSize': '28px',
                            'fontWeight': '800',
                            'fontFamily': 'Arial, sans-serif'
                        }
                    ),
                ], style={'marginBottom': '12px', 'borderBottom': '3px solid #2563eb', 'paddingBottom': '8px'}),

                # Main content: Side-by-side layout
                dbc.Row([
                    # Left column (30%): Image + Table + Trend
                    dbc.Col(
                        left_column_items,
                        md=4,
                        style={'padding': '16px', 'display': 'flex', 'flexDirection': 'column'}
                    ),

                    # Right column (70%): Chromatogram plots (full height)
                    dbc.Col([
                        html.Div(
                            dbc.Row(condition_plots, className='g-0'),
                            style={'height': '100%', 'display': 'flex', 'alignItems': 'stretch'}
                        )
                    ], md=8, style={'padding': '8px', 'display': 'flex', 'flexDirection': 'column'})
                ], style={'minHeight': '600px'})  # Ensure minimum height for proper stretch
            ])
        ],
        style={
            'backgroundColor': 'white',
            'borderRadius': '16px',
            'boxShadow': '0 4px 20px rgba(0,0,0,0.12)',
            'border': '1px solid #e5e7eb',
            'marginBottom': '32px'
        }
    )

    return card_content


def create_error_card(molecule_id: str, error_message: str) -> dbc.Card:
    """
    Create an error card when molecule data cannot be processed

    Args:
        molecule_id: Molecule identifier
        error_message: Error description

    Returns:
        dbc.Card component with error message
    """
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.I(className='fas fa-exclamation-triangle', style={
                    'fontSize': '32px',
                    'color': '#dc2626',
                    'marginBottom': '12px'
                }),
                html.H4(f"Error processing {molecule_id}", style={
                    'color': '#dc2626',
                    'fontWeight': '700',
                    'marginBottom': '8px'
                }),
                html.P(error_message, style={
                    'color': '#6b7280',
                    'fontSize': '14px'
                })
            ], style={'textAlign': 'center', 'padding': '32px'})
        ]),
        style={
            'backgroundColor': '#fee2e2',
            'borderRadius': '16px',
            'border': '2px solid #fca5a5',
            'marginBottom': '24px'
        }
    )
