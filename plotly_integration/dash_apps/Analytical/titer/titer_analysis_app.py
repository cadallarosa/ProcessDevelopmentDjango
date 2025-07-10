import plotly.graph_objects as go
from plotly.subplots import make_subplots
from django_plotly_dash import DjangoDash
import dash
from dash import dcc, html, Input, Output, State, dash_table, Dash, MATCH
import pandas as pd
from scipy.stats import linregress, t
from plotly_integration.models import Report, SampleMetadata, PeakResults, TimeSeriesData, LimsTiterResult, \
    LimsSampleAnalysis
import json
import logging
from openpyxl.workbook import Workbook
from collections import Counter
from django.db.models import F, ExpressionWrapper, fields
from datetime import datetime, timedelta
import re
import numpy as np
from collections import Counter
from collections import defaultdict
from datetime import timedelta

# Logging Configuration
logging.basicConfig(filename='app_logs.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the Dash app
app = DjangoDash('TiterAnalysisApp')

# Layout for the Dash app
app.layout = html.Div([

    dcc.Store(id='selected-report', data=None),
    dcc.Store(id='selected-report-2', data=None),
    dcc.Store(id="std-result-id-store"),
    dcc.Store(id='regression-parameters', data={"slope": 0,
                                                "intercept": 0,
                                                "std_err": 0,
                                                "t_score": 0,
                                                "n": 0,
                                                "mean_x": 0,
                                                "sum_x_sq": 0
                                                }),
    dcc.Store(id='result-table-store', data=[]),
    dcc.Store(id='report-list-store', data=[]),
    dcc.Store(id='current-plot-settings', data={}),
    dcc.Store(id='settings-collapsed', data=True),  # Collapsed by default
    dcc.Store(id='url-params', data={}),
    dcc.Store(id='embedded-mode', data=False),
    dcc.Interval(id="load-once", interval=1000, n_intervals=0, max_intervals=1),
    dcc.Download(id="download-pdf-report"),
    dcc.Location(id='url', refresh=False),

    # Modal for Create Report iframe
    html.Div(
        id="create-report-modal",
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
                    "margin": "5% auto",
                    "width": "1300px",
                    "maxWidth": "90%",
                    "height": "80%",
                    "backgroundColor": "white",
                    "borderRadius": "10px",
                    "padding": "20px",
                    "boxShadow": "0 5px 15px rgba(0,0,0,0.3)"
                },
                children=[
                    html.Button(
                        "✕",
                        id="close-modal-btn",
                        style={
                            "position": "absolute",
                            "top": "10px",
                            "right": "10px",
                            "fontSize": "24px",
                            "border": "none",
                            "backgroundColor": "transparent",
                            "cursor": "pointer",
                            "color": "#666",
                            "hover": {"color": "#000"}
                        }
                    ),
                    html.H3("Create New Report", style={"marginBottom": "20px", "color": "#0056b3"}),
                    html.Iframe(
                        src="/django_plotly_dash/app/CreateTiterReportApp/",
                        style={
                            "width": "100%",
                            "height": "calc(100% - 60px)",
                            "border": "none"
                        }
                    )
                ]
            )
        ]
    ),

    # Modal for Select Report
    html.Div(
        id="select-report-modal",
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
                        id="close-select-report-btn",
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
                    html.H3("Select a Report", style={
                        "marginBottom": "20px",
                        "color": "#0056b3",
                        "textAlign": "center"
                    }),
                    html.Div(
                        style={
                            "flex": "1",
                            "overflow": "auto",
                            "marginBottom": "60px"
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
                                row_selectable="single",
                                filter_action="native",
                                sort_action="native",
                                page_action="native",
                                page_size=20,
                                style_table={
                                    'overflowX': 'auto',
                                    'borderRadius': '5px',
                                    'height': '100%'
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
                                    'borderBottom': '2px solid #dee2e6',
                                    'color': '#495057'
                                },
                                style_data={
                                    'borderBottom': '1px solid #e9ecef',
                                    'color': '#212529'
                                },
                                style_data_conditional=[
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': '#f8f9fa',
                                    },
                                    {
                                        'if': {'state': 'selected'},
                                        'backgroundColor': '#e3f2fd',
                                        'border': '1px solid #0056b3',
                                    }
                                ],
                                style_filter={
                                    'backgroundColor': '#f8f9fa',
                                }
                            )
                        ]
                    ),
                    html.Button("Select Report",
                                id="confirm-report-selection",
                                style={
                                    'backgroundColor': '#0056b3',
                                    'color': 'white',
                                    'border': 'none',
                                    'padding': '10px 30px',
                                    'fontSize': '14px',
                                    'cursor': 'pointer',
                                    'borderRadius': '5px',
                                    'fontWeight': '500',
                                    'position': 'absolute',
                                    'bottom': '20px',
                                    'right': '20px',
                                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                                }
                                )
                ]
            )
        ]
    ),

    # Top toolbar with action buttons
    html.Div(
        id='toolbar-container',
        style={
            'display': 'flex',
            'justifyContent': 'space-between',
            'alignItems': 'center',
            'padding': '15px 20px',
            'backgroundColor': '#f8f9fa',
            'borderBottom': '1px solid #dee2e6',
            'gap': '10px'
        },
        children=[
            # Left side - Create Report button
            html.Div(
                id='left-toolbar',
                style={'display': 'flex', 'gap': '10px', 'alignItems': 'center'},
                children=[
                    html.Button([
                        html.Span("➕ ", style={'marginRight': '5px'}),
                        "Create New Report"
                    ], id="create-report-btn", style={
                        'backgroundColor': '#0056b3',
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px 20px',
                        'fontSize': '14px',
                        'cursor': 'pointer',
                        'borderRadius': '5px',
                        'fontWeight': '500',
                        'transition': 'all 0.3s ease',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    }),
                    html.Button([
                        html.Span("📊 ", style={'marginRight': '5px'}),
                        "Select Report"
                    ], id="change-report-btn", style={
                        'backgroundColor': '#6c757d',
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px 20px',
                        'fontSize': '14px',
                        'cursor': 'pointer',
                        'borderRadius': '5px',
                        'fontWeight': '500',
                        'transition': 'all 0.3s ease',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    }),
                    html.Div([
                        html.Span("Current Report: ", style={'fontWeight': '600', 'color': '#495057'}),
                        html.Span("No report selected", id="current-report-text", style={'color': '#6c757d'})
                    ], style={'marginLeft': '20px', 'fontSize': '14px'})
                ]
            ),

            # Right side - Save buttons
            html.Div(
                style={'display': 'flex', 'gap': '10px'},
                children=[
                    html.Button([
                        html.Span("💾 ", style={'marginRight': '5px'}),
                        "Save Settings"
                    ], id="save-settings-btn", style={
                        'backgroundColor': '#28a745',
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px 20px',
                        'fontSize': '14px',
                        'cursor': 'pointer',
                        'borderRadius': '5px',
                        'fontWeight': '500',
                        'transition': 'all 0.3s ease',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    }),
                    html.Button([
                        html.Span("🔗 ", style={'marginRight': '5px'}),
                        "Link Results"
                    ], id="save-to-lims-btn", style={
                        'backgroundColor': '#17a2b8',
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px 20px',
                        'fontSize': '14px',
                        'cursor': 'pointer',
                        'borderRadius': '5px',
                        'fontWeight': '500',
                        'transition': 'all 0.3s ease',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    }),
                    html.Button([
                        html.Span("📄 ", style={'marginRight': '5px'}),
                        "Create PDF Report"
                    ], id="create-pdf-btn", style={
                        'backgroundColor': '#dc3545',
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px 20px',
                        'fontSize': '14px',
                        'cursor': 'pointer',
                        'borderRadius': '5px',
                        'fontWeight': '500',
                        'transition': 'all 0.3s ease',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    }),
                ]
            )
        ]
    ),

    # Status messages
    html.Div(id="status-message", style={
        'padding': '15px',
        'margin': '10px 20px',
        'borderRadius': '5px',
        'display': 'none',
        'fontSize': '14px',
        'fontWeight': '500',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
    }),

    # Main content area
    html.Div(
        style={
            'padding': '20px',
            'backgroundColor': '#f5f5f5',
            'minHeight': 'calc(100vh - 200px)'
        },
        children=[
            dcc.Tabs(id="main-tabs", value="tab-1", style={'backgroundColor': 'white', 'borderRadius': '5px'},
                     children=[

                         dcc.Tab(label="📈 Sample Analysis", value="tab-1",
                                 style={'padding': '10px', 'fontWeight': '500'},
                                 selected_style={'padding': '10px', 'fontWeight': '600', 'backgroundColor': '#e3f2fd'},
                                 children=[
                                     html.Div([
                                         # Container for plot and settings side by side
                                         html.Div(
                                             style={
                                                 'display': 'flex',
                                                 'gap': '20px',
                                                 'marginTop': '20px',
                                                 'marginBottom': '20px'
                                             },
                                             children=[
                                                 # Plot area (left side)
                                                 html.Div(
                                                     id='plot-area',
                                                     children=[
                                                         html.H4("Titer Results", id="results-header",
                                                                 style={'textAlign': 'center', 'color': '#0056b3',
                                                                        'fontWeight': '500'}),
                                                         dcc.Graph(id='time-series-graph', style={'height': '500px'})
                                                     ],
                                                     style={
                                                         'backgroundColor': 'white',
                                                         'padding': '20px',
                                                         'borderRadius': '8px',
                                                         'boxShadow': '0 2px 4px rgba(0,0,0,0.08)',
                                                         'flex': '1'
                                                     }
                                                 ),

                                                 # Plot settings (right side - collapsible)
                                                 html.Div(
                                                     id='plot-settings-container',
                                                     style={
                                                         'width': '50px',  # Start collapsed
                                                         'transition': 'width 0.3s ease',
                                                         'position': 'relative',
                                                         'overflow': 'hidden'
                                                     },
                                                     children=[
                                                         html.Div(
                                                             id='plot-settings',
                                                             style={
                                                                 'backgroundColor': 'white',
                                                                 'padding': '20px',
                                                                 'borderRadius': '8px',
                                                                 'boxShadow': '0 2px 4px rgba(0,0,0,0.08)',
                                                                 'height': '100%',
                                                                 'minHeight': '400px',
                                                                 'position': 'relative'
                                                             },
                                                             children=[
                                                                 # Toggle button
                                                                 html.Button(
                                                                     "▶",  # Start with expand arrow
                                                                     id="toggle-settings-btn",
                                                                     style={
                                                                         'position': 'absolute',
                                                                         'left': '10px',
                                                                         'top': '10px',
                                                                         'backgroundColor': '#0056b3',
                                                                         'border': 'none',
                                                                         'fontSize': '16px',
                                                                         'cursor': 'pointer',
                                                                         'color': 'white',
                                                                         'padding': '5px 10px',
                                                                         'borderRadius': '3px',
                                                                         'zIndex': '10'
                                                                     }
                                                                 ),
                                                                 # Content wrapper
                                                                 html.Div(
                                                                     id='settings-inner-content',
                                                                     style={'display': 'none'},  # Hidden by default
                                                                     children=[
                                                                         html.H4("Plot Settings",
                                                                                 style={
                                                                                     'color': '#0056b3',
                                                                                     'margin': '0 0 20px 40px',
                                                                                     'fontWeight': '500',
                                                                                     'textAlign': 'left'
                                                                                 }
                                                                                 ),
                                                                         html.Div(
                                                                             style={'paddingLeft': '40px'},
                                                                             children=[
                                                                                 html.Label("Channel Selection:",
                                                                                            style={'fontWeight': '600',
                                                                                                   'marginBottom': '10px'}),
                                                                                 dcc.RadioItems(
                                                                                     id='channel-radio',
                                                                                     options=[
                                                                                         {'label': ' UV280',
                                                                                          'value': 'channel_1'},
                                                                                         {'label': ' UV260',
                                                                                          'value': 'channel_2'},
                                                                                         {'label': ' Pressure',
                                                                                          'value': 'channel_3'}
                                                                                     ],
                                                                                     value='channel_1',
                                                                                     labelStyle={
                                                                                         'display': 'block',
                                                                                         'marginBottom': '10px',
                                                                                         'cursor': 'pointer',
                                                                                         'padding': '5px',
                                                                                         'borderRadius': '3px',
                                                                                         'transition': 'all 0.3s ease'
                                                                                     },
                                                                                     inputStyle={"marginRight": "5px"}
                                                                                 ),
                                                                                 html.Hr(style={'margin': '20px 0'}),
                                                                                 html.Label("Plot View:",
                                                                                            style={'fontWeight': '600',
                                                                                                   'marginBottom': '10px'}),
                                                                                 dcc.Dropdown(
                                                                                     id='plot-type-dropdown',
                                                                                     options=[
                                                                                         {'label': 'Single Plot View',
                                                                                          'value': 'plotly'},
                                                                                         {'label': 'Subplot View',
                                                                                          'value': 'subplots'}
                                                                                     ],
                                                                                     value='plotly',
                                                                                     style={'width': '90%'}
                                                                                 ),
                                                                             ]
                                                                         )
                                                                     ]
                                                                 ),
                                                                 # Vertical title (visible when collapsed)
                                                                 html.Div(
                                                                     id='vertical-title',
                                                                     style={
                                                                         'position': 'absolute',
                                                                         'left': '50%',
                                                                         'top': '50%',
                                                                         'transform': 'translate(-50%, -50%) rotate(-90deg)',
                                                                         'transformOrigin': 'center',
                                                                         'whiteSpace': 'nowrap',
                                                                         'color': '#0056b3',
                                                                         'fontWeight': '600',
                                                                         'fontSize': '18px',
                                                                         'display': 'block'
                                                                         # Visible by default (collapsed state)
                                                                     },
                                                                     children="Plot Settings"
                                                                 )
                                                             ]
                                                         )
                                                     ]
                                                 )
                                             ]
                                         ),

                                         # Results table
                                         html.Div(
                                             id='titer-data',
                                             children=[
                                                 html.Div(
                                                     style={'display': 'flex', 'justifyContent': 'space-between',
                                                            'alignItems': 'center', 'marginBottom': '20px'},
                                                     children=[
                                                         html.H4("Analysis Results",
                                                                 style={'color': '#0056b3', 'margin': '0',
                                                                        'fontWeight': '500'}),
                                                         html.Button([
                                                             html.Span("📥 ", style={'marginRight': '5px'}),
                                                             "Export to Excel"
                                                         ], id="export-button", style={
                                                             'backgroundColor': '#6c757d',
                                                             'color': 'white',
                                                             'padding': '8px 16px',
                                                             'border': 'none',
                                                             'borderRadius': '5px',
                                                             'cursor': 'pointer',
                                                             'fontSize': '14px',
                                                             'fontWeight': '500',
                                                             'transition': 'all 0.3s ease'
                                                         }),
                                                     ]
                                                 ),
                                                 dash_table.DataTable(
                                                     id='result-table',
                                                     columns=[
                                                         {"name": "Sample Name", "id": "Sample Name"},
                                                         {"name": "Dilution Factor", "id": "Dilution Factor"},
                                                         {"name": "Peak Start", "id": "Peak Start", "type": "numeric",
                                                          "format": {"specifier": ".2f"}},
                                                         {"name": "Peak End", "id": "Peak End", "type": "numeric",
                                                          "format": {"specifier": ".2f"}},
                                                         {"name": "Main Peak Area", "id": "Main Peak Area",
                                                          "type": "numeric", "format": {"specifier": ".0f"}},
                                                         {"name": "Concentration (mg/mL)", "id": "Concentration",
                                                          "type": "numeric", "format": {"specifier": ".3f"}},
                                                         {"name": "Uncertainty", "id": "Uncertainty"},
                                                         {"name": "Injection Volume (µL)", "id": "Injection Volume"},
                                                         {"name": "LIMS Status", "id": "LIMS Status"}
                                                     ],
                                                     data=[],
                                                     sort_action="native",
                                                     fixed_rows={'headers': True},
                                                     style_table={
                                                         'overflowX': 'auto',
                                                         'overflowY': 'auto',
                                                         'maxHeight': '500px',
                                                         'borderRadius': '5px'
                                                     },
                                                     style_cell={
                                                         'textAlign': 'center',
                                                         'padding': '12px',
                                                         'fontSize': '14px',
                                                         'fontFamily': 'system-ui, -apple-system, sans-serif'
                                                     },
                                                     style_header={
                                                         'backgroundColor': '#0056b3',
                                                         'fontWeight': '600',
                                                         'color': 'white',
                                                         'borderBottom': '2px solid #004494'
                                                     },
                                                     style_data={
                                                         'borderBottom': '1px solid #e9ecef',
                                                         'color': '#212529'
                                                     },
                                                     style_data_conditional=[
                                                         {
                                                             'if': {'row_index': 'odd'},
                                                             'backgroundColor': '#f8f9fa',
                                                         },
                                                         {
                                                             'if': {'column_id': 'LIMS Status',
                                                                    'filter_query': '{LIMS Status} = "Saved"'},
                                                             'backgroundColor': '#d4edda',
                                                             'color': '#155724',
                                                             'fontWeight': '600'
                                                         },
                                                         {
                                                             'if': {'column_id': 'Concentration'},
                                                             'fontWeight': '600'
                                                         }
                                                     ]
                                                 ),
                                                 dcc.Download(id="download-result-data")
                                             ],
                                             style={
                                                 'backgroundColor': 'white',
                                                 'padding': '20px',
                                                 'borderRadius': '8px',
                                                 'boxShadow': '0 2px 4px rgba(0,0,0,0.08)'
                                             }
                                         ),
                                     ])
                                 ]),

                         dcc.Tab(label="🔬 Standard Analysis", value="tab-2",
                                 style={'padding': '10px', 'fontWeight': '500'},
                                 selected_style={'padding': '10px', 'fontWeight': '600', 'backgroundColor': '#e3f2fd'},
                                 children=[
                                     html.Div(
                                         id='standard-analysis',
                                         children=[
                                             html.Div(
                                                 style={
                                                     'backgroundColor': 'white',
                                                     'padding': '20px',
                                                     'borderRadius': '8px',
                                                     'boxShadow': '0 2px 4px rgba(0,0,0,0.08)',
                                                     'marginTop': '20px',
                                                     'marginBottom': '20px'
                                                 },
                                                 children=[
                                                     html.H4("Standard Curve Analysis", style={
                                                         'textAlign': 'center',
                                                         'color': '#0056b3',
                                                         'marginBottom': '20px',
                                                         'fontWeight': '500'
                                                     }),
                                                     dcc.Graph(id='standard-plot', style={'height': '400px'}),
                                                 ]
                                             ),

                                             html.Div(
                                                 id='standard-analysis-content',
                                                 children=[
                                                     html.Div(
                                                         style={'marginBottom': '20px'},
                                                         children=[
                                                             dcc.Graph(id='regression-plot', style={'height': '400px'}),
                                                         ]
                                                     ),
                                                     html.Div(
                                                         style={
                                                             'display': 'flex',
                                                             'gap': '20px',
                                                             'marginBottom': '20px'
                                                         },
                                                         children=[
                                                             html.Div(
                                                                 style={
                                                                     'flex': '1',
                                                                     'backgroundColor': '#e3f2fd',
                                                                     'padding': '15px',
                                                                     'borderRadius': '5px',
                                                                     'textAlign': 'center'
                                                                 },
                                                                 children=[
                                                                     html.P("Regression Equation",
                                                                            style={'margin': '0', 'fontWeight': '600',
                                                                                   'color': '#0056b3'}),
                                                                     html.P(id="regression-equation",
                                                                            style={'margin': '5px 0',
                                                                                   'fontSize': '16px'})
                                                                 ]
                                                             ),
                                                             html.Div(
                                                                 style={
                                                                     'flex': '1',
                                                                     'backgroundColor': '#e8f5e9',
                                                                     'padding': '15px',
                                                                     'borderRadius': '5px',
                                                                     'textAlign': 'center'
                                                                 },
                                                                 children=[
                                                                     html.P("R² Value",
                                                                            style={'margin': '0', 'fontWeight': '600',
                                                                                   'color': '#2e7d32'}),
                                                                     html.P(id="r-squared-value",
                                                                            style={'margin': '5px 0',
                                                                                   'fontSize': '16px'})
                                                                 ]
                                                             )
                                                         ]
                                                     ),
                                                     dash_table.DataTable(
                                                         id="standard-table",
                                                         columns=[
                                                             {"name": "Sample Name", "id": "Sample Name"},
                                                             {"name": "Injection Date", "id": "Injection Date"},
                                                             {"name": "Peak Start", "id": "Peak Start",
                                                              "type": "numeric", "format": {"specifier": ".2f"}},
                                                             {"name": "Peak End", "id": "Peak End", "type": "numeric",
                                                              "format": {"specifier": ".2f"}},
                                                             {"name": "Peak Area", "id": "Main Peak Area",
                                                              "type": "numeric", "format": {"specifier": ".0f"}},
                                                             {"name": "Concentration (mg/mL)",
                                                              "id": "Concentration (mg/mL)", "type": "numeric",
                                                              "format": {"specifier": ".3f"}},
                                                             {"name": "Injection Volume (µL)",
                                                              "id": "Injection Volume (uL)"}
                                                         ],
                                                         data=[],
                                                         row_selectable='multi',
                                                         selected_rows=[],
                                                         style_table={
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
                                                             'borderBottom': '2px solid #dee2e6',
                                                             'color': '#495057'
                                                         },
                                                         style_data={
                                                             'borderBottom': '1px solid #e9ecef',
                                                             'color': '#212529'
                                                         },
                                                         style_data_conditional=[
                                                             {
                                                                 'if': {'row_index': 'odd'},
                                                                 'backgroundColor': '#f8f9fa',
                                                             },
                                                             {
                                                                 'if': {'state': 'selected'},
                                                                 'backgroundColor': '#e3f2fd',
                                                                 'border': '1px solid #0056b3',
                                                             }
                                                         ]
                                                     )
                                                 ],
                                                 style={
                                                     'backgroundColor': 'white',
                                                     'padding': '20px',
                                                     'borderRadius': '8px',
                                                     'boxShadow': '0 2px 4px rgba(0,0,0,0.08)'
                                                 }
                                             ),
                                         ],
                                     )
                                 ])
                     ])
        ]
    )
])


