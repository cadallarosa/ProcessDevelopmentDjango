"""
Octet Kinetics Dashboard

Interactive Dash app for visualizing Octet kinetics binding data from database.
Pattern based on octet_analysis_app_v2.py but simplified for kinetics data.

Features:
- Experiment selection modal with filterable table
- View all antibodies as subplots (grid layout)
- View single antibody with concentration series
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from django_plotly_dash import DjangoDash
from django.db.models import Q, Count, Prefetch
import logging
import io
import time
from functools import wraps

from plotly_integration.models import (
    OctetKineticsExperiment,
    OctetKineticsSensor
)

# Import signal processing functions from same package
from .dashboard_processing import process_sensor_data
from .kinetics_curve_fitting import (
    fit_1_1_langmuir_global,
    fit_dissociation_only
)

logger = logging.getLogger(__name__)


# Performance timing decorator
def time_function(func):
    """Decorator to time function execution and print results to console"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        print(f"⏱️  {func.__name__} took {elapsed:.3f}s")
        return result
    return wrapper


# Initialize Dash app
app = DjangoDash(
    "OctetKineticsDashboard",
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

# Styles
CARD_STYLE = {
    "margin": "10px 0",
    "padding": "15px",
    "border": "1px solid #dee2e6",
    "border-radius": "8px",
    "box-shadow": "0 2px 4px rgba(0,0,0,0.1)"
}

# Layout
app.layout = html.Div([
    # Data stores
    dcc.Store(id='selected-experiment', data=None),
    dcc.Store(id='experiment-data', data=None),
    dcc.Store(id='processed-plot-data', data=None),  # Store processed data for export
    dcc.Download(id='download-data'),  # Download component for exports

    # Experiment Selection Modal
    dbc.Modal(
        id="experiment-modal",
        size="xl",
        is_open=False,
        children=[
            dbc.ModalHeader(dbc.ModalTitle("Select Octet Kinetics Experiment")),
            dbc.ModalBody([
                # Filters
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Search:"),
                        dbc.Input(
                            id="experiment-search",
                            type="text",
                            placeholder="Filter by name or description...",
                            debounce=True
                        )
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Date Range:"),
                        dcc.DatePickerRange(
                            id="experiment-date-range",
                            display_format='YYYY-MM-DD',
                            style={"width": "100%"}
                        )
                    ], width=6),
                ], className="mb-3"),

                # Experiment table
                html.Div(id="experiment-table-container", style={"max-height": "400px", "overflow-y": "auto"}),
            ]),
            dbc.ModalFooter([
                dbc.Button("Close", id="close-modal-btn", color="secondary", className="me-2"),
                dbc.Button("Load Selected", id="load-experiment-btn", color="primary"),
            ])
        ]
    ),

    # Top Toolbar
    html.Div([
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            "Select Experiment",
                            id="select-experiment-btn",
                            color="primary",
                            className="me-2"
                        ),
                        html.Span(
                            id="current-experiment-text",
                            style={"font-weight": "bold", "color": "#0056b3"}
                        )
                    ], width=8),
                    dbc.Col([
                        html.Div(id="experiment-summary", style={"text-align": "right", "color": "#6c757d"})
                    ], width=4)
                ])
            ])
        ], style={"margin-bottom": "20px"})
    ]),

    # Main content area
    html.Div(id="main-content", children=[
        html.Div([
            html.H5("Please select an experiment to begin",
                   style={"text-align": "center", "color": "#6c757d", "margin-top": "50px"})
        ])
    ]),

], style={"max-width": "1800px", "margin": "0 auto", "padding": "20px"})


# Callbacks

@app.callback(
    Output("experiment-modal", "is_open"),
    [Input("select-experiment-btn", "n_clicks"),
     Input("close-modal-btn", "n_clicks"),
     Input("load-experiment-btn", "n_clicks")],
    [State("experiment-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_modal(open_clicks, close_clicks, load_clicks, is_open):
    """Toggle experiment selection modal"""
    # Simply toggle the modal state - this works without context checking
    # If any button is clicked, we toggle the modal
    return not is_open


@app.callback(
    Output("experiment-table-container", "children"),
    [Input("experiment-modal", "is_open"),
     Input("experiment-search", "value"),
     Input("experiment-date-range", "start_date"),
     Input("experiment-date-range", "end_date")]
)
def update_experiment_table(is_open, search_term, start_date, end_date):
    """Load and filter experiments for selection"""
    if not is_open:
        return html.Div()

    # Query kinetics experiments
    experiments = OctetKineticsExperiment.objects.annotate(
        sensor_count=Count('sensors')
    ).order_by('-start_datetime')

    # Apply filters
    if search_term:
        experiments = experiments.filter(
            Q(experiment_name__icontains=search_term) |
            Q(description__icontains=search_term)
        )

    if start_date:
        experiments = experiments.filter(start_datetime__gte=start_date)

    if end_date:
        experiments = experiments.filter(start_datetime__lte=end_date)

    # Convert to dataframe
    data = []
    for exp in experiments:
        data.append({
            'id': exp.id,
            'Experiment': exp.experiment_name,
            'Description': exp.description[:80] + '...' if len(exp.description) > 80 else exp.description,
            'Date': exp.start_datetime.strftime('%Y-%m-%d %H:%M') if exp.start_datetime else '',
            'Sensors': exp.sensor_count,
            'Type': exp.experiment_subtype,
        })

    if not data:
        return html.Div("No experiments found", className="alert alert-info")

    df = pd.DataFrame(data)

    return dash_table.DataTable(
        id='experiment-selection-table',
        columns=[
            {'name': col, 'id': col} for col in df.columns if col != 'id'
        ],
        data=df.to_dict('records'),
        row_selectable='single',
        selected_rows=[],
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontSize': '14px'
        },
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            },
            {
                'if': {'state': 'selected'},
                'backgroundColor': '#cfe2ff',
                'border': '1px solid #0d6efd'
            }
        ],
        page_size=10,
    )


@app.callback(
    [Output("selected-experiment", "data"),
     Output("current-experiment-text", "children")],
    Input("load-experiment-btn", "n_clicks"),
    [State("experiment-selection-table", "selected_rows"),
     State("experiment-selection-table", "data")]
)
def load_selected_experiment(n_clicks, selected_rows, table_data):
    """Load selected experiment"""
    if not n_clicks or not selected_rows or not table_data:
        return None, "No experiment selected"

    selected_row = table_data[selected_rows[0]]
    exp_name = selected_row['Experiment']

    # Get experiment ID by name
    try:
        experiment = OctetKineticsExperiment.objects.get(
            experiment_name=exp_name
        )

        return {
            'id': experiment.id,
            'name': experiment.experiment_name,
            'description': experiment.description
        }, f"Current: {experiment.experiment_name}"

    except OctetKineticsExperiment.DoesNotExist:
        return None, "Error loading experiment"


