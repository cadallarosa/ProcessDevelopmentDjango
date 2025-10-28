"""Callbacks package for PD Analytics Dashboard."""
from .analytics_table import register_analytics_callbacks


def register_all_callbacks(app):
    """Register all callbacks for the analytics dashboard."""
    register_analytics_callbacks(app)
