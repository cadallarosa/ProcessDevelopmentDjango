from django_plotly_dash import DjangoDash
from dash import html
import dash_bootstrap_components as dbc

app = DjangoDash("HomeDashboardApp",
                 external_stylesheets=[dbc.themes.BOOTSTRAP],
                 suppress_callback_exceptions=True)

app.layout = html.Div([
    dbc.Container([
        html.H1("PD Dashboard Home", className="mt-4 mb-4"),
        html.P("Welcome to the Process Development Dashboard"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("CLD", className="card-title"),
                        html.P("Cell Line Development"),
                    ])
                ], className="mb-3")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("USP", className="card-title"),
                        html.P("Upstream Processing"),
                    ])
                ], className="mb-3")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("DSP", className="card-title"),
                        html.P("Downstream Processing"),
                    ])
                ], className="mb-3")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Analytical", className="card-title"),
                        html.P("Analytical Methods"),
                    ])
                ], className="mb-3")
            ], width=3),
        ])
    ], fluid=True)
], style={"backgroundColor": "#f8f9fa", "minHeight": "100vh"})