from dash import html, dcc, dash_table
import plotly.graph_objects as go
from .table_config import TABLE_STYLE_CELL, TABLE_STYLE_HEADER

# Layout for the Dash app with consistent styling matching SEC app
app_layout = html.Div([
    dcc.Store(id='tab-visibility-store', data={"show_sample_analysis": True, "show_standard_analysis": True}),
    dcc.Location(id="url", refresh=False),
    dcc.Store(id='selected-report', data=None),
    dcc.Store(id="report-settings"),
    dcc.Store(id="settings-applied", data={}),
    dcc.Store(id="std-result-id-store"),
    dcc.Store(id='regression-parameters', data={'slope': 0, 'intercept': 0}),
    dcc.Store(id='pi-regression-data', data={'slope': 0, 'intercept': 0, 'r_squared': 0}),
    dcc.Store(id='pi-markers-store', data={'default_markers': [10.0, 9.5, 5.5, 4.0]}),
    dcc.Store(id='main-peak-rt-store', data=None),
    dcc.Store(id='low-mw-cutoff-store', data=12),
    dcc.Store(id='hmw-table-store', data=[]),
    dcc.Store(id='report-list-store', data=[]),
    dcc.Store(id='export-state', data={'processed': True, 'last_n_clicks': 0}),
    dcc.Store(id='url-params', data={}),
    dcc.Store(id='embedded-mode', data=False),
    dcc.Interval(id="load-once", interval=1000, n_intervals=0, max_intervals=1),

    dcc.Store(id='button-success-trigger', data=0),
    dcc.Interval(id="button-reset-interval", interval=3000, n_intervals=0, disabled=True),

    # Enhanced toolbar with modern styling
    html.Div(
        id='toolbar-container',
        style={
            'display': 'flex',
            'justifyContent': 'space-between',
            'alignItems': 'center',
            'padding': '15px 20px',
            'backgroundColor': '#ffffff',
            'borderBottom': '1px solid #e3e6ea',
            'gap': '10px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.08)',
            'position': 'relative',
            'zIndex': '10'
        },
        children=[
            # Left side - Single Select/Create Report button
            html.Div(
                style={'display': 'flex', 'gap': '20px', 'alignItems': 'center'},
                children=[
                    html.Button([
                        html.Span("📊 ", style={'marginRight': '5px'}),
                        "Select/Create Report"
                    ], id="select-create-report-btn", style={
                        'backgroundColor': '#2563eb',
                        'color': 'white',
                        'border': 'none',
                        'padding': '12px 24px',
                        'fontSize': '14px',
                        'cursor': 'pointer',
                        'borderRadius': '12px',
                        'fontWeight': '600',
                        'transition': 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                        'boxShadow': '0 4px 12px rgba(37, 99, 235, 0.25)',
                        'position': 'relative',
                        'overflow': 'hidden'
                    }),
                    html.Div([
                        html.Span(id="current-report-text", children="No report selected",
                                  style={'color': '#6c757d', 'fontSize': '14px'})
                    ])
                ]
            ),

            # Right side - Action buttons
            html.Div(
                style={'display': 'flex', 'gap': '10px'},
                children=[
                    html.Button([
                        html.Span("💾 ", style={'marginRight': '5px'}),
                        "Save Settings"
                    ], id="save-plot-settings", style={
                        'backgroundColor': '#059669',
                        'color': 'white',
                        'border': 'none',
                        'padding': '12px 20px',
                        'fontSize': '14px',
                        'cursor': 'pointer',
                        'borderRadius': '10px',
                        'fontWeight': '600',
                        'transition': 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                        'boxShadow': '0 4px 12px rgba(5, 150, 105, 0.25)',
                        'position': 'relative',
                        'overflow': 'hidden'
                    }),
                    html.Button([
                        html.Span("📈 ", style={'marginRight': '5px'}),
                        "Report Results"
                    ], id="report-results-btn", style={
                        'backgroundColor': '#0891b2',
                        'color': 'white',
                        'border': 'none',
                        'padding': '12px 20px',
                        'fontSize': '14px',
                        'cursor': 'pointer',
                        'borderRadius': '10px',
                        'fontWeight': '600',
                        'transition': 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                        'boxShadow': '0 4px 12px rgba(8, 145, 178, 0.25)',
                        'position': 'relative',
                        'overflow': 'hidden'
                    })
                ]
            )
        ]
    ),

    # Enhanced Modal for Select/Create Report (matching SEC app exactly)
    html.Div(
        id="report-modal",
        style={
            'display': 'none',
            'position': 'fixed',
            'zIndex': '1000',
            'left': '0',
            'top': '0',
            'width': '100%',
            'height': '100%',
            'backgroundColor': 'rgba(0,0,0,0.6)',
            'backdropFilter': 'blur(4px)',
            'overflow': 'auto',
            'animation': 'fadeIn 0.3s ease-out'
        },
        children=[
            html.Div(
                style={
                    'backgroundColor': 'white',
                    'margin': '40px auto',
                    'padding': '32px',
                    'border': 'none',
                    'borderRadius': '20px',
                    'width': '90%',
                    'maxWidth': '1200px',
                    'maxHeight': '85vh',
                    'overflow': 'auto',
                    'boxShadow': '0 25px 50px -12px rgba(0,0,0,0.25)',
                    'position': 'relative',
                    'transform': 'scale(1)',
                    'animation': 'modalSlideUp 0.3s ease-out'
                },
                children=[
                    # Modal header with tabs
                    html.Div([
                        html.Button("×", id="close-report-modal-btn", style={
                            'position': 'absolute',
                            'right': '20px',
                            'top': '20px',
                            'fontSize': '30px',
                            'background': 'none',
                            'border': 'none',
                            'cursor': 'pointer',
                            'color': '#666',
                            'transition': 'color 0.2s'
                        }),
                        html.H2("cIEF Report Management", style={
                            'marginBottom': '30px',
                            'color': '#1f2937',
                            'fontSize': '28px',
                            'fontWeight': '700'
                        }),
                        
                        # Tab navigation
                        dcc.Tabs(
                            id="report-tabs",
                            value="select",
                            style={'marginBottom': '25px'},
                            children=[
                                dcc.Tab(
                                    label="📋 Select Existing Report",
                                    value="select",
                                    style={
                                        'padding': '15px 25px',
                                        'fontSize': '14px',
                                        'fontWeight': '600'
                                    }
                                ),
                                dcc.Tab(
                                    label="✨ Create New Report",
                                    value="create",
                                    style={
                                        'padding': '15px 25px',
                                        'fontSize': '14px',
                                        'fontWeight': '600'
                                    }
                                )
                            ]
                        ),
                        
                        html.Div(id="report-tab-content")
                    ])
                ]
            )
        ]
    ),

    # Main content with tabs (matching SEC app structure)
    html.Div([
        dcc.Tabs(id="main-tabs", value="sample-analysis", children=[
            dcc.Tab(
                label="🧪 Sample Analysis",
                value="sample-analysis",
                style={'padding': '15px 25px', 'fontSize': '14px', 'fontWeight': '600'}
            ),
            dcc.Tab(
                label="📊 pI Standard Analysis", 
                value="standard-analysis",
                style={'padding': '15px 25px', 'fontSize': '14px', 'fontWeight': '600'}
            )
        ])
    ], style={'marginTop': '10px'}),

    # Tab content container
    html.Div(id="tab-content", children=[
        # Sample Analysis Tab Content
        html.Div(
            id="sample-analysis-content",
            style={'display': 'block', 'padding': '20px'},
            children=[
                # Main plotting area (matching SEC app layout)
                html.Div([
                    # Plot controls row
                    html.Div([
                        html.Div([
                            html.Label("Smoothing Window:", 
                                     style={'fontSize': '12px', 'color': '#666', 'marginBottom': '5px', 'display': 'block'}),
                            dcc.Input(
                                id="smoothing-window",
                                type="number",
                                value=5,
                                step=2,
                                min=0,
                                style={'width': '100px', 'padding': '8px', 'borderRadius': '4px', 'border': '1px solid #ddd'}
                            )
                        ], style={'marginRight': '20px'}),
                        
                        html.Div([
                            html.Label("Height Threshold:", 
                                     style={'fontSize': '12px', 'color': '#666', 'marginBottom': '5px', 'display': 'block'}),
                            dcc.Input(
                                id="height-threshold",
                                type="number",
                                value=0.01,
                                step=0.001,
                                min=0,
                                style={'width': '100px', 'padding': '8px', 'borderRadius': '4px', 'border': '1px solid #ddd'}
                            )
                        ], style={'marginRight': '20px'}),
                        
                        html.Div([
                            html.Label("Prominence:", 
                                     style={'fontSize': '12px', 'color': '#666', 'marginBottom': '5px', 'display': 'block'}),
                            dcc.Input(
                                id="prominence",
                                type="number",
                                value=0.005,
                                step=0.001,
                                min=0,
                                style={'width': '100px', 'padding': '8px', 'borderRadius': '4px', 'border': '1px solid #ddd'}
                            )
                        ])
                    ], style={'display': 'flex', 'alignItems': 'flex-end', 'marginBottom': '20px', 'gap': '15px'}),
                    
                    # Main plot
                    dcc.Graph(
                        id="cief-plot",
                        config={'displayModeBar': True, 'toImageButtonOptions': {'format': 'svg'}},
                        style={'height': '600px'}
                    )
                ], style={
                    'backgroundColor': 'white',
                    'padding': '25px',
                    'borderRadius': '12px',
                    'marginBottom': '20px',
                    'boxShadow': '0 4px 16px rgba(0,0,0,0.06)'
                }),
                
                # Results table (matching SEC app table layout)
                html.Div([
                    html.H3("Peak Integration Results", 
                           style={'marginBottom': '20px', 'color': '#1f2937', 'fontSize': '20px', 'fontWeight': '600'}),
                    dash_table.DataTable(
                        id='peak-results-table',
                        columns=[
                            {'name': 'Peak #', 'id': 'peak_num', 'type': 'numeric'},
                            {'name': 'Retention Time (min)', 'id': 'retention_time', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                            {'name': 'Height (AU)', 'id': 'height', 'type': 'numeric', 'format': {'specifier': '.4f'}},
                            {'name': 'Area', 'id': 'area', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                            {'name': '% Area', 'id': 'percent_area', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                            {'name': 'pI', 'id': 'pi', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                            {'name': 'pI Marker', 'id': 'is_pi_marker', 'presentation': 'dropdown'}
                        ],
                        data=[],
                        style_cell=TABLE_STYLE_CELL,
                        style_header=TABLE_STYLE_HEADER,
                        style_data_conditional=[
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': '#f5f5f5',
                            },
                            {
                                'if': {'filter_query': '{is_pi_marker} = Yes'},
                                'backgroundColor': '#fff3cd',
                                'border': '2px solid #ffc107'
                            }
                        ],
                        editable=True,
                        dropdown={
                            'is_pi_marker': {
                                'options': [
                                    {'label': 'Yes', 'value': 'Yes'},
                                    {'label': 'No', 'value': 'No'}
                                ]
                            }
                        },
                        sort_action='native',
                        row_selectable='multi'
                    )
                ], style={
                    'backgroundColor': 'white',
                    'padding': '25px',
                    'borderRadius': '12px',
                    'boxShadow': '0 4px 16px rgba(0,0,0,0.06)'
                })
            ]
        ),
        
        # pI Standard Analysis Tab Content
        html.Div(
            id="standard-analysis-content", 
            style={'display': 'none', 'padding': '20px'},
            children=[
                # pI Calibration section
                html.Div([
                    html.H3("pI Calibration Curve", 
                           style={'marginBottom': '20px', 'color': '#1f2937', 'fontSize': '20px', 'fontWeight': '600'}),
                    
                    # Calibration controls
                    html.Div([
                        html.Button("Calculate pI Regression", id="calc-regression-btn", style={
                            'backgroundColor': '#2563eb',
                            'color': 'white',
                            'border': 'none',
                            'padding': '12px 24px',
                            'fontSize': '14px',
                            'cursor': 'pointer',
                            'borderRadius': '8px',
                            'fontWeight': '600',
                            'boxShadow': '0 2px 8px rgba(37, 99, 235, 0.25)',
                            'marginBottom': '20px'
                        })
                    ]),
                    
                    # Regression results display
                    html.Div(id="regression-results", style={
                        'marginBottom': '20px', 
                        'padding': '15px', 
                        'backgroundColor': '#f8f9fa', 
                        'borderRadius': '8px',
                        'minHeight': '100px'
                    }),
                    
                    # Calibration plot
                    dcc.Graph(
                        id="pi-calibration-plot",
                        config={'displayModeBar': True, 'toImageButtonOptions': {'format': 'svg'}},
                        style={'height': '400px'}
                    )
                ], style={
                    'backgroundColor': 'white',
                    'padding': '25px',
                    'borderRadius': '12px',
                    'marginBottom': '20px',
                    'boxShadow': '0 4px 16px rgba(0,0,0,0.06)'
                })
            ]
        )
    ])
])