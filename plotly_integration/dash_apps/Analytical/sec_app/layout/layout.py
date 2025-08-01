from dash import html, dcc, dash_table
import plotly.graph_objects as go
from .table_config import TABLE_STYLE_CELL, TABLE_STYLE_HEADER

# Layout for the Dash app with consistent styling matching other apps
app_layout = html.Div([
    dcc.Store(id='tab-visibility-store', data={"show_sample_analysis": True, "show_standard_analysis": True}),
    dcc.Location(id="url", refresh=False),
    dcc.Store(id='selected-report', data=None),
    dcc.Store(id="report-settings"),
    dcc.Store(id="settings-applied", data={}),
    dcc.Store(id="std-result-id-store"),
    dcc.Store(id='regression-parameters', data={'slope': 0, 'intercept': 0}),
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

    # Consistent toolbar matching other analytical apps
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
            # Left side - Single Select/Create Report button
            html.Div(
                style={'display': 'flex', 'gap': '20px', 'alignItems': 'center'},
                children=[
                    html.Button([
                        html.Span("📊 ", style={'marginRight': '5px'}),
                        "Select/Create Report"
                    ], id="select-create-report-btn", style={
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
                        html.Span("📈 ", style={'marginRight': '5px'}),
                        "Report Results"
                    ], id="report-results-btn", style={
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
                    })
                ]
            )
        ]
    ),

    # Single Modal for Select/Create Report (matching callback ID)
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
            'backgroundColor': 'rgba(0,0,0,0.5)',
            'overflow': 'auto'
        },
        children=[
            html.Div(
                style={
                    'backgroundColor': 'white',
                    'margin': '50px auto',
                    'padding': '20px',
                    'border': 'none',
                    'borderRadius': '8px',
                    'width': '90%',
                    'maxWidth': '1200px',
                    'maxHeight': '90vh',
                    'overflow': 'auto',
                    'boxShadow': '0 4px 6px rgba(0,0,0,0.1)',
                    'position': 'relative'
                },
                children=[
                    # Modal header with tabs
                    html.Div([
                        html.Button("×", id="close-report-modal-btn", style={
                            'position': 'absolute',
                            'top': '0',
                            'right': '0',
                            'background': 'none',
                            'border': 'none',
                            'fontSize': '24px',
                            'cursor': 'pointer',
                            'color': '#6c757d',
                            'padding': '0',
                            'width': '30px',
                            'height': '30px'
                        })
                    ], style={'position': 'relative', 'borderBottom': '1px solid #dee2e6', 'paddingBottom': '15px',
                              'marginBottom': '20px'}),

                    # Modal content with tabs (matching callback ID)
                    dcc.Tabs(id="report-tabs", value="select-tab", children=[
                        dcc.Tab(
                            label="Select Report",
                            value="select-tab",
                            children=[
                                html.Div([
                                    # Mode and Sample Type Selectors
                                    html.Div([
                                        html.Label("Mode:", style={"fontWeight": "600", "marginRight": "10px",
                                                                   "color": "#495057"}),
                                        dcc.Dropdown(
                                            id="view_mode",
                                            options=[
                                                {"label": "Select Report", "value": "report"},
                                                {"label": "Select Samples", "value": "samples"},
                                            ],
                                            value="report",
                                            style={"width": "200px"}
                                        ),
                                        html.Label("Sample Type:", id="sample-type-label",  # ADDED MISSING ID
                                                   style={"fontWeight": "600", "marginLeft": "20px",
                                                          "marginRight": "10px", "color": "#495057"}),
                                        dcc.Dropdown(
                                            id="sample_type_filter",
                                            options=[
                                                {"label": "PD", "value": "PD"},
                                                {"label": "UP", "value": "UP"},
                                                {"label": "FB", "value": "FB"},
                                            ],
                                            value="PD",
                                            style={"width": "120px"}
                                        )
                                    ], style={
                                        "display": "flex",
                                        "alignItems": "center",
                                        "marginBottom": "20px",
                                        "gap": "10px"
                                    }),

                                    # Report Selection Table Container - FIXED STRUCTURE
                                    html.Div(id="report-table-container", children=[
                                        html.H4("Select a Report", style={'textAlign': 'center', 'color': '#0056b3'}),
                                        dash_table.DataTable(
                                            id='report-selection-table',
                                            columns=[
                                                {"name": "Report ID", "id": "report_id"},
                                                {"name": "Report Name", "id": "report_name"},
                                                {"name": "Project ID", "id": "project_id"},
                                                {"name": "Created By", "id": "user_id"},
                                                {"name": "Date Created", "id": "date_created"},
                                            ],
                                            page_size=10,
                                            sort_action="native",
                                            filter_action="native",
                                            row_selectable="single",
                                            selected_rows=[],
                                            style_table={'overflowX': 'auto'},
                                            style_cell={
                                                'textAlign': 'center',
                                                'padding': '12px',
                                                'fontFamily': 'Arial, sans-serif',
                                                'fontSize': '14px',
                                                'border': '1px solid #dee2e6'
                                            },
                                            style_header={
                                                'backgroundColor': '#f8f9fa',
                                                'fontWeight': '600',
                                                'borderBottom': '2px solid #dee2e6'
                                            },
                                            style_data={
                                                'borderBottom': '1px solid #dee2e6'
                                            },
                                            style_data_conditional=[
                                                {
                                                    'if': {'row_index': 'odd'},
                                                    'backgroundColor': '#f8f9fa'
                                                },
                                                {
                                                    "if": {"state": "active"},
                                                    "backgroundColor": "#e3f2fd",
                                                    "border": "1px solid #2196f3"
                                                },
                                                {
                                                    "if": {"state": "selected"},
                                                    "backgroundColor": "#bbdefb",
                                                    "fontWeight": "600"
                                                }
                                            ]
                                        )
                                    ], style={
                                        'width': '98%',
                                        'margin': 'auto',
                                        'padding': '10px',
                                        'border': '2px solid #0056b3',
                                        'border-radius': '5px',
                                        'background-color': '#f7f9fc',
                                        'margin-bottom': '10px',
                                        'display': 'block'  # CRITICAL: Callbacks control this
                                    }),

                                    # Sample Selection Table Container - FIXED STRUCTURE
                                    html.Div(id="sample-table-container", children=[
                                        html.H4("Select Samples", style={'textAlign': 'center', 'color': '#0056b3'}),
                                        dash_table.DataTable(
                                            id='sample-selection-table',
                                            columns=[
                                                {"name": "Sample Name", "id": "sample_name"},
                                                {"name": "Result ID", "id": "result_id"},
                                                {"name": "Date Acquired", "id": "date_acquired"},
                                                {"name": "Sample Set Name", "id": "sample_set_name"},
                                                {"name": "Column Name", "id": "column_name"},
                                            ],
                                            data=[],
                                            page_size=15,
                                            sort_action="native",
                                            filter_action="native",
                                            row_selectable="multi",
                                            style_table={'overflowX': 'auto'},
                                            style_cell={
                                                'textAlign': 'center',
                                                'padding': '12px',
                                                'fontFamily': 'Arial, sans-serif',
                                                'fontSize': '14px',
                                                'border': '1px solid #dee2e6'
                                            },
                                            style_header={
                                                'backgroundColor': '#f8f9fa',
                                                'fontWeight': '600',
                                                'borderBottom': '2px solid #dee2e6'
                                            },
                                            style_data={
                                                'borderBottom': '1px solid #dee2e6'
                                            },
                                            style_data_conditional=[
                                                {
                                                    'if': {'row_index': 'odd'},
                                                    'backgroundColor': '#f8f9fa'
                                                }
                                            ]
                                        )
                                    ], style={
                                        'width': '98%',
                                        'margin': 'auto',
                                        'padding': '10px',
                                        'border': '2px solid #0056b3',
                                        'border-radius': '5px',
                                        'background-color': '#f7f9fc',
                                        'margin-bottom': '10px',
                                        'display': 'none'  # CRITICAL: Callbacks control this
                                    }),

                                    # Status area - MOVED INSIDE MODAL
                                    html.Div(id="submission_status", style={
                                        "textAlign": "center",
                                        "color": "green",
                                        "fontWeight": "bold",
                                        "fontSize": "16px",
                                        "marginBottom": "10px"
                                    }),

                                    # Action buttons
                                    html.Div([
                                        html.Button("Cancel", id="cancel-select-btn", style={
                                            'backgroundColor': '#6c757d',
                                            'color': 'white',
                                            'padding': '8px 16px',
                                            'border': 'none',
                                            'borderRadius': '5px',
                                            'cursor': 'pointer',
                                            'fontSize': '14px',
                                            'fontWeight': '500',
                                            'marginRight': '10px'
                                        }),
                                        html.Button("Confirm Selection", id="confirm-report-selection", style={
                                            'backgroundColor': '#0056b3',
                                            'color': 'white',
                                            'padding': '8px 16px',
                                            'border': 'none',
                                            'borderRadius': '5px',
                                            'cursor': 'pointer',
                                            'fontSize': '14px',
                                            'fontWeight': '500'
                                        })
                                    ], style={'display': 'flex', 'justifyContent': 'flex-end', 'gap': '10px'})
                                ])
                            ]
                        ),
                        dcc.Tab(
                            label="Create Report",
                            value="create-tab",
                            children=[
                                html.Div(
                                    style={
                                        "height": "calc(80vh - 200px)",
                                        "overflow": "hidden"
                                    },
                                    children=[
                                        html.Iframe(
                                            src="/plotly_integration/dash-app/app/CreateSECReportApp/",
                                            style={
                                                "width": "100%",
                                                "height": "100%",
                                                "border": "none",
                                                "display": "block"
                                            }
                                        )
                                    ]
                                )
                            ]
                        )
                    ])
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

    # Main content area with NO HORIZONTAL SCROLL - FIXED LAYOUT
    html.Div([
        dcc.Tabs(
            id="main-tabs",
            value="tab-2",
            style={
                'borderBottom': '1px solid #dee2e6',
                'marginBottom': '20px'
            },
            children=[
                # Tab 2: Sample Analysis - FIXED TO PREVENT HORIZONTAL SCROLL
                dcc.Tab(
                    label="Sample Analysis",
                    value="tab-2",
                    style={
                        'padding': '12px 24px',
                        'borderBottom': '3px solid transparent',
                        'fontWeight': '500'
                    },
                    selected_style={
                        'borderTop': 'none',
                        'borderLeft': 'none',
                        'borderRight': 'none',
                        'borderBottom': '3px solid #0056b3',
                        'backgroundColor': 'white',
                        'color': '#0056b3',
                        'fontWeight': '600'
                    },
                    children=[
                        html.Div([
                            # Plot area with fixed width calculation
                            html.Div(
                                id='plot-area',
                                children=[
                                    html.H4("SEC Results", style={
                                        'text-align': 'center',
                                        'color': '#495057',
                                        'marginBottom': '20px',
                                        'fontSize': '18px',
                                        'fontWeight': '600'
                                    }),
                                    dcc.Graph(
                                        id='time-series-graph',
                                        figure=go.Figure(
                                            data=[go.Scatter(x=[], y=[], mode='lines')],
                                            layout=go.Layout(
                                                title="Sample Plot",
                                                xaxis_title="Time",
                                                yaxis_title="UV280",
                                                height=800,
                                                dragmode="select",
                                                annotations=[{"showarrow": True}]
                                            )
                                        ),
                                        config={
                                            'toImageButtonOptions': {'filename': 'sec_results'},
                                            'edits': {"annotationPosition": True}
                                        }
                                    )
                                ],
                                style={
                                    'flex': '1',  # Takes remaining space after settings panel
                                    'minWidth': '0',  # Allows flex item to shrink below content size
                                    'padding': '20px',
                                    'border': '1px solid #dee2e6',
                                    'borderRadius': '8px',
                                    'backgroundColor': 'white',
                                    'boxShadow': '0 2px 4px rgba(0,0,0,0.06)',
                                    'marginBottom': '10px'
                                }
                            ),

                            # Settings panel with fixed width
                            html.Div(
                                id='plot-settings',
                                children=[
                                    html.H4("Plot Settings", style={
                                        'color': '#495057',
                                        'marginBottom': '20px',
                                        'fontSize': '16px',
                                        'fontWeight': '600'
                                    }),

                                    # Channel selection
                                    html.Div([
                                        html.Label("Channels:", style={'fontWeight': '500', 'marginBottom': '8px',
                                                                       'display': 'block', 'color': '#495057'}),
                                        dcc.Checklist(
                                            id='channel-checklist',
                                            options=[
                                                {'label': 'UV280', 'value': 'channel_1'},
                                                {'label': 'UV260', 'value': 'channel_2'},
                                                {'label': 'Pressure', 'value': 'channel_3'}
                                            ],
                                            value=['channel_1'],
                                            style={'marginBottom': '15px'}
                                        )
                                    ]),

                                    # Plot type dropdown
                                    html.Div([
                                        html.Label("Plot Type:", style={'fontWeight': '500', 'marginBottom': '8px',
                                                                        'display': 'block', 'color': '#495057'}),
                                        dcc.Dropdown(
                                            id='plot-type-dropdown',
                                            options=[
                                                {'label': 'Plotly Graph', 'value': 'plotly'},
                                                {'label': 'Subplots', 'value': 'subplots'}
                                            ],
                                            value='subplots',
                                            style={'marginBottom': '15px'}
                                        )
                                    ]),

                                    # Shading options
                                    html.Div([
                                        html.Label("Options:", style={'fontWeight': '500', 'marginBottom': '8px',
                                                                      'display': 'block', 'color': '#495057'}),
                                        dcc.Checklist(
                                            id='shading-checklist',
                                            options=[
                                                {'label': 'Enable Shading', 'value': 'enable_shading'}
                                            ],
                                            value=['enable_shading'],
                                            style={'marginBottom': '15px'}
                                        )
                                    ]),

                                    # Numeric inputs with consistent styling
                                    html.Div([
                                        html.Label("Main Peak RT:", style={'fontWeight': '500', 'marginBottom': '8px',
                                                                           'display': 'block', 'color': '#495057'}),
                                        dcc.Input(
                                            id='main-peak-rt-input',
                                            type='number',
                                            value=7.843,
                                            style={
                                                'width': '90%',
                                                'padding': '8px 12px',
                                                'border': '1px solid #ced4da',
                                                'borderRadius': '4px',
                                                'fontSize': '14px',
                                                'marginBottom': '15px'
                                            }
                                        )
                                    ]),

                                    # Refresh button
                                    html.Button("Refresh RT", id="refresh-rt-btn", n_clicks=0, style={
                                        'backgroundColor': '#0056b3',
                                        'color': 'white',
                                        'border': 'none',
                                        'padding': '8px 16px',
                                        'fontSize': '14px',
                                        'cursor': 'pointer',
                                        'borderRadius': '4px',
                                        'fontWeight': '500',
                                        'width': '100%',
                                        'marginBottom': '15px'
                                    }),

                                    html.Div([
                                        html.Label("LMW Cutoff Time:",
                                                   style={'fontWeight': '500', 'marginBottom': '8px',
                                                          'display': 'block', 'color': '#495057'}),
                                        dcc.Input(
                                            id='low-mw-cutoff-input',
                                            type='number',
                                            value=12,
                                            style={
                                                'width': '95%',
                                                'padding': '8px 12px',
                                                'border': '1px solid #ced4da',
                                                'borderRadius': '4px',
                                                'fontSize': '14px',
                                                'marginBottom': '15px'
                                            }
                                        )
                                    ]),

                                    # Peak labeling
                                    html.Div([
                                        html.Label("Peak Settings:", style={'fontWeight': '500', 'marginBottom': '8px',
                                                                            'display': 'block', 'color': '#495057'}),
                                        dcc.Checklist(
                                            id='peak-label-checklist',
                                            options=[
                                                {'label': 'Enable Peak Labeling', 'value': 'enable_peak_labeling'}
                                            ],
                                            value=['enable_peak_labeling'],
                                            style={'marginBottom': '15px'}
                                        )
                                    ]),

                                    # Spacing controls
                                    html.Div([
                                        html.Label("Columns:", style={'fontWeight': '500', 'marginBottom': '8px',
                                                                      'display': 'block', 'color': '#495057'}),
                                        dcc.Input(
                                            id='num-cols-input',
                                            type='number',
                                            min=1,
                                            step=1,
                                            value=3,
                                            debounce=True,
                                            style={
                                                'width': '95%',
                                                'padding': '8px 12px',
                                                'border': '1px solid #ced4da',
                                                'borderRadius': '4px',
                                                'fontSize': '14px',
                                                'marginBottom': '15px'
                                            }
                                        )
                                    ]),

                                    html.Div([
                                        html.Label("Vertical Spacing:",
                                                   style={'fontWeight': '500', 'marginBottom': '8px',
                                                          'display': 'block', 'color': '#495057'}),
                                        dcc.Input(
                                            id='vertical-spacing-input',
                                            type='number',
                                            min=0,
                                            max=1,
                                            step=0.01,
                                            value=0.07,
                                            style={
                                                'width': '95%',
                                                'padding': '8px 12px',
                                                'border': '1px solid #ced4da',
                                                'borderRadius': '4px',
                                                'fontSize': '14px',
                                                'marginBottom': '15px'
                                            }
                                        )
                                    ]),

                                    html.Div([
                                        html.Label("Horizontal Spacing:",
                                                   style={'fontWeight': '500', 'marginBottom': '8px',
                                                          'display': 'block', 'color': '#495057'}),
                                        dcc.Input(
                                            id='horizontal-spacing-input',
                                            type='number',
                                            min=0,
                                            max=1,
                                            step=0.01,
                                            value=0.05,
                                            style={
                                                'width': '95%',
                                                'padding': '8px 12px',
                                                'border': '1px solid #ced4da',
                                                'borderRadius': '4px',
                                                'fontSize': '14px'
                                            }
                                        )
                                    ])
                                ],
                                style={
                                    'width': '280px',  # Fixed width instead of percentage
                                    'flexShrink': '0',  # Prevents shrinking
                                    'padding': '20px',
                                    'backgroundColor': 'white',
                                    'border': '1px solid #dee2e6',
                                    'borderRadius': '8px',
                                    'boxShadow': '0 2px 4px rgba(0,0,0,0.06)',
                                    'height': 'fit-content'
                                }
                            )
                        ], style={
                            'display': 'flex',
                            'flexDirection': 'row',
                            'gap': '20px',
                            'width': '100%',
                            'boxSizing': 'border-box'  # Includes padding in width calculation
                        })
                    ]
                ),

                # Tab 3: Table Data - Full width tabs
                dcc.Tab(
                    label="Table Data",
                    value="tab-3",
                    style={
                        'padding': '12px 24px',
                        'borderBottom': '3px solid transparent',
                        'fontWeight': '500'
                    },
                    selected_style={
                        'borderTop': 'none',
                        'borderLeft': 'none',
                        'borderRight': 'none',
                        'borderBottom': '3px solid #0056b3',
                        'backgroundColor': 'white',
                        'color': '#0056b3',
                        'fontWeight': '600'
                    },
                    children=[
                        # Project info banner
                        html.Div(
                            id='project-info-banner',
                            children=[
                                html.H4("Project Information", style={
                                    'text-align': 'center',
                                    'color': '#495057',
                                    'margin': '0 0 15px 0',
                                    'fontSize': '16px',
                                    'fontWeight': '600'
                                }),
                                html.P(id='project-id-display',
                                       style={'fontSize': '14px', 'margin': '5px 0', 'color': '#6c757d'}),
                                html.P(id='expected-mw-display',
                                       style={'fontSize': '14px', 'margin': '5px 0', 'color': '#6c757d'})
                            ],
                            style={
                                'width': '100%',
                                'padding': '20px',
                                'border': '1px solid #dee2e6',
                                'borderRadius': '8px',
                                'backgroundColor': '#f8f9fa',
                                'marginBottom': '20px',
                                'boxShadow': '0 2px 4px rgba(0,0,0,0.06)',
                                'boxSizing': 'border-box'
                            }
                        ),

                        # Peak results table
                        html.Div(
                            id='hmw-data',
                            children=[
                                html.H4("Peak Results", style={
                                    'text-align': 'center',
                                    'color': '#495057',
                                    'margin': '0 0 20px 0',
                                    'fontSize': '16px',
                                    'fontWeight': '600'
                                }),

                                dcc.Dropdown(
                                    id='hmw-column-selector',
                                    options=[
                                        {"label": "Sample Name", "value": "Sample Name"},
                                        {"label": "Main Peak Start", "value": "Main Peak Start"},
                                        {"label": "Main Peak End", "value": "Main Peak End"},
                                        {"label": "HMW Start", "value": "HMW Start"},
                                        {"label": "HMW End", "value": "HMW End"},
                                        {"label": "LMW Start", "value": "LMW Start"},
                                        {"label": "LMW End", "value": "LMW End"},
                                        {"label": "HMW Area", "value": "HMW Area"},
                                        {"label": "Main Peak Area", "value": "Main Peak Area"},
                                        {"label": "LMW Area", "value": "LMW Area"},
                                        {"label": "HMW %", "value": "HMW"},
                                        {"label": "Main Peak %", "value": "Main Peak"},
                                        {"label": "LMW %", "value": "LMW"},
                                        {"label": "Total Area", "value": "Total Area"},
                                        {"label": "Injection Volume", "value": "Injection Volume"},
                                        {"label": "Total Area/uL", "value": "Total Area/uL"},
                                        {"label": "Max Peak Height", "value": "Max Peak Height"},
                                        {"label": "Calculated MW", "value": "Calculated MW"},
                                        {"label": "MW Deviation", "value": "MW Deviation"},
                                    ],
                                    value=["Sample Name", "HMW", "Main Peak", "LMW", "Calculated MW", "MW Deviation"],
                                    multi=True,
                                    placeholder="Select columns to display",
                                    style={'marginBottom': '15px'}
                                ),

                                dash_table.DataTable(
                                    id='hmw-table',
                                    columns=[
                                        {"name": "Sample Name", "id": "Sample Name"},
                                        {"name": "HMW %", "id": "HMW"},
                                        {"name": "Main Peak %", "id": "Main Peak"},
                                        {"name": "LMW %", "id": "LMW"}
                                    ],
                                    data=[],
                                    sort_action="native",
                                    style_table={'overflowX': 'auto'},
                                    style_cell={
                                        'textAlign': 'center',
                                        'padding': '12px',
                                        'fontFamily': 'Arial, sans-serif',
                                        'fontSize': '14px',
                                        'border': '1px solid #dee2e6'
                                    },
                                    style_header={
                                        'backgroundColor': '#f8f9fa',
                                        'fontWeight': '600',
                                        'borderBottom': '2px solid #dee2e6'
                                    },
                                    style_data={
                                        'borderBottom': '1px solid #dee2e6'
                                    },
                                    style_data_conditional=[
                                        {
                                            'if': {'row_index': 'odd'},
                                            'backgroundColor': '#f8f9fa'
                                        },
                                        {
                                            'if': {
                                                'filter_query': '{MW Deviation} > 30 || {MW Deviation} < -10',
                                                'column_id': 'MW Deviation'
                                            },
                                            'color': 'white',
                                            'backgroundColor': '#dc3545',
                                            'fontWeight': '600'
                                        },
                                        {
                                            'if': {
                                                'filter_query': '{Calculated MW} = "Error" || {MW Deviation} = "Error"',
                                                'column_id': 'MW Deviation'
                                            },
                                            'color': 'white',
                                            'backgroundColor': '#6c757d',
                                            'fontWeight': '600'
                                        }
                                    ]
                                ),

                                html.Button("Export to XLSX", id="export-button", style={
                                    'marginTop': '15px',
                                    'backgroundColor': '#28a745',
                                    'color': 'white',
                                    'border': 'none',
                                    'padding': '10px 20px',
                                    'fontSize': '14px',
                                    'cursor': 'pointer',
                                    'borderRadius': '5px',
                                    'fontWeight': '500',
                                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                                }),
                                dcc.Download(id="download-hmw-data")
                            ],
                            style={
                                'width': '100%',
                                'padding': '20px',
                                'border': '1px solid #dee2e6',
                                'borderRadius': '8px',
                                'backgroundColor': 'white',
                                'marginBottom': '20px',
                                'boxShadow': '0 2px 4px rgba(0,0,0,0.06)',
                                'boxSizing': 'border-box'
                            }
                        ),

                        # Sample details
                        html.Div(
                            id='sample-details',
                            children=[
                                html.H4("Sample Details", style={
                                    'text-align': 'center',
                                    'color': '#495057',
                                    'margin': '0 0 20px 0',
                                    'fontSize': '16px',
                                    'fontWeight': '600'
                                }),
                                dash_table.DataTable(
                                    id='sample-details-table',
                                    columns=[
                                        {"name": "Field", "id": "field"},
                                        {"name": "Value", "id": "value"}
                                    ],
                                    data=[
                                        {"field": "Sample Set Name", "value": ""},
                                        {"field": "Column Name", "value": ""},
                                        {"field": "Column Serial Number", "value": ""},
                                        {"field": "Instrument Method Name", "value": ""},
                                    ],
                                    style_table={'overflowX': 'auto'},
                                    style_cell={
                                        'textAlign': 'left',
                                        'padding': '12px',
                                        'fontFamily': 'Arial, sans-serif',
                                        'fontSize': '14px',
                                        'border': '1px solid #dee2e6'
                                    },
                                    style_header={
                                        'backgroundColor': '#f8f9fa',
                                        'fontWeight': '600',
                                        'borderBottom': '2px solid #dee2e6',
                                        'textAlign': 'center'
                                    },
                                    style_data={
                                        'borderBottom': '1px solid #dee2e6'
                                    }
                                )
                            ],
                            style={
                                'width': '100%',
                                'padding': '20px',
                                'border': '1px solid #dee2e6',
                                'borderRadius': '8px',
                                'backgroundColor': 'white',
                                'boxShadow': '0 2px 4px rgba(0,0,0,0.06)',
                                'boxSizing': 'border-box'
                            }
                        )
                    ]
                ),

                # Tab 4: Standard Analysis
                dcc.Tab(
                    label="Standard Analysis",
                    value="tab-4",
                    style={
                        'padding': '12px 24px',
                        'borderBottom': '3px solid transparent',
                        'fontWeight': '500'
                    },
                    selected_style={
                        'borderTop': 'none',
                        'borderLeft': 'none',
                        'borderRight': 'none',
                        'borderBottom': '3px solid #0056b3',
                        'backgroundColor': 'white',
                        'color': '#0056b3',
                        'fontWeight': '600'
                    },
                    children=[
                        html.Div(
                            id='standard-analysis',
                            children=[
                                html.H4("Standard Analysis", style={
                                    'text-align': 'center',
                                    'color': '#495057',
                                    'marginBottom': '20px',
                                    'fontSize': '18px',
                                    'fontWeight': '600'
                                }),

                                html.Div([
                                    html.Label("Select Standard ID:",
                                               style={'fontWeight': '500', 'marginBottom': '8px', 'display': 'block',
                                                      'color': '#495057'}),
                                    dcc.Dropdown(
                                        id='standard-id-dropdown',
                                        placeholder="Select a Standard ID",
                                        value='',
                                        style={'marginBottom': '20px'}
                                    )
                                ]),

                                # Standard plots with consistent styling
                                html.Div([
                                    dcc.Graph(
                                        id='standard-peak-plot',
                                        figure=go.Figure(
                                            data=[go.Scatter(x=[], y=[], mode='lines')],
                                            layout=go.Layout(
                                                title="Standard Peak Plot",
                                                xaxis_title="Time",
                                                yaxis_title="UV280",
                                                height=400,
                                                dragmode="select"
                                            )
                                        )
                                    ),

                                    dcc.Graph(
                                        id='regression-plot',
                                        figure=go.Figure(
                                            data=[go.Scatter(x=[], y=[], mode='lines', line=dict(dash='dash'))],
                                            layout=go.Layout(
                                                title="MW Calibration Curve",
                                                xaxis_title="Retention Time (min)",
                                                yaxis_title="Log(MW)",
                                                height=400,
                                                dragmode="select"
                                            )
                                        ),
                                        style={'marginTop': '20px'}
                                    ),

                                    dash_table.DataTable(
                                        id="standard-table",
                                        columns=[
                                            {"name": "Peak Name", "id": "peak_name"},
                                            {"name": "Retention Time", "id": "peak_retention_time"},
                                            {"name": "MW", "id": "MW"},
                                            {"name": "Asymmetry at 10%", "id": "asym_at_10"},
                                            {"name": "Plate Count", "id": "plate_count"},
                                            {"name": "Res-HH", "id": "res_hh"},
                                            {"name": "Performance Cutoff", "id": "performance_cutoff"},
                                            {"name": "Pass/Fail", "id": "pass/fail"},
                                        ],
                                        data=[],
                                        row_selectable='multi',
                                        selected_rows=[i for i in range(4)],
                                        style_table={'overflowX': 'auto', 'marginTop': '20px'},
                                        style_cell={
                                            'textAlign': 'center',
                                            'padding': '12px',
                                            'fontFamily': 'Arial, sans-serif',
                                            'fontSize': '14px',
                                            'border': '1px solid #dee2e6'
                                        },
                                        style_header={
                                            'backgroundColor': '#f8f9fa',
                                            'fontWeight': '600',
                                            'borderBottom': '2px solid #dee2e6'
                                        },
                                        style_data={
                                            'borderBottom': '1px solid #dee2e6'
                                        },
                                        style_data_conditional=[
                                            {
                                                'if': {'row_index': 'odd'},
                                                'backgroundColor': '#f8f9fa'
                                            }
                                        ]
                                    )
                                ], style={
                                    'padding': '20px',
                                    'border': '1px solid #dee2e6',
                                    'borderRadius': '8px',
                                    'backgroundColor': 'white',
                                    'marginBottom': '20px',
                                    'boxShadow': '0 2px 4px rgba(0,0,0,0.06)',
                                    'boxSizing': 'border-box'
                                }),

                                # MW calculation section
                                html.Div([
                                    html.P("Regression Equation: ", id="regression-equation",
                                           style={'margin': '10px 0', 'fontSize': '14px', 'color': '#495057'}),
                                    html.P("R² Value: ", id="r-squared-value",
                                           style={'margin': '10px 0', 'fontSize': '14px', 'color': '#495057'}),
                                    html.P("Estimated MW for RT: ", id="estimated-mw",
                                           style={'margin': '10px 0', 'fontSize': '14px', 'color': '#495057'}),

                                    html.Div([
                                        dcc.Input(
                                            id="rt-input",
                                            type="number",
                                            placeholder="Enter Retention Time",
                                            style={
                                                'width': '200px',
                                                'padding': '8px 12px',
                                                'border': '1px solid #ced4da',
                                                'borderRadius': '4px',
                                                'fontSize': '14px',
                                                'marginRight': '10px'
                                            }
                                        ),
                                        html.Button("Calculate MW", id="calculate-mw-button", style={
                                            'backgroundColor': '#0056b3',
                                            'color': 'white',
                                            'border': 'none',
                                            'padding': '8px 16px',
                                            'cursor': 'pointer',
                                            'borderRadius': '4px',
                                            'fontSize': '14px',
                                            'fontWeight': '500'
                                        })
                                    ], style={'margin': '15px 0', 'display': 'flex', 'alignItems': 'center'})
                                ], style={
                                    'padding': '20px',
                                    'border': '1px solid #dee2e6',
                                    'borderRadius': '8px',
                                    'backgroundColor': 'white',
                                    'boxShadow': '0 2px 4px rgba(0,0,0,0.06)',
                                    'boxSizing': 'border-box'
                                })
                            ],
                            style={'width': '100%', 'boxSizing': 'border-box'}
                        )
                    ]
                ),

            ]
        )
    ], style={
        'width': '100%',
        'maxWidth': '100vw',  # Ensures it never exceeds viewport width
        'padding': '20px',
        'backgroundColor': '#f8f9fa',
        'minHeight': '100vh',
        'boxSizing': 'border-box',  # Includes padding in width calculation
        'overflowX': 'hidden'  # Prevents horizontal scrolling
    }),

    # Hidden stores and intervals
    dcc.Store(id='main-peak-rt-store', data=5.10),
    dcc.Interval(id="reset-save-settings-timer", interval=3000, n_intervals=0, disabled=True),
    dcc.Store(id="reset-save-settings-trigger", data=False)
])
