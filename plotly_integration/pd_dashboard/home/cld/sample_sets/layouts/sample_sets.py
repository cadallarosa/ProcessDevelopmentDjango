# plotly_integration/pd_dashboard/home/cld/sample_sets/layouts/sample_sets.py
# Updated to use the new sample_set_details layout

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc


def create_sample_sets_main_layout():
    """Create main sample sets layout with table view"""
    return dbc.Container([
        # Header with navigation
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-layer-group text-primary me-2"),
                    "Sample Sets Management"
                ]),
                html.P("Monitor and manage analysis status for sample sets", className="text-muted")
            ], md=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-plus me-1"),
                        "Create Set"
                    ], href="#!/cld/create-sample-sets", color="primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-sync-alt me-1"),
                        "Refresh"
                    ], id="refresh-sample-sets-btn", color="outline-secondary", size="sm")
                ], className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Quick stats (keep existing metrics functionality)
        dbc.Row([
            dbc.Col([
                create_metric_card("Total Sets", "total-sets-metric", "fa-layer-group", "primary")
            ], md=3),
            dbc.Col([
                create_metric_card("Pending Analysis", "pending-metric", "fa-clock", "warning")
            ], md=3),
            dbc.Col([
                create_metric_card("In Progress", "in-progress-metric", "fa-spinner", "info")
            ], md=3),
            dbc.Col([
                create_metric_card("Completed", "completed-metric", "fa-check-circle", "success")
            ], md=3)
        ], className="mb-4"),

        # Filters
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Filter by Status:", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="status-filter",
                                    options=[
                                        {"label": "All Sample Sets", "value": "all"},
                                        {"label": "No Analysis Requested", "value": "none"},
                                        {"label": "Pending Analysis", "value": "pending"},
                                        {"label": "Analysis Complete", "value": "complete"}
                                    ],
                                    value="all",
                                    clearable=False
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("Search:", className="fw-bold small"),
                                dbc.Input(
                                    id="search-input",
                                    placeholder="Search by project, SIP, or set name...",
                                    type="text"
                                )
                            ], md=4),
                            dbc.Col([
                                html.Label("Project:", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="project-filter",
                                    placeholder="All projects",
                                    clearable=True
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("Actions:", className="fw-bold small"),
                                dbc.Button([
                                    html.I(className="fas fa-search me-1"),
                                    "Apply Filters"
                                ], id="apply-filters-btn", color="outline-primary", size="sm", className="mt-1")
                            ], md=2)
                        ])
                    ])
                ], className="shadow-sm")
            ])
        ], className="mb-4"),

        # Sample Sets Table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.H5("Sample Sets", className="mb-0"),
                            html.Small("Click 'Details' to view individual samples and manage analysis", className="text-muted")
                        ])
                    ]),
                    dbc.CardBody([
                        html.Div(id="sample-sets-table-container", children=[
                            dbc.Spinner(
                                html.Div([
                                    html.P("Loading sample sets...", className="text-center text-muted"),
                                ], style={"height": "200px", "display": "flex", "alignItems": "center", "justifyContent": "center"}),
                                color="primary"
                            )
                        ])
                    ])
                ], className="shadow-sm")
            ])
        ]),

        # Keep existing hidden stores and modals from original implementation
        dcc.Store(id="selected-sample-set", data={}),
        dcc.Store(id="available-projects", data=[]),
        dcc.Store(id="sec-report-created", data={}),
        dcc.Store(id="sec-selected-sample-set", data={}),

        # Keep existing modals (SEC, analysis request, etc.)
        create_sec_sample_selection_modal(),
        create_sample_set_details_modal(),
        create_analysis_request_modal(),

        # Notifications area
        html.Div(id="sample-sets-notifications"),

        # Dummy output for callbacks
        html.Div(id="dummy-output", style={"display": "none"})

    ], fluid=True, style={"padding": "20px"})


# REMOVED: create_sample_set_detail_layout - now in separate file
# Use sample_set_details.py for the details page layout