# Parse URL parameters
@app.callback(
    [Output('url-params', 'data'),
     Output('embedded-mode', 'data'),
     Output('selected-report', 'data', allow_duplicate=True)],
    [Input('url', 'search')],
    prevent_initial_call='initial_duplicate'
)
def parse_url_params(search):
    if not search:
        return {}, False, None

    # Parse query parameters
    from urllib.parse import parse_qs
    params = parse_qs(search.lstrip('?'))

    # Extract parameters
    url_params = {}
    embedded = False
    report_id = None

    if 'embedded' in params:
        embedded = params['embedded'][0].lower() in ['true', '1', 'yes']
        url_params['embedded'] = embedded

    if 'report_id' in params:
        try:
            report_id = int(params['report_id'][0])
            url_params['report_id'] = report_id
        except:
            pass

    return url_params, embedded, report_id


# Update toolbar visibility based on embedded mode
@app.callback(
    [Output('create-report-btn', 'style'),
     Output('change-report-btn', 'style')],
    [Input('embedded-mode', 'data')],
    prevent_initial_call=False
)
def update_toolbar_visibility(embedded):
    if embedded:
        # Hide buttons in embedded mode
        hidden_style = {'display': 'none'}
        return hidden_style, hidden_style
    else:
        # Show buttons in normal mode
        create_btn_style = {
            'backgroundColor': '#0056b3',
            'color': 'white',
            'border': 'none',
            'padding': '10px 20px',
            'fontSize': '14px',
            'cursor': 'pointer',
            'borderRadius': '5px',
            'fontWeight': '500',
            'transition': 'all 0.3s ease',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
        }

        select_btn_style = {
            'backgroundColor': '#6c757d',
            'color': 'white',
            'border': 'none',
            'padding': '10px 20px',
            'fontSize': '14px',
            'cursor': 'pointer',
            'borderRadius': '5px',
            'fontWeight': '500',
            'transition': 'all 0.3s ease',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
        }

        return create_btn_style, select_btn_style


