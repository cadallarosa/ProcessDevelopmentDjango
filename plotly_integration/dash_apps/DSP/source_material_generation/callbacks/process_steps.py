"""Callbacks for process steps table management."""
from dash import Input, Output, State
from dash.exceptions import PreventUpdate
from ..utils.data_helpers import get_source_material_steps
from ..components.tables import create_process_steps_table


def register_process_callbacks(app):
    """Register callbacks for process steps table."""

    @app.callback(
        Output("sm-gen-process-table-container", "children"),
        Input("sm-gen-add-step", "n_clicks"),
        Input("sm-gen-existing-dropdown", "value"),
        State("sm-gen-mode", "value"),
        State("sm-gen-process-table-container", "children"),
        prevent_initial_call=False
    )
    def update_process_steps_container(n_clicks, sm_id, mode, current_container):
        """
        Handle process steps table updates in a container.

        - Add new step when button clicked
        - Load existing steps when SM selected
        - Render table in container to fix dropdown issues
        """
        from dash import callback_context

        ctx = callback_context
        if not ctx.triggered:
            # Initial load
            table = create_process_steps_table(
                table_id="sm-gen-process-table",
                data=[{"step": 1, "process": "", "notes": ""}]
            )
            return table

        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Get current table data from container if it exists
        current_data = [{"step": 1, "process": "", "notes": ""}]
        if current_container and hasattr(current_container, 'data'):
            current_data = current_container.data or current_data

        # Load steps from existing SM
        if triggered_id == "sm-gen-existing-dropdown" and mode == "existing" and sm_id:
            steps = get_source_material_steps(sm_id)
            data = steps if steps else [{"step": 1, "process": "", "notes": ""}]
            table = create_process_steps_table(table_id="sm-gen-process-table", data=data)
            return table

        # Reset to blank when switching to new mode
        if triggered_id == "sm-gen-existing-dropdown" and mode == "new":
            table = create_process_steps_table(
                table_id="sm-gen-process-table",
                data=[{"step": 1, "process": "", "notes": ""}]
            )
            return table

        # Add new step
        if triggered_id == "sm-gen-add-step":
            # Try to extract data from current container
            if current_container:
                try:
                    if hasattr(current_container, 'data'):
                        current_data = current_container.data
                    elif isinstance(current_container, dict) and 'props' in current_container:
                        current_data = current_container['props'].get('data', current_data)
                except:
                    pass

            if not current_data:
                current_data = []

            next_step = len(current_data) + 1
            current_data.append({
                "step": next_step,
                "process": "",
                "notes": ""
            })

            table = create_process_steps_table(table_id="sm-gen-process-table", data=current_data)
            return table

        raise PreventUpdate
