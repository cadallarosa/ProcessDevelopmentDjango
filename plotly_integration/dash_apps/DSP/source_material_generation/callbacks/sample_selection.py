"""Callbacks for sample pooling and selection."""
from dash import Input, Output, State
from dash.exceptions import PreventUpdate
from ..utils.data_helpers import (
    get_samples_by_project_and_type,
    get_pooled_sample_ids,
    format_sample_dropdown_label
)


def register_sample_callbacks(app):
    """Register callbacks for sample selection and pooling."""

    @app.callback(
        Output("sm-gen-pooled-samples", "options"),
        Output("sm-gen-pooled-samples", "value"),
        Input("sm-gen-project-id", "value"),
        Input("sm-gen-sample-type", "value"),
        Input("sm-gen-existing-dropdown", "value"),
        State("sm-gen-mode", "value"),
        prevent_initial_call=True
    )
    def populate_pooled_samples_dropdown(project_id, sample_type, sm_id, mode):
        """
        Populate available samples based on project and type.

        If in 'existing' mode and SM selected, pre-populate with pooled samples.
        """
        if not project_id or not project_id.strip():
            return [], []

        # Get all samples matching project and type
        samples = get_samples_by_project_and_type(project_id, sample_type)

        options = [
            {
                "label": format_sample_dropdown_label(sample),
                "value": sample.sample_id
            }
            for sample in samples
        ]

        # Pre-populate with existing pooled samples if in existing mode
        selected_values = []
        if mode == "existing" and sm_id:
            selected_values = get_pooled_sample_ids(sm_id)

        return options, selected_values
