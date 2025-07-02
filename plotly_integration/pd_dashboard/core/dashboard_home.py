# plotly_integration/pd_dashboard/core/dashboard_home.py
# Minimal version - just import from layout_manager

from .layout_manager import (
    create_dashboard_layout,
    create_settings_layout
)

from .sidebar_navigation import create_sidebar_navigation

# Re-export functions for backward compatibility
__all__ = [
    'create_dashboard_layout',
    'create_settings_layout',
    'create_sidebar_navigation'
]