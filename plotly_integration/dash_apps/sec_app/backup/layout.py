from dash import html, dcc, dash_table
import plotly.graph_objects as go
from .table_config import TABLE_STYLE_CELL, TABLE_STYLE_HEADER

# Layout for the Dash app
app_layout = html.Div([
    dcc.Store(id='tab-visibility-store', data={"show_sample_analysis": True, "show_standard_analysis": True}),
    dcc.Location(id="url", refresh=False),
    dcc.Store(id='selected-report', data=None),
    dcc.Store(id="report-settings"),
    dcc.Store(id="settings-applied", data={}),
    dcc.Store(id="std-result-id-store"),
    dcc.Store(id='regression-parameters', data={'slope': 0, 'intercept': 0}),
    dcc.Store(id='main-peak-rt-store', data=None),  # Default value for main peak RT
    dcc.Store(id='low-mw-cutoff-store', data=12),  # Default value for low MW cutoff
    dcc.Store(id='hmw-table-store', data=[]),
    dcc.Store(id='report-list-store', data=[]),

    # Top-left Home Button
    html.Div([
        dcc.Interval(id="reset-save-settings-timer", interval=3000, n_intervals=0, disabled=True),
        dcc.Store(id="reset-save-settings-trigger", data=False),
        html.Button("💾 Save Settings", id="save-plot-settings", style={
            'background-color': '#0056b3',
            'color': 'white',
            'border': 'none',
            'padding': '10px 20px',
            'font-size': '16px',
            'cursor': 'pointer',
            'border-radius': '5px'
        })
    ], style={'margin': '10px'}),

    html.Div([  # Main layout with sidebar and content areas

        html.Div([  # Main content container
            dcc.Tabs(id="main-tabs", value="tab-1", children=[
                dcc.Tab(
                    label="Select Report",
                    value="tab-1",
                    id="select-report-tab",
                    children=[

                        # Mode and Sample Type Selectors
                        html.Div([
                            html.Label("Mode:", style={"fontWeight": "bold", "marginRight": "10px"}),
                            dcc.Dropdown(
                                id="view_mode",
                                options=[
                                    {"label": "Select Report", "value": "report"},
                                    {"label": "Select Samples", "value": "samples"},
                                ],
                                value="report",
                                style={"width": "250px"}
                            ),
                            html.Label("Sample Type:", id="sample-type-label",
                                       style={"fontWeight": "bold", "marginLeft": "30px", "marginRight": "10px"}),
                            dcc.Dropdown(
                                id="sample_type_filter",
                                options=[
                                    {"label": "PD", "value": "PD"},
                                    {"label": "UP", "value": "UP"},
                                    {"label": "FB", "value": "FB"},

                                ],
                                value="PD",
                                style={"width": "150px"}
                            )
                        ], style={
                            "display": "flex",
                            "alignItems": "center",
                            "marginTop": "20px",  # 👈 Top margin added
                            "marginBottom": "15px"
                        }),

                        # Report Selection Table Container
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
                                page_size=20,
                                sort_action="native",
                                filter_action="native",
                                row_selectable="single",
                                style_table={'overflowX': 'auto'},
                                style_cell=TABLE_STYLE_CELL,
                                style_header=TABLE_STYLE_HEADER,
                                style_data_conditional=[
                                    {"if": {"state": "active"}, "backgroundColor": "#f0f8ff",
                                     "border": "1px solid #0056b3"},
                                    {"if": {"state": "selected"}, "backgroundColor": "#d9eaff", "fontWeight": "bold"}
                                ],
                            )
                        ], style={
                            'width': '98%',
                            'margin': 'auto',
                            'padding': '10px',
                            'border': '2px solid #0056b3',
                            'border-radius': '5px',
                            'background-color': '#f7f9fc',
                            'margin-bottom': '10px',
                            'display': 'block'  # Will be toggled in callback
                        }),

                        # Sample Selection Table Container
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
                                data=[],  # filled by callback
                                page_size=20,
                                sort_action="native",
                                filter_action="native",
                                row_selectable="multi",
                                style_table={'overflowX': 'auto'},
                                style_cell=TABLE_STYLE_CELL,
                                style_header=TABLE_STYLE_HEADER,
                            )
                        ], style={
                            'width': '98%',
                            'margin': 'auto',
                            'padding': '10px',
                            'border': '2px solid #0056b3',
                            'border-radius': '5px',
                            'background-color': '#f7f9fc',
                            'margin-bottom': '10px',
                            'display': 'none'  # Will be toggled in callback
                        }),

                        # Status area (used by both modes)
                        html.Div(id="submission_status", style={
                            "textAlign": "center",
                            "color": "green",
                            "fontWeight": "bold",
                            "fontSize": "16px",
                            "marginBottom": "10px"
                        })
                    ]
                ),

                # 🔹 Tab 2: Sample Analysis
                dcc.Tab(label="Sample Analysis", value="tab-2", children=[
                    html.Div([  # Plot and settings
                        dcc.Store(id='selected-report', data={}),  # Add this line for state persistence
                        html.Div(  # Plot area
                            id='plot-area',
                            children=[
                                html.H4("SEC Results", id="sec-results-header",
                                        style={'text-align': 'center', 'color': '#0056b3'}),
                                dcc.Graph(
                                    id='time-series-graph',
                                    figure=go.Figure(
                                        data=[go.Scatter(
                                            x=[],
                                            y=[],
                                            mode='lines'
                                        )],
                                        layout=go.Layout(
                                            title="Sample Plot",
                                            xaxis_title="Time",
                                            yaxis_title="UV280",
                                            height=800,  # Adjust height (default is 400)
                                            dragmode="select",
                                            annotations=[
                                                {
                                                    # "showarrow": True
                                                }
                                            ]
                                        )
                                    ),
                                    config={  # ✅ Correct placement
                                        'toImageButtonOptions': {
                                            'filename': 'custom_name'},
                                        'edits': {"annotationPosition": True}}

                                )
                            ],
                            style={
                                'width': '85%',
                                'padding': '10px',
                                'border': '2px solid #0056b3',
                                'border-radius': '5px',
                                'background-color': '#f7f9fc',
                                'margin-bottom': '10px'
                            }
                        ),
                        html.Div(  # Plot settings
                            id='plot-settings',
                            children=[
                                html.H4("Plot Settings", style={'color': '#0056b3'}),
                                dcc.Checklist(
                                    id='channel-checklist',
                                    options=[
                                        {'label': 'UV280', 'value': 'channel_1'},
                                        {'label': 'UV260', 'value': 'channel_2'},
                                        {'label': 'Pressure', 'value': 'channel_3'}
                                    ],
                                    value=['channel_1']
                                ),
                                html.Div([
                                    html.Label("Select Plot Type:", style={'color': '#0056b3'}),
                                    dcc.Dropdown(
                                        id='plot-type-dropdown',
                                        options=[
                                            {'label': 'Plotly Graph', 'value': 'plotly'},
                                            {'label': 'Subplots', 'value': 'subplots'}
                                        ],
                                        value='subplots',  # Default value
                                        style={'width': '100%'}
                                    )
                                ], style={'margin-top': '10px'}),
                                dcc.Checklist(
                                    id='shading-checklist',
                                    options=[
                                        {'label': 'Enable Shading', 'value': 'enable_shading'}
                                    ],
                                    value=['enable_shading'],  # Default to off
                                    style={'margin-top': '10px'}
                                ),
                                html.Div([
                                    html.Label("Main Peak RT:", style={'color': '#0056b3'}),
                                    dcc.Input(
                                        id='main-peak-rt-input',
                                        type='number',
                                        value=7.843,  # Default
                                        style={'width': '100%'}
                                    ),
                                    dcc.Store(id='main-peak-rt-store', data=5.10),
                                ], style={'margin-top': '10px'}),

                                html.Button("Refresh RT", id="refresh-rt-btn", n_clicks=0, style={
                                    'background-color': '#0056b3',
                                    'color': 'white',
                                    'border': 'none',
                                    'padding': '10px',
                                    'font-size': '14px',
                                    'cursor': 'pointer',
                                    'border-radius': '5px',
                                    'margin-left': '0px',
                                    'margin-top': '15px',  # Adds space above the button
                                    'margin-bottom': '15px'  # Adds space below the button
                                }),

                                html.Div([
                                    html.Label("LMW Cutoff Time:", style={'color': '#0056b3'}),
                                    dcc.Input(
                                        id='low-mw-cutoff-input',
                                        type='number',
                                        value=12,  # Default value
                                        style={'width': '100%'}
                                    )
                                ], style={'margin-top': '10px'}),

                                dcc.Checklist(
                                    id='peak-label-checklist',
                                    options=[
                                        {'label': 'Enable Peak Labeling', 'value': 'enable_peak_labeling'}
                                    ],
                                    value=['enable_peak_labeling'],  # Default to no peak labeling
                                    style={'margin-top': '10px'}
                                ),
                                html.Div([
                                    html.Label("Number of Columns:", style={'color': '#0056b3'}),
                                    dcc.Input(
                                        id='num-cols-input',
                                        type='number',
                                        min=1,
                                        step=1,
                                        value=3,  # Default value
                                        debounce=True,
                                        style={'width': '100%'}
                                    )
                                ], style={'margin-top': '10px'}),

                                html.Div([
                                    html.Label("Vertical Spacing:", style={'color': '#0056b3'}),
                                    dcc.Input(
                                        id='vertical-spacing-input',
                                        type='number',
                                        min=0,
                                        max=1,
                                        step=0.01,
                                        value=0.05,  # Default value
                                        style={'width': '100%'}
                                    )
                                ], style={'margin-top': '10px'}),
                                html.Div([
                                    html.Label("Horizontal Spacing:", style={'color': '#0056b3'}),
                                    dcc.Input(
                                        id='horizontal-spacing-input',
                                        type='number',
                                        min=0,
                                        max=1,
                                        step=0.01,
                                        value=0.05,  # Default value
                                        style={'width': '100%'}
                                    )
                                ], style={'margin-top': '10px'}),

                            ],
                            style={
                                'height': '100%',
                                'width': '15%',
                                'padding': '10px',
                                'background-color': '#f7f9fc',
                                'border': '2px solid #0056b3',
                                'border-radius': '5px',
                            }

                        )
                    ], style={'display': 'flex', 'flex-direction': 'row', 'gap': '10px'}),
                ]),

                # 🔹 Tab 3: Standard Analysis
                dcc.Tab(label="Table Data", value="tab-3", children=[
                    html.Div(
                        id='project-info-banner',
                        children=[
                            html.H4("Project Information", style={'text-align': 'center', 'color': '#0056b3'}),
                            html.P(id='project-id-display', style={'fontSize': '14px'}),
                            html.P(id='expected-mw-display', style={'fontSize': '14px'})
                        ],
                        style={
                            'width': '98%',
                            'padding': '10px',
                            'border': '2px solid #0056b3',
                            'border-radius': '5px',
                            'background-color': '#e6f0fa',
                            'margin-bottom': '15px'
                        }
                    ),

                    html.Div(
                        id='hmw-data',
                        children=[
                            html.H4("Peak Results", style={'text-align': 'center', 'color': '#0056b3'}),
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
                                # Default columns
                                multi=True,
                                placeholder="Select columns to display",
                                style={'margin-bottom': '10px'},

                            ),
                            dash_table.DataTable(
                                id='hmw-table',
                                columns=[  # Default columns for initialization
                                    {"name": "Sample Name", "id": "Sample Name"},
                                    {"name": "HMW %", "id": "HMW"},
                                    {"name": "Main Peak %", "id": "Main Peak"},
                                    {"name": "LMW %", "id": "LMW"}
                                ],
                                data=[],  # Dynamically updated by the callback
                                sort_action="native",
                                style_table={'overflowX': 'auto'},
                                style_cell={'textAlign': 'center', 'padding': '5px'},
                                style_header={'fontWeight': 'bold', 'backgroundColor': '#e9f1fb'},
                                style_data_conditional=[
                                    {
                                        'if': {
                                            'filter_query': '{MW Deviation} > 30 || {MW Deviation} < -10',
                                            'column_id': 'MW Deviation'
                                        },
                                        'color': 'white',
                                        'backgroundColor': '#d9534f',  # red
                                        'fontWeight': 'bold'
                                    },
                                    {
                                        'if': {
                                            'filter_query': '{Calculated MW} = "Error" || {MW Deviation} = "Error"',
                                            'column_id': 'MW Deviation'
                                        },
                                        'color': 'white',
                                        'backgroundColor': '#6c757d',  # gray
                                        'fontWeight': 'bold'
                                    }
                                ]

                            ),
                            html.Button("Export to XLSX", id="export-button", style={
                                'margin-top': '10px',
                                'background-color': '#0056b3',
                                'color': 'white',
                                'border': 'none',
                                'padding': '10px',
                                'font-size': '14px',
                                'cursor': 'pointer',
                                'border-radius': '5px'
                            }),
                            dcc.Download(id="download-hmw-data")
                        ],
                        style={
                            'width': '98%',
                            'padding': '10px',
                            'border': '2px solid #0056b3',
                            'border-radius': '5px',
                            'background-color': '#f7f9fc'
                        }
                    ),

                    html.Div(
                        id='sample-details',
                        children=[
                            html.H4("Sample Details", style={'text-align': 'center', 'color': '#0056b3'}),
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
                                    'padding': '5px',
                                    'border': '1px solid #ddd',
                                    'backgroundColor': '#f7f9fc',
                                },
                                style_header={
                                    'backgroundColor': '#0056b3',
                                    'fontWeight': 'bold',
                                    'color': 'white',
                                    'textAlign': 'center',
                                },
                            )
                        ],
                        style={
                            'width': '98%',
                            'margin-top': '20px',
                            'padding': '10px',
                            'border': '2px solid #0056b3',
                            'border-radius': '5px',
                            'background-color': '#f7f9fc'
                        }
                    ),
                ]),

                # 🔹 Tab 4: Standard Analysis
                dcc.Tab(label="Standard Analysis", value="tab-4", children=[
                    html.Div(
                        id='standard-analysis',
                        children=[
                            html.H4("Standard Analysis", style={'text-align': 'center', 'color': '#0056b3'}),

                            # 🔹 Standard ID Dropdown
                            html.Div([
                                html.Label("Select Standard ID:", style={'color': '#0056b3'}),
                                dcc.Dropdown(
                                    id='standard-id-dropdown',
                                    placeholder="Select a Standard ID",
                                    value='',
                                    style={'width': '100%'}
                                )
                            ], style={'margin-top': '10px'}),

                            html.Div(
                                id='standard-analysis-content',
                                children=[
                                    # 🔹 Standard Peak Plot
                                    dcc.Graph(
                                        id='standard-peak-plot',
                                        figure=go.Figure(
                                            data=[go.Scatter(
                                                x=[],
                                                y=[],
                                                mode='lines'
                                            )],
                                            layout=go.Layout(
                                                title="Sample Plot",
                                                xaxis_title="Time",
                                                yaxis_title="UV280",
                                                height=375,  # Adjust height (default is 400)
                                                dragmode="select",
                                            )
                                        ),

                                        style={'margin-top': '10px'}
                                    )],
                                style={
                                    'padding': '10px',
                                    'border': '2px solid #0056b3',
                                    'border-radius': '5px',
                                    'background-color': '#f7f9fc',
                                    'margin-top': '20px',
                                }
                            ),

                            html.Div(
                                id='standard-analysis-content',
                                children=[
                                    dcc.Graph(
                                        id='regression-plot',
                                        figure=go.Figure(
                                            data=[go.Scatter(
                                                x=[],
                                                y=[],
                                                mode='lines',
                                                line=dict(dash='dash'),  # ✅ Makes the line dashed
                                            )],
                                            layout=go.Layout(
                                                title="Sample Plot",
                                                xaxis_title="Retention Time (min)",
                                                yaxis_title="Log(MW)",
                                                height=375,  # Adjust height (default is 400)
                                                dragmode="select",
                                            )
                                        ),
                                        style={'margin-top': '20px'}),
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
                                        row_selectable='multi',  # Allow multiple rows to be selected
                                        selected_rows=[i for i in range(4)],  # Default: select all rows in `data`
                                        style_table={'overflowX': 'auto'},
                                        style_cell={'textAlign': 'center', 'padding': '5px'},
                                        style_header={'fontWeight': 'bold', 'backgroundColor': '#e9f1fb'}
                                    )
                                ],
                                style={
                                    'padding': '10px',
                                    'margin-top': '20px',
                                    'border': '2px solid #0056b3',
                                    'border-radius': '5px',
                                    'background-color': '#f7f9fc',
                                }
                            ),

                            html.P("Regression Equation: ", id="regression-equation"),
                            html.P("R² Value: ", id="r-squared-value"),
                            html.P("Estimated MW for RT: ", id="estimated-mw"),

                            dcc.Input(
                                id="rt-input",
                                type="number",
                                placeholder="Enter Retention Time",
                                style={'width': '80%', 'margin-top': '10px'}
                            ),

                            html.Button("Calculate MW", id="calculate-mw-button", style={
                                'background-color': '#0056b3',
                                'color': 'white',
                                'border': 'none',
                                'padding': '10px',
                                'cursor': 'pointer',
                                'border-radius': '5px'
                            }),
                        ],
                        style={
                            'width': '98%',  # Match the width of the Sample Details box
                            'margin-top': '20px',
                            'padding': '10px',
                            'border': '2px solid #0056b3',
                            'border-radius': '5px',
                            'background-color': '#f7f9fc'
                        }
                    )
                ]),
                dcc.Tab(
                    id="lims-link-tab",
                    label="Link Samples to LIMS",
                    value="tab-5",
                    style={},  # Keep empty or with your default styles
                    children=[
                        html.Div(
                            id='link-samples-lims-container',
                            children=[
                                html.H4("Link SEC Results to LIMS Samples",
                                        style={'text-align': 'center', 'color': '#0056b3'}),

                                html.Div([
                                    html.Button("🔗 Link SEC Results to Samples", id="link-samples-btn", n_clicks=0),
                                    html.Div(id="link-samples-status", style={
                                        'marginTop': '10px',
                                        'color': 'green',
                                        'fontWeight': 'bold'
                                    })
                                ], style={
                                    'padding': '20px',
                                    'border': '2px solid #0056b3',
                                    'border-radius': '5px',
                                    'background-color': '#f7f9fc',
                                    'margin-top': '20px'
                                }),
                            ],
                            style={
                                'width': '98%',
                                'padding': '10px',
                                'border': '2px solid #0056b3',
                                'border-radius': '5px',
                                'background-color': '#f7f9fc'
                            }
                        )
                    ]
                ),
            ])
        ], style={'width': '100%', 'padding': '10px', 'overflow-y': 'auto'})
    ], style={'display': 'flex', 'flex-direction': 'row', 'gap': '10px'})
])
