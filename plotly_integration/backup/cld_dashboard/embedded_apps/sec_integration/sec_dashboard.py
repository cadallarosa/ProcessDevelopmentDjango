# cld_dashboard/embedded_apps/sec_integration/sec_dashboard.py
from dash import html
import dash_bootstrap_components as dbc
from ...shared.styles.common_styles import CARD_STYLE


def create_sec_dashboard_layout():
    """Create SEC analysis dashboard overview"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("SEC Analysis Dashboard"),
                html.P("Size Exclusion Chromatography analysis overview", className="text-muted")
            ], md=8),
            dbc.Col([
                dbc.Button([
                    html.I(className="fas fa-plus me-1"),
                    "New Analysis"
                ], href="/analysis/sec/report", color="primary", size="sm", className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Quick stats
        dbc.Row([
            dbc.Col([
                create_sec_stats_card("Total Requests", "23", "fa-clipboard-list", "primary")
            ], md=3),
            dbc.Col([
                create_sec_stats_card("Completed", "18", "fa-check-circle", "success")
            ], md=3),
            dbc.Col([
                create_sec_stats_card("In Progress", "3", "fa-clock", "warning")
            ], md=3),
            dbc.Col([
                create_sec_stats_card("Pending", "2", "fa-hourglass-half", "info")
            ], md=3)
        ], className="mb-4"),

        # Recent analysis requests table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Recent SEC Analysis Requests"),
                    dbc.CardBody([
                        html.P("Analysis requests table will go here")
                    ])
                ])
            ])
        ])

    ], fluid=True, style={"padding": "20px"})


def create_sec_sample_sets_layout():
    """Create SEC sample sets specific view"""
    return dbc.Container([
        html.H2("SEC Sample Sets"),
        html.P("Sample sets available for SEC analysis"),
        # Sample sets specific to SEC analysis
    ], fluid=True, style={"padding": "20px"})


def create_sec_reports_layout():
    """Create SEC reports view"""
    return dbc.Container([
        html.H2("SEC Reports"),
        html.P("Generated SEC analysis reports"),
        # SEC reports listing
    ], fluid=True, style={"padding": "20px"})


def create_sec_stats_card(title, value, icon, color):
    """Create SEC statistics card"""
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