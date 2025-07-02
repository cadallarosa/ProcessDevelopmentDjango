from dash import html
import dash_bootstrap_components as dbc
from ...shared.styles.common_styles import CARD_STYLE


def create_akta_dashboard_layout():
    """Create AKTA analysis dashboard overview"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("AKTA Analysis Dashboard"),
                html.P("Chromatography purification analysis overview", className="text-muted")
            ], md=8),
            dbc.Col([
                dbc.Button([
                    html.I(className="fas fa-plus me-1"),
                    "New Analysis"
                ], href="#!/analysis/akta/report", color="warning", size="sm", className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Quick stats
        dbc.Row([
            dbc.Col([
                create_akta_stats_card("Total Requests", "15", "fa-clipboard-list", "warning")
            ], md=3),
            dbc.Col([
                create_akta_stats_card("Completed", "12", "fa-check-circle", "success")
            ], md=3),
            dbc.Col([
                create_akta_stats_card("In Progress", "2", "fa-clock", "info")
            ], md=3),
            dbc.Col([
                create_akta_stats_card("Pending", "1", "fa-hourglass-half", "secondary")
            ], md=3)
        ], className="mb-4"),

        # Recent analysis requests table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Recent AKTA Analysis Requests"),
                    dbc.CardBody([
                        html.P("AKTA analysis requests table will go here")
                    ])
                ])
            ])
        ])

    ], fluid=True, style={"padding": "20px"})


def create_akta_sample_sets_layout():
    """Create AKTA sample sets specific view"""
    return dbc.Container([
        html.H2("AKTA Sample Sets"),
        html.P("Sample sets available for AKTA analysis"),
        # Sample sets specific to AKTA analysis
    ], fluid=True, style={"padding": "20px"})


def create_akta_reports_layout():
    """Create AKTA reports view"""
    return dbc.Container([
        html.H2("AKTA Reports"),
        html.P("Generated AKTA analysis reports"),
        # AKTA reports listing
    ], fluid=True, style={"padding": "20px"})


def create_akta_stats_card(title, value, icon, color):
    """Create AKTA statistics card"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.H4(value, className=f"text-{color} mb-0"),
                    html.P(title, className="text-muted mb-0 small")
                ], className="flex-grow-1"),
                html.Div([
                    html.I(className=f"fas {icon} fa-2x text-{color}")
                ], className="align-self-center")
            ], className="d-flex")
        ])
    ], className="shadow-sm h-100")