# Callback to show/hide Create Report modal
@app.callback(
    Output("create-report-modal", "style"),
    [Input("create-report-btn", "n_clicks"),
     Input("close-modal-btn", "n_clicks")],
    [State("create-report-modal", "style")],
    prevent_initial_call=True
)
def toggle_modal(open_clicks, close_clicks, current_style):
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_style

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "create-report-btn":
        return {**current_style, "display": "block"}
    elif button_id == "close-modal-btn":
        return {**current_style, "display": "none"}

    return current_style


# Callback to show/hide Select Report modal
@app.callback(
    [Output("select-report-modal", "style"),
     Output("current-report-text", "children")],
    [Input("change-report-btn", "n_clicks"),
     Input("close-select-report-btn", "n_clicks"),
     Input("confirm-report-selection", "n_clicks"),
     Input("load-once", "n_intervals"),
     Input("url-params", "data")],
    [State("select-report-modal", "style"),
     State("selected-report", "data"),
     State("report-selection-table", "selected_rows"),
     State("report-selection-table", "data"),
     State("embedded-mode", "data")],
    prevent_initial_call=False
)
def toggle_select_report_modal(change_clicks, close_clicks, confirm_clicks, load_interval,
                               url_params, current_style, selected_report, selected_rows,
                               table_data, embedded):
    ctx = dash.callback_context

    # Get the ID of the component that triggered the callback
    if not ctx.triggered:
        triggered_id = None
    else:
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Check if report_id is provided in URL
    if triggered_id == "url-params" and url_params.get('report_id'):
        report_id = url_params['report_id']
        report = Report.objects.filter(report_id=report_id).first()
        if report:
            return current_style, f"{report.project_id} - {report.report_name}"

    # Check if no report is selected on initial load (but not in embedded mode)
    if triggered_id == "load-once" and not selected_report and not embedded:
        return {**current_style, "display": "block"}, "No report selected"

    if not ctx.triggered:
        return current_style, "No report selected"

    if triggered_id == "change-report-btn":
        return {**current_style, "display": "block"}, dash.no_update
    elif triggered_id == "close-select-report-btn":
        return {**current_style, "display": "none"}, dash.no_update
    elif triggered_id == "confirm-report-selection" and selected_rows and table_data:
        # Get selected report info
        selected = table_data[selected_rows[0]]
        report_text = f"{selected['project_id']} - {selected['report_name']}"
        return {**current_style, "display": "none"}, report_text

    # Update report text if report is selected
    if selected_report:
        report = Report.objects.filter(report_id=selected_report).first()
        if report:
            return current_style, f"{report.project_id} - {report.report_name}"

    return current_style, "No report selected"


