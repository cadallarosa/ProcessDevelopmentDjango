"""
Formulation Stability Plotting App
Modern interface for plotting formulation stability data with trends and analysis
"""

import dash
from dash import dcc, html, Input, Output, State, no_update
import dash
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from scipy import stats
from plotly_integration.models import (
    FormulationExperiment, 
    FormulationMatrix, 
    FormulationComponent, 
    FormulationSample
)

app = DjangoDash("FormulationStabilityApp", external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
], suppress_callback_exceptions=True)

COLOR_PALETTE = {
    "primary": "#2E86C1",
    "secondary": "#E74C3C",
    "success": "#27AE60",
    "warning": "#F39C12",
    "info": "#8E44AD",
    "light": "#F8F9FA",
    "dark": "#2C3E50",
    "background": "#FFFFFF",
}

def get_experiments():
    """Get all available experiments"""
    experiments = FormulationExperiment.objects.all().order_by('-created_date')
    return [{'label': f"{exp.experiment_id} - {exp.name}", 'value': exp.experiment_id} 
            for exp in experiments]

def get_formulation_data(experiment_id=None):
    """Get formulation data for stability analysis"""
    query = FormulationSample.objects.select_related(
        'formulation__experiment', 'formulation'
    ).prefetch_related('formulation__components')
    
    if experiment_id:
        query = query.filter(formulation__experiment_id=experiment_id)
    
    samples = query.order_by('formulation__formulation_number', 'storage_condition', 'time_point_months')
    
    data = []
    for sample in samples:
        # Get buffer components for formulation description
        buffers = sample.formulation.components.filter(component_type='buffer')
        buffer_desc = ', '.join([f"{b.name} {b.concentration}{b.unit}" for b in buffers])
        
        excipients = sample.formulation.components.exclude(component_type='buffer')
        excipient_desc = ', '.join([f"{e.name} {e.concentration}{e.unit}" for e in excipients])
        
        data.append({
            'sample_id': sample.sample_id,
            'experiment_id': sample.formulation.experiment_id,
            'formulation_number': sample.formulation.formulation_number,
            'formulation_key': f"F{sample.formulation.formulation_number:02d} | {buffer_desc} | pH{sample.formulation.target_ph}",
            'buffer': buffer_desc,
            'excipients': excipient_desc,
            'target_ph': sample.formulation.target_ph,
            'storage_condition': sample.storage_condition,
            'time_point_months': sample.time_point_months,
            'hmw': sample.hmw,
            'main': sample.main,
            'lmw': sample.lmw,
            'concentration_mg_ml': sample.concentration_mg_ml,
            'ph_measured': sample.ph_measured,
            'tm_celsius': sample.tm_celsius,
            'total_area': sample.total_area,
            'osmolality_measured': sample.osmolality_measured,
            'scattering_onset': sample.scattering_onset
        })
    
    return data

# Main Layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1([
                html.I(className="fas fa-chart-line text-primary me-3"),
                "Formulation Stability Analysis"
            ], className="mb-3"),
            html.P("Analyze stability trends across formulations and storage conditions", 
                   className="lead text-muted")
        ])
    ]),
    
    # Controls section
    dbc.Card([
        dbc.CardHeader([
            html.H5([html.I(className="fas fa-sliders-h me-2"), "Analysis Controls"], className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Select Experiment:", className="fw-bold"),
                    dcc.Dropdown(
                        id="experiment-dropdown",
                        options=get_experiments(),
                        value=None,
                        placeholder="Choose experiment..."
                    )
                ], width=4),
                dbc.Col([
                    dbc.Label("Y-Axis Variable:", className="fw-bold"),
                    dcc.Dropdown(
                        id="y-axis-selector",
                        options=[
                            {"label": "HMW %", "value": "hmw"},
                            {"label": "Main %", "value": "main"},
                            {"label": "LMW %", "value": "lmw"},
                            {"label": "Concentration (mg/mL)", "value": "concentration_mg_ml"},
                            {"label": "pH (measured)", "value": "ph_measured"},
                            {"label": "Total Area", "value": "total_area"},
                            {"label": "Tm (°C)", "value": "tm_celsius"},
                            {"label": "Osmolality", "value": "osmolality_measured"},
                            {"label": "Scattering Onset", "value": "scattering_onset"}
                        ],
                        value="hmw"
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("Storage Condition:", className="fw-bold"),
                    dcc.Dropdown(
                        id="storage-condition-filter",
                        options=[
                            {"label": "All Conditions", "value": "all"},
                            {"label": "25°C Only", "value": "25C"},
                            {"label": "40°C Only", "value": "40C"},
                            {"label": "4°C Only", "value": "4C"},
                            {"label": "-80°C Only", "value": "-80C"},
                            {"label": "Freeze/Thaw Only", "value": "FT"}
                        ],
                        value="all"
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("Select Formulations:", className="fw-bold"),
                    dcc.Dropdown(
                        id="formulation-selector",
                        options=[],
                        value=[],
                        multi=True,
                        placeholder="All formulations"
                    )
                ], width=2)
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Plots per Row:", className="fw-bold"),
                    dcc.Dropdown(
                        id="plots-per-row",
                        options=[
                            {"label": "1", "value": 1},
                            {"label": "2", "value": 2},
                            {"label": "3", "value": 3},
                            {"label": "4", "value": 4}
                        ],
                        value=2
                    )
                ], width=2),
                dbc.Col([
                    dbc.Label("Plot Height (px):", className="fw-bold"),
                    dcc.Input(
                        id="plot-height-input",
                        type="number",
                        value=600,
                        min=300,
                        max=1000,
                        step=50,
                        className="form-control"
                    )
                ], width=2),
                dbc.Col([
                    dbc.Label("Statistics:", className="fw-bold"),
                    dbc.Checklist(
                        id='statistics-checklist',
                        options=[
                            {'label': ' R² Values', 'value': 'show_r2'},
                            {'label': ' Slope Values', 'value': 'show_slope'}
                        ],
                        value=['show_r2'],
                        inline=True
                    )
                ], width=4),
                dbc.Col([
                    html.Div(id="data-summary", className="mt-2")
                ], width=4)
            ])
        ])
    ], className="mb-4"),
    
    # Main plotting area
    dbc.Card([
        dbc.CardHeader([
            html.H5([html.I(className="fas fa-chart-area me-2"), "Stability Trends"], className="mb-0")
        ]),
        dbc.CardBody([
            dcc.Loading(
                dcc.Graph(
                    id='stability-plots',
                    config={
                        'toImageButtonOptions': {'filename': 'stability_analysis'},
                        'edits': {"annotationPosition": True}
                    }
                ),
                type="default"
            )
        ])
    ])
    
], fluid=True, className="p-4")

