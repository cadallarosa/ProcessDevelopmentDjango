"""
Improved Experimental Set Management App
Enhanced layout with better organization and user experience
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context, ALL, MATCH, no_update
from django_plotly_dash import DjangoDash
import pandas as pd
import json
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from django.db.models import Q
from plotly_integration.models import LimsDnAssignment

# Initialize the Dash app
app = DjangoDash('ExperimentalSetAppImproved')

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

# Custom styles
CARD_STYLE = {
    'backgroundColor': 'white',
    'borderRadius': '8px',
    'padding': '20px',
    'marginBottom': '20px',
    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
    'border': '1px solid #e0e0e0'
}

HEADER_STYLE = {
    'color': '#0047b3',
    'fontSize': '18px',
    'fontWeight': 'bold',
    'marginBottom': '15px',
    'borderBottom': '2px solid #0047b3',
    'paddingBottom': '8px'
}

BUTTON_PRIMARY = {
    'backgroundColor': '#0047b3',
    'color': 'white',
    'padding': '10px 20px',
    'border': 'none',
    'borderRadius': '5px',
    'cursor': 'pointer',
    'fontSize': '14px',
    'fontWeight': '500',
    'transition': 'all 0.3s'
}

BUTTON_SUCCESS = {
    **BUTTON_PRIMARY,
    'backgroundColor': '#28a745'
}

BUTTON_DANGER = {
    **BUTTON_PRIMARY,
    'backgroundColor': '#dc3545'
}

BUTTON_INFO = {
    **BUTTON_PRIMARY,
    'backgroundColor': '#17a2b8'
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
    dcc.Store(id='experimental-sets-store', storage_type='session'),
    dcc.Store(id='current-set-data', storage_type='session'),
    dcc.Store(id='selected-columns-store', storage_type='session'),
    
    # Main content container
    html.Div([
        # Tabs with enhanced styling
        dcc.Tabs(id='main-tabs', value='view-tab', children=[
            # View Sets Tab
            dcc.Tab(label='View Experiment Sets', value='view-tab', children=[
                html.Div([
                    # Collapsible Set Information Section
                    html.Div([
                        html.Div([
                            html.H3("📋 Set Information", style=HEADER_STYLE),
                            html.Span("▼", id='collapse-info-icon', style={'float': 'right', 'cursor': 'pointer'})
                        ], id='info-header', style={'cursor': 'pointer'}),
                        
                        html.Div([
                            html.Div([
                                html.Div([
                                    html.Label("Set Name *", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                                    dcc.Input(
                                        id='set-name',
                                        type='text',
                                        placeholder='e.g., CEX Optimization Study 1',
                                        style={'width': '100%', 'padding': '10px', 'borderRadius': '5px', 'border': '1px solid #ddd'}
                                    )
                                ], style={'flex': '1', 'marginRight': '15px'}),
                                
                                html.Div([
                                    html.Label("Project ID *", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                                    dcc.Input(
                                        id='set-project-id',
                                        type='text',
                                        placeholder='e.g., PROJ-2024-001',
                                        style={'width': '100%', 'padding': '10px', 'borderRadius': '5px', 'border': '1px solid #ddd'}
                                    )
                                ], style={'flex': '1', 'marginRight': '15px'}),
                                
                                html.Div([
                                    html.Label("Study Type", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                                    dcc.Dropdown(
                                        id='study-type',
                                        options=[
                                            {'label': 'CEX Optimization', 'value': 'cex'},
                                            {'label': 'AEX Optimization', 'value': 'aex'},
                                            {'label': 'HIC Study', 'value': 'hic'},
                                            {'label': 'Protein A', 'value': 'prota'},
                                            {'label': 'Custom', 'value': 'custom'}
                                        ],
                                        placeholder='Select study type',
                                        style={'borderRadius': '5px'}
                                    )
                                ], style={'flex': '1'})
                            ], style={'display': 'flex', 'marginBottom': '15px'}),
                            
                            html.Div([
                                html.Label("Description", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                                dcc.Textarea(
                                    id='set-description',
                                    placeholder='Describe the experimental objectives, variables being tested, and expected outcomes...',
                                    style={'width': '100%', 'padding': '10px', 'borderRadius': '5px', 'border': '1px solid #ddd', 'minHeight': '80px'}
                                )
                            ])
                        ], id='info-content')
                    ], style=CARD_STYLE),
                    
                    # Quick Actions Bar
                    html.Div([
                        html.Button("➕ Add DNs", id='quick-add-dns',
                                   style={**BUTTON_SUCCESS, 'marginRight': '10px'}),
                        html.Button("📊 Import Template", id='import-template',
                                   style={**BUTTON_INFO, 'marginRight': '10px'}),
                        html.Button("⚙️ Column Settings", id='column-settings',
                                   style={**BUTTON_PRIMARY, 'marginRight': '10px'}),
                        html.Button("👁️ Preview Mode", id='preview-mode',
                                   style={**BUTTON_PRIMARY})
                    ], style={'marginBottom': '20px', 'textAlign': 'center'}),
                    
                    # DN Selection with enhanced UI
                    html.Div([
                        html.H3("🔬 Experiment Selection", style=HEADER_STYLE),
                        
                        dcc.Tabs(id='dn-input-tabs', value='manual-tab', children=[
                            dcc.Tab(label='Manual Entry', value='manual-tab', children=[
                                html.Div([
                                    html.P("Enter DN numbers separated by commas or ranges (e.g., DN001-DN005)", 
                                          style={'color': '#666', 'marginBottom': '10px'}),
                                    html.Div([
                                        dcc.Input(
                                            id='dn-input',
                                            type='text',
                                            placeholder='DN001, DN002, DN003 or DN001-DN005',
                                            style={'width': '70%', 'padding': '12px', 'borderRadius': '5px', 
                                                  'border': '1px solid #ddd', 'fontSize': '14px'}
                                        ),
                                        html.Button("Add", id='add-dns-btn',
                                                   style={**BUTTON_SUCCESS, 'marginLeft': '10px', 'verticalAlign': 'top'})
                                    ])
                                ], style={'padding': '20px'})
                            ]),
                            
                            dcc.Tab(label='Search Database', value='search-tab', children=[
                                html.Div([
                                    html.P("Search and select existing DNs from the database", 
                                          style={'color': '#666', 'marginBottom': '10px'}),
                                    dcc.Dropdown(
                                        id='dn-dropdown',
                                        options=[],
                                        multi=True,
                                        placeholder='Type to search DNs, projects, or studies...',
                                        style={'fontSize': '14px'}
                                    ),
                                    html.Div(id='dn-search-stats', style={'marginTop': '10px', 'color': '#666'})
                                ], style={'padding': '20px'})
                            ])
                        ])
                    ], style=CARD_STYLE),
                    
                    # Column Management - Collapsible
                    html.Div([
                        html.Div([
                            html.H3("⚙️ Column Configuration", style=HEADER_STYLE),
                            html.Span("▼", id='collapse-columns-icon', style={'float': 'right', 'cursor': 'pointer'})
                        ], id='columns-header', style={'cursor': 'pointer'}),
                        
                        html.Div([
                            # Column categories with checkboxes
                            html.Div([
                                html.Div([
                                    html.H4("Process Parameters", style={'color': '#0047b3', 'marginBottom': '10px'}),
                                    dcc.Checklist(
                                        id='process-columns-check',
                                        options=[{'label': col['name'], 'value': col['id']} for col in PROCESS_COLUMNS],
                                        value=[col['id'] for col in PROCESS_COLUMNS],
                                        style={'fontSize': '14px'}
                                    )
                                ], style={'flex': '1', 'marginRight': '20px'}),
                                
                                html.Div([
                                    html.H4("Buffer Conditions", style={'color': '#0047b3', 'marginBottom': '10px'}),
                                    dcc.Checklist(
                                        id='buffer-columns-check',
                                        options=[{'label': col['name'], 'value': col['id']} for col in BUFFER_COLUMNS],
                                        value=[col['id'] for col in BUFFER_COLUMNS],
                                        style={'fontSize': '14px'}
                                    )
                                ], style={'flex': '1', 'marginRight': '20px'}),
                                
                                html.Div([
                                    html.H4("Load Parameters", style={'color': '#0047b3', 'marginBottom': '10px'}),
                                    dcc.Checklist(
                                        id='load-columns-check',
                                        options=[{'label': col['name'], 'value': col['id']} for col in LOAD_COLUMNS],
                                        value=[col['id'] for col in LOAD_COLUMNS],
                                        style={'fontSize': '14px'}
                                    )
                                ], style={'flex': '1', 'marginRight': '20px'}),
                                
                                html.Div([
                                    html.H4("Results", style={'color': '#0047b3', 'marginBottom': '10px'}),
                                    dcc.Checklist(
                                        id='results-columns-check',
                                        options=[{'label': col['name'], 'value': col['id']} for col in RESULTS_COLUMNS],
                                        value=[col['id'] for col in RESULTS_COLUMNS],
                                        style={'fontSize': '14px'}
                                    )
                                ], style={'flex': '1', 'marginRight': '20px'}),
                                
                                html.Div([
                                    html.H4("Analytics", style={'color': '#0047b3', 'marginBottom': '10px'}),
                                    dcc.Checklist(
                                        id='analytical-columns-check',
                                        options=[{'label': col['name'], 'value': col['id']} for col in ANALYTICAL_COLUMNS],
                                        value=[col['id'] for col in ANALYTICAL_COLUMNS],
                                        style={'fontSize': '14px'}
                                    )
                                ], style={'flex': '1'})
                            ], style={'display': 'flex', 'marginBottom': '20px'}),
                            
                            # Custom column addition
                            html.Div([
                                html.Hr(style={'margin': '20px 0'}),
                                html.H4("Add Custom Column", style={'color': '#666', 'marginBottom': '10px'}),
                                html.Div([
                                    dcc.Input(
                                        id='custom-column-name',
                                        type='text',
                                        placeholder='Column name',
                                        style={'padding': '8px', 'marginRight': '10px', 'borderRadius': '5px', 'border': '1px solid #ddd'}
                                    ),
                                    dcc.Dropdown(
                                        id='custom-column-type',
                                        options=[
                                            {'label': 'Text', 'value': 'text'},
                                            {'label': 'Numeric', 'value': 'numeric'},
                                            {'label': 'Date', 'value': 'date'}
                                        ],
                                        value='text',
                                        style={'width': '150px', 'display': 'inline-block', 'marginRight': '10px'}
                                    ),
                                    html.Button("Add Column", id='add-column-btn', style=BUTTON_INFO)
                                ], style={'display': 'flex', 'alignItems': 'center'})
                            ])
                        ], id='columns-content', style={'display': 'block'})
                    ], style=CARD_STYLE),
                    
                    # Data Table with enhanced styling
                    html.Div([
                        html.Div([
                            html.H3("📊 Experimental Data", style={**HEADER_STYLE, 'display': 'inline-block'}),
                            html.Div([
                                html.Span(id='table-row-count', style={'color': '#666', 'marginRight': '20px'}),
                                html.Button("Export Excel", id='export-excel', 
                                           style={**BUTTON_SUCCESS, 'padding': '5px 15px', 'fontSize': '12px', 'marginRight': '10px'}),
                                html.Button("Import Data", id='import-data',
                                           style={**BUTTON_INFO, 'padding': '5px 15px', 'fontSize': '12px'}),
                            ], style={'float': 'right'})
                        ], style={'marginBottom': '15px', 'overflow': 'hidden'}),
                        
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
                                style_cell={
                                    'textAlign': 'left',
                                    'padding': '12px',
                                    'fontSize': '13px',
                                    'fontFamily': 'Segoe UI, Arial, sans-serif'
                                },
                                style_header={
                                    'backgroundColor': '#f8f9fa',
                                    'color': '#333',
                                    'fontWeight': 'bold',
                                    'border': '1px solid #dee2e6'
                                },
                                style_data={
                                    'border': '1px solid #dee2e6',
                                    'backgroundColor': 'white'
                                },
                                style_data_conditional=[
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': '#f8f9fa'
                                    },
                                    {
                                        'if': {'state': 'selected'},
                                        'backgroundColor': 'rgba(0, 116, 217, 0.1)',
                                        'border': '1px solid #0074D9'
                                    }
                                ],
                                style_table={'overflowX': 'auto'},
                                export_format='xlsx',
                                export_headers='display'
                            )
                        ], style={'borderRadius': '5px', 'overflow': 'hidden', 'border': '1px solid #dee2e6'}),
                        
                        # Action buttons
                        html.Div([
                            html.Button("💾 Save Set", id='save-set-btn', style={**BUTTON_SUCCESS, 'marginRight': '10px'}),
                            html.Button("📋 Save as Template", id='save-template-btn', style={**BUTTON_INFO, 'marginRight': '10px'}),
                            html.Button("🔄 Clear All", id='clear-all-btn', style=BUTTON_DANGER)
                        ], style={'marginTop': '20px', 'textAlign': 'center'})
                    ], style=CARD_STYLE)
                ], style={'padding': '20px'})
            ]),
            
            # View Sets Tab
            dcc.Tab(label='📂 View Experiment Sets', value='view-tab', children=[
                html.Div([
                    # Search and Filter Bar
                    html.Div([
                        html.H3("🔍 Search Experiment Sets", style=HEADER_STYLE),
                        html.Div([
                            html.Div([
                                dcc.Input(
                                    id='global-search',
                                    type='text',
                                    placeholder='Search all fields...',
                                    style={'width': '100%', 'padding': '10px', 'borderRadius': '5px', 'border': '1px solid #ddd'}
                                )
                            ], style={'flex': '2', 'marginRight': '15px'}),
                            
                            html.Div([
                                dcc.Dropdown(
                                    id='filter-study-type',
                                    options=[
                                        {'label': 'All Types', 'value': 'all'},
                                        {'label': 'CEX', 'value': 'cex'},
                                        {'label': 'AEX', 'value': 'aex'},
                                        {'label': 'HIC', 'value': 'hic'},
                                        {'label': 'Protein A', 'value': 'prota'}
                                    ],
                                    value='all',
                                    placeholder='Study Type',
                                    style={'borderRadius': '5px'}
                                )
                            ], style={'flex': '1', 'marginRight': '15px'}),
                            
                            html.Div([
                                dcc.DatePickerRange(
                                    id='date-range-filter',
                                    start_date_placeholder_text='Start Date',
                                    end_date_placeholder_text='End Date',
                                    style={'borderRadius': '5px'}
                                )
                            ], style={'flex': '1', 'marginRight': '15px'}),
                            
                            html.Button("Search", id='apply-filters-btn', style=BUTTON_PRIMARY)
                        ], style={'display': 'flex', 'alignItems': 'center'})
                    ], style=CARD_STYLE),
                    
                    # Statistics Overview
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H4("Total Sets", style={'color': '#666', 'marginBottom': '5px'}),
                                html.H2(id='total-sets-count', children='0', style={'color': '#0047b3', 'margin': '0'})
                            ], style={'flex': '1', 'textAlign': 'center'}),
                            
                            html.Div([
                                html.H4("Total Experiments", style={'color': '#666', 'marginBottom': '5px'}),
                                html.H2(id='total-experiments-count', children='0', style={'color': '#28a745', 'margin': '0'})
                            ], style={'flex': '1', 'textAlign': 'center'}),
                            
                            html.Div([
                                html.H4("Active Projects", style={'color': '#666', 'marginBottom': '5px'}),
                                html.H2(id='active-projects-count', children='0', style={'color': '#17a2b8', 'margin': '0'})
                            ], style={'flex': '1', 'textAlign': 'center'}),
                            
                            html.Div([
                                html.H4("This Week", style={'color': '#666', 'marginBottom': '5px'}),
                                html.H2(id='week-sets-count', children='0', style={'color': '#ffc107', 'margin': '0'})
                            ], style={'flex': '1', 'textAlign': 'center'})
                        ], style={'display': 'flex', 'padding': '20px'})
                    ], style={**CARD_STYLE, 'background': 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)'}),
                    
                    # Sets Grid
                    html.Div([
                        html.H3("📁 Experiment Sets", style=HEADER_STYLE),
                        html.Div(id='sets-grid-container')
                    ], style=CARD_STYLE)
                ], style={'padding': '20px'})
            ]),
            
            # Analytics Tab
            dcc.Tab(label='📈 Analytics', value='analytics-tab', children=[
                html.Div([
                    html.Div([
                        html.H3("📊 Experimental Analytics Dashboard", style=HEADER_STYLE),
                        html.P("Visualize and compare experimental results across sets", 
                              style={'color': '#666', 'marginBottom': '20px'}),
                        
                        # Charts placeholder
                        html.Div([
                            dcc.Graph(id='yield-comparison-chart'),
                            dcc.Graph(id='purity-trends-chart'),
                            dcc.Graph(id='process-parameters-heatmap')
                        ])
                    ], style=CARD_STYLE)
                ], style={'padding': '20px'})
            ])
        ], style={
            'marginBottom': '30px'
        }, colors={
            "border": "#d6d6d6",
            "primary": "#0047b3",
            "background": "#f8f9fa"
        })
    ], style={'maxWidth': '1400px', 'margin': '0 auto'}),
    
    # Notification Toast
    html.Div(id='notification-toast', style={
        'position': 'fixed',
        'top': '80px',
        'right': '20px',
        'zIndex': 9999,
        'minWidth': '300px'
    }),
    
    # Loading overlay
    dcc.Loading(
        id='loading-overlay',
        type='circle',
        children=html.Div(id='loading-output')
    )
])


# Callbacks for collapsible sections
@app.callback(
    [Output('info-content', 'style'),
     Output('collapse-info-icon', 'children')],
    Input('info-header', 'n_clicks'),
    State('info-content', 'style'),
    prevent_initial_call=True
)
def toggle_info_section(n_clicks, current_style):
    if n_clicks:
        if current_style and current_style.get('display') == 'none':
            return {'display': 'block'}, '▼'
        else:
            return {'display': 'none'}, '▶'
    return {'display': 'block'}, '▼'


@app.callback(
    [Output('columns-content', 'style'),
     Output('collapse-columns-icon', 'children')],
    Input('columns-header', 'n_clicks'),
    State('columns-content', 'style'),
    prevent_initial_call=True
)
def toggle_columns_section(n_clicks, current_style):
    if n_clicks:
        if current_style and current_style.get('display') == 'none':
            return {'display': 'block'}, '▼'
        else:
            return {'display': 'none'}, '▶'
    return {'display': 'block'}, '▼'


# Callback for combining column selections
@app.callback(
    Output('experimental-data-table', 'columns'),
    [Input('process-columns-check', 'value'),
     Input('buffer-columns-check', 'value'),
     Input('load-columns-check', 'value'),
     Input('results-columns-check', 'value'),
     Input('analytical-columns-check', 'value'),
     Input('add-column-btn', 'n_clicks')],
    [State('custom-column-name', 'value'),
     State('custom-column-type', 'value'),
     State('experimental-data-table', 'columns')]
)
def update_table_columns(process_cols, buffer_cols, load_cols, results_cols, analytical_cols,
                         add_click, custom_name, custom_type, current_columns):
    ctx = callback_context
    
    # Combine selected columns
    selected_ids = (process_cols or []) + (buffer_cols or []) + (load_cols or []) + \
                   (results_cols or []) + (analytical_cols or [])
    
    # Filter ALL_COLUMNS based on selection
    selected_columns = [col for col in ALL_COLUMNS if col['id'] in selected_ids]
    
    # Handle custom column addition
    if ctx.triggered and ctx.triggered[0]['prop_id'].split('.')[0] == 'add-column-btn':
        if custom_name:
            new_column = {
                'name': custom_name,
                'id': custom_name.lower().replace(' ', '_'),
                'type': custom_type,
                'editable': True
            }
            # Add custom columns from current state
            for col in current_columns:
                if col['id'] not in [c['id'] for c in ALL_COLUMNS] and col['id'] != new_column['id']:
                    selected_columns.append(col)
            selected_columns.append(new_column)
            return selected_columns
    
    # Preserve custom columns
    for col in (current_columns or []):
        if col['id'] not in [c['id'] for c in ALL_COLUMNS]:
            selected_columns.append(col)
    
    return selected_columns


# Enhanced notification system
@app.callback(
    Output('notification-toast', 'children'),
    [Input('add-dns-btn', 'n_clicks'),
     Input('save-set-btn', 'n_clicks')],
    [State('dn-input', 'value'),
     State('set-name', 'value')],
    prevent_initial_call=True
)
def show_notification(add_click, save_click, dn_input, set_name):
    ctx = callback_context
    if not ctx.triggered:
        return None
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'add-dns-btn' and dn_input:
        return html.Div([
            html.Div([
                html.Strong("✓ Success", style={'marginRight': '10px'}),
                f"DNs added successfully"
            ], style={
                'backgroundColor': '#28a745',
                'color': 'white',
                'padding': '15px',
                'borderRadius': '5px',
                'boxShadow': '0 4px 6px rgba(0,0,0,0.1)',
                'animation': 'slideIn 0.3s ease-out'
            })
        ])
    
    elif trigger_id == 'save-set-btn' and set_name:
        return html.Div([
            html.Div([
                html.Strong("✓ Saved", style={'marginRight': '10px'}),
                f"Set '{set_name}' saved successfully"
            ], style={
                'backgroundColor': '#28a745',
                'color': 'white',
                'padding': '15px',
                'borderRadius': '5px',
                'boxShadow': '0 4px 6px rgba(0,0,0,0.1)',
                'animation': 'slideIn 0.3s ease-out'
            })
        ])
    
    return None


# Row count display
@app.callback(
    Output('table-row-count', 'children'),
    Input('experimental-data-table', 'data')
)
def update_row_count(data):
    count = len(data) if data else 0
    return f"{count} experiments"


# DN dropdown update callback
@app.callback(
    Output('dn-dropdown', 'options'),
    Input('dn-dropdown', 'search_value')
)
def update_dn_dropdown(search_value):
    """Update DN dropdown options based on search"""
    if not search_value:
        return []

    try:
        # Query existing DNs from database
        dns = LimsDnAssignment.objects.filter(
            Q(dn__icontains=search_value) |
            Q(project_id__icontains=search_value)
        ).values('dn', 'project_id', 'study_name')[:20]

        options = [
            {
                'label': f"DN{dn['dn']} - {dn['project_id']} - {dn['study_name']}",
                'value': f"DN{dn['dn']}"
            }
            for dn in dns
        ]
        return options
    except:
        return []


# Add DNs to table callback
@app.callback(
    [Output('experimental-data-table', 'data'),
     Output('dn-search-stats', 'children')],
    [Input('add-dns-btn', 'n_clicks'),
     Input('dn-dropdown', 'value')],
    [State('dn-input', 'value'),
     State('experimental-data-table', 'data')]
)
def add_dns_to_table(add_clicks, dropdown_dns, dn_input, current_data):
    """Add DNs to the experimental data table"""
    
    ctx = callback_context
    if not ctx.triggered:
        return current_data or [], None
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    stats_message = None
    
    # Handle adding DNs from input
    if trigger_id == 'add-dns-btn' and dn_input:
        dns = []
        # Parse comma-separated and ranges
        parts = [p.strip() for p in dn_input.split(',')]
        for part in parts:
            if '-' in part and 'DN' in part:
                # Handle range like DN001-DN005
                try:
                    start_dn = part.split('-')[0].strip()
                    end_dn = part.split('-')[1].strip()
                    start_num = int(start_dn.replace('DN', ''))
                    end_num = int(end_dn.replace('DN', ''))
                    for i in range(start_num, end_num + 1):
                        dns.append(f'DN{i:03d}')
                except:
                    dns.append(part)
            else:
                dns.append(part)
        
        new_rows = []
        for dn in dns:
            if not any(row.get('dn') == dn for row in (current_data or [])):
                new_rows.append({'dn': dn})
        
        if new_rows:
            current_data = (current_data or []) + new_rows
            stats_message = f"Added {len(new_rows)} DN(s)"
    
    # Handle adding DNs from dropdown
    elif trigger_id == 'dn-dropdown' and dropdown_dns:
        new_rows = []
        for dn in dropdown_dns:
            if not any(row.get('dn') == dn for row in (current_data or [])):
                new_rows.append({'dn': dn})
        
        if new_rows:
            current_data = (current_data or []) + new_rows
            stats_message = f"Added {len(new_rows)} DN(s) from database"
    
    return current_data or [], stats_message


# Save experimental set callback
@app.callback(
    Output('experimental-sets-store', 'data'),
    [Input('save-set-btn', 'n_clicks')],
    [State('set-name', 'value'),
     State('set-project-id', 'value'),
     State('set-description', 'value'),
     State('study-type', 'value'),
     State('experimental-data-table', 'data'),
     State('experimental-data-table', 'columns'),
     State('experimental-sets-store', 'data')]
)
def save_experimental_set(n_clicks, set_name, project_id, description, study_type, 
                         table_data, columns, stored_sets):
    """Save the current experimental set"""
    if not n_clicks or not set_name:
        return stored_sets or {}
    
    # Create set object
    new_set = {
        'name': set_name,
        'project_id': project_id,
        'description': description,
        'study_type': study_type,
        'data': table_data,
        'columns': columns,
        'created_at': datetime.now().isoformat(),
        'dn_count': len(table_data)
    }
    
    # Update stored sets
    if stored_sets is None:
        stored_sets = {}
    
    stored_sets[set_name] = new_set
    return stored_sets


# Display experimental sets with enhanced cards
@app.callback(
    [Output('sets-grid-container', 'children'),
     Output('total-sets-count', 'children'),
     Output('total-experiments-count', 'children'),
     Output('active-projects-count', 'children')],
    [Input('apply-filters-btn', 'n_clicks'),
     Input('experimental-sets-store', 'data')],
    [State('global-search', 'value'),
     State('filter-study-type', 'value')]
)
def display_experimental_sets(n_clicks, stored_sets, search_text, study_type_filter):
    """Display the list of experimental sets with filtering"""
    
    if not stored_sets:
        return html.Div([
            html.P("No experimental sets defined yet. Create your first set in the 'Define Set' tab.",
                   style={'color': '#666', 'fontStyle': 'italic', 'textAlign': 'center', 'padding': '40px'})
        ]), '0', '0', '0'
    
    # Apply filters
    filtered_sets = []
    total_experiments = 0
    unique_projects = set()
    
    for set_name, set_data in stored_sets.items():
        # Check search filter
        if search_text:
            search_lower = search_text.lower()
            if not any([
                search_lower in set_name.lower(),
                search_lower in set_data.get('project_id', '').lower(),
                search_lower in set_data.get('description', '').lower()
            ]):
                continue
        
        # Check study type filter
        if study_type_filter and study_type_filter != 'all':
            if set_data.get('study_type') != study_type_filter:
                continue
        
        filtered_sets.append((set_name, set_data))
        total_experiments += set_data.get('dn_count', 0)
        if set_data.get('project_id'):
            unique_projects.add(set_data.get('project_id'))
    
    if not filtered_sets:
        return html.Div([
            html.P("No sets match the current filters.",
                   style={'color': '#666', 'fontStyle': 'italic', 'textAlign': 'center', 'padding': '40px'})
        ]), '0', '0', '0'
    
    # Create enhanced set cards
    set_cards = []
    for set_name, set_data in filtered_sets:
        # Determine study type badge color
        study_type = set_data.get('study_type', 'custom')
        badge_colors = {
            'cex': '#28a745',
            'aex': '#17a2b8',
            'hic': '#ffc107',
            'prota': '#6c757d',
            'custom': '#6610f2'
        }
        
        card = html.Div([
            # Card header with study type badge
            html.Div([
                html.Span(study_type.upper(), style={
                    'backgroundColor': badge_colors.get(study_type, '#6c757d'),
                    'color': 'white',
                    'padding': '4px 8px',
                    'borderRadius': '4px',
                    'fontSize': '11px',
                    'fontWeight': 'bold',
                    'float': 'right'
                }),
                html.H4(set_name, style={'color': '#0047b3', 'marginBottom': '10px', 'marginRight': '60px'})
            ]),
            
            # Card body
            html.Div([
                html.Div([
                    html.Strong("Project: "),
                    html.Span(set_data.get('project_id', 'N/A'))
                ], style={'marginBottom': '8px'}),
                
                html.Div([
                    html.Strong("Description: "),
                    html.Span(set_data.get('description', 'No description')[:100] + '...' 
                             if len(set_data.get('description', '')) > 100 else set_data.get('description', 'No description'))
                ], style={'marginBottom': '8px', 'fontSize': '14px', 'color': '#666'}),
                
                html.Div([
                    html.Div([
                        html.Span("🧪", style={'fontSize': '20px', 'marginRight': '5px'}),
                        html.Span(f"{set_data.get('dn_count', 0)} experiments", 
                                 style={'fontSize': '14px', 'fontWeight': 'bold'})
                    ], style={'display': 'inline-block', 'marginRight': '20px'}),
                    
                    html.Div([
                        html.Span("📅", style={'fontSize': '16px', 'marginRight': '5px'}),
                        html.Span(set_data.get('created_at', 'N/A')[:10] if set_data.get('created_at') else 'N/A',
                                 style={'fontSize': '12px', 'color': '#666'})
                    ], style={'display': 'inline-block'})
                ], style={'marginTop': '10px', 'marginBottom': '15px'}),
                
                # Action buttons
                html.Div([
                    html.Button("View Details",
                               id={'type': 'view-set-btn', 'index': set_name},
                               style={
                                   'backgroundColor': '#0047b3',
                                   'color': 'white',
                                   'padding': '6px 12px',
                                   'border': 'none',
                                   'borderRadius': '4px',
                                   'cursor': 'pointer',
                                   'marginRight': '8px',
                                   'fontSize': '13px'
                               }),
                    html.Button("Edit",
                               id={'type': 'edit-set-btn', 'index': set_name},
                               style={
                                   'backgroundColor': '#17a2b8',
                                   'color': 'white',
                                   'padding': '6px 12px',
                                   'border': 'none',
                                   'borderRadius': '4px',
                                   'cursor': 'pointer',
                                   'marginRight': '8px',
                                   'fontSize': '13px'
                               }),
                    html.Button("Export",
                               id={'type': 'export-set-btn', 'index': set_name},
                               style={
                                   'backgroundColor': '#28a745',
                                   'color': 'white',
                                   'padding': '6px 12px',
                                   'border': 'none',
                                   'borderRadius': '4px',
                                   'cursor': 'pointer',
                                   'fontSize': '13px'
                               })
                ])
            ])
        ], className='experiment-card', style={
            'backgroundColor': 'white',
            'borderRadius': '8px',
            'padding': '20px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'border': '1px solid #e0e0e0',
            'transition': 'all 0.3s ease'
        })
        
        set_cards.append(card)
    
    # Create grid layout
    grid_container = html.Div(set_cards, className='experiment-grid', style={
        'display': 'grid',
        'gridTemplateColumns': 'repeat(auto-fill, minmax(350px, 1fr))',
        'gap': '20px'
    })
    
    return grid_container, str(len(filtered_sets)), str(total_experiments), str(len(unique_projects))


# Clear table callback
@app.callback(
    [Output('experimental-data-table', 'data', allow_duplicate=True),
     Output('set-name', 'value'),
     Output('set-project-id', 'value'),
     Output('set-description', 'value'),
     Output('dn-input', 'value')],
    [Input('clear-all-btn', 'n_clicks')],
    prevent_initial_call=True
)
def clear_all_data(n_clicks):
    """Clear all form data and table"""
    if n_clicks:
        return [], '', '', '', ''
    return no_update