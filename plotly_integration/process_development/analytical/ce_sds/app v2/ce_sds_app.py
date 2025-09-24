# import pandas as pd
# from dash import dcc, html, dash_table
# from django_plotly_dash import DjangoDash
# from plotly_integration.models import (
#     # Keep these for compatibility
#     SampleMetadata, TimeSeriesData  # Unified tables - primary data source
# )
#
# # Import our modular components for backend processing
# from .modules.callbacks import register_callbacks
# from .modules.data_access import get_metadata_from_source
# from .modules.plotting import generate_unified_chromatogram
# from .modules.peak_processing import calculate_baseline
#
# app = DjangoDash("CESDSReportViewerApp")
# app.layout = html.Div([
#     dcc.Location(id='url', refresh=False),
#     dcc.Store(id="selected-result-ids"),
#     dcc.Store(id="reduced-result-ids"),
#     dcc.Store(id="nonreduced-result-ids"),
#     dcc.Store(id="standard-regression-params"),
#     dcc.Store(id="selected-report"),
#
#     dcc.Store(id='url-params', data={}),
#     dcc.Store(id='embedded-mode', data=False),
#     dcc.Interval(id="load-once", interval=1000, n_intervals=0, max_intervals=1),
#
#     dcc.Store(id='button-success-trigger', data=0),
#     dcc.Interval(id='button-reset-interval', interval=5000, n_intervals=0, disabled=True),
#
#     dcc.Store(id="lc-hc-times-store", data={}),
#
#     # Modal for Select Report - keeping existing functionality
#     html.Div(
#         id="report-modal",
#         style={
#             "display": "none",
#             "position": "fixed",
#             "top": "0",
#             "left": "0",
#             "width": "100%",
#             "height": "100%",
#             "backgroundColor": "rgba(0, 0, 0, 0.5)",
#             "zIndex": "1000"
#         },
#         children=[
#             html.Div(
#                 style={
#                     "position": "relative",
#                     "margin": "2% auto",
#                     "width": "90%",
#                     "maxWidth": "1400px",
#                     "height": "85%",
#                     "backgroundColor": "white",
#                     "borderRadius": "10px",
#                     "padding": "20px",
#                     "boxShadow": "0 5px 15px rgba(0,0,0,0.3)",
#                     "display": "flex",
#                     "flexDirection": "column"
#                 },
#                 children=[
#                     html.Button(
#                         "✕",
#                         id="close-report-modal-btn",
#                         style={
#                             "position": "absolute",
#                             "top": "10px",
#                             "right": "10px",
#                             "fontSize": "24px",
#                             "border": "none",
#                             "backgroundColor": "transparent",
#                             "cursor": "pointer",
#                             "color": "#666"
#                         }
#                     ),
#                     html.H3("Report Management",
#                             style={"marginBottom": "20px", "color": "#0056b3", "textAlign": "center"}),
#
#                     # Tabs for Select/Create
#                     dcc.Tabs(
#                         id="report-tabs",
#                         value="select-tab",
#                         children=[
#                             dcc.Tab(
#                                 label="Select Report",
#                                 value="select-tab",
#                                 style={"height": "100%"},
#                                 children=[
#                                     html.Div(
#                                         style={
#                                             "padding": "20px",
#                                             "height": "100%",
#                                             "display": "flex",
#                                             "flexDirection": "column",
#                                             "boxSizing": "border-box"
#                                         },
#                                         children=[
#                                             html.H4("Select an Existing Report",
#                                                     style={'marginBottom': '20px', 'color': '#0056b3'}),
#
#                                             # Table container that grows to fill available space
#                                             html.Div(
#                                                 style={
#                                                     "flexGrow": 1,
#                                                     "marginBottom": "20px",
#                                                     "minHeight": 0
#                                                 },
#                                                 children=[
#                                                     dash_table.DataTable(
#                                                         id='report-selection-table',
#                                                         columns=[
#                                                             {"name": "Report ID", "id": "report_id"},
#                                                             {"name": "Report Name", "id": "report_name"},
#                                                             {"name": "Project ID", "id": "project_id"},
#                                                             {"name": "Created By", "id": "user_id"},
#                                                             {"name": "Date Created", "id": "date_created"},
#                                                         ],
#                                                         data=[],
#                                                         row_selectable="single",
#                                                         selected_rows=[],
#                                                         filter_action="native",
#                                                         sort_action="native",
#                                                         page_action="native",
#                                                         page_size=15,
#                                                         fixed_rows={'headers': True},
#                                                         style_table={
#                                                             'height': '90%',
#                                                             'overflowY': 'auto',
#                                                             'overflowX': 'auto',
#                                                             'borderRadius': '5px'
#                                                         },
#                                                         style_cell={
#                                                             'textAlign': 'center',
#                                                             'padding': '12px',
#                                                             'fontSize': '14px',
#                                                             'fontFamily': 'system-ui, -apple-system, sans-serif'
#                                                         },
#                                                         style_header={
#                                                             'backgroundColor': '#f8f9fa',
#                                                             'fontWeight': '600',
#                                                             'borderBottom': '2px solid #dee2e6'
#                                                         },
#                                                         style_data={
#                                                             'borderBottom': '1px solid #dee2e6'
#                                                         },
#                                                         style_data_conditional=[
#                                                             {
#                                                                 'if': {'row_index': 'odd'},
#                                                                 'backgroundColor': '#f8f9fa'
#                                                             }
#                                                         ]
#                                                     )
#                                                 ]
#                                             ),
#
#                                             # Buttons at the bottom
#                                             html.Div(
#                                                 style={'display': 'flex', 'justifyContent': 'flex-end', 'gap': '10px'},
#                                                 children=[
#                                                     html.Button(
#                                                         "Cancel",
#                                                         id="cancel-select-btn",
#                                                         style={
#                                                             'backgroundColor': '#6c757d',
#                                                             'color': 'white',
#                                                             'padding': '8px 16px',
#                                                             'border': 'none',
#                                                             'borderRadius': '5px',
#                                                             'cursor': 'pointer',
#                                                             'fontSize': '14px',
#                                                             'fontWeight': '500'
#                                                         }
#                                                     ),
#                                                     html.Button(
#                                                         "Confirm Selection",
#                                                         id="confirm-report-selection",
#                                                         style={
#                                                             'backgroundColor': '#0056b3',
#                                                             'color': 'white',
#                                                             'padding': '8px 16px',
#                                                             'border': 'none',
#                                                             'borderRadius': '5px',
#                                                             'cursor': 'pointer',
#                                                             'fontSize': '14px',
#                                                             'fontWeight': '500'
#                                                         }
#                                                     ),
#                                                 ]
#                                             )
#                                         ]
#                                     )
#                                 ]
#                             ),
#                             dcc.Tab(
#                                 label="Create Report",
#                                 value="create-tab",
#                                 children=[
#                                     html.Div(
#                                         style={
#                                             "height": "calc(100vh - 300px)",
#                                             "overflow": "hidden"
#                                         },
#                                         children=[
#                                             html.Iframe(
#                                                 src="/plotly_integration/dash-app/app/CreateCESDSReportApp/",
#                                                 style={
#                                                     "width": "100%",
#                                                     "height": "100%",
#                                                     "border": "none",
#                                                     "display": "block"
#                                                 }
#                                             )
#                                         ]
#                                     )
#                                 ]
#                             )
#                         ]
#                     )
#                 ]
#             )
#         ]
#     ),
#
#     # Modern toolbar with action buttons
#     html.Div(
#         id='toolbar-container',
#         style={
#             'display': 'flex',
#             'justifyContent': 'space-between',
#             'alignItems': 'center',
#             'padding': '20px 30px',
#             'backgroundColor': 'white',
#             'borderRadius': '12px',
#             'margin': '0 30px 30px 30px',
#             'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.08)',
#             'gap': '10px'
#         },
#         children=[
#             # Left side - Create Report button
#             html.Div(
#                 id='left-toolbar',
#                 style={'display': 'flex', 'gap': '20px', 'alignItems': 'center'},
#                 children=[
#                     html.Button([
#                         html.Span("📊 ", style={'marginRight': '5px'}),
#                         "Select/Create Report"
#                     ], id="select-create-report-btn", style={
#                         'backgroundColor': '#0056b3',
#                         'color': 'white',
#                         'border': 'none',
#                         'padding': '12px 24px',
#                         'fontSize': '14px',
#                         'cursor': 'pointer',
#                         'borderRadius': '8px',
#                         'fontWeight': '500',
#                         'transition': 'background-color 0.3s ease'
#                     }),
#                     html.Div([
#                         html.Span("Current Report: ", style={'fontWeight': '600', 'color': '#495057'}),
#                         html.Span("No report selected", id="current-report-text", style={'color': '#6c757d'})
#                     ], style={'marginLeft': '10px', 'fontSize': '15px'})
#                 ]
#             ),
#
#             # Right side - Save buttons
#             html.Div(
#                 style={'display': 'flex', 'gap': '15px'},
#                 children=[
#                     html.Button([
#                         html.Span("💾 ", style={'marginRight': '5px'}),
#                         "Save Report Settings"
#                     ], id="save-settings-btn", style={
#                         'backgroundColor': '#28a745',
#                         'color': 'white',
#                         'border': 'none',
#                         'padding': '12px 24px',
#                         'fontSize': '14px',
#                         'cursor': 'pointer',
#                         'borderRadius': '8px',
#                         'fontWeight': '500',
#                         'transition': 'background-color 0.3s ease'
#                     }),
#                     html.Button([
#                         html.Span("🔗 ", style={'marginRight': '5px'}),
#                         "Report Results"
#                     ], id="report-results-btn", style={
#                         'backgroundColor': '#17a2b8',
#                         'color': 'white',
#                         'border': 'none',
#                         'padding': '12px 24px',
#                         'fontSize': '14px',
#                         'cursor': 'pointer',
#                         'borderRadius': '8px',
#                         'fontWeight': '500',
#                         'transition': 'background-color 0.3s ease'
#                     }),
#                 ]
#             )
#         ]
#     ),
#
#     # Status messages with modern styling
#     html.Div(id="status-message", style={
#         'padding': '16px 24px',
#         'margin': '0 30px 20px 30px',
#         'borderRadius': '8px',
#         'display': 'none',
#         'fontSize': '15px',
#         'fontWeight': '500',
#         'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
#         'transition': 'all 0.3s ease'
#     }),
#
#     # Main content area with modern tabs
#     html.Div(
#         style={
#             'padding': '0 30px 30px 30px',
#         },
#         children=[
#             dcc.Tabs(
#                 id="main-tabs",
#                 value="tab-reduced",
#                 persistence=False,
#                 style={
#                     'borderBottom': 'none',
#                     'marginBottom': '0'
#                 },
#                 children=[
#                     # Reduced Tab - Chromatogram only
#                     dcc.Tab(
#                         label="Reduced",
#                         value="tab-reduced",
#                         style={
#                             'padding': '12px 24px',
#                             'borderRadius': '12px 12px 0 0',
#                             'marginRight': '4px',
#                             'backgroundColor': '#f8f9fa',
#                             'border': 'none',
#                             'fontWeight': '500'
#                         },
#                         selected_style={
#                             'padding': '12px 24px',
#                             'borderRadius': '12px 12px 0 0',
#                             'marginRight': '4px',
#                             'backgroundColor': 'white',
#                             'border': 'none',
#                             'fontWeight': '600',
#                             'color': '#0056b3',
#                             'boxShadow': '0 -2px 10px rgba(0, 0, 0, 0.05)'
#                         },
#                         children=[
#                             html.Div(
#                                 style={
#                                     'background': 'white',
#                                     'borderRadius': '0 12px 12px 12px',
#                                     'padding': '30px',
#                                     'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.08)'
#                                 },
#                                 children=[
#                                     html.Div(style={"display": "flex", "gap": "30px"}, children=[
#                                         # Chromatogram section
#                                         html.Div([
#                                             dcc.Graph(
#                                                 id="reduced-chromatogram",
#                                                 config={
#                                                     'responsive': True,
#                                                     'displayModeBar': True,
#                                                     'displaylogo': False
#                                                 },
#                                                 # style={"height": "800px"},
#                                                 figure={'layout': {'autosize': True}}
#                                             )
#                                         ], style={"flex": "1"}),
#
#                                         # Modern control panel
#                                         html.Div([
#
#                                             html.Div(
#                                                 style={
#                                                     'background': '#f8f9fa',
#                                                     'borderRadius': '12px',
#                                                     'padding': '20px',
#                                                     'marginBottom': '20px'
#                                                 },
#                                                 children=[
#                                                     html.H4("Marker Settings",
#                                                             style={'marginTop': '0', 'color': '#495057'}),
#                                                     html.Label("Marker RT (min):",
#                                                                style={'fontWeight': '500', 'color': '#6c757d'}),
#                                                     dcc.Input(id="marker-rt", type="number", value=7, step=0.1,
#                                                               style={"width": "100%", "marginBottom": "15px",
#                                                                      "borderRadius": "6px",
#                                                                      "border": "1px solid #ced4da", "padding": "8px"}),
#
#                                                     html.Label("Marker Label:",
#                                                                style={'fontWeight': '500', 'color': '#6c757d'}),
#                                                     dcc.Input(id="marker-label", type="text", value="10 kDa",
#                                                               style={"width": "100%", "borderRadius": "6px",
#                                                                      "border": "1px solid #ced4da", "padding": "8px"}),
#                                                 ]
#                                             ),
#
#                                             html.Div(
#                                                 style={
#                                                     'background': '#f8f9fa',
#                                                     'borderRadius': '12px',
#                                                     'padding': '20px',
#                                                     'marginBottom': '20px'
#                                                 },
#                                                 children=[
#                                                     html.H4("Plot Settings",
#                                                             style={'marginTop': '0', 'color': '#495057'}),
#                                                     html.Label("Y-Axis Scaling:",
#                                                                style={'fontWeight': '500', 'color': '#6c757d'}),
#                                                     dcc.Input(id="reduced-y-axis-scaling", type="number", value=1.0,
#                                                               step=0.01,
#                                                               style={"width": "100%", "marginBottom": "15px",
#                                                                      "borderRadius": "6px",
#                                                                      "border": "1px solid #ced4da", "padding": "8px"}),
#
#                                                     html.Label("Subplot Vertical Spacing:",
#                                                                style={'fontWeight': '500', 'color': '#6c757d'}),
#                                                     dcc.Input(id="reduced-subplot-vertical-spacing", type="number",
#                                                               value=0.04, step=0.005,
#                                                               style={"width": "100%", "marginBottom": "15px",
#                                                                      "borderRadius": "6px",
#                                                                      "border": "1px solid #ced4da", "padding": "8px"}),
#
#                                                     html.Label("Display Options:",
#                                                                style={'fontWeight': '500', 'color': '#6c757d'}),
#                                                     dcc.Checklist(
#                                                         id='reduced-show-mw-checklist',
#                                                         options=[
#                                                             {'label': ' Show MW in Annotations', 'value': 'show_mw'}
#                                                         ],
#                                                         value=['show_mw'],
#                                                         style={'marginTop': '5px', 'color': '#495057'}
#                                                     ),
#
#                                                     html.Label("Annotation Positioning:",
#                                                                style={'fontWeight': '500', 'color': '#6c757d',
#                                                                       'marginTop': '15px'}),
#                                                     dcc.Dropdown(
#                                                         id='reduced-annotation-positioning',
#                                                         options=[
#                                                             {'label': 'Fixed Offset', 'value': 'fixed'},
#                                                             {'label': 'Combined Mode (30s, <5% area)', 'value': 'combined'},
#                                                             {'label': 'Vertical Text Mode', 'value': 'vertical'},
#                                                             {'label': 'Height Offset Mode', 'value': 'height_offset'}
#                                                         ],
#                                                         value='fixed',
#                                                         style={'marginTop': '5px'}
#                                                     ),
#                                                 ]
#                                             ),
#
#                                             html.Div(
#                                                 style={
#                                                     'background': '#e3f2fd',
#                                                     'borderRadius': '12px',
#                                                     'padding': '20px'
#                                                 },
#                                                 children=[
#                                                     html.H4("Light Chain Timing",
#                                                             style={'marginTop': '0', 'color': '#1976d2'}),
#                                                     html.Button("Calculate Light Chain Time", id="calc-light-chain-btn",
#                                                                 style={
#                                                                     "width": "100%",
#                                                                     "marginBottom": "15px",
#                                                                     "backgroundColor": "#1976d2",
#                                                                     "color": "white",
#                                                                     "border": "none",
#                                                                     "padding": "10px",
#                                                                     "borderRadius": "6px",
#                                                                     "fontWeight": "500",
#                                                                     "cursor": "pointer",
#                                                                     "transition": "background-color 0.3s ease"
#                                                                 }),
#                                                     dcc.Input(id="light-chain-time", type="number",
#                                                               placeholder="Light Chain Time (min)",
#                                                               readOnly=True,
#                                                               style={"width": "100%", "borderRadius": "6px",
#                                                                      "border": "1px solid #90caf9", "padding": "8px",
#                                                                      "backgroundColor": "white"})
#                                                 ]
#                                             ),
#                                         ], style={"width": "300px", "flexShrink": "0"})
#                                     ])
#                                 ]
#                             )
#                         ]
#                     ),
#
#                     # Non-Reduced Tab - Chromatogram only
#                     dcc.Tab(
#                         label="Non-Reduced",
#                         value="tab-nonreduced",
#                         style={
#                             'padding': '12px 24px',
#                             'borderRadius': '12px 12px 0 0',
#                             'marginRight': '4px',
#                             'backgroundColor': '#f8f9fa',
#                             'border': 'none',
#                             'fontWeight': '500'
#                         },
#                         selected_style={
#                             'padding': '12px 24px',
#                             'borderRadius': '12px 12px 0 0',
#                             'marginRight': '4px',
#                             'backgroundColor': 'white',
#                             'border': 'none',
#                             'fontWeight': '600',
#                             'color': '#0056b3',
#                             'boxShadow': '0 -2px 10px rgba(0, 0, 0, 0.05)'
#                         },
#                         children=[
#                             html.Div(
#                                 style={
#                                     'background': 'white',
#                                     'borderRadius': '0 12px 12px 12px',
#                                     'padding': '30px',
#                                     'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.08)'
#                                 },
#                                 children=[
#                                     html.Div(style={"display": "flex", "gap": "30px"}, children=[
#                                         # Chromatogram section
#                                         html.Div([
#                                             dcc.Graph(
#                                                 id="nonreduced-chromatogram",
#                                                 config={
#                                                     'responsive': True,
#                                                     'displayModeBar': True,
#                                                     'displaylogo': False
#                                                 },
#                                                 style={"height": "800px"},
#                                                 figure={'layout': {'autosize': True}}
#                                             )
#                                         ], style={"flex": "1"}),
#
#                                         # Modern control panel for non-reduced
#                                         html.Div([
#
#                                             html.Div(
#                                                 style={
#                                                     'background': '#f8f9fa',
#                                                     'borderRadius': '12px',
#                                                     'padding': '20px',
#                                                     'marginBottom': '20px'
#                                                 },
#                                                 children=[
#                                                     html.H4("Marker Settings",
#                                                             style={'marginTop': '0', 'color': '#495057'}),
#                                                     html.Label("Marker RT (min):",
#                                                                style={'fontWeight': '500', 'color': '#6c757d'}),
#                                                     dcc.Input(id="nr-marker-rt", type="number", value=7, step=0.1,
#                                                               style={"width": "100%", "marginBottom": "15px",
#                                                                      "borderRadius": "6px",
#                                                                      "border": "1px solid #ced4da", "padding": "8px"}),
#
#                                                     html.Label("Marker Label:",
#                                                                style={'fontWeight': '500', 'color': '#6c757d'}),
#                                                     dcc.Input(id="nr-marker-label", type="text", value="10 kDa",
#                                                               style={"width": "100%", "borderRadius": "6px",
#                                                                      "border": "1px solid #ced4da", "padding": "8px"}),
#                                                 ]
#                                             ),
#
#                                             html.Div(
#                                                 style={
#                                                     'background': '#f8f9fa',
#                                                     'borderRadius': '12px',
#                                                     'padding': '20px',
#                                                     'marginBottom': '20px'
#                                                 },
#                                                 children=[
#                                                     html.H4("Plot Settings",
#                                                             style={'marginTop': '0', 'color': '#495057'}),
#                                                     html.Label("Y-Axis Scaling:",
#                                                                style={'fontWeight': '500', 'color': '#6c757d'}),
#                                                     dcc.Input(id="non-reduced-y-axis-scaling", type="number", value=1.0,
#                                                               step=0.01,
#                                                               style={"width": "100%", "marginBottom": "15px",
#                                                                      "borderRadius": "6px",
#                                                                      "border": "1px solid #ced4da", "padding": "8px"}),
#
#                                                     html.Label("Subplot Vertical Spacing:",
#                                                                style={'fontWeight': '500', 'color': '#6c757d'}),
#                                                     dcc.Input(id="non-reduced-subplot-vertical-spacing", type="number",
#                                                               value=0.04, step=0.005,
#                                                               style={"width": "100%", "marginBottom": "15px",
#                                                                      "borderRadius": "6px",
#                                                                      "border": "1px solid #ced4da", "padding": "8px"}),
#
#                                                     html.Label("Display Options:",
#                                                                style={'fontWeight': '500', 'color': '#6c757d'}),
#                                                     dcc.Checklist(
#                                                         id='nonreduced-show-mw-checklist',
#                                                         options=[
#                                                             {'label': ' Show MW in Annotations', 'value': 'show_mw'}
#                                                         ],
#                                                         value=['show_mw'],
#                                                         style={'marginTop': '5px', 'color': '#495057'}
#                                                     ),
#
#                                                     html.Label("Annotation Positioning:",
#                                                                style={'fontWeight': '500', 'color': '#6c757d',
#                                                                       'marginTop': '15px'}),
#                                                     dcc.Dropdown(
#                                                         id='nonreduced-annotation-positioning',
#                                                         options=[
#                                                             {'label': 'Fixed Offset', 'value': 'fixed'},
#                                                             {'label': 'Combined Mode (30s, <5% area)', 'value': 'combined'},
#                                                             {'label': 'Vertical Text Mode', 'value': 'vertical'},
#                                                             {'label': 'Height Offset Mode', 'value': 'height_offset'}
#                                                         ],
#                                                         value='fixed',
#                                                         style={'marginTop': '5px'}
#                                                     ),
#                                                 ]
#                                             ),
#
#                                         ], style={"width": "300px", "flexShrink": "0"})
#                                     ])
#                                 ]
#                             )
#                         ]
#                     ),
#
#                     # Standard Analysis Tab with modern styling
#                     dcc.Tab(
#                         label="Standard Analysis",
#                         value="tab-std-analysis",
#                         style={
#                             'padding': '12px 24px',
#                             'borderRadius': '12px 12px 0 0',
#                             'marginRight': '4px',
#                             'backgroundColor': '#f8f9fa',
#                             'border': 'none',
#                             'fontWeight': '500'
#                         },
#                         selected_style={
#                             'padding': '12px 24px',
#                             'borderRadius': '12px 12px 0 0',
#                             'marginRight': '4px',
#                             'backgroundColor': 'white',
#                             'border': 'none',
#                             'fontWeight': '600',
#                             'color': '#0056b3',
#                             'boxShadow': '0 -2px 10px rgba(0, 0, 0, 0.05)'
#                         },
#                         children=[
#                             html.Div(
#                                 style={
#                                     'background': 'white',
#                                     'borderRadius': '0 12px 12px 12px',
#                                     'padding': '30px',
#                                     'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.08)'
#                                 },
#                                 children=[
#                                     html.H3("Standard Analysis",
#                                             style={'textAlign': 'center', 'color': '#0056b3', 'marginBottom': '30px'}),
#
#                                     html.Div([
#                                         html.Label("Select Standard Sample ID:",
#                                                    style={'color': '#495057', 'fontWeight': '500',
#                                                           'marginBottom': '10px', 'display': 'block'}),
#                                         dcc.Dropdown(
#                                             id='standard-id-dropdown',
#                                             placeholder="Select a Standard Sample",
#                                             style={'width': '100%', 'borderRadius': '8px'}
#                                         )
#                                     ], style={'marginBottom': '30px'}),
#
#                                     dcc.Graph(id='standard-peak-plot'),
#
#                                     html.Div([
#                                         html.P("Regression Equation: ", id="regression-equation",
#                                                style={'fontWeight': '500'}),
#                                         html.P("R² Value: ", id="r-squared-value", style={'fontWeight': '500'}),
#                                         html.P("Estimated MW for RT: ", id="estimated-mw", style={'fontWeight': '500'}),
#
#                                         html.Div(style={'display': 'flex', 'gap': '15px', 'marginTop': '20px'},
#                                                  children=[
#                                                      dcc.Input(
#                                                          id="rt-input",
#                                                          type="number",
#                                                          placeholder="Enter Retention Time",
#                                                          style={'flex': '1', 'padding': '10px', 'borderRadius': '6px',
#                                                                 'border': '1px solid #ced4da'}
#                                                      ),
#                                                      html.Button("Calculate MW", id="calculate-mw-button", style={
#                                                          'backgroundColor': '#0056b3',
#                                                          'color': 'white',
#                                                          'border': 'none',
#                                                          'padding': '10px 20px',
#                                                          'cursor': 'pointer',
#                                                          'borderRadius': '6px',
#                                                          'fontWeight': '500',
#                                                          'transition': 'background-color 0.3s ease'
#                                                      }),
#                                                  ]),
#                                         dcc.Graph(id='regression-plot', style={'marginTop': '20px'})
#                                     ], style={
#                                         'marginTop': '30px',
#                                         'padding': '25px',
#                                         'border': '1px solid #e3f2fd',
#                                         'borderRadius': '12px',
#                                         'backgroundColor': '#f8fbff',
#                                     }),
#
#                                     html.Div([
#                                         html.H4("Detected Peaks & Assigned MWs",
#                                                 style={'color': '#0056b3', 'marginBottom': '20px'}),
#                                         html.Div(style={'display': 'flex', 'alignItems': 'center', 'gap': '15px',
#                                                         'marginBottom': '20px'}, children=[
#                                             html.Label("Number of Peaks to Use:",
#                                                        style={'fontWeight': '500', 'color': '#495057'}),
#                                             dcc.Input(
#                                                 id="num-std-peaks",
#                                                 type="number",
#                                                 value=7,
#                                                 min=1,
#                                                 max=20,
#                                                 step=1,
#                                                 style={'width': '100px', 'padding': '8px', 'borderRadius': '6px',
#                                                        'border': '1px solid #ced4da'}
#                                             ),
#                                         ]),
#                                         dash_table.DataTable(
#                                             id="std-detected-peak-table",
#                                             columns=[
#                                                 {"name": "Retention Time (min)", "id": "peak_rt", "type": "numeric"},
#                                                 {"name": "Peak Height", "id": "peak_height", "type": "numeric"},
#                                                 {"name": "Assigned MW (kDa)", "id": "assigned_mw", "type": "numeric",
#                                                  "editable": True}
#                                             ],
#                                             data=[],
#                                             editable=True,
#                                             row_selectable="multi",
#                                             style_table={'overflowX': 'auto', 'borderRadius': '8px'},
#                                             style_cell={'textAlign': 'center', 'padding': '12px'},
#                                             style_header={
#                                                 'fontWeight': '600',
#                                                 'backgroundColor': '#f8f9fa',
#                                                 'borderBottom': '2px solid #dee2e6'
#                                             },
#                                             style_data_conditional=[
#                                                 {
#                                                     'if': {'row_index': 'odd'},
#                                                     'backgroundColor': '#f8f9fa'
#                                                 }
#                                             ]
#                                         )
#                                     ], style={
#                                         'marginTop': '30px',
#                                         'padding': '25px',
#                                         'border': '1px solid #e3f2fd',
#                                         'borderRadius': '12px',
#                                         'backgroundColor': '#f8fbff'
#                                     })
#                                 ]
#                             )
#                         ]
#                     ),
#
#                     # NEW: Results Tables Tab
#                     dcc.Tab(
#                         label="Results Tables",
#                         value="tab-results",
#                         style={
#                             'padding': '12px 24px',
#                             'borderRadius': '12px 12px 0 0',
#                             'marginRight': '4px',
#                             'backgroundColor': '#f8f9fa',
#                             'border': 'none',
#                             'fontWeight': '500'
#                         },
#                         selected_style={
#                             'padding': '12px 24px',
#                             'borderRadius': '12px 12px 0 0',
#                             'marginRight': '4px',
#                             'backgroundColor': 'white',
#                             'border': 'none',
#                             'fontWeight': '600',
#                             'color': '#0056b3',
#                             'boxShadow': '0 -2px 10px rgba(0, 0, 0, 0.05)'
#                         },
#                         children=[
#                             html.Div(
#                                 style={
#                                     'background': 'white',
#                                     'borderRadius': '0 12px 12px 12px',
#                                     'padding': '30px',
#                                     'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.08)'
#                                 },
#                                 children=[
#                                     # Reduced Results Section
#                                     html.Div(
#                                         style={
#                                             'marginBottom': '40px'
#                                         },
#                                         children=[
#                                             html.Div(
#                                                 style={
#                                                     'display': 'flex',
#                                                     'justifyContent': 'space-between',
#                                                     'alignItems': 'center',
#                                                     'marginBottom': '20px',
#                                                     'paddingBottom': '15px',
#                                                     'borderBottom': '2px solid #e9ecef'
#                                                 },
#                                                 children=[
#                                                     html.H3("Reduced Results",
#                                                             style={
#                                                                 'color': '#0056b3',
#                                                                 'margin': '0',
#                                                                 'fontWeight': '500'
#                                                             }),
#                                                     html.Button(
#                                                         "Export Reduced Table",
#                                                         id="export-reduced-btn",
#                                                         style={
#                                                             'padding': '8px 20px',
#                                                             'backgroundColor': '#17a2b8',
#                                                             'border': 'none',
#                                                             'borderRadius': '6px',
#                                                             'color': 'white',
#                                                             'fontWeight': '500',
#                                                             'cursor': 'pointer',
#                                                             'transition': 'background-color 0.3s ease'
#                                                         }
#                                                     )
#                                                 ]
#                                             ),
#                                             dash_table.DataTable(
#                                                 id="reduced-table",
#                                                 columns=[],
#                                                 data=[],
#                                                 style_header={
#                                                     'backgroundColor': '#f8f9fa',
#                                                     'fontWeight': '600',
#                                                     'textAlign': 'center',
#                                                     'borderBottom': '2px solid #dee2e6',
#                                                     'padding': '12px'
#                                                 },
#                                                 style_table={
#                                                     'overflowX': 'auto',
#                                                     'borderRadius': '8px',
#                                                     'border': '1px solid #dee2e6'
#                                                 },
#                                                 style_cell={
#                                                     'textAlign': 'center',
#                                                     'padding': '12px',
#                                                     'borderRight': '1px solid #e9ecef'
#                                                 },
#                                                 style_data_conditional=[
#                                                     {
#                                                         'if': {'row_index': 'odd'},
#                                                         'backgroundColor': '#f8f9fa'
#                                                     }
#                                                 ]
#                                             ),
#                                             dcc.Download(id="download-reduced-xlsx")
#                                         ]
#                                     ),
#
#                                     # Non-Reduced Results Section
#                                     html.Div([
#                                         html.Div(
#                                             style={
#                                                 'display': 'flex',
#                                                 'justifyContent': 'space-between',
#                                                 'alignItems': 'center',
#                                                 'marginBottom': '20px',
#                                                 'paddingBottom': '15px',
#                                                 'borderBottom': '2px solid #e9ecef'
#                                             },
#                                             children=[
#                                                 html.H3("Non-Reduced Results",
#                                                         style={
#                                                             'color': '#0056b3',
#                                                             'margin': '0',
#                                                             'fontWeight': '500'
#                                                         }),
#                                                 html.Button(
#                                                     "Export Non-Reduced Table",
#                                                     id="export-nonreduced-btn",
#                                                     style={
#                                                         'padding': '8px 20px',
#                                                         'backgroundColor': '#17a2b8',
#                                                         'border': 'none',
#                                                         'borderRadius': '6px',
#                                                         'color': 'white',
#                                                         'fontWeight': '500',
#                                                         'cursor': 'pointer',
#                                                         'transition': 'background-color 0.3s ease'
#                                                     }
#                                                 )
#                                             ]
#                                         ),
#                                         dash_table.DataTable(
#                                             id="nonreduced-table",
#                                             columns=[],
#                                             data=[],
#                                             style_header={
#                                                 'backgroundColor': '#f8f9fa',
#                                                 'fontWeight': '600',
#                                                 'textAlign': 'center',
#                                                 'borderBottom': '2px solid #dee2e6',
#                                                 'padding': '12px'
#                                             },
#                                             style_table={
#                                                 'overflowX': 'auto',
#                                                 'borderRadius': '8px',
#                                                 'border': '1px solid #dee2e6'
#                                             },
#                                             style_cell={
#                                                 'textAlign': 'center',
#                                                 'padding': '12px',
#                                                 'borderRight': '1px solid #e9ecef'
#                                             },
#                                             style_data_conditional=[
#                                                 {
#                                                     'if': {'row_index': 'odd'},
#                                                     'backgroundColor': '#f8f9fa'
#                                                 }
#                                             ]
#                                         ),
#                                         dcc.Download(id="download-nonreduced-xlsx")
#                                     ])
#                                 ]
#                             )
#                         ]
#                     ),
#                 ]
#             )
#         ]
#     )
# ])
#
#
# # ==================== Helper Functions for Data Fetching ====================
#
# def get_metadata_from_source(result_ids):
#     """
#     Fetch metadata from unified tables
#
#     Args:
#         result_ids: List of result IDs to fetch
#
#     Returns:
#         List of metadata objects
#     """
#     # Always use unified tables - filter by analysis_type=3 for CE-SDS
#     metas = SampleMetadata.objects.filter(
#         result_id__in=result_ids,
#         analysis_type=3  # CE-SDS
#     )
#     # Convert to have consistent attributes for compatibility
#     converted_metas = []
#     for m in metas:
#         # Create a simple object with attributes matching legacy structure
#         class MetaObj:
#             def __init__(self, unified_meta):
#                 self.id = unified_meta.result_id  # Use result_id as ID
#                 self.result_id = unified_meta.result_id
#                 self.sample_id_full = unified_meta.sample_name
#                 self.sample_prefix = unified_meta.sample_prefix
#                 self.sample_name = unified_meta.sample_name
#                 self.date_acquired = unified_meta.date_acquired
#                 self.sample_set_name = unified_meta.sample_set_name
#
#         converted_metas.append(MetaObj(m))
#     return converted_metas
#
#
# def get_timeseries_data(result_id):
#     """
#     Fetch time series data from unified tables
#
#     Args:
#         result_id: The result ID
#
#     Returns:
#         DataFrame with time_min and channel_1 columns
#     """
#     # Always use unified tables
#     qs = TimeSeriesData.objects.filter(
#         result_id=result_id,
#         system_name__icontains='CE'  # Filter for CE-SDS data
#     ).values('time', 'channel_1')
#     df = pd.DataFrame(list(qs))
#     if not df.empty:
#         # Rename 'time' to 'time_min' for consistency
#         df = df.rename(columns={'time': 'time_min'})
#         # Scale channel_1 by 1,000,000 to convert from base units to micro units (match peak results)
#         df['channel_1'] = df['channel_1'] * 1_000_000
#         print(f"[DEBUG] Scaled {len(df)} time series data points by 1M for result_id {result_id}")
#
#     return df
#
#
# def get_peak_results(result_id, integration_method='manual'):
#     """
#     Get peak results either from database (Empower) or through manual detection
#
#     Args:
#         result_id: The result ID
#         integration_method: 'empower' or 'manual'
#
#     Returns:
#         List of peak dictionaries with retention_time, area, height, etc.
#     """
#     if integration_method == 'empower':
#         # Fetch from PeakResults table - keeping original functions but will use modular backend
#
# # ============================================================================
# # REGISTER MODULAR CALLBACKS - All callback logic is now in the modules
# # ============================================================================
#
# register_callbacks(app)
