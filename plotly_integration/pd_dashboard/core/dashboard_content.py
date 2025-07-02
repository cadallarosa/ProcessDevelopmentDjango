# plotly_integration/pd_dashboard/core/dashboard_content.py
from dash import html
import dash_bootstrap_components as dbc
from ..shared.styles.common_styles import CARD_STYLE


def create_stats_card(title, value, subtitle, color, icon):
    """Create a statistics card"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.H3(value, className=f"text-{color} mb-1"),
                    html.H6(title, className="mb-1"),
                    html.Small(subtitle, className="text-muted")
                ], className="flex-grow-1"),
                html.Div([
                    html.I(className=f"fas {icon} fa-2x text-{color} opacity-75")
                ])
            ], className="d-flex align-items-center")
        ])
    ], style=CARD_STYLE)


def create_recent_activity():
    """Create recent activity feed"""
    activities = [
        {
            'time': '2 min ago',
            'action': 'SEC Analysis completed',
            'details': 'Sample Set CLD-001-MP',
            'icon': 'fa-microscope',
            'color': 'success'
        },
        {
            'time': '15 min ago',
            'action': 'New samples created',
            'details': '12 samples added to USP-024',
            'icon': 'fa-plus',
            'color': 'primary'
        },
        {
            'time': '1 hour ago',
            'action': 'AKTA run started',
            'details': 'DSP experiment DSP-156',
            'icon': 'fa-chart-area',
            'color': 'info'
        },
        {
            'time': '2 hours ago',
            'action': 'Report generated',
            'details': 'Analytical summary for Set-089',
            'icon': 'fa-file-alt',
            'color': 'warning'
        },
        {
            'time': '3 hours ago',
            'action': 'Data imported',
            'details': 'Vicell results batch upload',
            'icon': 'fa-upload',
            'color': 'secondary'
        }
    ]

    activity_items = []
    for activity in activities:
        activity_items.append(
            html.Div([
                html.Div([
                    html.I(className=f"fas {activity['icon']} text-{activity['color']}")
                ], className="me-3"),
                html.Div([
                    html.Strong(activity['action']),
                    html.Br(),
                    html.Small(activity['details'], className="text-muted"),
                    html.Br(),
                    html.Small(activity['time'], className="text-muted")
                ], className="flex-grow-1")
            ], className="d-flex align-items-start mb-3 pb-3 border-bottom")
        )

    return activity_items[:-1]  # Remove border from last item


def create_quick_actions():
    """Create quick action buttons"""
    actions = [
        {
            'title': 'Create Samples',
            'desc': 'Add new samples to CLD',
            'href': '#!/cld/create-samples',
            'icon': 'fa-plus',
            'color': 'primary'
        },
        {
            'title': 'View Sample Sets',
            'desc': 'Manage sample collections',
            'href': '#!/cld/sample-sets',
            'icon': 'fa-layer-group',
            'color': 'success'
        },
        {
            'title': 'SEC Analysis',
            'desc': 'Size exclusion chromatography',
            'href': '#!/analytical/sec',
            'icon': 'fa-microscope',
            'color': 'info'
        },
        {
            'title': 'AKTA Experiments',
            'desc': 'Chromatography workflows',
            'href': '#!/dsp/akta',
            'icon': 'fa-chart-area',
            'color': 'warning'
        },
        {
            'title': 'Create Reports',
            'desc': 'Generate analytical reports',
            'href': '#!/analytical/create-reports',
            'icon': 'fa-file-alt',
            'color': 'danger'
        },
        {
            'title': 'Data Import',
            'desc': 'Upload external data',
            'href': '#!/data-management/import',
            'icon': 'fa-upload',
            'color': 'secondary'
        }
    ]

    action_cards = []
    for action in actions:
        action_cards.append(
            dbc.Col([
                html.A([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className=f"fas {action['icon']} fa-2x text-{action['color']} mb-2"),
                                html.H6(action['title'], className="mb-1"),
                                html.P(action['desc'], className="text-muted small mb-0")
                            ], className="text-center")
                        ], className="p-3")
                    ], className="h-100 shadow-sm border-0",
                        style={'transition': 'all 0.2s ease'})
                ],
                    href=action['href'],
                    className="text-decoration-none",
                    style={'color': 'inherit'})
            ], md=4, className="mb-3")
        )

    return dbc.Row(action_cards)


def create_dashboard_content():
    """Create the main dashboard content (without sidebar)"""
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("Dashboard Overview", className="display-5 mb-1"),
                html.P("Cell Line Development Sample Management & Analysis Platform",
                       className="lead text-muted mb-4")
            ])
        ]),

        # Stats Cards
        dbc.Row([
            dbc.Col([
                create_stats_card("Total Samples", "1,247", "↑ 12% this month", "primary", "fa-vial")
            ], md=3),
            dbc.Col([
                create_stats_card("Sample Sets", "89", "Active collections", "success", "fa-layer-group")
            ], md=3),
            dbc.Col([
                create_stats_card("Active Experiments", "23", "DSP & Analytical", "warning", "fa-flask")
            ], md=3),
            dbc.Col([
                create_stats_card("Reports Generated", "156", "This month", "info", "fa-chart-line")
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
                        html.Div(create_recent_activity())
                    ])
                ], style=CARD_STYLE)
            ], md=6),

            # Right Column - System Status
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("System Status", className="mb-0")
                    ]),
                    dbc.CardBody([
                        # Status indicators
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-circle text-success me-2"),
                                "CLD System",
                                html.Span("Online", className="badge bg-success ms-2")
                            ], className="d-flex justify-content-between align-items-center mb-2"),

                            html.Div([
                                html.I(className="fas fa-circle text-success me-2"),
                                "AKTA Interface",
                                html.Span("Connected", className="badge bg-success ms-2")
                            ], className="d-flex justify-content-between align-items-center mb-2"),

                            html.Div([
                                html.I(className="fas fa-circle text-warning me-2"),
                                "Nova Flex",
                                html.Span("Maintenance", className="badge bg-warning ms-2")
                            ], className="d-flex justify-content-between align-items-center mb-2"),

                            html.Div([
                                html.I(className="fas fa-circle text-success me-2"),
                                "Vicell System",
                                html.Span("Online", className="badge bg-success ms-2")
                            ], className="d-flex justify-content-between align-items-center mb-3"),

                            html.Hr(),

                            # Queue Status
                            html.H6("Analysis Queue"),
                            html.Div([
                                html.Small("SEC: 3 pending", className="text-muted d-block"),
                                html.Small("TITER: 7 pending", className="text-muted d-block"),
                                html.Small("CE SDS: 2 pending", className="text-muted d-block"),
                                html.Small("cIEF: 1 running", className="text-muted d-block")
                            ])
                        ])
                    ])
                ], style=CARD_STYLE)
            ], md=6)
        ], className="mb-4"),

        # Quick Actions Section
        dbc.Row([
            dbc.Col([
                html.H4("Quick Actions", className="mb-3"),
                create_quick_actions()
            ])
        ])

    ], fluid=True)


def get_dashboard_css():
    """CSS specific to dashboard content"""
    return html.Style("""
    /* Quick action cards hover */
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15) !important;
    }

    /* Stats cards animation */
    .stats-card {
        transition: all 0.3s ease;
    }

    .stats-card:hover {
        transform: scale(1.02);
    }
    """)