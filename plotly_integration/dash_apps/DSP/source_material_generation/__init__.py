"""
Source Material Generation App

Import this module to register the Dash app with Django.

Usage in urls.py or views.py:
    from plotly_integration.dash_apps.DSP.source_material_generation import app
"""
from .app import app

__all__ = ["app"]
