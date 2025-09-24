"""
Formulation Stability Visualization App
Advanced visualization and analysis tool for formulation stability data
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table, no_update, ALL, MATCH
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy import stats
from datetime import datetime
import json
import base64
import io

from plotly_integration.models import (
    FormulationExperiment,
    FormulationMatrix,
    FormulationComponent,
    FormulationSample
)

# Initialize the app
app = DjangoDash("FormulationVisualizationApp", external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
], suppress_callback_exceptions=True)

# Constants
STORAGE_COLOR_MAP = {
    '25C': '#2E86AB',  # Blue
    '40C': '#F24236',  # Red
    '4C': '#27AE60',   # Green
    '-80C': '#8E44AD', # Purple
    'FT': '#F39C12'    # Orange
}

Y_AXIS_OPTIONS = [
    {'label': 'SEC - HMW %', 'value': 'hmw'},
    {'label': 'SEC - Main %', 'value': 'main'},
    {'label': 'SEC - LMW %', 'value': 'lmw'},
    {'label': 'SEC - Total Impurities %', 'value': 'total_impurities'},
    {'label': 'Concentration (mg/mL)', 'value': 'concentration_mg_ml'},
    {'label': 'pH Measured', 'value': 'ph_measured'},
    {'label': 'Osmolality (mOsm/kg)', 'value': 'osmolality_measured'},
    {'label': 'Tm (°C)', 'value': 'tm_celsius'},
    {'label': 'Scattering Onset (°C)', 'value': 'scattering_onset'},
    {'label': 'SEC Total Area', 'value': 'total_area'}
]

def get_experiment_options():
    """Get available experiments for dropdown"""
    experiments = FormulationExperiment.objects.all().order_by('-created_date')
    return [{'label': f"{exp.experiment_id} - {exp.name}", 'value': exp.experiment_id}
            for exp in experiments]

def get_formulation_data(experiment_id):
    """Get all formulation data for an experiment"""
    if not experiment_id:
        return pd.DataFrame()

    samples = FormulationSample.objects.filter(
        formulation__experiment_id=experiment_id
    ).select_related('formulation').prefetch_related('formulation__components')

    data = []
    for sample in samples:
        # Get formulation components
        components = sample.formulation.components.all()
        buffers = [c for c in components if c.component_type == 'buffer']
        excipients = [c for c in components if c.component_type == 'excipient']

        buffer_str = ', '.join([f"{b.name} {b.concentration}{b.unit}" for b in buffers])
        excipient_str = ', '.join([f"{e.name} {e.concentration}{e.unit}" for e in excipients])

        # Calculate total impurities if SEC data available
        total_impurities = None
        if sample.hmw is not None and sample.lmw is not None:
            total_impurities = sample.hmw + sample.lmw

        data.append({
            'sample_id': sample.sample_id,
            'formulation_id': sample.formulation.formulation_id,
            'formulation_number': sample.formulation.formulation_number,
            'formulation_name': f"F{sample.formulation.formulation_number:02d}",
            'buffer_system': buffer_str,
            'excipients': excipient_str,
            'target_ph': sample.formulation.target_ph,
            'storage_condition': sample.storage_condition,
            'time_point_months': sample.time_point_months,
            'pull_date': sample.pull_date,
            'appearance': sample.appearance,
            'concentration_mg_ml': sample.concentration_mg_ml,
            'ph_measured': sample.ph_measured,
            'osmolality_measured': sample.osmolality_measured,
            'hmw': sample.hmw,
            'main': sample.main,
            'lmw': sample.lmw,
            'total_impurities': total_impurities,
            'total_area': sample.total_area,
            'tm_celsius': sample.tm_celsius,
            'scattering_onset': sample.scattering_onset,
            'sec_result_id': sample.sec_result_id,
            'notes': sample.notes,
            'analysis_date': sample.analysis_date
        })

    return pd.DataFrame(data)

def create_stability_plot(df, formulation_name, y_variable, show_regression=True, show_stats=True):
    """Create a stability plot for a single formulation"""
    fig = go.Figure()

    # Get unique storage conditions
    conditions = df['storage_condition'].unique()

    for condition in conditions:
        condition_df = df[df['storage_condition'] == condition].sort_values('time_point_months')

        # Remove rows with missing y values
        condition_df = condition_df.dropna(subset=[y_variable])

        if len(condition_df) == 0:
            continue

        # Add scatter points
        fig.add_trace(go.Scatter(
            x=condition_df['time_point_months'],
            y=condition_df[y_variable],
            mode='markers',
            name=f"{condition}",
            marker=dict(
                color=STORAGE_COLOR_MAP.get(condition, '#333'),
                size=10,
                line=dict(width=1, color='white')
            ),
            text=condition_df['sample_id'],
            hovertemplate='<b>%{text}</b><br>' +
                         f'{y_variable}: %{{y:.2f}}<br>' +
                         'Time: %{x} months<br>' +
                         '<extra></extra>'
        ))

        # Add regression line if requested and sufficient data
        if show_regression and len(condition_df) >= 2:
            x = condition_df['time_point_months'].values
            y = condition_df[y_variable].values

            # Calculate linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

            # Generate regression line
            x_line = np.linspace(x.min(), x.max() * 1.1, 100)
            y_line = slope * x_line + intercept

            fig.add_trace(go.Scatter(
                x=x_line,
                y=y_line,
                mode='lines',
                name=f"{condition} trend",
                line=dict(
                    color=STORAGE_COLOR_MAP.get(condition, '#333'),
                    dash='dash',
                    width=2
                ),
                showlegend=False,
                hovertemplate=f'Slope: {slope:.4f}<br>R²: {r_value**2:.3f}<extra></extra>'
            ))

            # Add statistics annotation if requested
            if show_stats:
                fig.add_annotation(
                    x=x.max() * 0.95,
                    y=y_line[-1],
                    text=f"R²={r_value**2:.3f}<br>m={slope:.3f}",
                    showarrow=False,
                    bgcolor='rgba(255,255,255,0.8)',
                    bordercolor=STORAGE_COLOR_MAP.get(condition, '#333'),
                    borderwidth=1,
                    font=dict(size=10)
                )

    # Update layout
    y_label = next((opt['label'] for opt in Y_AXIS_OPTIONS if opt['value'] == y_variable), y_variable)

    fig.update_layout(
        title=formulation_name,
        xaxis_title="Time (months)",
        yaxis_title=y_label,
        hovermode='closest',
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        margin=dict(l=60, r=120, t=40, b=60)
    )

    return fig

# App Layout
app.layout = dbc.Container([
    # Store components for data
    dcc.Store(id='filtered-data-store'),
    dcc.Store(id='graph-settings-store'),

    # Header
    dbc.Row([
        dbc.Col([
            html.H1([
                html.I(className="fas fa-chart-line text-primary me-3"),
                "Formulation Stability Visualization"
            ], className="mb-3"),
            html.P("Advanced analysis and visualization of formulation stability data",
                   className="lead text-muted")
        ])
    ], className="mb-4"),

    # Main Content Area
    dbc.Row([
        # Control Panel (Left Sidebar)
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5([
                        html.I(className="fas fa-sliders-h me-2"),
                        "Controls"
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    # Experiment Selection
                    html.Div([
                        dbc.Label("Select Experiment", className="fw-bold"),
                        dcc.Dropdown(
                            id="experiment-selector",
                            options=get_experiment_options(),
                            placeholder="Choose an experiment...",
                            className="mb-3"
                        )
                    ]),

                    # Formulation Filter
                    html.Div([
                        dbc.Label("Filter Formulations", className="fw-bold"),
                        dcc.Dropdown(
                            id="formulation-filter",
                            options=[],
                            multi=True,
                            placeholder="All formulations",
                            className="mb-3"
                        )
                    ]),

                    # Storage Condition Filter
                    html.Div([
                        dbc.Label("Storage Conditions", className="fw-bold"),
                        dcc.Checklist(
                            id="storage-filter",
                            options=[
                                {'label': ' 4°C', 'value': '4C'},
                                {'label': ' 25°C', 'value': '25C'},
                                {'label': ' 40°C', 'value': '40C'},
                                {'label': ' -80°C', 'value': '-80C'},
                                {'label': ' Freeze/Thaw', 'value': 'FT'}
                            ],
                            value=['25C', '40C'],
                            inline=False,
                            className="mb-3"
                        )
                    ]),

                    # Y-Axis Variable Selection
                    html.Div([
                        dbc.Label("Y-Axis Variable", className="fw-bold"),
                        dcc.Dropdown(
                            id="y-variable-selector",
                            options=Y_AXIS_OPTIONS,
                            value='hmw',
                            clearable=False,
                            className="mb-3"
                        )
                    ]),

                    html.Hr(),

                    # Graph Layout Settings
                    html.Div([
                        dbc.Label("Graph Layout", className="fw-bold"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Columns:", className="small"),
                                dcc.Dropdown(
                                    id="plot-columns",
                                    options=[
                                        {'label': '1', 'value': 1},
                                        {'label': '2', 'value': 2},
                                        {'label': '3', 'value': 3},
                                        {'label': '4', 'value': 4}
                                    ],
                                    value=2,
                                    clearable=False
                                )
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Height:", className="small"),
                                dcc.Input(
                                    id="plot-height",
                                    type="number",
                                    value=400,
                                    min=200,
                                    max=800,
                                    step=50,
                                    className="form-control form-control-sm"
                                )
                            ], width=6)
                        ], className="mb-3")
                    ]),

                    # Display Options
                    html.Div([
                        dbc.Label("Display Options", className="fw-bold"),
                        dcc.Checklist(
                            id="display-options",
                            options=[
                                {'label': ' Show Regression Lines', 'value': 'regression'},
                                {'label': ' Show Statistics', 'value': 'statistics'},
                                {'label': ' Show Grid', 'value': 'grid'}
                            ],
                            value=['regression', 'statistics', 'grid'],
                            className="mb-3"
                        )
                    ]),

                    html.Hr(),

                    # Action Buttons
                    html.Div([
                        dbc.Button([
                            html.I(className="fas fa-sync me-2"),
                            "Refresh Plots"
                        ], id="refresh-plots-btn", color="primary", className="w-100 mb-2"),

                        dbc.Button([
                            html.I(className="fas fa-download me-2"),
                            "Export Report"
                        ], id="export-report-btn", color="success", className="w-100 mb-2"),

                        dbc.Button([
                            html.I(className="fas fa-table me-2"),
                            "View Data Table"
                        ], id="view-table-btn", color="info", className="w-100")
                    ])
                ])
            ], className="sticky-top", style={'top': '20px'})
        ], width=3),

        # Main Visualization Area
        dbc.Col([
            dcc.Tabs(id="main-tabs", value="stability-tab", children=[
                # Stability Trends Tab
                dcc.Tab(label="Stability Trends", value="stability-tab", children=[
                    html.Div([
                        # Summary Stats Card
                        dbc.Card([
                            dbc.CardBody([
                                dbc.Row(id="summary-stats-row", children=[
                                    dbc.Col([
                                        html.H6("Total Samples", className="text-muted"),
                                        html.H3("0", id="total-samples-stat")
                                    ], width=3),
                                    dbc.Col([
                                        html.H6("Formulations", className="text-muted"),
                                        html.H3("0", id="total-formulations-stat")
                                    ], width=3),
                                    dbc.Col([
                                        html.H6("Time Points", className="text-muted"),
                                        html.H3("0", id="total-timepoints-stat")
                                    ], width=3),
                                    dbc.Col([
                                        html.H6("Data Completeness", className="text-muted"),
                                        html.H3("0%", id="completeness-stat")
                                    ], width=3)
                                ])
                            ])
                        ], className="mb-4"),

                        # Plots Container
                        dcc.Loading(
                            id="loading-stability",
                            type="default",
                            children=html.Div(id="stability-plots-container")
                        )
                    ], className="p-3")
                ]),

                # Comparative Analysis Tab
                dcc.Tab(label="Comparative Analysis", value="comparison-tab", children=[
                    html.Div([
                        # Comparison Controls
                        dbc.Card([
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Comparison Type"),
                                        dcc.Dropdown(
                                            id="comparison-type",
                                            options=[
                                                {'label': 'Overlay Plot', 'value': 'overlay'},
                                                {'label': 'Side-by-Side', 'value': 'sidebyside'},
                                                {'label': 'Difference Plot', 'value': 'difference'},
                                                {'label': 'Heatmap', 'value': 'heatmap'}
                                            ],
                                            value='overlay',
                                            clearable=False
                                        )
                                    ], width=4),
                                    dbc.Col([
                                        dbc.Label("Reference Formulation"),
                                        dcc.Dropdown(
                                            id="reference-formulation",
                                            options=[],
                                            placeholder="Select reference..."
                                        )
                                    ], width=4),
                                    dbc.Col([
                                        dbc.Label("Comparison Timepoint"),
                                        dcc.Dropdown(
                                            id="comparison-timepoint",
                                            options=[],
                                            placeholder="All timepoints"
                                        )
                                    ], width=4)
                                ])
                            ])
                        ], className="mb-4"),

                        # Comparison Plot
                        dcc.Loading(
                            id="loading-comparison",
                            type="default",
                            children=html.Div(id="comparison-plot-container")
                        )
                    ], className="p-3")
                ]),

                # Statistical Analysis Tab
                dcc.Tab(label="Statistical Analysis", value="stats-tab", children=[
                    html.Div([
                        # Statistical Summary
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5("Statistical Summary", className="mb-0")
                            ]),
                            dbc.CardBody([
                                html.Div(id="statistical-summary-container")
                            ])
                        ], className="mb-4"),

                        # Regression Analysis Table
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5("Regression Analysis", className="mb-0")
                            ]),
                            dbc.CardBody([
                                html.Div(id="regression-table-container")
                            ])
                        ])
                    ], className="p-3")
                ]),

                # Data Table Tab
                dcc.Tab(label="Data Table", value="data-tab", children=[
                    html.Div([
                        dbc.Card([
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Button([
                                            html.I(className="fas fa-download me-2"),
                                            "Export to Excel"
                                        ], id="export-excel-btn", color="success", className="mb-3")
                                    ])
                                ]),
                                html.Div(id="data-table-container")
                            ])
                        ])
                    ], className="p-3")
                ])
            ])
        ], width=9)
    ]),

    # Hidden download component
    dcc.Download(id="download-report"),

    # Alert container
    html.Div(id="alert-container")

], fluid=True, className="p-4")

# Callbacks

@app.callback(
    [Output('formulation-filter', 'options'),
     Output('filtered-data-store', 'data')],
    [Input('experiment-selector', 'value')],
    prevent_initial_call=True
)
def update_formulation_options(experiment_id):
    """Update formulation filter options when experiment is selected"""
    if not experiment_id:
        return [], None

    # Get all data for the experiment
    df = get_formulation_data(experiment_id)

    if df.empty:
        return [], None

    # Create formulation options
    formulations = df.groupby(['formulation_name', 'buffer_system', 'target_ph']).size().reset_index()
    options = []
    for _, row in formulations.iterrows():
        label = f"{row['formulation_name']}: {row['buffer_system']} pH {row['target_ph']}"
        options.append({'label': label, 'value': row['formulation_name']})

    # Store the full dataset
    return options, df.to_json(orient='split', date_format='iso')

@app.callback(
    [Output('stability-plots-container', 'children'),
     Output('total-samples-stat', 'children'),
     Output('total-formulations-stat', 'children'),
     Output('total-timepoints-stat', 'children'),
     Output('completeness-stat', 'children')],
    [Input('filtered-data-store', 'data'),
     Input('formulation-filter', 'value'),
     Input('storage-filter', 'value'),
     Input('y-variable-selector', 'value'),
     Input('plot-columns', 'value'),
     Input('plot-height', 'value'),
     Input('display-options', 'value'),
     Input('refresh-plots-btn', 'n_clicks')],
    prevent_initial_call=True
)
def update_stability_plots(json_data, selected_formulations, storage_conditions,
                          y_variable, num_columns, plot_height, display_options, n_clicks):
    """Update stability trend plots based on filters"""
    if not json_data:
        return html.Div("Please select an experiment"), "0", "0", "0", "0%"

    # Load data
    df = pd.read_json(json_data, orient='split')

    # Apply filters
    if storage_conditions:
        df = df[df['storage_condition'].isin(storage_conditions)]

    if selected_formulations:
        df = df[df['formulation_name'].isin(selected_formulations)]
    else:
        # If no specific formulations selected, show all
        selected_formulations = df['formulation_name'].unique()

    # Calculate statistics
    total_samples = len(df)
    total_formulations = df['formulation_name'].nunique()
    total_timepoints = df['time_point_months'].nunique()

    # Calculate completeness for the selected y variable
    completeness = (df[y_variable].notna().sum() / len(df) * 100) if len(df) > 0 else 0

    # Create plots
    plots = []
    show_regression = 'regression' in display_options if display_options else True
    show_stats = 'statistics' in display_options if display_options else True
    show_grid = 'grid' in display_options if display_options else True

    # Create subplots
    num_formulations = len(selected_formulations)
    if num_formulations == 0:
        return html.Div("No data to display"), "0", "0", "0", "0%"

    num_rows = (num_formulations + num_columns - 1) // num_columns

    fig = make_subplots(
        rows=num_rows,
        cols=num_columns,
        subplot_titles=[f for f in selected_formulations],
        vertical_spacing=0.12,
        horizontal_spacing=0.08
    )

    for idx, formulation in enumerate(selected_formulations):
        row = (idx // num_columns) + 1
        col = (idx % num_columns) + 1

        form_df = df[df['formulation_name'] == formulation]

        # Process each storage condition
        for condition in form_df['storage_condition'].unique():
            cond_df = form_df[form_df['storage_condition'] == condition].sort_values('time_point_months')
            cond_df = cond_df.dropna(subset=[y_variable])

            if len(cond_df) == 0:
                continue

            # Add data points
            fig.add_trace(
                go.Scatter(
                    x=cond_df['time_point_months'],
                    y=cond_df[y_variable],
                    mode='markers+lines',
                    name=condition,
                    marker=dict(
                        color=STORAGE_COLOR_MAP.get(condition, '#333'),
                        size=8
                    ),
                    line=dict(
                        color=STORAGE_COLOR_MAP.get(condition, '#333'),
                        width=1
                    ),
                    legendgroup=condition,
                    showlegend=(idx == 0)  # Only show legend for first subplot
                ),
                row=row, col=col
            )

            # Add regression if requested
            if show_regression and len(cond_df) >= 2:
                x = cond_df['time_point_months'].values
                y = cond_df[y_variable].values
                slope, intercept, r_value, _, _ = stats.linregress(x, y)

                x_line = np.linspace(x.min(), x.max() * 1.1, 50)
                y_line = slope * x_line + intercept

                fig.add_trace(
                    go.Scatter(
                        x=x_line,
                        y=y_line,
                        mode='lines',
                        line=dict(
                            color=STORAGE_COLOR_MAP.get(condition, '#333'),
                            dash='dash',
                            width=2
                        ),
                        showlegend=False,
                        hovertemplate=f'Trend: {condition}<br>Slope: {slope:.3f}<br>R²: {r_value**2:.3f}<extra></extra>'
                    ),
                    row=row, col=col
                )

                # Add statistics annotation
                if show_stats:
                    fig.add_annotation(
                        xref=f"x{col if row == 1 else (row-1)*num_columns + col}",
                        yref=f"y{col if row == 1 else (row-1)*num_columns + col}",
                        x=x.max() * 0.95,
                        y=y_line[-20],
                        text=f"R²={r_value**2:.2f}",
                        showarrow=False,
                        bgcolor='rgba(255,255,255,0.7)',
                        bordercolor=STORAGE_COLOR_MAP.get(condition, '#333'),
                        borderwidth=1,
                        font=dict(size=9)
                    )

    # Update layout
    y_label = next((opt['label'] for opt in Y_AXIS_OPTIONS if opt['value'] == y_variable), y_variable)

    fig.update_layout(
        height=plot_height * num_rows,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        title_text=f"Stability Trends - {y_label}",
        hovermode='closest'
    )

    # Update axes
    fig.update_xaxes(title_text="Time (months)", showgrid=show_grid)
    fig.update_yaxes(title_text=y_label, showgrid=show_grid)

    return (
        dcc.Graph(figure=fig, config={'toImageButtonOptions': {'filename': f'stability_{y_variable}'}}),
        str(total_samples),
        str(total_formulations),
        str(total_timepoints),
        f"{completeness:.1f}%"
    )

@app.callback(
    Output('data-table-container', 'children'),
    [Input('filtered-data-store', 'data'),
     Input('formulation-filter', 'value'),
     Input('storage-filter', 'value')],
    prevent_initial_call=True
)
def update_data_table(json_data, selected_formulations, storage_conditions):
    """Update the editable data table view with all fields"""
    if not json_data:
        return html.Div("Please select an experiment")

    # Load data
    df = pd.read_json(json_data, orient='split')

    # Apply filters
    if storage_conditions:
        df = df[df['storage_condition'].isin(storage_conditions)]

    if selected_formulations:
        df = df[df['formulation_name'].isin(selected_formulations)]

    # Define all columns matching the data entry app
    columns = [
        # Read-only identification columns
        {'name': 'Sample ID', 'id': 'sample_id', 'editable': False, 'type': 'text'},
        {'name': 'Form', 'id': 'formulation_name', 'editable': False, 'type': 'text'},
        {'name': 'Buffer System', 'id': 'buffer_system', 'editable': False, 'type': 'text'},
        {'name': 'Excipients', 'id': 'excipients', 'editable': False, 'type': 'text'},
        {'name': 'Target pH', 'id': 'target_ph', 'type': 'numeric', 'editable': False, 'format': {'specifier': '.1f'}},
        {'name': 'Storage', 'id': 'storage_condition', 'editable': False, 'type': 'text'},
        {'name': 'Timepoint\n(months)', 'id': 'time_point_months', 'type': 'numeric', 'editable': False, 'format': {'specifier': '.1f'}},
        {'name': 'Pull Date', 'id': 'pull_date', 'editable': True, 'type': 'datetime'},

        # Editable analytical data columns
        {'name': 'Appearance', 'id': 'appearance', 'editable': True, 'type': 'text'},
        {'name': 'Conc (mg/mL)', 'id': 'concentration_mg_ml', 'type': 'numeric', 'editable': True, 'format': {'specifier': '.2f'}},
        {'name': 'pH Measured', 'id': 'ph_measured', 'type': 'numeric', 'format': {'specifier': '.2f'}, 'editable': True},
        {'name': 'Osmolality\n(mOsm/kg)', 'id': 'osmolality_measured', 'type': 'numeric', 'editable': True},

        # SEC columns
        {'name': 'SEC Result ID', 'id': 'sec_result_id', 'editable': True, 'type': 'text'},
        {'name': 'HMW %', 'id': 'hmw', 'type': 'numeric', 'format': {'specifier': '.2f'}, 'editable': True},
        {'name': 'Main %', 'id': 'main', 'type': 'numeric', 'format': {'specifier': '.2f'}, 'editable': True},
        {'name': 'LMW %', 'id': 'lmw', 'type': 'numeric', 'format': {'specifier': '.2f'}, 'editable': True},
        {'name': 'Total Area', 'id': 'total_area', 'type': 'numeric', 'editable': True},

        # Thermal columns
        {'name': 'Tm (°C)', 'id': 'tm_celsius', 'type': 'numeric', 'format': {'specifier': '.1f'}, 'editable': True},
        {'name': 'Scattering\nOnset (°C)', 'id': 'scattering_onset', 'type': 'numeric', 'format': {'specifier': '.1f'}, 'editable': True},

        # Metadata
        {'name': 'Analysis Date', 'id': 'analysis_date', 'editable': True, 'type': 'datetime'},
        {'name': 'Notes', 'id': 'notes', 'editable': True, 'type': 'text'}
    ]

    # Prepare data - format dates properly
    df_display = df.copy()

    # Format dates
    if 'pull_date' in df_display.columns:
        df_display['pull_date'] = pd.to_datetime(df_display['pull_date']).dt.strftime('%Y-%m-%d')
    if 'analysis_date' in df_display.columns:
        df_display['analysis_date'] = pd.to_datetime(df_display['analysis_date']).dt.strftime('%Y-%m-%d')

    # Create editable data table
    return html.Div([
        # Save Controls
        dbc.Row([
            dbc.Col([
                dbc.Button([
                    html.I(className="fas fa-save me-2"),
                    "Save All Changes"
                ], id="save-table-data-btn", color="primary", className="me-2"),
                dbc.Button([
                    html.I(className="fas fa-undo me-2"),
                    "Discard Changes"
                ], id="discard-table-changes-btn", color="secondary", className="me-2"),
                dbc.Button([
                    html.I(className="fas fa-plus me-2"),
                    "Add New Sample"
                ], id="add-sample-btn", color="success")
            ], width=12)
        ], className="mb-3"),

        # Data Table
        dash_table.DataTable(
            id="editable-data-table",
            data=df_display.to_dict('records'),
            columns=columns,
            editable=True,
            row_deletable=True,
            style_cell={
                'textAlign': 'left',
                'padding': '8px',
                'fontSize': '12px',
                'minWidth': '80px',
                'width': 'auto',
                'whiteSpace': 'normal'
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold',
                'padding': '8px'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                },
                # Highlight editable columns
                {
                    'if': {'column_editable': True},
                    'backgroundColor': 'rgb(255, 255, 240)'
                },
                # Highlight missing critical data
                {
                    'if': {'filter_query': '{hmw} is blank', 'column_id': 'hmw'},
                    'backgroundColor': '#ffeaa7',
                    'color': 'black',
                },
                {
                    'if': {'filter_query': '{main} is blank', 'column_id': 'main'},
                    'backgroundColor': '#ffeaa7',
                    'color': 'black',
                },
                {
                    'if': {'filter_query': '{lmw} is blank', 'column_id': 'lmw'},
                    'backgroundColor': '#ffeaa7',
                    'color': 'black',
                }
            ],
            fixed_columns={'headers': True, 'data': 2},  # Fix first 2 columns
            style_table={
                'overflowX': 'auto',
                'width': '100%',
                'minWidth': '100%'
            },
            filter_action="native",
            sort_action="native",
            page_action="native",
            page_size=25,
            export_format="xlsx",
            export_headers="display",
            tooltip_data=[
                {
                    column: {'value': f'Edit {column}', 'type': 'markdown'}
                    for column in df_display.columns if column in [col['id'] for col in columns if col.get('editable')]
                } for _ in range(len(df_display))
            ],
            tooltip_duration=None
        ),

        # Status/Alert area
        html.Div(id="table-save-status", className="mt-3")
    ])

@app.callback(
    Output('download-report', 'data'),
    Input('export-report-btn', 'n_clicks'),
    [State('filtered-data-store', 'data'),
     State('formulation-filter', 'value'),
     State('storage-filter', 'value')],
    prevent_initial_call=True
)
def export_report(n_clicks, json_data, selected_formulations, storage_conditions):
    """Export filtered data to Excel"""
    if not n_clicks or not json_data:
        return no_update

    # Load and filter data
    df = pd.read_json(json_data, orient='split')

    if storage_conditions:
        df = df[df['storage_condition'].isin(storage_conditions)]

    if selected_formulations:
        df = df[df['formulation_name'].isin(selected_formulations)]

    # Create Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Write main data
        df.to_excel(writer, sheet_name='Stability Data', index=False)

        # Add summary statistics sheet
        summary_stats = df.groupby(['formulation_name', 'storage_condition'])[
            ['hmw', 'main', 'lmw', 'concentration_mg_ml', 'ph_measured']
        ].agg(['mean', 'std', 'min', 'max'])
        summary_stats.to_excel(writer, sheet_name='Summary Statistics')

    output.seek(0)

    return dcc.send_bytes(output.read(), f"stability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")

@app.callback(
    [Output('reference-formulation', 'options'),
     Output('comparison-timepoint', 'options')],
    [Input('filtered-data-store', 'data'),
     Input('formulation-filter', 'value')],
    prevent_initial_call=True
)
def update_comparison_options(json_data, selected_formulations):
    """Update comparison dropdown options"""
    if not json_data:
        return [], []

    df = pd.read_json(json_data, orient='split')

    # Get formulation options
    if selected_formulations:
        df_filtered = df[df['formulation_name'].isin(selected_formulations)]
    else:
        df_filtered = df

    formulation_options = [
        {'label': f, 'value': f}
        for f in sorted(df_filtered['formulation_name'].unique())
    ]

    # Get timepoint options
    timepoint_options = [
        {'label': f"{tp} months", 'value': tp}
        for tp in sorted(df_filtered['time_point_months'].unique())
    ]

    return formulation_options, timepoint_options

@app.callback(
    Output('comparison-plot-container', 'children'),
    [Input('comparison-type', 'value'),
     Input('reference-formulation', 'value'),
     Input('comparison-timepoint', 'value'),
     Input('filtered-data-store', 'data'),
     Input('formulation-filter', 'value'),
     Input('storage-filter', 'value'),
     Input('y-variable-selector', 'value')],
    prevent_initial_call=True
)
def update_comparison_plot(comparison_type, reference_form, timepoint, json_data,
                           selected_formulations, storage_conditions, y_variable):
    """Create comparative analysis plots"""
    if not json_data:
        return html.Div("Please select an experiment")

    df = pd.read_json(json_data, orient='split')

    # Apply filters
    if storage_conditions:
        df = df[df['storage_condition'].isin(storage_conditions)]

    if selected_formulations:
        df = df[df['formulation_name'].isin(selected_formulations)]

    if timepoint is not None:
        df = df[df['time_point_months'] == timepoint]

    y_label = next((opt['label'] for opt in Y_AXIS_OPTIONS if opt['value'] == y_variable), y_variable)

    if comparison_type == 'overlay':
        # Overlay all formulations on one plot
        fig = go.Figure()

        for formulation in df['formulation_name'].unique():
            form_df = df[df['formulation_name'] == formulation]

            for condition in form_df['storage_condition'].unique():
                cond_df = form_df[form_df['storage_condition'] == condition].sort_values('time_point_months')
                cond_df = cond_df.dropna(subset=[y_variable])

                if len(cond_df) == 0:
                    continue

                fig.add_trace(go.Scatter(
                    x=cond_df['time_point_months'],
                    y=cond_df[y_variable],
                    mode='markers+lines',
                    name=f"{formulation} - {condition}",
                    marker=dict(size=8),
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                 f'{y_label}: %{{y:.2f}}<br>' +
                                 'Time: %{x} months<extra></extra>'
                ))

        fig.update_layout(
            title=f"Formulation Comparison - {y_label}",
            xaxis_title="Time (months)",
            yaxis_title=y_label,
            hovermode='closest',
            height=600
        )

        return dcc.Graph(figure=fig)

    elif comparison_type == 'heatmap':
        # Create heatmap of values
        pivot_df = df.pivot_table(
            values=y_variable,
            index='formulation_name',
            columns='time_point_months',
            aggfunc='mean'
        )

        fig = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=[f"{x} months" for x in pivot_df.columns],
            y=pivot_df.index,
            colorscale='RdYlBu_r',
            reversescale=False,
            text=np.round(pivot_df.values, 2),
            texttemplate='%{text}',
            textfont={"size": 10},
            colorbar=dict(title=y_label)
        ))

        fig.update_layout(
            title=f"Stability Heatmap - {y_label}",
            xaxis_title="Time Point",
            yaxis_title="Formulation",
            height=400 + len(pivot_df.index) * 30
        )

        return dcc.Graph(figure=fig)

    elif comparison_type == 'difference' and reference_form:
        # Show difference from reference formulation
        ref_df = df[df['formulation_name'] == reference_form]
        fig = go.Figure()

        for formulation in df['formulation_name'].unique():
            if formulation == reference_form:
                continue

            form_df = df[df['formulation_name'] == formulation]

            for tp in form_df['time_point_months'].unique():
                ref_value = ref_df[ref_df['time_point_months'] == tp][y_variable].mean()
                form_value = form_df[form_df['time_point_months'] == tp][y_variable].mean()

                if pd.notna(ref_value) and pd.notna(form_value):
                    diff = form_value - ref_value

                    fig.add_trace(go.Bar(
                        x=[f"{tp} months"],
                        y=[diff],
                        name=formulation,
                        hovertemplate=f'<b>{formulation}</b><br>' +
                                    f'Difference: %{{y:.2f}}<br>' +
                                    f'Reference: {ref_value:.2f}<br>' +
                                    f'Value: {form_value:.2f}<extra></extra>'
                    ))

        fig.update_layout(
            title=f"Difference from {reference_form} - {y_label}",
            xaxis_title="Time Point",
            yaxis_title=f"Difference in {y_label}",
            barmode='group',
            height=500
        )

        return dcc.Graph(figure=fig)

    else:
        # Side-by-side comparison
        formulations = df['formulation_name'].unique()
        num_forms = len(formulations)

        fig = make_subplots(
            rows=1,
            cols=num_forms,
            subplot_titles=list(formulations),
            shared_yaxes=True
        )

        for idx, formulation in enumerate(formulations):
            form_df = df[df['formulation_name'] == formulation]

            for condition in form_df['storage_condition'].unique():
                cond_df = form_df[form_df['storage_condition'] == condition].sort_values('time_point_months')
                cond_df = cond_df.dropna(subset=[y_variable])

                if len(cond_df) == 0:
                    continue

                fig.add_trace(
                    go.Scatter(
                        x=cond_df['time_point_months'],
                        y=cond_df[y_variable],
                        mode='markers+lines',
                        name=condition,
                        marker=dict(
                            color=STORAGE_COLOR_MAP.get(condition, '#333'),
                            size=8
                        ),
                        legendgroup=condition,
                        showlegend=(idx == 0)
                    ),
                    row=1, col=idx+1
                )

        fig.update_layout(
            title=f"Side-by-Side Comparison - {y_label}",
            height=500,
            showlegend=True
        )

        fig.update_xaxes(title_text="Time (months)")
        fig.update_yaxes(title_text=y_label, col=1)

        return dcc.Graph(figure=fig)

@app.callback(
    Output('statistical-summary-container', 'children'),
    [Input('filtered-data-store', 'data'),
     Input('formulation-filter', 'value'),
     Input('storage-filter', 'value'),
     Input('y-variable-selector', 'value')],
    prevent_initial_call=True
)
def update_statistical_summary(json_data, selected_formulations, storage_conditions, y_variable):
    """Generate statistical summary"""
    if not json_data:
        return html.Div("Please select an experiment")

    df = pd.read_json(json_data, orient='split')

    # Apply filters
    if storage_conditions:
        df = df[df['storage_condition'].isin(storage_conditions)]

    if selected_formulations:
        df = df[df['formulation_name'].isin(selected_formulations)]

    # Calculate statistics
    summary_stats = df.groupby(['formulation_name', 'storage_condition'])[y_variable].agg([
        'count', 'mean', 'std', 'min', 'max'
    ]).round(2)

    # Create summary cards
    cards = []
    for (formulation, condition), stats in summary_stats.iterrows():
        card = dbc.Card([
            dbc.CardHeader([
                html.H6(f"{formulation} - {condition}", className="mb-0")
            ]),
            dbc.CardBody([
                html.P([
                    html.Strong("n: "), f"{int(stats['count'])}", html.Br(),
                    html.Strong("Mean: "), f"{stats['mean']:.2f}", html.Br(),
                    html.Strong("Std: "), f"{stats['std']:.2f}", html.Br(),
                    html.Strong("Range: "), f"{stats['min']:.2f} - {stats['max']:.2f}"
                ], className="small mb-0")
            ])
        ], className="mb-2")
        cards.append(dbc.Col(card, width=3))

    return dbc.Row(cards)

@app.callback(
    Output('regression-table-container', 'children'),
    [Input('filtered-data-store', 'data'),
     Input('formulation-filter', 'value'),
     Input('storage-filter', 'value'),
     Input('y-variable-selector', 'value')],
    prevent_initial_call=True
)
def update_regression_table(json_data, selected_formulations, storage_conditions, y_variable):
    """Generate regression analysis table"""
    if not json_data:
        return html.Div("Please select an experiment")

    df = pd.read_json(json_data, orient='split')

    # Apply filters
    if storage_conditions:
        df = df[df['storage_condition'].isin(storage_conditions)]

    if selected_formulations:
        df = df[df['formulation_name'].isin(selected_formulations)]

    # Calculate regression for each formulation/condition combination
    regression_data = []

    for formulation in df['formulation_name'].unique():
        form_df = df[df['formulation_name'] == formulation]

        for condition in form_df['storage_condition'].unique():
            cond_df = form_df[form_df['storage_condition'] == condition].dropna(subset=[y_variable])

            if len(cond_df) >= 2:
                x = cond_df['time_point_months'].values
                y = cond_df[y_variable].values

                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

                regression_data.append({
                    'Formulation': formulation,
                    'Condition': condition,
                    'Slope': f"{slope:.4f}",
                    'Intercept': f"{intercept:.2f}",
                    'R²': f"{r_value**2:.3f}",
                    'P-value': f"{p_value:.4f}",
                    'Std Error': f"{std_err:.4f}",
                    'n': len(cond_df)
                })

    if not regression_data:
        return html.Div("Insufficient data for regression analysis")

    regression_df = pd.DataFrame(regression_data)

    return dash_table.DataTable(
        data=regression_df.to_dict('records'),
        columns=[{"name": col, "id": col} for col in regression_df.columns],
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            },
            {
                'if': {'filter_query': '{R²} > 0.9'},
                'backgroundColor': '#d4edda',
                'color': 'black',
            }
        ],
        sort_action="native"
    )

@app.callback(
    Output('table-save-status', 'children'),
    Input('save-table-data-btn', 'n_clicks'),
    State('editable-data-table', 'data'),
    prevent_initial_call=True
)
def save_table_data(n_clicks, table_data):
    """Save changes from the editable data table"""
    if not n_clicks or not table_data:
        return no_update

    try:
        from django.db import transaction
        from datetime import datetime

        with transaction.atomic():
            updated_count = 0

            for row in table_data:
                sample_id = row.get('sample_id')
                if not sample_id:
                    continue

                try:
                    sample = FormulationSample.objects.get(sample_id=sample_id)

                    # Update editable fields
                    fields_to_update = [
                        'appearance', 'concentration_mg_ml', 'ph_measured', 'osmolality_measured',
                        'sec_result_id', 'hmw', 'main', 'lmw', 'total_area',
                        'tm_celsius', 'scattering_onset', 'notes'
                    ]

                    updated = False
                    for field in fields_to_update:
                        new_value = row.get(field)
                        # Allow empty strings to be saved as None for text fields and numeric fields
                        if new_value == '' or new_value is None:
                            new_value = None

                        if getattr(sample, field) != new_value:
                            setattr(sample, field, new_value)
                            updated = True

                    # Handle analysis date
                    analysis_date = row.get('analysis_date')
                    if analysis_date:
                        try:
                            analysis_date_obj = datetime.strptime(analysis_date, '%Y-%m-%d').date()
                            if sample.analysis_date != analysis_date_obj:
                                sample.analysis_date = analysis_date_obj
                                updated = True
                        except ValueError:
                            pass  # Skip invalid dates

                    # Handle pull date
                    pull_date_str = row.get('pull_date')
                    if pull_date_str:
                        try:
                            pull_date_obj = datetime.strptime(pull_date_str, '%Y-%m-%d').date()
                            if sample.pull_date != pull_date_obj:
                                sample.pull_date = pull_date_obj
                                updated = True
                        except ValueError:
                            pass  # Skip invalid dates

                    if updated:
                        sample.save()
                        updated_count += 1

                except FormulationSample.DoesNotExist:
                    continue

            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Successfully updated {updated_count} samples!"
            ], color="success", dismissable=True)

    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error saving data: {str(e)}"
        ], color="danger", dismissable=True)

@app.callback(
    Output('alert-container', 'children'),
    [Input('export-report-btn', 'n_clicks'),
     Input('export-excel-btn', 'n_clicks')],
    prevent_initial_call=True
)
def show_export_alert(export_clicks, excel_clicks):
    """Show success alert after export"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update

    return dbc.Alert(
        "Report exported successfully!",
        color="success",
        dismissable=True,
        duration=3000
    )

# Auto-select most recent experiment on load
@app.callback(
    Output('experiment-selector', 'value'),
    Input('experiment-selector', 'options'),
    prevent_initial_call=False
)
def auto_select_experiment(options):
    """Auto-select the most recent experiment"""
    if options and len(options) > 0:
        return options[0]['value']
    return None