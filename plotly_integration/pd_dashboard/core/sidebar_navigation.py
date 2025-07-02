# plotly_integration/pd_dashboard/core/sidebar_navigation.py
from dash import html
import dash_bootstrap_components as dbc


def create_sidebar_navigation():
    """Create the main sidebar navigation with icon-based expandable sections"""

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


def get_sidebar_css():
    """CSS for sidebar hover effects and popout menus"""
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