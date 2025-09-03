# USP sample_sets layout - Grouped by Project ID and Reactor Type
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc


def create_sample_sets_main_layout():
    """Create main USP sample sets layout grouped by project and reactor type"""
    return dbc.Container([
        # Header with navigation
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-layer-group text-primary me-2"),
                    "USP Sample Sets"
                ]),
                html.P("Manage upstream process samples grouped by project and reactor type", 
                       className="text-muted")
            ], md=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-plus me-1"),
                        "Create Samples"
                    ], href="#!/usp/samples/create", color="primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-eye me-1"),
                        "View All Samples"
                    ], href="#!/usp/samples/view", color="outline-primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-sync-alt me-1"),
                        "Refresh"
                    ], id="usp-refresh-sample-sets-btn", color="outline-secondary", size="sm")
                ], className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Quick stats
        dbc.Row([
            dbc.Col([
                create_metric_card("Total Projects", "usp-total-projects-metric", "fa-project-diagram", "primary")
            ], md=3),
            dbc.Col([
                create_metric_card("Total Sample Sets", "usp-total-sets-metric", "fa-layer-group", "info")
            ], md=3),
            dbc.Col([
                create_metric_card("Total Samples", "usp-total-samples-metric", "fa-vials", "success")
            ], md=3),
            dbc.Col([
                create_metric_card("Avg Samples/Set", "usp-avg-samples-metric", "fa-chart-bar", "warning")
            ], md=3)
        ], className="mb-4"),

        # Filters
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Filter by Project:", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="usp-project-set-filter",
                                    options=[
                                        {"label": "All Projects", "value": "all"}
                                    ],
                                    value="all",
                                    clearable=False
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("Filter by Reactor:", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="usp-reactor-set-filter",
                                    options=[
                                        {"label": "All Reactors", "value": "all"},
                                        {"label": "Bioreactor", "value": "bioreactor"},
                                        {"label": "Flask", "value": "flask"},
                                        {"label": "Wave", "value": "wave"},
                                        {"label": "AMBR", "value": "ambr"},
                                        {"label": "DasGip", "value": "dasgip"},
                                        {"label": "Other", "value": "other"}
                                    ],
                                    value="all",
                                    clearable=False
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("Search:", className="fw-bold small"),
                                dbc.Input(
                                    id="usp-search-input",
                                    placeholder="Search by project, clone, or sample...",
                                    type="text"
                                )
                            ], md=4),
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

        # Sample Sets Table - Grouped by Project and Reactor
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-table me-2"),
                            "USP Sample Sets (Grouped by Project & Reactor)"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id="usp-sample-sets-table",
                            columns=[
                                {"name": "Project ID", "id": "project_id"},
                                {"name": "Reactor Type", "id": "reactor_type"},
                                {"name": "Sample Count", "id": "sample_count", "type": "numeric"},
                                {"name": "Date Range", "id": "date_range"},
                                {"name": "Avg Titer (g/L)", "id": "avg_titer", "type": "numeric"},
                                {"name": "Avg VCD", "id": "avg_vcd", "type": "numeric"},
                                {"name": "Avg Viability (%)", "id": "avg_viability", "type": "numeric"},
                                {"name": "Clones", "id": "clones"},
                                {"name": "Created", "id": "created_date"},
                                {"name": "Actions", "id": "actions", "presentation": "markdown"}
                            ],
                            data=[],
                            sort_action="native",
                            filter_action="native",
                            page_action="native",
                            page_size=15,
                            style_cell={
                                'textAlign': 'left',
                                'padding': '10px',
                                'fontSize': '14px'
                            },
                            style_header={
                                'backgroundColor': '#1976d2',
                                'color': 'white',
                                'fontWeight': 'bold'
                            },
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': 'rgb(248, 248, 248)'
                                },
                                {
                                    'if': {'column_id': 'actions'},
                                    'textAlign': 'center'
                                },
                                # Highlight by reactor type
                                {
                                    'if': {
                                        'filter_query': '{reactor_type} = bioreactor',
                                        'column_id': 'reactor_type'
                                    },
                                    'backgroundColor': '#e3f2fd',
                                    'fontWeight': 'bold'
                                },
                                {
                                    'if': {
                                        'filter_query': '{reactor_type} = dasgip',
                                        'column_id': 'reactor_type'
                                    },
                                    'backgroundColor': '#f3e5f5',
                                    'fontWeight': 'bold'
                                }
                            ]
                        )
                    ], className="p-0")
                ], className="shadow-sm")
            ])
        ]),

        # Detail view container (for when a set is selected)
        html.Div(id="usp-sample-set-details-container", className="mt-4"),

        # Hidden stores
        dcc.Store(id="usp-selected-set-store", data={}),
        dcc.Store(id="usp-sample-sets-data-store", data={}),
        
        # No auto-refresh interval - manual refresh only

    ], fluid=True)


