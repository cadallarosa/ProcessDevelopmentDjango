"""
Layout components for the formulation stability analysis app
"""

import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Color palette and styling
COLOR_PALETTE = {
    "primary": "#2E86C1",
    "secondary": "#E74C3C", 
    "success": "#27AE60",
    "warning": "#F39C12",
    "info": "#8E44AD",
    "light": "#F8F9FA",
    "dark": "#2C3E50",
    "accent": "#3498DB",
    "background": "#FFFFFF",
    "muted": "#6C757D",
}

MODERN_STYLE = {
    "font_family": "'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif",
    "card_shadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
    "border_radius": "8px",
    "spacing": "16px"
}

def create_stability_trends_layout():
    """Create the stability trends visualization layout"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-chart-line me-2"),
                            "Stability Over Time"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Parameter to Plot:"),
                                dbc.RadioItems(
                                    id="parameter-selector",
                                    options=[
                                        {"label": "Main Peak (%)", "value": "main"},
                                        {"label": "HMW Aggregates (%)", "value": "hmw"},
                                        {"label": "LMW Fragments (%)", "value": "lmw"},
                                        {"label": "Melting Temperature (°C)", "value": "tm"},
                                        {"label": "Scattering Onset (°C)", "value": "scattering"}
                                    ],
                                    value="main",
                                    inline=True
                                )
                            ], width=8),
                            dbc.Col([
                                dbc.Label("Show Trend Lines:"),
                                dbc.Switch(
                                    id="show-trendlines",
                                    value=True,
                                    label="Linear Fit"
                                )
                            ], width=4)
                        ], className="mb-3"),
                        dcc.Graph(
                            id="stability-trends-plot",
                            style={"height": "500px"},
                            config={'displayModeBar': True, 'displaylogo': False}
                        )
                    ])
                ], style={"boxShadow": MODERN_STYLE["card_shadow"]})
            ], width=12)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-table me-2"),
                            "Degradation Rate Summary"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div(id="degradation-rates-table")
                    ])
                ], style={"boxShadow": MODERN_STYLE["card_shadow"]})
            ], width=12)
        ])
    ], fluid=True)

def create_formulation_details_layout():
    """Create the formulation details layout"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-info-circle me-2"),
                            "Formulation Composition"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div(id="formulation-composition-table")
                    ])
                ], style={"boxShadow": MODERN_STYLE["card_shadow"]})
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-thermometer-half me-2"),
                            "Physical Properties"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div(id="physical-properties-chart")
                    ])
                ], style={"boxShadow": MODERN_STYLE["card_shadow"]})
            ], width=6)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-flask me-2"),
                            "Sample Timeline"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(
                            id="sample-timeline-plot",
                            style={"height": "400px"},
                            config={'displayModeBar': True, 'displaylogo': False}
                        )
                    ])
                ], style={"boxShadow": MODERN_STYLE["card_shadow"]})
            ], width=12)
        ])
    ], fluid=True)

def create_statistical_summary_layout():
    """Create the statistical summary layout"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-chart-bar me-2"),
                            "Stability Ranking"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Ranking Criteria:"),
                                dbc.RadioItems(
                                    id="ranking-criteria",
                                    options=[
                                        {"label": "Overall Stability Score", "value": "stability_score"},
                                        {"label": "Main Peak Retention", "value": "main_retention"},
                                        {"label": "HMW Formation Rate", "value": "hmw_formation"},
                                        {"label": "Temperature Stability", "value": "temperature"}
                                    ],
                                    value="stability_score",
                                    inline=True
                                )
                            ], width=12)
                        ], className="mb-3"),
                        dcc.Graph(
                            id="stability-ranking-plot",
                            style={"height": "400px"},
                            config={'displayModeBar': True, 'displaylogo': False}
                        )
                    ])
                ], style={"boxShadow": MODERN_STYLE["card_shadow"]})
            ], width=8),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-trophy me-2"),
                            "Top Performers"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div(id="top-performers-list")
                    ])
                ], style={"boxShadow": MODERN_STYLE["card_shadow"]})
            ], width=4)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-calculator me-2"),
                            "Statistical Analysis"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div(id="statistical-analysis-table")
                    ])
                ], style={"boxShadow": MODERN_STYLE["card_shadow"]})
            ], width=12)
        ])
    ], fluid=True)

def create_comparison_heatmap():
    """Create a comparison heatmap for formulation performance"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-th me-2"),
                "Formulation Performance Heatmap"
            ], className="mb-0")
        ]),
        dbc.CardBody([
            dcc.Graph(
                id="performance-heatmap",
                style={"height": "400px"},
                config={'displayModeBar': True, 'displaylogo': False}
            )
        ])
    ], style={"boxShadow": MODERN_STYLE["card_shadow"]})

