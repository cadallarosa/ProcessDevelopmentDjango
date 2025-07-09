# plotly_integration/pd_dashboard/home/cld/sample_sets/layouts/sample_sets.py
# Updated to move actions left, remove AKTA, add sample range, remove set name

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

        # Quick stats
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

        # Table container
        dbc.Row([
            dbc.Col([
                html.Div(id="sample-sets-table-container", children=[
                    dbc.Spinner(
                        html.Div("Loading sample sets...", className="text-center p-4"),
                        color="primary"
                    )
                ])
            ])
        ]),

        # Store for selected sample set data
        dcc.Store(id="selected-sample-set", data={}),

        # Modals
        create_analysis_request_modal(),
        create_sample_set_details_modal(),

        # Notifications area
        html.Div(id="sample-sets-notifications"),

        # Dummy output for callbacks
        html.Div(id="dummy-output", style={"display": "none"})

    ], fluid=True, style={"padding": "20px"})


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
    """Create the data table for sample sets with analysis status columns - UPDATED"""
    if not sample_sets_data:
        return dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "No sample sets found. Create some samples to get started!"
        ], color="info")

    # Define table columns - ACTIONS MOVED TO FIRST COLUMN, REMOVED SET NAME
    columns = [
        # Actions column moved to the left
        {"name": "Actions", "id": "actions", "presentation": "markdown"},
        {"name": "Project", "id": "project_id", "type": "text"},
        {"name": "SIP", "id": "sip_number", "type": "text"},
        {"name": "Sample Range", "id": "sample_range", "type": "text"},  # NEW COLUMN
        {"name": "Samples", "id": "sample_count", "type": "numeric"},
        {"name": "Created", "id": "created_date", "type": "text"},
        # Analysis status columns (removed AKTA)
        {"name": "SEC", "id": "sec_status", "presentation": "markdown"},
        {"name": "Titer", "id": "titer_status", "presentation": "markdown"},
        {"name": "CE-SDS", "id": "ce_sds_status", "presentation": "markdown"},
        {"name": "cIEF", "id": "cief_status", "presentation": "markdown"},
        {"name": "Mass Check", "id": "mass_check_status", "presentation": "markdown"},
        {"name": "Glycan", "id": "glycan_status", "presentation": "markdown"},
        {"name": "HCP", "id": "hcp_status", "presentation": "markdown"},
        {"name": "ProA", "id": "proa_status", "presentation": "markdown"}
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


def create_analysis_request_modal():
    """Create modal for requesting analysis on sample sets"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H5("Request Analysis", className="text-primary")
        ]),
        dbc.ModalBody([
            html.Div(id="modal-sample-set-info", className="mb-3"),
            html.Div([
                html.Label("Select Analysis Types", className="fw-bold mb-2"),
                dbc.Checklist(
                    id="analysis-type-checklist",
                    options=[
                        {"label": "SEC - Size Exclusion Chromatography", "value": "SEC"},
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


def create_sample_set_details_modal():
    """Create modal for viewing sample set details"""
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


print("Sample sets layout components loaded successfully")