# plotly_integration/pd_dashboard/home/cld/sample_sets/layouts/sample_set_details.py
# Complete layout file with SEC analysis results integration

from dash import html, dash_table, dcc
import dash_bootstrap_components as dbc

# Import field definitions for sample details table
UP_SAMPLE_FIELDS = [
    {"name": "Project", "id": "project", "editable": False},
    {"name": "Sample #", "id": "sample_number", "editable": False},
    {"name": "Clone", "id": "cell_line", "editable": True},
    {"name": "SIP #", "id": "sip_number", "editable": True},
    {"name": "Dev Stage", "id": "development_stage", "editable": True},
    {"name": "Analyst", "id": "analyst", "editable": True},
    {"name": "Harvest Date", "id": "harvest_date", "editable": True, "type": "datetime"},
    {"name": "Unifi #", "id": "unifi_number", "editable": True},
    {"name": "HF Octet Titer", "id": "hf_octet_titer", "editable": True, "type": "numeric"},
    {"name": "ProAqa HF Titer", "id": "pro_aqa_hf_titer", "editable": True, "type": "numeric"},
    {"name": "ProAqa Eluate Titer", "id": "pro_aqa_e_titer", "editable": True, "type": "numeric"},
    {"name": "Eluate A280", "id": "proa_eluate_a280_conc", "editable": True, "type": "numeric"},
    {"name": "HF Volume", "id": "hccf_loading_volume", "editable": True, "type": "numeric"},
    {"name": "Eluate Volume", "id": "proa_eluate_volume", "editable": True, "type": "numeric"},
    {"name": "ProAqa Recovery", "id": "fast_pro_a_recovery", "editable": False, "type": "numeric"},
    {"name": "A280 Recovery", "id": "purification_recovery_a280", "editable": False, "type": "numeric"},
    {"name": "Note", "id": "note", "editable": True}
]

# SEC Results table field definitions
SEC_RESULTS_FIELDS = [
    {"name": "Sample ID", "id": "sample_id", "editable": False},
    {"name": "Main Peak (%)", "id": "main_peak", "editable": False, "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "HMW (%)", "id": "hmw", "editable": False, "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "LMW (%)", "id": "lmw", "editable": False, "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "QC Pass", "id": "qc_pass", "editable": False, "type": "text"},
    {"name": "Status", "id": "status", "editable": False},
    {"name": "Report", "id": "report_name", "editable": False},
    {"name": "Analysis Date", "id": "created_at", "editable": False, "type": "datetime"}
]


def create_sample_set_detail_layout(query_params):
    """Create detailed view layout for a specific sample set"""
    sample_set_id = query_params.get('id', [None])[0] if query_params else None

    if not sample_set_id:
        return dbc.Container([
            dbc.Alert("No sample set ID provided", color="warning")
        ])

    return dbc.Container([
        # Store for current sample set ID
        dcc.Store(id="current-sample-set-id", data=sample_set_id),

        # Header
        dbc.Row([
            dbc.Col([
                html.Div(id="sample-set-basic-info", children=[
                    dbc.Spinner(html.Div("Loading...", className="text-center"), color="primary")
                ])
            ], md=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-arrow-left me-1"),
                        "Back to Sets"
                    ], href="#!/cld/sample-sets", color="outline-secondary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-edit me-1"),
                        "Edit Set"
                    ], color="outline-primary", size="sm", id="edit-sample-set-btn"),
                    dbc.Button([
                        html.I(className="fas fa-sync-alt me-1"),
                        "Refresh"
                    ], color="outline-info", size="sm", id="refresh-sample-set-details-btn")
                ], className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Main content tabs
        dbc.Tabs([
            # Sample Details Tab
            dbc.Tab(label="Sample Details", tab_id="sample-details", children=[
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-vial text-primary me-2"),
                            "Sample Information"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div(id="sample-set-details-table-container", children=[
                            dbc.Spinner(
                                html.Div("Loading sample data...", className="text-center"),
                                color="primary"
                            )
                        ])
                    ])
                ], className="mt-3")
            ]),

            # Analysis Status Tab
            dbc.Tab(label="Analysis Status", tab_id="analysis-status", children=[
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-chart-line text-success me-2"),
                            "Analysis Request Status"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div(id="analysis-status-cards", children=[
                            dbc.Spinner(
                                html.Div("Loading analysis status...", className="text-center"),
                                color="primary"
                            )
                        ])
                    ])
                ], className="mt-3")
            ]),

            # SEC Results Tab - NEW
            dbc.Tab(label="SEC Results", tab_id="sec-results", children=[
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.H5([
                                html.I(className="fas fa-chart-bar text-info me-2"),
                                "SEC Analysis Results"
                            ], className="mb-0 d-inline"),
                            dbc.Badge(
                                id="sec-results-count-badge",
                                color="info",
                                className="ms-2"
                            )
                        ])
                    ]),
                    dbc.CardBody([
                        # SEC Results table
                        html.Div(id="sec-results-table-container", children=[
                            dbc.Spinner(
                                html.Div("Loading SEC results...", className="text-center"),
                                color="primary"
                            )
                        ]),

                        # Summary statistics
                        html.Hr(),
                        html.H6("SEC Results Summary", className="mt-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H4(id="avg-main-peak", children="--", className="text-success"),
                                        html.P("Avg Main Peak (%)", className="text-muted mb-0")
                                    ])
                                ], className="text-center")
                            ], md=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H4(id="avg-hmw", children="--", className="text-warning"),
                                        html.P("Avg HMW (%)", className="text-muted mb-0")
                                    ])
                                ], className="text-center")
                            ], md=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H4(id="avg-lmw", children="--", className="text-info"),
                                        html.P("Avg LMW (%)", className="text-muted mb-0")
                                    ])
                                ], className="text-center")
                            ], md=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H4(id="qc-pass-count", children="--", className="text-primary"),
                                        html.P("QC Pass Rate", className="text-muted mb-0")
                                    ])
                                ], className="text-center")
                            ], md=3)
                        ], id="sec-summary-stats")
                    ])
                ], className="mt-3")
            ])
        ], id="sample-set-detail-tabs", active_tab="sample-details"),

        # Analysis request modal (existing)
        dbc.Modal([
            dbc.ModalHeader([
                html.H5("Request Analysis", className="text-primary")
            ]),
            dbc.ModalBody([
                html.Div(id="analysis-request-modal-content")
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="cancel-analysis-request", color="secondary"),
                dbc.Button("Submit Request", id="submit-analysis-request", color="primary")
            ])
        ], id="analysis-request-modal", size="lg"),

        # Notifications
        html.Div(id="sample-set-details-notifications")
    ], fluid=True, style={"padding": "20px"})


