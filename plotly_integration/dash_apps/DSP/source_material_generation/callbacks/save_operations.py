"""Callbacks for saving and updating source materials with validation."""
from datetime import datetime
from dash import Input, Output, State, html, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from django.db import transaction

from plotly_integration.models import (
    LimsSourceMaterial,
    LimsSampleAnalysis,
    LimsSourceMaterialStep
)
from ..utils.data_helpers import get_next_pd_number, get_next_dn_number


def register_save_callbacks(app):
    """Register callbacks for save operations."""

    @app.callback(
        Output("sm-gen-alert-container", "children"),
        Output("sm-gen-overwrite-modal", "is_open"),
        Output("sm-gen-modal-body", "children"),
        Input("sm-gen-save-btn", "n_clicks"),
        Input("sm-gen-confirm-overwrite", "n_clicks"),
        Input("sm-gen-cancel-overwrite", "n_clicks"),
        State("sm-gen-overwrite-modal", "is_open"),
        State("sm-gen-mode", "value"),
        State("sm-gen-project-id", "value"),
        State("sm-gen-existing-dropdown", "value"),
        State("sm-gen-name", "value"),
        State("sm-gen-final-ph", "value"),
        State("sm-gen-final-conductivity", "value"),
        State("sm-gen-final-concentration", "value"),
        State("sm-gen-final-volume", "value"),
        State("sm-gen-pooled-samples", "value"),
        State("sm-gen-process-table", "data"),
        prevent_initial_call=True
    )
    def save_source_material(
        save_clicks,
        confirm_clicks,
        cancel_clicks,
        modal_open,
        mode,
        project_id,
        existing_sm_id,
        name,
        final_ph,
        final_cond,
        final_conc,
        final_vol,
        pooled_samples,
        step_table_data
    ):
        """
        Save or update source material with validation.

        Handles:
        - Creating new source materials
        - Updating existing source materials
        - Validation and confirmation modals
        - Auto-generating PD samples
        """
        from dash import callback_context

        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Handle cancel button
        if triggered_id == "sm-gen-cancel-overwrite":
            return no_update, False, no_update

        # Validation
        if not project_id or not project_id.strip():
            return create_error_alert("Project ID is required"), False, no_update

        if not name or not name.strip():
            return create_error_alert("Source Material Name is required"), False, no_update

        # Determine SM ID
        if mode == "existing" and existing_sm_id:
            sm_id = existing_sm_id
            existing_sm = LimsSourceMaterial.objects.filter(sm_id=sm_id).first()
        else:
            # For new SM, use next available ID (could be based on DN or auto-increment)
            # For now, using auto-increment based on max SM ID
            last_sm = LimsSourceMaterial.objects.order_by("-sm_id").first()
            sm_id = (last_sm.sm_id + 1) if last_sm else 1
            existing_sm = None

        # Check if changes detected for existing SM
        if existing_sm and triggered_id == "sm-gen-save-btn":
            if has_changes(
                existing_sm,
                name,
                final_ph,
                final_cond,
                final_conc,
                final_vol,
                pooled_samples,
                step_table_data
            ):
                modal_message = (
                    f"Changes detected in SM{sm_id}. "
                    "Do you want to overwrite the existing Source Material?"
                )
                return no_update, True, modal_message

        # Proceed with save (either new or confirmed overwrite)
        if triggered_id in ("sm-gen-save-btn", "sm-gen-confirm-overwrite"):
            try:
                with transaction.atomic():
                    # Create or update source material
                    if existing_sm:
                        sm = existing_sm
                        sm.name = name
                        sm.final_pH = final_ph
                        sm.final_conductivity = final_cond
                        sm.final_concentration = final_conc
                        sm.final_total_volume = final_vol
                        sm.project_id = project_id
                        sm.save()
                        action = "updated"
                    else:
                        # Step 1: Create DN experiment first (type "SMG")
                        next_dn = get_next_dn_number()

                        dn_record = LimsDnAssignment.objects.create(
                            dn=next_dn,
                            project_id=project_id,
                            unit_operation="SMG",  # Source Material Generation
                            study_name=f"Source Material: {name}",
                            scouting_details=f"Generated SM{sm_id}",
                            status="Completed",
                            notes=f"Auto-generated for source material {name}"
                        )

                        # Step 2: Create new PD sample linked to DN
                        next_pd_num = get_next_pd_number()
                        pd_id = f"PD{next_pd_num}"

                        pd_sample = LimsSampleAnalysis.objects.create(
                            sample_id=pd_id,
                            sample_type=3,  # PD
                            sample_date=datetime.today().date(),
                            project_id=project_id,
                            description=f"SM{sm_id}-{name}",
                            analyst="",
                            status="in_progress",
                            dn=dn_record  # Link PD to DN
                        )

                        # Step 3: Create source material
                        sm = LimsSourceMaterial.objects.create(
                            sm_id=sm_id,
                            name=name,
                            final_pH=final_ph,
                            final_conductivity=final_cond,
                            final_concentration=final_conc,
                            final_total_volume=final_vol,
                            project_id=project_id,
                            resulting_sample=pd_sample
                        )

                        # Step 4: Link SM to DN
                        dn_record.source_material = sm
                        dn_record.save()

                        action = "created"

                    # Link pooled samples
                    if pooled_samples:
                        linked_samples = LimsSampleAnalysis.objects.filter(
                            sample_id__in=pooled_samples
                        )
                        sm.samples.set(linked_samples)

                    # Save process steps
                    LimsSourceMaterialStep.objects.filter(source_material=sm).delete()
                    for i, step in enumerate(step_table_data or [], start=1):
                        process = step.get("process", "").strip()
                        notes = step.get("notes", "").strip()
                        if process:
                            LimsSourceMaterialStep.objects.create(
                                source_material=sm,
                                step_number=i,
                                process=process,
                                notes=notes
                            )

                    # Success message
                    result_sample = (
                        sm.resulting_sample.sample_id
                        if sm.resulting_sample
                        else "N/A"
                    )

                    # Include DN info if created
                    if action == "created" and 'dn_record' in locals():
                        alert = create_success_alert(
                            f"✅ Source Material SM{sm.sm_id} successfully {action}! "
                            f"DN{dn_record.dn} created. "
                            f"Resulting sample: {result_sample}"
                        )
                    else:
                        alert = create_success_alert(
                            f"Source Material SM{sm.sm_id} successfully {action}! "
                            f"Resulting sample: {result_sample}"
                        )

                    return alert, False, no_update

            except Exception as e:
                return create_error_alert(f"Error saving: {str(e)}"), False, no_update

        raise PreventUpdate


