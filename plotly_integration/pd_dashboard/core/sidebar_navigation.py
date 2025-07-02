# plotly_integration/pd_dashboard/core/sidebar_navigation.py
from dash import html, callback, Output, Input, State
import dash_bootstrap_components as dbc


def create_sidebar_navigation():
    """Create the main sidebar navigation with expandable/collapsible sections"""

    sidebar_style = {
        'position': 'fixed',
        'top': 0,
        'left': 0,
        'bottom': 0,
        'width': '250px',
        'padding': '1rem',
        'backgroundColor': '#2c3e50',
        'borderRight': '1px solid #34495e',
        'overflowY': 'auto',
        'zIndex': 1000
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
        """Create a navigation item with expandable/collapsible sub-items"""
        item_id = f"nav-{section['id']}"

        if section['items']:
            # Section with sub-items - collapsible
            main_item = dbc.Card([
                dbc.CardHeader([
                    dbc.Button([
                        html.I(
                            className=f"fas {section['icon']}",
                            style={
                                'fontSize': '16px',
                                'color': section['color'],
                                'marginRight': '12px',
                                'width': '20px'
                            }
                        ),
                        html.Span(section['title'], style={'color': '#ecf0f1'}),
                        html.I(
                            className="fas fa-chevron-down",
                            style={
                                'fontSize': '12px',
                                'color': '#bdc3c7',
                                'marginLeft': 'auto'
                            },
                            id=f"{item_id}-chevron"
                        )
                    ],
                        id=f"{item_id}-toggle",
                        color="link",
                        className="text-start p-0 w-100 d-flex align-items-center",
                        style={
                            'backgroundColor': 'transparent',
                            'border': 'none',
                            'padding': '12px 16px !important',
                            'textDecoration': 'none'
                        }
                    )
                ], style={
                    'backgroundColor': 'transparent',
                    'border': 'none',
                    'padding': '0'
                }),

                dbc.Collapse([
                    dbc.CardBody([
                        html.Div([
                            html.A([
                                html.I(className=f"fas {item['icon']}",
                                       style={'width': '16px', 'marginRight': '8px', 'fontSize': '12px',
                                              'color': '#bdc3c7'}),
                                item['name']
                            ],
                                href=item['href'],
                                style={
                                    'display': 'block',
                                    'padding': '8px 16px',
                                    'color': '#bdc3c7',
                                    'textDecoration': 'none',
                                    'fontSize': '14px',
                                    'borderRadius': '4px',
                                    'margin': '2px 0',
                                    'transition': 'all 0.2s ease'
                                },
                                className="sidebar-sub-item"
                            ) for item in section['items']
                        ])
                    ], style={'padding': '0 0 10px 36px'})  # Indent sub-items
                ],
                    id=f"{item_id}-collapse",
                    is_open=False  # Start collapsed
                )
            ], style={
                'backgroundColor': 'transparent',
                'border': 'none',
                'marginBottom': '4px'
            })

        else:
            # Direct link item (no sub-items)
            main_item = html.A([
                html.I(
                    className=f"fas {section['icon']}",
                    style={
                        'fontSize': '16px',
                        'color': section['color'],
                        'marginRight': '12px',
                        'width': '20px'
                    }
                ),
                html.Span(section['title'], style={'color': '#ecf0f1'})
            ],
                href=section.get('href', '#'),
                style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'padding': '12px 16px',
                    'borderRadius': '8px',
                    'textDecoration': 'none',
                    'transition': 'all 0.2s ease',
                    'marginBottom': '4px'
                },
                className="sidebar-main-item"
            )

        return main_item

    # Create all navigation items
    nav_items = [create_nav_item(section) for section in nav_sections]

    return html.Div([
        # Logo/Brand area
        html.Div([
            html.Div([
                html.Span("🧬", style={'fontSize': '24px', 'marginRight': '10px'}),
                html.Span("PD Dashboard", style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#3498db'})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '30px', 'padding': '10px'})
        ]),

        # Navigation items
        html.Div(nav_items),

        # User info at bottom
        html.Div([
            html.Hr(style={'borderColor': '#4a5a6a', 'margin': '20px 0'}),
            html.Div([
                html.I(className="fas fa-user-circle",
                       style={'fontSize': '16px', 'color': '#bdc3c7', 'marginRight': '8px'}),
                html.Span("User", style={'color': '#bdc3c7', 'fontSize': '14px'})
            ],
                style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'padding': '10px 16px'
                })
        ], style={'position': 'absolute', 'bottom': '10px', 'width': '100%'}),

        # Add CSS for hover effects
        html.Div([
            html.Link(
                rel="stylesheet",
                href="data:text/css;charset=utf-8," + """
                .sidebar-main-item:hover {
                    background-color: rgba(52, 152, 219, 0.1) !important;
                }

                .sidebar-sub-item:hover {
                    background-color: rgba(52, 152, 219, 0.2) !important;
                    color: #ffffff !important;
                }
                """
            )
        ])

    ], style=sidebar_style, id="main-sidebar")


# Add callbacks for collapsible sections
def register_sidebar_callbacks(app):
    """Register callbacks for sidebar collapse functionality"""

    # Get all sections with items for callbacks
    sections_with_items = ['cld', 'usp', 'dsp', 'analytical', 'data']

    for section in sections_with_items:
        @callback(
            [Output(f"nav-{section}-collapse", "is_open"),
             Output(f"nav-{section}-chevron", "className")],
            Input(f"nav-{section}-toggle", "n_clicks"),
            State(f"nav-{section}-collapse", "is_open"),
            prevent_initial_call=True
        )
        def toggle_collapse(n_clicks, is_open):
            if n_clicks:
                new_state = not is_open
                chevron_class = "fas fa-chevron-up" if new_state else "fas fa-chevron-down"
                return new_state, chevron_class
            return is_open, "fas fa-chevron-down"