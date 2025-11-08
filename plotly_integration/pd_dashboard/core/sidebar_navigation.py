# plotly_integration/pd_dashboard/core/sidebar_navigation.py
# Collapsible sidebar navigation with formulation section

from dash import html, dcc
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
    SIDEBAR_HOVER_CSS
)
from .sidebar_state import SidebarStateManager


def create_sidebar_navigation():
    """Create the main sidebar navigation with collapsible sections"""

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
                {'name': 'Experiment Management', 'href': '#!/cld/experiment-manager', 'icon': 'fa-flask'},
                {'name': 'Create Samples', 'href': '#!/cld/create-samples', 'icon': 'fa-plus'},
                {'name': 'View Samples', 'href': '#!/cld/view-samples', 'icon': 'fa-list'},
                {'name': 'Sample Sets', 'href': '#!/cld/sample-sets', 'icon': 'fa-layer-group'},
                {'name': 'Vicell', 'href': '#!/cld/vicell', 'icon': 'fa-vial'},
                {'name': 'Nova Flex II', 'href': '#!/cld/nova', 'icon': 'fa-microscope'}
            ]
        },
        {
            'id': 'usp',
            'title': 'USP',
            'icon': 'fa-seedling',
            'color': '#27ae60',
            'items': [
                {'name': 'Experiment Management', 'href': '#!/usp/experiment-manager', 'icon': 'fa-flask'},
                {'name': 'Media Tracking', 'href': '#!/usp/media-tracking', 'icon': 'fa-flask'},
                {'name': 'Titer Tracking', 'href': '#!/usp/titer-tracking', 'icon': 'fa-flask'},
                {'name': 'Vicell', 'href': '#!/usp/vicell', 'icon': 'fa-vial'},
                {'name': 'Nova Flex II', 'href': '#!/usp/nova', 'icon': 'fa-microscope'},
                {'name': 'Bioreactors', 'href': '#!/usp/brx', 'icon': 'fa-microscope'}
            ]
        },
        {
            'id': 'dsp',
            'title': 'DSP',
            'icon': 'fa-cogs',
            'color': '#f39c12',
            'items': [
                {'name': 'Create DN/PD', 'href': '#!/dsp/create-dn-pd', 'icon': 'fa-plus'},
                {'name': 'Source Material Generation', 'href': '#!/dsp/source-material-generation', 'icon': 'fa-virus'},
                {'name': 'Experiment Management', 'href': '#!/dsp/experiment-manager', 'icon': 'fa-virus'},
                {'name': 'Sample Management', 'href': '#!/dsp/sample-manager', 'icon': 'fa-virus'},
                {'name': 'Analytics Dashboard', 'href': '#!/dsp/analytics-dashboard', 'icon': 'fa-virus'},
                {'name': 'AKTA', 'href': '#!/dsp/akta', 'icon': 'fa-chart-line'},
                {'name': 'UFDF', 'href': '#!/dsp/ufdf', 'icon': 'fa-filter'},
                {'name': 'VF', 'href': '#!/dsp/vf', 'icon': 'fa-virus'},
                {'name': 'Viral Inactivation', 'href': '#!/dsp/viral-inactivation', 'icon': 'fa-shield-virus'}
            ]
        },
        {
            'id': 'analytical',
            'title': 'Analytical',
            'icon': 'fa-microscope',
            'color': '#9b59b6',
            'items': [
                {'name': 'Create Report', 'href': '#!/analytical/report', 'icon': 'fa-chart-area'},
                {'name': 'SEC', 'href': '#!/analytical/sec', 'icon': 'fa-chart-area'},
                {'name': 'Titer', 'href': '#!/analytical/titer', 'icon': 'fa-vial'},
                {'name': 'CE SDS', 'href': '#!/analytical/ce-sds', 'icon': 'fa-wave-square'},
                {'name': 'cIEF', 'href': '#!/analytical/cief', 'icon': 'fa-bolt'},
                {'name': 'Mass Spec', 'href': '#!/analytical/mass-spec', 'icon': 'fa-atom'},
                {'name': 'Octet', 'href': '#!/analytical/octet', 'icon': 'fa-atom'}
            ]
        },
        {
            'id': 'formulation',
            'title': 'Formulation',
            'icon': 'fa-vials',
            'color': '#e67e22',
            'items': [
                # {'name': 'Dashboard', 'href': '#!/formulation/dashboard', 'icon': 'fa-chart-pie'},
                # {'name': 'Create Experiment', 'href': '#!/formulation/create-experiment', 'icon': 'fa-plus-circle'},
                # {'name': 'Experiment Manager', 'href': '#!/formulation/experiment-manager', 'icon': 'fa-flask'},
                # {'name': 'Design Formulations', 'href': '#!/formulation/design', 'icon': 'fa-vials'},
                # {'name': 'Sample Management', 'href': '#!/formulation/samples', 'icon': 'fa-plus-circle'},
                # {'name': 'Data Entry', 'href': '#!/formulation/data-entry', 'icon': 'fa-table'},
                # {'name': 'Stability Visualization', 'href': '#!/formulation/visualization', 'icon': 'fa-chart-line'},
                {'name': 'Plasma Stability', 'href': '#!/formulation/plasma-stability', 'icon': 'fa-chart-line'}

            ]
        },
        {
            'id': 'protein-engineering',
            'title': 'PE',
            'icon': 'fa-vials',
            'color': '#e67e22',
            'items': [
                {'name': 'Octet Kinetics', 'href': '#!/protein-engineering/octet-kinetics', 'icon': 'fa-chart-line'}
            ]
        },

    ]

    def create_nav_item(section):
        """Create a navigation item - collapsible if it has sub-items"""

        nav_elements = []

        # Main item (section header)
        if section['items']:
            # Section with sub-items - clickable header with chevron
            main_item = html.Div([
                html.I(
                    className=f"fas {section['icon']}",
                    style=get_main_item_icon_style(section['color'])
                ),
                html.Span(section['title'], style=get_main_item_text_style()),
                html.I(
                    id={'type': 'collapse-icon', 'index': section['id']},
                    className="fas fa-chevron-down",
                    style={
                        'fontSize': SIDEBAR_CONFIG['chevron_size'],
                        'color': SIDEBAR_CONFIG['text_muted'],
                        'marginLeft': 'auto',
                        'transition': 'transform 0.3s ease'
                    }
                )
            ],
                id={'type': 'section-header', 'index': section['id']},
                style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'padding': SIDEBAR_CONFIG['main_item_padding'],
                    'borderRadius': '8px',
                    'marginBottom': f"{SIDEBAR_CONFIG['item_margin']}",
                    'backgroundColor': 'rgba(255,255,255,0.05)',
                    'fontWeight': 'bold',
                    'cursor': 'pointer',
                    'transition': 'all 0.2s ease'
                },
                className="sidebar-section-header"
            )
            nav_elements.append(main_item)

            # Sub-items (collapsible)
            # Start collapsed by default
            initial_state = SidebarStateManager.DEFAULT_COLLAPSE_STATE.get(section['id'], False)
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
            ],
                id={'type': 'sub-items', 'index': section['id']},
                style=SidebarStateManager.get_section_style(section['id'], initial_state)
            )

            nav_elements.append(sub_items)

        else:
            # Direct link item (no sub-items) - like Dashboard and Data Import
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
        # State storage for collapse state
        SidebarStateManager.create_state_store(),

        # Logo/Brand area
        html.Div([
            html.Div([
                html.Span("PD Dashboard", style=get_sidebar_title_style())
            ], style=get_logo_area_style())
        ]),

        # Navigation items
        html.Div(nav_items),

        # Add CSS for hover and collapse effects
        html.Div([
            html.Link(
                rel="stylesheet",
                href="data:text/css;charset=utf-8," + SIDEBAR_HOVER_CSS + """
.sidebar-section-header:hover {
    background-color: rgba(52, 152, 219, 0.15) !important;
}

.collapse-icon-rotated {
    transform: rotate(-90deg);
}
"""
            )
        ])

    ], style=get_sidebar_main_style(), id="main-sidebar")


