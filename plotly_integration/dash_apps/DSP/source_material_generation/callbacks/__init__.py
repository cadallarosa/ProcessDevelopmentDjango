"""Callbacks for Source Material Generation app."""
from .mode_toggle import register_mode_callbacks
from .sample_selection import register_sample_callbacks
from .process_steps import register_process_callbacks
from .save_operations import register_save_callbacks
from .view_edit import register_view_edit_callbacks


def register_all_callbacks(app):
    """Register all callbacks for the app."""
    register_mode_callbacks(app)
    register_sample_callbacks(app)
    register_process_callbacks(app)
    register_save_callbacks(app)
    register_view_edit_callbacks(app)