@app.callback(
    [Output('formulation-selector', 'options'),
     Output('data-summary', 'children')],
    Input('experiment-dropdown', 'value')
)
def update_formulation_options(experiment_id):
    if not experiment_id:
        return [], ""
    
    try:
        data = get_formulation_data(experiment_id)
        
        if not data:
            return [], dbc.Badge("No data available", color="warning")
        
        # Get unique formulations
        formulations = {}
        for item in data:
            key = item['formulation_key']
            if key not in formulations:
                formulations[key] = 0
            formulations[key] += 1
        
        formulation_options = [
            {'label': f"{key} ({count} samples)", 'value': key}
            for key, count in sorted(formulations.items())
        ]
        
        # Data summary
        total_samples = len(data)
        analyzed_samples = len([d for d in data if d['hmw'] is not None])
        unique_formulations = len(formulations)
        
        summary = dbc.Badge(
            f"{unique_formulations} formulations, {analyzed_samples}/{total_samples} analyzed",
            color="info"
        )
        
        return formulation_options, summary
        
    except Exception as e:
        return [], dbc.Badge(f"Error: {str(e)}", color="danger")

@app.callback(
    Output('stability-plots', 'figure'),
    [Input('y-axis-selector', 'value'),
     Input('formulation-selector', 'value'),
     Input('storage-condition-filter', 'value'),
     Input('plots-per-row', 'value'),
     Input('plot-height-input', 'value'),
     Input('statistics-checklist', 'value'),
     Input('experiment-dropdown', 'value')]
)
def update_stability_plots(y_axis_variable, selected_formulations, storage_condition_filter, 
                          plots_per_row, plot_height, statistics_options, experiment_id):
    
    if not experiment_id or not y_axis_variable:
        fig = go.Figure()
        fig.add_annotation(
            text="Select experiment and Y-axis variable to view stability plots",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig
    
    try:
        # Get data
        data = get_formulation_data(experiment_id)
        
        if not data:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for selected experiment",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        # Filter data
        df = pd.DataFrame(data)
        
        # Filter by storage condition
        if storage_condition_filter != "all":
            df = df[df['storage_condition'] == storage_condition_filter]
        
        # Filter by formulations
        if selected_formulations:
            df = df[df['formulation_key'].isin(selected_formulations)]
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No data matches the selected filters",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        # Group by formulation
        formulation_groups = df.groupby('formulation_key')
        
        # Create subplots
        num_formulations = len(formulation_groups)
        cols = min(plots_per_row or 2, num_formulations)
        rows = (num_formulations + cols - 1) // cols
        
        # Calculate spacing
        vertical_spacing = max(0.02, min(0.1, 1.0 / max(rows, 1) * 0.3))
        horizontal_spacing = max(0.02, min(0.1, 1.0 / max(cols, 1) * 0.2))
        
        fig = make_subplots(
            rows=rows, cols=cols,
            subplot_titles=[name for name, _ in formulation_groups],
            vertical_spacing=vertical_spacing,
            horizontal_spacing=horizontal_spacing
        )
        
        # Color palette for conditions
        condition_colors = {
            '25C': '#1f77b4',
            '40C': '#ff7f0e', 
            '4C': '#2ca02c',
            '-80C': '#d62728',
            'FT': '#9467bd'
        }
        
        y_axis_labels = {
            'hmw': 'HMW %',
            'main': 'Main %',
            'lmw': 'LMW %',
            'concentration_mg_ml': 'Concentration (mg/mL)',
            'ph_measured': 'pH (measured)',
            'total_area': 'Total Area',
            'tm_celsius': 'Tm (°C)',
            'osmolality_measured': 'Osmolality (mOsm/kg)',
            'scattering_onset': 'Scattering Onset (°C)'
        }
        
        for i, (formulation_name, form_data) in enumerate(formulation_groups):
            row = (i // cols) + 1
            col = (i % cols) + 1
            
            # Group by storage condition
            for condition, cond_data in form_data.groupby('storage_condition'):
                # Filter out None values
                plot_data = cond_data.dropna(subset=['time_point_months', y_axis_variable])
                
                if plot_data.empty or len(plot_data) < 2:
                    continue
                
                # Sort by time
                plot_data = plot_data.sort_values('time_point_months')
                
                x_vals = plot_data['time_point_months'].values
                y_vals = plot_data[y_axis_variable].values
                
                # Add data points
                fig.add_trace(
                    go.Scatter(
                        x=x_vals,
                        y=y_vals,
                        mode='markers',
                        name=f"{condition}",
                        marker=dict(
                            color=condition_colors.get(condition, '#8c564b'), 
                            size=8
                        ),
                        showlegend=(i == 0),  # Only show legend for first subplot
                        hovertemplate=f"<b>{condition}</b><br>" +
                                    f"Time: %{{x}} months<br>" +
                                    f"{y_axis_labels.get(y_axis_variable, y_axis_variable)}: %{{y}}<br>" +
                                    "<extra></extra>"
                    ),
                    row=row, col=col
                )
                
                # Add regression line if we have enough points
                if len(x_vals) >= 2:
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x_vals, y_vals)
                    
                    # Create regression line
                    x_range = np.linspace(x_vals.min() * 0.95, x_vals.max() * 1.05, 100)
                    y_regression = slope * x_range + intercept
                    
                    fig.add_trace(
                        go.Scatter(
                            x=x_range,
                            y=y_regression,
                            mode='lines',
                            name=f"{condition} fit",
                            line=dict(
                                color=condition_colors.get(condition, '#8c564b'),
                                dash='dash',
                                width=2
                            ),
                            showlegend=(i == 0),
                            hovertemplate=f"<b>{condition} Linear Fit</b><br>" +
                                        f"Slope: {slope:.4f}<br>" +
                                        f"R²: {r_value**2:.3f}<br>" +
                                        "<extra></extra>"
                        ),
                        row=row, col=col
                    )
                    
                    # Add statistics annotation
                    if statistics_options:
                        stats_text = []
                        if 'show_r2' in statistics_options:
                            stats_text.append(f"R² = {r_value**2:.3f}")
                        if 'show_slope' in statistics_options:
                            stats_text.append(f"Slope = {slope:.4f}")
                        
                        if stats_text:
                            fig.add_annotation(
                                x=0.95, y=0.95,
                                text="<br>".join(stats_text),
                                showarrow=False,
                                font=dict(size=10, color=condition_colors.get(condition, '#8c564b')),
                                align="right",
                                bgcolor="rgba(255, 255, 255, 0.8)",
                                bordercolor=condition_colors.get(condition, '#8c564b'),
                                borderwidth=1,
                                borderpad=4,
                                xref=f"x{'' if col == 1 else col} domain",
                                yref=f"y{'' if row == 1 else ((row-1)*cols + col)} domain"
                            )
        
        # Update layout
        total_height = (plot_height or 600) * rows
        
        fig.update_layout(
            height=total_height,
            margin=dict(l=40, r=40, t=60, b=40),
            showlegend=True,
            plot_bgcolor="white",
            title_text=f"Stability Analysis: {y_axis_labels.get(y_axis_variable, y_axis_variable)} vs Time"
        )
        
        # Update axes
        for i in range(1, rows + 1):
            for j in range(1, cols + 1):
                fig.update_xaxes(
                    title_text="Time (months)",
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(128, 128, 128, 0.2)',
                    showline=True,
                    linewidth=1,
                    linecolor='rgba(0, 0, 0, 0.3)',
                    row=i, col=j
                )
                fig.update_yaxes(
                    title_text=y_axis_labels.get(y_axis_variable, y_axis_variable),
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(128, 128, 128, 0.2)',
                    showline=True,
                    linewidth=1,
                    linecolor='rgba(0, 0, 0, 0.3)',
                    row=i, col=j
                )
        
        return fig
        
    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error creating plots: {str(e)}",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(color="red")
        )
        return fig