def register_sidebar_callbacks(app):
    """Register callbacks for collapsible sidebar sections"""
    from dash import Input, Output, State, ALL
    import dash

    @app.callback(
        [Output({'type': 'sub-items', 'index': ALL}, 'style'),
         Output({'type': 'collapse-icon', 'index': ALL}, 'style'),
         Output('sidebar-collapse-state', 'data')],
        [Input({'type': 'section-header', 'index': ALL}, 'n_clicks')],
        [State('sidebar-collapse-state', 'data'),
         State({'type': 'sub-items', 'index': ALL}, 'id'),
         State({'type': 'collapse-icon', 'index': ALL}, 'id')],
        prevent_initial_call=False
    )
    def toggle_sidebar_sections(n_clicks, current_state, sub_items_ids, icon_ids):
        """Toggle sidebar section collapse state"""
        import json

        # Get which section was clicked from callback context
        ctx = dash.callback_context
        if not ctx.triggered:
            # Return current styles
            return (
                [SidebarStateManager.get_section_style(item['index'], current_state.get(item['index'], False))
                 for item in sub_items_ids],
                [{'fontSize': SIDEBAR_CONFIG['chevron_size'],
                  'color': SIDEBAR_CONFIG['text_muted'],
                  'marginLeft': 'auto',
                  'transition': 'transform 0.3s ease',
                  'transform': 'rotate(0deg)' if current_state.get(icon['index'], False) else 'rotate(-90deg)'}
                 for icon in icon_ids],
                current_state
            )

        # Parse the triggered prop_id to get the section that was clicked
        triggered_prop = ctx.triggered[0]['prop_id']
        if not triggered_prop or triggered_prop == '.':
            # Return current styles
            return (
                [SidebarStateManager.get_section_style(item['index'], current_state.get(item['index'], False))
                 for item in sub_items_ids],
                [{'fontSize': SIDEBAR_CONFIG['chevron_size'],
                  'color': SIDEBAR_CONFIG['text_muted'],
                  'marginLeft': 'auto',
                  'transition': 'transform 0.3s ease',
                  'transform': 'rotate(0deg)' if current_state.get(icon['index'], False) else 'rotate(-90deg)'}
                 for icon in icon_ids],
                current_state
            )

        # Extract the section ID from the triggered prop_id
        # Format: {"index":"cld","type":"section-header"}.n_clicks
        triggered_id_str = triggered_prop.split('.')[0]
        triggered_id = json.loads(triggered_id_str)
        section_id = triggered_id['index']

        # Toggle the state
        new_state = SidebarStateManager.toggle_section_state(current_state, section_id)

        # Generate new styles for all sections
        new_styles = [
            SidebarStateManager.get_section_style(item['index'], new_state.get(item['index'], False))
            for item in sub_items_ids
        ]

        # Generate icon styles with rotation
        icon_styles = [
            {
                'fontSize': SIDEBAR_CONFIG['chevron_size'],
                'color': SIDEBAR_CONFIG['text_muted'],
                'marginLeft': 'auto',
                'transition': 'transform 0.3s ease',
                'transform': 'rotate(0deg)' if new_state.get(icon['index'], False) else 'rotate(-90deg)'
            }
            for icon in icon_ids
        ]

        return new_styles, icon_styles, new_state

    print("Success: Sidebar collapse callbacks registered")