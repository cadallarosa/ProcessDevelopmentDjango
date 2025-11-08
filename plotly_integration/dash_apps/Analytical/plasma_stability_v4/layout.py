"""
Layout for Plasma Stability SEC Analysis App V4
Excel template-based workflow with automated summary generation
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

app_layout = html.Div([
    # Data stores
    dcc.Store(id='template-data-store', data=None),
    dcc.Store(id='summary-config-store', data=None),  # V4: Slide configuration
    dcc.Store(id='analysis-results-store', data=None),
    dcc.Store(id='channel-settings-store', data=['channel_1']),
    dcc.Store(id='show-trend-store', data=False),
    dcc.Store(id='x-axis-range-store', data=[4, 12]),
    dcc.Store(id='image-height-store', data=225),
    dcc.Store(id='plot-width-store', data=600),  # 600px height in container div
    dcc.Store(id='plot-mode-store', data='subplots'),  # V4: Plot mode (overlay/subplots) - default to subplots
    # Sample ID Lookup stores
    dcc.Store(id='sample-lookup-results-store', data=None),

    # Header
    html.Div(
        style={
            'padding': '24px',
            'backgroundColor': '#ffffff',
            'borderBottom': '3px solid #2563eb',
            'boxShadow': '0 2px 12px rgba(0,0,0,0.1)',
        },
        children=[
            html.Div(
                style={'maxWidth': '1400px', 'margin': '0 auto'},
                children=[
                    html.H1("Plasma Stability SEC Analysis V4", style={
                        'margin': '0',
                        'color': '#2563eb',
                        'fontSize': '32px',
                        'fontWeight': '800'
                    })
                ]
            )
        ]
    ),

    # Control Buttons Section (above tabs)
    html.Div(
        style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '20px 24px 0 24px'},
        children=[
            # Control buttons
            html.Div(
                style={'display': 'flex', 'gap': '12px', 'padding': '0 0 16px 0', 'justifyContent': 'flex-start', 'flexWrap': 'wrap'},
                children=[
                    html.Button("Download Template", id='download-template-btn', style={
                        'backgroundColor': '#10b981',
                        'color': 'white',
                        'border': 'none',
                        'padding': '12px 24px',
                        'fontSize': '15px',
                        'cursor': 'pointer',
                        'borderRadius': '8px',
                        'fontWeight': '600',
                        'boxShadow': '0 2px 8px rgba(16, 185, 129, 0.3)'
                    }),
                    dcc.Upload(
                        id='upload-template',
                        children=html.Button("Upload Template", style={
                            'backgroundColor': '#2563eb',
                            'color': 'white',
                            'border': 'none',
                            'padding': '12px 24px',
                            'fontSize': '15px',
                            'cursor': 'pointer',
                            'borderRadius': '8px',
                            'fontWeight': '600',
                            'boxShadow': '0 2px 8px rgba(37, 99, 235, 0.3)'
                        }),
                        multiple=False
                    ),
                    html.Button("Configure Settings", id='open-settings-modal-btn', style={
                        'backgroundColor': '#6b7280',
                        'color': 'white',
                        'border': 'none',
                        'padding': '12px 24px',
                        'fontSize': '15px',
                        'cursor': 'pointer',
                        'borderRadius': '8px',
                        'fontWeight': '600',
                        'boxShadow': '0 2px 8px rgba(107, 114, 128, 0.3)'
                    }),
                    html.Button("Sample ID Lookup", id='open-sample-lookup-modal-btn', style={
                        'backgroundColor': '#8b5cf6',
                        'color': 'white',
                        'border': 'none',
                        'padding': '12px 24px',
                        'fontSize': '15px',
                        'cursor': 'pointer',
                        'borderRadius': '8px',
                        'fontWeight': '600',
                        'boxShadow': '0 2px 8px rgba(139, 92, 246, 0.3)'
                    }),
                    html.Div(
                        id='export-ppt-btn-container',
                        style={'display': 'none'},
                        children=html.Button("Export to PowerPoint", id='export-ppt-btn', style={
                            'backgroundColor': '#dc2626',
                            'color': 'white',
                            'border': 'none',
                            'padding': '12px 24px',
                            'fontSize': '15px',
                            'cursor': 'pointer',
                            'borderRadius': '8px',
                            'fontWeight': '600',
                            'boxShadow': '0 2px 8px rgba(220, 38, 38, 0.3)'
                        })
                    )
                ]
            ),
            # Upload Status
            html.Div(id='upload-status', style={'marginBottom': '8px'}),
            # Toast Notification Container
            html.Div(id='toast-container', style={
                'position': 'fixed',
                'top': '20px',
                'right': '20px',
                'zIndex': '9999'
            }),
            # PPT Export Loading Toast
            dbc.Toast(
                id="ppt-export-loading-toast",
                header="Generating PowerPoint",
                children=html.Div([
                    dbc.Spinner(size="sm", color="primary", spinner_style={'marginRight': '8px'}),
                    html.Span("This may take a moment... Please wait.")
                ], style={'display': 'flex', 'alignItems': 'center'}),
                is_open=False,
                dismissable=False,
                duration=None,
                icon="info",
                style={'position': 'fixed', 'top': 80, 'right': 20, 'minWidth': '350px', 'zIndex': 10000}
            )
        ]
    ),

    # Tabs
    html.Div(
        style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '0 24px'},
        children=[
            dcc.Tabs(
                id='main-tabs',
                value='tab-analysis',
                children=[
                    # Tab 1: Standard Analysis
                    dcc.Tab(
                        label='Standard Analysis',
                        value='tab-analysis',
                        style={'padding': '12px 24px', 'fontWeight': '600'},
                        selected_style={'padding': '12px 24px', 'fontWeight': '600', 'borderTop': '3px solid #2563eb'},
                        children=[
                            # Results Container with Loading Indicator
                            html.Div(
                                style={
                                    'backgroundColor': '#f1f5f9',
                                    'minHeight': 'calc(100vh - 300px)',
                                    'padding': '24px',
                                    'borderRadius': '8px',
                                    'marginTop': '16px'
                                },
                                children=[
                                    dcc.Loading(
                                        children=[
                                            html.Div(id='results-container', children=[])
                                        ],
                                        type="default",  # Spinner style
                                        color="#2563eb",
                                        fullscreen=False
                                    )
                                ]
                            )
                        ]
                    ),
                    # Tab 2: Summary Tables
                    dcc.Tab(
                        label='Summary Tables',
                        value='tab-summary',
                        style={'padding': '12px 24px', 'fontWeight': '600'},
                        selected_style={'padding': '12px 24px', 'fontWeight': '600', 'borderTop': '3px solid #2563eb'},
                        children=[
                            html.Div(
                                style={'padding': '24px'},
                                children=[
                                    # Summary Tables Container
                                    html.Div(
                                        id='summary-tables-container',
                                        children=[
                                            html.Div(
                                                style={'textAlign': 'center', 'padding': '60px', 'color': '#6b7280'},
                                                children=[
                                                    html.I(className="fas fa-table fa-3x mb-3", style={'color': '#cbd5e1'}),
                                                    html.P("Upload and analyze template data to view summary tables",
                                                           style={'fontSize': '16px', 'margin': '0'})
                                                ]
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

    # Settings Modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Analysis Settings"), style={'backgroundColor': '#f8fafc'}),
        dbc.ModalBody([
            dbc.Row([
                # Left Column
                dbc.Col([
                    html.Div(
                        style={'padding': '16px', 'backgroundColor': '#f8fafc', 'borderRadius': '12px',
                               'border': '2px solid #e5e7eb', 'marginBottom': '16px'},
                        children=[
                            html.Label("Channel Selection:", style={'fontWeight': '600', 'marginBottom': '10px',
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
                        ]
                    ),
                    html.Div(
                        style={'padding': '16px', 'backgroundColor': '#f8fafc', 'borderRadius': '12px',
                               'border': '2px solid #e5e7eb', 'marginBottom': '16px'},
                        children=[
                            html.Label("Peak Display Options:", style={'fontWeight': '600', 'marginBottom': '10px',
                                                                      'display': 'block', 'fontSize': '14px'}),
                            dcc.Checklist(
                                id='peak-options-ps',
                                options=[
                                    {'label': ' Show Peak Shading', 'value': 'shading'},
                                    {'label': ' Show Peak Drop Lines', 'value': 'drop_lines'},
                                    {'label': ' Show Percentages on Plot', 'value': 'percentages'}
                                ],
                                value=[],
                                labelStyle={'display': 'block', 'marginBottom': '8px'}
                            )
                        ]
                    ),
                    html.Div(
                        style={'padding': '16px', 'backgroundColor': '#f8fafc', 'borderRadius': '12px',
                               'border': '2px solid #e5e7eb'},
                        children=[
                            html.Label("Plot Mode:", style={'fontWeight': '600', 'marginBottom': '10px',
                                                            'display': 'block', 'fontSize': '14px'}),
                            dcc.RadioItems(
                                id='plot-mode-radio',
                                options=[
                                    {'label': ' Overlay (Side-by-Side)', 'value': 'overlay'},
                                    {'label': ' Subplots (3×2 Grid)', 'value': 'subplots'}
                                ],
                                value='subplots',  # Default to subplots
                                labelStyle={'display': 'block', 'marginBottom': '8px'}
                            ),
                            html.P("Subplots: 3 rows (days) × 2 columns (Buffer/Plasma) with shared x-axis",
                                   style={'fontSize': '11px', 'color': '#6b7280', 'marginTop': '8px', 'marginBottom': '0'})
                        ]
                    )
                ], width=6),
                # Right Column
                dbc.Col([
                    html.Div(
                        style={'padding': '16px', 'backgroundColor': '#f8fafc', 'borderRadius': '12px',
                               'border': '2px solid #e5e7eb', 'marginBottom': '16px'},
                        children=[
                            html.Label("Display Options:", style={'fontWeight': '600', 'marginBottom': '10px',
                                                                  'display': 'block', 'fontSize': '14px'}),
                            dcc.Checklist(
                                id='display-options-ps',
                                options=[
                                    {'label': ' Show Stability Trend Plot', 'value': 'show_trend'}
                                ],
                                value=[],
                                labelStyle={'display': 'block', 'marginBottom': '8px'}
                            )
                        ]
                    ),
                    html.Div(
                        style={'padding': '16px', 'backgroundColor': '#f8fafc', 'borderRadius': '12px',
                               'border': '2px solid #e5e7eb', 'marginBottom': '16px'},
                        children=[
                            html.Label("X-Axis Range (minutes):", style={'fontWeight': '600', 'marginBottom': '10px',
                                                                          'display': 'block', 'fontSize': '14px'}),
                            html.Div(
                                style={'display': 'flex', 'gap': '12px', 'alignItems': 'center'},
                                children=[
                                    html.Div([
                                        html.Label("Min:", style={'fontSize': '12px', 'marginBottom': '4px'}),
                                        dcc.Input(
                                            id='x-axis-min-input',
                                            type='number',
                                            value=4,
                                            min=0,
                                            step=0.5,
                                            style={'width': '80px', 'padding': '6px', 'borderRadius': '4px', 'border': '1px solid #d1d5db'}
                                        )
                                    ]),
                                    html.Div([
                                        html.Label("Max:", style={'fontSize': '12px', 'marginBottom': '4px'}),
                                        dcc.Input(
                                            id='x-axis-max-input',
                                            type='number',
                                            value=12,
                                            min=0,
                                            step=0.5,
                                            style={'width': '80px', 'padding': '6px', 'borderRadius': '4px', 'border': '1px solid #d1d5db'}
                                        )
                                    ])
                                ]
                            )
                        ]
                    ),
                    html.Div(
                        style={'padding': '16px', 'backgroundColor': '#f8fafc', 'borderRadius': '12px',
                               'border': '2px solid #e5e7eb', 'marginBottom': '16px'},
                        children=[
                            html.Label("Image Height (px):", style={'fontWeight': '600', 'marginBottom': '10px',
                                                                    'display': 'block', 'fontSize': '14px'}),
                            dcc.Input(
                                id='image-height-input',
                                type='number',
                                value=225,
                                min=100,
                                max=600,
                                step=10,
                                style={'width': '100px', 'padding': '6px', 'borderRadius': '4px', 'border': '1px solid #d1d5db'}
                            )
                        ]
                    ),
                    html.Div(
                        style={'padding': '16px', 'backgroundColor': '#f8fafc', 'borderRadius': '12px',
                               'border': '2px solid #e5e7eb'},
                        children=[
                            html.Label("Plot Height (px):", style={'fontWeight': '600', 'marginBottom': '10px',
                                                                   'display': 'block', 'fontSize': '14px'}),
                            dcc.Input(
                                id='plot-height-input',
                                type='number',
                                value=1600,
                                min=800,
                                max=2400,
                                step=100,
                                style={'width': '100px', 'padding': '6px', 'borderRadius': '4px', 'border': '1px solid #d1d5db'}
                            )
                        ]
                    )
                ], width=6)
            ])
        ]),
        dbc.ModalFooter([
            html.Button("Apply Settings", id='apply-settings-btn', style={
                'backgroundColor': '#2563eb', 'color': 'white', 'border': 'none',
                'padding': '12px 32px', 'fontSize': '15px', 'cursor': 'pointer',
                'borderRadius': '8px', 'fontWeight': '700',
                'boxShadow': '0 4px 12px rgba(37, 99, 235, 0.3)'
            })
        ])
    ], id='settings-modal', size='lg', is_open=False),

    # Sample ID Lookup Modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Sample ID Lookup Tool"), style={'backgroundColor': '#f8fafc'}),
        dbc.ModalBody([
            html.Div(
                style={'padding': '16px'},
                children=[
                    # Description
                    dbc.Card([
                        dbc.CardBody([
                            html.P([
                                "Upload a template with Sample IDs to automatically look up Result IDs. ",
                                "The tool will validate Sample ID/Result ID pairs and flag duplicates."
                            ], className="mb-0", style={'fontSize': '14px'})
                        ])
                    ], className="mb-4", style={'backgroundColor': '#f0f9ff', 'border': '1px solid #bfdbfe'}),

                    # Upload Section
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Upload Template", className="mb-3"),
                            dcc.Upload(
                                id='sample-lookup-upload',
                                children=html.Div([
                                    html.I(className="fas fa-cloud-upload-alt fa-2x mb-2", style={'color': '#2563eb'}),
                                    html.P("Drag and drop or click to select template file", className="mb-1", style={'fontSize': '13px'}),
                                    html.P("Excel format (.xlsx)", style={'fontSize': '11px', 'color': '#6b7280'})
                                ], style={'textAlign': 'center', 'padding': '30px'}),
                                style={
                                    'border': '2px dashed #cbd5e1',
                                    'borderRadius': '8px',
                                    'cursor': 'pointer',
                                    'backgroundColor': '#f8fafc'
                                },
                                multiple=False
                            )
                        ])
                    ], className="mb-3"),

                    # Status Display
                    html.Div(id='sample-lookup-status', children=[]),

                    # Download Section
                    html.Div(
                        id='sample-lookup-download-section',
                        style={'display': 'none'},
                        children=[
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6("Download Enhanced Template", className="mb-2"),
                                    html.P("Download the template with populated Result IDs and validation information.",
                                           style={'fontSize': '13px', 'marginBottom': '12px'}),
                                    html.Button(
                                        "Download Excel",
                                        id='sample-lookup-download-btn',
                                        className="btn btn-success",
                                        style={
                                            'backgroundColor': '#10b981',
                                            'border': 'none',
                                            'padding': '10px 28px',
                                            'fontSize': '14px',
                                            'fontWeight': '600',
                                            'borderRadius': '8px'
                                        }
                                    )
                                ])
                            ], className="mb-3"),
                        ]
                    ),

                    # Preview Section
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Preview", className="mb-3"),
                            html.Div(id='sample-lookup-preview-table')
                        ])
                    ])
                ]
            )
        ]),
        dbc.ModalFooter([
            html.Button("Close", id='close-sample-lookup-modal-btn', style={
                'backgroundColor': '#6b7280', 'color': 'white', 'border': 'none',
                'padding': '10px 24px', 'fontSize': '14px', 'cursor': 'pointer',
                'borderRadius': '8px', 'fontWeight': '600'
            })
        ])
    ], id='sample-lookup-modal', size='xl', is_open=False),

    # Downloads
    dcc.Download(id='download-template'),
    dcc.Download(id='download-ppt'),
    dcc.Download(id='sample-lookup-download')
])