@app.callback(
    [Output("experiment-data", "data"),
     Output("experiment-summary", "children")],
    Input("selected-experiment", "data")
)
def load_experiment_data(exp_data):
    """Load data for selected experiment"""
    if not exp_data:
        return None, ""

    experiment_id = exp_data['id']

    # Query sensors - much simpler with new model!
    sensors = OctetKineticsSensor.objects.filter(
        experiment_id=experiment_id
    ).select_related('experiment')

    # Organize by antibody
    antibody_data = {}

    for sensor in sensors:
        antibody = sensor.antibody_id
        if antibody not in antibody_data:
            antibody_data[antibody] = {
                'concentrations': [],
                'kd': None,
                'sensor_ids': []
            }

        antibody_data[antibody]['concentrations'].append(sensor.concentration_nm)
        antibody_data[antibody]['sensor_ids'].append(sensor.id)

        # Get KD if available (stored directly on sensor)
        if sensor.kd_m:
            antibody_data[antibody]['kd'] = sensor.kd_m

    # Summary
    n_antibodies = len(antibody_data)
    total_sensors = sum(len(ab_data['concentrations']) for ab_data in antibody_data.values())

    summary = f"{n_antibodies} antibodies | {total_sensors} sensors"

    # Store antibody list for dropdown
    antibody_list = [
        {
            'label': f"{ab} (KD={data['kd']:.2e}M)" if data['kd'] else ab,
            'value': ab
        }
        for ab, data in sorted(antibody_data.items())
    ]

    return {
        'experiment_id': experiment_id,
        'antibodies': antibody_list,
        'n_antibodies': n_antibodies,
        'total_sensors': total_sensors
    }, summary


@app.callback(
    Output("main-content", "children"),
    Input("experiment-data", "data")
)
def update_main_content(exp_data):
    """Update main content area with controls and plot area"""
    if not exp_data:
        return html.Div([
            html.H5("Please select an experiment to begin",
                   style={"text-align": "center", "color": "#6c757d", "margin-top": "50px"})
        ])

    return html.Div([
        # Controls
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("View Mode:"),
                        dbc.RadioItems(
                            id="view-mode",
                            options=[
                                {"label": " All Antibodies (Grid)", "value": "grid"},
                                {"label": " Single Antibody", "value": "single"},
                            ],
                            value="single",
                            inline=True
                        )
                    ], width=3),
                    dbc.Col([
                        dbc.Label("Select Antibody:", id="antibody-label"),
                        dcc.Dropdown(
                            id="antibody-selector",
                            options=exp_data['antibodies'],
                            placeholder="Choose antibody...",
                            disabled=True
                        )
                    ], width=3, id="antibody-selector-col"),
                    dbc.Col([
                        dbc.Label("Grid Layout (columns):"),
                        dbc.Input(
                            id="grid-columns",
                            type="number",
                            value=4,
                            min=1,
                            max=8,
                            step=1,
                            size="sm"
                        )
                    ], width=2, id="grid-layout-col", style={"display": "none"}),
                    dbc.Col([
                        dbc.Label("Display Options:"),
                        dbc.Checklist(
                            id="display-options",
                            options=[
                                {"label": " Show KD", "value": "show_kd"},
                                {"label": " Show All Steps (Load/Baseline)", "value": "all_steps"},
                            ],
                            value=["show_kd"],
                            inline=True
                        )
                    ], width=4),
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Signal Processing:"),
                        dbc.Checklist(
                            id="processing-options",
                            options=[
                                {"label": " Baseline Align", "value": "baseline_align"},
                                {"label": " Reference Subtraction (0 nM)", "value": "reference_subtract"},
                                {"label": " Smooth (Filter)", "value": "apply_filter"},
                            ],
                            value=["baseline_align"],
                            inline=True
                        )
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Baseline Window (s - auto from middle 1/3 of baseline):"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Input(id="baseline-start", type="number", value=None, min=-1000, step=1, size="sm", placeholder="Auto")
                            ], width=6),
                            dbc.Col([
                                dbc.Input(id="baseline-end", type="number", value=None, min=-1000, step=1, size="sm", placeholder="Auto")
                            ], width=6),
                        ])
                    ], width=3, id="baseline-window-col"),
                    dbc.Col([
                        dbc.Label("Filter Window (Savitzky-Golay smoothing, must be odd):"),
                        dbc.Input(
                            id="filter-window",
                            type="number",
                            value=11,
                            min=5,
                            max=51,
                            step=2,
                            size="sm",
                            placeholder="11 points"
                        )
                    ], width=3, id="filter-window-col", style={"display": "none"}),
                ])
            ])
        ], style=CARD_STYLE),

        # Curve Fitting Controls (New Section)
        dbc.Card([
            dbc.CardBody([
                html.H6("Curve Fitting Options", className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Checklist(
                            id="enable-fitting",
                            options=[
                                {"label": " Enable Curve Fitting", "value": "enabled"}
                            ],
                            value=[],
                            inline=True
                        )
                    ], width=3),
                    dbc.Col([
                        dbc.Label("Fitting Model:", id="fitting-model-label", style={"color": "#6c757d"}),
                        dcc.Dropdown(
                            id="fitting-model",
                            options=[
                                {"label": "1:1 Langmuir (Global)", "value": "1:1_langmuir"},
                                {"label": "Dissociation Only (koff)", "value": "dissociation_only"},
                            ],
                            value="1:1_langmuir",
                            disabled=True,
                            clearable=False
                        )
                    ], width=3),
                    dbc.Col([
                        dbc.Label("Display Fitted Curves:", id="show-fitted-label", style={"color": "#6c757d"}),
                        html.Div(
                            id="show-fitted-curves-container",
                            children=[
                                dbc.Checklist(
                                    id="show-fitted-curves",
                                    options=[
                                        {"label": " Overlay Fits", "value": "overlay"},
                                        {"label": " Show Residuals", "value": "residuals"}
                                    ],
                                    value=["overlay"],
                                    inline=True
                                )
                            ],
                            style={"pointer-events": "none", "opacity": "0.5"}
                        )
                    ], width=3),
                    dbc.Col([
                        dbc.Label("Comparison Table:", id="show-comparison-label", style={"color": "#6c757d"}),
                        html.Div(
                            id="show-comparison-table-container",
                            children=[
                                dbc.Checklist(
                                    id="show-comparison-table",
                                    options=[
                                        {"label": " Show KD Comparison", "value": "show"}
                                    ],
                                    value=["show"],
                                    inline=True
                                )
                            ],
                            style={"pointer-events": "none", "opacity": "0.5"}
                        )
                    ], width=3),
                ])
            ])
        ], style=CARD_STYLE, id="fitting-controls-card"),

        # Plot and Export buttons
        html.Div([
            dbc.Button(
                "Generate Plot",
                id="plot-button",
                color="success",
                size="lg",
                className="mb-3 me-2"
            ),
            dbc.Button(
                "Export Data",
                id="export-button",
                color="info",
                size="lg",
                className="mb-3",
                disabled=True  # Initially disabled until plot is generated
            )
        ], style={"text-align": "center"}),

        # Comparison Table Area (shown above plot when fitting enabled)
        html.Div(id="comparison-table-container"),

        # Plot area
        dcc.Loading(
            id="loading-plot",
            type="circle",
            children=html.Div(id="plot-container")
        ),
    ])