def create_metric_card(title, metric_id, icon, color):
    """Create a metric display card"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.H3("0", id=metric_id, className=f"text-{color} mb-0"),
                    html.P(title, className="text-muted mb-0 small")
                ], className="flex-grow-1"),
                html.Div([
                    html.I(className=f"fas {icon} fa-2x text-{color} opacity-75")
                ], className="align-self-center")
            ], className="d-flex")
        ])
    ], className="shadow-sm h-100")


def create_sample_sets_table(sample_sets_data):
    """Create the data table for sample sets with analysis status columns"""
    if not sample_sets_data:
        return dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "No sample sets found. Create some samples to get started!"
        ], color="info")

    # Define table columns - keep basic info + analysis status
    columns = [
        {"name": "Set Name", "id": "set_name", "type": "text"},
        {"name": "Project", "id": "project_id", "type": "text"},
        {"name": "SIP", "id": "sip_number", "type": "text"},
        {"name": "Samples", "id": "sample_count", "type": "numeric"},
        {"name": "Created", "id": "created_date", "type": "text"},
        # Analysis status columns
        {"name": "SEC", "id": "sec_status", "presentation": "markdown"},
        {"name": "AKTA", "id": "akta_status", "presentation": "markdown"},
        {"name": "Titer", "id": "titer_status", "presentation": "markdown"},
        {"name": "CE-SDS", "id": "ce_sds_status", "presentation": "markdown"},
        {"name": "cIEF", "id": "cief_status", "presentation": "markdown"},
        {"name": "Mass Check", "id": "mass_check_status", "presentation": "markdown"},
        {"name": "Glycan", "id": "glycan_status", "presentation": "markdown"},
        {"name": "HCP", "id": "hcp_status", "presentation": "markdown"},
        {"name": "ProA", "id": "proa_status", "presentation": "markdown"},
        # Actions column
        {"name": "Actions", "id": "actions", "presentation": "markdown"}
    ]

    return dash_table.DataTable(
        id="sample-sets-datatable",
        columns=columns,
        data=sample_sets_data,
        sort_action="native",
        filter_action="native",
        page_action="native",
        page_current=0,
        page_size=15,
        style_table={"overflowX": "auto"},
        style_cell={
            "textAlign": "left",
            "padding": "8px",
            "fontSize": "14px",
            "fontFamily": "system-ui",
            "whiteSpace": "normal",
            "height": "auto",
            "minWidth": "100px"
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
        markdown_options={"html": True}
    )


# Keep existing modal functions
def create_sec_sample_selection_modal():
    """Create modal for SEC sample selection (keep existing)"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H5("Select Samples for SEC Analysis", className="text-primary")
        ]),
        dbc.ModalBody([
            html.Div([
                html.Label("Report Name", className="fw-bold"),
                dbc.Input(id="sec-report-name", placeholder="Enter report name", className="mb-3")
            ]),
            html.Div([
                html.Label("Comments", className="fw-bold"),
                dbc.Textarea(id="sec-report-comments", placeholder="Optional comments", rows=2, className="mb-3")
            ]),
            html.Div(id="sec-modal-info", className="mb-3"),
            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                "Select which samples to include in the SEC analysis. Disabled samples have no SEC results."
            ], color="info", className="mb-3"),
            dbc.Checklist(
                id="sec-sample-checklist",
                options=[],
                value=[],
                className="mb-3",
                style={"maxHeight": "300px", "overflowY": "auto"}
            ),
            html.Div(id="sec-selection-status", className="mb-3")
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-sec-creation", color="secondary"),
            dbc.Button([
                html.I(className="fas fa-chart-line me-2"),
                "Create SEC Report"
            ], id="create-sec-report-with-samples", color="primary", disabled=False)
        ])
    ], id="sec-sample-selection-modal", size="lg", scrollable=True)


def create_sample_set_details_modal():
    """Create modal for viewing sample set details (keep existing)"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H5("Sample Set Details", className="text-primary")
        ]),
        dbc.ModalBody([
            html.Div(id="modal-sample-set-details")
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id="close-details-modal", color="secondary")
        ])
    ], id="sample-set-details-modal", size="xl")


def create_analysis_request_modal():
    """Create modal for analysis requests (keep existing)"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H5("Request Analysis", className="text-primary")
        ]),
        dbc.ModalBody([
            html.Div([
                html.Label("Analysis Types", className="fw-bold"),
                dbc.Checklist(
                    id="analysis-types",
                    options=[
                        {"label": "SEC - Size Exclusion Chromatography", "value": "SEC"},
                        {"label": "AKTA - Chromatography", "value": "AKTA"},
                        {"label": "Titer - Potency Assay", "value": "Titer"},
                        {"label": "CE-SDS - Capillary Electrophoresis", "value": "CE-SDS"},
                        {"label": "cIEF - Capillary Isoelectric Focusing", "value": "cIEF"},
                        {"label": "Mass Check - Mass Spectrometry", "value": "Mass Check"},
                        {"label": "Glycan Analysis", "value": "Glycan"},
                        {"label": "HCP - Host Cell Protein", "value": "HCP"},
                        {"label": "ProA - Protein A", "value": "ProA"}
                    ],
                    value=[],
                    className="mb-3"
                ),
                html.Div([
                    html.Label("Priority", className="fw-bold"),
                    dbc.RadioItems(
                        id="analysis-priority",
                        options=[
                            {"label": "Normal", "value": 1},
                            {"label": "High", "value": 2},
                            {"label": "Urgent", "value": 3}
                        ],
                        value=1,
                        inline=True
                    )
                ], className="mb-3"),
                html.Div([
                    html.Label("Notes", className="fw-bold"),
                    dbc.Textarea(
                        id="analysis-notes",
                        placeholder="Add any special instructions...",
                        rows=3
                    )
                ])
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-analysis-request", color="secondary"),
            dbc.Button([
                html.I(className="fas fa-paper-plane me-2"),
                "Submit Request"
            ], id="submit-analysis-request", color="primary")
        ])
    ], id="analysis-request-modal", size="lg")


print("✅ Main Sample Sets Layout - Updated to use separate details file")