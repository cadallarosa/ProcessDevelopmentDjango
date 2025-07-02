# Simplified dashboard_home.py - Working version
from dash import html, Input, Output, callback, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from ..shared.styles.common_styles import CARD_STYLE, COLORS
from ..config.analysis_types import ANALYSIS_TYPES, STATUS_COLORS


def create_dashboard_layout():
    """Create the main dashboard overview layout - simplified working version"""
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("CLD Dashboard", className="display-4"),
                html.P("Cell Line Development Sample Management & Analysis",
                       className="lead text-muted")
            ])
        ], className="mb-4"),

        # Stats Cards
        dbc.Row([
            dbc.Col([
                create_stats_card("Total Samples", "1,247", "↑ 12% this month", "primary", "fa-vial")
            ], md=3),
            dbc.Col([
                create_stats_card("Sample Sets", "89", "Active groups", "success", "fa-layer-group")
            ], md=3),
            dbc.Col([
                create_stats_card("SEC Analysis", "23", "Pending requests", "warning", "fa-microscope")
            ], md=3),
            dbc.Col([
                create_stats_card("Reports", "156", "Generated this month", "info", "fa-chart-line")
            ], md=3)
        ], className="mb-4"),

        # Main Content Row
        dbc.Row([
            # Left Column - Recent Activity
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Recent Activity", className="mb-0"),
                        dbc.Button("View All", color="outline-primary", size="sm", className="float-end")
                    ]),
                    dbc.CardBody([
                        create_activity_list()
                    ])
                ], style=CARD_STYLE)
            ], md=6),

            # Right Column - Quick Actions
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Quick Actions", className="mb-0")
                    ]),
                    dbc.CardBody([
                        create_quick_actions()
                    ])
                ], style=CARD_STYLE)
            ], md=6)
        ], className="mb-4"),

        # Analysis Status Overview
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Analysis Status Overview", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div(id="analysis-status-chart")
                    ])
                ], style=CARD_STYLE)
            ])
        ])

    ], fluid=True, style={"padding": "20px"})


