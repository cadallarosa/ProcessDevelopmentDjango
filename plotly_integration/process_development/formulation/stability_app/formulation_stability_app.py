"""
Formulation Stability Analysis App
Dedicated Dash application for analyzing and comparing formulation stability data
"""

import dash
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State, callback_context, dash_table, no_update
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import os

from plotly_integration.models import FormulationData

app = DjangoDash("FormulationStabilityApp")

COLOR_PALETTE = {
    "primary": "#2E86C1",
    "secondary": "#E74C3C",
    "success": "#27AE60",
    "warning": "#F39C12",
    "info": "#8E44AD",
    "light": "#F8F9FA",
    "dark": "#2C3E50",
    "accent": "#3498DB",
    "background": "#FFFFFF",
    "muted": "#6C757D",
}

MODERN_STYLE = {
    "font_family": "'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif",
    "card_shadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
    "border_radius": "8px",
    "spacing": "16px"
}

STORAGE_CONDITIONS = {
    "25C": {"label": "25°C", "color": COLOR_PALETTE["success"]},
    "40C": {"label": "40°C", "color": COLOR_PALETTE["secondary"]},
    "FT": {"label": "Freeze/Thaw", "color": COLOR_PALETTE["warning"]},
    "4C": {"label": "4°C", "color": COLOR_PALETTE["info"]},
    "-80C": {"label": "-80°C", "color": COLOR_PALETTE["primary"]},
}

def get_studies():
    """Get all available formulation experiments"""
    try:
        experiments = FormulationData.objects.values('experiment_id').distinct().order_by('experiment_id')
        return [{'label': exp['experiment_id'], 'value': exp['experiment_id']} for exp in experiments]
    except Exception as e:
        print(f"Error fetching experiments: {e}")
        return []

def get_formulations_for_study(experiment_id):
    """Get all formulations for a specific experiment"""
    try:
        formulations = FormulationData.objects.filter(experiment_id=experiment_id).values('formulation_number').distinct().order_by('formulation_number')
        return [{'label': f"Formulation {f['formulation_number']}", 'value': f['formulation_number']} for f in formulations]
    except Exception as e:
        print(f"Error fetching formulations: {e}")
        return []

def create_header():
    """Create the app header with title and controls"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1([
                    html.I(className="fas fa-chart-line me-3", style={"color": COLOR_PALETTE["primary"]}),
                    "Formulation Stability Analysis"
                ], className="mb-0", style={
                    "fontFamily": MODERN_STYLE["font_family"],
                    "fontWeight": "300",
                    "color": COLOR_PALETTE["dark"]
                }),
                html.P("Analyze formulation stability over time and storage conditions", 
                      className="text-muted mb-0", style={"fontSize": "1.1rem"})
            ], width=12)
        ], className="mb-4")
    ], fluid=True)

def create_control_panel():
    """Create the main control panel for study and formulation selection"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-sliders-h me-2"),
                "Stability Analysis Controls"
            ], className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Select Study:", html_for="study-selector"),
                    dcc.Dropdown(
                        id="study-selector",
                        options=get_studies(),
                        value=None,
                        placeholder="Choose a formulation study...",
                        clearable=False,
                        style={"fontFamily": MODERN_STYLE["font_family"]}
                    )
                ], width=6),
                dbc.Col([
                    dbc.Label("Select Formulations to Compare:", html_for="formulation-selector"),
                    dcc.Dropdown(
                        id="formulation-selector",
                        options=[],
                        value=[],
                        multi=True,
                        placeholder="Select formulations to compare...",
                        style={"fontFamily": MODERN_STYLE["font_family"]}
                    )
                ], width=6)
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Storage Conditions:", html_for="storage-condition-selector"),
                    dbc.Checklist(
                        id="storage-condition-selector",
                        options=[
                            {"label": info["label"], "value": condition} 
                            for condition, info in STORAGE_CONDITIONS.items()
                        ],
                        value=["25C", "40C"],
                        inline=True,
                        style={"fontFamily": MODERN_STYLE["font_family"]}
                    )
                ], width=6),
                dbc.Col([
                    dbc.Label("Analysis Type:", html_for="analysis-type-selector"),
                    dbc.RadioItems(
                        id="analysis-type-selector",
                        options=[
                            {"label": "Stability Over Time", "value": "time_series"},
                            {"label": "Degradation Rates", "value": "degradation_rates"},
                            {"label": "Comparative Analysis", "value": "comparison"}
                        ],
                        value="time_series",
                        inline=True,
                        style={"fontFamily": MODERN_STYLE["font_family"]}
                    )
                ], width=6)
            ])
        ])
    ], className="mb-4", style={"boxShadow": MODERN_STYLE["card_shadow"]})

def create_main_content():
    """Create the main content area with tabs for different views"""
    return dbc.Card([
        dbc.CardHeader([
            dbc.Tabs([
                dbc.Tab(label="Stability Trends", tab_id="stability-trends", active_tab_style={"backgroundColor": COLOR_PALETTE["primary"], "color": "white"}),
                dbc.Tab(label="Degradation Analysis", tab_id="degradation-analysis", active_tab_style={"backgroundColor": COLOR_PALETTE["primary"], "color": "white"}),
                dbc.Tab(label="Statistical Summary", tab_id="statistical-summary", active_tab_style={"backgroundColor": COLOR_PALETTE["primary"], "color": "white"}),
            ], id="main-tabs", active_tab="stability-trends")
        ]),
        dbc.CardBody([
            html.Div(id="main-content-area")
        ], style={"minHeight": "600px"})
    ], style={"boxShadow": MODERN_STYLE["card_shadow"]})

app.layout = dbc.Container([
    dcc.Store(id='selected-data-store'),
    dcc.Store(id='formulation-data-store'),
    
    create_header(),
    create_control_panel(),
    create_main_content(),
    
    dcc.Loading(
        id="loading-main",
        type="default",
        children=html.Div(id="loading-output"),
        style={"zIndex": "9999"}
    )
], fluid=True, className="p-4", style={
    "backgroundColor": COLOR_PALETTE["light"],
    "minHeight": "100vh",
    "fontFamily": MODERN_STYLE["font_family"]
})

from .callbacks.formulation_selection import *
from .callbacks.data_loading import *
from .callbacks.plotting import *
from .callbacks.statistical_analysis import *

if __name__ == '__main__':
    app.run_server(debug=True)