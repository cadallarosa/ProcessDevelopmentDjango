# plotly_integration/pd_dashboard/core/settings_content.py
from dash import html
import dash_bootstrap_components as dbc
from ..shared.styles.common_styles import CARD_STYLE


def create_settings_content():
    """Create the settings page content (without sidebar)"""
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2("Dashboard Settings"),
                html.P("Configure your dashboard preferences and integrations", className="text-muted")
            ])
        ], className="mb-4"),

        # Settings Sections
        dbc.Row([
            # General Settings
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("General Settings", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.P("Configure general dashboard behavior and appearance."),

                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Default Page Size"),
                                dbc.Select(
                                    id="default-page-size",
                                    options=[
                                        {"label": "25 rows", "value": 25},
                                        {"label": "50 rows", "value": 50},
                                        {"label": "100 rows", "value": 100}
                                    ],
                                    value=25
                                )
                            ], md=6),
                            dbc.Col([
                                dbc.Label("Theme"),
                                dbc.Select(
                                    id="theme-select",
                                    options=[
                                        {"label": "Light", "value": "light"},
                                        {"label": "Dark", "value": "dark"}
                                    ],
                                    value="light"
                                )
                            ], md=6)
                        ], className="mb-3"),

                        dbc.Checklist(
                            options=[
                                {"label": "Show breadcrumb navigation", "value": "breadcrumbs"},
                                {"label": "Auto-refresh data", "value": "auto_refresh"},
                                {"label": "Show detailed tooltips", "value": "tooltips"}
                            ],
                            value=["breadcrumbs", "tooltips"],
                            id="general-settings-checklist"
                        ),

                        html.Hr(),
                        dbc.Button("Save Settings", color="primary", size="sm"),
                        dbc.Button("Reset to Defaults", color="outline-warning", size="sm", className="ms-2")
                    ])
                ], style=CARD_STYLE)
            ], md=6),

            # Analysis Settings
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Analysis Integration", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.P("Configure analysis tool integrations and default parameters."),

                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Default SEC Parameters"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("Flow Rate"),
                                    dbc.Input(placeholder="0.5 mL/min", value="0.5")
                                ], className="mb-2"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("Detection"),
                                    dbc.Select(
                                        options=[
                                            {"label": "UV 280nm", "value": "uv280"},
                                            {"label": "UV 214nm", "value": "uv214"},
                                            {"label": "Multi-wavelength", "value": "multi"}
                                        ],
                                        value="uv280"
                                    )
                                ])
                            ], md=12)
                        ], className="mb-3"),

                        dbc.Row([
                            dbc.Col([
                                dbc.Label("AKTA Integration"),
                                dbc.Switch(
                                    id="akta-auto-import",
                                    label="Auto-import AKTA results",
                                    value=True
                                ),
                                dbc.Switch(
                                    id="akta-notifications",
                                    label="Enable run notifications",
                                    value=False
                                )
                            ], md=12)
                        ], className="mb-3"),

                        html.Hr(),
                        dbc.Button("Test Connections", color="info", size="sm"),
                        dbc.Button("Reset Analysis Settings", color="outline-secondary", size="sm", className="ms-2")
                    ])
                ], style=CARD_STYLE)
            ], md=6)
        ], className="mb-4"),

        # System Integration Status
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("System Integration Status", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-circle text-success me-2"),
                                "CLD Database Connection",
                                html.Span("Connected", className="badge bg-success ms-2")
                            ], className="d-flex justify-content-between align-items-center mb-2"),

                            html.Div([
                                html.I(className="fas fa-circle text-success me-2"),
                                "AKTA Chromatography System",
                                html.Span("Online", className="badge bg-success ms-2")
                            ], className="d-flex justify-content-between align-items-center mb-2"),

                            html.Div([
                                html.I(className="fas fa-circle text-warning me-2"),
                                "Nova Flex Cell Counter",
                                html.Span("Maintenance Mode", className="badge bg-warning ms-2")
                            ], className="d-flex justify-content-between align-items-center mb-2"),

                            html.Div([
                                html.I(className="fas fa-circle text-success me-2"),
                                "Vicell System",
                                html.Span("Connected", className="badge bg-success ms-2")
                            ], className="d-flex justify-content-between align-items-center mb-2"),

                            html.Div([
                                html.I(className="fas fa-circle text-danger me-2"),
                                "Mass Spectrometry",
                                html.Span("Offline", className="badge bg-danger ms-2")
                            ], className="d-flex justify-content-between align-items-center mb-3"),
                        ])
                    ])
                ], style=CARD_STYLE)
            ], md=12)
        ])

    ], fluid=True)