# Callback to save plot settings
@app.callback(
    [Output("status-message", "children"),
     Output("status-message", "style")],
    [Input("save-settings-btn", "n_clicks")],
    [State("selected-report", "data"),
     State("channel-radio", "value"),
     State("plot-type-dropdown", "value"),
     State("standard-table", "selected_rows"),
     State("regression-parameters", "data")],
    prevent_initial_call=True
)
def save_plot_settings(n_clicks, report_id, channel, plot_type, selected_std_rows, regression_params):
    if not report_id:
        return "⚠️ No report selected!", {
            "display": "block",
            "backgroundColor": "#f8d7da",
            "color": "#721c24",
            "border": "1px solid #f5c6cb"
        }

    try:
        report = Report.objects.get(report_id=report_id)

        # Prepare settings to save
        plot_settings = {
            "channel": channel,
            "plot_type": plot_type,
            "selected_standard_rows": selected_std_rows,
            "regression_parameters": regression_params,
            "saved_at": datetime.now().isoformat()
        }

        # Save to report's plot_settings field
        report.plot_settings = plot_settings
        report.save()

        return "✅ Plot settings saved successfully!", {
            "display": "block",
            "backgroundColor": "#d4edda",
            "color": "#155724",
            "border": "1px solid #c3e6cb"
        }

    except Exception as e:
        return f"❌ Error saving settings: {str(e)}", {
            "display": "block",
            "backgroundColor": "#f8d7da",
            "color": "#721c24",
            "border": "1px solid #f5c6cb"
        }


