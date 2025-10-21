"""
Octet Biolayer Interferometry Analysis App

Interactive dashboard for visualizing and analyzing Octet binding kinetics data.
Features:
- Experiment selection
- Multi-sensor binding curve visualization
- Step-by-step data exploration
- Interactive trace selection
- Export capabilities
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context, ALL
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from django_plotly_dash import DjangoDash
from plotly_integration.models import (
    OctetExperiment, OctetSensorData, OctetStepData,
    OctetTimeSeriesData, OctetSensorLayout, OctetSampleLayout
)

# Initialize the Dash app
app = DjangoDash('OctetAnalysisAppV3', suppress_callback_exceptions=True)

# Color palette for traces
COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
    '#c49c94'
]

# App layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("Octet Biolayer Interferometry Analysis",
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '10px'}),
        html.P("Interactive analysis of binding kinetics data",
               style={'textAlign': 'center', 'color': '#7f8c8d', 'marginBottom': '30px'})
    ], style={'backgroundColor': '#ecf0f1', 'padding': '20px', 'borderRadius': '5px', 'marginBottom': '20px'}),

    # Control Panel
    html.Div([
        html.Div([
            # Experiment Selection
            html.Div([
                html.Label("Select Experiment:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='experiment-dropdown',
                    placeholder="Select an experiment...",
                    style={'width': '100%'}
                )
            ], style={'marginBottom': '15px'}),

            # Experiment Info Display
            html.Div(id='experiment-info', style={'marginBottom': '15px'}),

            # Step Selection
            html.Div([
                html.Label("Select Step:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='step-dropdown',
                    placeholder="Select a step to visualize...",
                    value='Association',
                    style={'width': '100%'}
                )
            ], style={'marginBottom': '15px'}),

            # Sensor Selection Mode
            html.Div([
                html.Label("Sensor Selection:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.RadioItems(
                    id='sensor-selection-mode',
                    options=[
                        {'label': ' Show All Sensors', 'value': 'all'},
                        {'label': ' Select Specific Sensors', 'value': 'specific'}
                    ],
                    value='all',
                    style={'marginBottom': '10px'}
                )
            ], style={'marginBottom': '15px'}),

            # Multi-select for specific sensors
            html.Div([
                dcc.Dropdown(
                    id='sensor-multiselect',
                    multi=True,
                    placeholder="Select sensors to display...",
                    style={'width': '100%'}
                )
            ], id='sensor-select-container', style={'marginBottom': '15px', 'display': 'none'}),

            # Plot Options
            html.Div([
                html.Label("Plot Options:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Checklist(
                    id='plot-options',
                    options=[
                        {'label': ' Show Grid', 'value': 'grid'},
                        {'label': ' Show Legend', 'value': 'legend'},
                        {'label': ' Normalize Baseline', 'value': 'normalize'}
                    ],
                    value=['grid', 'legend'],
                    style={'marginBottom': '10px'}
                )
            ], style={'marginBottom': '15px'}),

            # Refresh Button
            html.Button('Refresh Plot', id='refresh-button', n_clicks=0,
                       style={
                           'width': '100%',
                           'padding': '10px',
                           'backgroundColor': '#3498db',
                           'color': 'white',
                           'border': 'none',
                           'borderRadius': '5px',
                           'cursor': 'pointer',
                           'fontWeight': 'bold'
                       })

        ], style={
            'backgroundColor': '#f8f9fa',
            'padding': '20px',
            'borderRadius': '5px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
        })
    ], style={'width': '300px', 'display': 'inline-block', 'verticalAlign': 'top', 'marginRight': '20px'}),

    # Main Plot Area
    html.Div([
        # Binding Curves Plot
        dcc.Graph(
            id='binding-curves-plot',
            style={'height': '600px', 'marginBottom': '20px'}
        ),

        # Sensor Results Table
        html.Div([
            html.H3("Sensor Results", style={'color': '#2c3e50', 'marginBottom': '15px'}),
            html.Div(id='results-table')
        ], style={
            'backgroundColor': '#f8f9fa',
            'padding': '20px',
            'borderRadius': '5px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
        })

    ], style={'width': 'calc(100% - 340px)', 'display': 'inline-block', 'verticalAlign': 'top'}),

    # Hidden div to store data
    dcc.Store(id='experiment-data-store'),
    dcc.Store(id='sensor-data-store')

], style={'padding': '20px', 'fontFamily': 'Arial, sans-serif', 'maxWidth': '1800px', 'margin': '0 auto'})


# Callback to populate experiment dropdown
@app.callback(
    Output('experiment-dropdown', 'options'),
    Input('experiment-dropdown', 'id')
)
def populate_experiments(_):
    """Load all available experiments from database"""
    experiments = OctetExperiment.objects.all().order_by('-start_datetime')

    options = []
    for exp in experiments:
        label = f"{exp.experiment_name} ({exp.experiment_type})"
        if exp.start_datetime:
            label += f" - {exp.start_datetime.strftime('%Y-%m-%d')}"

        options.append({
            'label': label,
            'value': exp.id
        })

    return options


# Callback to show/hide sensor multi-select
@app.callback(
    Output('sensor-select-container', 'style'),
    Input('sensor-selection-mode', 'value')
)
def toggle_sensor_select(mode):
    """Show/hide sensor selection dropdown based on mode"""
    if mode == 'specific':
        return {'marginBottom': '15px', 'display': 'block'}
    return {'marginBottom': '15px', 'display': 'none'}


# Callback to load experiment info and populate dropdowns
@app.callback(
    [Output('experiment-info', 'children'),
     Output('step-dropdown', 'options'),
     Output('step-dropdown', 'value'),
     Output('sensor-multiselect', 'options'),
     Output('experiment-data-store', 'data')],
    Input('experiment-dropdown', 'value')
)
def load_experiment(exp_id):
    """Load experiment details when selected"""
    if not exp_id:
        return html.Div("Select an experiment to begin", style={'color': '#95a5a6'}), [], None, [], None

    try:
        exp = OctetExperiment.objects.get(id=exp_id)

        # Experiment info card
        info_card = html.Div([
            html.P([html.Strong("Type: "), f"{exp.experiment_type} - {exp.experiment_subtype}"],
                   style={'marginBottom': '5px', 'fontSize': '14px'}),
            html.P([html.Strong("Date: "), exp.start_datetime.strftime('%Y-%m-%d %H:%M') if exp.start_datetime else 'N/A'],
                   style={'marginBottom': '5px', 'fontSize': '14px'}),
            html.P([html.Strong("Temperature: "), f"{exp.temperature}°C" if exp.temperature else 'N/A'],
                   style={'marginBottom': '5px', 'fontSize': '14px'}),
            html.P([html.Strong("Sensors: "), str(exp.sensors.count())],
                   style={'marginBottom': '0px', 'fontSize': '14px'})
        ], style={
            'backgroundColor': '#e8f4f8',
            'padding': '10px',
            'borderRadius': '5px',
            'border': '1px solid #b8dae8'
        })

        # Get unique step names from step sequence
        step_sequence = exp.step_sequence.all().order_by('step_order')
        step_options = [{'label': step.step_name, 'value': step.step_name} for step in step_sequence]

        # Default to Association if available, otherwise first step
        default_step = 'Association' if any(s.step_name == 'Association' for s in step_sequence) else (step_sequence[0].step_name if step_sequence else None)

        # Get sensor options
        sensors = exp.sensors.all().order_by('sensor_location')
        sensor_options = [{'label': f"{s.sensor_location} - {s.sample_id}", 'value': s.sensor_location} for s in sensors]

        # Store experiment data
        exp_data = {
            'id': exp.id,
            'name': exp.experiment_name,
            'type': exp.experiment_type
        }

        return info_card, step_options, default_step, sensor_options, exp_data

    except OctetExperiment.DoesNotExist:
        return html.Div("Experiment not found", style={'color': '#e74c3c'}), [], None, [], None


# Main callback to update plot
@app.callback(
    [Output('binding-curves-plot', 'figure'),
     Output('results-table', 'children')],
    [Input('refresh-button', 'n_clicks'),
     Input('step-dropdown', 'value')],
    [State('experiment-dropdown', 'value'),
     State('sensor-selection-mode', 'value'),
     State('sensor-multiselect', 'value'),
     State('plot-options', 'value')]
)
def update_plot(n_clicks, step_name, exp_id, sensor_mode, selected_sensors, plot_options):
    """Update binding curves plot and results table"""
    if not exp_id or not step_name:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            title="Select an experiment and step to visualize data",
            xaxis_title="Time (s)",
            yaxis_title="Response (nm)",
            template="plotly_white"
        )
        return empty_fig, html.Div("No data to display", style={'color': '#95a5a6'})

    try:
        exp = OctetExperiment.objects.get(id=exp_id)

        # Get sensors to plot
        if sensor_mode == 'specific' and selected_sensors:
            sensors = exp.sensors.filter(sensor_location__in=selected_sensors).order_by('sensor_location')
        else:
            sensors = exp.sensors.all().order_by('sensor_location')

        if not sensors:
            empty_fig = go.Figure()
            empty_fig.update_layout(title="No sensors selected")
            return empty_fig, html.Div("No sensors to display", style={'color': '#95a5a6'})

        # Create figure
        fig = go.Figure()

        # Results data for table
        results_data = []

        # Plot each sensor
        for idx, sensor in enumerate(sensors):
            # Get the step
            step = sensor.steps.filter(step_name=step_name).first()

            if not step:
                continue

            # Get time series data
            time_series = step.time_series.all().order_by('time')

            if not time_series:
                continue

            # Extract times and responses
            times = [ts.time for ts in time_series]
            responses = [ts.response for ts in time_series]

            # Normalize baseline if option selected
            if 'normalize' in (plot_options or []):
                baseline = responses[0] if responses else 0
                responses = [r - baseline for r in responses]

            # Add trace
            color = COLORS[idx % len(COLORS)]
            trace_name = f"{sensor.sensor_location}: {sensor.sample_id}" if sensor.sample_id else sensor.sensor_location

            fig.add_trace(go.Scatter(
                x=times,
                y=responses,
                mode='lines',
                name=trace_name,
                line=dict(color=color, width=2),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             'Time: %{x:.2f}s<br>' +
                             'Response: %{y:.4f}nm<br>' +
                             '<extra></extra>'
            ))

            # Add to results table
            results_data.append({
                'Location': sensor.sensor_location,
                'Sample ID': sensor.sample_id or 'N/A',
                'Response (nm)': f"{sensor.response:.4f}" if sensor.response else 'N/A',
                'Concentration': f"{sensor.concentration}" if sensor.concentration else 'N/A',
                'Points': len(times)
            })

        # Update layout
        show_legend = 'legend' in (plot_options or [])
        show_grid = 'grid' in (plot_options or [])

        fig.update_layout(
            title=f"{exp.experiment_name} - {step_name}",
            xaxis_title="Time (s)",
            yaxis_title="Response (nm)" + (" (Baseline Normalized)" if 'normalize' in (plot_options or []) else ""),
            hovermode='closest',
            showlegend=show_legend,
            template="plotly_white",
            height=600,
            xaxis=dict(showgrid=show_grid),
            yaxis=dict(showgrid=show_grid),
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99,
                bgcolor="rgba(255, 255, 255, 0.8)"
            )
        )

        # Create results table
        if results_data:
            table = html.Table([
                # Header
                html.Thead(html.Tr([
                    html.Th(col, style={'padding': '10px', 'textAlign': 'left', 'backgroundColor': '#3498db', 'color': 'white'})
                    for col in results_data[0].keys()
                ])),
                # Body
                html.Tbody([
                    html.Tr([
                        html.Td(row[col], style={'padding': '8px', 'borderBottom': '1px solid #ddd'})
                        for col in row.keys()
                    ], style={'backgroundColor': '#f8f9fa' if i % 2 == 0 else 'white'})
                    for i, row in enumerate(results_data)
                ])
            ], style={'width': '100%', 'borderCollapse': 'collapse'})
        else:
            table = html.Div("No results to display", style={'color': '#95a5a6'})

        return fig, table

    except Exception as e:
        empty_fig = go.Figure()
        empty_fig.update_layout(title=f"Error loading data: {str(e)}")
        return empty_fig, html.Div(f"Error: {str(e)}", style={'color': '#e74c3c'})


# Export the app
def get_app():
    """Return the configured Dash app"""
    return app
