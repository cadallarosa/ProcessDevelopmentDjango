"""Callbacks for mode toggling between existing and new source materials."""
from dash import Input, Output, State
from dash.exceptions import PreventUpdate
from ..utils.data_helpers import (
    get_source_materials_by_project,
    get_source_material_by_id,
    format_sm_dropdown_label,
    get_all_project_ids
)


def register_mode_callbacks(app):
    """Register callbacks for mode switching."""

    @app.callback(
        Output("sm-gen-project-id", "options"),
        Input("sm-gen-mode", "value"),
        prevent_initial_call=False
    )
    def populate_project_id_dropdown(mode):
        """Populate project ID dropdown with existing projects."""
        project_ids = get_all_project_ids()
        return [{"label": pid, "value": pid} for pid in project_ids]

    @app.callback(
        Output("sm-gen-existing-section", "style"),
        Input("sm-gen-mode", "value"),
        prevent_initial_call=False
    )
    def toggle_existing_section(mode):
        """Show/hide existing SM dropdown based on mode."""
        if mode == "existing":
            return {"display": "block"}
        return {"display": "none"}

    @app.callback(
        Output("sm-gen-existing-dropdown", "options"),
        Input("sm-gen-project-id", "value"),
        prevent_initial_call=True
    )
    def populate_existing_sm_dropdown(project_id):
        """Populate existing source materials dropdown for the project."""
        if not project_id or not project_id.strip():
            return []

        source_materials = get_source_materials_by_project(project_id)

        return [
            {
                "label": format_sm_dropdown_label(sm),
                "value": sm.sm_id
            }
            for sm in source_materials
        ]

    @app.callback(
        Output("sm-gen-name", "value"),
        Output("sm-gen-final-ph", "value"),
        Output("sm-gen-final-conductivity", "value"),
        Output("sm-gen-final-concentration", "value"),
        Output("sm-gen-final-volume", "value"),
        Output("sm-gen-result-sample-id", "children"),
        Input("sm-gen-existing-dropdown", "value"),
        Input("sm-gen-mode", "value"),
        prevent_initial_call=True
    )
    def load_existing_sm_data(sm_id, mode):
        """
        Load existing source material data when selected.

        Returns all field values to populate the form.
        """
        # Clear fields when switching to new mode
        if mode == "new":
            return None, None, None, None, None, "Will be auto-generated"

        # Load existing SM data
        if mode == "existing" and sm_id:
            sm = get_source_material_by_id(sm_id)
            if sm:
                result_sample_id = (
                    sm.resulting_sample.sample_id
                    if sm.resulting_sample
                    else "Not assigned"
                )

                return (
                    sm.name,
                    sm.final_pH,
                    sm.final_conductivity,
                    sm.final_concentration,
                    sm.final_total_volume,
                    result_sample_id
                )

        raise PreventUpdate
