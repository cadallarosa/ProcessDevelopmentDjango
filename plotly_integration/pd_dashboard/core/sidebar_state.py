# plotly_integration/pd_dashboard/core/sidebar_state.py
# State management utilities for sidebar collapse functionality

from dash import dcc, html
import json


class SidebarStateManager:
    """Manages sidebar collapse state across page navigation"""

    DEFAULT_COLLAPSE_STATE = {
        'cld': True,  # Expanded by default
        'usp': True,  # Expanded by default
        'dsp': True,  # Expanded by default
        'analytical': True,  # Expanded by default
    }

    @classmethod
    def get_initial_state(cls):
        """Get the initial collapse state for all sections"""
        return cls.DEFAULT_COLLAPSE_STATE.copy()

    @classmethod
    def create_state_store(cls):
        """Create a dcc.Store component for sidebar state"""
        return dcc.Store(
            id='sidebar-collapse-state',
            data=cls.get_initial_state(),
            storage_type='session'  # Persist across browser tabs but not browser restarts
        )

    @classmethod
    def get_section_style(cls, section_id, is_expanded=True):
        """Get the style for a collapsible section"""
        from ..shared.styles.common_styles import get_dropdown_container_style

        base_style = {
            **get_dropdown_container_style(),
            'overflow': 'hidden',
            'transition': 'max-height 0.3s ease'
        }

        if is_expanded:
            return {**base_style, 'maxHeight': '1000px'}
        else:
            return {
                **base_style,
                'maxHeight': '0px',
                'paddingTop': '0px',
                'paddingBottom': '0px'
            }

    @classmethod
    def get_icon_class(cls, is_expanded=True):
        """Get the icon class for collapse indicator"""
        if is_expanded:
            return "fas fa-chevron-down"
        else:
            return "fas fa-chevron-down collapse-icon-rotated"

    @classmethod
    def toggle_section_state(cls, current_state, section_id):
        """Toggle the collapse state of a specific section"""
        new_state = current_state.copy()
        new_state[section_id] = not current_state.get(section_id, True)
        return new_state

    @classmethod
    def expand_all_sections(cls):
        """Return state with all sections expanded"""
        return {key: True for key in cls.DEFAULT_COLLAPSE_STATE.keys()}

    @classmethod
    def collapse_all_sections(cls):
        """Return state with all sections collapsed"""
        return {key: False for key in cls.DEFAULT_COLLAPSE_STATE.keys()}


def create_sidebar_controls():
    """Create additional controls for sidebar management"""
    return html.Div([
        html.Div([
            html.Button(
                [html.I(className="fas fa-expand-arrows-alt"), " Expand All"],
                id="expand-all-btn",
                className="btn btn-sm btn-outline-light me-2",
                style={'fontSize': '11px', 'padding': '4px 8px'}
            ),
            html.Button(
                [html.I(className="fas fa-compress-arrows-alt"), " Collapse All"],
                id="collapse-all-btn",
                className="btn btn-sm btn-outline-light",
                style={'fontSize': '11px', 'padding': '4px 8px'}
            )
        ], className="d-flex justify-content-center mb-3"),
    ], style={'padding': '10px 5px'})


def register_sidebar_control_callbacks(app):
    """Register callbacks for sidebar control buttons"""
    from dash import Input, Output, State, ALL

    @app.callback(
        [Output('sidebar-collapse-state', 'data', allow_duplicate=True),
         Output({'type': 'sub-items', 'index': ALL}, 'style', allow_duplicate=True),
         Output({'type': 'collapse-icon', 'index': ALL}, 'className', allow_duplicate=True)],
        [Input('expand-all-btn', 'n_clicks'),
         Input('collapse-all-btn', 'n_clicks')],
        [State('sidebar-collapse-state', 'data'),
         State({'type': 'sub-items', 'index': ALL}, 'id')],
        prevent_initial_call=True
    )
    def handle_expand_collapse_all(expand_clicks, collapse_clicks, current_state, sub_items_ids):
        """Handle expand all / collapse all button clicks"""
        from dash import ctx

        if not ctx.triggered:
            return current_state, [], []

        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if button_id == 'expand-all-btn' and expand_clicks:
            new_state = SidebarStateManager.expand_all_sections()
            styles = [SidebarStateManager.get_section_style(item['index'], True) for item in sub_items_ids]
            icon_classes = [SidebarStateManager.get_icon_class(True) for _ in sub_items_ids]
            return new_state, styles, icon_classes

        elif button_id == 'collapse-all-btn' and collapse_clicks:
            new_state = SidebarStateManager.collapse_all_sections()
            styles = [SidebarStateManager.get_section_style(item['index'], False) for item in sub_items_ids]
            icon_classes = [SidebarStateManager.get_icon_class(False) for _ in sub_items_ids]
            return new_state, styles, icon_classes

        # Default return
        return current_state, [], []


def add_keyboard_shortcuts():
    """Add keyboard shortcuts for sidebar navigation"""
    return html.Div([
        dcc.Store(id='keyboard-shortcuts-active', data=True),
        html.Script("""
            document.addEventListener('keydown', function(e) {
                // Only if no input is focused
                if (document.activeElement.tagName.toLowerCase() !== 'input' && 
                    document.activeElement.tagName.toLowerCase() !== 'textarea') {

                    // Alt + 1-5 for quick section toggle
                    if (e.altKey && e.key >= '1' && e.key <= '5') {
                        e.preventDefault();
                        const sections = ['cld', 'usp', 'dsp', 'analytical'];
                        const sectionIndex = parseInt(e.key) - 1;
                        if (sectionIndex < sections.length) {
                            const sectionId = sections[sectionIndex];
                            const header = document.querySelector(`[id*='section-header'][id*='${sectionId}']`);
                            if (header) header.click();
                        }
                    }

                    // Alt + A for expand all
                    if (e.altKey && e.key.toLowerCase() === 'a') {
                        e.preventDefault();
                        const expandBtn = document.getElementById('expand-all-btn');
                        if (expandBtn) expandBtn.click();
                    }

                    // Alt + C for collapse all
                    if (e.altKey && e.key.toLowerCase() === 'c') {
                        e.preventDefault();
                        const collapseBtn = document.getElementById('collapse-all-btn');
                        if (collapseBtn) collapseBtn.click();
                    }
                }
            });
        """)
    ])


def create_sidebar_help_tooltip():
    """Create help tooltip for sidebar shortcuts"""
    return html.Div([
        html.Button(
            html.I(className="fas fa-question-circle"),
            id="sidebar-help-btn",
            className="btn btn-sm btn-outline-light",
            style={
                'position': 'absolute',
                'top': '10px',
                'right': '10px',
                'fontSize': '12px',
                'padding': '2px 6px'
            }
        ),
        dbc.Tooltip([
            html.Div("Keyboard Shortcuts:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
            html.Div("Alt + 1-4: Toggle sections"),
            html.Div("Alt + A: Expand all"),
            html.Div("Alt + C: Collapse all"),
        ],
            target="sidebar-help-btn",
            placement="right"
        )
    ], style={'position': 'relative'})