@app.callback(
    [Output("antibody-selector", "disabled"),
     Output("antibody-label", "style"),
     Output("antibody-selector-col", "style"),
     Output("grid-layout-col", "style")],
    Input("view-mode", "value")
)
def toggle_view_mode_controls(view_mode):
    """Show/hide controls based on view mode"""
    if view_mode == "single":
        # Single antibody mode: show antibody selector, hide grid layout
        return (
            False,
            {"font-weight": "bold"},
            {},  # Show antibody selector column
            {"display": "none"}  # Hide grid layout column
        )
    else:
        # Grid mode: hide antibody selector, show grid layout
        return (
            True,
            {"font-weight": "normal", "color": "#6c757d"},
            {"display": "none"},  # Hide antibody selector column
            {}  # Show grid layout column
        )


@app.callback(
    Output("antibody-selector", "value"),
    [Input("experiment-data", "data"),
     Input("view-mode", "value")],
    State("antibody-selector", "value")
)
def auto_select_antibody(exp_data, view_mode, current_value):
    """Auto-select first antibody when switching to single mode"""
    # Only auto-select if in single mode and no antibody currently selected
    if not exp_data or view_mode != "single":
        return current_value

    # If no antibody selected, select the first one
    if not current_value and exp_data.get('antibodies'):
        return exp_data['antibodies'][0]['value']

    return current_value


@app.callback(
    Output("baseline-window-col", "style"),
    Input("processing-options", "value")
)
def toggle_baseline_window(processing_options):
    """Show/hide baseline window inputs based on baseline align checkbox"""
    if "baseline_align" in (processing_options or []):
        return {}  # Show
    else:
        return {"display": "none"}  # Hide


@app.callback(
    Output("filter-window-col", "style"),
    Input("processing-options", "value")
)
def toggle_filter_window(processing_options):
    """Show/hide filter window input based on filter checkbox"""
    if "apply_filter" in (processing_options or []):
        return {}  # Show
    else:
        return {"display": "none"}  # Hide


@app.callback(
    [Output("fitting-model", "disabled"),
     Output("show-fitted-curves-container", "style"),
     Output("show-comparison-table-container", "style"),
     Output("fitting-model-label", "style"),
     Output("show-fitted-label", "style"),
     Output("show-comparison-label", "style")],
    Input("enable-fitting", "value")
)
def toggle_fitting_controls(enable_fitting):
    """Enable/disable curve fitting controls"""
    is_enabled = "enabled" in (enable_fitting or [])

    if is_enabled:
        return (
            False,  # fitting-model enabled
            {"pointer-events": "auto", "opacity": "1"},  # show-fitted-curves enabled
            {"pointer-events": "auto", "opacity": "1"},  # show-comparison-table enabled
            {"font-weight": "bold"},  # fitting-model-label style
            {"font-weight": "bold"},  # show-fitted-label style
            {"font-weight": "bold"}   # show-comparison-label style
        )
    else:
        return (
            True,  # fitting-model disabled
            {"pointer-events": "none", "opacity": "0.5"},  # show-fitted-curves disabled
            {"pointer-events": "none", "opacity": "0.5"},  # show-comparison-table disabled
            {"color": "#6c757d"},  # fitting-model-label style
            {"color": "#6c757d"},  # show-fitted-label style
            {"color": "#6c757d"}   # show-comparison-label style
        )


@app.callback(
    [Output("plot-container", "children"),
     Output("comparison-table-container", "children"),
     Output("processed-plot-data", "data"),
     Output("export-button", "disabled")],
    Input("plot-button", "n_clicks"),
    [State("experiment-data", "data"),
     State("view-mode", "value"),
     State("antibody-selector", "value"),
     State("grid-columns", "value"),
     State("display-options", "value"),
     State("processing-options", "value"),
     State("baseline-start", "value"),
     State("baseline-end", "value"),
     State("filter-window", "value"),
     State("enable-fitting", "value"),
     State("fitting-model", "value"),
     State("show-fitted-curves", "value"),
     State("show-comparison-table", "value")]
)
def generate_plot(n_clicks, exp_data, view_mode, selected_antibody, grid_columns, display_options,
                 processing_options, baseline_start, baseline_end, filter_window,
                 enable_fitting, fitting_model, show_fitted_curves, show_comparison_table):
    """Generate kinetics plot based on selected mode"""
    if not n_clicks or not exp_data:
        return html.Div(), html.Div(), None, True

    experiment_id = exp_data['experiment_id']
    show_kd = "show_kd" in (display_options or [])
    show_all_steps = "all_steps" in (display_options or [])

    # Processing settings (baseline window will be auto-calculated from first sensor if None)
    processing_settings = {
        'baseline_align': "baseline_align" in (processing_options or []),
        'reference_subtract': "reference_subtract" in (processing_options or []),
        'apply_filter': "apply_filter" in (processing_options or []),
        'baseline_start': baseline_start if baseline_start is not None else None,  # Will be auto-calculated
        'baseline_end': baseline_end if baseline_end is not None else None,  # Will be auto-calculated
        'filter_window': filter_window or 11,
    }

    # Fitting settings
    fitting_enabled = "enabled" in (enable_fitting or [])
    fitting_settings = {
        'enabled': fitting_enabled,
        'model': fitting_model if fitting_enabled else None,
        'show_overlay': "overlay" in (show_fitted_curves or []) if fitting_enabled else False,
        'show_residuals': "residuals" in (show_fitted_curves or []) if fitting_enabled else False,
        'show_comparison': "show" in (show_comparison_table or []) if fitting_enabled else False,
    }

    try:
        if view_mode == "grid":
            cols = grid_columns or 4  # Default to 4 columns
            plot_output, plot_data = generate_grid_plot(experiment_id, show_kd, show_all_steps, processing_settings, cols, fitting_settings)
            comparison_table = html.Div()  # No comparison table in grid mode for now

            # Store plot data for export
            export_data = {
                'view_mode': 'grid',
                'experiment_id': experiment_id,
                'experiment_name': exp_data.get('name', 'Unknown'),
                'plot_data': plot_data
            }
            return plot_output, comparison_table, export_data, False  # Enable export button
        else:
            if not selected_antibody:
                return html.Div("Please select an antibody", className="alert alert-warning"), html.Div(), None, True
            plot_output, comparison_table, plot_data = generate_single_plot(
                experiment_id, selected_antibody, show_kd, show_all_steps,
                processing_settings, fitting_settings
            )

            # Store plot data for export
            export_data = {
                'view_mode': 'single',
                'experiment_id': experiment_id,
                'experiment_name': exp_data.get('name', 'Unknown'),
                'antibody': selected_antibody,
                'plot_data': plot_data
            }
            return plot_output, comparison_table, export_data, False  # Enable export button

    except Exception as e:
        logger.error(f"Error generating plot: {e}", exc_info=True)
        return html.Div(f"Error: {str(e)}", className="alert alert-danger"), html.Div(), None, True


