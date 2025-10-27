"""
Source Material Generation App

A modern, standalone Dash application for creating and managing source materials
in downstream processing experiments.

Features:
- Create new source materials or use existing ones
- Pool multiple samples together
- Track process steps
- Auto-generate resulting PD samples
- Validation and confirmation modals

URL: /django_plotly_dash/app/SourceMaterialGenerationApp/
"""
import dash_bootstrap_components as dbc
from django_plotly_dash import DjangoDash

from .layout import create_layout
from .callbacks import register_all_callbacks


# Initialize the app with Bootstrap theme
app = DjangoDash(
    "SourceMaterialGenerationApp",
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.BOOTSTRAP  # For icons
    ],
    suppress_callback_exceptions=True
)

# Set layout
app.layout = create_layout()

# Register all callbacks
register_all_callbacks(app)
