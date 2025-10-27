"""Callbacks for viewing and editing existing source materials."""
from dash import Input, Output, State, html, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from django.db import transaction

from plotly_integration.models import (
    LimsSourceMaterial,
    LimsSampleAnalysis,
    LimsDnAssignment,
    LimsSourceMaterialStep
)
from ..utils.data_helpers import (
    get_all_source_materials,
    get_all_dn_assignments,
    get_source_material_by_id,
    get_source_material_steps,
    get_pooled_sample_ids,
    get_samples_by_project_and_type
)


def register_view_edit_callbacks(app):
    """Register callbacks for view/edit functionality."""

    @app.callback(
        Output("sm-manage-table", "data"),
        Input("sm-manage-refresh", "n_clicks"),
        Input("sm-manage-project-filter", "value"),
        Input("sm-gen-tabs", "value"),
        prevent_initial_call=False
    )
    def load_sm_table(n_clicks, project_filter, active_tab):
        """Load source materials table with optional filters."""
        if active_tab != "manage-tab":
            raise PreventUpdate

        source_materials = get_all_source_materials(project_id=project_filter)
        return source_materials

    @app.callback(
        Output("sm-edit-modal", "is_open"),
        Output("sm-edit-header", "children"),
        Output("sm-edit-name", "value"),
        Output("sm-edit-ph", "value"),
        Output("sm-edit-conductivity", "value"),
        Output("sm-edit-concentration", "value"),
        Output("sm-edit-volume", "value"),
        Output("sm-edit-dn", "value"),
        Output("sm-edit-dn", "options"),
        Output("sm-edit-pooled-samples", "value"),
        Output("sm-edit-pooled-samples", "options"),
        Output("sm-edit-process-table", "data"),
        Output("sm-edit-pd-sample", "children"),
        Output("sm-edit-selected-id", "data"),
        Input("sm-manage-table", "selected_rows"),
        State("sm-manage-table", "data"),
        prevent_initial_call=True
    )
    def load_sm_for_edit(selected_rows, table_data):
        """Load selected source material into edit modal."""
        if not selected_rows or not table_data:
            # Close modal
            return False, "", None, None, None, None, None, None, [], [], [], [], "", None

        selected_row = table_data[selected_rows[0]]
        sm_id = selected_row["sm_id"]

        # Load full SM from database
        sm = get_source_material_by_id(sm_id)
        if not sm:
            return False, "", None, None, None, None, None, None, [], [], [], [], "", None

        # Get DN options
        dn_options = get_all_dn_assignments(project_id=sm.project_id)

        # Get current DN value
        dn_value = sm.resulting_sample.dn.dn if sm.resulting_sample and sm.resulting_sample.dn else None

        # Get pooled samples
        pooled_sample_ids = get_pooled_sample_ids(sm_id)

        # Get all available samples for project (PD type most common for pooling)
        all_samples = get_samples_by_project_and_type(sm.project_id or "", 3)
        sample_options = [
            {
                "label": f"{s.sample_id} - {s.description or 'No desc'}",
                "value": s.sample_id
            }
            for s in all_samples
        ]

        # Get process steps
        steps = get_source_material_steps(sm_id)
        if not steps:
            steps = [{"step": 1, "process": "", "notes": ""}]

        # Resulting PD sample
        pd_sample_display = sm.resulting_sample.sample_id if sm.resulting_sample else "N/A"

        return (
            True,  # Open modal
            f"Edit Source Material: SM{sm_id}",
            sm.name,
            sm.final_pH,
            sm.final_conductivity,
            sm.final_concentration,
            sm.final_total_volume,
            dn_value,
            dn_options,
            pooled_sample_ids,
            sample_options,
            steps,
            pd_sample_display,
            sm_id  # Store selected SM ID
        )

    @app.callback(
        Output("sm-edit-process-table", "data", allow_duplicate=True),
        Input("sm-edit-add-step", "n_clicks"),
        State("sm-edit-process-table", "data"),
        prevent_initial_call=True
    )
    def add_process_step_edit(n_clicks, current_data):
        """Add new process step in edit mode."""
        if not current_data:
            current_data = []

        next_step = len(current_data) + 1
        current_data.append({
            "step": next_step,
            "process": "",
            "notes": ""
        })
        return current_data

    @app.callback(
        Output("sm-edit-alert", "children"),
        Output("sm-manage-table", "data", allow_duplicate=True),
        Output("sm-edit-modal", "is_open", allow_duplicate=True),
        Output("sm-manage-table", "selected_rows", allow_duplicate=True),
        Input("sm-edit-save", "n_clicks"),
        State("sm-edit-selected-id", "data"),
        State("sm-edit-name", "value"),
        State("sm-edit-ph", "value"),
        State("sm-edit-conductivity", "value"),
        State("sm-edit-concentration", "value"),
        State("sm-edit-volume", "value"),
        State("sm-edit-dn", "value"),
        State("sm-edit-pooled-samples", "value"),
        State("sm-edit-process-table", "data"),
        State("sm-manage-project-filter", "value"),
        prevent_initial_call=True
    )
    def save_edited_sm(
        n_clicks,
        sm_id,
        name,
        ph,
        conductivity,
        concentration,
        volume,
        dn_value,
        pooled_samples,
        process_steps,
        project_filter
    ):
        """Save changes to existing source material."""
        if not sm_id:
            return no_update, no_update, no_update, no_update

        try:
            with transaction.atomic():
                # Get SM
                sm = LimsSourceMaterial.objects.get(sm_id=sm_id)

                # Update basic fields
                sm.name = name
                sm.final_pH = ph
                sm.final_conductivity = conductivity
                sm.final_concentration = concentration
                sm.final_total_volume = volume
                sm.save()

                # Update DN link
                if dn_value:
                    dn_obj = LimsDnAssignment.objects.get(dn=dn_value)
                    if sm.resulting_sample:
                        sm.resulting_sample.dn = dn_obj
                        sm.resulting_sample.save()
                    # Also update DN's source_material link
                    dn_obj.source_material = sm
                    dn_obj.save()
                else:
                    # Unlink DN
                    if sm.resulting_sample:
                        sm.resulting_sample.dn = None
                        sm.resulting_sample.save()

                # Update pooled samples
                if pooled_samples:
                    linked_samples = LimsSampleAnalysis.objects.filter(
                        sample_id__in=pooled_samples
                    )
                    sm.samples.set(linked_samples)
                else:
                    sm.samples.clear()

                # Update process steps
                LimsSourceMaterialStep.objects.filter(source_material=sm).delete()
                for i, step in enumerate(process_steps or [], start=1):
                    process = step.get("process", "").strip()
                    notes = step.get("notes", "").strip()
                    if process:
                        LimsSourceMaterialStep.objects.create(
                            source_material=sm,
                            step_number=i,
                            process=process,
                            notes=notes
                        )

                # Success - refresh table and close modal
                alert = dbc.Alert(
                    [html.I(className="bi bi-check-circle me-2"), f"SM{sm_id} updated successfully!"],
                    color="success",
                    dismissable=True,
                    duration=3000
                )

                updated_table = get_all_source_materials(project_id=project_filter)

                return alert, updated_table, False, []  # Close modal, clear selection

        except Exception as e:
            alert = dbc.Alert(
                [html.I(className="bi bi-exclamation-triangle me-2"), f"Error: {str(e)}"],
                color="danger",
                dismissable=True
            )
            return alert, no_update, no_update, no_update

    @app.callback(
        Output("sm-edit-modal", "is_open", allow_duplicate=True),
        Output("sm-manage-table", "selected_rows", allow_duplicate=True),
        Input("sm-edit-cancel", "n_clicks"),
        prevent_initial_call=True
    )
    def cancel_edit(n_clicks):
        """Cancel editing and close modal."""
        return False, []