def create_export_controls():
    """Create export controls for data and reports"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-download me-2"),
                "Export Data"
            ], className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-file-excel me-2"), "Export to Excel"],
                        id="export-excel-btn",
                        color="success",
                        outline=True,
                        className="me-2"
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-file-csv me-2"), "Export to CSV"],
                        id="export-csv-btn",
                        color="primary",
                        outline=True,
                        className="me-2"
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-file-pdf me-2"), "Generate Report"],
                        id="generate-report-btn",
                        color="secondary",
                        outline=True
                    )
                ], width=12)
            ]),
            dcc.Download(id="download-excel"),
            dcc.Download(id="download-csv"),
            dcc.Download(id="download-report")
        ])
    ], className="mt-4", style={"boxShadow": MODERN_STYLE["card_shadow"]})

def create_error_message(error_text):
    """Create an error message component"""
    return dbc.Alert([
        html.I(className="fas fa-exclamation-triangle me-2"),
        html.Strong("Error: "),
        error_text
    ], color="danger", className="mt-3")

def create_loading_spinner(loading_text="Loading data..."):
    """Create a loading spinner component"""
    return dbc.Spinner([
        html.Div([
            html.P(loading_text, className="text-center text-muted"),
        ])
    ], size="lg", color="primary", type="border")

def create_empty_state(message="No data available", icon="fas fa-chart-line"):
    """Create an empty state component"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"{icon} fa-3x mb-3", style={"color": COLOR_PALETTE["muted"]}),
                html.H4(message, className="text-muted"),
                html.P("Select formulations and storage conditions to view analysis.", 
                      className="text-muted")
            ], className="text-center py-5")
        ])
    ], style={"boxShadow": MODERN_STYLE["card_shadow"]})

def create_data_quality_indicator(quality_score):
    """Create a data quality indicator"""
    if quality_score >= 0.8:
        color = COLOR_PALETTE["success"]
        icon = "fas fa-check-circle"
        label = "High Quality"
    elif quality_score >= 0.6:
        color = COLOR_PALETTE["warning"] 
        icon = "fas fa-exclamation-circle"
        label = "Medium Quality"
    else:
        color = COLOR_PALETTE["secondary"]
        icon = "fas fa-times-circle"
        label = "Low Quality"
    
    return dbc.Badge([
        html.I(className=f"{icon} me-1"),
        f"Data Quality: {label} ({quality_score:.1%})"
    ], color=color, className="me-2")

def create_stability_scorecard(stability_metrics):
    """Create a stability scorecard showing key metrics"""
    cards = []
    
    metrics = [
        {"title": "Stability Score", "value": stability_metrics.get("stability_score", "N/A"), 
         "icon": "fas fa-star", "color": COLOR_PALETTE["primary"]},
        {"title": "Half Life", "value": f"{stability_metrics.get('half_life_months', 'N/A')} months", 
         "icon": "fas fa-clock", "color": COLOR_PALETTE["info"]},
        {"title": "Main Peak Loss", "value": f"{stability_metrics.get('main_degradation_rate', 'N/A')}%/month", 
         "icon": "fas fa-arrow-down", "color": COLOR_PALETTE["secondary"]},
        {"title": "HMW Formation", "value": f"{stability_metrics.get('hmw_increase_rate', 'N/A')}%/month", 
         "icon": "fas fa-arrow-up", "color": COLOR_PALETTE["warning"]}
    ]
    
    for metric in metrics:
        card = dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className=f"{metric['icon']} fa-2x", 
                              style={"color": metric["color"]}),
                        html.H3(metric["value"], className="mt-2 mb-0"),
                        html.P(metric["title"], className="text-muted small mb-0")
                    ], className="text-center")
                ])
            ], style={"boxShadow": MODERN_STYLE["card_shadow"]})
        ], width=3)
        cards.append(card)
    
    return dbc.Row(cards, className="mb-4")