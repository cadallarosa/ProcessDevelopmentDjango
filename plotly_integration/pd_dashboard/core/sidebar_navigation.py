# plotly_integration/pd_dashboard/core/sidebar_navigation.py
# Simplified version - all items always visible, no dropdowns

from dash import html
import dash_bootstrap_components as dbc
from ..shared.styles.common_styles import (
    SIDEBAR_CONFIG,
    get_sidebar_main_style,
    get_sidebar_title_style,
    get_main_item_icon_style,
    get_main_item_text_style,
    get_dropdown_container_style,
    get_dropdown_item_style,
    get_dropdown_icon_style,
    get_logo_area_style,
    get_user_area_style,
    get_user_text_style,
    SIDEBAR_HOVER_CSS
)


def create_sidebar_navigation():
    """Create the main sidebar navigation with all items always visible"""

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
        """Create a navigation item - always expanded if it has sub-items"""

        nav_elements = []

        # Main item (section header)
        if section['items']:
            # Section with sub-items - show header but no link
            main_item = html.Div([
                html.I(
                    className=f"fas {section['icon']}",
                    style=get_main_item_icon_style(section['color'])
                ),
                html.Span(section['title'], style=get_main_item_text_style())
            ],
                style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'padding': SIDEBAR_CONFIG['main_item_padding'],
                    'borderRadius': '8px',
                    'marginBottom': f"{SIDEBAR_CONFIG['item_margin']}",
                    'backgroundColor': 'rgba(255,255,255,0.05)',  # Slight background for headers
                    'fontWeight': 'bold'
                }
            )
            nav_elements.append(main_item)

            # Sub-items (always visible)
            sub_items = html.Div([
                html.A([
                    html.I(
                        className=f"fas {item['icon']}",
                        style=get_dropdown_icon_style()
                    ),
                    html.Span(item['name'])
                ],
                    href=item['href'],
                    style=get_dropdown_item_style(),
                    className="sidebar-sub-item"
                ) for item in section['items']
            ], style=get_dropdown_container_style())

            nav_elements.append(sub_items)

        else:
            # Direct link item (no sub-items) - like Dashboard and Settings
            main_item = html.A([
                html.I(
                    className=f"fas {section['icon']}",
                    style=get_main_item_icon_style(section['color'])
                ),
                html.Span(section['title'], style=get_main_item_text_style())
            ],
                href=section.get('href', '#'),
                style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'padding': SIDEBAR_CONFIG['main_item_padding'],
                    'borderRadius': '8px',
                    'textDecoration': 'none',
                    'transition': 'all 0.2s ease',
                    'marginBottom': SIDEBAR_CONFIG['item_margin']
                },
                className="sidebar-main-item"
            )
            nav_elements.append(main_item)

        return html.Div(nav_elements, style={'marginBottom': '15px'})  # Space between sections

    # Create all navigation items
    nav_items = [create_nav_item(section) for section in nav_sections]

    return html.Div([
        # Logo/Brand area
        html.Div([
            html.Div([
                html.Span("🧬", style={'fontSize': '22px', 'marginRight': '8px'}),
                html.Span("PD Dashboard", style=get_sidebar_title_style())
            ], style=get_logo_area_style())
        ]),

        # Navigation items
        html.Div(nav_items),

        # User info at bottom
        html.Div([
            html.Hr(style={'borderColor': '#4a5a6a', 'margin': '20px 0'}),
            html.Div([
                html.I(className="fas fa-user-circle",
                       style={'fontSize': '16px', 'color': SIDEBAR_CONFIG['text_muted'], 'marginRight': '8px'}),
                html.Span("User", style=get_user_text_style())
            ], style=get_user_area_style())
        ], style={'position': 'absolute', 'bottom': '10px', 'width': '100%'}),

        # Add CSS for hover effects
        html.Div([
            html.Link(
                rel="stylesheet",
                href="data:text/css;charset=utf-8," + SIDEBAR_HOVER_CSS
            )
        ])

    ], style=get_sidebar_main_style(), id="main-sidebar")


# 🎯 NO CALLBACKS NEEDED! - Remove the register_sidebar_callbacks function entirely
def register_sidebar_callbacks(app):
    """No callbacks needed for always-expanded sidebar"""
    print("✅ Sidebar callbacks skipped - using always-expanded mode")
    pass