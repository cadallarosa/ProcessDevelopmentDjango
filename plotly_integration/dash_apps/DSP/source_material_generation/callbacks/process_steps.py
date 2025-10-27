"""Callbacks for process steps table management."""
from dash import Input, Output, State
from dash.exceptions import PreventUpdate
from ..utils.data_helpers import get_source_material_steps


def register_process_callbacks(app):
    """Register callbacks for process steps table."""

    @app.callback(
        Output("sm-gen-process-table", "data"),
        Input("sm-gen-add-step", "n_clicks"),
        Input("sm-gen-existing-dropdown", "value"),
        State("sm-gen-mode", "value"),
        State("sm-gen-process-table", "data"),
        prevent_initial_call=True
    )
    def update_process_steps(n_clicks, sm_id, mode, current_data):
        """
        Handle process steps table updates.

        - Add new step when button clicked
        - Load existing steps when SM selected
        """
        from dash import callback_context

        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Load steps from existing SM
        if triggered_id == "sm-gen-existing-dropdown" and mode == "existing" and sm_id:
            steps = get_source_material_steps(sm_id)
            return steps if steps else [{"step": 1, "process": "", "notes": ""}]

        # Reset to blank when switching to new mode
        if triggered_id == "sm-gen-existing-dropdown" and mode == "new":
            return [{"step": 1, "process": "", "notes": ""}]

        # Add new step
        if triggered_id == "sm-gen-add-step":
            if not current_data:
                current_data = []

            next_step = len(current_data) + 1
            current_data.append({
                "step": next_step,
                "process": "",
                "notes": ""
            })
            return current_data

        raise PreventUpdate