def create_stats_card(title, value, subtitle, color, icon):
    """Create a statistics card"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.H3(str(value), className=f"text-{color} mb-0"),
                    html.P(title, className="text-muted mb-0"),
                    html.Small(subtitle, className="text-muted")
                ], className="flex-grow-1"),
                html.Div([
                    html.I(className=f"fas {icon} fa-2x text-{color}")
                ], className="align-self-center")
            ], className="d-flex")
        ])
    ], className="shadow-sm h-100")


def create_activity_list():
    """Create recent activity list"""
    activities = [
        {"time": "2 hours ago", "action": "SEC analysis completed", "item": "Sample Set PRJ123_SIP001",
         "icon": "fa-check-circle", "color": "success"},
        {"time": "4 hours ago", "action": "New sample set created", "item": "PRJ456_SIP002_DEV",
         "icon": "fa-plus-circle", "color": "primary"},
        {"time": "6 hours ago", "action": "Analysis requested", "item": "SEC for FB001-FB020", "icon": "fa-clock",
         "color": "warning"},
        {"time": "1 day ago", "action": "Report generated", "item": "Weekly Summary Report", "icon": "fa-file-alt",
         "color": "info"},
        {"time": "2 days ago", "action": "Data imported", "item": "50 new samples", "icon": "fa-upload",
         "color": "secondary"}
    ]

    activity_items = []
    for activity in activities:
        activity_items.append(
            html.Div([
                html.Div([
                    html.I(className=f"fas {activity['icon']} text-{activity['color']} me-2"),
                    html.Strong(activity['action']),
                    html.Br(),
                    html.Small(activity['item'], className="text-muted")
                ], className="flex-grow-1"),
                html.Small(activity['time'], className="text-muted")
            ], className="d-flex mb-3")
        )

    return html.Div(activity_items)


def create_quick_actions():
    """Create quick action buttons"""
    actions = [
        {"title": "View Sample Sets", "desc": "Browse grouped samples", "href": "#!/sample-sets",
         "icon": "fa-layer-group", "color": "primary"},
        {"title": "Create Samples", "desc": "Add new samples", "href": "#!/samples/create", "icon": "fa-plus",
         "color": "success"},
        {"title": "SEC Analysis", "desc": "Size exclusion chromatography", "href": "#!/analysis/sec",
         "icon": "fa-microscope", "color": "info"},
        {"title": "Settings", "desc": "Configure dashboard", "href": "#!/settings", "icon": "fa-cogs",
         "color": "secondary"}
    ]

    action_buttons = []
    for action in actions:
        action_buttons.append(
            html.A([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className=f"fas {action['icon']} fa-2x text-{action['color']} mb-2"),
                            html.H6(action['title'], className="mb-1"),
                            html.P(action['desc'], className="text-muted small mb-0")
                        ], className="text-center")
                    ], className="p-3")
                ], className="shadow-sm")
            ],
                href=action['href'],
                className="text-decoration-none mb-3",
                style={"cursor": "pointer"})
        )

    return html.Div(action_buttons)


def create_settings_layout():
    """Create settings page layout"""
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
                ])
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
                                dbc.Label("Default Analysis Type"),
                                dbc.Select(
                                    id="default-analysis-type",
                                    options=[
                                        {"label": config["name"], "value": key}
                                        for key, config in ANALYSIS_TYPES.items()
                                    ],
                                    value="SEC"
                                )
                            ], md=12)
                        ], className="mb-3"),

                        dbc.Checklist(
                            options=[
                                {"label": "Auto-open reports in new tab", "value": "auto_open"},
                                {"label": "Show embedding controls", "value": "show_controls"},
                                {"label": "Enable analysis notifications", "value": "notifications"}
                            ],
                            value=["show_controls"],
                            id="analysis-settings-checklist"
                        ),

                        html.Hr(),
                        dbc.Button("Test SEC Connection", color="outline-info", size="sm"),
                        dbc.Button("Refresh Data", color="outline-secondary", size="sm", className="ms-2")
                    ])
                ])
            ], md=6)
        ], className="mb-4"),

        # Application Info
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Application Information", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Dl([
                            html.Dt("Version"),
                            html.Dd("3.0.0-simplified"),
                            html.Dt("Last Updated"),
                            html.Dd("January 2025"),
                            html.Dt("Features"),
                            html.Dd("Enhanced SEC Integration, Sample Set Management, Analysis Request Tracking"),
                            html.Dt("SEC App Location"),
                            html.Dd("plotly_integration/process_development/downstream_processing/empower/sec_report_app/"),
                            html.Dt("Dashboard Location"),
                            html.Dd("plotly_integration/cld_dashboard/")
                        ])
                    ])
                ])
            ], md=12)
        ])

    ], style={"padding": "20px"})


# # Simple callback for updating analysis status chart
# @callback(
#     Output("analysis-status-chart", "children"),
#     Input("analysis-status-chart", "id")  # Dummy input
# )
# def update_analysis_status_chart(_):
#     """Update the analysis status overview chart"""
#     # Mock data - replace with actual database queries
#     status_data = {
#         'Status': ['Requested', 'Data Available', 'Report Created', 'Completed'],
#         'Count': [8, 5, 12, 31],
#         'Color': [STATUS_COLORS['REQUESTED'], STATUS_COLORS['DATA_AVAILABLE'],
#                   STATUS_COLORS['REPORT_CREATED'], STATUS_COLORS['COMPLETED']]
#     }
#
#     fig = px.bar(
#         x=status_data['Count'],
#         y=status_data['Status'],
#         orientation='h',
#         title="Analysis Requests by Status",
#         color=status_data['Status'],
#         color_discrete_map={
#             'Requested': '#ffc107',
#             'Data Available': '#17a2b8',
#             'Report Created': '#28a745',
#             'Completed': '#28a745'
#         }
#     )
#
#     fig.update_layout(
#         showlegend=False,
#         height=300,
#         margin=dict(l=20, r=20, t=40, b=20)
#     )
#
#     return dcc.Graph(figure=fig)