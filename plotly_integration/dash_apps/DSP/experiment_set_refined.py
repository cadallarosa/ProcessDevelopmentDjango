"""
Refined Experimental Set Management App
Streamlined layout aligned with existing apps
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table, ALL, MATCH, no_update, ctx
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
import json
from datetime import datetime
import plotly.graph_objects as go
from django.db.models import Q
from plotly_integration.models import LimsDnAssignment, ExperimentalSet, ExperimentalSetData
from django.contrib.auth.models import User
import re

# Project ID normalization function
def normalize_project_id(project_id):
    """
    Normalize project IDs to follow SI-## format
    Examples: 
    - '49T5' -> 'SI-49T5'
    - '49t5' -> 'SI-49T5'  
    - 'SI-49T5' -> 'SI-49T5'
    - 'si-49t5' -> 'SI-49T5'
    - '10A1' -> 'SI-10A1'
    - 'SI-10A1' -> 'SI-10A1'
    - 'SI50E15' -> 'SI-50E15'
    - 'si50e15' -> 'SI-50E15'
    """
    if not project_id or not project_id.strip():
        return project_id
    
    # Clean and uppercase
    clean_id = project_id.strip().upper()
    
    # If it already starts with SI- and has the hyphen, it's correct
    if clean_id.startswith('SI-'):
        return clean_id
    
    # If it starts with SI but no hyphen (e.g., SI50E15)
    if clean_id.startswith('SI') and len(clean_id) > 2 and clean_id[2].isdigit():
        # Insert hyphen after SI
        return f'SI-{clean_id[2:]}'
    
    # Check if it looks like a project ID pattern (digits followed by letters/digits)
    # Pattern: starts with digits, followed by letters/numbers
    if re.match(r'^\d+[A-Z0-9]+$', clean_id):
        return f'SI-{clean_id}'
    
    # If it doesn't match expected pattern, return as-is but uppercase
    return clean_id


def extract_project_number(project_id):
    """
    Extract numeric part for sorting (e.g., SI-49T5 -> 49)
    """
    try:
        normalized = normalize_project_id(project_id)
        if normalized.startswith('SI-'):
            # Extract the number part after SI-
            match = re.match(r'SI-(\d+)', normalized)
            if match:
                return int(match.group(1))
        return 999999  # Put non-standard formats at the end
    except:
        return 999999


# Custom CSS to override Bootstrap modal width
custom_css = """
.modal-90w {
    max-width: 90% !important;
    width: 90% !important;
}
.modal-90w .modal-dialog {
    max-width: 90% !important;
    width: 90% !important;
    margin: 1.75rem auto;
}
.modal-90w .modal-content {
    width: 100% !important;
}
"""

# Initialize the Dash app - aligned with existing apps
app = DjangoDash('ExperimentalSetAppRefined', external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the experimental variables columns - grouped by category
PROCESS_COLUMNS = [
    {'name': 'DN', 'id': 'dn', 'type': 'text', 'editable': False},
    {'name': 'Resin', 'id': 'resin', 'type': 'text', 'editable': True},
    {'name': 'Description', 'id': 'description', 'type': 'text', 'editable': True},
    {'name': 'CV (mL)', 'id': 'cv_ml', 'type': 'numeric', 'editable': True},
    {'name': 'Residence Time (min)', 'id': 'residence_time', 'type': 'numeric', 'editable': True},
]

BUFFER_COLUMNS = [
    {'name': 'Elution Condition', 'id': 'elution_condition', 'type': 'text', 'editable': True},
    {'name': 'EQ', 'id': 'eq', 'type': 'text', 'editable': True},
    {'name': 'Wash Condition', 'id': 'wash_condition', 'type': 'text', 'editable': True},
]

LOAD_COLUMNS = [
    {'name': 'Load Density (mg/mL)', 'id': 'load_density', 'type': 'numeric', 'editable': True},
    {'name': 'Product Required (mg)', 'id': 'product_required', 'type': 'numeric', 'editable': True},
    {'name': 'Load Volume (mL)', 'id': 'load_volume', 'type': 'numeric', 'editable': True},
]

RESULTS_COLUMNS = [
    {'name': 'Eluate Volume (mL)', 'id': 'eluate_volume', 'type': 'numeric', 'editable': True},
    {'name': 'Eluate Concentration (mg/mL)', 'id': 'eluate_concentration', 'type': 'numeric', 'editable': True},
    {'name': 'Eluate Amount (mg)', 'id': 'eluate_amount', 'type': 'numeric', 'editable': True},
    {'name': 'Yield (%)', 'id': 'yield_percent', 'type': 'numeric', 'editable': True},
]

ANALYTICAL_COLUMNS = [
    {'name': '% MP SEC', 'id': 'mp_sec_percent', 'type': 'numeric', 'editable': True},
    {'name': 'PPM HCP', 'id': 'ppm_hcp', 'type': 'numeric', 'editable': True},
    {'name': 'PPB DNA', 'id': 'ppb_dna', 'type': 'numeric', 'editable': True}
]

ALL_COLUMNS = PROCESS_COLUMNS + BUFFER_COLUMNS + LOAD_COLUMNS + RESULTS_COLUMNS + ANALYTICAL_COLUMNS

# DN Assignment columns for selection
DN_SELECTION_COLUMNS = [
    {'name': 'DN', 'id': 'dn', 'type': 'numeric'},
    {'name': 'Project ID', 'id': 'project_id', 'type': 'text'},
    {'name': 'Unit Op', 'id': 'unit_operation', 'type': 'text'},
    {'name': 'Study Name', 'id': 'study_name', 'type': 'text'},
    {'name': 'Scouting Details', 'id': 'scouting_details', 'type': 'text'},
    {'name': 'Status', 'id': 'status', 'type': 'text'},
    {'name': 'Created By', 'id': 'created_by', 'type': 'text'},
    {'name': 'Assigned To', 'id': 'assigned_to', 'type': 'text'},
    {'name': 'Notes', 'id': 'notes', 'type': 'text'},
]

# Styling aligned with existing apps
TABLE_STYLE_CELL = {
    "textAlign": "left",
    "padding": "2px 4px",
    "fontSize": "11px",
    "border": "1px solid #ddd",
    "minWidth": "100px",
    "width": "100px",
    "maxWidth": "200px",
    "overflow": "hidden",
    "textOverflow": "ellipsis",
}

TABLE_STYLE_HEADER = {
    "backgroundColor": "#0056b3",
    "fontWeight": "bold",
    "color": "white",
    "textAlign": "center",
    "fontSize": "11px",
    "padding": "2px 4px"
}

# App layout
app.layout = html.Div([
    # Header aligned with existing apps
    html.Div([
        html.H1("Experimental Set Management",
                style={'color': '#0056b3', 'marginBottom': '10px', 'fontSize': '24px'}),
        html.P("Organize and track downstream processing experiments",
               style={'color': '#666', 'fontSize': '14px', 'marginBottom': '0'})
    ], style={'padding': '15px 20px', 'backgroundColor': '#f8f9fa', 'marginBottom': '20px'}),

    # Store components
    dcc.Store(id='edit-mode-store', storage_type='session'),  # Stores set ID when editing
    dcc.Store(id='current-user-store', storage_type='session'),
    
    # Main content container
    html.Div([
        # Tabs - View first, then Create
        dcc.Tabs(id='main-tabs', value='view-tab', children=[
            # View Sets Tab (First)
            dcc.Tab(label='View Experiment Sets', value='view-tab', children=[
                html.Div([
                    # Search and Filter Bar
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Experimental Sets", className="card-title"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Search:", className="fw-bold"),
                                    dbc.Input(
                                        id='global-search',
                                        type='text',
                                        placeholder='Search all fields...',
                                        size='sm'
                                    )
                                ], width=4),
                                dbc.Col([
                                    dbc.Label("Study Type:", className="fw-bold"),
                                    dbc.Select(
                                        id='filter-study-type',
                                        options=[
                                            {'label': 'All Types', 'value': 'all'},
                                            {'label': 'CEX', 'value': 'cex'},
                                            {'label': 'AEX', 'value': 'aex'},
                                            {'label': 'HIC', 'value': 'hic'},
                                            {'label': 'Protein A', 'value': 'prota'},
                                            {'label': 'Custom', 'value': 'custom'}
                                        ],
                                        value='all',
                                        size='sm'
                                    )
                                ], width=3),
                                dbc.Col([
                                    dbc.Label("Actions:", className="fw-bold"),
                                    html.Div([
                                        dbc.Button("Refresh", id='refresh-sets-btn', color="secondary", size="sm", className="me-2"),
                                        dbc.Button("Export All", id='bulk-export-btn', color="success", size="sm")
                                    ])
                                ], width=3)
                            ])
                        ])
                    ], className="mb-3"),
                    
                    # Quick Statistics Bar
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Strong(id='total-sets-count', children='0', className="text-primary"),
                                html.Span(" Sets", className="text-muted ms-1")
                            ], className="d-inline-block me-4")
                        ], width=2),
                        dbc.Col([
                            html.Div([
                                html.Strong(id='total-experiments-count', children='0', className="text-success"),
                                html.Span(" Experiments", className="text-muted ms-1")
                            ], className="d-inline-block me-4")
                        ], width=2),
                        dbc.Col([
                            html.Div([
                                html.Strong(id='active-projects-count', children='0', className="text-info"),
                                html.Span(" Projects", className="text-muted ms-1")
                            ], className="d-inline-block me-4")
                        ], width=2)
                    ], className="mb-3"),
                    
                    # Action buttons - moved to top under search bar
                    html.Div([
                        html.P("Select a row below and click an action:", className="text-muted mb-2"),
                        html.Div(id="selection-debug", className="small text-info mb-2"),  # Debug info
                        dbc.ButtonGroup([
                            dbc.Button("View Details", id='view-selected-btn', color="primary", size="sm", disabled=True),
                            dbc.Button("View Result", id='result-selected-btn', color="warning", size="sm", disabled=True),
                            dbc.Button("Export Set", id='export-selected-btn', color="success", size="sm", disabled=True),
                            dbc.Button("Delete Set", id='delete-selected-btn', color="danger", size="sm", disabled=True)
                        ])
                    ], className="mb-3"),
                    
                    # Experimental Sets DataTable
                    html.Div(id='sets-table-container')
                ], style={'padding': '20px'})
            ]),
            
            # Create Experiment Set Tab (Second)
            dcc.Tab(label='Create Experiment Set', value='define-tab', children=[
                html.Div([
                    # Set Information
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.H5("Set Information", className="card-title d-inline"),
                                html.Div(id='edit-mode-indicator', className="float-end")
                            ], className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Set Name *"),
                                    dbc.Input(
                                        id='set-name',
                                        type='text',
                                        placeholder='e.g., CEX Optimization Study 1',
                                        size='sm'
                                    )
                                ], width=4),
                                dbc.Col([
                                    dbc.Label("Project ID *"),
                                    dbc.Select(
                                        id='set-project-id',
                                        options=[],
                                        placeholder='Select Project ID...',
                                        size='sm'
                                    )
                                ], width=4),
                                dbc.Col([
                                    dbc.Label("Study Type"),
                                    dbc.Select(
                                        id='study-type',
                                        options=[
                                            {'label': 'CEX Optimization', 'value': 'cex'},
                                            {'label': 'AEX Optimization', 'value': 'aex'},
                                            {'label': 'HIC Study', 'value': 'hic'},
                                            {'label': 'Protein A', 'value': 'prota'},
                                            {'label': 'Custom', 'value': 'custom'}
                                        ],
                                        size='sm'
                                    )
                                ], width=4)
                            ], className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Description"),
                                    dbc.Textarea(
                                        id='set-description',
                                        placeholder='Describe the experimental objectives, variables being tested, and expected outcomes...',
                                        rows=3,
                                        size='sm'
                                    )
                                ], width=12)
                            ])
                        ])
                    ], className="mb-3"),
                    
                    # Experiment Selection Card
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Experiment Selection", className="card-title"),
                            
                            # Filters for DN selection
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Unit Operation Filter"),
                                    dbc.Select(
                                        id='dn-filter-unit-op',
                                        options=[
                                            {'label': 'All', 'value': 'all'},
                                            {'label': 'ProA', 'value': 'ProA'},
                                            {'label': 'AEX', 'value': 'AEX'},
                                            {'label': 'CEX', 'value': 'CEX'},
                                            {'label': 'CHT', 'value': 'CHT'},
                                            {'label': 'VI', 'value': 'VI'},
                                            {'label': 'UFDF', 'value': 'UFDF'},
                                            {'label': 'DF', 'value': 'DF'}
                                        ],
                                        value='all',
                                        size='sm'
                                    )
                                ], width=4),
                                dbc.Col([
                                    dbc.Label("Status Filter"),
                                    dbc.Select(
                                        id='dn-filter-status',
                                        options=[
                                            {'label': 'All', 'value': 'all'},
                                            {'label': 'Pending', 'value': 'Pending'},
                                            {'label': 'In Progress', 'value': 'In Progress'},
                                            {'label': 'Completed', 'value': 'Completed'}
                                        ],
                                        value='all',
                                        size='sm'
                                    )
                                ], width=4),
                                dbc.Col([
                                    dbc.Label("Display Columns"),
                                    dcc.Dropdown(
                                        id='dn-display-columns',
                                        options=[{'label': col['name'], 'value': col['id']} for col in DN_SELECTION_COLUMNS],
                                        value=['dn', 'project_id', 'unit_operation', 'study_name', 'status'],
                                        multi=True,
                                        style={'fontSize': '11px'}
                                    )
                                ], width=4)
                            ], className="mb-3"),
                            
                            # Load DN data button
                            dbc.Button("Load Available Experiments", id='load-dns-btn', color="secondary", size="sm", className="mb-3"),
                            
                            # DN Selection Table
                            html.Div(id='dn-selection-table-container'),
                            
                            # Add Selected DNs Button
                            html.Div([
                                dbc.Button("Add Selected DNs to Set", id='add-selected-dns-btn', color="success", 
                                          size="sm", className="me-2"),
                                html.Span(id='selected-count', style={'color': '#666'})
                            ], className="mt-3")
                        ])
                    ], className="mb-3"),
                    
                    
                    # Experimental Data Table
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.H5("Experimental Data", className="card-title d-inline"),
                                html.Div([
                                    html.Span(id='table-row-count', className="text-muted me-3"),
                                    dbc.Button("Export Excel", id='export-excel', color="success", 
                                              size="sm", className="me-2"),
                                    dbc.Button("Clear All", id='clear-all-btn', color="danger", size="sm")
                                ], className="float-end")
                            ], className="mb-3"),
                            
                            # Column Configuration
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Select Columns to Display", className="fw-bold"),
                                    dcc.Dropdown(
                                        id='experiment-columns-selector',
                                        options=[
                                            {'label': 'Process Parameters', 'value': 'process'},
                                            {'label': 'Buffer Conditions', 'value': 'buffer'},
                                            {'label': 'Load Parameters', 'value': 'load'},
                                            {'label': 'Results', 'value': 'results'},
                                            {'label': 'Analytics', 'value': 'analytical'}
                                        ],
                                        value=['process', 'buffer', 'load', 'results', 'analytical'],
                                        multi=True,
                                        style={'fontSize': '12px'}
                                    )
                                ], width=12)
                            ], className="mb-3"),
                            
                            html.Div([
                                dash_table.DataTable(
                                    id='experimental-data-table',
                                    columns=ALL_COLUMNS,
                                    data=[],
                                    editable=True,
                                    row_deletable=True,
                                    sort_action="native",
                                    filter_action="native",
                                    page_action="native",
                                    page_size=15,
                                    style_cell=TABLE_STYLE_CELL,
                                    style_header=TABLE_STYLE_HEADER,
                                    style_table={'overflowX': 'auto'},
                                    export_format='xlsx',
                                    export_headers='display'
                                )
                            ]),
                            
                            # Save buttons
                            html.Div([
                                dbc.Button("Save Set", id='save-set-btn', color="primary", className="me-2"),
                                dbc.Button("Cancel Edit", id='cancel-edit-btn', color="secondary", style={'display': 'none'})
                            ], className="mt-3")
                        ])
                    ])
                ], style={'padding': '20px'})
            ])
        ])
    ], style={'maxWidth': '1400px', 'margin': '0 auto'}),
    
    # Modals
    # View/Edit Set Modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id='modal-title')),
        dbc.ModalBody(id='modal-body'),
        dbc.ModalFooter([
            dbc.Button("Close", id='modal-close-btn', color="secondary", className="me-2"),
            dbc.Button("Edit", id='modal-edit-btn', color="info", className="me-2"),
            dbc.Button("Save Changes", id='modal-save-btn', color="primary", style={'display': 'none'})
        ])
    ], id='view-edit-modal', 
       size="xl", 
       is_open=False,
       centered=True,
       scrollable=True,
       backdrop="static"),
    
    
    # Delete Confirmation Modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Confirm Delete")),
        dbc.ModalBody([
            html.P("Are you sure you want to delete this experimental set?"),
            html.P(id='delete-set-name', className="fw-bold text-danger"),
            html.P("This action cannot be undone.", className="text-muted")
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id='delete-cancel-btn', color="secondary", className="me-2"),
            dbc.Button("Delete", id='delete-confirm-btn', color="danger")
        ])
    ], id='delete-confirm-modal', is_open=False),
    
    # Notification Toast
    html.Div(id='notification-toast', style={
        'position': 'fixed',
        'top': '80px',
        'right': '20px',
        'zIndex': 9999,
        'minWidth': '300px'
    })
])


# Callback to populate Project ID dropdown with unique project IDs
@app.callback(
    Output('set-project-id', 'options'),
    Input('set-project-id', 'id')  # Triggers on component load
)
def populate_project_id_options(trigger):
    """Populate Project ID dropdown with normalized and sorted project IDs from DN experiments"""
    try:
        # Get unique project IDs from DN assignments
        raw_project_ids = LimsDnAssignment.objects.values_list('project_id', flat=True).distinct()
        raw_project_ids = [pid for pid in raw_project_ids if pid and pid.strip()]  # Remove empty/null values
        
        # Normalize project IDs and create mapping
        normalized_projects = {}
        for raw_pid in raw_project_ids:
            normalized = normalize_project_id(raw_pid)
            # Keep track of original value for database queries
            normalized_projects[normalized] = raw_pid
        
        # Sort by numeric part (SI-## format)
        sorted_normalized = sorted(normalized_projects.keys(), key=extract_project_number)
        
        # Create options with normalized display but original values for DB queries
        options = []
        for normalized in sorted_normalized:
            original = normalized_projects[normalized]
            options.append({
                'label': normalized,
                'value': original  # Use original value for database queries
            })
        
        return options
    except Exception as e:
        return []


# Callback to load available DNs from database
@app.callback(
    Output('dn-selection-table-container', 'children'),
    [Input('load-dns-btn', 'n_clicks'),
     Input('set-project-id', 'value'),
     Input('dn-filter-unit-op', 'value'),
     Input('dn-filter-status', 'value'),
     Input('dn-display-columns', 'value')]
)
def load_dn_selection_table(n_clicks, project_id, unit_op_filter, status_filter, display_columns):
    """Load DN selection table with filters using set project ID as primary filter"""
    # Only load if button clicked or project ID is selected
    if not n_clicks and not project_id:
        return html.P("Select a Project ID and click 'Load Available Experiments' to see available DNs", className="text-muted")
    
    try:
        # Build query - use project ID from set information as primary filter
        query = LimsDnAssignment.objects.all()
        
        if project_id:
            query = query.filter(project_id=project_id)
        if unit_op_filter and unit_op_filter != 'all':
            query = query.filter(unit_operation=unit_op_filter)
        if status_filter and status_filter != 'all':
            query = query.filter(status=status_filter)
        
        # Get data ordered by DN number
        dns = query.values('dn', 'project_id', 'unit_operation', 'study_name', 'scouting_details', 
                          'status', 'created_by__username', 'assigned_to__username', 'notes').order_by('dn')[:100]
        
        # Prepare data
        data = []
        for dn in dns:
            row = {
                'dn': f"DN{dn['dn']:03d}",
                'project_id': dn['project_id'] or '',
                'unit_operation': dn['unit_operation'] or '',
                'study_name': dn['study_name'] or '',
                'scouting_details': dn['scouting_details'] or '',
                'status': dn['status'] or '',
                'created_by': dn['created_by__username'] or '',
                'assigned_to': dn['assigned_to__username'] or '',
                'notes': dn['notes'] or ''
            }
            data.append(row)
        
        # Filter columns based on selection
        if display_columns:
            columns = [col for col in DN_SELECTION_COLUMNS if col['id'] in display_columns]
        else:
            columns = DN_SELECTION_COLUMNS[:5]  # Default columns
        
        return dash_table.DataTable(
            id='dn-selection-table',
            columns=columns,
            data=data,
            editable=False,
            row_selectable="multi",
            page_action="native",
            page_size=10,
            style_cell=TABLE_STYLE_CELL,
            style_header=TABLE_STYLE_HEADER,
            style_table={'overflowX': 'auto'},
            filter_action="native",
            sort_action="native"
        )
    
    except Exception as e:
        return html.P(f"Error loading DNs: {str(e)}", className="text-danger")


# Callback to show selected DN count
@app.callback(
    Output('selected-count', 'children'),
    Input('dn-selection-table', 'selected_rows'),
    State('dn-selection-table', 'data')
)
def update_selected_count(selected_rows, table_data):
    """Update selected DN count"""
    if not selected_rows or not table_data:
        return "No DNs selected"
    
    count = len(selected_rows)
    return f"{count} DN(s) selected"


# Callback to add selected DNs to experimental data table
@app.callback(
    [Output('experimental-data-table', 'data'),
     Output('notification-toast', 'children')],
    Input('add-selected-dns-btn', 'n_clicks'),
    [State('dn-selection-table', 'selected_rows'),
     State('dn-selection-table', 'data'),
     State('experimental-data-table', 'data')]
)
def add_selected_dns(n_clicks, selected_rows, selection_data, current_data):
    """Add selected DNs to experimental data table in numerical order"""
    if not n_clicks or not selected_rows or not selection_data:
        return current_data or [], None
    
    new_rows = []
    for idx in selected_rows:
        dn = selection_data[idx]['dn']
        if not any(row.get('dn') == dn for row in (current_data or [])):
            new_rows.append({'dn': dn})
    
    if new_rows:
        # Combine existing and new data
        all_data = (current_data or []) + new_rows
        
        # Sort by DN number (extract numeric part from DN001, DN002, etc.)
        def extract_dn_number(row):
            dn = row.get('dn', '')
            try:
                # Extract number from DN001 format
                if dn.startswith('DN'):
                    return int(dn[2:])
                return 0
            except:
                return 0
        
        all_data.sort(key=extract_dn_number)
        
        notification = dbc.Toast(
            [html.P(f"Added {len(new_rows)} DN(s) to experimental set")],
            header="Success",
            is_open=True,
            dismissable=True,
            duration=3000,
            style={"position": "fixed", "top": 66, "right": 10, "width": 350}
        )
        return all_data, notification
    
    return current_data or [], None


# Callback to update table columns based on selection
@app.callback(
    Output('experimental-data-table', 'columns'),
    Input('experiment-columns-selector', 'value')
)
def update_experiment_table_columns(selected_categories):
    """Update experimental data table columns based on category selection"""
    if not selected_categories:
        return [ALL_COLUMNS[0]]  # Just DN column
    
    selected_columns = []
    
    if 'process' in selected_categories:
        selected_columns.extend(PROCESS_COLUMNS)
    if 'buffer' in selected_categories:
        selected_columns.extend(BUFFER_COLUMNS)
    if 'load' in selected_categories:
        selected_columns.extend(LOAD_COLUMNS)
    if 'results' in selected_categories:
        selected_columns.extend(RESULTS_COLUMNS)
    if 'analytical' in selected_categories:
        selected_columns.extend(ANALYTICAL_COLUMNS)
    
    return selected_columns if selected_columns else ALL_COLUMNS


# Callback to update row count
@app.callback(
    Output('table-row-count', 'children'),
    Input('experimental-data-table', 'data')
)
def update_row_count(data):
    count = len(data) if data else 0
    return f"{count} experiments"


# Save experimental set to database
@app.callback(
    Output('notification-toast', 'children', allow_duplicate=True),
    [Input('save-set-btn', 'n_clicks')],
    [State('set-name', 'value'),
     State('set-project-id', 'value'),
     State('set-description', 'value'),
     State('study-type', 'value'),
     State('experimental-data-table', 'data'),
     State('edit-mode-store', 'data')],
    prevent_initial_call=True
)
def save_experimental_set(n_clicks, set_name, project_id, description, study_type, table_data, edit_mode_data):
    """Save experimental set to database"""
    if not n_clicks or not set_name:
        return None
    
    try:
        # Get current user (simplified - in real app, get from session/auth)
        user = User.objects.first()  # Replace with actual user authentication
        
        # Normalize project ID before saving
        normalized_project_id = normalize_project_id(project_id) if project_id else project_id
        
        # Check if editing existing set
        if edit_mode_data and edit_mode_data.get('set_id'):
            # Update existing set
            exp_set = ExperimentalSet.objects.get(id=edit_mode_data['set_id'])
            exp_set.name = set_name
            exp_set.project_id = normalized_project_id
            exp_set.description = description or ''
            exp_set.study_type = study_type or 'custom'
            exp_set.save()
            
            # Clear existing data
            exp_set.experimental_data.all().delete()
            action = "updated"
        else:
            # Create new set
            exp_set = ExperimentalSet.objects.create(
                name=set_name,
                project_id=normalized_project_id,
                description=description or '',
                study_type=study_type or 'custom',
                created_by=user
            )
            action = "created"
        
        # Save experimental data
        if table_data:
            for row in table_data:
                dn_str = row.get('dn', '')
                if dn_str and dn_str.startswith('DN'):
                    try:
                        dn_number = int(dn_str[2:])  # Extract number from DN001
                        dn_assignment = LimsDnAssignment.objects.get(dn=dn_number)
                        
                        ExperimentalSetData.objects.create(
                            experimental_set=exp_set,
                            dn_assignment=dn_assignment,
                            resin=row.get('resin', ''),
                            cv_ml=row.get('cv_ml'),
                            residence_time=row.get('residence_time'),
                            elution_condition=row.get('elution_condition', ''),
                            eq=row.get('eq', ''),
                            wash_condition=row.get('wash_condition', ''),
                            load_density=row.get('load_density'),
                            product_required=row.get('product_required'),
                            load_volume=row.get('load_volume'),
                            eluate_volume=row.get('eluate_volume'),
                            eluate_concentration=row.get('eluate_concentration'),
                            eluate_amount=row.get('eluate_amount'),
                            yield_percent=row.get('yield_percent'),
                            mp_sec_percent=row.get('mp_sec_percent'),
                            ppm_hcp=row.get('ppm_hcp'),
                            ppb_dna=row.get('ppb_dna')
                        )
                    except (LimsDnAssignment.DoesNotExist, ValueError):
                        continue  # Skip invalid DN
        
        return dbc.Toast(
            [html.P(f"Experimental set '{set_name}' {action} successfully!")],
            header="Success",
            is_open=True,
            dismissable=True,
            duration=4000,
            style={"position": "fixed", "top": 66, "right": 10, "width": 350}
        )
    
    except Exception as e:
        return dbc.Toast(
            [html.P(f"Error saving experimental set: {str(e)}")],
            header="Error",
            is_open=True,
            dismissable=True,
            duration=5000,
            style={"position": "fixed", "top": 66, "right": 10, "width": 350}
        )


# Display experimental sets in DataTable
@app.callback(
    [Output('sets-table-container', 'children'),
     Output('total-sets-count', 'children'),
     Output('total-experiments-count', 'children'),
     Output('active-projects-count', 'children')],
    [Input('refresh-sets-btn', 'n_clicks'),
     Input('main-tabs', 'value'),  # Refresh when switching to view tab
     Input('delete-confirm-btn', 'n_clicks'),  # Refresh after delete
     Input('save-set-btn', 'n_clicks')],  # Refresh after save
    [State('global-search', 'value'),
     State('filter-study-type', 'value')]
)
def display_experimental_sets_table(n_clicks, tab_value, delete_clicks, save_clicks, search_text, study_type_filter):
    """Display experimental sets in DataTable format"""
    
    try:
        # Build query
        query = ExperimentalSet.objects.all()
        
        # Apply filters
        if search_text:
            search_lower = search_text.lower()
            query = query.filter(
                Q(name__icontains=search_lower) |
                Q(project_id__icontains=search_lower) |
                Q(description__icontains=search_lower)
            )
        
        if study_type_filter and study_type_filter != 'all':
            query = query.filter(study_type=study_type_filter)
        
        experimental_sets = query.prefetch_related('experimental_data__dn_assignment').order_by('-created_at')
        
        if not experimental_sets.exists():
            return [
                dbc.Alert("No experimental sets found. Create your first set in the 'Create Experiment Set' tab.", 
                         color="info", className="text-center")
            ], '0', '0', '0'
        
        # Calculate statistics
        total_sets = experimental_sets.count()
        total_experiments = sum(exp_set.experimental_data.count() for exp_set in experimental_sets)
        unique_projects = len(set(exp_set.project_id for exp_set in experimental_sets if exp_set.project_id))
        
        # Prepare data for DataTable
        table_data = []
        for exp_set in experimental_sets:
            # Get DN list for AKTA links
            dn_list = [f"DN{data.dn_assignment.dn:03d}" for data in exp_set.experimental_data.all()]
            
            row = {
                'id': exp_set.id,
                'name': exp_set.name,
                'project_id': normalize_project_id(exp_set.project_id) if exp_set.project_id else 'N/A',
                'study_type': exp_set.get_study_type_display(),
                'study_type_code': exp_set.study_type,  # For color coding
                'description': exp_set.description[:100] + '...' if len(exp_set.description) > 100 else exp_set.description or 'No description',
                'dn_count': exp_set.experimental_data.count(),
                'created_by': exp_set.created_by.username if exp_set.created_by else 'Unknown',
                'created_at': exp_set.created_at.strftime('%Y-%m-%d'),
                'updated_at': exp_set.updated_at.strftime('%Y-%m-%d'),
                'dn_list': ', '.join(dn_list)  # For AKTA links
            }
            table_data.append(row)
        
        # Define columns 
        columns = [
            {
                'name': 'Set Name',
                'id': 'name',
                'type': 'text'
            },
            {
                'name': 'Project ID',
                'id': 'project_id',
                'type': 'text'
            },
            {
                'name': 'Study Type',
                'id': 'study_type',
                'type': 'text'
            },
            {
                'name': 'Description',
                'id': 'description',
                'type': 'text'
            },
            {
                'name': 'DN Count',
                'id': 'dn_count',
                'type': 'numeric'
            },
            {
                'name': 'Created By',
                'id': 'created_by',
                'type': 'text'
            },
            {
                'name': 'Created',
                'id': 'created_at',
                'type': 'text'
            },
            {
                'name': 'Updated',
                'id': 'updated_at',
                'type': 'text'
            }
        ]
        
        # Style conditional for study type colors
        style_data_conditional = [
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            }
        ]
        
        # Add color coding based on study type
        study_type_colors = {
            'cex': '#d4edda',      # Light green
            'aex': '#d1ecf1',      # Light blue
            'hic': '#fff3cd',      # Light yellow
            'prota': '#f8d7da',    # Light red
            'custom': '#e2e3e5'    # Light gray
        }
        
        for i, row in enumerate(table_data):
            study_type = row['study_type_code']
            if study_type in study_type_colors:
                style_data_conditional.append({
                    'if': {'row_index': i},
                    'backgroundColor': study_type_colors[study_type]
                })
        
        table = dash_table.DataTable(
            id='experimental-sets-table',
            columns=columns,
            data=table_data,
            editable=False,
            row_selectable="single",
            sort_action="native",
            filter_action="native",
            page_action="native",
            page_size=20,
            style_cell={
                'textAlign': 'left',
                'padding': '8px',
                'fontSize': '12px',
                'fontFamily': 'Segoe UI, Arial, sans-serif'
            },
            style_header={
                'backgroundColor': '#0056b3',
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_data_conditional=style_data_conditional,
            style_table={'overflowX': 'auto'}
        )
        
        return [table], str(total_sets), str(total_experiments), str(unique_projects)
    
    except Exception as e:
        return [
            dbc.Alert(f"Error loading experimental sets: {str(e)}", color="danger", className="text-center")
        ], '0', '0', '0'


# Clear table callback
@app.callback(
    [Output('experimental-data-table', 'data', allow_duplicate=True),
     Output('set-name', 'value'),
     Output('set-project-id', 'value'),
     Output('set-description', 'value'),
     Output('study-type', 'value')],
    [Input('clear-all-btn', 'n_clicks')],
    prevent_initial_call=True
)
def clear_all_data(n_clicks):
    """Clear all form data and table"""
    if n_clicks:
        return [], '', None, '', None  # None for dropdowns to clear selection
    return no_update


# Edit mode functionality is now handled directly within the modal


# Edit mode indicator
@app.callback(
    [Output('edit-mode-indicator', 'children'),
     Output('cancel-edit-btn', 'style')],
    Input('edit-mode-store', 'data')
)
def update_edit_mode_indicator(edit_mode_data):
    """Update edit mode indicator"""
    if edit_mode_data and edit_mode_data.get('editing'):
        indicator = dbc.Badge("EDITING MODE", color="warning", className="me-2")
        cancel_style = {'display': 'inline-block'}
        return indicator, cancel_style
    return None, {'display': 'none'}


# Cancel edit mode
@app.callback(
    [Output('edit-mode-store', 'data', allow_duplicate=True),
     Output('main-tabs', 'value', allow_duplicate=True)],
    Input('cancel-edit-btn', 'n_clicks'),
    prevent_initial_call=True
)
def cancel_edit_mode(n_clicks):
    """Cancel edit mode and return to view"""
    if n_clicks:
        return None, 'view-tab'
    return no_update


# Delete confirmation callback
@app.callback(
    Output('notification-toast', 'children', allow_duplicate=True),
    Input('delete-confirm-btn', 'n_clicks'),
    State('edit-mode-store', 'data'),
    prevent_initial_call=True
)
def delete_experimental_set(confirm_clicks, edit_mode_data):
    """Delete experimental set from database after confirmation"""
    if not confirm_clicks or not edit_mode_data or not edit_mode_data.get('set_id'):
        return None
    
    set_id = edit_mode_data['set_id']
    
    try:
        exp_set = ExperimentalSet.objects.get(id=set_id)
        set_name = exp_set.name
        exp_set.delete()
        
        return dbc.Toast(
            [html.P(f"Experimental set '{set_name}' deleted successfully!")],
            header="Success",
            is_open=True,
            dismissable=True,
            duration=3000,
            style={"position": "fixed", "top": 66, "right": 10, "width": 350}
        )
    
    except ExperimentalSet.DoesNotExist:
        return dbc.Toast(
            [html.P("Experimental set not found!")],
            header="Error",
            is_open=True,
            dismissable=True,
            duration=3000,
            style={"position": "fixed", "top": 66, "right": 10, "width": 350}
        )


# Debug selection callback
@app.callback(
    Output('selection-debug', 'children'),
    Input('experimental-sets-table', 'selected_rows')
)
def debug_selection(selected_rows):
    """Show debug info about selection"""
    if selected_rows:
        return f"Selected rows: {selected_rows}"
    return "No rows selected"


# Enable/disable action buttons based on row selection
@app.callback(
    [Output('view-selected-btn', 'disabled'),
     Output('result-selected-btn', 'disabled'),
     Output('export-selected-btn', 'disabled'),
     Output('delete-selected-btn', 'disabled')],
    Input('experimental-sets-table', 'selected_rows')
)
def enable_action_buttons(selected_rows):
    """Enable action buttons when a row is selected"""
    # Default case: no rows selected or None
    if not selected_rows or len(selected_rows) == 0:
        return True, True, True, True
    # Enable buttons when row is selected
    return False, False, False, False


# View Details button callback - opens modal and loads content directly
@app.callback(
    [Output('view-edit-modal', 'is_open'),
     Output('modal-title', 'children'),
     Output('modal-body', 'children'),
     Output('modal-edit-btn', 'style'),
     Output('modal-save-btn', 'style'),
     Output('edit-mode-store', 'data', allow_duplicate=True)],
    Input('view-selected-btn', 'n_clicks'),
    [State('experimental-sets-table', 'selected_rows'),
     State('experimental-sets-table', 'data')],
    prevent_initial_call=True
)
def handle_view_button(n_clicks, selected_rows, table_data):
    """Handle view details button click and load modal content"""
    print(f"DEBUG VIEW BTN: Called with n_clicks={n_clicks}, selected_rows={selected_rows}")
    
    if not n_clicks or not selected_rows or not table_data:
        print("DEBUG VIEW BTN: Missing required data, returning no_update")
        return no_update
    
    row_index = selected_rows[0]
    row_data = table_data[row_index]
    set_id = row_data['id']
    
    print(f"DEBUG VIEW BTN: Selected set_id={set_id}, set_name={row_data.get('name', 'Unknown')}")
    
    try:
        print(f"DEBUG VIEW BTN: Looking for ExperimentalSet with id={set_id}")
        exp_set = ExperimentalSet.objects.get(id=set_id)
        print(f"DEBUG VIEW BTN: Found experimental set: {exp_set.name}")
        
        exp_data = exp_set.experimental_data.select_related('dn_assignment').order_by('dn_assignment__dn')
        print(f"DEBUG VIEW BTN: Found {exp_data.count()} experimental data entries")
        
        # Modal title
        title = f"View Experimental Set: {exp_set.name}"
        
        # Create content with full-width styling
        content = [
            # Set Information in full-width container
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H5("Set Information", className="text-primary"),
                        html.P([html.Strong("Name: "), exp_set.name]),
                        html.P([html.Strong("Project ID: "), normalize_project_id(exp_set.project_id)]),
                        html.P([html.Strong("Study Type: "), exp_set.get_study_type_display()]),
                        html.P([html.Strong("Description: "), exp_set.description or 'No description']),
                    ], width=6),
                    dbc.Col([
                        html.H5("Set Details", className="text-primary"),
                        html.P([html.Strong("Created By: "), exp_set.created_by.username if exp_set.created_by else 'Unknown']),
                        html.P([html.Strong("Created: "), exp_set.created_at.strftime('%Y-%m-%d %H:%M')]),
                        html.P([html.Strong("Last Updated: "), exp_set.updated_at.strftime('%Y-%m-%d %H:%M')]),
                        html.P([html.Strong("Experiment Count: "), str(exp_data.count())]),
                    ], width=6)
                ], className="mb-4"),
                html.Hr()
            ], style={'padding': '15px'})
        ]
        
        if exp_data.exists():
            content.append(html.H5("Experimental Data", className="text-primary mb-3"))
            
            # Create comprehensive table data for ALL experimental parameters
            exp_table_data = []
            for data in exp_data:
                row = {
                    'dn': f"DN{data.dn_assignment.dn:03d}",
                    'result_link': f"📊 View Result",  # Text for the link
                    'resin': data.resin or '',
                    'cv_ml': data.cv_ml if data.cv_ml is not None else '',
                    'residence_time': data.residence_time if data.residence_time is not None else '',
                    'elution_condition': data.elution_condition or '',
                    'eq': data.eq or '',
                    'wash_condition': data.wash_condition or '',
                    'load_density': data.load_density if data.load_density is not None else '',
                    'product_required': data.product_required if data.product_required is not None else '',
                    'load_volume': data.load_volume if data.load_volume is not None else '',
                    'eluate_volume': data.eluate_volume if data.eluate_volume is not None else '',
                    'eluate_concentration': data.eluate_concentration if data.eluate_concentration is not None else '',
                    'eluate_amount': data.eluate_amount if data.eluate_amount is not None else '',
                    'yield_percent': data.yield_percent if data.yield_percent is not None else '',
                    'mp_sec_percent': data.mp_sec_percent if data.mp_sec_percent is not None else '',
                    'ppm_hcp': data.ppm_hcp if data.ppm_hcp is not None else '',
                    'ppb_dna': data.ppb_dna if data.ppb_dna is not None else ''
                }
                exp_table_data.append(row)
            
            # Create single comprehensive table with all data
            comprehensive_table = dash_table.DataTable(
                id=f'modal-comprehensive-table-{set_id}',
                columns=[
                    # Fixed columns
                    {'name': 'DN', 'id': 'dn', 'type': 'text', 'editable': False},
                    {'name': 'Result', 'id': 'result_link', 'type': 'text', 'editable': False, 'presentation': 'markdown'},
                    
                    # Process parameters
                    {'name': 'Resin', 'id': 'resin', 'type': 'text', 'editable': True},
                    {'name': 'CV (mL)', 'id': 'cv_ml', 'type': 'numeric', 'editable': True},
                    {'name': 'Res. Time (min)', 'id': 'residence_time', 'type': 'numeric', 'editable': True},
                    
                    # Buffer conditions
                    {'name': 'Elution Condition', 'id': 'elution_condition', 'type': 'text', 'editable': True},
                    {'name': 'EQ Buffer', 'id': 'eq', 'type': 'text', 'editable': True},
                    {'name': 'Wash Condition', 'id': 'wash_condition', 'type': 'text', 'editable': True},
                    
                    # Load parameters
                    {'name': 'Load Density (mg/mL)', 'id': 'load_density', 'type': 'numeric', 'editable': True},
                    {'name': 'Product Req. (mg)', 'id': 'product_required', 'type': 'numeric', 'editable': True},
                    {'name': 'Load Vol. (mL)', 'id': 'load_volume', 'type': 'numeric', 'editable': True},
                    
                    # Results
                    {'name': 'Eluate Vol. (mL)', 'id': 'eluate_volume', 'type': 'numeric', 'editable': True},
                    {'name': 'Eluate Conc. (mg/mL)', 'id': 'eluate_concentration', 'type': 'numeric', 'editable': True},
                    {'name': 'Eluate Amt. (mg)', 'id': 'eluate_amount', 'type': 'numeric', 'editable': True},
                    {'name': 'Yield (%)', 'id': 'yield_percent', 'type': 'numeric', 'editable': True},
                    
                    # Analytics
                    {'name': '% MP SEC', 'id': 'mp_sec_percent', 'type': 'numeric', 'editable': True},
                    {'name': 'PPM HCP', 'id': 'ppm_hcp', 'type': 'numeric', 'editable': True},
                    {'name': 'PPB DNA', 'id': 'ppb_dna', 'type': 'numeric', 'editable': True}
                ],
                data=exp_table_data,
                style_cell={
                    'textAlign': 'left', 
                    'padding': '6px', 
                    'fontSize': '11px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'width': 'auto'
                },
                style_header={
                    'backgroundColor': '#0056b3', 
                    'color': 'white', 
                    'fontWeight': 'bold',
                    'textAlign': 'center',
                    'fontSize': '11px'
                },
                style_table={'width': '100%', 'minWidth': '100%'},
                style_data_conditional=[
                    {
                        'if': {'column_id': 'result_link'},
                        'backgroundColor': '#e3f2fd',
                        'color': '#1976d2',
                        'textAlign': 'center',
                        'fontWeight': 'bold'
                    }
                ],
                fixed_columns={'headers': True, 'data': 2},  # Fix DN and Result columns
                page_size=15,
                editable=True,
                markdown_options={"link_target": "_blank"}
            )
            
            # Convert Result column to actual links using the correct format
            for i, data in enumerate(exp_data):
                exp_table_data[i]['result_link'] = f'[📊 View](/plotly_integration/dash-app/app/AktaChromatogramApp/?dn={data.dn_assignment.dn})'
            
            # Update table data with actual markdown links
            comprehensive_table.data = exp_table_data
            
            # Wrap table in full-width container
            table_container = html.Div([
                comprehensive_table,
                # Add View All Results button
                html.Div([
                    dbc.Button(
                        f"View All Results ({len(exp_data)} DNs)",
                        href=f"/plotly_integration/dash-app/app/AktaChromatogramApp/?dn={','.join([str(data.dn_assignment.dn) for data in exp_data])}",
                        target="_blank",
                        color="warning",
                        size="sm",
                        className="mt-3"
                    )
                ], className="text-center")
            ], style={
                'padding': '15px'
            })
            
            content.append(table_container)
        else:
            content.append(dbc.Alert("No experimental data available for this set.", color="info", className="mt-3"))
        
        edit_btn_style = {'display': 'none'}  # Hide edit button since editing is now inline
        save_btn_style = {'display': 'inline-block'}  # Show save button for inline edits
        
        print(f"DEBUG VIEW BTN: Successfully loaded modal content")
        
        return (True, title, content, edit_btn_style, save_btn_style, {'set_id': set_id, 'editing': False})
        
    except ExperimentalSet.DoesNotExist:
        print("DEBUG VIEW BTN: ExperimentalSet.DoesNotExist exception")
        error_content = [html.P("Experimental set not found.", className="text-danger")]
        return (True, "Set Not Found", error_content, {'display': 'none'}, {'display': 'none'}, {'set_id': set_id, 'editing': False})
    except Exception as e:
        print(f"DEBUG VIEW BTN: Exception occurred: {e}")
        error_content = [html.P(f"Error loading set: {str(e)}", className="text-danger")]
        return (True, "Error", error_content, {'display': 'none'}, {'display': 'none'}, {'set_id': set_id, 'editing': False})


# Edit functionality is now handled directly within the View Details modal


# Delete Set button callback
@app.callback(
    [Output('delete-confirm-modal', 'is_open'),
     Output('delete-set-name', 'children'),
     Output('edit-mode-store', 'data', allow_duplicate=True)],
    Input('delete-selected-btn', 'n_clicks'),
    [State('experimental-sets-table', 'selected_rows'),
     State('experimental-sets-table', 'data')],
    prevent_initial_call=True
)
def handle_delete_button(n_clicks, selected_rows, table_data):
    """Handle delete set button click"""
    if not n_clicks or not selected_rows or not table_data:
        return no_update
    
    row_index = selected_rows[0]
    row_data = table_data[row_index]
    set_id = row_data['id']
    set_name = row_data['name']
    
    return (True, set_name, {'set_id': set_id, 'editing': False})


# Save changes from modal editing
@app.callback(
    Output('notification-toast', 'children', allow_duplicate=True),
    Input('modal-save-btn', 'n_clicks'),
    [State('edit-mode-store', 'data'),
     State({'type': 'modal-process-table', 'index': ALL}, 'data'),
     State({'type': 'modal-buffer-table', 'index': ALL}, 'data'),
     State({'type': 'modal-load-table', 'index': ALL}, 'data'),
     State({'type': 'modal-results-table', 'index': ALL}, 'data'),
     State({'type': 'modal-analytics-table', 'index': ALL}, 'data')],
    prevent_initial_call=True
)
def save_modal_changes(n_clicks, edit_mode_data, process_data, buffer_data, load_data, results_data, analytics_data):
    """Save changes made in the modal tables"""
    if not n_clicks or not edit_mode_data or not edit_mode_data.get('set_id'):
        return None
    
    set_id = edit_mode_data['set_id']
    
    try:
        # Get experimental set
        exp_set = ExperimentalSet.objects.get(id=set_id)
        
        # For now, show a placeholder toast - full implementation would update the database
        return dbc.Toast(
            [html.P(f"Changes to experimental set '{exp_set.name}' would be saved here."),
             html.P("Full save functionality can be implemented based on your data structure.", className="small text-muted")],
            header="Save Functionality",
            is_open=True,
            dismissable=True,
            duration=4000,
            style={"position": "fixed", "top": 66, "right": 10, "width": 400}
        )
        
    except ExperimentalSet.DoesNotExist:
        return dbc.Toast(
            [html.P("Experimental set not found!")],
            header="Error",
            is_open=True,
            dismissable=True,
            duration=3000,
            style={"position": "fixed", "top": 66, "right": 10, "width": 350}
        )


# View Result button callback - opens URL with all DNs from the set
@app.callback(
    Output('notification-toast', 'children', allow_duplicate=True),
    Input('result-selected-btn', 'n_clicks'),
    [State('experimental-sets-table', 'selected_rows'),
     State('experimental-sets-table', 'data')],
    prevent_initial_call=True
)
def view_result_for_set(result_clicks, selected_rows, table_data):
    """Open result page with all DNs from the experimental set"""
    if not result_clicks or not selected_rows or not table_data:
        return None
    
    try:
        # Get selected row data
        row_index = selected_rows[0]
        row_data = table_data[row_index]
        set_id = row_data['id']
        set_name = row_data['name']
        
        # Load experimental set from database
        exp_set = ExperimentalSet.objects.get(id=set_id)
        exp_data = exp_set.experimental_data.select_related('dn_assignment').order_by('dn_assignment__dn')
        
        if not exp_data.exists():
            return dbc.Toast(
                [html.P("No experiments in this set to view.")],
                header="Info",
                is_open=True,
                dismissable=True,
                duration=3000,
                style={"position": "fixed", "top": 66, "right": 10, "width": 350}
            )
        
        # Get all DN numbers from the set
        dn_numbers = [data.dn_assignment.dn for data in exp_data]
        dn_query = ','.join(map(str, dn_numbers))
        
        # Create URL with all DNs (adjust URL pattern as needed for your result page)
        result_url = f"/dash/akta_report_app/?dn={dn_query}"
        
        # For now, show a toast with the URL that would be opened
        # In a real implementation, you'd use dcc.Location or similar to navigate
        return dbc.Toast([
            html.P(f"Would open result page for set '{set_name}' with DNs: {', '.join(f'DN{dn:03d}' for dn in dn_numbers)}"),
            html.P(f"URL: {result_url}", className="small text-muted")
        ],
            header="View Result",
            is_open=True,
            dismissable=True,
            duration=5000,
            style={"position": "fixed", "top": 66, "right": 10, "width": 400}
        )
        
    except ExperimentalSet.DoesNotExist:
        return dbc.Toast(
            [html.P("Experimental set not found!")],
            header="Error",
            is_open=True,
            dismissable=True,
            duration=3000,
            style={"position": "fixed", "top": 66, "right": 10, "width": 350}
        )


# Close modal callbacks
@app.callback(
    [Output('view-edit-modal', 'is_open', allow_duplicate=True),
     Output('delete-confirm-modal', 'is_open', allow_duplicate=True)],
    [Input('modal-close-btn', 'n_clicks'),
     Input('delete-cancel-btn', 'n_clicks'),
     Input('delete-confirm-btn', 'n_clicks')],  # Close delete modal after confirm
    prevent_initial_call=True
)
def close_modals(modal_close, delete_cancel, delete_confirm):
    """Close all modals"""
    return False, False


# Export selected set callback
@app.callback(
    Output('notification-toast', 'children', allow_duplicate=True),
    Input('export-selected-btn', 'n_clicks'),
    [State('experimental-sets-table', 'selected_rows'),
     State('experimental-sets-table', 'data')],
    prevent_initial_call=True
)
def export_selected_set(export_clicks, selected_rows, table_data):
    """Export selected experimental set to Excel"""
    if not export_clicks or not selected_rows or not table_data:
        return None
    
    try:
        # Get selected row data
        row_index = selected_rows[0]
        row_data = table_data[row_index]
        set_id = row_data['id']
        set_name = row_data['name']
        
        # Load experimental set from database
        exp_set = ExperimentalSet.objects.get(id=set_id)
        exp_data = exp_set.experimental_data.select_related('dn_assignment').order_by('dn_assignment__dn')
        
        if not exp_data.exists():
            return dbc.Toast(
                [html.P("No experimental data to export.")],
                header="Info",
                is_open=True,
                dismissable=True,
                duration=3000,
                style={"position": "fixed", "top": 66, "right": 10, "width": 350}
            )
        
        return dbc.Toast(
            [html.P(f"Export functionality for '{set_name}' would be implemented here.")],
            header="Info",
            is_open=True,
            dismissable=True,
            duration=4000,
            style={"position": "fixed", "top": 66, "right": 10, "width": 350}
        )
        
    except ExperimentalSet.DoesNotExist:
        return dbc.Toast(
            [html.P("Experimental set not found!")],
            header="Error",
            is_open=True,
            dismissable=True,
            duration=3000,
            style={"position": "fixed", "top": 66, "right": 10, "width": 350}
        )