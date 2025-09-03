import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta


def create_usp_view_samples_layout():
    """Create the USP view samples layout"""
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-eye text-info me-2"),
                    "View USP Samples"
                ]),
                html.P("Browse and manage existing upstream process samples",
                       className="text-muted")
            ], md=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-plus me-1"),
                        "Create Samples"
                    ], href="#!/usp/samples/create", color="success", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-layer-group me-1"),
                        "Sample Sets"
                    ], href="#!/usp/sample-sets", color="outline-info", size="sm")
                ], className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Quick stats
        dbc.Row([
            dbc.Col([
                create_metric_card("Total Samples", "usp-total-samples-count", "fa-flask", "primary")
            ], md=3),
            dbc.Col([
                create_metric_card("Filtered Results", "usp-filtered-samples-count", "fa-filter", "info")
            ], md=3),
            dbc.Col([
                create_metric_card("Active Projects", "usp-active-projects-count", "fa-project-diagram", "success")
            ], md=3),
            dbc.Col([
                create_metric_card("Recent Samples", "usp-recent-samples-count", "fa-clock", "warning")
            ], md=3)
        ], className="mb-4"),

        # Filters
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Filters & Search", className="mb-0")
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            # Project filter
                            dbc.Col([
                                html.Label("Project:", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="usp-project-filter",
                                    options=[{"label": "All Projects", "value": "all"}],
                                    value="all",
                                    clearable=False,
                                    placeholder="Select project..."
                                )
                            ], md=2),
                            
                            # Cell line filter
                            dbc.Col([
                                html.Label("Cell Line:", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="usp-cell-line-filter",
                                    options=[{"label": "All Cell Lines", "value": "all"}],
                                    value="all",
                                    clearable=False,
                                    placeholder="Select cell line..."
                                )
                            ], md=2),
                            
                            # Vessel type filter
                            dbc.Col([
                                html.Label("Vessel Type:", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="usp-vessel-type-filter",
                                    options=[{"label": "All Vessel Types", "value": "all"}],
                                    value="all",
                                    clearable=False,
                                    placeholder="Select vessel..."
                                )
                            ], md=2),
                            
                            # Development stage filter
                            dbc.Col([
                                html.Label("Dev Stage:", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="usp-development-stage-filter",
                                    options=[{"label": "All Stages", "value": "all"}],
                                    value="all",
                                    clearable=False,
                                    placeholder="Select stage..."
                                )
                            ], md=2),
                            
                            # Date range
                            dbc.Col([
                                html.Label("Date Range:", className="fw-bold small"),
                                dcc.DatePickerRange(
                                    id="usp-date-range-filter",
                                    start_date=(datetime.now() - timedelta(days=90)).date(),
                                    end_date=datetime.now().date(),
                                    display_format="YYYY-MM-DD",
                                    style={"width": "100%"}
                                )
                            ], md=2),
                            
                            # Search and actions
                            dbc.Col([
                                html.Label("Search:", className="fw-bold small"),
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="usp-search-input",
                                        placeholder="Search samples...",
                                        type="text"
                                    ),
                                    dbc.Button([
                                        html.I(className="fas fa-search")
                                    ], id="usp-apply-filters-btn", color="primary", outline=True)
                                ])
                            ], md=2)
                        ])
                    ])
                ], className="shadow-sm")
            ])
        ], className="mb-4"),

        # Action buttons
        dbc.Row([
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-sync-alt me-1"),
                        "Refresh"
                    ], id="usp-refresh-samples-btn", color="outline-secondary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-download me-1"),
                        "Export CSV"
                    ], id="usp-export-samples-btn", color="outline-success", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-layer-group me-1"),
                        "Create Sample Set"
                    ], id="usp-create-set-btn", color="outline-warning", size="sm")
                ])
            ])
        ], className="mb-3"),

        # Samples table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("USP Samples", className="mb-0")
                    ]),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id="usp-samples-table",
                            columns=[],
                            data=[],
                            sort_action="native",
                            filter_action="native",
                            page_action="native",
                            page_current=0,
                            page_size=20,
                            row_selectable="multi",
                            selected_rows=[],
                            style_table={"overflowX": "auto"},
                            style_cell={
                                "textAlign": "left",
                                "padding": "8px",
                                "fontSize": "14px",
                                "fontFamily": "system-ui",
                                "whiteSpace": "normal",
                                "height": "auto",
                                "minWidth": "80px"
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
                    ])
                ], className="shadow-sm")
            ])
        ]),

        # Download component for export
        dcc.Download(id="usp-export-data"),

        # Modals and stores (for future functionality)
        html.Div(id="usp-view-samples-modals"),
        dcc.Store(id="usp-selected-samples-store"),
        dcc.Store(id="usp-sample-edit-store")

    ], fluid=True, style={"padding": "20px"})


def create_metric_card(title, metric_id, icon, color):
    """Create a metric display card"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.H4("0", id=metric_id, className=f"text-{color} mb-0"),
                    html.P(title, className="text-muted mb-0 small")
                ], className="flex-grow-1"),
                html.Div([
                    html.I(className=f"fas {icon} fa-2x text-{color} opacity-75")
                ], className="align-self-center")
            ], className="d-flex")
        ])
    ], className="shadow-sm h-100")


print("✅ USP View Samples Layout loaded successfully")