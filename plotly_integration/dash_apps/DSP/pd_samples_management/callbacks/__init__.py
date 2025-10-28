"""Callbacks package for PD Samples Management app."""
from .samples_table import register_samples_table_callbacks
from .modal_workflows import register_modal_callbacks


def register_all_callbacks(app):
    """Register all callbacks for the PD Samples Management app."""
    register_samples_table_callbacks(app)
    register_modal_callbacks(app)
