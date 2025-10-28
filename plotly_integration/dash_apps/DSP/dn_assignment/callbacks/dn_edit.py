"""Callbacks for single DN editing."""
from dash import Input, Output, State
from dash.exceptions import PreventUpdate
from django.contrib.auth.models import User
from plotly_integration.models import LimsDnAssignment
import pandas as pd


def register_dn_edit_callbacks(app):
    """Register callbacks for single DN edit functionality."""

    @app.callback(
        Output("edit-dn-table", "data"),
        Input("refresh-edit-dn", "n_clicks"),
        Input("dn-tabs", "value"),
        State("dn-context", "data"),
        prevent_initial_call=False
    )
    def load_dn_for_edit(n_clicks, active_tab, dn_context):
        """Load DN data into edit table when Edit DN tab is opened."""
        if active_tab != "edit-dn-tab" or not dn_context or "dn" not in dn_context:
            raise PreventUpdate

        dn_val = dn_context["dn"]
        dn_obj = LimsDnAssignment.objects.filter(dn=dn_val).first()

        if not dn_obj:
            return []

        # Build row data
        row = {
            "dn": dn_obj.dn,
            "project_id": dn_obj.project_id or "",
            "unit_operation": dn_obj.unit_operation or "",
            "scouting_details": dn_obj.scouting_details or "",
            "created_by": dn_obj.created_by.username if dn_obj.created_by else "",
            "assigned_to": dn_obj.assigned_to.username if dn_obj.assigned_to else "",
            "notes": dn_obj.notes or "",
            "status": dn_obj.status or "Pending"
        }

        return [row]

    @app.callback(
        Output("save-edit-dn", "children"),
        Input("save-edit-dn", "n_clicks"),
        State("edit-dn-table", "data"),
        prevent_initial_call=True
    )
    def save_edit_dn_changes(n_clicks, table_data):
        """Save changes to DN from edit table."""
        if not table_data:
            raise PreventUpdate

        updated = 0
        for row in table_data:
            dn_value = row.get("dn")
            if not dn_value:
                continue

            # Resolve ForeignKeys (set to None if not valid)
            assigned_user = User.objects.filter(username=row.get("assigned_to")).first()
            created_user = User.objects.filter(username=row.get("created_by")).first()

            _, created = LimsDnAssignment.objects.update_or_create(
                dn=dn_value,
                defaults={
                    "project_id": row.get("project_id", ""),
                    "scouting_details": row.get("scouting_details"),
                    "assigned_to": assigned_user,
                    "created_by": created_user,
                    "unit_operation": row.get("unit_operation", ""),
                    "notes": row.get("notes", ""),
                    "status": row.get("status", "Pending")
                }
            )
            updated += 1

        return f"✅ {updated} DNs saved"
