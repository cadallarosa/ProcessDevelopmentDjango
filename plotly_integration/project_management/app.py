"""
Project Management Dashboard - Main Application File

A comprehensive Dash application for managing protein engineering projects,
replacing Excel-based tracking with a database-backed solution.

Features:
- Project tracking with status, priority, and timeline management
- Automated scoring and recommendation engine
- Interactive Gantt charts and priority matrix
- Decision history tracking and audit trail
- Excel import/export capabilities
- Real-time analytics and reporting
"""
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc

from .layout import create_layout
from .callbacks import register_all_callbacks
from .config import APP_NAME, APP_TITLE


# ========================================
# Create Dash App
# ========================================

app = DjangoDash(
    name=APP_NAME,
    external_stylesheets=[
        dbc.themes.FLATLY,  # Bootstrap theme
        dbc.icons.BOOTSTRAP,  # Bootstrap icons
    ],
    suppress_callback_exceptions=True,  # Required for dynamic callbacks
    title=APP_TITLE,
)

# Set the app layout
app.layout = create_layout()

# Register all callbacks
register_all_callbacks(app)

# ========================================
# Application Info
# ========================================

print("=" * 70)
print(f"  {APP_TITLE}")
print("=" * 70)
print(f"  App Name: {APP_NAME}")
print(f"  Status: Initialized")
print(f"  Callbacks: Registered")
print("=" * 70)
print("\nTo access this app:")
print("  1. Ensure Django server is running")
print("  2. Navigate to: /django_plotly_dash/{APP_NAME}/")
print("=" * 70)
