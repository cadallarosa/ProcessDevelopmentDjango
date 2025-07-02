# plotly_integration/pd_dashboard/core/dashboard_home.py
from dash import html, Input, Output, callback, dcc, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from ..shared.styles.common_styles import CARD_STYLE, COLORS


def create_sidebar_navigation():
    """Create the main sidebar navigation with icon-based expandable sections"""

    # Compact sidebar style (collapsed state)
    sidebar_style = {
        'position': 'fixed',
        'top': 0,
        'left': 0,
        'bottom': 0,
        'width': '70px',
        'padding': '1rem 0.5rem',
        'backgroundColor': '#2c3e50',
        'borderRight': '1px solid #34495e',
        'overflowY': 'auto',
        'overflowX': 'visible',
        'zIndex': 1000,
        'transition': 'width 0.3s ease'
    }

    # Navigation items with their sub-menus
    nav_sections = [
        {
            'id': 'home',
            'title': 'Dashboard',
            'icon': 'fa-home',
            'color': '#3498db',
            'href': '#!/',
            'items': []
        },
        {
            'id': 'cld',
            'title': 'CLD',
            'icon': 'fa-flask',
            'color': '#e74c3c',
            'items': [
                {'name': 'Create Samples', 'href': '#!/cld/create-samples', 'icon': 'fa-plus'},
                {'name': 'View Samples', 'href': '#!/cld/view-samples', 'icon': 'fa-list'},
                {'name': 'Sample Sets', 'href': '#!/cld/sample-sets', 'icon': 'fa-layer-group'},
                {'name': 'Nova Flex', 'href': '#!/cld/nova-flex', 'icon': 'fa-microscope'},
                {'name': 'Vicell', 'href': '#!/cld/vicell', 'icon': 'fa-vial'}
            ]
        },
        {
            'id': 'usp',
            'title': 'USP',
            'icon': 'fa-seedling',
            'color': '#27ae60',
            'items': [
                {'name': 'Create Samples', 'href': '#!/usp/create-samples', 'icon': 'fa-plus'},
                {'name': 'View Samples', 'href': '#!/usp/view-samples', 'icon': 'fa-list'},
                {'name': 'Sample Sets', 'href': '#!/usp/sample-sets', 'icon': 'fa-layer-group'},
                {'name': 'Nova Flex', 'href': '#!/usp/nova-flex', 'icon': 'fa-microscope'},
                {'name': 'Vicell', 'href': '#!/usp/vicell', 'icon': 'fa-vial'}
            ]
        },
        {
            'id': 'dsp',
            'title': 'DSP',
            'icon': 'fa-industry',
            'color': '#f39c12',
            'items': [
                {'name': 'Create Experiments', 'href': '#!/dsp/create-experiments', 'icon': 'fa-flask'},
                {'name': 'AKTA', 'href': '#!/dsp/akta', 'icon': 'fa-chart-area'},
                {'name': 'VI', 'href': '#!/dsp/vi', 'icon': 'fa-shield-virus'},
                {'name': 'VF', 'href': '#!/dsp/vf', 'icon': 'fa-filter'},
                {'name': 'UFDF', 'href': '#!/dsp/ufdf', 'icon': 'fa-water'}
            ]
        },
        {
            'id': 'analytical',
            'title': 'Analytical',
            'icon': 'fa-chart-bar',
            'color': '#9b59b6',
            'items': [
                {'name': 'SEC', 'href': '#!/analytical/sec', 'icon': 'fa-microscope'},
                {'name': 'TITER', 'href': '#!/analytical/titer', 'icon': 'fa-vial'},
                {'name': 'CE SDS', 'href': '#!/analytical/ce-sds', 'icon': 'fa-chart-line'},
                {'name': 'cIEF', 'href': '#!/analytical/cief', 'icon': 'fa-wave-square'},
                {'name': 'Mass Spec', 'href': '#!/analytical/mass-spec', 'icon': 'fa-atom'},
                {'name': 'Create Reports', 'href': '#!/analytical/create-reports', 'icon': 'fa-file-alt'}
            ]
        },
        {
            'id': 'data',
            'title': 'Data Management',
            'icon': 'fa-database',
            'color': '#34495e',
            'items': [
                {'name': 'Import Data', 'href': '#!/data-management/import', 'icon': 'fa-upload'},
                {'name': 'Export Data', 'href': '#!/data-management/export', 'icon': 'fa-download'},
                {'name': 'Data Quality', 'href': '#!/data-management/quality', 'icon': 'fa-check-circle'},
                {'name': 'Archive', 'href': '#!/data-management/archive', 'icon': 'fa-archive'}
            ]
        },
        {
            'id': 'settings',
            'title': 'Settings',
            'icon': 'fa-cog',
            'color': '#7f8c8d',
            'href': '#!/settings',
            'items': []
        }
    ]

    def create_nav_item(section):
        """Create a navigation item with popout menu"""
        item_id = f"nav-{section['id']}"

        # For sections with items, don't make the main icon a direct link
        main_href = section.get('href', '#') if not section['items'] else '#'

        # Main icon button
        main_button = html.Div([
            html.Div([
                html.I(
                    className=f"fas {section['icon']}",
                    style={
                        'fontSize': '20px',
                        'color': section['color'],
                        'display': 'block',
                        'textAlign': 'center'
                    }
                )
            ],
                className="nav-icon-link",
                style={
                    'display': 'block',
                    'padding': '15px 10px',
                    'textDecoration': 'none',
                    'borderRadius': '8px',
                    'transition': 'all 0.2s ease',
                    'position': 'relative',
                    'cursor': 'pointer'
                },
                id=f"{item_id}-trigger"
            ),

            # Tooltip with section title
            dbc.Tooltip(
                section['title'],
                target=f"{item_id}-trigger",
                placement="right"
            ),

            # Popout menu (only if has items)
            html.Div([
                html.Div([
                    html.Div([
                        html.H6(section['title'],
                                className="text-white mb-3 px-3 pt-3",
                                style={'borderBottom': '1px solid #4a5a6a', 'paddingBottom': '10px'})
                    ]),
                    html.Div([
                        html.A([
                            html.I(className=f"fas {item['icon']} me-2",
                                   style={'width': '16px', 'textAlign': 'center'}),
                            item['name']
                        ],
                            href=item['href'],
                            className="dropdown-item text-white py-2 px-3",
                            style={
                                'textDecoration': 'none',
                                'fontSize': '14px',
                                'borderRadius': '4px',
                                'margin': '2px 8px',
                                'transition': 'background-color 0.2s ease',
                                'display': 'flex',
                                'alignItems': 'center'
                            }
                        ) for item in section['items']
                    ], style={'paddingBottom': '10px'})
                ], style={
                    'backgroundColor': '#34495e',
                    'borderRadius': '8px',
                    'minWidth': '220px',
                    'boxShadow': '0 4px 12px rgba(0,0,0,0.15)',
                    'border': '1px solid #4a5a6a'
                })
            ],
                id=f"{item_id}-popout",
                className="nav-popout",
                style={
                    'position': 'absolute',
                    'left': '75px',
                    'top': '0',
                    'zIndex': 1001,
                    'display': 'none'
                }
            ) if section['items'] else html.Div()
        ],
            className="nav-item-container",
            style={'position': 'relative', 'marginBottom': '5px'}
        )

        return main_button

    # Create all navigation items
    nav_items = [create_nav_item(section) for section in nav_sections]

    return html.Div([
        # Logo/Brand area
        html.Div([
            html.Div("🧬", style={
                'fontSize': '24px',
                'textAlign': 'center',
                'color': '#3498db',
                'marginBottom': '20px',
                'padding': '10px'
            })
        ]),

        # Navigation items
        html.Div(nav_items),

        # User info at bottom
        html.Div([
            html.Div([
                html.I(className="fas fa-user-circle",
                       style={
                           'fontSize': '20px',
                           'color': '#bdc3c7',
                           'textAlign': 'center',
                           'display': 'block'
                       })
            ],
                style={
                    'padding': '15px 10px',
                    'borderTop': '1px solid #4a5a6a',
                    'marginTop': 'auto'
                })
        ], style={'position': 'absolute', 'bottom': '10px', 'width': '100%'})

    ], style=sidebar_style, id="main-sidebar")


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