# Callback to save results to LIMS
@app.callback(
    [Output("result-table", "data", allow_duplicate=True),
     Output("status-message", "children", allow_duplicate=True),
     Output("status-message", "style", allow_duplicate=True)],
    [Input("save-to-lims-btn", "n_clicks")],
    [State("result-table", "data"),
     State("selected-report", "data")],
    prevent_initial_call=True
)
def save_to_lims(n_clicks, table_data, report_id):
    if not table_data or not report_id:
        return table_data, "⚠️ No data to link!", {
            "display": "block",
            "backgroundColor": "#f8d7da",
            "color": "#721c24",
            "border": "1px solid #f5c6cb"
        }

    try:
        # Get report info for project_id
        report = Report.objects.get(report_id=report_id)
        project_id = report.project_id

        saved_count = 0
        errors = []

        for row in table_data:
            sample_name = row.get("Sample Name")
            concentration = row.get("Concentration")

            # Skip if already saved or no concentration
            if row.get("LIMS Status") == "Saved" or not concentration:
                continue

            try:
                # Extract sample type from sample name prefix
                sample_type = None
                if sample_name.startswith("UP"):
                    sample_type = 1  # UP
                elif sample_name.startswith("FB"):
                    sample_type = 2  # FB
                elif sample_name.startswith("PD"):
                    sample_type = 3  # PD
                else:
                    # Try to get from SampleMetadata
                    sample_meta = SampleMetadata.objects.filter(sample_name=sample_name).first()
                    if sample_meta and sample_meta.sample_prefix:
                        if sample_meta.sample_prefix == "UP":
                            sample_type = 1
                        elif sample_meta.sample_prefix == "FB":
                            sample_type = 2
                        elif sample_meta.sample_prefix == "PD":
                            sample_type = 3

                if not sample_type:
                    errors.append(f"{sample_name}: Unable to determine sample type")
                    continue

                # Create or update LIMS sample analysis
                lims_sample, created = LimsSampleAnalysis.objects.update_or_create(
                    sample_id=sample_name,
                    defaults={
                        'sample_type': sample_type,
                        'project_id': project_id,
                        'analyst': report.user_id or 'Unknown',
                        'sample_date': datetime.now().date(),
                        'description': f'Titer analysis from report {report.report_name}'
                    }
                )

                # Create or update titer result
                titer_result, created = LimsTiterResult.objects.update_or_create(
                    sample_id=lims_sample,
                    defaults={
                        'titer': concentration,
                        'qc_pass': True,
                        'status': 'completed'
                    }
                )

                # Update the relationship in LimsSampleAnalysis
                lims_sample.titer_result = titer_result
                lims_sample.save()

                # Update row status
                row["LIMS Status"] = "Saved"
                saved_count += 1

            except Exception as e:
                errors.append(f"{sample_name}: {str(e)}")

        if errors:
            message = f"⚠️ Linked {saved_count} results. Errors: {'; '.join(errors[:3])}"  # Show first 3 errors
            if len(errors) > 3:
                message += f" and {len(errors) - 3} more..."
            style = {
                "display": "block",
                "backgroundColor": "#fff3cd",
                "color": "#856404",
                "border": "1px solid #ffeeba"
            }
        else:
            message = f"✅ Successfully linked {saved_count} results to LIMS!"
            style = {
                "display": "block",
                "backgroundColor": "#d4edda",
                "color": "#155724",
                "border": "1px solid #c3e6cb"
            }

        return table_data, message, style

    except Exception as e:
        return table_data, f"❌ Error linking to LIMS: {str(e)}", {
            "display": "block",
            "backgroundColor": "#f8d7da",
            "color": "#721c24",
            "border": "1px solid #f5c6cb"
        }


# Populate report table
@app.callback(
    Output("report-selection-table", "data"),
    Input("load-once", "n_intervals")
)
def populate_report_table(active_tab):
    reports = Report.objects.filter(analysis_type=2).order_by('-date_created').values(
        "report_id", "report_name", "project_id", "user_id", "date_created"
    )
    data = []
    for report in reports:
        date = report["date_created"]
        date_str = date.strftime("%Y-%m-%d %H:%M:%S") if date else "N/A"
        data.append({
            "report_id": report["report_id"],
            "report_name": report["report_name"],
            "project_id": report["project_id"],
            "user_id": report["user_id"] or "N/A",
            "date_created": date_str
        })
    return data


# Store selected report
@app.callback(
    Output("selected-report", "data"),
    [Input("confirm-report-selection", "n_clicks")],
    [State("report-selection-table", "selected_rows"),
     State("report-selection-table", "data")],
    prevent_initial_call=True
)
def store_selected_report(confirm_clicks, selected_rows, table_data):
    if not selected_rows or not confirm_clicks:
        return dash.no_update
    selected_row = table_data[selected_rows[0]]
    return selected_row["report_id"]


# Update results header
@app.callback(
    Output("results-header", "children"),
    [Input("selected-report", "data")],
    prevent_initial_call=True
)
def update_results_header(selected_report):
    report_name = selected_report

    if not report_name:
        return "Titer Results"

    report = Report.objects.filter(report_id=report_name).first()

    if not report:
        return "Report Not Found"

    return f"{report.project_id} - {report.report_name}"


def extract_concentration(sample_name):
    """Extracts concentration from sample names formatted as '130E7 Std_x'."""
    match = re.search(r"Std_([\d\.]+)", sample_name)
    return float(match.group(1)) if match else None


