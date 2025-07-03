# plotly_integration/pd_dashboard/home/cld/sample_sets/layouts/sample_set_details.py
# Separate layout file for sample set details page

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

# Import the view samples table structure
try:
    from ...view_samples.layouts.view_samples import UP_SAMPLE_FIELDS
except ImportError:
    # Fallback field definitions if import fails
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


def create_sample_set_detail_layout(query_params):
    """Create detailed view layout for a specific sample set with tabs"""
    sample_set_id = query_params.get('id', [None])[0] if query_params else None

    if not sample_set_id:
        return dbc.Container([
            dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "No sample set ID provided"
            ], color="warning")
        ])

    return dbc.Container([
        # Header with navigation
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-info-circle text-primary me-2"),
                    "Sample Set Details"
                ]),
                html.P("Detailed view and analysis management", className="text-muted")
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
                    ], id="edit-sample-set", color="outline-primary", size="sm")
                ], className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Sample Set Basic Info (always visible)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div(id="sample-set-basic-info", children=[
                            dbc.Spinner(color="primary")
                        ])
                    ])
                ], className="shadow-sm")
            ])
        ], className="mb-4"),

        # Tabbed Content
        dbc.Tabs([
            # Tab 1: Overview with samples table
            dbc.Tab(
                label="Overview",
                tab_id="overview-tab",
                children=[
                    html.Div([
                        # Samples Table Section
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([
                                        html.H5([
                                            html.I(className="fas fa-vials me-2"),
                                            "Sample Set Samples"
                                        ], className="mb-0")
                                    ]),
                                    dbc.CardBody([
                                        html.Div(id="sample-set-samples-table", children=[
                                            dbc.Spinner(color="primary")
                                        ])
                                    ])
                                ], className="shadow-sm")
                            ])
                        ], className="mt-4")
                    ])
                ]
            ),

            # Tab 2: Analytics with analysis cards
            dbc.Tab(
                label="Analytics",
                tab_id="analytics-tab",
                children=[
                    html.Div([
                        # Analysis Results Section
                        dbc.Row([
                            dbc.Col([
                                html.H5([
                                    html.I(className="fas fa-chart-line me-2"),
                                    "Analysis Results"
                                ], className="mb-3 mt-4"),
                                html.Div(id="analysis-results-cards", children=[
                                    dbc.Spinner(color="primary")
                                ])
                            ])
                        ])
                    ])
                ]
            )
        ], id="details-tabs", active_tab="overview-tab"),

        # Hidden stores for detail page
        dcc.Store(id="current-sample-set-id", data=sample_set_id),
        dcc.Store(id="sample-set-data", data={}),

        # Dummy output
        html.Div(id="detail-dummy-output", style={"display": "none"})

    ], fluid=True, style={"padding": "20px"})


def create_samples_table_for_set():
    """Create the samples table using the same structure as view_samples"""
    return dash_table.DataTable(
        id="sample-set-details-table",
        columns=UP_SAMPLE_FIELDS,
        data=[],
        editable=True,
        sort_action="native",
        filter_action="native",
        page_action="native",
        page_current=0,
        page_size=20,
        style_table={
            "overflowX": "auto",
            "minWidth": "100%"
        },
        style_cell={
            "textAlign": "left",
            "padding": "8px",
            "fontSize": "14px",
            "fontFamily": "system-ui",
            "whiteSpace": "normal",
            "height": "auto",
            "minWidth": "120px"
        },
        style_header={
            "backgroundColor": "#f8f9fa",
            "fontWeight": "bold",
            "border": "1px solid #dee2e6",
            "textAlign": "center"
        },
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#f8f9fa"
            }
        ],
        export_format="xlsx",
        export_headers="display"
    )


