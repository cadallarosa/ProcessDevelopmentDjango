"""
Layout for Plasma Stability SEC Analysis App
Matrix-style configuration with side-by-side plots and trend analysis
"""

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

app_layout = html.Div([
    # Data stores
    dcc.Store(id='stability-config-store', data=[]),
    dcc.Store(id='id-type-store-ps', data='result_id'),
    dcc.Store(id='monomer-data-store', data=[]),
    dcc.Store(id='conditions-store', data=['Plasma', 'Buffer']),  # Store condition names
    dcc.Store(id='project-id-store', data=''),  # Store project ID

    # Header
    html.Div(
        style={
            'padding': '24px',
            'backgroundColor': '#ffffff',
            'borderBottom': '3px solid #2563eb',
            'boxShadow': '0 2px 12px rgba(0,0,0,0.1)',
            'display': 'flex',
            'justifyContent': 'space-between',
            'alignItems': 'center'
        },
        children=[
            html.Div([
                html.H1("Plasma Stability SEC Analysis", style={
                    'margin': '0',
                    'color': '#2563eb',
                    'fontSize': '32px',
                    'fontWeight': '800'
                }),
                html.P("Track protein stability in plasma vs buffer over time", style={
                    'margin': '8px 0 0 0',
                    'color': '#6b7280',
                    'fontSize': '15px'
                })
            ]),
            html.Button("⚙️ Configure Analysis", id='open-config-modal-btn', style={
                'backgroundColor': '#2563eb',
                'color': 'white',
                'border': 'none',
                'padding': '12px 24px',
                'fontSize': '15px',
                'cursor': 'pointer',
                'borderRadius': '8px',
                'fontWeight': '600',
                'boxShadow': '0 2px 8px rgba(37, 99, 235, 0.3)'
            })
        ]
    ),

    # Configuration Modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Configure Plasma Stability Analysis"), style={'backgroundColor': '#f8fafc'}),
        dbc.ModalBody([
            # Project ID and ID Type
            html.Div(
                style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'marginBottom': '20px'},
                children=[
                    html.Div([
                        html.Label("Project ID:", style={'fontWeight': '600', 'marginBottom': '8px',
                                                        'display': 'block', 'fontSize': '14px'}),
                        dcc.Input(
                            id='project-id-input',
                            type='text',
                            placeholder='e.g., SI-205T2',
                            style={'width': '100%', 'padding': '10px', 'border': '2px solid #d1d5db',
                                   'borderRadius': '8px', 'fontSize': '14px'}
                        )
                    ]),
                    html.Div([
                        html.Label("ID Type:", style={'fontWeight': '600', 'marginBottom': '8px',
                                                     'display': 'block', 'fontSize': '14px'}),
                        dcc.Dropdown(
                            id='id-type-dropdown-ps',
                            options=[
                                {'label': 'Result ID', 'value': 'result_id'},
                                {'label': 'Sample ID', 'value': 'sample_id'}
                            ],
                            value='result_id',
                            clearable=False
                        )
                    ])
                ]
            ),

            # Condition Configuration
            html.Div(
                style={'backgroundColor': '#f8fafc', 'borderRadius': '12px', 'padding': '16px',
                       'marginBottom': '20px', 'border': '2px solid #e5e7eb'},
                children=[
                    html.Div(
                        style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
                               'marginBottom': '12px'},
                        children=[
                            html.Label("Conditions (e.g., Plasma, Buffer, Buffer 1):",
                                      style={'fontWeight': '600', 'fontSize': '14px', 'margin': '0'}),
                            html.Button("🔄 Update Matrix", id='update-conditions-btn', style={
                                'backgroundColor': '#6b7280', 'color': 'white', 'border': 'none',
                                'padding': '8px 16px', 'fontSize': '13px', 'cursor': 'pointer',
                                'borderRadius': '6px', 'fontWeight': '600'
                            })
                        ]
                    ),
                    dcc.Input(
                        id='conditions-input',
                        type='text',
                        placeholder='Enter conditions separated by commas',
                        value='Plasma, Buffer',
                        style={'width': '100%', 'padding': '10px', 'border': '1px solid #d1d5db',
                               'borderRadius': '6px', 'fontSize': '14px'}
                    )
                ]
            ),

            # Matrix Table
            html.Div(id='matrix-table-container', style={'marginBottom': '20px'}),

            # Settings Row (3 columns)
            html.Div(
                style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr 1fr', 'gap': '20px',
                       'marginBottom': '20px', 'padding': '16px', 'backgroundColor': '#f8fafc',
                       'borderRadius': '12px', 'border': '1px solid #e5e7eb'},
                children=[
                    html.Div([
                        html.Label("Channel:", style={'fontWeight': '600', 'marginBottom': '10px',
                                                     'display': 'block', 'fontSize': '14px'}),
                        dcc.Checklist(
                            id='channel-checklist-ps',
                            options=[
                                {'label': ' UV280', 'value': 'channel_1'},
                                {'label': ' UV260', 'value': 'channel_2'}
                            ],
                            value=['channel_1'],
                            labelStyle={'display': 'block', 'marginBottom': '8px'}
                        )
                    ]),
                    html.Div([
                        html.Label("Peak Display:", style={'fontWeight': '600', 'marginBottom': '10px',
                                                          'display': 'block', 'fontSize': '14px'}),
                        dcc.Checklist(
                            id='peak-options-ps',
                            options=[
                                {'label': ' Show Shading', 'value': 'shading'},
                                {'label': ' Show %', 'value': 'percentages'}
                            ],
                            value=[],
                            labelStyle={'display': 'block', 'marginBottom': '8px'}
                        )
                    ]),
                    html.Div([
                        html.Label("Table Data:", style={'fontWeight': '600', 'marginBottom': '10px',
                                                        'display': 'block', 'fontSize': '14px'}),
                        dcc.Checklist(
                            id='table-data-options',
                            options=[
                                {'label': ' Monomer %', 'value': 'monomer'},
                                {'label': ' HMW %', 'value': 'hmw'},
                                {'label': ' LMW %', 'value': 'lmw'}
                            ],
                            value=['monomer'],
                            labelStyle={'display': 'block', 'marginBottom': '8px'}
                        )
                    ])
                ]
            )
        ]),
        dbc.ModalFooter([
            html.Button("📊 Generate Analysis", id='generate-analysis-btn', style={
                'backgroundColor': '#2563eb', 'color': 'white', 'border': 'none',
                'padding': '12px 32px', 'fontSize': '15px', 'cursor': 'pointer',
                'borderRadius': '8px', 'fontWeight': '700',
                'boxShadow': '0 4px 12px rgba(37, 99, 235, 0.3)'
            })
        ])
    ], id='config-modal', size='xl', is_open=False),

    # Main content area
    html.Div(
        style={
            'backgroundColor': '#f1f5f9',
            'minHeight': 'calc(100vh - 120px)',
            'padding': '24px'
        },
        children=[
            # SEC Chromatograms Section (only shows after analysis)
            html.Div(
                id='sec-plots-section',
                children=[]  # Empty initially, populated after analysis
            ),

            # Results Section (also shown after analysis)
            html.Div(
                id='results-section',
                children=[]  # Empty initially, populated after analysis
            )
        ]
    ),

    # Download component
    dcc.Download(id='download-plasma-stability-data')
])
