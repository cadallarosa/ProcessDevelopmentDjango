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

    # Enhanced Modal for Select/Create Report
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
                            'top': '16px',
                            'right': '16px',
                            'background': '#f3f4f6',
                            'border': 'none',
                            'fontSize': '20px',
                            'cursor': 'pointer',
                            'color': '#6b7280',
                            'padding': '8px',
                            'width': '36px',
                            'height': '36px',
                            'borderRadius': '50%',
                            'display': 'flex',
                            'alignItems': 'center',
                            'justifyContent': 'center',
                            'transition': 'all 0.2s ease',
                            'hover': {'backgroundColor': '#e5e7eb', 'transform': 'scale(1.1)'}
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
                                                        'padding': '12px 16px',
                                                        'fontFamily': 'system-ui, -apple-system, sans-serif',
                                                        'fontSize': '14px',
                                                        'border': '1px solid #e5e7eb',  # Visible borders back
                                                        'borderCollapse': 'collapse'
                                                    },
                                                    style_header={
                                                        'backgroundColor': '#f8fafc',
                                                        'fontWeight': '700',
                                                        'border': '1px solid #d1d5db',  # Visible header borders back
                                                        'color': '#374151',
                                                        'textTransform': 'uppercase',
                                                        'fontSize': '12px',
                                                        'letterSpacing': '0.5px'
                                                    },
                                                    style_data={
                                                        'backgroundColor': 'white',
                                                        'color': '#374151',
                                                        'border': '1px solid #e5e7eb'  # Visible data borders back
                                                    },
                                                    style_data_conditional=[
                                                        {
                                                            'if': {'row_index': 'odd'},
                                                            'backgroundColor': '#fafbfc'
                                                        },
                                                        {
                                                            "if": {"state": "active"},
                                                            "backgroundColor": "#eff6ff",
                                                            "border": "1px solid #3b82f6",
                                                            "borderRadius": "8px",
                                                            "boxShadow": "0 0 0 3px rgba(59, 130, 246, 0.1)"
                                                        },
                                                        {
                                                            "if": {"state": "selected"},
                                                            "backgroundColor": "#dbeafe",
                                                            "fontWeight": "600",
                                                            "color": "#1e40af",
                                                            "borderRadius": "8px"
                                                        }
                                                    ]
                                                )
                                    ], style={
                                        'width': '100%',
                                        'margin': 'auto',
                                        'padding': '20px',
                                        'border': 'none',  # Remove border
                                        'borderRadius': '16px',
                                        'backgroundColor': '#ffffff',  # Clean white background
                                        'marginBottom': '20px',
                                        'display': 'block',  # CRITICAL: Callbacks control this
                                        'boxShadow': '0 2px 4px rgba(0,0,0,0.05)',  # Subtle shadow
                                        'transition': 'all 0.2s ease'
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
                                                        'padding': '16px 20px',
                                                        'fontFamily': 'system-ui, -apple-system, sans-serif',
                                                        'fontSize': '14px',
                                                        'border': 'none',
                                                        'borderBottom': '1px solid #f1f5f9',
                                                        'transition': 'all 0.2s ease'
                                                    },
                                                    style_header={
                                                        'backgroundColor': '#f8fafc',
                                                        'fontWeight': '700',
                                                        'borderBottom': '2px solid #e2e8f0',
                                                        'color': '#374151',
                                                        'textTransform': 'uppercase',
                                                        'fontSize': '12px',
                                                        'letterSpacing': '0.5px'
                                                    },
                                                    style_data={
                                                        'backgroundColor': 'white',
                                                        'color': '#374151',
                                                        'borderBottom': '1px solid #f1f5f9'
                                                    },
                                                    style_data_conditional=[
                                                        {
                                                            'if': {'row_index': 'odd'},
                                                            'backgroundColor': '#fafbfc'
                                                        },
                                                        {
                                                            'if': {'state': 'hover'},
                                                            'backgroundColor': '#f0f9ff',
                                                            'transform': 'translateY(-1px)',
                                                            'boxShadow': '0 4px 8px rgba(0,0,0,0.08)'
                                                        }
                                                    ]
                                                )
                                    ], style={
                                        'width': '100%',
                                        'margin': 'auto',
                                        'padding': '20px',
                                        'border': '1px solid #e2e8f0',
                                        'borderRadius': '16px',
                                        'backgroundColor': '#f8fafc',
                                        'marginBottom': '20px',
                                        'display': 'none',  # CRITICAL: Callbacks control this
                                        'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)',
                                        'transition': 'all 0.2s ease'
                                    }),

                                    # Status area - MOVED INSIDE MODAL
                                    html.Div(id="submission_status", style={
                                        "textAlign": "center",
                                        "color": "green",
                                        "fontWeight": "bold",
                                        "fontSize": "16px",
                                        "marginBottom": "10px"
                                    }),

                                    # Enhanced Action buttons
                                    html.Div([
                                        html.Button("Cancel", id="cancel-select-btn", style={
                                            'backgroundColor': '#6b7280',
                                            'color': 'white',
                                            'padding': '12px 20px',
                                            'border': 'none',
                                            'borderRadius': '10px',
                                            'cursor': 'pointer',
                                            'fontSize': '14px',
                                            'fontWeight': '600',
                                            'marginRight': '12px',
                                            'transition': 'all 0.2s ease',
                                            'boxShadow': '0 2px 4px rgba(107, 114, 128, 0.2)'
                                        }),
                                        html.Button("Confirm Selection", id="confirm-report-selection", style={
                                            'backgroundColor': '#2563eb',
                                            'color': 'white',
                                            'padding': '12px 24px',
                                            'border': 'none',
                                            'borderRadius': '10px',
                                            'cursor': 'pointer',
                                            'fontSize': '14px',
                                            'fontWeight': '600',
                                            'transition': 'all 0.2s ease',
                                            'boxShadow': '0 4px 12px rgba(37, 99, 235, 0.25)'
                                        })
                                    ], style={'display': 'flex', 'justifyContent': 'flex-end', 'gap': '12px', 'marginTop': '16px'})
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
    dcc.Loading(
        id="main-content-loading",
        type="default",
        children=[
            html.Div([
                dcc.Tabs(
                    id="main-tabs",
                    value="tab-2",
                    style={
                        'borderBottom': '2px solid #e2e8f0',
                        'marginBottom': '24px',
                        'backgroundColor': 'white',
                        'borderRadius': '12px 12px 0 0',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
                    },
                    children=[
                # Tab 2: Sample Analysis - Enhanced Styling
                dcc.Tab(
                    label="Sample Analysis",
                    value="tab-2",
                    style={
                        'padding': '16px 28px',
                        'borderBottom': '3px solid transparent',
                        'fontWeight': '600',
                        'color': '#6b7280',
                        'fontSize': '15px',
                        'transition': 'all 0.2s ease',
                        'borderRadius': '8px 8px 0 0'
                    },
                    selected_style={
                        'borderTop': 'none',
                        'borderLeft': 'none',
                        'borderRight': 'none',
                        'borderBottom': '3px solid #2563eb',
                        'backgroundColor': 'white',
                        'color': '#2563eb',
                        'fontWeight': '700',
                        'borderRadius': '8px 8px 0 0',
                        'boxShadow': '0 -2px 8px rgba(37, 99, 235, 0.1)'
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
                                    
                                    # Top Pagination controls (initially hidden)
                                    html.Div(id='pagination-controls-top', style={'display': 'none'}, children=[
                                        html.Div([
                                            html.Button("◀ Previous", id="prev-page-btn-top", n_clicks=0, disabled=True, style={
                                                'backgroundColor': '#6b7280',
                                                'color': 'white',
                                                'border': 'none',
                                                'padding': '8px 16px',
                                                'fontSize': '14px',
                                                'cursor': 'pointer',
                                                'borderRadius': '8px',
                                                'marginRight': '10px'
                                            }),
                                            html.Span(id="page-info-top", children="Page 1 of 1", style={
                                                'margin': '0 15px',
                                                'fontWeight': '500',
                                                'color': '#374151'
                                            }),
                                            html.Button("Next ▶", id="next-page-btn-top", n_clicks=0, style={
                                                'backgroundColor': '#2563eb',
                                                'color': 'white',
                                                'border': 'none',
                                                'padding': '8px 16px',
                                                'fontSize': '14px',
                                                'cursor': 'pointer',
                                                'borderRadius': '8px',
                                                'marginLeft': '10px'
                                            }),
                                            html.Span(id="samples-info-top", children="", style={
                                                'marginLeft': '20px',
                                                'fontSize': '12px',
                                                'color': '#6b7280',
                                                'fontStyle': 'italic'
                                            })
                                        ], style={
                                            'textAlign': 'center',
                                            'padding': '12px',
                                            'backgroundColor': '#f8fafc',
                                            'border': '1px solid #e5e7eb',
                                            'borderRadius': '8px',
                                            'marginBottom': '15px'
                                        })
                                    ]),
                                    
                                    
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
                                            ),
                                    
                                    # Bottom Pagination controls (initially hidden)
                                    html.Div(id='pagination-controls-bottom', style={'display': 'none'}, children=[
                                        html.Div([
                                            html.Button("◀ Previous", id="prev-page-btn-bottom", n_clicks=0, disabled=True, style={
                                                'backgroundColor': '#6b7280',
                                                'color': 'white',
                                                'border': 'none',
                                                'padding': '8px 16px',
                                                'fontSize': '14px',
                                                'cursor': 'pointer',
                                                'borderRadius': '8px',
                                                'marginRight': '10px'
                                            }),
                                            html.Span(id="page-info-bottom", children="Page 1 of 1", style={
                                                'margin': '0 15px',
                                                'fontWeight': '500',
                                                'color': '#374151'
                                            }),
                                            html.Button("Next ▶", id="next-page-btn-bottom", n_clicks=0, style={
                                                'backgroundColor': '#2563eb',
                                                'color': 'white',
                                                'border': 'none',
                                                'padding': '8px 16px',
                                                'fontSize': '14px',
                                                'cursor': 'pointer',
                                                'borderRadius': '8px',
                                                'marginLeft': '10px'
                                            }),
                                            html.Span(id="samples-info-bottom", children="", style={
                                                'marginLeft': '20px',
                                                'fontSize': '12px',
                                                'color': '#6b7280',
                                                'fontStyle': 'italic'
                                            })
                                        ], style={
                                            'textAlign': 'center',
                                            'padding': '12px',
                                            'backgroundColor': '#f8fafc',
                                            'border': '1px solid #e5e7eb',
                                            'borderRadius': '8px',
                                            'marginTop': '15px'
                                        })
                                    ])
                                ],
                                style={
                                    'flex': '1',  # Takes remaining space after settings panel
                                    'minWidth': '0',  # Allows flex item to shrink below content size
                                    'padding': '24px',
                                    'border': '1px solid #e5e7eb',
                                    'borderRadius': '16px',
                                    'backgroundColor': 'white',
                                    'boxShadow': '0 10px 25px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)',
                                    'marginBottom': '16px',
                                    'transition': 'all 0.3s ease',
                                    'position': 'relative',  # Required for loading overlay
                                    'overflow': 'hidden',
                                    'minHeight': '500px'  # Ensure space for loading overlay
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
                                            debounce=True,
                                            style={
                                                'width': '100%',
                                                'padding': '12px 16px',
                                                'border': '1px solid #d1d5db',
                                                'borderRadius': '10px',
                                                'fontSize': '14px',
                                                'marginBottom': '16px',
                                                'backgroundColor': '#f9fafb',
                                                'transition': 'all 0.2s ease',
                                                'boxSizing': 'border-box',
                                                'fontFamily': 'system-ui, -apple-system, sans-serif'
                                            }
                                        )
                                    ]),

                                    # Enhanced Refresh button
                                    html.Button("Refresh RT", id="refresh-rt-btn", n_clicks=0, style={
                                        'backgroundColor': '#2563eb',
                                        'color': 'white',
                                        'border': 'none',
                                        'padding': '12px 20px',
                                        'fontSize': '14px',
                                        'cursor': 'pointer',
                                        'borderRadius': '10px',
                                        'fontWeight': '600',
                                        'width': '100%',
                                        'marginBottom': '18px',
                                        'transition': 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                                        'boxShadow': '0 4px 12px rgba(37, 99, 235, 0.25)',
                                        'fontFamily': 'system-ui, -apple-system, sans-serif'
                                    }),

                                    html.Div([
                                        html.Label("LMW Cutoff Time:",
                                                   style={'fontWeight': '500', 'marginBottom': '8px',
                                                          'display': 'block', 'color': '#495057'}),
                                        dcc.Input(
                                            id='low-mw-cutoff-input',
                                            type='number',
                                            value=12,
                                            debounce=True,
                                            style={
                                                'width': '100%',
                                                'padding': '12px 16px',
                                                'border': '1px solid #d1d5db',
                                                'borderRadius': '10px',
                                                'fontSize': '14px',
                                                'marginBottom': '16px',
                                                'backgroundColor': '#f9fafb',
                                                'transition': 'all 0.2s ease',
                                                'boxSizing': 'border-box',
                                                'fontFamily': 'system-ui, -apple-system, sans-serif'
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
                                                {'label': 'Enable Peak Labeling', 'value': 'enable_peak_labeling'},
                                                {'label': 'Show MW in Annotations', 'value': 'show_mw_annotations'}
                                            ],
                                            value=['enable_peak_labeling', 'show_mw_annotations'],
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
                                                'width': '100%',
                                                'padding': '12px 16px',
                                                'border': '1px solid #d1d5db',
                                                'borderRadius': '10px',
                                                'fontSize': '14px',
                                                'marginBottom': '16px',
                                                'backgroundColor': '#f9fafb',
                                                'transition': 'all 0.2s ease',
                                                'boxSizing': 'border-box',
                                                'fontFamily': 'system-ui, -apple-system, sans-serif'
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
                                            debounce=True,
                                            style={
                                                'width': '100%',
                                                'padding': '12px 16px',
                                                'border': '1px solid #d1d5db',
                                                'borderRadius': '10px',
                                                'fontSize': '14px',
                                                'marginBottom': '16px',
                                                'backgroundColor': '#f9fafb',
                                                'transition': 'all 0.2s ease',
                                                'boxSizing': 'border-box',
                                                'fontFamily': 'system-ui, -apple-system, sans-serif'
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
                                            debounce=True,
                                            style={
                                                'width': '100%',
                                                'padding': '12px 16px',
                                                'border': '1px solid #d1d5db',
                                                'borderRadius': '10px',
                                                'fontSize': '14px',
                                                'backgroundColor': '#f9fafb',
                                                'transition': 'all 0.2s ease',
                                                'boxSizing': 'border-box',
                                                'fontFamily': 'system-ui, -apple-system, sans-serif'
                                            }
                                        )
                                    ]),
                                    
                                    # Manual Scaling Section
                                    html.Hr(style={'margin': '20px 0', 'borderColor': '#e5e7eb'}),
                                    
                                    html.Div([
                                        html.Label("Axis Scaling:", style={'fontWeight': '500', 'marginBottom': '8px',
                                                                          'display': 'block', 'color': '#495057'}),
                                        dcc.Checklist(
                                            id='manual-scaling-checkbox',
                                            options=[
                                                {'label': 'Manual Scaling', 'value': 'enable_manual_scaling'}
                                            ],
                                            value=[],
                                            style={'marginBottom': '15px'}
                                        )
                                    ]),
                                    
                                    # Manual scaling inputs container
                                    html.Div(
                                        id='manual-scaling-inputs',
                                        children=[
                                            html.Div([
                                                html.Label("X-axis Range:", style={'fontWeight': '500', 'marginBottom': '8px',
                                                                                   'display': 'block', 'color': '#495057'}),
                                                html.Div([
                                                    dcc.Input(
                                                        id='x-min-input',
                                                        type='number',
                                                        placeholder='X min',
                                                        style={
                                                            'width': '48%',
                                                            'padding': '10px',
                                                            'border': '1px solid #d1d5db',
                                                            'borderRadius': '8px',
                                                            'fontSize': '13px',
                                                            'marginRight': '4%',
                                                            'backgroundColor': '#f9fafb'
                                                        }
                                                    ),
                                                    dcc.Input(
                                                        id='x-max-input',
                                                        type='number',
                                                        placeholder='X max',
                                                        style={
                                                            'width': '48%',
                                                            'padding': '10px',
                                                            'border': '1px solid #d1d5db',
                                                            'borderRadius': '8px',
                                                            'fontSize': '13px',
                                                            'backgroundColor': '#f9fafb'
                                                        }
                                                    )
                                                ], style={'display': 'flex', 'marginBottom': '12px'})
                                            ]),
                                            
                                            html.Div([
                                                html.Label("Y-axis Range:", style={'fontWeight': '500', 'marginBottom': '8px',
                                                                                   'display': 'block', 'color': '#495057'}),
                                                html.Div([
                                                    dcc.Input(
                                                        id='y-min-input',
                                                        type='number',
                                                        placeholder='Y min',
                                                        style={
                                                            'width': '48%',
                                                            'padding': '10px',
                                                            'border': '1px solid #d1d5db',
                                                            'borderRadius': '8px',
                                                            'fontSize': '13px',
                                                            'marginRight': '4%',
                                                            'backgroundColor': '#f9fafb'
                                                        }
                                                    ),
                                                    dcc.Input(
                                                        id='y-max-input',
                                                        type='number',
                                                        placeholder='Y max',
                                                        style={
                                                            'width': '48%',
                                                            'padding': '10px',
                                                            'border': '1px solid #d1d5db',
                                                            'borderRadius': '8px',
                                                            'fontSize': '13px',
                                                            'backgroundColor': '#f9fafb'
                                                        }
                                                    )
                                                ], style={'display': 'flex', 'marginBottom': '15px'})
                                            ])
                                        ],
                                        style={'display': 'none'}  # Initially hidden
                                    ),
                                    
                                    # Helpful note
                                    html.Div([
                                        html.P("💡 Layout changes (columns, spacing) require clicking Apply", 
                                               style={'fontSize': '12px', 'color': '#6b7280', 'fontStyle': 'italic', 
                                                      'marginBottom': '10px', 'textAlign': 'center'})
                                    ]),
                                    
                                    # Apply Settings Button
                                    html.Div([
                                        html.Button("🔄 Apply Layout Settings", id="apply-layout-btn", n_clicks=0, style={
                                            'backgroundColor': '#059669',
                                            'color': 'white',
                                            'border': 'none',
                                            'padding': '14px 20px',
                                            'fontSize': '14px',
                                            'cursor': 'pointer',
                                            'borderRadius': '10px',
                                            'fontWeight': '600',
                                            'width': '100%',
                                            'marginTop': '20px',
                                            'transition': 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                                            'boxShadow': '0 4px 12px rgba(5, 150, 105, 0.25)',
                                            'fontFamily': 'system-ui, -apple-system, sans-serif'
                                        })
                                    ], style={'marginTop': '16px'})
                                ],
                                style={
                                    'width': '300px',  # Slightly wider for better UX
                                    'flexShrink': '0',  # Prevents shrinking
                                    'padding': '24px',
                                    'backgroundColor': 'white',
                                    'border': '1px solid #e5e7eb',
                                    'borderRadius': '16px',
                                    'boxShadow': '0 10px 25px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)',
                                    'height': 'fit-content',
                                    'transition': 'all 0.3s ease',
                                    'position': 'relative'
                                }
                            )
                        ], style={
                            'display': 'flex',
                            'flexDirection': 'row',
                            'gap': '24px',
                            'width': '100%',
                            'boxSizing': 'border-box',  # Includes padding in width calculation
                            'alignItems': 'flex-start'
                        })
                    ]
                ),

                # Tab 3: Table Data - Enhanced Styling
                dcc.Tab(
                    label="Table Data",
                    value="tab-3",
                    style={
                        'padding': '16px 28px',
                        'borderBottom': '3px solid transparent',
                        'fontWeight': '600',
                        'color': '#6b7280',
                        'fontSize': '15px',
                        'transition': 'all 0.2s ease',
                        'borderRadius': '8px 8px 0 0'
                    },
                    selected_style={
                        'borderTop': 'none',
                        'borderLeft': 'none',
                        'borderRight': 'none',
                        'borderBottom': '3px solid #2563eb',
                        'backgroundColor': 'white',
                        'color': '#2563eb',
                        'fontWeight': '700',
                        'borderRadius': '8px 8px 0 0',
                        'boxShadow': '0 -2px 8px rgba(37, 99, 235, 0.1)'
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
                                       style={'fontSize': '16px', 'margin': '8px 0', 'color': '#374151', 'fontWeight': '600'}),
                                html.P(id='expected-mw-display',
                                       style={'fontSize': '16px', 'margin': '8px 0', 'color': '#374151', 'fontWeight': '600'})
                            ],
                            style={
                                'width': '100%',
                                'padding': '24px',
                                'border': '1px solid #e5e7eb',
                                'borderRadius': '16px',
                                'backgroundColor': '#f8fafc',
                                'marginBottom': '24px',
                                'boxShadow': '0 10px 25px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)',
                                'boxSizing': 'border-box',
                                'transition': 'all 0.3s ease'
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
                                        {"label": "Result ID", "value": "Result ID"},
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

                                html.Button([
                                    html.Span("📄 ", style={'marginRight': '8px'}),
                                    "Export to XLSX"
                                ], id="export-button", style={
                                    'marginTop': '20px',
                                    'backgroundColor': '#059669',
                                    'color': 'white',
                                    'border': 'none',
                                    'padding': '14px 24px',
                                    'fontSize': '14px',
                                    'cursor': 'pointer',
                                    'borderRadius': '12px',
                                    'fontWeight': '600',
                                    'boxShadow': '0 4px 14px rgba(5, 150, 105, 0.35)',
                                    'transition': 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                                    'fontFamily': 'system-ui, -apple-system, sans-serif',
                                    'position': 'relative',
                                    'overflow': 'hidden'
                                }),
                                dcc.Download(id="download-hmw-data")
                            ],
                            style={
                                'width': '100%',
                                'padding': '24px',
                                'border': '1px solid #e5e7eb',
                                'borderRadius': '16px',
                                'backgroundColor': 'white',
                                'marginBottom': '24px',
                                'boxShadow': '0 10px 25px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)',
                                'boxSizing': 'border-box',
                                'transition': 'all 0.3s ease'
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
                                'padding': '24px',
                                'border': '1px solid #e5e7eb',
                                'borderRadius': '16px',
                                'backgroundColor': 'white',
                                'boxShadow': '0 10px 25px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)',
                                'boxSizing': 'border-box',
                                'transition': 'all 0.3s ease'
                            }
                        )
                    ]
                ),

                # Tab 4: Standard Analysis - Enhanced Styling
                dcc.Tab(
                    label="Standard Analysis",
                    value="tab-4",
                    style={
                        'padding': '16px 28px',
                        'borderBottom': '3px solid transparent',
                        'fontWeight': '600',
                        'color': '#6b7280',
                        'fontSize': '15px',
                        'transition': 'all 0.2s ease',
                        'borderRadius': '8px 8px 0 0'
                    },
                    selected_style={
                        'borderTop': 'none',
                        'borderLeft': 'none',
                        'borderRight': 'none',
                        'borderBottom': '3px solid #2563eb',
                        'backgroundColor': 'white',
                        'color': '#2563eb',
                        'fontWeight': '700',
                        'borderRadius': '8px 8px 0 0',
                        'boxShadow': '0 -2px 8px rgba(37, 99, 235, 0.1)'
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
                                                'width': '220px',
                                                'padding': '12px 16px',
                                                'border': '1px solid #d1d5db',
                                                'borderRadius': '10px',
                                                'fontSize': '14px',
                                                'marginRight': '12px',
                                                'backgroundColor': '#f9fafb',
                                                'transition': 'all 0.2s ease',
                                                'fontFamily': 'system-ui, -apple-system, sans-serif'
                                            }
                                        ),
                                        html.Button([
                                            html.Span("🧮 ", style={'marginRight': '6px'}),
                                            "Calculate MW"
                                        ], id="calculate-mw-button", style={
                                            'backgroundColor': '#2563eb',
                                            'color': 'white',
                                            'border': 'none',
                                            'padding': '12px 20px',
                                            'cursor': 'pointer',
                                            'borderRadius': '10px',
                                            'fontSize': '14px',
                                            'fontWeight': '600',
                                            'transition': 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                                            'boxShadow': '0 4px 12px rgba(37, 99, 235, 0.25)',
                                            'fontFamily': 'system-ui, -apple-system, sans-serif'
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
                'padding': '24px',
                'backgroundColor': '#f1f5f9',
                'minHeight': '100vh',
                'boxSizing': 'border-box',  # Includes padding in width calculation
                'overflowX': 'hidden',  # Prevents horizontal scrolling
                'backgroundImage': 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%)',
                'fontFamily': 'system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif'
            })
        ]
    ),

    # Hidden stores and intervals
    dcc.Store(id='main-peak-rt-store', data=5.10),
    dcc.Interval(id="reset-save-settings-timer", interval=3000, n_intervals=0, disabled=True),
    dcc.Store(id="reset-save-settings-trigger", data=False),
    
    # Pagination stores
    dcc.Store(id='pagination-data', data={'current_page': 1, 'total_pages': 1, 'samples_per_page': 30, 'all_samples': [], 'all_result_ids': []}),
    dcc.Store(id='cached-plots', data={}),  # Cache for background-loaded plots
    dcc.Store(id='background-loading-queue', data=[]),  # Queue for background loading
])
