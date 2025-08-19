"""
Experimental Set Management App
Based on DN Assignment App - Groups experiments into sets with all variables tracked
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context, ALL, MATCH
from django_plotly_dash import DjangoDash
import pandas as pd
import json
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from django.db.models import Q
from plotly_integration.models import LimsDnAssignment

# Initialize the Dash app
app = DjangoDash('ExperimentalSetApp')

# Define the experimental variables columns
EXPERIMENTAL_COLUMNS = [
    {'name': 'DN', 'id': 'dn', 'type': 'text', 'editable': False},
    {'name': 'Resin', 'id': 'resin', 'type': 'text', 'editable': True},
    {'name': 'Description', 'id': 'description', 'type': 'text', 'editable': True},
    {'name': 'CV (mL)', 'id': 'cv_ml', 'type': 'numeric', 'editable': True},
    {'name': 'Residence Time (min)', 'id': 'residence_time', 'type': 'numeric', 'editable': True},
    {'name': 'Elution Condition', 'id': 'elution_condition', 'type': 'text', 'editable': True},
    {'name': 'EQ', 'id': 'eq', 'type': 'text', 'editable': True},
    {'name': 'Wash Condition', 'id': 'wash_condition', 'type': 'text', 'editable': True},
    {'name': 'Load Density (mg/mL)', 'id': 'load_density', 'type': 'numeric', 'editable': True},
    {'name': 'Product Required (mg)', 'id': 'product_required', 'type': 'numeric', 'editable': True},
    {'name': 'Load Volume (mL)', 'id': 'load_volume', 'type': 'numeric', 'editable': True},
    {'name': 'Eluate Volume (mL)', 'id': 'eluate_volume', 'type': 'numeric', 'editable': True},
    {'name': 'Eluate Concentration (mg/mL)', 'id': 'eluate_concentration', 'type': 'numeric', 'editable': True},
    {'name': 'Eluate Amount (mg)', 'id': 'eluate_amount', 'type': 'numeric', 'editable': True},
    {'name': 'Yield (%)', 'id': 'yield_percent', 'type': 'numeric', 'editable': True},
    {'name': '% MP SEC', 'id': 'mp_sec_percent', 'type': 'numeric', 'editable': True},
    {'name': 'PPM HCP', 'id': 'ppm_hcp', 'type': 'numeric', 'editable': True},
    {'name': 'PPB DNA', 'id': 'ppb_dna', 'type': 'numeric', 'editable': True}
]

# App layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("Experimental Set Management",
                style={'color': '#0047b3', 'marginBottom': '20px'}),
        html.P("Group DN experiments into sets and track experimental variables",
               style={'color': '#666', 'fontSize': '14px'})
    ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#f8f9fa'}),

    # Store components for data persistence
    dcc.Store(id='experimental-sets-store', storage_type='session'),
    dcc.Store(id='current-set-data', storage_type='session'),
    dcc.Store(id='selected-dns-store', storage_type='session'),

    # Tabs for View and Define functionality
    dcc.Tabs(id='main-tabs', value='view-tab', children=[
        # View Experiments Tab
        dcc.Tab(label='View Experiment Sets', value='view-tab', children=[
            html.Div([
                # Filter controls
                html.Div([
                    html.H3("Filter Sets", style={'color': '#0047b3', 'marginBottom': '15px'}),

                    html.Div([
                        html.Div([
                            html.Label("Project ID:", style={'fontWeight': 'bold'}),
                            dcc.Input(
                                id='filter-project-id',
                                type='text',
                                placeholder='Enter project ID...',
                                style={'width': '100%', 'padding': '8px', 'marginBottom': '10px'}
                            )
                        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '2%'}),

                        html.Div([
                            html.Label("Description:", style={'fontWeight': 'bold'}),
                            dcc.Input(
                                id='filter-description',
                                type='text',
                                placeholder='Search description...',
                                style={'width': '100%', 'padding': '8px', 'marginBottom': '10px'}
                            )
                        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '2%'}),

                        html.Div([
                            html.Label("Steps:", style={'fontWeight': 'bold'}),
                            dcc.Input(
                                id='filter-steps',
                                type='text',
                                placeholder='Filter by steps...',
                                style={'width': '100%', 'padding': '8px', 'marginBottom': '10px'}
                            )
                        ], style={'width': '30%', 'display': 'inline-block'})
                    ]),

                    html.Button("Apply Filters", id='apply-filters-btn',
                                style={
                                    'backgroundColor': '#0047b3',
                                    'color': 'white',
                                    'padding': '10px 20px',
                                    'border': 'none',
                                    'borderRadius': '5px',
                                    'cursor': 'pointer',
                                    'marginTop': '10px'
                                })
                ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '10px',
                          'marginBottom': '20px'}),

                # Experimental Sets List
                html.Div([
                    html.H3("Experimental Sets", style={'color': '#0047b3', 'marginBottom': '15px'}),
                    html.Div(id='sets-list-container')
                ], style={'padding': '20px'})
            ])
        ]),

        # Define Set Tab
        dcc.Tab(label='Define Set', value='define-tab', children=[
            html.Div([
                # Set Information
                html.Div([
                    html.H3("Set Information", style={'color': '#0047b3', 'marginBottom': '15px'}),

                    html.Div([
                        html.Div([
                            html.Label("Set Name:", style={'fontWeight': 'bold'}),
                            dcc.Input(
                                id='set-name',
                                type='text',
                                placeholder='Enter set name...',
                                style={'width': '100%', 'padding': '8px'}
                            )
                        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '2%'}),

                        html.Div([
                            html.Label("Project ID:", style={'fontWeight': 'bold'}),
                            dcc.Input(
                                id='set-project-id',
                                type='text',
                                placeholder='Enter project ID...',
                                style={'width': '100%', 'padding': '8px'}
                            )
                        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '2%'}),

                        html.Div([
                            html.Label("Description:", style={'fontWeight': 'bold'}),
                            dcc.Input(
                                id='set-description',
                                type='text',
                                placeholder='Enter description...',
                                style={'width': '100%', 'padding': '8px'}
                            )
                        ], style={'width': '30%', 'display': 'inline-block'})
                    ], style={'marginBottom': '20px'})
                ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '10px',
                          'marginBottom': '20px'}),

                # DN Selection
                html.Div([
                    html.H3("Add DN Numbers", style={'color': '#0047b3', 'marginBottom': '15px'}),

                    html.Div([
                        html.Div([
                            html.Label("Enter DN Numbers (comma-separated):", style={'fontWeight': 'bold'}),
                            dcc.Input(
                                id='dn-input',
                                type='text',
                                placeholder='e.g., DN001, DN002, DN003...',
                                style={'width': '70%', 'padding': '8px', 'marginRight': '10px'}
                            ),
                            html.Button("Add DNs", id='add-dns-btn',
                                        style={
                                            'backgroundColor': '#28a745',
                                            'color': 'white',
                                            'padding': '8px 15px',
                                            'border': 'none',
                                            'borderRadius': '5px',
                                            'cursor': 'pointer'
                                        })
                        ], style={'marginBottom': '10px'}),

                        html.Div([
                            html.Label("Or search existing DNs:", style={'fontWeight': 'bold'}),
                            dcc.Dropdown(
                                id='dn-dropdown',
                                options=[],
                                multi=True,
                                placeholder='Search and select DNs...',
                                style={'width': '100%'}
                            )
                        ])
                    ])
                ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '10px',
                          'marginBottom': '20px'}),

                # Column Management
                html.Div([
                    html.H3("Manage Columns", style={'color': '#0047b3', 'marginBottom': '15px'}),

                    html.Div([
                        dcc.Dropdown(
                            id='column-selector',
                            options=[{'label': col['name'], 'value': col['id']} for col in EXPERIMENTAL_COLUMNS],
                            value=[col['id'] for col in EXPERIMENTAL_COLUMNS],
                            multi=True,
                            placeholder='Select columns to display...',
                            style={'marginBottom': '10px'}
                        ),

                        html.Div([
                            html.Button("Add Custom Column", id='add-column-btn',
                                        style={
                                            'backgroundColor': '#17a2b8',
                                            'color': 'white',
                                            'padding': '8px 15px',
                                            'border': 'none',
                                            'borderRadius': '5px',
                                            'cursor': 'pointer',
                                            'marginRight': '10px'
                                        }),
                            dcc.Input(
                                id='custom-column-name',
                                type='text',
                                placeholder='Custom column name...',
                                style={'padding': '8px', 'marginRight': '10px'}
                            ),
                            dcc.Dropdown(
                                id='custom-column-type',
                                options=[
                                    {'label': 'Text', 'value': 'text'},
                                    {'label': 'Numeric', 'value': 'numeric'}
                                ],
                                value='text',
                                style={'width': '150px', 'display': 'inline-block'}
                            )
                        ], style={'display': 'inline-block'})
                    ])
                ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '10px',
                          'marginBottom': '20px'}),

                # Data Table
                html.Div([
                    html.H3("Experimental Data", style={'color': '#0047b3', 'marginBottom': '15px'}),

                    dash_table.DataTable(
                        id='experimental-data-table',
                        columns=EXPERIMENTAL_COLUMNS,
                        data=[],
                        editable=True,
                        row_deletable=True,
                        style_cell={
                            'textAlign': 'left',
                            'padding': '10px',
                            'fontSize': '14px'
                        },
                        style_header={
                            'backgroundColor': '#0047b3',
                            'color': 'white',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': '#f8f9fa'
                            }
                        ],
                        page_size=20,
                        export_format='xlsx',
                        export_headers='display'
                    ),

                    html.Div([
                        html.Button("Save Set", id='save-set-btn',
                                    style={
                                        'backgroundColor': '#28a745',
                                        'color': 'white',
                                        'padding': '10px 20px',
                                        'border': 'none',
                                        'borderRadius': '5px',
                                        'cursor': 'pointer',
                                        'marginRight': '10px',
                                        'marginTop': '20px'
                                    }),
                        html.Button("Clear All", id='clear-all-btn',
                                    style={
                                        'backgroundColor': '#dc3545',
                                        'color': 'white',
                                        'padding': '10px 20px',
                                        'border': 'none',
                                        'borderRadius': '5px',
                                        'cursor': 'pointer',
                                        'marginTop': '20px'
                                    })
                    ])
                ], style={'padding': '20px'})
            ])
        ])
    ]),

    # Notification area
    html.Div(id='notification-area', style={'position': 'fixed', 'top': '20px', 'right': '20px', 'zIndex': 1000})
])


# Callbacks
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


@app.callback(
    [Output('experimental-data-table', 'data'),
     Output('experimental-data-table', 'columns'),
     Output('notification-area', 'children')],
    [Input('add-dns-btn', 'n_clicks'),
     Input('dn-dropdown', 'value'),
     Input('column-selector', 'value'),
     Input('add-column-btn', 'n_clicks')],
    [State('dn-input', 'value'),
     State('experimental-data-table', 'data'),
     State('experimental-data-table', 'columns'),
     State('custom-column-name', 'value'),
     State('custom-column-type', 'value')]
)
def update_table(add_clicks, dropdown_dns, selected_columns, add_col_clicks,
                 dn_input, current_data, current_columns, custom_col_name, custom_col_type):
    """Update the experimental data table"""

    ctx = callback_context
    if not ctx.triggered:
        return current_data or [], EXPERIMENTAL_COLUMNS, None

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    notification = None

    # Handle adding DNs from input
    if trigger_id == 'add-dns-btn' and dn_input:
        dns = [dn.strip() for dn in dn_input.split(',')]
        new_rows = []
        for dn in dns:
            if not any(row.get('dn') == dn for row in (current_data or [])):
                new_rows.append({'dn': dn})

        if new_rows:
            current_data = (current_data or []) + new_rows
            notification = html.Div([
                html.P(f"Added {len(new_rows)} DN(s)",
                       style={'backgroundColor': '#28a745', 'color': 'white',
                              'padding': '10px', 'borderRadius': '5px'})
            ])

    # Handle adding DNs from dropdown
    elif trigger_id == 'dn-dropdown' and dropdown_dns:
        new_rows = []
        for dn in dropdown_dns:
            if not any(row.get('dn') == dn for row in (current_data or [])):
                new_rows.append({'dn': dn})

        if new_rows:
            current_data = (current_data or []) + new_rows
            notification = html.Div([
                html.P(f"Added {len(new_rows)} DN(s) from selection",
                       style={'backgroundColor': '#28a745', 'color': 'white',
                              'padding': '10px', 'borderRadius': '5px'})
            ])

    # Handle column selection
    elif trigger_id == 'column-selector' and selected_columns is not None:
        # Filter columns based on selection
        filtered_columns = [col for col in EXPERIMENTAL_COLUMNS if col['id'] in selected_columns]
        # Add any custom columns that exist
        for col in current_columns:
            if col['id'] not in [c['id'] for c in EXPERIMENTAL_COLUMNS]:
                if col['id'] in selected_columns:
                    filtered_columns.append(col)
        return current_data or [], filtered_columns, None

    # Handle adding custom column
    elif trigger_id == 'add-column-btn' and custom_col_name:
        new_column = {
            'name': custom_col_name,
            'id': custom_col_name.lower().replace(' ', '_'),
            'type': custom_col_type,
            'editable': True
        }
        if not any(col['id'] == new_column['id'] for col in current_columns):
            current_columns.append(new_column)
            notification = html.Div([
                html.P(f"Added custom column: {custom_col_name}",
                       style={'backgroundColor': '#17a2b8', 'color': 'white',
                              'padding': '10px', 'borderRadius': '5px'})
            ])

    return current_data or [], current_columns, notification


@app.callback(
    Output('experimental-sets-store', 'data'),
    [Input('save-set-btn', 'n_clicks')],
    [State('set-name', 'value'),
     State('set-project-id', 'value'),
     State('set-description', 'value'),
     State('experimental-data-table', 'data'),
     State('experimental-data-table', 'columns'),
     State('experimental-sets-store', 'data')]
)
def save_experimental_set(n_clicks, set_name, project_id, description, table_data, columns, stored_sets):
    """Save the current experimental set"""
    if not n_clicks or not set_name:
        return stored_sets or {}

    # Create set object
    new_set = {
        'name': set_name,
        'project_id': project_id,
        'description': description,
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


@app.callback(
    Output('sets-list-container', 'children'),
    [Input('apply-filters-btn', 'n_clicks'),
     Input('experimental-sets-store', 'data')],
    [State('filter-project-id', 'value'),
     State('filter-description', 'value'),
     State('filter-steps', 'value')]
)
def display_experimental_sets(n_clicks, stored_sets, filter_project, filter_desc, filter_steps):
    """Display the list of experimental sets with filtering"""

    if not stored_sets:
        return html.Div([
            html.P("No experimental sets defined yet.",
                   style={'color': '#666', 'fontStyle': 'italic'})
        ])

    # Apply filters
    filtered_sets = []
    for set_name, set_data in stored_sets.items():
        # Check filters
        if filter_project and filter_project.lower() not in set_data.get('project_id', '').lower():
            continue
        if filter_desc and filter_desc.lower() not in set_data.get('description', '').lower():
            continue
        if filter_steps:
            # Add step filtering logic here if needed
            pass

        filtered_sets.append((set_name, set_data))

    if not filtered_sets:
        return html.Div([
            html.P("No sets match the current filters.",
                   style={'color': '#666', 'fontStyle': 'italic'})
        ])

    # Create set cards
    set_cards = []
    for set_name, set_data in filtered_sets:
        card = html.Div([
            html.Div([
                html.H4(set_name, style={'color': '#0047b3', 'marginBottom': '10px'}),
                html.P(f"Project: {set_data.get('project_id', 'N/A')}",
                       style={'marginBottom': '5px', 'fontWeight': 'bold'}),
                html.P(f"Description: {set_data.get('description', 'N/A')}",
                       style={'marginBottom': '5px'}),
                html.P(f"DN Count: {set_data.get('dn_count', 0)}",
                       style={'marginBottom': '5px'}),
                html.P(f"Created: {set_data.get('created_at', 'N/A')}",
                       style={'fontSize': '12px', 'color': '#666'}),
                html.Div([
                    html.Button("View Details",
                                id={'type': 'view-set-btn', 'index': set_name},
                                style={
                                    'backgroundColor': '#0047b3',
                                    'color': 'white',
                                    'padding': '5px 15px',
                                    'border': 'none',
                                    'borderRadius': '5px',
                                    'cursor': 'pointer',
                                    'marginRight': '10px'
                                }),
                    html.Button("Export",
                                id={'type': 'export-set-btn', 'index': set_name},
                                style={
                                    'backgroundColor': '#28a745',
                                    'color': 'white',
                                    'padding': '5px 15px',
                                    'border': 'none',
                                    'borderRadius': '5px',
                                    'cursor': 'pointer'
                                })
                ], style={'marginTop': '10px'})
            ], style={
                'padding': '15px',
                'backgroundColor': '#f8f9fa',
                'borderRadius': '10px',
                'marginBottom': '15px',
                'border': '1px solid #dee2e6'
            })
        ])
        set_cards.append(card)

    return html.Div(set_cards)


@app.callback(
    [Output('experimental-data-table', 'data', allow_duplicate=True),
     Output('experimental-data-table', 'columns', allow_duplicate=True)],
    [Input('clear-all-btn', 'n_clicks')],
    prevent_initial_call=True
)
def clear_table(n_clicks):
    """Clear the experimental data table"""
    if n_clicks:
        return [], EXPERIMENTAL_COLUMNS
    return dash.no_update


# Additional callback for viewing set details
@app.callback(
    Output('main-tabs', 'value'),
    [Input({'type': 'view-set-btn', 'index': ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def switch_to_define_tab(n_clicks):
    """Switch to define tab when viewing a set"""
    if any(n_clicks):
        return 'define-tab'
    return dash.no_update