# Plot standard time series
@app.callback(
    Output("standard-plot", "figure"),
    [Input("selected-report", "data")],
    [State("selected-report", "data")],
    prevent_initial_call=True
)
def plot_standard_time_series(report_clicks, selected_report):
    """Fetch time series data for standard samples in the selected report and plot it."""
    report_name = selected_report

    if not report_name:
        return go.Figure()

    report = Report.objects.filter(report_id=report_name).first()

    if not report:
        return go.Figure()

    selected_samples = [s.strip() for s in report.selected_samples.split(",") if s.strip()]

    if not selected_samples:
        return go.Figure()

    result_ids = [r.strip() for r in report.selected_result_ids.split(",") if r.strip()]

    # Step 1: Retrieve sample_set_ids associated with these result_ids
    sample_set_ids = SampleMetadata.objects.filter(result_id__in=result_ids).values_list("sample_set_id",
                                                                                         flat=True).distinct()

    # Step 2: Filter standard samples within the identified sample_set_ids
    std_samples = SampleMetadata.objects.filter(
        sample_set_id__in=sample_set_ids,
        sample_name__contains="Std_"
    ).values("sample_name", "injection_volume", "result_id")

    # If not enough standards found, use fallback logic
    if len(std_samples) < 3:
        project_prefix = report.project_id.replace("SI-", "")

        sample_times = SampleMetadata.objects.filter(
            result_id__in=result_ids
        ).values_list("date_acquired", flat=True)

        if sample_times:
            median_time = sorted(sample_times)[len(sample_times) // 2]

            candidate_stds = SampleMetadata.objects.filter(
                sample_name__startswith=project_prefix,
                sample_name__contains="Std_"
            ).exclude(date_acquired__isnull=True).values(
                "sample_name", "injection_volume", "result_id", "sample_set_id", "date_acquired"
            )

            grouped_by_set = defaultdict(list)
            for std in candidate_stds:
                grouped_by_set[std["sample_set_id"]].append(std)

            best_group = None
            best_time_diff = timedelta.max

            for sample_set_id, group in grouped_by_set.items():
                if len(group) < 3:
                    continue
                group_times = [std["date_acquired"] for std in group]
                group_median = sorted(group_times)[len(group_times) // 2]
                time_diff = abs(group_median - median_time)
                if time_diff < best_time_diff:
                    best_time_diff = time_diff
                    best_group = group

            std_samples = best_group if best_group else []

    if not std_samples:
        return go.Figure()

    fig = go.Figure()

    for std in std_samples:
        result_id = std["result_id"]
        sample_name = std["sample_name"]

        time_series = TimeSeriesData.objects.filter(result_id=result_id).values("time", "channel_1")

        df = pd.DataFrame(list(time_series))

        if df.empty:
            continue

        fig.add_trace(go.Scatter(
            x=df["time"],
            y=df["channel_1"],
            mode="lines",
            name=sample_name,
            line=dict(width=2)
        ))

    fig.update_layout(
        title="Time Series Data for Standards",
        xaxis_title="Time (min)",
        yaxis_title="Signal Intensity",
        template="plotly_white",
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.01
        )
    )

    return fig


# Toggle plot settings collapse/expand
@app.callback(
    [Output("plot-settings-container", "style"),
     Output("toggle-settings-btn", "children"),
     Output("settings-collapsed", "data"),
     Output("settings-inner-content", "style"),
     Output("vertical-title", "style"),
     Output("toggle-settings-btn", "style")],
    [Input("toggle-settings-btn", "n_clicks")],
    [State("settings-collapsed", "data")],
    prevent_initial_call=True
)
def toggle_settings(n_clicks, is_collapsed):
    if is_collapsed:
        # Expand
        container_style = {'width': '300px', 'transition': 'width 0.3s ease', 'position': 'relative',
                           'overflow': 'visible'}
        content_style = {'display': 'block'}
        vertical_title_style = {'display': 'none'}
        button_style = {
            'position': 'absolute',
            'left': '10px',
            'top': '10px',
            'backgroundColor': '#0056b3',
            'border': 'none',
            'fontSize': '16px',
            'cursor': 'pointer',
            'color': 'white',
            'padding': '5px 10px',
            'borderRadius': '3px',
            'zIndex': '10'
        }
        return container_style, "◀", False, content_style, vertical_title_style, button_style
    else:
        # Collapse
        container_style = {'width': '50px', 'transition': 'width 0.3s ease', 'overflow': 'hidden',
                           'position': 'relative'}
        content_style = {'display': 'none'}
        vertical_title_style = {
            'position': 'absolute',
            'left': '50%',
            'top': '50%',
            'transform': 'translate(-50%, -50%) rotate(-90deg)',
            'transformOrigin': 'center',
            'whiteSpace': 'nowrap',
            'color': '#0056b3',
            'fontWeight': '600',
            'fontSize': '18px',
            'display': 'block'
        }
        button_style = {
            'position': 'absolute',
            'left': '10px',
            'top': '10px',
            'backgroundColor': '#0056b3',
            'border': 'none',
            'fontSize': '16px',
            'cursor': 'pointer',
            'color': 'white',
            'padding': '5px 10px',
            'borderRadius': '3px',
            'zIndex': '10'
        }
        return container_style, "▶", True, content_style, vertical_title_style, button_style


# Create PDF Report
@app.callback(
    [Output("download-pdf-report", "data"),
     Output("status-message", "children", allow_duplicate=True),
     Output("status-message", "style", allow_duplicate=True)],
    [Input("create-pdf-btn", "n_clicks")],
    [State("selected-report", "data"),
     State("time-series-graph", "figure"),
     State("result-table", "data"),
     State("regression-plot", "figure"),
     State("standard-table", "data"),
     State("regression-equation", "children"),
     State("r-squared-value", "children")],
    prevent_initial_call=True
)
def create_pdf_report(n_clicks, report_id, chromatogram_fig, result_data, regression_fig,
                      standard_data, regression_eq, r_squared):
    print(f"PDF Report Debug - n_clicks: {n_clicks}")
    print(f"PDF Report Debug - report_id: {report_id}")
    print(f"PDF Report Debug - has chromatogram: {chromatogram_fig is not None}")
    print(f"PDF Report Debug - result_data length: {len(result_data) if result_data else 0}")

    if not n_clicks:
        print("PDF Report Debug - No clicks, returning")
        return dash.no_update, dash.no_update, dash.no_update

    if not report_id:
        print("PDF Report Debug - No report ID")
        return dash.no_update, "⚠️ No report selected!", {
            "display": "block",
            "backgroundColor": "#f8d7da",
            "color": "#721c24",
            "border": "1px solid #f5c6cb"
        }

    try:
        import io
        import base64
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch

        print("PDF Report Debug - ReportLab imported successfully")

        try:
            import plotly.io as pio
            print("PDF Report Debug - Plotly.io imported successfully")
        except ImportError as e:
            print(f"PDF Report Debug - Plotly.io import error: {e}")
            # Try alternative approach
            pass

        # Get report info
        report = Report.objects.get(report_id=report_id)
        print(f"PDF Report Debug - Report found: {report.report_name}")

        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
        story = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0056b3'),
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph("Titer Analysis Report", title_style))
        story.append(Spacer(1, 12))

        # Report info
        info_style = ParagraphStyle(
            'Info',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=6
        )
        story.append(Paragraph(f"<b>Project ID:</b> {report.project_id}", info_style))
        story.append(Paragraph(f"<b>Report Name:</b> {report.report_name}", info_style))
        story.append(Paragraph(f"<b>Date Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
        story.append(Spacer(1, 20))

        # Section 1: Chromatogram
        story.append(Paragraph("Chromatogram", styles['Heading2']))
        story.append(Spacer(1, 12))

        # Convert plotly figure to image
        if chromatogram_fig:
            try:
                print("PDF Report Debug - Attempting to convert chromatogram to image")
                img_bytes = pio.to_image(chromatogram_fig, format='png', width=700, height=400)
                img_buffer = io.BytesIO(img_bytes)
                img = Image(img_buffer, width=6.5 * inch, height=3.7 * inch)
                story.append(img)
                print("PDF Report Debug - Chromatogram added successfully")
            except Exception as e:
                print(f"PDF Report Debug - Error converting chromatogram: {e}")
                story.append(Paragraph("Chromatogram could not be rendered", styles['Normal']))

        story.append(Spacer(1, 20))

        # Section 2: Analysis Results Table
        story.append(Paragraph("Analysis Results", styles['Heading2']))
        story.append(Spacer(1, 12))

        if result_data:
            print(f"PDF Report Debug - Creating table with {len(result_data)} rows")
            # Create table data
            table_data = [["Sample Name", "Dilution", "Concentration\n(mg/mL)", "Uncertainty", "LIMS Status"]]
            for row in result_data:
                if "Std_" not in row.get("Sample Name", ""):  # Exclude standards
                    table_data.append([
                        row.get("Sample Name", ""),
                        str(row.get("Dilution Factor", "")),
                        str(row.get("Concentration", "")),
                        row.get("Uncertainty", ""),
                        row.get("LIMS Status", "")
                    ])

            print(f"PDF Report Debug - Table has {len(table_data)} rows (including header)")

            # Create table
            t = Table(table_data, colWidths=[2 * inch, 0.8 * inch, 1.2 * inch, 1.5 * inch, 1 * inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#495057')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            story.append(t)

        story.append(PageBreak())

        # Section 3: Standard Analysis
        story.append(Paragraph("Standard Analysis", styles['Heading2']))
        story.append(Spacer(1, 12))

        # Add regression equation and R²
        story.append(Paragraph(f"<b>Regression Equation:</b> {regression_eq}", info_style))
        story.append(Paragraph(f"<b>R² Value:</b> {r_squared}", info_style))
        story.append(Spacer(1, 12))

        # Add regression plot
        if regression_fig:
            try:
                print("PDF Report Debug - Attempting to convert regression plot to image")
                img_bytes = pio.to_image(regression_fig, format='png', width=700, height=400)
                img_buffer = io.BytesIO(img_bytes)
                img = Image(img_buffer, width=6.5 * inch, height=3.7 * inch)
                story.append(img)
                print("PDF Report Debug - Regression plot added successfully")
            except Exception as e:
                print(f"PDF Report Debug - Error converting regression plot: {e}")
                story.append(Paragraph("Regression plot could not be rendered", styles['Normal']))

        story.append(Spacer(1, 20))

        # Standards table
        if standard_data:
            story.append(Paragraph("Standards Data", styles['Heading3']))
            story.append(Spacer(1, 12))

            table_data = [["Sample Name", "Concentration\n(mg/mL)", "Peak Area"]]
            for row in standard_data:
                table_data.append([
                    row.get("Sample Name", ""),
                    str(row.get("Concentration (mg/mL)", "")),
                    str(row.get("Main Peak Area", ""))
                ])

            t = Table(table_data, colWidths=[3 * inch, 1.5 * inch, 1.5 * inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#495057')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            story.append(t)

        # Build PDF
        print("PDF Report Debug - Building PDF document")
        doc.build(story)
        buffer.seek(0)

        # Create filename
        filename = f"{datetime.now().strftime('%Y%m%d')}_{report.project_id}_{report.report_name}_Analysis.pdf"
        print(f"PDF Report Debug - PDF created successfully, filename: {filename}")

        return dcc.send_bytes(buffer.read(), filename), \
            "✅ PDF report generated successfully!", \
            {
                "display": "block",
                "backgroundColor": "#d4edda",
                "color": "#155724",
                "border": "1px solid #c3e6cb"
            }

    except ImportError as e:
        print(f"PDF Report Debug - Import error: {e}")
        return dash.no_update, \
            "❌ Error: reportlab library not installed. Please install with: pip install reportlab plotly kaleido", \
            {
                "display": "block",
                "backgroundColor": "#f8d7da",
                "color": "#721c24",
                "border": "1px solid #f5c6cb"
            }
    except Exception as e:
        print(f"PDF Report Debug - General error: {e}")
        import traceback
        traceback.print_exc()
        return dash.no_update, \
            f"❌ Error generating PDF: {str(e)}", \
            {
                "display": "block",
                "backgroundColor": "#f8d7da",
                "color": "#721c24",
                "border": "1px solid #f5c6cb"
            }


# Update standard table
@app.callback(
    [Output("standard-table", "data"),
     Output("standard-table", "selected_rows")],
    [Input("selected-report", "data")],
    [State("selected-report", "data")],
    prevent_initial_call=True
)
def update_standard_table(report_clicks, selected_report):
    """Populate standard-table when a report is selected, and set default selected rows."""
    report_name = selected_report

    if not report_name:
        return [], []

    report = Report.objects.filter(report_id=report_name).first()
    if not report:
        return [], []

    result_ids = [r.strip() for r in report.selected_result_ids.split(",") if r.strip()]

    sample_set_ids = SampleMetadata.objects.filter(result_id__in=result_ids).values_list("sample_set_id",
                                                                                         flat=True).distinct()

    std_samples = SampleMetadata.objects.filter(
        sample_set_id__in=sample_set_ids,
        sample_name__contains="Std_"
    ).values("sample_name", "injection_volume", "result_id", "date_acquired")

    if len(std_samples) < 3:
        project_prefix = report.project_id.replace("SI-", "")

        sample_times = SampleMetadata.objects.filter(
            result_id__in=result_ids
        ).values_list("date_acquired", flat=True)

        if sample_times:
            median_time = sorted(sample_times)[len(sample_times) // 2]

            candidate_stds = SampleMetadata.objects.filter(
                sample_name__startswith=project_prefix,
                sample_name__contains="Std_"
            ).exclude(date_acquired__isnull=True).values(
                "sample_name", "injection_volume", "result_id", "sample_set_id", "date_acquired"
            )

            grouped_by_set = defaultdict(list)
            for std in candidate_stds:
                grouped_by_set[std["sample_set_id"]].append(std)

            best_group = None
            best_time_diff = timedelta.max

            for sample_set_id, group in grouped_by_set.items():
                if len(group) < 3:
                    continue
                group_times = [std["date_acquired"] for std in group]
                group_median = sorted(group_times)[len(group_times) // 2]
                time_diff = abs(group_median - median_time)
                if time_diff < best_time_diff:
                    best_time_diff = time_diff
                    best_group = group

            std_samples = best_group if best_group else []

    if not std_samples:
        return [], []

    table_data = []
    for std in std_samples:
        concentration = extract_concentration(std["sample_name"])
        injection_volume = std["injection_volume"]
        result_id = std["result_id"]

        dt = std["date_acquired"]
        dt = dt.replace(tzinfo=None)
        injection_date = dt.strftime("%b %d, %Y %I:%M %p")

        peak_result = (PeakResults.objects.filter(result_id=result_id).order_by("-height")
                       .values("area", "peak_start_time", "peak_end_time").first())

        peak_area = peak_result["area"] if peak_result else None
        peak_start = peak_result["peak_start_time"] if peak_result else None
        peak_end = peak_result["peak_end_time"] if peak_result else None

        if concentration and peak_area:
            table_data.append({
                "Sample Name": std["sample_name"],
                "Injection Date": injection_date,
                "Peak Start": peak_start,
                "Peak End": peak_end,
                "Main Peak Area": peak_area,
                "Concentration (mg/mL)": concentration,
                "Injection Volume (uL)": injection_volume
            })

    table_data = sorted(table_data, key=lambda x: x["Concentration (mg/mL)"])

    selected_rows = list(range(len(table_data)))

    return table_data, selected_rows


# Update regression plot
@app.callback(
    [Output("regression-equation", "children"),
     Output("r-squared-value", "children"),
     Output("regression-plot", "figure"),
     Output("regression-parameters", "data")],
    [Input("standard-table", "selected_rows")],
    [State("standard-table", "data")],
    prevent_initial_call=True
)
def update_regression_plot(selected_rows, table_data):
    """Update regression plot based on selected rows from the standard-table."""

    if not table_data or not selected_rows:
        return "No Standard Data Selected", "N/A", go.Figure(), {"slope": None, "intercept": None}

    selected_data = [table_data[i] for i in selected_rows if i < len(table_data)]
    selected_df = pd.DataFrame(selected_data)

    if selected_df.empty:
        return "No Standard Data Selected", "N/A", go.Figure(), {"slope": None, "intercept": None}

    concentrations = selected_df["Concentration (mg/mL)"].astype(float)
    peak_areas = selected_df["Main Peak Area"].astype(float)

    try:
        slope, intercept, r_value, _, std_err = linregress(concentrations, peak_areas)
    except Exception as e:
        return "Regression Failed", "N/A", go.Figure(), {"slope": None, "intercept": None, "std_dev": None}

    x_vals = np.linspace(concentrations.min(), concentrations.max(), 100)
    y_vals = slope * x_vals + intercept

    n = len(concentrations)
    mean_x = np.mean(concentrations)
    sum_x_sq = np.sum((concentrations - mean_x) ** 2)

    t_score = t.ppf(0.975, df=n - 2)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=concentrations,
        y=peak_areas,
        mode="markers",
        name="Standard Data",
        marker=dict(size=10, color="#0056b3", line=dict(width=1, color='DarkSlateGrey'))
    ))
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="lines",
        name="Regression Line",
        line=dict(color="#dc3545", width=3, dash="dash")
    ))

    for i, (x, y) in enumerate(zip(concentrations, peak_areas)):
        fig.add_annotation(
            x=x, y=y,
            text=f"{x:.3f} mg/mL",
            showarrow=True,
            arrowhead=2,
            ax=0, ay=-30,
            bgcolor="white",
            bordercolor="#0056b3",
            borderwidth=1
        )

    fig.update_layout(
        title="Regression Analysis: Concentration vs Peak Area",
        xaxis_title="Concentration (mg/mL)",
        yaxis_title="Peak Area",
        template="plotly_white",
        hovermode='x unified'
    )

    return (
        f"y = {slope:.4f}x + {intercept:.4f}",
        f"{r_value ** 2:.4f}",
        fig,
        {"slope": slope,
         "intercept": intercept,
         "std_err": std_err,
         "t_score": t_score,
         "n": n,
         "mean_x": mean_x,
         "sum_x_sq": sum_x_sq
         }
    )


# Update result table
@app.callback(
    [Output("result-table", "columns"),
     Output("result-table", "data")],
    [Input("selected-report", "data"),
     Input("regression-parameters", "data")],
    [State("selected-report", "data")],
    prevent_initial_call=True
)
def update_result_table(report_clicks, regression_params, selected_report):
    """Populate result-table with all report samples and update calculated concentrations using regression parameters."""
    report_name = selected_report

    if not report_name:
        return [], []

    report = Report.objects.filter(report_id=report_name).first()
    if not report:
        return [], []

    all_samples = [s.strip() for s in report.selected_result_ids.split(",") if s.strip()]
    report_samples = SampleMetadata.objects.filter(result_id__in=all_samples).values(
        "sample_name", "injection_volume", "result_id", "system_name", "date_acquired"
    )

    if not report_samples:
        return [], []

    slope = regression_params.get("slope")
    intercept = regression_params.get("intercept")
    std_err = regression_params.get("std_err")
    t_score = regression_params.get("t_score")
    n = regression_params.get("n")
    mean_x = regression_params.get("mean_x")
    sum_x_sq = regression_params.get("sum_x_sq")

    result_data = []

    for i, sample in enumerate(report_samples):
        sample_name = sample["sample_name"]
        injection_volume = sample["injection_volume"]
        result_id = sample["result_id"]
        system_name = sample["system_name"]
        date_acquired = sample["date_acquired"]
        dt = sample["date_acquired"]
        dt = dt.replace(tzinfo=None)
        injection_date = dt.strftime("%b %d, %Y %I:%M %p")

        sample_metadata = SampleMetadata.objects.filter(result_id=result_id).first()

        dilution_factor = sample_metadata.dilution if sample_metadata and sample_metadata.dilution is not None else 1

        peak_result = PeakResults.objects.filter(result_id=result_id, channel_name='DAD.0.0').order_by(
            "-height").values(
            "area", "peak_start_time", "peak_end_time", "height").first()

        peak_area = peak_result["area"] if peak_result else None
        peak_start = peak_result["peak_start_time"] if peak_result else None
        peak_end = peak_result["peak_end_time"] if peak_result else None

        calculated_concentration = None
        uncertainty = None

        if peak_area and slope is not None and intercept is not None:
            calculated_concentration = round(((peak_area - intercept) / slope) * dilution_factor, 3) if slope else None

            if calculated_concentration is not None and slope is not None and intercept is not None:
                uncertainty = t_score * std_err * np.sqrt(
                    1 + (1 / n) + ((calculated_concentration - mean_x) ** 2 / sum_x_sq))

                uncertainty /= abs(slope)

                calculated_concentration = round(calculated_concentration, 3)
                uncertainty = round(uncertainty, 3)

        lims_status = "Not Saved"
        try:
            lims_sample = LimsSampleAnalysis.objects.filter(sample_name=sample_name).first()
            if lims_sample:
                titer_result = LimsTiterResult.objects.filter(sample_id=lims_sample).first()
                if titer_result:
                    lims_status = "Saved"
        except:
            pass

        result_data.append({
            "Sample Name": sample_name,
            "System Name": system_name,
            "Injection Date": injection_date,
            "Dilution Factor": dilution_factor,
            "Peak Start": peak_start,
            "Peak End": peak_end,
            "Main Peak Area": peak_area,
            "Concentration": calculated_concentration,
            "Uncertainty": f"{calculated_concentration:.3f} ± {uncertainty:.3f}" if calculated_concentration and uncertainty else None,
            "Injection Volume": injection_volume,
            "Result ID": result_id,
            "LIMS Status": lims_status
        })

    result_data_sorted = sorted(
        result_data,
        key=lambda x: ("Std_" in x["Sample Name"], x["Result ID"])
    )

    table_columns = [
        {"name": "Sample Name", "id": "Sample Name"},
        {"name": "Injection Date", "id": "Injection Date"},
        {"name": "System Name", "id": "System Name"},
        {"name": "Dilution Factor", "id": "Dilution Factor"},
        {"name": "Peak Start", "id": "Peak Start", "type": "numeric", "format": {"specifier": ".2f"}},
        {"name": "Peak End", "id": "Peak End", "type": "numeric", "format": {"specifier": ".2f"}},
        {"name": "Main Peak Area", "id": "Main Peak Area", "type": "numeric", "format": {"specifier": ".0f"}},
        {"name": "Concentration (mg/mL)", "id": "Concentration", "type": "numeric", "format": {"specifier": ".3f"}},
        {"name": "Uncertainty", "id": "Uncertainty"},
        {"name": "Injection Volume (µL)", "id": "Injection Volume"},
        {"name": "LIMS Status", "id": "LIMS Status"}
    ]

    return table_columns, result_data_sorted


# Load saved plot settings
@app.callback(
    [Output("channel-radio", "value"),
     Output("plot-type-dropdown", "value")],
    [Input("selected-report", "data")],
    prevent_initial_call=True
)
def load_plot_settings(report_id):
    if not report_id:
        return "channel_1", "plotly"

    try:
        report = Report.objects.get(report_id=report_id)
        if report.plot_settings:
            settings = report.plot_settings
            return (
                settings.get("channel", "channel_1"),
                settings.get("plot_type", "plotly")
            )
    except:
        pass

    return "channel_1", "plotly"


# Export to Excel
@app.callback(
    [Output("download-result-data", "data")],
    [Input("export-button", "n_clicks")],
    [State("result-table", "data"),
     State('selected-report', 'data')],
    prevent_initial_call=True
)
def export_to_xlsx(n_clicks, table_data, selected_report):
    if not table_data:
        return [dash.no_update]

    report = Report.objects.filter(report_id=int(selected_report)).first()

    if not report:
        return [dash.no_update]

    current_date = datetime.now().strftime("%Y%m%d")

    file_name = f"{current_date}-{report.project_id}-{report.report_name}.xlsx"

    df = pd.DataFrame(table_data)

    return [dcc.send_data_frame(df.to_excel, file_name, index=False)]


# Plot time series graph
@app.callback(
    Output("time-series-graph", "figure"),
    [Input("selected-report", "data"),
     Input("channel-radio", "value")],
    [State("selected-report", "data")],
    prevent_initial_call=True
)
def plot_sample_time_series(report_clicks, channel, selected_report):
    """Fetch time series data for samples in the selected report and plot it."""
    report_name = selected_report

    if not report_name:
        return go.Figure()

    report = Report.objects.filter(report_id=report_name).first()

    if not report:
        return go.Figure()

    selected_samples = [s.strip() for s in report.selected_samples.split(",") if s.strip()]

    if not selected_samples:
        return go.Figure()

    non_std_samples = SampleMetadata.objects.filter(
        sample_name__in=selected_samples
    ).exclude(sample_name__contains="Std_").order_by("result_id")

    if not non_std_samples:
        return go.Figure()

    fig = go.Figure()

    channel_labels = {
        'channel_1': 'UV280',
        'channel_2': 'UV260',
        'channel_3': 'Pressure'
    }

    colors = ['#0056b3', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6610f2', '#e83e8c', '#fd7e14']

    for idx, sample in enumerate(non_std_samples):
        result_id = sample.result_id
        sample_name = sample.sample_name

        time_series = TimeSeriesData.objects.filter(result_id=result_id).values("time", channel)

        df = pd.DataFrame(list(time_series))

        if df.empty:
            continue

        fig.add_trace(go.Scatter(
            x=df["time"],
            y=df[channel],
            mode="lines",
            name=sample_name,
            line=dict(width=2, color=colors[idx % len(colors)])
        ))

    fig.update_layout(
        title=f"Time Series Data for Samples - {channel_labels.get(channel, channel)}",
        xaxis_title="Time (min)",
        yaxis_title=channel_labels.get(channel, channel),
        template="plotly_white",
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.01
        )
    )

    return fig