@time_function
def normalize_full_experiment_time(sensor):
    """
    Normalize full experiment time so ASSOCIATION starts at 0

    Returns:
        time_array, response_array, step_info dict with normalized boundaries
    """
    # Get full timeseries
    time_full, response_full = sensor.get_full_timeseries()

    if len(time_full) == 0:
        return np.array([]), np.array([]), {}

    # Calculate step boundaries based on point counts FIRST
    experiment = sensor.experiment
    delta_t = experiment.delta_t

    # Calculate absolute time positions (from experiment start)
    loading_duration = sensor.loading_points * delta_t if sensor.loading_points > 0 else 0
    baseline_duration = sensor.baseline_points * delta_t if sensor.baseline_points > 0 else 0
    association_duration = sensor.association_points * delta_t if sensor.association_points > 0 else 0
    dissociation_duration = sensor.dissociation_points * delta_t if sensor.dissociation_points > 0 else 0

    # Association starts at this absolute time offset
    association_absolute_start = loading_duration + baseline_duration

    # Normalize all times so ASSOCIATION starts at 0
    experiment_start = time_full[0]
    time_normalized = time_full - experiment_start - association_absolute_start

    # Build step info with normalized times (association = 0)
    step_info = {
        'loading_start': -association_absolute_start,
        'loading_end': -association_absolute_start + loading_duration,
        'baseline_start': -baseline_duration,
        'baseline_end': 0,
        'association_start': 0,
        'association_end': association_duration,
        'dissociation_start': association_duration,
        'dissociation_end': association_duration + dissociation_duration,
    }

    # Store Y value at association start for axis range
    assoc_start_idx = sensor.loading_points + sensor.baseline_points
    if assoc_start_idx < len(response_full):
        step_info['association_start_y'] = response_full[assoc_start_idx]
    else:
        step_info['association_start_y'] = response_full[0] if len(response_full) > 0 else 0

    # Calculate Y-axis range for visible data (association + dissociation only)
    assoc_dissoc_start_idx = sensor.loading_points + sensor.baseline_points
    if assoc_dissoc_start_idx < len(response_full):
        visible_response = response_full[assoc_dissoc_start_idx:]
        step_info['visible_y_min'] = np.min(visible_response)
        step_info['visible_y_max'] = np.max(visible_response)
    else:
        step_info['visible_y_min'] = response_full.min() if len(response_full) > 0 else 0
        step_info['visible_y_max'] = response_full.max() if len(response_full) > 0 else 1

    # Auto-calculate baseline window from middle third of baseline step
    if baseline_duration > 0:
        baseline_third = baseline_duration / 3
        step_info['baseline_window_start'] = step_info['baseline_start'] + baseline_third
        step_info['baseline_window_end'] = step_info['baseline_end'] - baseline_third
    else:
        # No baseline step - default to early association (not recommended)
        step_info['baseline_window_start'] = 0
        step_info['baseline_window_end'] = 10

    return time_normalized, response_full, step_info


