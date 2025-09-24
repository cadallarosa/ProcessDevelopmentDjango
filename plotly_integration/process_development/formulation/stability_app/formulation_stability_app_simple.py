# """
# Formulation Data Management App
# Modern interface for managing formulation stability data
# """
#
# import dash
# from dash import dcc, html, Input, Output, State, callback_context, dash_table, no_update
# from django_plotly_dash import DjangoDash
# import dash_bootstrap_components as dbc
# import pandas as pd
# import json
# import plotly.graph_objects as go
# import plotly.express as px
# from plotly.subplots import make_subplots
# import numpy as np
# from scipy import stats
#
# # from plotly_integration.models import FormulationData
#
# app = DjangoDash("FormulationStabilityApp", external_stylesheets=[
#     dbc.themes.BOOTSTRAP,
#     "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
# ], suppress_callback_exceptions=True)
#
# def get_experiments():
#     """Get all available experiments using the property"""
#     try:
#         experiments = set()
#         for sample in FormulationData.objects.all():
#             experiments.add(sample.experiment_id)
#         return [{'label': exp, 'value': exp} for exp in sorted(list(experiments))]
#     except Exception as e:
#         print(f"Error fetching experiments: {e}")
#         return []
#
# COLOR_PALETTE = {
#     "primary": "#2E86C1",
#     "secondary": "#E74C3C",
#     "success": "#27AE60",
#     "warning": "#F39C12",
#     "info": "#8E44AD",
#     "light": "#F8F9FA",
#     "dark": "#2C3E50",
#     "background": "#FFFFFF",
# }
#
# MODERN_STYLE = {
#     "font_family": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
#     "card_shadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
#     "border_radius": "8px"
# }
#
#
#
#
# # Define columns exactly matching Excel structure
# COLUMNS = [
#     {"name": "Sample Number", "id": "sample_number", "editable": False, "type": "text"},
#     {"name": "Buffer", "id": "buffer", "editable": True, "type": "text"},
#     {"name": "pH", "id": "ph", "editable": True, "type": "numeric", "format": {"specifier": ".2f"}},
#     {"name": "Excipients", "id": "excipients", "editable": True, "type": "text"},
#     {"name": "Formulation", "id": "formulation", "editable": True, "type": "text"},
#     {"name": "Condition", "id": "condition", "editable": True, "type": "text"},
#     {"name": "Pull Day", "id": "pull_day", "editable": True, "type": "numeric"},
#     {"name": "Time Point (months)", "id": "time_point_months", "editable": True, "type": "numeric", "format": {"specifier": ".1f"}},
#     {"name": "Appearance", "id": "appearance", "editable": True, "type": "text"},
#     {"name": "Concentration (mg/mL)", "id": "concentration", "editable": True, "type": "numeric", "format": {"specifier": ".2f"}},
#     {"name": "pH (measured)", "id": "ph_measured", "editable": True, "type": "numeric", "format": {"specifier": ".2f"}},
#     {"name": "Result ID", "id": "result_id", "editable": True, "type": "text"},
#     {"name": "HMW", "id": "hmw", "editable": True, "type": "numeric", "format": {"specifier": ".2f"}},
#     {"name": "Main", "id": "main", "editable": True, "type": "numeric", "format": {"specifier": ".2f"}},
#     {"name": "LMW", "id": "lmw", "editable": True, "type": "numeric", "format": {"specifier": ".2f"}},
#     {"name": "Total Area", "id": "total_area", "editable": True, "type": "numeric"},
#     {"name": "Osmolality (mOsm/kg)", "id": "osmolality", "editable": True, "type": "numeric"},
#     {"name": "Tm (°C)", "id": "tm_celsius", "editable": True, "type": "numeric", "format": {"specifier": ".1f"}},
#     {"name": "Scattering Onset", "id": "scattering_onset", "editable": True, "type": "numeric", "format": {"specifier": ".1f"}},
# ]
#
# # Main Layout
# app.layout = dbc.Container([
#     dcc.Store(id='original-data-store'),
#     dcc.Store(id='has-changes-store', data=False),
#     dcc.Store(id='table-ready-store', data=False),
#
#     # Interval component to manage initial loading sequence
#     dcc.Interval(
#         id='init-interval',
#         interval=500,  # 500ms intervals
#         n_intervals=0,
#         max_intervals=1  # Only run once
#     ),
#
#     # Header section
#     html.Div(),  # Empty header
#
#     # Controls section
#     html.Div([
#         dbc.Row([
#             dbc.Col([
#                 dbc.Label("Select Experiment:", className="fw-bold"),
#                 dcc.Dropdown(
#                     id="experiment-dropdown",
#                     options=get_experiments(),
#                     value="FD-003",  # Default to FD-003
#                     placeholder="Choose experiment...",
#                     clearable=False,
#                     style={"fontFamily": MODERN_STYLE["font_family"]}
#                 )
#             ], width=4),
#             dbc.Col([
#                 html.Div(id="save-status", className="mt-2")
#             ], width=8)
#         ])
#     ], className="mb-4"),
#
#     # Main tabs
#     html.Div([
#         dcc.Tabs(
#             id="main-tabs",
#             value="data-tab",
#             style={
#                 'borderBottom': '2px solid #e2e8f0',
#                 'marginBottom': '24px',
#                 'backgroundColor': 'white',
#                 'borderRadius': '12px 12px 0 0',
#                 'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
#             },
#         children=[
#             dcc.Tab(
#                 label="Data Table",
#                 value="data-tab",
#                 style={
#                     'padding': '16px 28px',
#                     'borderBottom': '3px solid transparent',
#                     'fontWeight': '600',
#                     'color': '#6b7280',
#                     'fontSize': '15px',
#                     'transition': 'all 0.2s ease',
#                     'borderRadius': '8px 8px 0 0'
#                 },
#                 selected_style={
#                     'borderTop': 'none',
#                     'borderLeft': 'none',
#                     'borderRight': 'none',
#                     'borderBottom': '3px solid #2563eb',
#                     'backgroundColor': 'white',
#                     'color': '#2563eb',
#                     'fontWeight': '700',
#                     'borderRadius': '8px 8px 0 0',
#                     'boxShadow': '0 -2px 8px rgba(37, 99, 235, 0.1)'
#                 },
#                 children=[
#                     # Data table tab content
#                     html.Div([
#                         dbc.Row([
#                             dbc.Col([
#                                 dbc.Button([
#                                     html.I(className="fas fa-save me-2"),
#                                     "Save Changes"
#                                 ], id="save-btn", color="success", disabled=True, className="me-2"),
#                                 html.Br(),
#                                 html.Small("Changes are automatically detected", className="text-muted")
#                             ], width=3),
#                             dbc.Col([
#                                 dbc.Label("Filter by Formulation:", className="fw-bold mb-1"),
#                                 dcc.Dropdown(
#                                     id="data-formulation-filter",
#                                     options=[],
#                                     value=None,
#                                     placeholder="All formulations",
#                                     clearable=True,
#                                     multi=True
#                                 )
#                             ], width=4),
#                             dbc.Col([
#                                 dbc.Label("Filter by Condition:", className="fw-bold mb-1"),
#                                 dcc.Dropdown(
#                                     id="data-condition-filter",
#                                     options=[],
#                                     value=None,
#                                     placeholder="All conditions",
#                                     clearable=True,
#                                     multi=True
#                                 )
#                             ], width=3)
#                         ], className="mb-3"),
#                         dash_table.DataTable(
#                             id="data-table",
#                             columns=COLUMNS,
#                             data=[],
#                             editable=True,
#                             row_deletable=True,
#                             style_table={'overflowY': 'auto', 'height': 'calc(100vh - 400px)'},
#                             style_cell={
#                                 'textAlign': 'left',
#                                 'fontSize': 12,
#                                 'fontFamily': 'system-ui, -apple-system, sans-serif',
#                                 'padding': '8px',
#                                 'whiteSpace': 'normal',
#                                 'height': 'auto',
#                                 'minWidth': '100px',
#                                 'maxWidth': '200px',
#                                 'border': '1px solid #dee2e6'
#                             },
#                             style_header={
#                                 'backgroundColor': '#007bff',
#                                 'color': 'white',
#                                 'fontWeight': 'bold',
#                                 'textAlign': 'center',
#                                 'border': '1px solid #dee2e6'
#                             },
#                             style_data_conditional=[
#                                 {
#                                     'if': {'row_index': 'odd'},
#                                     'backgroundColor': '#f8f9fa'
#                                 },
#                                 {
#                                     'if': {'column_id': 'sample_number'},
#                                     'backgroundColor': '#e3f2fd',
#                                     'fontWeight': 'bold'
#                                 },
#                                 {
#                                     'if': {'state': 'selected'},
#                                     'backgroundColor': '#d1ecf1',
#                                     'border': '1px solid #bee5eb'
#                                 }
#                             ],
#                             sort_action="native",
#                             filter_action="native",
#                             export_format="xlsx",
#                             export_headers="display",
#                             fill_width=True,
#                             fixed_rows={'headers': True}
#                         )
#                     ])
#                 ]
#             ),
#             dcc.Tab(
#                 label="Stability Analysis",
#                 value="graphs-tab",
#                 style={
#                     'padding': '16px 28px',
#                     'borderBottom': '3px solid transparent',
#                     'fontWeight': '600',
#                     'color': '#6b7280',
#                     'fontSize': '15px',
#                     'transition': 'all 0.2s ease',
#                     'borderRadius': '8px 8px 0 0'
#                 },
#                 selected_style={
#                     'borderTop': 'none',
#                     'borderLeft': 'none',
#                     'borderRight': 'none',
#                     'borderBottom': '3px solid #2563eb',
#                     'backgroundColor': 'white',
#                     'color': '#2563eb',
#                     'fontWeight': '700',
#                     'borderRadius': '8px 8px 0 0',
#                     'boxShadow': '0 -2px 8px rgba(37, 99, 235, 0.1)'
#                 },
#                 children=[
#                     # Graphs tab content
#                     html.Div([
#                         # Plot area with fixed width calculation
#                         html.Div(
#                             id='plot-area',
#                             children=[
#                                 dcc.Graph(
#                                     id='time-series-graph',
#                                     figure=go.Figure(
#                                         data=[go.Scatter(x=[], y=[], mode='lines')],
#                                         layout=go.Layout(
#                                             title="Formulation Stability Analysis",
#                                             xaxis_title="Time (months)",
#                                             yaxis_title="Value",
#                                             height=600,
#                                             dragmode="select"
#                                         )
#                                     ),
#                                     config={
#                                         'toImageButtonOptions': {'filename': 'formulation_results'},
#                                         'edits': {"annotationPosition": True}
#                                     }
#                                 ),
#                             ],
#                             style={
#                                 'flex': '1',
#                                 'minWidth': '0',
#                                 'padding': '24px',
#                                 'border': '1px solid #e5e7eb',
#                                 'borderRadius': '16px',
#                                 'backgroundColor': 'white',
#                                 'boxShadow': '0 10px 25px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)',
#                                 'marginBottom': '16px',
#                                 'transition': 'all 0.3s ease',
#                                 'position': 'relative',
#                                 'overflow': 'hidden',
#                                 'minHeight': '500px'
#                             }
#                         ),
#
#                         # Settings panel with fixed width
#                         html.Div([
#                             dbc.Card([
#                                 dbc.CardHeader([
#                                     html.H6([
#                                         html.I(className="fas fa-sliders-h me-2"),
#                                         "Graph Controls"
#                                     ], className="mb-0")
#                                 ]),
#                                 dbc.CardBody([
#                                     html.Div([
#                                         dbc.Label("Y-Axis Variable:", className="fw-bold"),
#                                         dcc.Dropdown(
#                                             id="y-axis-selector",
#                                             options=[
#                                                 {"label": "HMW %", "value": "hmw"},
#                                                 {"label": "Main %", "value": "main"},
#                                                 {"label": "LMW %", "value": "lmw"},
#                                                 {"label": "Concentration (mg/mL)", "value": "concentration"},
#                                                 {"label": "pH (measured)", "value": "ph_measured"},
#                                                 {"label": "Total Area", "value": "total_area"},
#                                                 {"label": "Tm (°C)", "value": "tm_celsius"},
#                                                 {"label": "Osmolality", "value": "osmolality"}
#                                             ],
#                                             value="hmw",
#                                             clearable=False
#                                         )
#                                     ], className="mb-3"),
#
#                                     html.Div([
#                                         dbc.Label("Storage Condition:", className="fw-bold"),
#                                         dcc.Dropdown(
#                                             id="storage-condition-filter",
#                                             options=[
#                                                 {"label": "All Conditions", "value": "all"},
#                                                 {"label": "25°C Only", "value": "25°C"},
#                                                 {"label": "40°C Only", "value": "40°C"},
#                                                 {"label": "4°C Only", "value": "4°C"},
#                                                 {"label": "-80°C Only", "value": "-80°C"}
#                                             ],
#                                             value="all",
#                                             clearable=False
#                                         )
#                                     ], className="mb-3"),
#
#                                     html.Div([
#                                         dbc.Label("Select Formulations:", className="fw-bold"),
#                                         dcc.Dropdown(
#                                             id="formulation-selector",
#                                             options=[],
#                                             value=[],
#                                             multi=True,
#                                             placeholder="All formulations"
#                                         )
#                                     ], className="mb-3"),
#
#                                     html.Hr(),
#
#                                     html.Div([
#                                         dbc.Label("Plots per Row:", className="fw-bold"),
#                                         dcc.Dropdown(
#                                             id="plots-per-row",
#                                             options=[
#                                                 {"label": "1", "value": 1},
#                                                 {"label": "2", "value": 2},
#                                                 {"label": "3", "value": 3},
#                                                 {"label": "4", "value": 4}
#                                             ],
#                                             value=2,
#                                             clearable=False
#                                         )
#                                     ], className="mb-3"),
#
#                                     html.Div([
#                                         dbc.Label("Plot Height (pixels):", className="fw-bold"),
#                                         dcc.Input(
#                                             id="plot-height-input",
#                                             type="number",
#                                             value=600,
#                                             min=200,
#                                             max=800,
#                                             step=50,
#                                             className="form-control"
#                                         )
#                                     ], className="mb-3"),
#
#                                     html.Div([
#                                         dbc.Label("Statistics Display:", className="fw-bold"),
#                                         dcc.Checklist(
#                                             id='statistics-checklist',
#                                             options=[
#                                                 {'label': 'Show R² Values', 'value': 'show_r2'},
#                                                 {'label': 'Show Slope Values', 'value': 'show_slope'}
#                                             ],
#                                             value=['show_r2'],
#                                             style={'marginBottom': '15px'}
#                                         )
#                                     ], className="mb-3"),
#                                 ])
#                             ], style={
#                                 'padding': '24px',
#                                 'backgroundColor': 'white',
#                                 'border': '1px solid #e5e7eb',
#                                 'borderRadius': '16px',
#                                 'boxShadow': '0 10px 25px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)',
#                                 'height': 'fit-content',
#                                 'transition': 'all 0.3s ease',
#                                 'position': 'sticky',
#                                 'top': '20px'
#                             })
#                         ], style={
#                             'width': '300px',
#                             'flexShrink': '0',
#                             'height': 'fit-content',
#                             'transition': 'all 0.3s ease',
#                             'position': 'relative'
#                         })
#                     ], style={
#                         'display': 'flex',
#                         'flexDirection': 'row',
#                         'gap': '24px',
#                         'width': '100%',
#                         'boxSizing': 'border-box',
#                         'alignItems': 'flex-start'
#                     })
#                 ]
#             )
#         ]
#     )], style={
#         'height': 'calc(100vh - 200px)',
#         'display': 'flex',
#         'flexDirection': 'column'
#     }),
#
#
#     dcc.Loading(
#         id="loading",
#         children=html.Div(id="loading-output"),
#         type="default",
#     )
# ], fluid=True, className="p-4", style={
#     "backgroundColor": COLOR_PALETTE["light"],
#     "minHeight": "100vh",
#     "fontFamily": MODERN_STYLE["font_family"]
# })
#
# # Callbacks
#
# # Initial loading sequence callback
# @app.callback(
#     Output('table-ready-store', 'data'),
#     Input('init-interval', 'n_intervals')
# )
# def initialize_app(n_intervals):
#     """Initialize app after short delay to ensure all components are rendered"""
#     if n_intervals >= 1:
#         return True
#     return False
#
# @app.callback(
#     [Output('data-table', 'data'),
#      Output('original-data-store', 'data')],
#     [Input('experiment-dropdown', 'value'),
#      Input('data-formulation-filter', 'value'),
#      Input('data-condition-filter', 'value'),
#      Input('table-ready-store', 'data')],
#     prevent_initial_call=True,
#     suppress_callback_exceptions=True
# )
# def load_table(experiment_id, formulation_filter, condition_filter, table_ready):
#     if not experiment_id or not table_ready:
#         return [], {}
#
#     try:
#         # Get data for selected experiment using the property
#         all_samples = FormulationData.objects.all()
#         filtered_samples = [s for s in all_samples if s.experiment_id == experiment_id]
#
#         # Apply additional filters
#         if formulation_filter:
#             formulation_list = formulation_filter if isinstance(formulation_filter, list) else [formulation_filter]
#             temp_filtered = []
#             for sample in filtered_samples:
#                 buffer = sample.buffer or "Unknown"
#                 ph = f"pH{sample.ph}" if sample.ph else "pHUnknown"
#                 excipients = sample.excipients or "No excipients"  # Show full text, no truncation
#                 formulation_key = f"{buffer} | {ph} | {excipients}"
#                 if formulation_key in formulation_list:
#                     temp_filtered.append(sample)
#             filtered_samples = temp_filtered
#
#         if condition_filter:
#             condition_list = condition_filter if isinstance(condition_filter, list) else [condition_filter]
#             filtered_samples = [s for s in filtered_samples if (s.condition or "Unknown") in condition_list]
#
#         if not filtered_samples:
#             return html.Div([
#                 dbc.Alert(f"No data found for experiment {experiment_id} with the selected filters.", color="warning", className="text-center")
#             ]), {}
#
#         # Convert to DataFrame-like structure
#         data = []
#         for sample in filtered_samples:
#             data.append({
#                 'id': sample.id,
#                 'sample_number': sample.sample_number,
#                 'buffer': sample.buffer,
#                 'ph': sample.ph,
#                 'excipients': sample.excipients,
#                 'formulation': sample.formulation,
#                 'condition': sample.condition,
#                 'pull_day': sample.pull_day,
#                 'time_point_months': sample.time_point_months,
#                 'appearance': sample.appearance,
#                 'concentration': sample.concentration,
#                 'ph_measured': sample.ph_measured,
#                 'result_id': sample.result_id,
#                 'hmw': sample.hmw,
#                 'main': sample.main,
#                 'lmw': sample.lmw,
#                 'total_area': sample.total_area,
#                 'osmolality': sample.osmolality,
#                 'tm_celsius': sample.tm_celsius,
#                 'scattering_onset': sample.scattering_onset,
#             })
#
#         # Sort by sample number
#         data.sort(key=lambda x: x['sample_number'])
#
#         # Add multiple blank rows at the bottom for new entries
#         existing_numbers = []
#         for sample in filtered_samples:
#             try:
#                 # Extract number from sample_number format like "FD-003-001"
#                 parts = sample.sample_number.split('-')
#                 if len(parts) >= 3:
#                     num = int(parts[-1])  # Get the last part as the number
#                     existing_numbers.append(num)
#             except:
#                 pass
#
#         # Add 10 blank rows for easier data entry
#         start_num = max(existing_numbers) + 1 if existing_numbers else 1
#         for i in range(10):
#             blank_row = {
#                 'id': None,  # This signals it's a new row
#                 'sample_number': f"{experiment_id}-{start_num + i:03d}",
#                 'buffer': '',
#                 'ph': None,
#                 'excipients': '',
#                 'formulation': '',
#                 'condition': '',
#                 'pull_day': None,
#                 'time_point_months': None,
#                 'appearance': '',
#                 'concentration': None,
#                 'ph_measured': None,
#                 'result_id': '',
#                 'hmw': None,
#                 'main': None,
#                 'lmw': None,
#                 'total_area': None,
#                 'osmolality': None,
#                 'tm_celsius': None,
#                 'scattering_onset': None,
#             }
#             data.append(blank_row)
#
#
#         return data, data
#
#     except Exception as e:
#         print(f"Error loading data: {e}")
#         return [], {}
#
# @app.callback(
#     [Output('has-changes-store', 'data'),
#      Output('save-btn', 'disabled')],
#     [Input('data-table', 'data'),
#      Input('data-table', 'data_previous')],
#     [State('original-data-store', 'data'),
#      State('table-ready-store', 'data')],
#     prevent_initial_call=True,
#     suppress_callback_exceptions=True
# )
# def detect_changes(current_data, previous_data, original_data, table_ready):
#     if not current_data or not original_data or not table_ready:
#         return False, True
#
#     # Compare current data with original
#     has_changes = current_data != original_data
#     return has_changes, not has_changes
#
# @app.callback(
#     [Output('save-status', 'children'),
#      Output('original-data-store', 'data', allow_duplicate=True),
#      Output('has-changes-store', 'data', allow_duplicate=True)],
#     Input('save-btn', 'n_clicks'),
#     [State('data-table', 'data'),
#      State('original-data-store', 'data'),
#      State('table-ready-store', 'data')],
#     prevent_initial_call=True,
#     suppress_callback_exceptions=True
# )
# def save_changes(n_clicks, current_data, original_data, table_ready):
#     if not n_clicks or not current_data or not table_ready:
#         return "", no_update, no_update
#
#     try:
#         saved_count = 0
#         created_count = 0
#         errors = []
#
#         # Create a map of original data by ID for quick lookup
#         original_map = {item.get('id'): item for item in original_data if item.get('id')}
#
#         for row in current_data:
#             try:
#                 row_id = row.get('id')
#
#                 if not row_id:
#                     # This is a new row - create it
#                     sample_number = row.get('sample_number')
#                     if not sample_number:
#                         continue
#
#                     new_sample = FormulationData.objects.create(
#                         sample_number=sample_number,
#                         buffer=row.get('buffer') or None,
#                         ph=row.get('ph'),
#                         excipients=row.get('excipients') or None,
#                         formulation=row.get('formulation') or None,
#                         condition=row.get('condition') or None,
#                         pull_day=row.get('pull_day'),
#                         time_point_months=row.get('time_point_months'),
#                         appearance=row.get('appearance') or None,
#                         concentration=row.get('concentration'),
#                         ph_measured=row.get('ph_measured'),
#                         result_id=row.get('result_id') or None,
#                         hmw=row.get('hmw'),
#                         main=row.get('main'),
#                         lmw=row.get('lmw'),
#                         total_area=row.get('total_area'),
#                         osmolality=row.get('osmolality'),
#                         tm_celsius=row.get('tm_celsius'),
#                         scattering_onset=row.get('scattering_onset'),
#                     )
#                     # Update the row with the new ID
#                     row['id'] = new_sample.id
#                     created_count += 1
#                 else:
#                     # Update existing row
#                     sample = FormulationData.objects.get(id=row_id)
#                     original_row = original_map.get(row_id, {})
#
#                     # Update all fields
#                     sample.buffer = row.get('buffer') or None
#                     sample.ph = row.get('ph')
#                     sample.excipients = row.get('excipients') or None
#                     sample.formulation = row.get('formulation') or None
#                     sample.condition = row.get('condition') or None
#                     sample.pull_day = row.get('pull_day')
#                     sample.time_point_months = row.get('time_point_months')
#                     sample.appearance = row.get('appearance') or None
#                     sample.concentration = row.get('concentration')
#                     sample.ph_measured = row.get('ph_measured')
#                     sample.result_id = row.get('result_id') or None
#                     sample.hmw = row.get('hmw')
#                     sample.main = row.get('main')
#                     sample.lmw = row.get('lmw')
#                     sample.total_area = row.get('total_area')
#                     sample.osmolality = row.get('osmolality')
#                     sample.tm_celsius = row.get('tm_celsius')
#                     sample.scattering_onset = row.get('scattering_onset')
#
#                     sample.save()
#                     saved_count += 1
#
#             except Exception as e:
#                 errors.append(f"Row {row.get('sample_number', 'Unknown')}: {str(e)}")
#
#         # Update the original data store to current data to prevent showing changes
#         message_parts = []
#         if created_count > 0:
#             message_parts.append(f"Created {created_count} new records")
#         if saved_count > 0:
#             message_parts.append(f"Updated {saved_count} records")
#
#         success_message = ", ".join(message_parts) + "!"
#
#         if errors:
#             return dbc.Alert([
#                 html.Strong(f"{success_message} {len(errors)} errors occurred:"),
#                 html.Ul([html.Li(error) for error in errors[:5]])
#             ], color="warning", dismissable=True), current_data, False
#         else:
#             return dbc.Alert(success_message, color="success", dismissable=True), current_data, False
#
#     except Exception as e:
#         return dbc.Alert(f"Error saving data: {str(e)}", color="danger", dismissable=True), no_update, no_update
#
# # Data table filter callbacks
# @app.callback(
#     [Output('data-formulation-filter', 'options'),
#      Output('data-condition-filter', 'options')],
#     Input('experiment-dropdown', 'value'),
#     prevent_initial_call=False,
#     suppress_callback_exceptions=True
# )
# def update_data_filters(experiment_id):
#     if not experiment_id:
#         return [], []
#
#     try:
#         # Get all samples for the experiment
#         all_samples = FormulationData.objects.all()
#         filtered_samples = [s for s in all_samples if s.experiment_id == experiment_id]
#
#         # Get unique formulations (Buffer + pH + Excipients)
#         formulations = set()
#         conditions = set()
#
#         for sample in filtered_samples:
#             # Create formulation key
#             buffer = sample.buffer or "Unknown"
#             ph = f"pH{sample.ph}" if sample.ph else "pHUnknown"
#             excipients = sample.excipients or "No excipients"  # Show full text, no truncation
#             formulation_key = f"{buffer} | {ph} | {excipients}"
#             formulations.add(formulation_key)
#
#             # Add condition
#             condition = sample.condition or "Unknown"
#             conditions.add(condition)
#
#         formulation_options = [{'label': f, 'value': f} for f in sorted(formulations)]
#         condition_options = [{'label': c, 'value': c} for c in sorted(conditions)]
#
#         return formulation_options, condition_options
#     except Exception as e:
#         print(f"Error updating data filters: {e}")
#         return [], []
#
# # Graph callbacks
# @app.callback(
#     Output('formulation-selector', 'options'),
#     Input('experiment-dropdown', 'value'),
#     prevent_initial_call=False,
#     suppress_callback_exceptions=True
# )
# def update_formulation_dropdown(experiment_id):
#     if not experiment_id:
#         return []
#
#     try:
#         # Get all samples for the experiment
#         all_samples = FormulationData.objects.all()
#         filtered_samples = [s for s in all_samples if s.experiment_id == experiment_id]
#
#         # Group by unique formulation (Buffer + pH + Excipients)
#         formulation_groups = {}
#         for sample in filtered_samples:
#             # Create formulation key from Buffer + pH + Excipients
#             buffer = sample.buffer or "Unknown"
#             ph = f"pH{sample.ph}" if sample.ph else "pHUnknown"
#             excipients = sample.excipients or "No excipients"  # Show full text, no truncation
#
#             formulation_key = f"{buffer} | {ph} | {excipients}"
#
#             if formulation_key not in formulation_groups:
#                 formulation_groups[formulation_key] = {
#                     'key': formulation_key,
#                     'buffer': buffer,
#                     'ph': sample.ph,
#                     'excipients': sample.excipients,
#                     'samples': []
#                 }
#
#             formulation_groups[formulation_key]['samples'].append(sample)
#
#         # Create dropdown options
#         formulation_options = []
#         for key, group in sorted(formulation_groups.items()):
#             sample_count = len(group['samples'])
#             formulation_options.append({
#                 'label': f"{key} ({sample_count} samples)",
#                 'value': key
#             })
#
#         return formulation_options
#     except Exception as e:
#         print(f"Error updating dropdown: {e}")
#         return []
#
# @app.callback(
#     Output('time-series-graph', 'figure'),
#     [Input('y-axis-selector', 'value'),
#      Input('formulation-selector', 'value'),
#      Input('storage-condition-filter', 'value'),
#      Input('plots-per-row', 'value'),
#      Input('plot-height-input', 'value'),
#      Input('statistics-checklist', 'value'),
#      Input('experiment-dropdown', 'value')],
#     prevent_initial_call=False,
#     suppress_callback_exceptions=True
# )
# def update_graph(y_axis_variable, selected_formulations, storage_condition_filter, plots_per_row, plot_height, statistics_options, experiment_id):
#     print(f"=== Graph Update Debug ===")
#     print(f"Y-axis variable: {y_axis_variable}")
#     print(f"Storage condition filter: {storage_condition_filter}")
#     print(f"Plots per row: {plots_per_row}")
#     print(f"Plot height: {plot_height}")
#     print(f"Experiment ID: {experiment_id}")
#
#     if not experiment_id or not y_axis_variable:
#         return go.Figure().add_annotation(
#             text="Select experiment and Y-axis variable",
#             xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
#         )
#
#     try:
#         # Get all samples for the experiment
#         all_samples = FormulationData.objects.all()
#         filtered_samples = [s for s in all_samples if s.experiment_id == experiment_id]
#
#         if not filtered_samples:
#             return go.Figure().add_annotation(
#                 text="No data available",
#                 xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
#             )
#
#         # Group samples by formulation (Buffer + pH + Excipients)
#         formulation_groups = {}
#         for sample in filtered_samples:
#             buffer = sample.buffer or "Unknown"
#             ph = f"pH{sample.ph}" if sample.ph else "pHUnknown"
#             excipients = sample.excipients or "No excipients"  # Show full text, no truncation
#
#             formulation_key = f"{buffer} | {ph} | {excipients}"
#
#             if formulation_key not in formulation_groups:
#                 formulation_groups[formulation_key] = []
#
#             formulation_groups[formulation_key].append(sample)
#
#         # Filter by selected formulations if any
#         if selected_formulations:
#             formulation_groups = {k: v for k, v in formulation_groups.items() if k in selected_formulations}
#
#         if not formulation_groups:
#             return go.Figure().add_annotation(
#                 text="No data matches the selected filters",
#                 xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
#             )
#
#
#         # Create subplots - one for each formulation with user controls
#         num_formulations = len(formulation_groups)
#         cols = min(plots_per_row or 2, num_formulations)  # User-defined columns
#         rows = (num_formulations + cols - 1) // cols  # Ceiling division
#
#         # Calculate tighter spacing for better plot density
#         if rows == 1:
#             vertical_spacing = 0.02  # Single row needs minimal spacing
#         elif rows == 2:
#             vertical_spacing = 0.08  # Two rows - reduced from 0.15
#         elif rows <= 4:
#             vertical_spacing = max(0.04, (1 / (rows - 1)) * 0.1)  # 3-4 rows - reduced
#         elif rows <= 6:
#             vertical_spacing = 0.04  # 5-6 rows - reduced from 0.08
#         elif rows <= 8:
#             vertical_spacing = 0.03  # 7-8 rows - reduced from 0.06
#         else:
#             vertical_spacing = 0.02  # 9+ rows - keep tight spacing
#
#         horizontal_spacing = max(0.02, min(0.06, 0.2 / cols)) if cols > 1 else 0.03  # Reduced horizontal spacing
#
#         print(f"Rows: {rows}, Cols: {cols}, Vertical spacing: {vertical_spacing:.3f}, Horizontal spacing: {horizontal_spacing:.3f}")
#
#         fig = make_subplots(
#             rows=rows, cols=cols,
#             subplot_titles=list(formulation_groups.keys()),
#             vertical_spacing=vertical_spacing,
#             horizontal_spacing=horizontal_spacing
#         )
#
#         # Color palette for conditions
#         condition_colors = {
#             '25°C': '#1f77b4',
#             '40°C': '#ff7f0e',
#             '4°C': '#2ca02c',
#             '-80°C': '#d62728',
#             'FT': '#9467bd',
#             '25 °C': '#1f77b4',  # Alternative formatting
#             '40 °C': '#ff7f0e',
#         }
#
#         y_axis_labels = {
#             'hmw': 'HMW %',
#             'main': 'Main %',
#             'lmw': 'LMW %',
#             'concentration': 'Concentration (mg/mL)',
#             'ph_measured': 'pH (measured)',
#             'total_area': 'Total Area',
#             'tm_celsius': 'Tm (°C)',
#             'osmolality': 'Osmolality (mOsm/kg)'
#         }
#
#         for i, (formulation_key, samples) in enumerate(formulation_groups.items()):
#             row = (i // cols) + 1
#             col = (i % cols) + 1
#
#             # Group samples by condition within this formulation
#             condition_groups = {}
#             for sample in samples:
#                 condition = sample.condition or "Unknown"
#
#                 # Filter by storage condition if specified (with flexible matching)
#                 if storage_condition_filter != "all":
#                     condition_normalized = condition.replace(" ", "").lower()
#                     filter_normalized = storage_condition_filter.replace(" ", "").lower()
#                     if condition_normalized != filter_normalized:
#                         continue
#
#                 if condition not in condition_groups:
#                     condition_groups[condition] = []
#                 condition_groups[condition].append(sample)
#
#             # Plot each condition as a separate line
#             for condition, condition_samples in condition_groups.items():
#                 # Extract time points and y values
#                 time_points = []
#                 y_values = []
#
#                 for sample in condition_samples:
#                     if sample.time_point_months is not None:
#                         time_points.append(sample.time_point_months)
#                         y_val = getattr(sample, y_axis_variable, None)
#                         y_values.append(y_val)
#
#                 # Sort by time
#                 if time_points and y_values:
#                     paired_data = list(zip(time_points, y_values))
#                     paired_data = [(t, y) for t, y in paired_data if y is not None]
#                     if paired_data and len(paired_data) >= 2:  # Need at least 2 points for regression
#                         paired_data.sort()
#                         time_points, y_values = zip(*paired_data)
#
#                         # Convert to numpy arrays for regression
#                         x_array = np.array(time_points)
#                         y_array = np.array(y_values)
#
#                         # Add original data points
#                         fig.add_trace(
#                             go.Scatter(
#                                 x=time_points,
#                                 y=y_values,
#                                 mode='markers',
#                                 name=f"{condition} (data)",
#                                 marker=dict(color=condition_colors.get(condition, '#8c564b'), size=8),
#                                 showlegend=(i == 0)  # Only show legend for first subplot
#                             ),
#                             row=row, col=col
#                         )
#
#                         # Calculate linear regression
#                         if len(x_array) >= 2:
#                             slope, intercept, r_value, p_value, std_err = stats.linregress(x_array, y_array)
#
#                             # Create regression line points
#                             x_min, x_max = min(x_array), max(x_array)
#                             # Extend regression line slightly beyond data points
#                             x_extended = np.linspace(x_min * 0.95, x_max * 1.05, 100)
#                             y_regression = slope * x_extended + intercept
#
#                             # Add regression line
#                             fig.add_trace(
#                                 go.Scatter(
#                                     x=x_extended,
#                                     y=y_regression,
#                                     mode='lines',
#                                     name=f"{condition} (fit)",
#                                     line=dict(
#                                         color=condition_colors.get(condition, '#8c564b'),
#                                         dash='dash',
#                                         width=2
#                                     ),
#                                     showlegend=(i == 0),  # Only show legend for first subplot
#                                     hovertemplate=f"<b>{condition} Linear Fit</b><br>" +
#                                                 f"Slope: {slope:.4f}<br>" +
#                                                 f"R²: {r_value**2:.3f}<br>" +
#                                                 f"<extra></extra>"
#                                 ),
#                                 row=row, col=col
#                             )
#
#                             # Add statistics annotation on the plot
#                             if statistics_options:
#                                 stats_text = []
#                                 if 'show_r2' in statistics_options:
#                                     stats_text.append(f"R² = {r_value**2:.3f}")
#                                 if 'show_slope' in statistics_options:
#                                     stats_text.append(f"Slope = {slope:.4f}")
#
#                                 if stats_text:
#                                     # Position annotation in top-right corner of subplot
#                                     fig.add_annotation(
#                                         x=0.95,
#                                         y=0.95,
#                                         text="<br>".join(stats_text),
#                                         showarrow=False,
#                                         font=dict(size=10, color=condition_colors.get(condition, '#8c564b')),
#                                         align="right",
#                                         bgcolor="rgba(255, 255, 255, 0.8)",
#                                         bordercolor=condition_colors.get(condition, '#8c564b'),
#                                         borderwidth=1,
#                                         borderpad=4,
#                                         xref=f"x{'' if col == 1 else col} domain",
#                                         yref=f"y{'' if row == 1 else ((row-1)*cols + col)} domain",
#                                         row=row,
#                                         col=col
#                                     )
#
#         # Update layout with user-defined plot height (matching SEC app approach)
#         plot_height = plot_height or 600  # Default to 600px
#         total_height = plot_height * rows  # Direct calculation like SEC app
#
#         print(f"Plot height per row: {plot_height}, Rows: {rows}, Total height: {total_height}")
#
#         fig.update_layout(
#             height=total_height,
#             margin=dict(l=10, r=10, t=30, b=10),  # Reduced top margin since no title
#             showlegend=True,
#             plot_bgcolor="white"  # Same background as SEC app
#         )
#
#         # Update axes with grid lines and styling
#         for i in range(1, rows + 1):
#             for j in range(1, cols + 1):
#                 fig.update_xaxes(
#                     title_text="Time (months)",
#                     showgrid=True,
#                     gridwidth=1,
#                     gridcolor='rgba(128, 128, 128, 0.2)',
#                     showline=True,
#                     linewidth=1,
#                     linecolor='rgba(0, 0, 0, 0.3)',
#                     row=i, col=j
#                 )
#                 fig.update_yaxes(
#                     title_text=y_axis_labels.get(y_axis_variable, y_axis_variable),
#                     showgrid=True,
#                     gridwidth=1,
#                     gridcolor='rgba(128, 128, 128, 0.2)',
#                     showline=True,
#                     linewidth=1,
#                     linecolor='rgba(0, 0, 0, 0.3)',
#                     row=i, col=j
#                 )
#
#         return fig
#
#     except Exception as e:
#         print(f"Error creating graph: {e}")
#         return go.Figure().add_annotation(
#             text=f"Error creating graph: {str(e)}",
#             xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
#         )
#
#
