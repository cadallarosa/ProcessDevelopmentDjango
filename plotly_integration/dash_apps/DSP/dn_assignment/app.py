"""DN Assignment App - Modular Architecture.

This app manages DN (Downstream) experiment assignments, PD sample tracking,
and related LIMS functionality.

Features:
- View and filter DN experiments
- Create bulk DN experiments
- Edit individual DN experiments
- Manage PD samples (create, view, edit)
- Link DN experiments to samples

Architecture:
- Separated into logical modules (callbacks, components, utils, layout)
- Clean separation of concerns
- Consistent with Source Material Generation app design
"""
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc

from .layout import create_layout, register_user_options_callback
from .callbacks import register_all_callbacks

# Create the Dash app with Bootstrap theme and icons
app = DjangoDash(
    "DnAssignmentAppModular",
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.BOOTSTRAP
    ],
    suppress_callback_exceptions=True
)

# Set the layout
app.layout = create_layout()

# Register layout callbacks
register_user_options_callback(app)

# Register all feature callbacks
register_all_callbacks(app)