@time_function
def generate_grid_plot(experiment_id, show_kd, show_all_steps, processing_settings, cols=4, fitting_settings=None):
    """
    Generate grid of all antibodies with configurable column layout
    Returns: (plot_component, plot_data_dict)
    """
    print(f"🔵 Starting grid plot generation for experiment {experiment_id}")

    # For grid mode, fitting is disabled for now (too complex with multiple antibodies)
    # Could be added later with individual fits per antibody
    # Query sensors - NO JOINS NEEDED!
    t0 = time.time()
    sensors = OctetKineticsSensor.objects.filter(
        experiment_id=experiment_id
    ).select_related('experiment')
    sensor_list = list(sensors)  # Force query evaluation
    print(f"  ├─ Database query: {time.time() - t0:.3f}s ({len(sensor_list)} sensors)")

    # Organize data by antibody
    antibody_data = {}
    first_step_info = None  # Store step boundaries from first sensor
    baseline_window_start = None  # Consistent baseline for all sensors
    baseline_window_end = None

    # Track Y-axis minimum for visible data (association + dissociation)
    all_y_min = []

    # Timing for data processing
    t_data_processing = time.time()

    for sensor in sensor_list:
        antibody = sensor.antibody_id
        concentration = sensor.concentration_nm

        if antibody not in antibody_data:
            antibody_data[antibody] = {
                'concentrations': {},
                'kd': None,
            }

            # Get KD - stored directly on sensor!
            if sensor.kd_m:
                antibody_data[antibody]['kd'] = sensor.kd_m

        # ALWAYS get full time series data with normalization
        time_array, response_array, step_info = normalize_full_experiment_time(sensor)

        # Store first sensor's step info for axis ranges and baseline window
        if first_step_info is None:
            first_step_info = step_info
            # Use first sensor's baseline window for ALL sensors (consistent)
            baseline_window_start = step_info['baseline_window_start']
            baseline_window_end = step_info['baseline_window_end']

        if len(time_array) > 0:
            # Use auto-calculated baseline window if not manually specified
            baseline_start = processing_settings['baseline_start']
            baseline_end = processing_settings['baseline_end']
            if baseline_start is None or baseline_end is None:
                # Use consistent baseline window from first sensor
                baseline_start = baseline_window_start
                baseline_end = baseline_window_end

            # Apply signal processing if requested
            time_array, response_array = process_sensor_data(
                time_array,
                response_array,
                baseline_align=processing_settings['baseline_align'],
                baseline_start=baseline_start,
                baseline_end=baseline_end,
                normalize=False,  # Never normalize
                apply_filter=processing_settings['apply_filter'],
                filter_window=processing_settings['filter_window'],
                filter_polyorder=3
            )

            antibody_data[antibody]['concentrations'][concentration] = {
                'time': time_array,
                'response': response_array,
            }

    print(f"  ├─ Data loading & processing: {time.time() - t_data_processing:.3f}s")

    # Apply reference subtraction if requested (AFTER baseline correction)
    t_ref_subtract = time.time()
    if processing_settings['reference_subtract']:
        for antibody in antibody_data:
            ab_data = antibody_data[antibody]

            # Find the 0.0 nM reference sensor data for this antibody
            reference_data = ab_data['concentrations'].get(0.0)

            if reference_data:
                ref_time = reference_data['time']
                ref_response = reference_data['response']

                # Subtract reference from all concentrations (including 0.0 nM itself)
                for conc in ab_data['concentrations']:
                    conc_data = ab_data['concentrations'][conc]
                    conc_time = conc_data['time']
                    conc_response = conc_data['response']

                    # Make sure arrays are same length (they should be)
                    if len(conc_time) == len(ref_time):
                        # Subtract reference response
                        conc_data['response'] = conc_response - ref_response
        print(f"  ├─ Reference subtraction: {time.time() - t_ref_subtract:.3f}s")

    # Track Y-minimum for axis scaling AFTER all processing
    for antibody in antibody_data:
        ab_data = antibody_data[antibody]
        for conc in ab_data['concentrations']:
            conc_data = ab_data['concentrations'][conc]
            time_array = conc_data['time']
            response_array = conc_data['response']

            # Track Y-minimum of processed data in visible window (association + dissociation)
            visible_mask = time_array >= first_step_info['association_start']
            if np.any(visible_mask):
                visible_response = response_array[visible_mask]
                all_y_min.append(np.min(visible_response))

    # Create subplot figure
    t_plot_creation = time.time()
    antibodies = sorted(antibody_data.keys())
    n_antibodies = len(antibodies)

    if n_antibodies == 0:
        return html.Div("No data found", className="alert alert-warning")

    print(f"  ├─ Creating subplot for {n_antibodies} antibodies in {cols} columns")

    # Calculate rows based on number of columns
    rows = int(np.ceil(n_antibodies / cols))

    # Create subplot titles
    subplot_titles = []
    for ab in antibodies:
        title = ab
        if show_kd and antibody_data[ab]['kd']:
            title += f"<br>KD={antibody_data[ab]['kd']:.2e}M"
        subplot_titles.append(title)

    # Adjust vertical spacing based on number of columns
    # Fewer columns = fewer rows = need less spacing
    if cols <= 2:
        v_spacing = 0.04  # Tight spacing for 1-2 columns
    elif cols == 3:
        v_spacing = 0.06  # Medium spacing for 3 columns
    else:
        v_spacing = 0.08  # Default spacing for 4+ columns

    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=subplot_titles,
        vertical_spacing=v_spacing,
        horizontal_spacing=0.06,
    )

    # Plot each antibody
    for idx, antibody in enumerate(antibodies):
        row = (idx // cols) + 1
        col = (idx % cols) + 1

        ab_data = antibody_data[antibody]
        concentrations = sorted(ab_data['concentrations'].keys())

        # Improved color scale with better differentiation
        colors = [
            '#440154',  # Dark purple
            '#3b528b',  # Dark blue
            '#21908c',  # Teal
            '#5dc863',  # Green
            '#fde724',  # Yellow
            '#fd9f28',  # Orange
            '#e85d0d'   # Red-orange
        ]

        # Plot each concentration
        for conc_idx, conc in enumerate(concentrations):
            data = ab_data['concentrations'][conc]
            time = data['time']
            response = data['response']

            color = colors[conc_idx % len(colors)]

            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=response,
                    mode='lines',
                    name=f'{conc} nM',
                    line=dict(width=1.5, color=color),
                    showlegend=(idx == 0),
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

    # Add step boundary vertical lines to all subplots (ALWAYS show, using normalized times)
    try:
        if first_step_info:
            # Build steps list from step_info
            steps = []

            if first_step_info['loading_end'] > 0:
                steps.append(('Loading', first_step_info['loading_start'], first_step_info['loading_end']))

            if first_step_info['baseline_end'] > first_step_info['baseline_start']:
                steps.append(('Baseline', first_step_info['baseline_start'], first_step_info['baseline_end']))

            if first_step_info['association_end'] > first_step_info['association_start']:
                steps.append(('Association', first_step_info['association_start'], first_step_info['association_end']))

            if first_step_info['dissociation_end'] > first_step_info['dissociation_start']:
                steps.append(('Dissociation', first_step_info['dissociation_start'], first_step_info['dissociation_end']))

            # Add vertical lines for each step boundary
            for step_name, start_time, end_time in steps:
                step_midpoint = (start_time + end_time) / 2

                for idx in range(n_antibodies):
                    row = (idx // cols) + 1
                    col = (idx % cols) + 1

                    # Add vertical line at step start
                    fig.add_vline(
                        x=start_time,
                        line_dash="dash",
                        line_color="gray",
                        line_width=0.8,
                        opacity=0.4,
                        row=row,
                        col=col
                    )

                    # ALWAYS show all step labels (only on first row to avoid clutter)
                    if row == 1:
                        fig.add_annotation(
                            x=step_midpoint,
                            y=0.98,
                            yref="paper",
                            text=step_name,
                            showarrow=False,
                            font=dict(size=8, color="darkgray"),
                            textangle=-90,
                            xanchor="center",
                            yanchor="top",
                            row=row,
                            col=col
                        )
    except Exception as e:
        logger.warning(f"Could not add step boundaries to grid: {e}")

    # Update layout
    fig.update_layout(
        title=f'Kinetics: {n_antibodies} Antibodies',
        height=300 * rows,
        width=1600,
        template='plotly_white',
        hovermode='closest',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # Update axes
    y_axis_label = 'Response (nm)'

    # Set x-axis range based on show_all_steps
    if first_step_info and not show_all_steps:
        # Zoom to show only association + dissociation
        x_min = first_step_info['association_start'] - 5  # Small buffer
        x_max = first_step_info['dissociation_end'] + 5
        fig.update_xaxes(title_text='Time (s)', showgrid=True, range=[x_min, x_max])
    else:
        # Show all steps
        fig.update_xaxes(title_text='Time (s)', showgrid=True)

    # Set y-axis minimum based on visible data when zoomed (let max auto-scale)
    if not show_all_steps and all_y_min:
        # When zoomed to kinetics view, set Y-min from visible data only
        y_min = min(all_y_min)
        y_buffer = abs(y_min) * 0.05 if y_min != 0 else 0.1  # 5% buffer below
        fig.update_yaxes(title_text=y_axis_label, showgrid=True, range=[y_min - y_buffer, None])
    else:
        # When showing all steps, let it auto-range from all data
        fig.update_yaxes(title_text=y_axis_label, showgrid=True)

    print(f"  ├─ Plot creation & rendering: {time.time() - t_plot_creation:.3f}s")

    # Prepare export data - convert numpy arrays to lists for JSON serialization
    t_export_prep = time.time()
    export_data = {
        'step_info': first_step_info  # Include step boundaries for phase separation in export
    }
    for antibody, ab_data in antibody_data.items():
        export_data[antibody] = {}
        for conc, conc_data in ab_data['concentrations'].items():
            export_data[antibody][str(conc)] = {
                'time': conc_data['time'].tolist() if isinstance(conc_data['time'], np.ndarray) else conc_data['time'],
                'response': conc_data['response'].tolist() if isinstance(conc_data['response'], np.ndarray) else conc_data['response']
            }
    print(f"  └─ Export data preparation: {time.time() - t_export_prep:.3f}s")

    return dcc.Graph(figure=fig, config={'displayModeBar': True}), export_data


@time_function
def generate_single_plot(experiment_id, antibody, show_kd, show_all_steps, processing_settings, fitting_settings=None):
    """
    Generate detailed plot for single antibody
    Returns: (plot_component, comparison_table_component, plot_data_dict)
    """
    print(f"🟢 Starting single plot generation for antibody {antibody}")

    # Default fitting settings if not provided
    if fitting_settings is None:
        fitting_settings = {'enabled': False}

    # Query sensors for this antibody - NO JOINS NEEDED!
    t0 = time.time()
    sensors = OctetKineticsSensor.objects.filter(
        experiment_id=experiment_id,
        antibody_id=antibody
    ).select_related('experiment')
    sensor_list = list(sensors)
    print(f"  ├─ Database query: {time.time() - t0:.3f}s ({len(sensor_list)} sensors)")

    if not sensor_list:
        return html.Div(f"No data found for {antibody}", className="alert alert-warning")

    # Get KD - stored directly on sensor!
    kd_value = None
    first_sensor = sensor_list[0]
    if first_sensor.kd_m:
        kd_value = first_sensor.kd_m

    # Organize data by concentration
    concentration_data = {}
    step_info = None
    baseline_window_start = None
    baseline_window_end = None

    # Track Y-axis minimum for visible data (association + dissociation)
    all_y_min = []

    # Timing for data processing
    t_data_processing = time.time()

    for sensor in sensor_list:
        concentration = sensor.concentration_nm

        # ALWAYS get full time series data with normalization
        time_array, response_array, sensor_step_info = normalize_full_experiment_time(sensor)

        # Store step info from first sensor
        if step_info is None:
            step_info = sensor_step_info
            # Use first sensor's baseline window for ALL sensors (consistent)
            baseline_window_start = step_info['baseline_window_start']
            baseline_window_end = step_info['baseline_window_end']

        if len(time_array) > 0:
            # Use auto-calculated baseline window if not manually specified
            baseline_start = processing_settings['baseline_start']
            baseline_end = processing_settings['baseline_end']
            if baseline_start is None or baseline_end is None:
                # Use consistent baseline window from first sensor
                baseline_start = baseline_window_start
                baseline_end = baseline_window_end

            # Apply signal processing if requested
            time_array, response_array = process_sensor_data(
                time_array,
                response_array,
                baseline_align=processing_settings['baseline_align'],
                baseline_start=baseline_start,
                baseline_end=baseline_end,
                normalize=False,  # Never normalize
                apply_filter=processing_settings['apply_filter'],
                filter_window=processing_settings['filter_window'],
                filter_polyorder=3
            )

            concentration_data[concentration] = {
                'time': time_array,
                'response': response_array,
            }

    print(f"  ├─ Data loading & processing: {time.time() - t_data_processing:.3f}s")

    # Apply reference subtraction if requested (AFTER baseline correction)
    t_ref_subtract = time.time()
    if processing_settings['reference_subtract']:
        # Find the 0.0 nM reference sensor data
        reference_data = concentration_data.get(0.0)

        if reference_data:
            ref_time = reference_data['time']
            ref_response = reference_data['response']

            # Subtract reference from all concentrations (including 0.0 nM itself)
            for conc in concentration_data:
                conc_data = concentration_data[conc]
                conc_time = conc_data['time']
                conc_response = conc_data['response']

                # Make sure arrays are same length (they should be)
                if len(conc_time) == len(ref_time):
                    # Subtract reference response
                    conc_data['response'] = conc_response - ref_response
        print(f"  ├─ Reference subtraction: {time.time() - t_ref_subtract:.3f}s")

    # Track Y-minimum for axis scaling AFTER all processing
    for conc in concentration_data:
        conc_data = concentration_data[conc]
        time_array = conc_data['time']
        response_array = conc_data['response']

        # Track Y-minimum of processed data in visible window (association + dissociation)
        visible_mask = time_array >= step_info['association_start']
        if np.any(visible_mask):
            visible_response = response_array[visible_mask]
            all_y_min.append(np.min(visible_response))

    # Create plot
    t_plot_creation = time.time()
    fig = go.Figure()

    concentrations = sorted(concentration_data.keys())

    # Improved color scale with better differentiation
    # Using a viridis-like scale from dark blue -> cyan -> yellow
    colors = [
        '#440154',  # Dark purple (lowest concentration)
        '#3b528b',  # Dark blue
        '#21908c',  # Teal
        '#5dc863',  # Green
        '#fde724',  # Yellow
        '#fd9f28',  # Orange
        '#e85d0d'   # Red-orange (highest concentration)
    ]

    for conc_idx, conc in enumerate(concentrations):
        data = concentration_data[conc]
        color = colors[conc_idx % len(colors)]

        fig.add_trace(
            go.Scatter(
                x=data['time'],
                y=data['response'],
                mode='lines',
                name=f'{conc} nM',
                line=dict(width=2, color=color),
                hovertemplate=f'{conc} nM<br>' +
                              'Time: %{x:.1f}s<br>' +
                              'Response: %{y:.2f} nm<br>' +
                              '<extra></extra>'
            )
        )

    # Add step boundary vertical lines (ALWAYS show, using normalized times)
    try:
        if step_info:
            # Build steps list from step_info
            steps = []

            if step_info['loading_end'] > 0:
                steps.append(('Loading', step_info['loading_start'], step_info['loading_end']))

            if step_info['baseline_end'] > step_info['baseline_start']:
                steps.append(('Baseline', step_info['baseline_start'], step_info['baseline_end']))

            if step_info['association_end'] > step_info['association_start']:
                steps.append(('Association', step_info['association_start'], step_info['association_end']))

            if step_info['dissociation_end'] > step_info['dissociation_start']:
                steps.append(('Dissociation', step_info['dissociation_start'], step_info['dissociation_end']))

            # Add vertical lines for each step boundary
            for step_name, start_time, end_time in steps:
                step_midpoint = (start_time + end_time) / 2

                # Add vertical line at step start
                fig.add_vline(
                    x=start_time,
                    line_dash="dash",
                    line_color="gray",
                    line_width=1,
                    opacity=0.5
                )

                # ALWAYS show all step labels
                fig.add_annotation(
                    x=step_midpoint,
                    y=0.98,
                    yref="paper",
                    text=step_name,
                    showarrow=False,
                    font=dict(size=10, color="darkgray"),
                    textangle=-90,
                    xanchor="center",
                    yanchor="top"
                )
    except Exception as e:
        logger.warning(f"Could not add step boundaries: {e}")

    # ========================================
    # CURVE FITTING (if enabled)
    # ========================================
    fit_result = None
    comparison_table = html.Div()  # Default empty

    if fitting_settings.get('enabled', False):
        t_curve_fitting = time.time()
        print(f"  ├─ Starting curve fitting with model: {fitting_settings.get('model')}")
        try:
            fitting_model = fitting_settings.get('model', '1:1_langmuir')

            if fitting_model == '1:1_langmuir':
                # Perform global fit with step_info for proper phase separation
                fit_result = fit_1_1_langmuir_global(concentration_data, step_info)

                if fit_result.get('success'):
                    # Add fitted curves to plot - ONLY ASSOCIATION PHASE
                    if fitting_settings.get('show_overlay', False):
                        for conc_idx, conc in enumerate(concentrations):
                            if conc == 0.0:
                                continue  # Skip reference

                            if conc in fit_result['fitted_curves']:
                                fitted_data = fit_result['fitted_curves'][conc]
                                color = colors[conc_idx % len(colors)]

                                # Plot ONLY the association fit
                                assoc_fit = fitted_data['association']
                                fig.add_trace(
                                    go.Scatter(
                                        x=assoc_fit['time'],
                                        y=assoc_fit['response'],
                                        mode='lines',
                                        name=f'{conc} nM (Assoc Fit)',
                                        line=dict(width=2, color=color, dash='dash'),
                                        hovertemplate=f'{conc} nM ASSOCIATION FIT<br>' +
                                                      'Time: %{x:.1f}s<br>' +
                                                      'Response: %{y:.2f} nm<br>' +
                                                      '<extra></extra>'
                                    )
                                )

                                # Optionally plot dissociation fit too (if you want it)
                                # dissoc_fit = fitted_data['dissociation']
                                # fig.add_trace(
                                #     go.Scatter(
                                #         x=dissoc_fit['time'],
                                #         y=dissoc_fit['response'],
                                #         mode='lines',
                                #         name=f'{conc} nM (Dissoc Fit)',
                                #         line=dict(width=2, color=color, dash='dot'),
                                #         showlegend=False
                                #     )
                                # )

                    # Create comparison table if requested
                    if fitting_settings.get('show_comparison', False):
                        comparison_data = []

                        # Add vendor KD vs fitted KD
                        fitted_kd = fit_result.get('fitted_kd')
                        fitted_kon = fit_result.get('fitted_kon')
                        fitted_koff = fit_result.get('fitted_koff')

                        # Get vendor values from sensor
                        vendor_kd = kd_value if kd_value else None
                        vendor_ka = first_sensor.ka_1_ms if first_sensor.ka_1_ms else None
                        vendor_kdis = first_sensor.kdis_1_s if first_sensor.kdis_1_s else None

                        comparison_data.append({
                            'Parameter': 'k_on (1/Ms)',
                            'Vendor': f'{vendor_ka:.2e}' if vendor_ka else 'N/A',
                            'Fitted': f'{fitted_kon:.2e}' if fitted_kon else 'N/A',
                            'Δ (%)': f'{((fitted_kon - vendor_ka) / vendor_ka * 100):.1f}' if (vendor_ka and fitted_kon) else 'N/A'
                        })

                        comparison_data.append({
                            'Parameter': 'k_off (1/s)',
                            'Vendor': f'{vendor_kdis:.2e}' if vendor_kdis else 'N/A',
                            'Fitted': f'{fitted_koff:.2e}' if fitted_koff else 'N/A',
                            'Δ (%)': f'{((fitted_koff - vendor_kdis) / vendor_kdis * 100):.1f}' if (vendor_kdis and fitted_koff) else 'N/A'
                        })

                        comparison_data.append({
                            'Parameter': 'K_D (M)',
                            'Vendor': f'{vendor_kd:.2e}' if vendor_kd else 'N/A',
                            'Fitted': f'{fitted_kd:.2e}' if fitted_kd else 'N/A',
                            'Δ (%)': f'{((fitted_kd - vendor_kd) / vendor_kd * 100):.1f}' if (vendor_kd and fitted_kd) else 'N/A'
                        })

                        # Add fit quality metrics
                        avg_r_squared = np.mean([
                            q['assoc_r_squared']
                            for q in fit_result.get('fit_quality', {}).values()
                        ])
                        avg_rmse = np.mean([
                            q['assoc_rmse']
                            for q in fit_result.get('fit_quality', {}).values()
                        ])

                        comparison_table = dbc.Card([
                            dbc.CardBody([
                                html.H6("Kinetic Parameters Comparison", className="mb-3"),
                                dbc.Row([
                                    dbc.Col([
                                        dash_table.DataTable(
                                            data=comparison_data,
                                            columns=[
                                                {'name': 'Parameter', 'id': 'Parameter'},
                                                {'name': 'Vendor Analysis', 'id': 'Vendor'},
                                                {'name': 'Fitted (1:1 Langmuir)', 'id': 'Fitted'},
                                                {'name': 'Difference (%)', 'id': 'Δ (%)'},
                                            ],
                                            style_cell={
                                                'textAlign': 'left',
                                                'padding': '10px',
                                                'fontSize': '14px'
                                            },
                                            style_header={
                                                'backgroundColor': '#f8f9fa',
                                                'fontWeight': 'bold'
                                            },
                                            style_data_conditional=[
                                                {
                                                    'if': {'row_index': 'odd'},
                                                    'backgroundColor': '#f8f9fa'
                                                }
                                            ]
                                        )
                                    ], width=8),
                                    dbc.Col([
                                        html.H6("Fit Quality", className="mb-2"),
                                        html.P([
                                            html.Strong("Avg R²: "),
                                            f"{avg_r_squared:.4f}"
                                        ], className="mb-1"),
                                        html.P([
                                            html.Strong("Avg RMSE: "),
                                            f"{avg_rmse:.3f} nm"
                                        ], className="mb-1"),
                                        html.P([
                                            html.Strong("Model: "),
                                            "1:1 Langmuir (Global)"
                                        ], className="mb-1", style={"font-size": "12px", "color": "#6c757d"})
                                    ], width=4)
                                ])
                            ])
                        ], style=CARD_STYLE, className="mb-3")

                else:
                    # Fitting failed
                    error_msg = fit_result.get('error', 'Unknown error')
                    comparison_table = dbc.Alert(
                        f"Curve fitting failed: {error_msg}",
                        color="warning",
                        className="mb-3"
                    )

        except Exception as e:
            logger.error(f"Error during curve fitting: {e}", exc_info=True)
            comparison_table = dbc.Alert(
                f"Error during curve fitting: {str(e)}",
                color="danger",
                className="mb-3"
            )

        if fitting_settings.get('enabled', False):
            print(f"  ├─ Curve fitting: {time.time() - t_curve_fitting:.3f}s")

    print(f"  ├─ Plot creation: {time.time() - t_plot_creation:.3f}s")

    # Update layout
    title = f'{antibody}'
    if show_kd and kd_value:
        title += f' (KD = {kd_value:.2e} M)'

    # Add fit info to title if fitted
    if fit_result and fit_result.get('success'):
        fitted_kd = fit_result.get('fitted_kd')
        title += f' | Fitted KD = {fitted_kd:.2e} M'

    # Set Y-axis label
    y_axis_label = 'Response (nm)'

    fig.update_layout(
        title=title,
        xaxis_title='Time (s)',
        yaxis_title=y_axis_label,
        height=600,
        template='plotly_white',
        hovermode='closest',
        legend=dict(
            title='Concentration',
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )

    # Set x-axis range based on show_all_steps
    if step_info and not show_all_steps:
        # Zoom to show only association + dissociation
        x_min = step_info['association_start'] - 5  # Small buffer
        x_max = step_info['dissociation_end'] + 5
        fig.update_xaxes(showgrid=True, range=[x_min, x_max])
    else:
        # Show all steps
        fig.update_xaxes(showgrid=True)

    # Set y-axis minimum based on visible data when zoomed (let max auto-scale)
    if not show_all_steps and all_y_min:
        # When zoomed to kinetics view, set Y-min from visible data only
        y_min = min(all_y_min)
        y_buffer = abs(y_min) * 0.05 if y_min != 0 else 0.1  # 5% buffer below
        fig.update_yaxes(showgrid=True, range=[y_min - y_buffer, None])
    else:
        # When showing all steps, let it auto-range from all data
        fig.update_yaxes(showgrid=True)

    # Prepare export data - convert numpy arrays to lists for JSON serialization
    t_export_prep = time.time()
    export_data = {
        'step_info': step_info  # Include step boundaries for phase separation in export
    }
    for conc, conc_data in concentration_data.items():
        export_data[str(conc)] = {
            'time': conc_data['time'].tolist() if isinstance(conc_data['time'], np.ndarray) else conc_data['time'],
            'response': conc_data['response'].tolist() if isinstance(conc_data['response'], np.ndarray) else conc_data['response']
        }
    print(f"  └─ Export data preparation: {time.time() - t_export_prep:.3f}s")

    # Return plot, comparison table, and export data
    return dcc.Graph(figure=fig, config={'displayModeBar': True}), comparison_table, export_data


@app.callback(
    Output("download-data", "data"),
    Input("export-button", "n_clicks"),
    State("processed-plot-data", "data"),
    prevent_initial_call=True
)
def export_plot_data(n_clicks, plot_data):
    """Export plot data to CSV file with association and dissociation phases separated"""
    if not n_clicks or not plot_data:
        return None

    try:
        view_mode = plot_data.get('view_mode')
        experiment_name = plot_data.get('experiment_name', 'Unknown')
        data = plot_data.get('plot_data', {})

        # Extract step_info for phase boundaries
        step_info = data.get('step_info', {})
        assoc_start = step_info.get('association_start', 0)
        assoc_end = step_info.get('association_end', 0)
        dissoc_start = step_info.get('dissociation_start', assoc_end)
        dissoc_end = step_info.get('dissociation_end', dissoc_start)

        if view_mode == 'single':
            # Single antibody mode - export with separate association and dissociation sheets
            antibody = plot_data.get('antibody', 'Unknown')

            # Create association phase DataFrame
            assoc_dict = {}
            dissoc_dict = {}

            # Process each concentration
            for conc_str, conc_data in data.items():
                if conc_str == 'step_info':
                    continue

                conc_nm = float(conc_str)
                time_array = conc_data['time']
                response_array = conc_data['response']

                # Split into association and dissociation based on time
                assoc_mask = [(t >= assoc_start and t < dissoc_start) for t in time_array]
                dissoc_mask = [(t >= dissoc_start and t <= dissoc_end) for t in time_array]

                assoc_times = [t for t, m in zip(time_array, assoc_mask) if m]
                assoc_responses = [r for r, m in zip(response_array, assoc_mask) if m]

                dissoc_times = [t for t, m in zip(time_array, dissoc_mask) if m]
                dissoc_responses = [r for r, m in zip(response_array, dissoc_mask) if m]

                # Store in dictionaries
                if not assoc_dict:  # First time, add time column
                    assoc_dict['Time (s)'] = assoc_times
                assoc_dict[f'Response_{conc_nm}_nM (nm)'] = assoc_responses

                if not dissoc_dict:  # First time, add time column
                    dissoc_dict['Time (s)'] = dissoc_times
                dissoc_dict[f'Response_{conc_nm}_nM (nm)'] = dissoc_responses

            # Create combined DataFrame with phase column
            assoc_df = pd.DataFrame(assoc_dict)
            assoc_df['Phase'] = 'Association'

            dissoc_df = pd.DataFrame(dissoc_dict)
            dissoc_df['Phase'] = 'Dissociation'

            # Combine both phases
            combined_df = pd.concat([assoc_df, dissoc_df], ignore_index=True)

            # Reorder columns to have Phase first
            cols = ['Phase', 'Time (s)'] + [c for c in combined_df.columns if c not in ['Phase', 'Time (s)']]
            combined_df = combined_df[cols]

            # Export to CSV
            output = io.StringIO()
            combined_df.to_csv(output, index=False)
            csv_string = output.getvalue()

            filename = f"{experiment_name}_{antibody}_kinetics_by_phase.csv"

            return dict(content=csv_string, filename=filename)

        else:
            # Grid mode - export with phase information
            all_rows = []

            for antibody, antibody_data in data.items():
                if antibody == 'step_info':
                    continue

                for conc_str, conc_data in antibody_data.items():
                    conc_nm = float(conc_str)
                    time_array = conc_data['time']
                    response_array = conc_data['response']

                    # Create rows for this antibody-concentration combination
                    for i in range(len(time_array)):
                        t = time_array[i]
                        # Determine phase
                        if assoc_start <= t < dissoc_start:
                            phase = 'Association'
                        elif dissoc_start <= t <= dissoc_end:
                            phase = 'Dissociation'
                        else:
                            phase = 'Other'

                        all_rows.append({
                            'Antibody': antibody,
                            'Concentration (nM)': conc_nm,
                            'Phase': phase,
                            'Time (s)': t,
                            'Response (nm)': response_array[i]
                        })

            df = pd.DataFrame(all_rows)

            # Export to CSV
            output = io.StringIO()
            df.to_csv(output, index=False)
            csv_string = output.getvalue()

            filename = f"{experiment_name}_all_antibodies_kinetics_by_phase.csv"

            return dict(content=csv_string, filename=filename)

    except Exception as e:
        logger.error(f"Error exporting data: {e}", exc_info=True)
        print(f"❌ Error exporting data: {e}")
        return None


if __name__ == '__main__':
    app.run_server(debug=True)