def create_sec_results_table():
    """Create SEC results data table with proper formatting and features"""
    return dash_table.DataTable(
        id="sec-results-table",
        columns=SEC_RESULTS_FIELDS,
        data=[],
        style_table={
            'overflowX': 'auto',
            'minWidth': '100%'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontFamily': 'Arial',
            'fontSize': '14px',
            'whiteSpace': 'normal',
            'height': 'auto'
        },
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold',
            'border': '1px solid #dee2e6'
        },
        style_data={
            'border': '1px solid #dee2e6'
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'qc_pass', 'filter_query': '{qc_pass} = Pass'},
                'backgroundColor': '#d4edda',
                'color': 'black'
            },
            {
                'if': {'column_id': 'qc_pass', 'filter_query': '{qc_pass} = Fail'},
                'backgroundColor': '#f8d7da',
                'color': 'black'
            },
            {
                'if': {'column_id': 'status', 'filter_query': '{status} = complete'},
                'backgroundColor': '#d1ecf1'
            }
        ],
        sort_action="native",
        filter_action="native",
        page_action="native",
        page_current=0,
        page_size=20,
        export_format="xlsx",
        export_headers="display"
    )


def create_sample_set_details_table():
    """Create sample details data table"""
    return dash_table.DataTable(
        id="sample-set-details-table",
        columns=UP_SAMPLE_FIELDS,
        data=[],
        editable=True,
        style_table={
            'overflowX': 'auto',
            'minWidth': '100%'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontFamily': 'Arial',
            'fontSize': '14px',
            'whiteSpace': 'normal',
            'height': 'auto'
        },
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold',
            'border': '1px solid #dee2e6'
        },
        style_data={
            'border': '1px solid #dee2e6'
        },
        style_data_conditional=[
            {
                'if': {'column_editable': False},
                'backgroundColor': '#f8f9fa'
            }
        ],
        sort_action="native",
        filter_action="native",
        page_action="native",
        page_current=0,
        page_size=20,
        export_format="xlsx",
        export_headers="display"
    )


print("Complete sample set details layout with SEC results loaded")