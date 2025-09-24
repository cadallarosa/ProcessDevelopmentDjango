from datetime import datetime

import dash
import pandas as pd
import numpy as np
from dash import dcc, html, Input, Output, State, dash_table
from dash.exceptions import PreventUpdate
from django_plotly_dash import DjangoDash
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from scipy.stats import linregress
from plotly_integration.models import CESDSReport, CESDSMetadata, CESDSTimeSeries, LimsSampleAnalysis, LimsCeSdsResult
from scipy.signal import find_peaks, savgol_filter, argrelextrema
import dash_bootstrap_components as dbc
from openpyxl import load_workbook
import io

app = DjangoDash("CESDSReportViewerApp")

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id="selected-result-ids"),
    dcc.Store(id="reduced-result-ids"),
    dcc.Store(id="nonreduced-result-ids"),
    dcc.Store(id="standard-regression-params"),
    dcc.Store(id="selected-report"),

    dcc.Store(id='url-params', data={}),
    dcc.Store(id='embedded-mode', data=False),
    dcc.Interval(id="load-once", interval=1000, n_intervals=0, max_intervals=1),

    dcc.Store(id='button-success-trigger', data=0),
    dcc.Interval(id='button-reset-interval', interval=5000, n_intervals=0, disabled=True),

    dcc.Store(id="lc-hc-times-store", data={}),

    # Modal for Select Report - keeping existing functionality
    html.Div(
        id="report-modal",
        style={
            "display": "none",
            "position": "fixed",
            "top": "0",
            "left": "0",
            "width": "100%",
            "height": "100%",
            "backgroundColor": "rgba(0, 0, 0, 0.5)",
            "zIndex": "1000"
        },
        children=[
            html.Div(
                style={
                    "position": "relative",
                    "margin": "2% auto",
                    "width": "90%",
                    "maxWidth": "1400px",
                    "height": "85%",
                    "backgroundColor": "white",
                    "borderRadius": "10px",
                    "padding": "20px",
                    "boxShadow": "0 5px 15px rgba(0,0,0,0.3)",
                    "display": "flex",
                    "flexDirection": "column"
                },
                children=[
                    html.Button(
                        "✕",
                        id="close-report-modal-btn",
                        style={
                            "position": "absolute",
                            "top": "10px",
                            "right": "10px",
                            "fontSize": "24px",
                            "border": "none",
                            "backgroundColor": "transparent",
                            "cursor": "pointer",
                            "color": "#666"
                        }
                    ),
                    html.H3("Report Management",
                            style={"marginBottom": "20px", "color": "#0056b3", "textAlign": "center"}),

                    # Tabs for Select/Create
                    dcc.Tabs(
                        id="report-tabs",
                        value="select-tab",
                        children=[
                            dcc.Tab(
                                label="Select Report",
                                value="select-tab",
                                style={"height": "100%"},
                                children=[
                                    html.Div(
                                        style={
                                            "padding": "20px",
                                            "height": "100%",
                                            "display": "flex",
                                            "flexDirection": "column",
                                            "boxSizing": "border-box"
                                        },
                                        children=[
                                            html.H4("Select an Existing Report",
                                                    style={'marginBottom': '20px', 'color': '#0056b3'}),

                                            # Table container that grows to fill available space
                                            html.Div(
                                                style={
                                                    "flexGrow": 1,
                                                    "marginBottom": "20px",
                                                    "minHeight": 0
                                                },
                                                children=[
                                                    dash_table.DataTable(
                                                        id='report-selection-table',
                                                        columns=[
                                                            {"name": "Report ID", "id": "report_id"},
                                                            {"name": "Report Name", "id": "report_name"},
                                                            {"name": "Project ID", "id": "project_id"},
                                                            {"name": "Created By", "id": "user_id"},
                                                            {"name": "Date Created", "id": "date_created"},
                                                        ],
                                                        data=[],
                                                        row_selectable="single",
                                                        selected_rows=[],
                                                        filter_action="native",
                                                        sort_action="native",
                                                        page_action="native",
                                                        page_size=15,
                                                        fixed_rows={'headers': True},
                                                        style_table={
                                                            'height': '90%',
                                                            'overflowY': 'auto',
                                                            'overflowX': 'auto',
                                                            'borderRadius': '5px'
                                                        },
                                                        style_cell={
                                                            'textAlign': 'center',
                                                            'padding': '12px',
                                                            'fontSize': '14px',
                                                            'fontFamily': 'system-ui, -apple-system, sans-serif'
                                                        },
                                                        style_header={
                                                            'backgroundColor': '#f8f9fa',
                                                            'fontWeight': '600',
                                                            'borderBottom': '2px solid #dee2e6'
                                                        },
                                                        style_data={
                                                            'borderBottom': '1px solid #dee2e6'
                                                        },
                                                        style_data_conditional=[
                                                            {
                                                                'if': {'row_index': 'odd'},
                                                                'backgroundColor': '#f8f9fa'
                                                            }
                                                        ]
                                                    )
                                                ]
                                            ),

                                            # Buttons at the bottom
                                            html.Div(
                                                style={'display': 'flex', 'justifyContent': 'flex-end', 'gap': '10px'},
                                                children=[
                                                    html.Button(
                                                        "Cancel",
                                                        id="cancel-select-btn",
                                                        style={
                                                            'backgroundColor': '#6c757d',
                                                            'color': 'white',
                                                            'padding': '8px 16px',
                                                            'border': 'none',
                                                            'borderRadius': '5px',
                                                            'cursor': 'pointer',
                                                            'fontSize': '14px',
                                                            'fontWeight': '500'
                                                        }
                                                    ),
                                                    html.Button(
                                                        "Confirm Selection",
                                                        id="confirm-report-selection",
                                                        style={
                                                            'backgroundColor': '#0056b3',
                                                            'color': 'white',
                                                            'padding': '8px 16px',
                                                            'border': 'none',
                                                            'borderRadius': '5px',
                                                            'cursor': 'pointer',
                                                            'fontSize': '14px',
                                                            'fontWeight': '500'
                                                        }
                                                    ),
                                                ]
                                            )
                                        ]
                                    )
                                ]
                            ),
                            dcc.Tab(
                                label="Create Report",
                                value="create-tab",
                                children=[
                                    html.Div(
                                        style={
                                            "height": "calc(100vh - 300px)",
                                            "overflow": "hidden"
                                        },
                                        children=[
                                            html.Iframe(
                                                src="/plotly_integration/dash-app/app/CreateCESDSReportApp/",
                                                style={
                                                    "width": "100%",
                                                    "height": "100%",
                                                    "border": "none",
                                                    "display": "block"
                                                }
                                            )
                                        ]
                                    )
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    ),

    # Modern toolbar with action buttons
    html.Div(
        id='toolbar-container',
        style={
            'display': 'flex',
            'justifyContent': 'space-between',
            'alignItems': 'center',
            'padding': '20px 30px',
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'margin': '0 30px 30px 30px',
            'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.08)',
            'gap': '10px'
        },
        children=[
            # Left side - Create Report button
            html.Div(
                id='left-toolbar',
                style={'display': 'flex', 'gap': '20px', 'alignItems': 'center'},
                children=[
                    html.Button([
                        html.Span("📊 ", style={'marginRight': '5px'}),
                        "Select/Create Report"
                    ], id="select-create-report-btn", style={
                        'backgroundColor': '#0056b3',
                        'color': 'white',
                        'border': 'none',
                        'padding': '12px 24px',
                        'fontSize': '14px',
                        'cursor': 'pointer',
                        'borderRadius': '8px',
                        'fontWeight': '500',
                        'transition': 'background-color 0.3s ease'
                    }),
                    html.Div([
                        html.Span("Current Report: ", style={'fontWeight': '600', 'color': '#495057'}),
                        html.Span("No report selected", id="current-report-text", style={'color': '#6c757d'})
                    ], style={'marginLeft': '10px', 'fontSize': '15px'})
                ]
            ),

            # Right side - Save buttons
            html.Div(
                style={'display': 'flex', 'gap': '15px'},
                children=[
                    html.Button([
                        html.Span("💾 ", style={'marginRight': '5px'}),
                        "Save Report Settings"
                    ], id="save-settings-btn", style={
                        'backgroundColor': '#28a745',
                        'color': 'white',
                        'border': 'none',
                        'padding': '12px 24px',
                        'fontSize': '14px',
                        'cursor': 'pointer',
                        'borderRadius': '8px',
                        'fontWeight': '500',
                        'transition': 'background-color 0.3s ease'
                    }),
                    html.Button([
                        html.Span("🔗 ", style={'marginRight': '5px'}),
                        "Report Results"
                    ], id="report-results-btn", style={
                        'backgroundColor': '#17a2b8',
                        'color': 'white',
                        'border': 'none',
                        'padding': '12px 24px',
                        'fontSize': '14px',
                        'cursor': 'pointer',
                        'borderRadius': '8px',
                        'fontWeight': '500',
                        'transition': 'background-color 0.3s ease'
                    }),
                ]
            )
        ]
    ),

    # Status messages with modern styling
    html.Div(id="status-message", style={
        'padding': '16px 24px',
        'margin': '0 30px 20px 30px',
        'borderRadius': '8px',
        'display': 'none',
        'fontSize': '15px',
        'fontWeight': '500',
        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
        'transition': 'all 0.3s ease'
    }),

    # Main content area with modern tabs
    html.Div(
        style={
            'padding': '0 30px 30px 30px',
        },
        children=[
            dcc.Tabs(
                id="main-tabs",
                value="tab-reduced",
                persistence=False,
                style={
                    'borderBottom': 'none',
                    'marginBottom': '0'
                },
                children=[
                    # Reduced Tab - Chromatogram only
                    dcc.Tab(
                        label="Reduced",
                        value="tab-reduced",
                        style={
                            'padding': '12px 24px',
                            'borderRadius': '12px 12px 0 0',
                            'marginRight': '4px',
                            'backgroundColor': '#f8f9fa',
                            'border': 'none',
                            'fontWeight': '500'
                        },
                        selected_style={
                            'padding': '12px 24px',
                            'borderRadius': '12px 12px 0 0',
                            'marginRight': '4px',
                            'backgroundColor': 'white',
                            'border': 'none',
                            'fontWeight': '600',
                            'color': '#0056b3',
                            'boxShadow': '0 -2px 10px rgba(0, 0, 0, 0.05)'
                        },
                        children=[
                            html.Div(
                                style={
                                    'background': 'white',
                                    'borderRadius': '0 12px 12px 12px',
                                    'padding': '30px',
                                    'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.08)'
                                },
                                children=[
                                    html.Div(style={"display": "flex", "gap": "30px"}, children=[
                                        # Chromatogram section
                                        html.Div([
                                            dcc.Graph(
                                                id="reduced-chromatogram",
                                                config={
                                                    'responsive': True,
                                                    'displayModeBar': True,
                                                    'displaylogo': False
                                                },
                                                # style={"height": "800px"},
                                                figure={'layout': {'autosize': True}}
                                            )
                                        ], style={"flex": "1"}),

                                        # Modern control panel
                                        html.Div([
                                            html.Div(
                                                style={
                                                    'background': '#f8f9fa',
                                                    'borderRadius': '12px',
                                                    'padding': '20px',
                                                    'marginBottom': '20px'
                                                },
                                                children=[
                                                    html.H4("Marker Settings",
                                                            style={'marginTop': '0', 'color': '#495057'}),
                                                    html.Label("Marker RT (min):",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="marker-rt", type="number", value=7, step=0.1,
                                                              style={"width": "100%", "marginBottom": "15px",
                                                                     "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),

                                                    html.Label("Marker Label:",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="marker-label", type="text", value="10 kDa",
                                                              style={"width": "100%", "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),
                                                ]
                                            ),

                                            html.Div(
                                                style={
                                                    'background': '#f8f9fa',
                                                    'borderRadius': '12px',
                                                    'padding': '20px',
                                                    'marginBottom': '20px'
                                                },
                                                children=[
                                                    html.H4("Plot Settings",
                                                            style={'marginTop': '0', 'color': '#495057'}),
                                                    html.Label("Y-Axis Scaling:",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="reduced-y-axis-scaling", type="number", value=1.0,
                                                              step=0.01,
                                                              style={"width": "100%", "marginBottom": "15px",
                                                                     "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),

                                                    html.Label("Subplot Vertical Spacing:",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="reduced-subplot-vertical-spacing", type="number",
                                                              value=0.04, step=0.005,
                                                              style={"width": "100%", "marginBottom": "15px",
                                                                     "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),

                                                    html.Label("Display Options:",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Checklist(
                                                        id='reduced-show-mw-checklist',
                                                        options=[
                                                            {'label': ' Show MW in Annotations', 'value': 'show_mw'}
                                                        ],
                                                        value=['show_mw'],
                                                        style={'marginTop': '5px', 'color': '#495057'}
                                                    ),
                                                ]
                                            ),

                                            html.Div(
                                                style={
                                                    'background': '#f8f9fa',
                                                    'borderRadius': '12px',
                                                    'padding': '20px',
                                                    'marginBottom': '20px'
                                                },
                                                children=[
                                                    html.H4("Peak Detection",
                                                            style={'marginTop': '0', 'color': '#495057'}),

                                                    html.Label("Skip Time After Marker (min):",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="skip-time", type="number", value=0.3, step=0.05,
                                                              style={"width": "100%", "marginBottom": "15px",
                                                                     "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),

                                                    html.Label("Max Peaks:",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="max-peaks", type="number", value=4, step=1, min=1,
                                                              style={"width": "100%", "marginBottom": "15px",
                                                                     "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),

                                                    html.Label("Prominence Threshold:",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="prominence-threshold", type="number", value=100.0,
                                                              step=0.01,
                                                              style={"width": "100%", "marginBottom": "15px",
                                                                     "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),

                                                    html.Label("Valley Search Window (min):",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="valley-search-window", type="number", value=1.5,
                                                              step=0.1,
                                                              style={"width": "100%", "marginBottom": "15px",
                                                                     "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),

                                                    html.Label("Valley Drop Ratio (0–1):",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="valley-drop-ratio", type="number", value=0.2,
                                                              step=0.05, min=0, max=1,
                                                              style={"width": "100%", "marginBottom": "15px",
                                                                     "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),

                                                    html.Label("Smoothing Window (odd):",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="smoothing-window", type="number", value=3, step=2,
                                                              min=3,
                                                              style={"width": "100%", "marginBottom": "15px",
                                                                     "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),

                                                    html.Label("Smoothing Polyorder:",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="smoothing-polyorder", type="number", value=1, step=1,
                                                              min=1,
                                                              style={"width": "100%", "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),
                                                ]
                                            ),

                                            html.Div(
                                                style={
                                                    'background': '#e3f2fd',
                                                    'borderRadius': '12px',
                                                    'padding': '20px'
                                                },
                                                children=[
                                                    html.H4("Light Chain Timing",
                                                            style={'marginTop': '0', 'color': '#1976d2'}),
                                                    html.Button("Calculate Light Chain Time", id="calc-light-chain-btn",
                                                                style={
                                                                    "width": "100%",
                                                                    "marginBottom": "15px",
                                                                    "backgroundColor": "#1976d2",
                                                                    "color": "white",
                                                                    "border": "none",
                                                                    "padding": "10px",
                                                                    "borderRadius": "6px",
                                                                    "fontWeight": "500",
                                                                    "cursor": "pointer",
                                                                    "transition": "background-color 0.3s ease"
                                                                }),
                                                    dcc.Input(id="light-chain-time", type="number",
                                                              placeholder="Light Chain Time (min)",
                                                              readOnly=True,
                                                              style={"width": "100%", "borderRadius": "6px",
                                                                     "border": "1px solid #90caf9", "padding": "8px",
                                                                     "backgroundColor": "white"})
                                                ]
                                            ),
                                        ], style={"width": "300px", "flexShrink": "0"})
                                    ])
                                ]
                            )
                        ]
                    ),

                    # Non-Reduced Tab - Chromatogram only
                    dcc.Tab(
                        label="Non-Reduced",
                        value="tab-nonreduced",
                        style={
                            'padding': '12px 24px',
                            'borderRadius': '12px 12px 0 0',
                            'marginRight': '4px',
                            'backgroundColor': '#f8f9fa',
                            'border': 'none',
                            'fontWeight': '500'
                        },
                        selected_style={
                            'padding': '12px 24px',
                            'borderRadius': '12px 12px 0 0',
                            'marginRight': '4px',
                            'backgroundColor': 'white',
                            'border': 'none',
                            'fontWeight': '600',
                            'color': '#0056b3',
                            'boxShadow': '0 -2px 10px rgba(0, 0, 0, 0.05)'
                        },
                        children=[
                            html.Div(
                                style={
                                    'background': 'white',
                                    'borderRadius': '0 12px 12px 12px',
                                    'padding': '30px',
                                    'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.08)'
                                },
                                children=[
                                    html.Div(style={"display": "flex", "gap": "30px"}, children=[
                                        # Chromatogram section
                                        html.Div([
                                            dcc.Graph(
                                                id="nonreduced-chromatogram",
                                                config={
                                                    'responsive': True,
                                                    'displayModeBar': True,
                                                    'displaylogo': False
                                                },
                                                style={"height": "800px"},
                                                figure={'layout': {'autosize': True}}
                                            )
                                        ], style={"flex": "1"}),

                                        # Modern control panel for non-reduced
                                        html.Div([
                                            html.Div(
                                                style={
                                                    'background': '#f8f9fa',
                                                    'borderRadius': '12px',
                                                    'padding': '20px',
                                                    'marginBottom': '20px'
                                                },
                                                children=[
                                                    html.H4("Marker Settings",
                                                            style={'marginTop': '0', 'color': '#495057'}),
                                                    html.Label("Marker RT (min):",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="nr-marker-rt", type="number", value=7, step=0.1,
                                                              style={"width": "100%", "marginBottom": "15px",
                                                                     "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),

                                                    html.Label("Marker Label:",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="nr-marker-label", type="text", value="10 kDa",
                                                              style={"width": "100%", "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),
                                                ]
                                            ),

                                            html.Div(
                                                style={
                                                    'background': '#f8f9fa',
                                                    'borderRadius': '12px',
                                                    'padding': '20px',
                                                    'marginBottom': '20px'
                                                },
                                                children=[
                                                    html.H4("Plot Settings",
                                                            style={'marginTop': '0', 'color': '#495057'}),
                                                    html.Label("Y-Axis Scaling:",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="non-reduced-y-axis-scaling", type="number", value=1.0,
                                                              step=0.01,
                                                              style={"width": "100%", "marginBottom": "15px",
                                                                     "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),

                                                    html.Label("Subplot Vertical Spacing:",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="non-reduced-subplot-vertical-spacing", type="number",
                                                              value=0.04, step=0.005,
                                                              style={"width": "100%", "marginBottom": "15px",
                                                                     "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),

                                                    html.Label("Display Options:",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Checklist(
                                                        id='nonreduced-show-mw-checklist',
                                                        options=[
                                                            {'label': ' Show MW in Annotations', 'value': 'show_mw'}
                                                        ],
                                                        value=['show_mw'],
                                                        style={'marginTop': '5px', 'color': '#495057'}
                                                    ),
                                                ]
                                            ),

                                            html.Div(
                                                style={
                                                    'background': '#f8f9fa',
                                                    'borderRadius': '12px',
                                                    'padding': '20px',
                                                    'marginBottom': '20px'
                                                },
                                                children=[
                                                    html.H4("Peak Detection",
                                                            style={'marginTop': '0', 'color': '#495057'}),

                                                    html.Label("Skip Time After Marker (min):",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="nr-skip-time", type="number", value=0.3, step=0.05,
                                                              style={"width": "100%", "marginBottom": "15px",
                                                                     "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),

                                                    html.Label("Max Peaks:",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="nr-max-peaks", type="number", value=5, step=1, min=1,
                                                              style={"width": "100%", "marginBottom": "15px",
                                                                     "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),

                                                    html.Label("Prominence Threshold:",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="nr-prominence-threshold", type="number", value=100,
                                                              step=0.01,
                                                              style={"width": "100%", "marginBottom": "15px",
                                                                     "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),

                                                    html.Label("Valley Search Window (min):",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="nr-valley-search-window", type="number", value=2,
                                                              step=0.1,
                                                              style={"width": "100%", "marginBottom": "15px",
                                                                     "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),

                                                    html.Label("Valley Drop Ratio (0–1):",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="nr-valley-drop-ratio", type="number", value=0.2,
                                                              step=0.05, min=0, max=1,
                                                              style={"width": "100%", "marginBottom": "15px",
                                                                     "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),

                                                    html.Label("Smoothing Window (odd):",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="nr-smoothing-window", type="number", value=3, step=2,
                                                              min=3,
                                                              style={"width": "100%", "marginBottom": "15px",
                                                                     "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),

                                                    html.Label("Smoothing Polyorder:",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="nr-smoothing-polyorder", type="number", value=1,
                                                              step=1, min=1,
                                                              style={"width": "100%", "marginBottom": "15px",
                                                                     "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),

                                                    html.Label("Intact Time (optional):",
                                                               style={'fontWeight': '500', 'color': '#6c757d'}),
                                                    dcc.Input(id="nr-intact-time", type="number",
                                                              placeholder="Use tallest peak if blank",
                                                              style={"width": "100%", "borderRadius": "6px",
                                                                     "border": "1px solid #ced4da", "padding": "8px"}),
                                                ]
                                            ),
                                        ], style={"width": "300px", "flexShrink": "0"})
                                    ])
                                ]
                            )
                        ]
                    ),

                    # Standard Analysis Tab with modern styling
                    dcc.Tab(
                        label="Standard Analysis",
                        value="tab-std-analysis",
                        style={
                            'padding': '12px 24px',
                            'borderRadius': '12px 12px 0 0',
                            'marginRight': '4px',
                            'backgroundColor': '#f8f9fa',
                            'border': 'none',
                            'fontWeight': '500'
                        },
                        selected_style={
                            'padding': '12px 24px',
                            'borderRadius': '12px 12px 0 0',
                            'marginRight': '4px',
                            'backgroundColor': 'white',
                            'border': 'none',
                            'fontWeight': '600',
                            'color': '#0056b3',
                            'boxShadow': '0 -2px 10px rgba(0, 0, 0, 0.05)'
                        },
                        children=[
                            html.Div(
                                style={
                                    'background': 'white',
                                    'borderRadius': '0 12px 12px 12px',
                                    'padding': '30px',
                                    'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.08)'
                                },
                                children=[
                                    html.H3("Standard Analysis",
                                            style={'textAlign': 'center', 'color': '#0056b3', 'marginBottom': '30px'}),

                                    html.Div([
                                        html.Label("Select Standard Sample ID:",
                                                   style={'color': '#495057', 'fontWeight': '500',
                                                          'marginBottom': '10px', 'display': 'block'}),
                                        dcc.Dropdown(
                                            id='standard-id-dropdown',
                                            placeholder="Select a Standard Sample",
                                            style={'width': '100%', 'borderRadius': '8px'}
                                        )
                                    ], style={'marginBottom': '30px'}),

                                    dcc.Graph(id='standard-peak-plot'),

                                    html.Div([
                                        html.P("Regression Equation: ", id="regression-equation",
                                               style={'fontWeight': '500'}),
                                        html.P("R² Value: ", id="r-squared-value", style={'fontWeight': '500'}),
                                        html.P("Estimated MW for RT: ", id="estimated-mw", style={'fontWeight': '500'}),

                                        html.Div(style={'display': 'flex', 'gap': '15px', 'marginTop': '20px'},
                                                 children=[
                                                     dcc.Input(
                                                         id="rt-input",
                                                         type="number",
                                                         placeholder="Enter Retention Time",
                                                         style={'flex': '1', 'padding': '10px', 'borderRadius': '6px',
                                                                'border': '1px solid #ced4da'}
                                                     ),
                                                     html.Button("Calculate MW", id="calculate-mw-button", style={
                                                         'backgroundColor': '#0056b3',
                                                         'color': 'white',
                                                         'border': 'none',
                                                         'padding': '10px 20px',
                                                         'cursor': 'pointer',
                                                         'borderRadius': '6px',
                                                         'fontWeight': '500',
                                                         'transition': 'background-color 0.3s ease'
                                                     }),
                                                 ]),
                                        dcc.Graph(id='regression-plot', style={'marginTop': '20px'})
                                    ], style={
                                        'marginTop': '30px',
                                        'padding': '25px',
                                        'border': '1px solid #e3f2fd',
                                        'borderRadius': '12px',
                                        'backgroundColor': '#f8fbff',
                                    }),

                                    html.Div([
                                        html.H4("Detected Peaks & Assigned MWs",
                                                style={'color': '#0056b3', 'marginBottom': '20px'}),
                                        html.Div(style={'display': 'flex', 'alignItems': 'center', 'gap': '15px',
                                                        'marginBottom': '20px'}, children=[
                                            html.Label("Number of Peaks to Use:",
                                                       style={'fontWeight': '500', 'color': '#495057'}),
                                            dcc.Input(
                                                id="num-std-peaks",
                                                type="number",
                                                value=7,
                                                min=1,
                                                max=20,
                                                step=1,
                                                style={'width': '100px', 'padding': '8px', 'borderRadius': '6px',
                                                       'border': '1px solid #ced4da'}
                                            ),
                                        ]),
                                        dash_table.DataTable(
                                            id="std-detected-peak-table",
                                            columns=[
                                                {"name": "Retention Time (min)", "id": "peak_rt", "type": "numeric"},
                                                {"name": "Peak Height", "id": "peak_height", "type": "numeric"},
                                                {"name": "Assigned MW (kDa)", "id": "assigned_mw", "type": "numeric",
                                                 "editable": True}
                                            ],
                                            data=[],
                                            editable=True,
                                            row_selectable="multi",
                                            style_table={'overflowX': 'auto', 'borderRadius': '8px'},
                                            style_cell={'textAlign': 'center', 'padding': '12px'},
                                            style_header={
                                                'fontWeight': '600',
                                                'backgroundColor': '#f8f9fa',
                                                'borderBottom': '2px solid #dee2e6'
                                            },
                                            style_data_conditional=[
                                                {
                                                    'if': {'row_index': 'odd'},
                                                    'backgroundColor': '#f8f9fa'
                                                }
                                            ]
                                        )
                                    ], style={
                                        'marginTop': '30px',
                                        'padding': '25px',
                                        'border': '1px solid #e3f2fd',
                                        'borderRadius': '12px',
                                        'backgroundColor': '#f8fbff'
                                    })
                                ]
                            )
                        ]
                    ),

                    # NEW: Results Tables Tab
                    dcc.Tab(
                        label="Results Tables",
                        value="tab-results",
                        style={
                            'padding': '12px 24px',
                            'borderRadius': '12px 12px 0 0',
                            'marginRight': '4px',
                            'backgroundColor': '#f8f9fa',
                            'border': 'none',
                            'fontWeight': '500'
                        },
                        selected_style={
                            'padding': '12px 24px',
                            'borderRadius': '12px 12px 0 0',
                            'marginRight': '4px',
                            'backgroundColor': 'white',
                            'border': 'none',
                            'fontWeight': '600',
                            'color': '#0056b3',
                            'boxShadow': '0 -2px 10px rgba(0, 0, 0, 0.05)'
                        },
                        children=[
                            html.Div(
                                style={
                                    'background': 'white',
                                    'borderRadius': '0 12px 12px 12px',
                                    'padding': '30px',
                                    'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.08)'
                                },
                                children=[
                                    # Reduced Results Section
                                    html.Div(
                                        style={
                                            'marginBottom': '40px'
                                        },
                                        children=[
                                            html.Div(
                                                style={
                                                    'display': 'flex',
                                                    'justifyContent': 'space-between',
                                                    'alignItems': 'center',
                                                    'marginBottom': '20px',
                                                    'paddingBottom': '15px',
                                                    'borderBottom': '2px solid #e9ecef'
                                                },
                                                children=[
                                                    html.H3("Reduced Results",
                                                            style={
                                                                'color': '#0056b3',
                                                                'margin': '0',
                                                                'fontWeight': '500'
                                                            }),
                                                    html.Button(
                                                        "Export Reduced Table",
                                                        id="export-reduced-btn",
                                                        style={
                                                            'padding': '8px 20px',
                                                            'backgroundColor': '#17a2b8',
                                                            'border': 'none',
                                                            'borderRadius': '6px',
                                                            'color': 'white',
                                                            'fontWeight': '500',
                                                            'cursor': 'pointer',
                                                            'transition': 'background-color 0.3s ease'
                                                        }
                                                    )
                                                ]
                                            ),
                                            dash_table.DataTable(
                                                id="reduced-table",
                                                columns=[],
                                                data=[],
                                                style_header={
                                                    'backgroundColor': '#f8f9fa',
                                                    'fontWeight': '600',
                                                    'textAlign': 'center',
                                                    'borderBottom': '2px solid #dee2e6',
                                                    'padding': '12px'
                                                },
                                                style_table={
                                                    'overflowX': 'auto',
                                                    'borderRadius': '8px',
                                                    'border': '1px solid #dee2e6'
                                                },
                                                style_cell={
                                                    'textAlign': 'center',
                                                    'padding': '12px',
                                                    'borderRight': '1px solid #e9ecef'
                                                },
                                                style_data_conditional=[
                                                    {
                                                        'if': {'row_index': 'odd'},
                                                        'backgroundColor': '#f8f9fa'
                                                    }
                                                ]
                                            ),
                                            dcc.Download(id="download-reduced-xlsx")
                                        ]
                                    ),

                                    # Non-Reduced Results Section
                                    html.Div([
                                        html.Div(
                                            style={
                                                'display': 'flex',
                                                'justifyContent': 'space-between',
                                                'alignItems': 'center',
                                                'marginBottom': '20px',
                                                'paddingBottom': '15px',
                                                'borderBottom': '2px solid #e9ecef'
                                            },
                                            children=[
                                                html.H3("Non-Reduced Results",
                                                        style={
                                                            'color': '#0056b3',
                                                            'margin': '0',
                                                            'fontWeight': '500'
                                                        }),
                                                html.Button(
                                                    "Export Non-Reduced Table",
                                                    id="export-nonreduced-btn",
                                                    style={
                                                        'padding': '8px 20px',
                                                        'backgroundColor': '#17a2b8',
                                                        'border': 'none',
                                                        'borderRadius': '6px',
                                                        'color': 'white',
                                                        'fontWeight': '500',
                                                        'cursor': 'pointer',
                                                        'transition': 'background-color 0.3s ease'
                                                    }
                                                )
                                            ]
                                        ),
                                        dash_table.DataTable(
                                            id="nonreduced-table",
                                            columns=[],
                                            data=[],
                                            style_header={
                                                'backgroundColor': '#f8f9fa',
                                                'fontWeight': '600',
                                                'textAlign': 'center',
                                                'borderBottom': '2px solid #dee2e6',
                                                'padding': '12px'
                                            },
                                            style_table={
                                                'overflowX': 'auto',
                                                'borderRadius': '8px',
                                                'border': '1px solid #dee2e6'
                                            },
                                            style_cell={
                                                'textAlign': 'center',
                                                'padding': '12px',
                                                'borderRight': '1px solid #e9ecef'
                                            },
                                            style_data_conditional=[
                                                {
                                                    'if': {'row_index': 'odd'},
                                                    'backgroundColor': '#f8f9fa'
                                                }
                                            ]
                                        ),
                                        dcc.Download(id="download-nonreduced-xlsx")
                                    ])
                                ]
                            )
                        ]
                    ),
                ]
            )
        ]
    )
])


# Combined URL parsing and report selection
@app.callback(
    [Output('url-params', 'data'),
     Output('embedded-mode', 'data'),
     Output('selected-report', 'data'),
     Output("selected-result-ids", "data")],
    [Input('url', 'search'),
     Input("confirm-report-selection", "n_clicks")],
    [State("report-selection-table", "selected_rows"),
     State("report-selection-table", "data")],
    prevent_initial_call=False
)
def parse_url_and_handle_report_selection(search, confirm_clicks, selected_rows, table_data):
    ctx = dash.callback_context

    # Parse URL parameters
    url_params = {}
    embedded = False
    report_id = None
    result_ids = []

    if search:
        # Parse query parameters
        from urllib.parse import parse_qs
        params = parse_qs(search.lstrip('?'))

        # Extract parameters
        if 'embedded' in params:
            embedded = params['embedded'][0].lower() in ['true', '1', 'yes']
            url_params['embedded'] = embedded

        if 'report_id' in params:
            try:
                report_id = int(params['report_id'][0])
                url_params['report_id'] = report_id
            except:
                pass

    # Get the ID of the component that triggered the callback
    if not ctx.triggered:
        triggered_id = None
    else:
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Handle report selection confirmation
    if triggered_id == "confirm-report-selection" and selected_rows and confirm_clicks:
        row = table_data[selected_rows[0]]
        report = CESDSReport.objects.filter(id=row["report_id"]).first()
        if report:
            report_id = report.id
            result_ids = [r.strip() for r in report.selected_result_ids.split(",")]

    # Handle URL-based report selection
    elif report_id and not triggered_id == "confirm-report-selection":
        try:
            report = CESDSReport.objects.get(id=int(report_id))
            result_ids = [r.strip() for r in report.selected_result_ids.split(",")]
        except CESDSReport.DoesNotExist:
            result_ids = []

    return url_params, embedded, report_id, result_ids


@app.callback(
    [Output("report-modal", "style"),
     Output("current-report-text", "children")],
    [Input("select-create-report-btn", "n_clicks"),
     Input("close-report-modal-btn", "n_clicks"),
     Input("cancel-select-btn", "n_clicks"),
     Input("confirm-report-selection", "n_clicks"),
     Input("load-once", "n_intervals"),
     Input("url-params", "data")],
    [State("report-modal", "style"),
     State("selected-report", "data"),
     State("report-selection-table", "selected_rows"),
     State("report-selection-table", "data"),
     State("embedded-mode", "data")],
    prevent_initial_call=False
)
def toggle_report_modal(open_clicks, close_clicks, cancel_clicks, confirm_clicks, load_interval,
                        url_params, current_style, selected_report, selected_rows,
                        table_data, embedded):
    ctx = dash.callback_context

    # Get the ID of the component that triggered the callback
    if not ctx.triggered:
        triggered_id = None
    else:
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Initial load with URL params
    if triggered_id == "load-once" and url_params.get("report_id") and not embedded:
        report_id = url_params.get("report_id")
        try:
            report = CESDSReport.objects.get(id=int(report_id))
            return current_style, f"{report.report_name}"
        except CESDSReport.DoesNotExist:
            return current_style, "Invalid report ID"

    # Handle button clicks
    if triggered_id == "select-create-report-btn":
        return {**current_style, "display": "block"}, dash.no_update

    elif triggered_id in ["close-report-modal-btn", "cancel-select-btn"]:
        return {**current_style, "display": "none"}, dash.no_update

    elif triggered_id == "confirm-report-selection" and selected_rows:
        selected_report_data = table_data[selected_rows[0]]
        report_name = selected_report_data.get("report_name", "Unknown Report")
        return {**current_style, "display": "none"}, f"{report_name}"

    # Default: show report name if selected
    if selected_report:
        try:
            report = CESDSReport.objects.get(report_id=int(selected_report))
            return current_style, f"{report.report_name}"
        except CESDSReport.DoesNotExist:
            return current_style, "Invalid report"

    return current_style, "No report selected"


@app.callback(
    Output("report-selection-table", "data"),
    [Input("report-modal", "style"),
     Input("report-tabs", "value")],  # Trigger when modal opens or tab changes
    prevent_initial_call=True
)
def populate_report_table(modal_style, active_tab):
    """Populate the report selection table when the modal is opened and select tab is active"""

    # Only populate if modal is visible and we're on the select tab
    if modal_style.get("display") == "block" and active_tab == "select-tab":
        try:
            # Fetch all reports with analysis_type=2 for Titer
            reports = CESDSReport.objects.all().order_by('-date_created')

            report_data = []
            for report in reports:
                report_data.append({
                    "report_id": report.id,
                    "report_name": report.report_name,
                    "project_id": report.project_id,
                    "user_id": report.user_id,
                    "date_created": report.date_created.strftime("%Y-%m-%d %H:%M") if report.date_created else ""
                })

            return report_data
        except Exception as e:
            print(f"Error fetching reports: {e}")
            return []

    return dash.no_update


@app.callback(
    [Output("reduced-result-ids", "data"),
     Output("nonreduced-result-ids", "data")],
    Input("selected-result-ids", "data")
)
def split_result_ids_by_prefix(result_ids):
    if not result_ids:
        return [], []

    metas = CESDSMetadata.objects.filter(id__in=result_ids)
    # Filter out samples with 'STD' in the sample name (case insensitive)
    metas = [m for m in metas if not (m.sample_id_full and "std" in m.sample_id_full.lower())]

    reduced = [m.id for m in metas if m.sample_prefix and m.sample_prefix.lower() == "r"]
    nonreduced = [m.id for m in metas if m.sample_prefix and m.sample_prefix.lower() == "nr"]
    return reduced, nonreduced


def detect_valley_to_valley_peaks(
        df,
        signal_col="channel_1",
        time_col="time_min",
        max_peaks=3,
        prominence_threshold=1.0,
        valley_search_window=3.0,
        valley_drop_ratio=0.2,
        smoothing_window=11,
        smoothing_polyorder=3
):
    """
    Detects peaks using valley-to-valley integration with adaptive valley thresholding.
    Returns a list of dictionaries with peak info.
    """
    from scipy.signal import savgol_filter, find_peaks

    time = df[time_col].values
    signal = df[signal_col].values
    smoothed = savgol_filter(signal, window_length=smoothing_window, polyorder=smoothing_polyorder)

    interval = time[1] - time[0]
    min_distance = int(0.3 / interval)
    peak_indices, _ = find_peaks(signal, prominence=prominence_threshold, distance=min_distance)

    peak_indices = sorted(peak_indices, key=lambda i: smoothed[i], reverse=True)[:max_peaks]
    peak_indices.sort()

    peak_infos = []

    for idx in peak_indices:
        peak_time = time[idx]
        peak_height = smoothed[idx]
        min_valley_height = peak_height * (1 - valley_drop_ratio)

        left_limit = max(0, idx - int(valley_search_window / interval))
        left_valley_idx = left_limit + np.argmin(smoothed[left_limit:idx])
        left_valley_val = smoothed[left_valley_idx]

        right_limit = min(len(smoothed) - 1, idx + int(valley_search_window / interval))
        right_valley_idx = idx + np.argmin(smoothed[idx:right_limit + 1])
        right_valley_val = smoothed[right_valley_idx]

        if left_valley_val > min_valley_height or right_valley_val > min_valley_height:
            continue

        baseline = np.linspace(left_valley_val, right_valley_val, right_valley_idx - left_valley_idx + 1)
        signal_segment = smoothed[left_valley_idx:right_valley_idx + 1]
        time_segment = time[left_valley_idx:right_valley_idx + 1]
        area = np.trapz(signal_segment - baseline, time_segment)

        if area > 0:
            peak_infos.append({
                "peak_time": time[idx],
                "peak_height": peak_height,
                "area": area,
                "start_time": time[left_valley_idx],
                "end_time": time[right_valley_idx],
                "baseline": baseline,
                "baseline_time": time_segment,
                "peak_index": idx
            })

    return sorted(peak_infos, key=lambda x: x["area"], reverse=True), smoothed


def shade_peak(fig, df, start_time, end_time, baseline, row, col, label, peak_time, peak_height, class_label):
    PEAK_CLASS_COLORS = {
        "LMW": "rgba(76, 175, 80, 0.3)",  # green (complement of red)
        "Intact": "rgba(33, 150, 243, 0.3)",  # blue (cool, clinical)
        "Light Chain": "rgba(33, 150, 243, 0.3)",  # blue (cool, clinical)
        "Heavy Chain": "rgba(255, 193, 7, 0.3)",  # amber (warm, eye-catching)
        "HMW": "rgba(244, 67, 54, 0.3)",  # red (danger, HMW)

    }

    color = PEAK_CLASS_COLORS.get(class_label, "rgba(0,100,200,0.2)")  # fallback gray

    region = df[(df["time_min"] >= start_time) & (df["time_min"] <= end_time)].copy()
    if region.empty:
        return

    fig.add_trace(
        go.Scatter(
            x=np.concatenate([region["time_min"], region["time_min"][::-1]]),
            y=np.concatenate([region["channel_1"], [baseline] * len(region)]),
            fill="toself",
            fillcolor=color,
            line=dict(color="rgba(255,255,255,0)"),
            showlegend=False,
            hoverinfo="skip"
        ),
        row=row,
        col=col
    )

    fig.add_annotation(
        x=peak_time,
        y=peak_height,
        text=label,
        showarrow=True,
        arrowhead=1,
        ax=0,
        ay=-30,
        row=row,
        col=col
    )


def generate_chromatogram_figure_advanced(
        result_df_by_id,
        title="Chromatograms",
        marker_rt=None,
        marker_label="10 kDa",
        skip_time=0.3,
        max_peaks=4,
        prominence_threshold=0.05,
        valley_search_window=3.0,
        valley_drop_ratio=0.2,
        smoothing_window=11,
        smoothing_polyorder=3,
        light_chain_time=None,
        table_output=None,
        regression_slope=None,
        regression_intercept=None,
        y_scale=1,
        subplot_vertical_spacing=0.25,
        show_mw_in_annotations=True,
):
    if not result_df_by_id:
        return go.Figure(), []

    num_rows = len(result_df_by_id)
    fig = make_subplots(
        rows=num_rows, cols=1,
        shared_xaxes=False,
        vertical_spacing=subplot_vertical_spacing,
        subplot_titles=[meta["sample_id"] for meta in result_df_by_id.values()]
    )

    for i, (mid, meta) in enumerate(result_df_by_id.items(), start=1):
        df = meta["data"]
        if df.empty:
            continue

        fig.add_trace(
            go.Scatter(x=df["time_min"], y=df["channel_1"], mode="lines", name=meta["sample_id"]),
            row=i, col=1
        )

        marker_peak_time = None
        if marker_rt is not None:
            df_marker = df[(df["time_min"] >= marker_rt - 0.5) & (df["time_min"] <= marker_rt + 0.5)]
            if not df_marker.empty:
                idx = df_marker["channel_1"].idxmax()
                marker_peak_time = df_marker.loc[idx, "time_min"]
                peak_height = df_marker.loc[idx, "channel_1"]
                fig.add_annotation(
                    x=marker_peak_time,
                    y=peak_height,
                    text=f"{marker_label} ({marker_peak_time:.2f} min)",
                    showarrow=True,
                    arrowhead=1,
                    ax=0,
                    ay=-40,
                    row=i, col=1
                )

        df_after_marker = df[df["time_min"] > (marker_peak_time or 0) + skip_time].copy()
        peaks, smoothed = detect_valley_to_valley_peaks(
            df_after_marker,
            signal_col="channel_1",
            time_col="time_min",
            max_peaks=max_peaks,
            prominence_threshold=prominence_threshold,
            valley_search_window=valley_search_window,
            valley_drop_ratio=valley_drop_ratio,
            smoothing_window=smoothing_window,
            smoothing_polyorder=smoothing_polyorder,
        )

        peaks = sorted(peaks, key=lambda x: x["peak_height"], reverse=True)
        light_chain = heavy_chain = None
        if len(peaks) >= 2:
            top2 = peaks[:2]
            if top2[0]["peak_time"] < top2[1]["peak_time"]:
                light_chain, heavy_chain = top2[0], top2[1]
            else:
                light_chain, heavy_chain = top2[1], top2[0]

        classified_peaks = []

        for p in peaks:
            class_label = None
            if p == light_chain:
                class_label = "Light Chain"
            elif p == heavy_chain:
                class_label = "Heavy Chain"
            elif light_chain and p["peak_time"] < light_chain["peak_time"]:
                class_label = "LMW"
            elif heavy_chain and p["peak_time"] > heavy_chain["peak_time"]:
                class_label = "HMW"

            if class_label:
                classified_peaks.append((p, class_label))

        total_area = sum(p["area"] for p, _ in classified_peaks)
        percentages = {"LMW": 0.0, "Light Chain": 0.0, "Heavy Chain": 0.0, "HMW": 0.0}

        max_signal = df["channel_1"].max()
        if not y_scale or y_scale == 1:
            fig.update_yaxes(title_text="UV", row=i, col=1)
        else:
            y_max = max_signal * y_scale
            fig.update_yaxes(
                title_text="UV",
                autorange=True,
                autorangeoptions=dict(maxallowed=y_max),
                row=i, col=1
            )

        fig.update_xaxes(title_text="Time (min)", row=i, col=1)

        # Store MW calculations for each peak class (reduced method)
        mw_values = {"LMW": None, "Light Chain": None, "Heavy Chain": None, "HMW": None}
        peak_times = {"LMW": None, "Light Chain": None, "Heavy Chain": None, "HMW": None}

        for p, class_label in classified_peaks:
            pct = (p["area"] / total_area * 100) if total_area else 0
            percentages[class_label] += pct
            label = f"{class_label}<br>({pct:.1f}%)"

            # Store the peak time for this class
            peak_times[class_label] = p["peak_time"]

            # Calculate MW and store it
            if regression_slope is not None and regression_intercept is not None:
                log_mw = regression_slope * p["peak_time"] + regression_intercept
                mw_kda = np.exp(log_mw)
                
                # Only add MW to label if show_mw_in_annotations is True
                if show_mw_in_annotations:
                    label += f"<br>{mw_kda:.1f} kDa"

                # Store the MW for this peak class
                mw_values[class_label] = round(mw_kda, 1)

            peak_height = p["peak_height"]
            if y_scale and y_scale != 1:
                peak_height = min(peak_height, y_max)

            shade_peak(
                fig, df,
                start_time=p["start_time"],
                end_time=p["end_time"],
                baseline=p["baseline"][0],
                row=i, col=1,
                label=label,
                peak_time=p["peak_time"],
                peak_height=peak_height,
                class_label=class_label
            )

        total_pct = sum(percentages.values())
        if abs(total_pct - 100) > 1e-2:
            print(f"[DEBUG] {meta['sample_id']} percentages do not sum to 100%: {total_pct:.2f}%")

        if table_output is not None:
            table_output.append({
                "Sample Name": meta["sample_id"],
                "LMW (%)": round(percentages["LMW"], 1),
                "Light Chain (%)": round(percentages["Light Chain"], 1),
                "Heavy Chain (%)": round(percentages["Heavy Chain"], 1),
                "HMW (%)": round(percentages["HMW"], 1),
                # Add MW columns for reduced method
                "LMW MW (kDa)": mw_values["LMW"],
                "Light Chain MW (kDa)": mw_values["Light Chain"],
                "Heavy Chain MW (kDa)": mw_values["Heavy Chain"],
                "HMW MW (kDa)": mw_values["HMW"],
                # Add peak times
                "LMW Time": peak_times["LMW"],
                "Light Chain Time": peak_times["Light Chain"],
                "Heavy Chain Time": peak_times["Heavy Chain"],
                "HMW Time": peak_times["HMW"],
            })

    fig.update_layout(
        height=300 * num_rows,
        title=title,
        showlegend=False,
        template="plotly_white",
        margin=dict(t=40, b=40, l=40, r=30)
    )
    return fig, table_output


@app.callback(
    [Output("reduced-chromatogram", "figure"),
     Output("reduced-chromatogram", "config"),
     Output("reduced-table", "data"),
     Output("reduced-table", "columns")],

    [
        Input("reduced-result-ids", "data"),
        Input("marker-rt", "value"),
        Input("marker-label", "value"),
        Input("skip-time", "value"),
        Input("max-peaks", "value"),
        Input("prominence-threshold", "value"),
        Input("valley-search-window", "value"),
        Input("valley-drop-ratio", "value"),
        Input("smoothing-window", "value"),
        Input("smoothing-polyorder", "value"),
        Input("light-chain-time", "value"),
        Input("standard-regression-params", "data"),
        Input("reduced-y-axis-scaling", "value"),
        Input("reduced-subplot-vertical-spacing", "value"),
        Input("reduced-show-mw-checklist", "value"),
        Input("main-tabs", "value"),
        Input("selected-report", "data"),

    ]
)
def reduced_callback(result_ids, marker_rt, marker_label, skip_time, max_peaks,
                     prominence_threshold, valley_search_window, valley_drop_ratio,
                     smoothing_window, smoothing_polyorder, light_chain_time,
                     regression_params, y_scale, subplot_vertical_spacing, show_mw_checklist, active_tab, selected_report):
    # if active_tab != "tab-reduced":
    #     raise PreventUpdate
    metas = CESDSMetadata.objects.filter(id__in=result_ids)
    result_df_by_id = {}

    for m in metas:
        qs = CESDSTimeSeries.objects.filter(metadata_id=m.id).values("time_min", "channel_1")
        df = pd.DataFrame(list(qs))

        if df.empty or "time_min" not in df.columns or "channel_1" not in df.columns:
            continue

        result_df_by_id[str(m.id)] = {
            "sample_id": m.sample_id_full,
            "data": df.sort_values("time_min")
        }

    # ✅ Handle the empty case after building the dict
    if not result_df_by_id:
        return go.Figure(), {}, [], []

    # ✅ Initialize table_output as empty list
    table_output = []

    slope = regression_params.get("slope") if regression_params else None
    intercept = regression_params.get("intercept") if regression_params else None
    show_mw = 'show_mw' in show_mw_checklist

    fig, table_data = generate_chromatogram_figure_advanced(
        result_df_by_id,
        title="Reduced Chromatograms with Peak Classification",
        marker_rt=marker_rt,
        marker_label=marker_label,
        skip_time=skip_time,
        max_peaks=max_peaks,
        prominence_threshold=prominence_threshold,
        valley_search_window=valley_search_window,
        valley_drop_ratio=valley_drop_ratio,
        smoothing_window=smoothing_window,
        smoothing_polyorder=smoothing_polyorder,
        light_chain_time=light_chain_time,
        table_output=table_output,
        regression_slope=slope,
        regression_intercept=intercept,
        y_scale=y_scale,
        subplot_vertical_spacing=subplot_vertical_spacing,
        show_mw_in_annotations=show_mw
    )
    print(f'table output: {table_output}')

    columns = [{"name": k, "id": k} for k in table_data[0].keys()] if table_data else []

    report_name = CESDSReport.objects.filter(
        id=selected_report).first().report_name if selected_report else "CESDS_Report"
    plot_config = {
        'toImageButtonOptions': {
            'filename': f"{datetime.now().strftime('%Y%m%d')}-R-{report_name}",
            'format': 'png',
            # 'height': 600,
            # 'width': 800,
            # 'scale': 2
        }}
    return fig, plot_config, table_data, columns


@app.callback(
    Output("download-reduced-xlsx", "data"),
    Input("export-reduced-btn", "n_clicks"),
    State("reduced-table", "data"),
    State("selected-report", "data"),
    prevent_initial_call=True
)
def export_nonreduced_table(n_clicks, table_data, selected_report):
    report_name = CESDSReport.objects.filter(id=selected_report).first().report_name if selected_report else "CESDS_Report"
    filename = f"{report_name}_Reduced.xlsx"
    df = pd.DataFrame(table_data)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, startrow=1)
        worksheet = writer.sheets["Sheet1"]
        worksheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(df.columns))
        worksheet.cell(row=1, column=1).value = "Reduced Results"

    buffer.seek(0)

    def write_buffer(out_io):
        out_io.write(buffer.getvalue())

    return dcc.send_bytes(write_buffer, filename)


def generate_chromatogram_figure_nonreduced(
        result_df_by_id,
        title="Non-Reduced Chromatograms",
        marker_rt=None,
        marker_label="10 kDa",
        skip_time=0.3,
        max_peaks=4,
        prominence_threshold=0.05,
        valley_search_window=3.0,
        valley_drop_ratio=0.2,
        smoothing_window=11,
        smoothing_polyorder=3,
        intact_time=None,
        table_output=None,
        regression_slope=None,
        regression_intercept=None,
        y_scale=1,
        subplot_vertical_spacing=0.25,
        reduced_table_data=None,
        show_mw_in_annotations=True,
):
    if not result_df_by_id:
        return go.Figure(), []

    # Create a lookup dictionary for reduced peak times
    reduced_peak_times = {}
    if reduced_table_data:
        for row in reduced_table_data:
            sample_name = row.get("Sample Name", "")
            # Remove R prefix and store
            clean_name = sample_name.replace("R ", "").strip()
            if clean_name.startswith("R"):
                clean_name = clean_name[1:].strip()

            reduced_peak_times[clean_name] = {
                "lc_time": row.get("Light Chain Time"),
                "hc_time": row.get("Heavy Chain Time")
            }
            print(
                f"Stored reduced times for {clean_name}: LC={row.get('Light Chain Time')}, HC={row.get('Heavy Chain Time')}")

    num_rows = len(result_df_by_id)
    fig = make_subplots(
        rows=num_rows, cols=1,
        shared_xaxes=False,
        vertical_spacing=subplot_vertical_spacing,
        subplot_titles=[meta["sample_id"] for meta in result_df_by_id.values()]
    )

    for i, (mid, meta) in enumerate(result_df_by_id.items(), start=1):
        df = meta["data"]
        if df.empty:
            continue

        # Get the corresponding reduced peak times for this sample
        sample_name = meta["sample_id"]
        clean_name = sample_name.replace("NR ", "").strip()
        if clean_name.startswith("NR"):
            clean_name = clean_name[2:].strip()

        # Get LC/HC times from reduced data
        lc_time = None
        hc_time = None
        if clean_name in reduced_peak_times:
            lc_time = reduced_peak_times[clean_name]["lc_time"]
            hc_time = reduced_peak_times[clean_name]["hc_time"]
            print(f"Found reduced times for {sample_name} (clean: {clean_name}): LC={lc_time}, HC={hc_time}")

        fig.add_trace(
            go.Scatter(x=df["time_min"], y=df["channel_1"], mode="lines", name=meta["sample_id"]),
            row=i, col=1
        )

        marker_peak_time = None
        if marker_rt is not None:
            df_marker = df[(df["time_min"] >= marker_rt - 0.5) & (df["time_min"] <= marker_rt + 0.5)]
            if not df_marker.empty:
                idx = df_marker["channel_1"].idxmax()
                marker_peak_time = df_marker.loc[idx, "time_min"]
                peak_height = df_marker.loc[idx, "channel_1"]

                fig.add_annotation(
                    x=marker_peak_time,
                    y=peak_height,
                    text=f"{marker_label} ({marker_peak_time:.2f} min)",
                    showarrow=True,
                    arrowhead=1,
                    ax=0,
                    ay=-40,
                    row=i, col=1
                )

        df_after_marker = df[df["time_min"] > (marker_peak_time or 0) + skip_time].copy()
        peaks, _ = detect_valley_to_valley_peaks(
            df_after_marker,
            signal_col="channel_1",
            time_col="time_min",
            max_peaks=max_peaks,
            prominence_threshold=prominence_threshold,
            valley_search_window=valley_search_window,
            valley_drop_ratio=valley_drop_ratio,
            smoothing_window=smoothing_window,
            smoothing_polyorder=smoothing_polyorder,
        )

        peaks = sorted(peaks, key=lambda x: x["peak_time"])
        intact = None
        if intact_time:
            closest = min(peaks, key=lambda p: abs(p["peak_time"] - intact_time))
            intact = closest
        elif peaks:
            intact = max(peaks, key=lambda p: p["peak_height"])

        classified_peaks = []
        peak_times = {"LMW": None, "Light Chain": None, "Heavy Chain": None,"Intact": None, "HMW": None}
        time_tolerance = 2.5  # ±30 seconds tolerance

        # First pass: identify intact peak
        for p in peaks:
            if intact and abs(p["peak_time"] - intact["peak_time"]) < 0.1:
                classified_peaks.append((p, "Intact"))
                peak_times["Intact"] = p["peak_time"]
                break

        # Second pass: classify other peaks based on intact position and reduced times
        for p in peaks:
            if intact and abs(p["peak_time"] - intact["peak_time"]) < 0.1:
                continue  # Already classified as intact

            class_label = None

            if intact and p["peak_time"] > intact["peak_time"]:
                class_label = "HMW"
            elif intact and p["peak_time"] < intact["peak_time"]:
                # Check if it matches LC or HC time from reduced
                if lc_time and abs(p["peak_time"] - lc_time) <= time_tolerance:
                    class_label = "Light Chain"
                elif hc_time and abs(p["peak_time"] - hc_time) <= time_tolerance:
                    class_label = "Heavy Chain"
                else:
                    class_label = "LMW"

            if class_label:
                classified_peaks.append((p, class_label))
                peak_times[class_label] = p["peak_time"]

        total_area = sum(p["area"] for p, _ in classified_peaks)
        percentages = {"LMW": 0.0, "Light Chain": 0.0,"Heavy Chain": 0.0, "Intact": 0.0, "HMW": 0.0}

        max_signal = df["channel_1"].max()
        if not y_scale or y_scale == 1:
            fig.update_yaxes(title_text="UV", row=i, col=1)
        else:
            y_max = max_signal * y_scale
            fig.update_yaxes(
                title_text="UV",
                autorange=True,
                autorangeoptions=dict(maxallowed=y_max),
                row=i, col=1
            )

        fig.update_xaxes(title_text="Time (min)", row=i, col=1)

        # Store MW calculations for each peak class
        mw_values = {"LMW": None, "Light Chain": None, "Intact": None, "HMW": None}

        for p, class_label in classified_peaks:
            pct = (p["area"] / total_area * 100) if total_area else 0
            percentages[class_label] += pct
            label = f"{class_label}<br>({pct:.1f}%)"

            # Calculate MW and store it
            if regression_slope is not None and regression_intercept is not None:
                log_mw = regression_slope * p["peak_time"] + regression_intercept
                mw_kda = np.exp(log_mw)
                
                # Only add MW to label if show_mw_in_annotations is True
                if show_mw_in_annotations:
                    label += f"<br>{mw_kda:.1f} kDa"

                # Store the MW for this peak class
                mw_values[class_label] = round(mw_kda, 1)

            peak_height = p["peak_height"]
            if y_scale and y_scale != 1:
                peak_height = min(peak_height, y_max)

            shade_peak(
                fig, df,
                start_time=p["start_time"],
                end_time=p["end_time"],
                baseline=p["baseline"][0],
                row=i, col=1,
                label=label,
                peak_time=p["peak_time"],
                peak_height=peak_height,
                class_label=class_label
            )

        total_pct = sum(percentages.values())
        if abs(total_pct - 100) > 1e-2:
            print(f"[DEBUG] {meta['sample_id']} percentages do not sum to 100%: {total_pct:.2f}%")

        # UPDATED: Add MW columns and peak times to table output
        if table_output is not None:
            table_output.append({
                "Sample Name": meta["sample_id"],
                "LMW (%)": round(percentages["LMW"], 1),
                "Light Chain (%)": round(percentages["Light Chain"], 1),
                "Intact (%)": round(percentages["Intact"], 1),
                "HMW (%)": round(percentages["HMW"], 1),
                # Add MW columns
                "LMW MW (kDa)": mw_values["LMW"],
                "Light Chain MW (kDa)": mw_values["Light Chain"],
                "Intact MW (kDa)": mw_values["Intact"],
                "HMW MW (kDa)": mw_values["HMW"],
                # Add peak times
                "LMW Time": peak_times["LMW"],
                "Light Chain Time": peak_times["Light Chain"],
                "Intact Time": peak_times["Intact"],
                "HMW Time": peak_times["HMW"],
            })

    fig.update_layout(
        height=300 * num_rows,
        title=title,
        showlegend=False,
        template="plotly_white",
        margin=dict(t=40, b=40, l=40, r=30)
    )

    return fig, table_output

@app.callback(
    [
        Output("nonreduced-chromatogram", "figure"),
        Output("nonreduced-chromatogram", "config"),
        Output("nonreduced-table", "data"),
        Output("nonreduced-table", "columns")
    ],
    [
        Input("nonreduced-result-ids", "data"),
        Input("nr-marker-rt", "value"),
        Input("nr-marker-label", "value"),
        Input("nr-skip-time", "value"),
        Input("nr-max-peaks", "value"),
        Input("nr-prominence-threshold", "value"),
        Input("nr-valley-search-window", "value"),
        Input("nr-valley-drop-ratio", "value"),
        Input("nr-smoothing-window", "value"),
        Input("nr-smoothing-polyorder", "value"),
        Input("nr-intact-time", "value"),
        Input("standard-regression-params", "data"),
        Input("non-reduced-y-axis-scaling", "value"),
        Input("non-reduced-subplot-vertical-spacing", "value"),
        Input("nonreduced-show-mw-checklist", "value"),
        Input("main-tabs", "value"),
        Input("selected-report", "data"),
        Input("reduced-table", "data"),
    ]
)
def nonreduced_callback(result_ids, marker_rt, marker_label, skip_time, max_peaks,
                        prominence_threshold, valley_search_window, valley_drop_ratio,
                        smoothing_window, smoothing_polyorder, intact_time, regression_params, y_scale,
                        subplot_vertical_spacing, show_mw_checklist, active_tab, selected_report, reduced_table_data):
    # if active_tab != "tab-nonreduced":
    #     raise PreventUpdate
    metas = CESDSMetadata.objects.filter(id__in=result_ids)
    result_df_by_id = {}

    for m in metas:
        qs = CESDSTimeSeries.objects.filter(metadata_id=m.id).values("time_min", "channel_1")
        df = pd.DataFrame(list(qs))

        if df.empty or "time_min" not in df.columns or "channel_1" not in df.columns:
            continue

        result_df_by_id[str(m.id)] = {
            "sample_id": m.sample_id_full,
            "data": df.sort_values("time_min")
        }

    # ✅ Handle the empty case after building the dict
    if not result_df_by_id:
        return go.Figure(), {}, [], []

    table_output = []
    slope = regression_params.get("slope") if regression_params else None
    intercept = regression_params.get("intercept") if regression_params else None
    show_mw = 'show_mw' in show_mw_checklist

    fig, table_data = generate_chromatogram_figure_nonreduced(
        result_df_by_id,
        title="Non-Reduced Chromatograms with Peak Classification",
        marker_rt=marker_rt,
        marker_label=marker_label,
        skip_time=skip_time,
        max_peaks=max_peaks,
        prominence_threshold=prominence_threshold,
        valley_search_window=valley_search_window,
        valley_drop_ratio=valley_drop_ratio,
        smoothing_window=smoothing_window,
        smoothing_polyorder=smoothing_polyorder,
        intact_time=intact_time,
        table_output=table_output,
        regression_slope=slope,
        regression_intercept=intercept,
        y_scale=y_scale,
        subplot_vertical_spacing=subplot_vertical_spacing,
        reduced_table_data=reduced_table_data,
        show_mw_in_annotations=show_mw
    )

    columns = [{"name": k, "id": k} for k in table_data[0].keys()] if table_data else []

    print(f'table output: {table_output}')

    report_name = CESDSReport.objects.filter(
        id=selected_report).first().report_name if selected_report else "CESDS_Report"

    plot_config = {
        'toImageButtonOptions': {
            'filename': f"{datetime.now().strftime('%Y%m%d')}-NR-{report_name}",
            'format': 'png',
            # 'height': 600,
            # 'width': 800,
            # 'scale': 2
        }}

    return fig, plot_config, table_data, columns


@app.callback(
    Output("download-nonreduced-xlsx", "data"),
    Input("export-nonreduced-btn", "n_clicks"),
    State("nonreduced-table", "data"),
    State("selected-report", "data"),
    prevent_initial_call=True
)
def export_nonreduced_table(n_clicks, table_data, selected_report):
    report_name = CESDSReport.objects.filter(
        id=selected_report).first().report_name if selected_report else "CESDS_Report"
    filename = f"{report_name}_NonReduced.xlsx"
    df = pd.DataFrame(table_data)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, startrow=1)
        worksheet = writer.sheets["Sheet1"]
        worksheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(df.columns))
        worksheet.cell(row=1, column=1).value = "Non-Reduced Results"

    buffer.seek(0)

    def write_buffer(out_io):
        out_io.write(buffer.getvalue())

    return dcc.send_bytes(write_buffer, filename)


# Standard Analysis Logic
@app.callback(
    Output("standard-id-dropdown", "options"),
    Input("selected-result-ids", "data")
)
def get_std_dropdown_options(result_ids):
    if not result_ids:
        return []

    stds = CESDSMetadata.objects.filter(
        id__in=result_ids,
        sample_id_full__iregex=r".*STD.*"
    )

    return [{"label": s.sample_id_full, "value": s.id} for s in stds]


@app.callback(
    Output("standard-id-dropdown", "value"),
    Input("standard-id-dropdown", "options")
)
def auto_select_first_std(options):
    if options:
        return options[0]["value"]
    return None


@app.callback(
    [
        Output("standard-peak-plot", "figure"),
        Output("std-detected-peak-table", "data")
    ],
    [
        Input("standard-id-dropdown", "value"),
        State("num-std-peaks", "value")
    ]
)
def plot_std_chromatogram_and_generate_table(metadata_id, num_to_keep):
    if not metadata_id:
        return go.Figure(), []

    qs = CESDSTimeSeries.objects.filter(metadata_id=metadata_id).values("time_min", "channel_1")
    df = pd.DataFrame(list(qs)).sort_values("time_min")
    if df.empty:
        return go.Figure(), []

    # Plot full chromatogram
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["time_min"],
        y=df["channel_1"],
        mode="lines",
        name="STD Chromatogram"
    ))

    # Filter to >5 min for peak detection
    df_filtered = df[df["time_min"] > 5.0]
    if df_filtered.empty:
        return fig, []

    x = df_filtered["time_min"].values
    y = df_filtered["channel_1"].values
    peak_indices, _ = find_peaks(y, distance=5)
    all_peaks = [{"peak_rt": x[i], "peak_height": y[i]} for i in peak_indices]

    # Step 1: Take top N peaks by height
    top_peaks = sorted(all_peaks, key=lambda p: p["peak_height"], reverse=True)[:num_to_keep or 7]

    # Step 2: Sort selected peaks by RT (ascending)
    sorted_peaks = sorted(top_peaks, key=lambda p: p["peak_rt"])

    # Step 3: Assign MWs linearly (left = 10 kDa, right = 250 kDa)
    default_mws = [10, 20, 35, 50, 100, 150, 250]
    assigned_mws = default_mws[:len(sorted_peaks)]

    table_data = []
    for i, peak in enumerate(sorted_peaks):
        table_data.append({
            "peak_rt": round(peak["peak_rt"], 3),
            "peak_height": round(peak["peak_height"], 3),
            "assigned_mw": assigned_mws[i] if i < len(assigned_mws) else ""
        })

    # Add peak markers to plot
    fig.add_trace(go.Scatter(
        x=[p["peak_rt"] for p in sorted_peaks],
        y=[p["peak_height"] for p in sorted_peaks],
        mode="markers+text",
        text=[f"{i + 1}" for i in range(len(sorted_peaks))],
        textposition="top center",
        marker=dict(color="red", size=8),
        name="Top Peaks"
    ))

    fig.update_layout(
        title="Standard Chromatogram with Assigned Peaks",
        xaxis_title="Time (min)",
        yaxis_title="UV (Channel 1)",
        template="plotly_white"
    )

    return fig, table_data


@app.callback(
    [
        Output("regression-equation", "children"),
        Output("r-squared-value", "children"),
        Output("regression-plot", "figure"),
        Output("estimated-mw", "children"),
        Output("standard-regression-params", "data")
    ],
    [
        Input("std-detected-peak-table", "data"),
        Input("std-detected-peak-table", "selected_rows"),
        Input("rt-input", "value")
    ]
)
def run_linear_mw_regression(table_data, selected_rows, rt_input):
    if not table_data or not selected_rows:
        return "No selected points", "N/A", go.Figure(), "N/A", {}

    df = pd.DataFrame(table_data)
    df = df.iloc[selected_rows]  # Only keep selected rows
    df = df.dropna(subset=["peak_rt", "assigned_mw"])
    df = df[df["assigned_mw"] > 0]

    if df.shape[0] < 2:
        return "Select ≥2 points", "N/A", go.Figure(), "N/A", {}

    try:
        x = df["peak_rt"]
        y = np.log(df["assigned_mw"])
        slope, intercept, r_value, _, _ = linregress(x, y)

        # Generate regression line
        x_vals = np.linspace(x.min(), x.max(), 100)
        y_vals = slope * x_vals + intercept

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x,
            y=np.log(df["assigned_mw"]),  # y = log(MW)
            mode="markers+text",
            text=[f"{mw:.0f} kDa" for mw in df["assigned_mw"]],  # ✅ correct label from original MWs
            textposition="top center",
            name="Selected Points"
        ))
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines",
            name="Regression Line"
        ))
        fig.update_layout(
            title="Log MW vs Retention Time",
            xaxis_title="Retention Time (min)",
            yaxis_title="Log MW (kDa)",
            template="plotly_white"
        )

        estimated_mw = "N/A"
        if rt_input is not None:
            log_mw = slope * rt_input + intercept
            estimated_mw = f"{np.exp(log_mw) / 1000:.2f} kD"

        return (
            f"MW = {slope:.3f} × RT + {intercept:.3f}",
            f"R² = {r_value ** 2:.4f}",
            fig,
            estimated_mw,
            {"slope": slope, "intercept": intercept}
        )

    except Exception as e:
        return f"Error: {e}", "N/A", go.Figure(), "N/A", {}


@app.callback(
    Output("std-detected-peak-table", "selected_rows"),
    Input("std-detected-peak-table", "data")
)
def auto_select_all_std_peaks(data):
    return list(range(len(data))) if data else []


@app.callback(
    [Output("status-message", "children", allow_duplicate=True),
     Output("status-message", "style", allow_duplicate=True),
     Output("button-success-trigger", "data"),
     Output("button-reset-interval", "disabled")],
    [Input("report-results-btn", "n_clicks")],
    [State("reduced-table", "data"),
     State("nonreduced-table", "data"),
     State("selected-report", "data"),
     State("button-success-trigger", "data"),
     State("standard-regression-params", "data")],  # ADD: Get regression parameters
    prevent_initial_call=True
)
def save_to_lims(n_clicks, reduced_data, nonreduced_data, selected_report, current_trigger, regression_params):
    print('=' * 50)
    print('SAVE TO LIMS CALLBACK TRIGGERED')
    print(f'n_clicks: {n_clicks}')
    print(f'selected_report: {selected_report}')
    print(f'reduced_data length: {len(reduced_data) if reduced_data else 0}')
    print(f'nonreduced_data length: {len(nonreduced_data) if nonreduced_data else 0}')
    print(f'regression_params: {regression_params}')
    print('=' * 50)

    if (not reduced_data and not nonreduced_data) or not selected_report:
        print('No data or report name - returning early')
        return "⚠️ No data to link!", {
            "display": "block",
            "backgroundColor": "#f8d7da",
            "color": "#721c24",
            "border": "1px solid #f5c6cb",
            "padding": "10px 20px",
            "margin": "10px 20px",
            "borderRadius": "5px"
        }, current_trigger, True

    try:
        # Get report info
        print(f'Looking for report with name: {selected_report}')
        report = CESDSReport.objects.filter(id=selected_report).first()
        if report:
            project_id = report.project_id
            print(f'Found report - project_id: {project_id}')
        else:
            project_id = "Unknown"
            print('Report not found - using Unknown project_id')

        saved_count = 0
        errors = []
        skipped_controls = []

        # Dictionary to combine reduced and non-reduced data by sample ID
        combined_samples = {}

        # Process reduced samples WITH MW DATA
        if reduced_data:
            print(f'\nProcessing {len(reduced_data)} reduced samples...')
            for idx, row in enumerate(reduced_data):
                print(f'\nReduced Row {idx}: {row}')
                sample_name = row.get("Sample Name", "")
                print(f'Sample name: "{sample_name}"')

                # Skip control samples
                if any(control in sample_name.upper() for control in ['BLK', 'IGG', 'STD', 'BLANK', 'CONTROL']):
                    print(f'Skipping control sample: {sample_name}')
                    skipped_controls.append(sample_name)
                    continue

                # Remove R prefix if present
                clean_sample_name = sample_name
                if sample_name.startswith('R '):
                    clean_sample_name = sample_name[2:].strip()
                elif sample_name.startswith('R'):
                    clean_sample_name = sample_name[1:].strip()
                print(f'Clean sample name: "{clean_sample_name}"')

                try:
                    # Get percentage values
                    lmw = row.get("LMW (%)", 0)
                    hmw = row.get("HMW (%)", 0)
                    light_chain = row.get("Light Chain (%)", 0)
                    heavy_chain = row.get("Heavy Chain (%)", 0)

                    # NEW: Get MW values
                    lmw_mw = row.get("LMW MW (kDa)", None)
                    lc_mw = row.get("Light Chain MW (kDa)", None)
                    hc_mw = row.get("Heavy Chain MW (kDa)", None)
                    hmw_mw = row.get("HMW MW (kDa)", None)

                    print(f'Raw values - LMW: {lmw}, HMW: {hmw}, LC: {light_chain}, HC: {heavy_chain}')
                    print(f'MW values - LMW MW: {lmw_mw}, LC MW: {lc_mw}, HC MW: {hc_mw}, HMW MW: {hmw_mw}')

                    # Convert to float, handling None and empty strings
                    lmw = float(lmw) if lmw not in [None, '', 'None'] else 0
                    hmw = float(hmw) if hmw not in [None, '', 'None'] else 0
                    light_chain = float(light_chain) if light_chain not in [None, '', 'None'] else 0
                    heavy_chain = float(heavy_chain) if heavy_chain not in [None, '', 'None'] else 0

                    # Convert MW values
                    lmw_mw = float(lmw_mw) if lmw_mw not in [None, '', 'None'] else None
                    lc_mw = float(lc_mw) if lc_mw not in [None, '', 'None'] else None
                    hc_mw = float(hc_mw) if hc_mw not in [None, '', 'None'] else None
                    hmw_mw = float(hmw_mw) if hmw_mw not in [None, '', 'None'] else None

                    # Initialize sample entry if not exists
                    if clean_sample_name not in combined_samples:
                        combined_samples[clean_sample_name] = {
                            'original_names': [],
                            'methods': {},
                            'purity': None
                        }

                    # UPDATED: Add reduced method data WITH MW
                    combined_samples[clean_sample_name]['original_names'].append(sample_name)
                    combined_samples[clean_sample_name]['methods']['reduced'] = {
                        "peaks": {
                            "LMW": {
                                "value": lmw,
                                "unit": "%",
                                "molecular_weight": lmw_mw
                            },
                            "Light Chain": {
                                "value": light_chain,
                                "unit": "%",
                                "molecular_weight": lc_mw
                            },
                            "Heavy Chain": {
                                "value": heavy_chain,
                                "unit": "%",
                                "molecular_weight": hc_mw
                            },
                            "HMW": {
                                "value": hmw,
                                "unit": "%",
                                "molecular_weight": hmw_mw
                            }
                        },
                        "total_peaks": 4
                    }

                    # Calculate purity for reduced (main chain components)
                    purity = 100 - lmw - hmw
                    combined_samples[clean_sample_name]['purity'] = purity
                    print(f'Calculated purity: {purity}')

                except Exception as e:
                    print(f'ERROR processing reduced sample {sample_name}: {str(e)}')
                    import traceback
                    traceback.print_exc()
                    errors.append(f"{sample_name} (reduced): {str(e)}")

        # Process non-reduced samples WITH MW DATA
        if nonreduced_data:
            print(f'\nProcessing {len(nonreduced_data)} non-reduced samples...')
            for idx, row in enumerate(nonreduced_data):
                print(f'\nNon-reduced Row {idx}: {row}')
                sample_name = row.get("Sample Name", "")
                print(f'Sample name: "{sample_name}"')

                # Skip control samples
                if any(control in sample_name.upper() for control in ['BLK', 'IGG', 'STD', 'BLANK', 'CONTROL']):
                    print(f'Skipping control sample: {sample_name}')
                    skipped_controls.append(sample_name)
                    continue

                # Remove NR prefix if present
                clean_sample_name = sample_name
                if sample_name.startswith('NR '):
                    clean_sample_name = sample_name[3:].strip()
                elif sample_name.startswith('NR'):
                    clean_sample_name = sample_name[2:].strip()
                print(f'Clean sample name: "{clean_sample_name}"')

                try:
                    # Get percentage values
                    lmw = row.get("LMW (%)", 0)
                    hmw = row.get("HMW (%)", 0)
                    light_chain = row.get("Light Chain (%)", 0)
                    intact = row.get("Intact (%)", 0)

                    # NEW: Get MW values
                    lmw_mw = row.get("LMW MW (kDa)", None)
                    lc_mw = row.get("Light Chain MW (kDa)", None)
                    intact_mw = row.get("Intact MW (kDa)", None)  # KEY VALUE for display
                    hmw_mw = row.get("HMW MW (kDa)", None)

                    print(f'Raw values - LMW: {lmw}, HMW: {hmw}, LC: {light_chain}, Intact: {intact}')
                    print(f'MW values - LMW MW: {lmw_mw}, LC MW: {lc_mw}, Intact MW: {intact_mw}, HMW MW: {hmw_mw}')

                    # Convert percentage values to float
                    lmw = float(lmw) if lmw not in [None, '', 'None'] else 0
                    hmw = float(hmw) if hmw not in [None, '', 'None'] else 0
                    light_chain = float(light_chain) if light_chain not in [None, '', 'None'] else 0
                    intact = float(intact) if intact not in [None, '', 'None'] else 0

                    # Convert MW values
                    lmw_mw = float(lmw_mw) if lmw_mw not in [None, '', 'None'] else None
                    lc_mw = float(lc_mw) if lc_mw not in [None, '', 'None'] else None
                    intact_mw = float(intact_mw) if intact_mw not in [None, '', 'None'] else None
                    hmw_mw = float(hmw_mw) if hmw_mw not in [None, '', 'None'] else None

                    # Initialize sample entry if not exists
                    if clean_sample_name not in combined_samples:
                        combined_samples[clean_sample_name] = {
                            'original_names': [],
                            'methods': {},
                            'purity': None
                        }

                    # UPDATED: Add non-reduced method data WITH MW
                    combined_samples[clean_sample_name]['original_names'].append(sample_name)
                    combined_samples[clean_sample_name]['methods']['non_reduced'] = {
                        "peaks": {
                            "LMW": {
                                "value": lmw,
                                "unit": "%",
                                "molecular_weight": lmw_mw
                            },
                            "Light Chain": {
                                "value": light_chain,
                                "unit": "%",
                                "molecular_weight": lc_mw
                            },
                            "Intact": {
                                "value": intact,
                                "unit": "%",
                                "molecular_weight": intact_mw  # KEY: Intact MW for display
                            },
                            "HMW": {
                                "value": hmw,
                                "unit": "%",
                                "molecular_weight": hmw_mw
                            }
                        },
                        "total_peaks": 4
                    }

                    # Calculate purity for non-reduced if not already set
                    if combined_samples[clean_sample_name]['purity'] is None:
                        purity = 100 - lmw - hmw
                        combined_samples[clean_sample_name]['purity'] = purity
                        print(f'Calculated purity: {purity}')

                except Exception as e:
                    print(f'ERROR processing non-reduced sample {sample_name}: {str(e)}')
                    import traceback
                    traceback.print_exc()
                    errors.append(f"{sample_name} (non-reduced): {str(e)}")

        # Now save the combined data to LIMS
        print(f'\n=== SAVING COMBINED DATA ===')
        print(f'Total unique samples to save: {len(combined_samples)}')

        for clean_sample_name, sample_data in combined_samples.items():
            try:
                print(f'\nProcessing combined sample: {clean_sample_name}')
                print(f'Original names: {sample_data["original_names"]}')
                print(f'Methods available: {list(sample_data["methods"].keys())}')

                # UPDATED: Create comprehensive band pattern with MW data and regression info
                band_pattern = {
                    "methods": sample_data['methods'],
                    "original_names": sample_data['original_names'],
                    "analysis_date": datetime.now().isoformat(),
                    "instrument": "CE-SDS",
                    "total_methods": len(sample_data['methods']),
                    "regression_parameters": regression_params if regression_params else None
                    # NEW: Add regression params
                }

                print(f'Combined band pattern: {band_pattern}')

                # Create or update LIMS records
                print(f'Creating/updating LimsSampleAnalysis for sample_id: {clean_sample_name}')
                lims_sample, created = LimsSampleAnalysis.objects.update_or_create(
                    sample_id=clean_sample_name,
                    defaults={
                        'sample_type': 2,  # FB samples
                        'project_id': project_id,
                        'analyst': report.user_id if report else 'Unknown',
                        'sample_date': datetime.now().date(),
                        'description': f'CE-SDS analysis from report {selected_report}'
                    }
                )
                print(f'LimsSampleAnalysis {"created" if created else "updated"}: {lims_sample.sample_id}')

                # Determine notes based on available methods
                method_list = list(sample_data['methods'].keys())
                if len(method_list) == 2:
                    notes = 'CE-SDS analysis (both reduced and non-reduced)'
                elif 'reduced' in method_list:
                    notes = 'CE-SDS analysis (reduced only)'
                else:
                    notes = 'CE-SDS analysis (non-reduced only)'

                print(f'Creating/updating LimsCeSdsResult...')

                # Get or create the CESDSReport (assuming it should exist)
                try:
                    cesds_report = CESDSReport.objects.get(id=selected_report)
                    print(f'Found CESDSReport: {cesds_report.report_name}')
                except CESDSReport.DoesNotExist:
                    print(f'CESDSReport with ID {selected_report} not found')
                    cesds_report = None

                cesds_result, created = LimsCeSdsResult.objects.update_or_create(
                    sample_id=lims_sample,
                    defaults={
                        'purity': sample_data['purity'],
                        'band_pattern': band_pattern,
                        'notes': notes,
                        'status': 'completed',
                        'report': cesds_report  # Use the CESDSReport object, not the ID
                    }
                )
                print(f'LimsCeSdsResult {"created" if created else "updated"}')

                # Update the OneToOne relationship in LimsSampleAnalysis
                lims_sample.ce_sds_result = cesds_result
                lims_sample.save()
                print(f'Updated LimsSampleAnalysis with ce_sds_result relationship')

                saved_count += 1
                print(f'Successfully saved combined sample {clean_sample_name}')

            except Exception as e:
                print(f'ERROR processing combined sample {clean_sample_name}: {str(e)}')
                import traceback
                traceback.print_exc()
                errors.append(f"{clean_sample_name}: {str(e)}")

        # ... rest of the function remains the same (summary, status messages, etc.)
        print(f'\n=== SUMMARY ===')
        print(f'Total saved: {saved_count}')
        print(f'Skipped controls: {len(skipped_controls)} - {skipped_controls}')
        print(f'Errors: {len(errors)} - {errors}')

        # Prepare status message
        message_parts = []
        if saved_count > 0:
            message_parts.append(f"✅ Linked {saved_count} CE-SDS results to LIMS")
        if skipped_controls:
            message_parts.append(f"⚠️ Skipped {len(skipped_controls)} control samples: {', '.join(skipped_controls)}")
        if errors:
            error_msg = f"❌ Errors: {'; '.join(errors[:3])}"
            if len(errors) > 3:
                error_msg += f" and {len(errors) - 3} more..."
            message_parts.append(error_msg)

        message = " | ".join(message_parts) if message_parts else "No samples processed"

        # Determine style based on results
        if errors and not saved_count:
            style = {
                "display": "block",
                "backgroundColor": "#f8d7da",
                "color": "#721c24",
                "border": "1px solid #f5c6cb",
                "padding": "10px 20px",
                "margin": "10px 20px",
                "borderRadius": "5px"
            }
        elif errors or skipped_controls:
            style = {
                "display": "block",
                "backgroundColor": "#fff3cd",
                "color": "#856404",
                "border": "1px solid #ffeeba",
                "padding": "10px 20px",
                "margin": "10px 20px",
                "borderRadius": "5px"
            }
        else:
            style = {
                "display": "block",
                "backgroundColor": "#d4edda",
                "color": "#155724",
                "border": "1px solid #c3e6cb",
                "padding": "10px 20px",
                "margin": "10px 20px",
                "borderRadius": "5px"
            }

        return message, style, current_trigger + 1, False

    except Exception as e:
        print(f'MAIN EXCEPTION: {str(e)}')
        import traceback
        traceback.print_exc()
        return f"❌ Error linking to LIMS: {str(e)}", {
            "display": "block",
            "backgroundColor": "#f8d7da",
            "color": "#721c24",
            "border": "1px solid #f5c6cb",
            "padding": "10px 20px",
            "margin": "10px 20px",
            "borderRadius": "5px"
        }, current_trigger, True
