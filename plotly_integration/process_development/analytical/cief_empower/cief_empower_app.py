"""
cIEF Empower Analysis App
=========================

This app provides a comprehensive interface for analyzing cIEF (Capillary Isoelectric Focusing) 
data from Empower, including:

1. pI marker configuration and linear regression
2. Peak detection and analysis
3. Peak-to-pI correlation
4. Data visualization and reporting

Usage:
------
To use this app in Django views:

    from plotly_integration.process_development.analytical.cief_empower import app
    
The app is automatically registered as "CiefEmpowerApp" and can be embedded in templates.
"""

from .app import app

__all__ = ['app']