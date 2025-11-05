"""
Plasma Stability SEC Analysis App V2
Rebuilt with modular architecture

Features:
- Excel template-based workflow
- Multiple molecule support
- 3 peak detection modes
- Molecule structure images
- DBC card layout for each molecule
"""

from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc

from .layout import app_layout
from .callbacks import (
    register_upload_callbacks,
    register_settings_callbacks,
    register_analysis_callbacks,
    register_export_callbacks,
    register_sample_lookup_callbacks
)

# Create the Dash app
app = DjangoDash(
    "PlasmaStabilityAppV4",
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

# Set layout
app.layout = app_layout

# Register all callbacks
register_upload_callbacks(app)
register_settings_callbacks(app)
register_analysis_callbacks(app)
register_export_callbacks(app)
register_sample_lookup_callbacks(app)

print("Plasma Stability App V2 initialized successfully")