def has_changes(
    sm: LimsSourceMaterial,
    name: str,
    final_ph: float,
    final_cond: float,
    final_conc: float,
    final_vol: float,
    pooled_samples: list,
    step_table_data: list
) -> bool:
    """
    Check if there are changes compared to existing SM.

    Returns:
        True if changes detected, False otherwise
    """
    # Check basic fields
    if (sm.name != name or
        sm.final_pH != final_ph or
        sm.final_conductivity != final_cond or
        sm.final_concentration != final_conc or
        sm.final_total_volume != final_vol):
        return True

    # Check pooled samples
    current_samples = set(sm.samples.values_list("sample_id", flat=True))
    if set(pooled_samples or []) != current_samples:
        return True

    # Check process steps
    existing_steps = list(
        LimsSourceMaterialStep.objects.filter(source_material=sm)
        .order_by("step_number")
        .values("process", "notes")
    )

    incoming_steps = [
        {"process": s["process"].strip(), "notes": s.get("notes", "").strip()}
        for s in (step_table_data or [])
        if s.get("process", "").strip()
    ]

    return existing_steps != incoming_steps


def create_success_alert(message: str):
    """Create a success alert component."""
    return dbc.Alert(
        [html.I(className="bi bi-check-circle me-2"), message],
        color="success",
        dismissable=True,
        duration=4000
    )


def create_error_alert(message: str):
    """Create an error alert component."""
    return dbc.Alert(
        [html.I(className="bi bi-exclamation-triangle me-2"), message],
        color="danger",
        dismissable=True
    )
