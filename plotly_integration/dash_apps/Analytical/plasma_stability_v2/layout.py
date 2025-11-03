"""
Layout for Plasma Stability SEC Analysis App V2
Excel template-based workflow for multiple molecules
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

app_layout = html.Div([
    # Data stores
    dcc.Store(id='template-data-store', data=None),
    dcc.Store(id='analysis-results-store', data=None),
    dcc.Store(id='channel-settings-store', data=['channel_1']),
    dcc.Store(id='show-trend-store', data=False),
    dcc.Store(id='x-axis-range-store', data=[4, 12]),
    dcc.Store(id='image-height-store', data=225),
    dcc.Store(id='plot-width-store', data=600),

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
                    html.Div(
                        style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'},
                        children=[
                            html.Div([
                                html.H1("Plasma Stability SEC Analysis", style={
                                    'margin': '0',
                                    'color': '#2563eb',
                                    'fontSize': '32px',
                                    'fontWeight': '800'
                                }),
                                html.P("Upload Excel template to analyze multiple molecules", style={
                                    'margin': '8px 0 0 0',
                                    'color': '#6b7280',
                                    'fontSize': '15px'
                                })
                            ]),
                            html.Div(
                                style={'display': 'flex', 'gap': '12px'},
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
            html.Div(
                style={'padding': '16px', 'backgroundColor': '#f8fafc', 'borderRadius': '12px',
                       'border': '2px solid #e5e7eb', 'marginBottom': '20px'},
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
                       'border': '2px solid #e5e7eb', 'marginBottom': '20px'},
                children=[
                    html.Label("Peak Display Options:", style={'fontWeight': '600', 'marginBottom': '10px',
                                                              'display': 'block', 'fontSize': '14px'}),
                    dcc.Checklist(
                        id='peak-options-ps',
                        options=[
                            {'label': ' Show Peak Shading', 'value': 'shading'},
                            {'label': ' Show Percentages on Plot', 'value': 'percentages'}
                        ],
                        value=[],
                        labelStyle={'display': 'block', 'marginBottom': '8px'}
                    )
                ]
            ),
            html.Div(
                style={'padding': '16px', 'backgroundColor': '#f8fafc', 'borderRadius': '12px',
                       'border': '2px solid #e5e7eb', 'marginBottom': '20px'},
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
                       'border': '2px solid #e5e7eb', 'marginBottom': '20px'},
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
                       'border': '2px solid #e5e7eb', 'marginBottom': '20px'},
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
                        value=600,
                        min=300,
                        max=800,
                        step=50,
                        style={'width': '100px', 'padding': '6px', 'borderRadius': '4px', 'border': '1px solid #d1d5db'}
                    )
                ]
            )
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

    # Upload Status Section (compact)
    html.Div(
        style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '24px 24px 0 24px'},
        children=[
            html.Div(id='upload-status', style={'marginBottom': '16px'})
        ]
    ),

    # Main content area
    html.Div(
        style={
            'backgroundColor': '#f1f5f9',
            'minHeight': 'calc(100vh - 120px)',
            'padding': '24px'
        },
        children=[
            html.Div(
                style={'maxWidth': '1400px', 'margin': '0 auto'},
                children=[
                    # Results Section (populated after upload and analysis)
                    html.Div(id='results-container', children=[])
                ]
            )
        ]
    ),

    # Downloads
    dcc.Download(id='download-template'),
    dcc.Download(id='download-ppt')
])