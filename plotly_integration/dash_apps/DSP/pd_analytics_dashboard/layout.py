"""Main layout for PD Analytics Dashboard."""
import dash_bootstrap_components as dbc
from dash import html, dcc
from .components.tables import create_analytics_table


def create_layout():
    """Create the analytics dashboard layout."""
    return html.Div([
        # Main Content
        html.Div([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H3([
                        html.I(className="bi bi-graph-up me-2"),
                        "PD Analytics Dashboard"
                    ], className="mb-0")
                ], width="auto"),
            ], className="mb-4"),

            # Filters Card
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Project Filter", className="fw-bold"),
                            dcc.Dropdown(
                                id="analytics-filter-project",
                                placeholder="All projects...",
                                clearable=True,
                                style={"minWidth": "200px"}
                            )
                        ], md=3),
                        dbc.Col([
                            dbc.Label("Assay Type", className="fw-bold"),
                            dcc.Dropdown(
                                id="analytics-filter-assay",
                                options=[
                                    {"label": "All", "value": "all"},
                                    {"label": "SEC Only", "value": "sec"},
                                    {"label": "Titer Only", "value": "titer"},
                                    {"label": "Mass Check Only", "value": "mass"},
                                    {"label": "Complete Profile", "value": "complete"},
                                ],
                                value="all",
                                clearable=False,
                                style={"minWidth": "180px"}
                            )
                        ], md=2),
                        dbc.Col([
                            dbc.Label("QC Filter", className="fw-bold"),
                            dcc.Dropdown(
                                id="analytics-filter-qc",
                                options=[
                                    {"label": "All", "value": "all"},
                                    {"label": "QC Pass Only", "value": "pass"},
                                    {"label": "QC Fail Only", "value": "fail"},
                                ],
                                value="all",
                                clearable=False,
                                style={"minWidth": "150px"}
                            )
                        ], md=2),
                        dbc.Col([
                            dbc.Label("Search", className="fw-bold"),
                            dbc.Input(
                                id="analytics-filter-search",
                                type="text",
                                placeholder="Search PD#, Project...",
                                debounce=True
                            )
                        ], md=3),
                        dbc.Col([
                            dbc.Label(html.Span([html.I(className="bi bi-blank")]), style={"visibility": "hidden"}),
                            html.Div([
                                dbc.Button(
                                    [html.I(className="bi bi-arrow-clockwise me-2"), "Refresh"],
                                    id="analytics-refresh-btn",
                                    color="primary",
                                    size="sm"
                                ),
                            ])
                        ], md=2, className="d-flex align-items-end"),
                    ], align="end")
                ])
            ], className="mb-3 shadow-sm"),

            # Info Card
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.I(className="bi bi-info-circle me-2 text-primary"),
                                html.Span("This dashboard shows all PD samples with joined analytical results. Export to Excel for detailed analysis.", className="text-muted")
                            ])
                        ])
                    ])
                ])
            ], className="mb-3", color="light"),

            # Table Card
            dbc.Card([
                dbc.CardBody([
                    html.Div(id="analytics-stats", className="mb-3"),
                    create_analytics_table(),
                ])
            ], className="shadow-sm"),
        ], style={"padding": "20px", "backgroundColor": "#f8f9fa", "minHeight": "100vh"})
    ])
