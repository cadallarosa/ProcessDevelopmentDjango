# plotly_integration/pd_dashboard/core/layout_manager.py
from dash import html
from .sidebar_navigation import create_sidebar_navigation
from .dashboard_content import create_dashboard_content
from .settings_content import create_settings_content


def create_full_page_layout(content):
    """
    Create a full page layout with sidebar and content

    Args:
        content: The main content component
    """
    content_style = {
        'marginLeft': '250px',  # Updated for wider sidebar
        'padding': '2rem',
        'backgroundColor': '#fafbfc',
        'minHeight': '100vh'
    }

    return html.Div([
        # Sidebar
        create_sidebar_navigation(),

        # Main Content
        html.Div([
            content
        ], style=content_style)
    ])


def create_dashboard_layout():
    """Create the complete dashboard layout (standalone version)"""
    return create_full_page_layout(create_dashboard_content())


def create_settings_layout():
    """Create the complete settings layout (standalone version)"""
    return create_full_page_layout(create_settings_content())


def create_placeholder_page(title, description):
    """Create a placeholder page for routes that don't exist yet"""
    from dash import html
    import dash_bootstrap_components as dbc

    content = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2(title, className="display-6 mb-3"),
                html.P(description, className="lead text-muted mb-4"),
                dbc.Alert([
                    html.I(className="fas fa-info-circle me-2"),
                    "This page is currently under development."
                ], color="info"),
                dbc.Button([
                    html.I(className="fas fa-home me-2"),
                    "Return to Dashboard"
                ], href="#!/", color="primary")
            ])
        ])
    ], fluid=True)

    return create_full_page_layout(content)


# Content-only functions for routing integration
def get_dashboard_content_only():
    """Get just the dashboard content for routing"""
    return create_dashboard_content()


def get_settings_content_only():
    """Get just the settings content for routing"""
    return create_settings_content()


# Common page layouts for different sections
def create_cld_page_layout(content):
    """Create a CLD section page layout"""
    return create_full_page_layout(content)


def create_usp_page_layout(content):
    """Create a USP section page layout"""
    return create_full_page_layout(content)


def create_dsp_page_layout(content):
    """Create a DSP section page layout"""
    return create_full_page_layout(content)


def create_analytical_page_layout(content):
    """Create an Analytical section page layout"""
    return create_full_page_layout(content)


def create_data_management_page_layout(content):
    """Create a Data Management section page layout"""
    return create_full_page_layout(content)