def create_dashboard_layout():
    """Create the main dashboard overview layout (standalone version)"""
    return create_full_page_layout(create_home_page_content())


def create_dashboard_content_only():
    """Create dashboard content for routing integration"""
    return create_home_page_content()


def create_settings_content_only():
    """Create settings content for routing integration"""
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


def create_settings_layout():
    """Create settings page layout (standalone version)"""
    return create_full_page_layout(create_settings_content_only())


# Add routing integration functions
def create_full_page_layout(content):
    """Create a full page layout with sidebar and content"""
    content_style = {
        'marginLeft': '70px',  # Match the compact sidebar width
        'padding': '2rem',
        'backgroundColor': '#fafbfc',
        'minHeight': '100vh'
    }

    return html.Div([
        # Compact Sidebar
        create_sidebar_navigation(),

        # Main Content
        html.Div([
            content,
            # Add the custom CSS for dropdown functionality
            get_custom_css()
        ], style=content_style)
    ])


def create_home_page_content():
    """Create just the home page content without sidebar (for routing)"""
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


# Add CSS for hover effects and popout menus
def get_custom_css():
    return html.Style("""
    /* Sidebar hover effects */
    .nav-icon-link:hover {
        background-color: rgba(52, 152, 219, 0.1) !important;
        transform: scale(1.05);
    }

    /* Show popout on hover */
    .nav-item-container:hover .nav-popout {
        display: block !important;
        animation: slideIn 0.2s ease-out;
    }

    /* Keep popout visible when hovering over it */
    .nav-popout:hover {
        display: block !important;
    }

    /* Popout animation */
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-10px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    /* Dropdown item hover */
    .dropdown-item:hover {
        background-color: rgba(52, 152, 219, 0.2) !important;
    }

    /* Quick action cards hover */
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15) !important;
    }

    /* Ensure popout stays visible during transition */
    .nav-item-container:hover .nav-popout,
    .nav-popout:hover {
        display: block !important;
    }

    /* Add some spacing for better UX */
    .nav-popout .dropdown-item {
        white-space: nowrap;
    }
    """)