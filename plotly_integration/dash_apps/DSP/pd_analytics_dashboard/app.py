"""PD Analytics Dashboard - Main registration file."""
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
from .layout import create_layout
from .callbacks import register_all_callbacks


def create_pd_analytics_app():
    """Create and register the PD Analytics Dashboard app."""
    app = DjangoDash(
        name="PDAnalyticsDashboard",
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            dbc.icons.BOOTSTRAP,
        ],
        suppress_callback_exceptions=True,
    )

    # Set layout
    app.layout = create_layout()

    # Register all callbacks
    register_all_callbacks(app)

    return app
