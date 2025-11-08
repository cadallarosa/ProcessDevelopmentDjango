"""
Plasma Stability SEC Analysis App V4
Enhanced with automated summary generation

Features:
- Excel template-based workflow with Summary Config sheet
- Starting material tracking (unpurified samples)
- Automated metric calculations and stability classification
- Auto-populated PowerPoint summary slides
- User-defined slide organization
- Multiple molecule support with purified/unpurified separation
- 3 peak detection modes
- Molecule structure images and rankings
"""

from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc

from .layout import app_layout
from .callbacks import (
    register_upload_callbacks,
    register_settings_callbacks,
    register_analysis_callbacks,
    register_export_callbacks,
    register_sample_lookup_callbacks,
    register_summary_tables_callbacks
)

# Create the Dash app
app = DjangoDash(
    "PlasmaStabilityAppV5",
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
register_summary_tables_callbacks(app)

print("✓ Plasma Stability App V4 initialized successfully")
print("  → Route: /dash/PlasmaStabilityAppV4/")
print("  → Features: Automated summary generation with starting material tracking")