def create_metric_card(title, metric_id, icon, color):
    """Create a metric card component"""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.I(className=f"fas {icon} fa-2x text-{color}")
                ], width=3),
                dbc.Col([
                    html.H3(id=metric_id, className="mb-0"),
                    html.P(title, className="text-muted small mb-0")
                ], width=9)
            ])
        ])
    ], className="shadow-sm")


def create_sample_set_details_view(project_id, reactor_type):
    """Create detailed view for a specific sample set"""
    return dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.H5([
                        html.I(className="fas fa-flask me-2"),
                        f"Sample Set Details: {project_id} - {reactor_type}"
                    ], className="mb-0")
                ], md=8),
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-arrow-left me-1"),
                        "Back to Sets"
                    ], id="usp-back-to-sets-btn", color="outline-secondary", size="sm", 
                       className="float-end")
                ], md=4)
            ])
        ]),
        dbc.CardBody([
            # Summary statistics
            dbc.Row([
                dbc.Col([
                    html.H6("Project Information", className="text-muted mb-3"),
                    html.Div(id="usp-set-project-info")
                ], md=4),
                dbc.Col([
                    html.H6("Performance Metrics", className="text-muted mb-3"),
                    html.Div(id="usp-set-performance-metrics")
                ], md=4),
                dbc.Col([
                    html.H6("Culture Conditions", className="text-muted mb-3"),
                    html.Div(id="usp-set-culture-conditions")
                ], md=4)
            ], className="mb-4"),
            
            html.Hr(),
            
            # Samples table for this set
            html.H6("Samples in this Set", className="mb-3"),
            dash_table.DataTable(
                id="usp-set-samples-table",
                columns=[
                    {"name": "Sample #", "id": "sample_number"},
                    {"name": "Clone", "id": "cell_line"},
                    {"name": "Run Date", "id": "run_date"},
                    {"name": "Harvest Date", "id": "harvest_date"},
                    {"name": "Duration (days)", "id": "culture_duration", "type": "numeric"},
                    {"name": "Max VCD", "id": "max_vcd", "type": "numeric"},
                    {"name": "Viability (%)", "id": "viability", "type": "numeric"},
                    {"name": "Titer (g/L)", "id": "final_titer", "type": "numeric"},
                    {"name": "Volume (L)", "id": "culture_volume", "type": "numeric"},
                    {"name": "Feed Strategy", "id": "feed_strategy"},
                    {"name": "Note", "id": "note"}
                ],
                data=[],
                sort_action="native",
                page_size=10,
                style_cell={
                    'textAlign': 'left',
                    'padding': '8px',
                    'fontSize': '13px'
                },
                style_header={
                    'backgroundColor': '#f8f9fa',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ]
            ),
            
            # Action buttons
            dbc.Row([
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button([
                            html.I(className="fas fa-download me-1"),
                            "Export Set"
                        ], id="usp-export-set-btn", color="info", size="sm"),
                        dbc.Button([
                            html.I(className="fas fa-chart-line me-1"),
                            "Analyze Trends"
                        ], id="usp-analyze-set-btn", color="success", size="sm"),
                        dbc.Button([
                            html.I(className="fas fa-file-alt me-1"),
                            "Generate Report"
                        ], id="usp-report-set-btn", color="warning", size="sm")
                    ])
                ], className="mt-3")
            ])
        ])
    ], className="shadow-sm")