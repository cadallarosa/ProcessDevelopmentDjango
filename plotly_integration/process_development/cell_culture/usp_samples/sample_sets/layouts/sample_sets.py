from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc


def create_usp_sample_sets_main_layout():
    """Create main USP sample sets layout with table view"""
    return dbc.Container([
        # Header with navigation
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-layer-group text-primary me-2"),
                    "USP Sample Sets Management"
                ]),
                html.P("Monitor and manage analysis status for USP sample sets grouped by project and reactor type", 
                       className="text-muted")
            ], md=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-plus me-1"),
                        "Create Set"
                    ], id="usp-create-new-set-btn", color="primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-sync-alt me-1"),
                        "Refresh"
                    ], id="usp-refresh-sample-sets-btn", color="outline-secondary", size="sm")
                ], className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Quick stats (USP-specific metrics)
        dbc.Row([
            dbc.Col([
                create_metric_card("Total Sets", "usp-total-sets-metric", "fa-layer-group", "primary")
            ], md=3),
            dbc.Col([
                create_metric_card("Pending Analysis", "usp-pending-metric", "fa-clock", "warning")
            ], md=3),
            dbc.Col([
                create_metric_card("In Progress", "usp-in-progress-metric", "fa-spinner", "info")
            ], md=3),
            dbc.Col([
                create_metric_card("Completed", "usp-completed-metric", "fa-check-circle", "success")
            ], md=3)
        ], className="mb-4"),

        # Filters (USP-specific)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Filter by Status:", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="usp-status-filter",
                                    options=[
                                        {"label": "All Sample Sets", "value": "all"},
                                        {"label": "No Analysis Requested", "value": "none"},
                                        {"label": "Pending Analysis", "value": "pending"},
                                        {"label": "Analysis Complete", "value": "complete"}
                                    ],
                                    value="all",
                                    clearable=False
                                )
                            ], md=2),
                            dbc.Col([
                                html.Label("Search:", className="fw-bold small"),
                                dbc.Input(
                                    id="usp-search-input",
                                    placeholder="Search by project, reactor, or set name...",
                                    type="text"
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("Project:", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="usp-project-filter",
                                    placeholder="All projects",
                                    clearable=True
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("Reactor Type:", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="usp-reactor-filter",
                                    placeholder="All reactor types",
                                    clearable=True
                                )
                            ], md=2),
                            dbc.Col([
                                html.Label("Actions:", className="fw-bold small"),
                                dbc.Button([
                                    html.I(className="fas fa-search me-1"),
                                    "Apply Filters"
                                ], id="usp-apply-filters-btn", color="outline-primary", size="sm", className="mt-1")
                            ], md=2)
                        ])
                    ])
                ], className="shadow-sm")
            ])
        ], className="mb-4"),

        # USP Sample Sets Table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.H5("USP Sample Sets", className="mb-0"),
                            html.Small("Click 'Details' to view individual samples and manage analysis", 
                                     className="text-muted")
                        ])
                    ]),
                    dbc.CardBody([
                        html.Div(id="usp-sample-sets-table-container", children=[
                            dbc.Spinner(
                                html.Div([
                                    html.P("Loading USP sample sets...", className="text-center text-muted"),
                                ], style={"height": "200px", "display": "flex", "alignItems": "center", 
                                         "justifyContent": "center"}),
                                color="primary"
                            )
                        ])
                    ])
                ], className="shadow-sm")
            ])
        ]),

        # Create Sample Set Modal
        create_usp_sample_set_creation_modal(),

        # Hidden stores and modals
        dcc.Store(id="usp-selected-sample-set", data={}),
        dcc.Store(id="usp-selected-samples", data=[]),
        dcc.Store(id="usp-available-projects", data=[]),

        # Notifications area
        html.Div(id="usp-sample-sets-notifications"),

        # Dummy output for callbacks
        html.Div(id="usp-dummy-output", style={"display": "none"})

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


def create_usp_sample_sets_table(sample_sets_data):
    """Create the data table for USP sample sets with analysis status columns"""
    if not sample_sets_data:
        return dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "No USP sample sets found. Create some samples and organize them into sets to get started!"
        ], color="info")

    # Define table columns for USP sample sets
    columns = [
        {"name": "Actions", "id": "actions", "presentation": "markdown"},
        {"name": "Project ID", "id": "project_id"},
        {"name": "Reactor Type", "id": "reactor_type"},
        {"name": "Exp #", "id": "experiment_number"},
        {"name": "Cell Line", "id": "cell_line"},
        {"name": "Sample Range", "id": "sample_range"},
        {"name": "Count", "id": "sample_count", "type": "numeric"},
        {"name": "Requested Analysis", "id": "requested_analysis"},
        {"name": "Completed Analysis", "id": "completed_analysis"},
        {"name": "Created", "id": "created_date"},
    ]

    return dash_table.DataTable(
        id="usp-sample-sets-datatable",
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


def create_usp_sample_set_creation_modal():
    """Create modal for creating new USP sample sets"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H5("Create New USP Sample Set", className="text-primary")
        ]),
        dbc.ModalBody([
            dbc.Form([
                # Row 1: Set Name and Project
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Set Name *", className="fw-bold"),
                        dbc.Input(
                            id="usp-set-name-input",
                            placeholder="Enter descriptive set name...",
                            required=True
                        )
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Project ID *", className="fw-bold"),
                        dbc.Input(
                            id="usp-set-project-input",
                            placeholder="Enter project ID...",
                            required=True
                        )
                    ], md=6)
                ], className="mb-3"),

                # Row 2: Reactor Type and Experiment Number
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Reactor Type *", className="fw-bold"),
                        dbc.Select(
                            id="usp-set-reactor-type-input",
                            options=[
                                {"label": "Bioreactor", "value": "Bioreactor"},
                                {"label": "Shake Flask", "value": "Shake Flask"},
                                {"label": "Ambr250", "value": "Ambr250"},
                                {"label": "Ambr15", "value": "Ambr15"},
                                {"label": "Fed-batch", "value": "Fed-batch"},
                                {"label": "Perfusion", "value": "Perfusion"},
                                {"label": "Other", "value": "Other"}
                            ],
                            placeholder="Select reactor type...",
                            required=True
                        )
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Experiment Number", className="fw-bold"),
                        dbc.Input(
                            id="usp-set-experiment-input",
                            type="number",
                            placeholder="Enter experiment #..."
                        )
                    ], md=6)
                ], className="mb-3"),

                # Row 3: Cell Line
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Cell Line", className="fw-bold"),
                        dbc.Input(
                            id="usp-set-cell-line-input",
                            placeholder="Enter cell line..."
                        )
                    ], md=12)
                ], className="mb-3"),

                # Instructions
                dbc.Alert([
                    html.I(className="fas fa-info-circle me-2"),
                    "After creating the sample set, you can add samples to it from the sample management pages."
                ], color="info")
            ]),

            # Status messages
            html.Div(id="usp-set-creation-status", className="mt-3")
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="usp-close-create-modal", color="secondary"),
            dbc.Button([
                html.I(className="fas fa-plus me-2"),
                "Create Sample Set"
            ], id="usp-submit-create-set", color="primary")
        ])
    ], id="usp-create-set-modal", size="lg", scrollable=True)


print("✅ USP Sample Sets Layout loaded successfully")