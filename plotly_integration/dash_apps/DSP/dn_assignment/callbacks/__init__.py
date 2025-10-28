"""Callbacks for DN Assignment app."""
from .dn_table import register_dn_table_callbacks
from .modal_workflows import register_modal_callbacks


def register_all_callbacks(app):
    """Register all callbacks for the DN Assignment app."""
    register_dn_table_callbacks(app)
    register_modal_callbacks(app)