def create_analysis_result_card(analysis_type, status, results_data=None, report_id=None):
    """Create a card for displaying analysis results"""

    # Status configuration
    status_config = {
        "not_requested": {"color": "secondary", "icon": "circle", "text": "Not Requested"},
        "requested": {"color": "warning", "icon": "clock", "text": "Requested"},
        "in_progress": {"color": "info", "icon": "spinner", "text": "In Progress"},
        "completed": {"color": "success", "icon": "check", "text": "Complete"},
        "failed": {"color": "danger", "icon": "times", "text": "Failed"}
    }

    config = status_config.get(status, status_config["not_requested"])

    # Card header with status
    card_header = dbc.CardHeader([
        html.Div([
            html.H6([
                html.I(className=f"fas fa-{get_analysis_icon(analysis_type)} me-2"),
                analysis_type
            ], className="mb-0"),
            html.Span([
                html.I(className=f"fas fa-{config['icon']} me-1"),
                config["text"]
            ], className=f"badge bg-{config['color']}")
        ], className="d-flex justify-content-between align-items-center")
    ])

    # Card body content
    if status == "completed" and results_data:
        card_body = create_analysis_results_content(analysis_type, results_data, report_id)
    elif status in ["requested", "in_progress"]:
        card_body = dbc.CardBody([
            html.P(f"{analysis_type} analysis is {status}.", className="text-muted"),
            html.Small("Results will appear here when analysis is complete.", className="text-muted")
        ])
    else:
        card_body = dbc.CardBody([
            html.P(f"No {analysis_type} analysis requested for this sample set.", className="text-muted"),
            dbc.Button([
                html.I(className="fas fa-play me-1"),
                f"Request {analysis_type} Analysis"
            ],
                id={"type": "request-analysis-detail", "analysis": analysis_type},
                color="outline-primary",
                size="sm")
        ])

    return dbc.Card([
        card_header,
        card_body
    ], className="mb-3 shadow-sm")


def create_analysis_results_content(analysis_type, results_data, report_id=None):
    """Create the content for analysis results based on type"""

    # Common elements
    content = []

    if results_data:
        # Display key results (customize based on analysis type)
        if analysis_type == "SEC":
            content.extend([
                html.P([
                    html.Strong("Results Summary:"), html.Br(),
                    f"Sample Count: {len(results_data)}", html.Br(),
                    f"Latest Analysis: {results_data[0].get('date_analyzed', 'N/A') if results_data else 'N/A'}"
                ]),
                html.Hr()
            ])
        elif analysis_type == "AKTA":
            content.extend([
                html.P([
                    html.Strong("AKTA Summary:"), html.Br(),
                    f"Chromatography runs: {len(results_data)}", html.Br(),
                    f"Latest Run: {results_data[0].get('run_date', 'N/A') if results_data else 'N/A'}"
                ]),
                html.Hr()
            ])
        else:
            # Generic results display
            content.extend([
                html.P([
                    html.Strong(f"{analysis_type} Results:"), html.Br(),
                    f"Data points: {len(results_data)}"
                ]),
                html.Hr()
            ])

    # Action buttons
    buttons = []

    if report_id:
        # Link to analysis app with report ID
        app_url = get_analysis_app_url(analysis_type, report_id)
        if app_url:
            buttons.append(
                dbc.Button([
                    html.I(className="fas fa-external-link-alt me-1"),
                    f"View in {analysis_type} App"
                ],
                    href=app_url,
                    color="primary",
                    size="sm",
                    className="me-2",
                    target="_blank")
            )

    # Download results button
    buttons.append(
        dbc.Button([
            html.I(className="fas fa-download me-1"),
            "Download Results"
        ],
            id={"type": "download-results", "analysis": analysis_type},
            color="outline-secondary",
            size="sm")
    )

    content.append(html.Div(buttons))

    return dbc.CardBody(content)


def get_analysis_icon(analysis_type):
    """Get appropriate icon for analysis type"""
    icon_map = {
        "SEC": "chart-line",
        "AKTA": "wave-square",
        "Titer": "vial",
        "CE-SDS": "dna",
        "cIEF": "electric",
        "Mass Check": "weight",
        "Glycan": "sugar",
        "HCP": "protein",
        "ProA": "molecule"
    }
    return icon_map.get(analysis_type, "flask")


def get_analysis_app_url(analysis_type, report_id):
    """Get the URL for the analysis app with report ID"""
    url_map = {
        "SEC": f"#!/analysis/sec/report?report_id={report_id}",
        "AKTA": f"#!/analysis/akta/report?report_id={report_id}",
        "Titer": f"#!/analysis/titer/report?report_id={report_id}",
        "CE-SDS": f"#!/analysis/ce-sds/report?report_id={report_id}",
        "cIEF": f"#!/analysis/cief/report?report_id={report_id}",
        "Mass Check": f"#!/analysis/mass-check/report?report_id={report_id}",
        "Glycan": f"#!/analysis/glycan/report?report_id={report_id}",
        "HCP": f"#!/analysis/hcp/report?report_id={report_id}",
        "ProA": f"#!/analysis/proa/report?report_id={report_id}"
    }
    return url_map.get(analysis_type)


print("✅ Sample Set Details Layout - Created successfully")