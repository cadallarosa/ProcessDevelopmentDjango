"""Callbacks for bulk DN creation."""
from dash import Input, Output, State
from dash.exceptions import PreventUpdate
from django.contrib.auth.models import User
from plotly_integration.models import LimsDnAssignment
from ..components.tables import COLUMN_ORDER


def register_dn_create_callbacks(app):
    """Register callbacks for bulk DN creation functionality."""

    @app.callback(
        Output("dn-bulk-table", "data"),
        Input("add-row-btn", "n_clicks_timestamp"),
        Input("clear-dn-btn", "n_clicks_timestamp"),
        State("dn-bulk-table", "data"),
        prevent_initial_call=True
    )
    def modify_bulk_table(add_ts, clear_ts, current_data):
        """Add or clear rows in the bulk DN creation table."""
        if current_data is None:
            current_data = []

        timestamps = {
            "add": add_ts or 0,
            "clear": clear_ts or 0,
        }
        latest_action = max(timestamps, key=timestamps.get)

        if latest_action == "clear":
            return [{key: "" for key, _ in COLUMN_ORDER if key not in ("date_created", "date_updated", "id")}]

        if latest_action == "add":
            current_data.append({key: "" for key, _ in COLUMN_ORDER if key not in ("date_created", "date_updated", "id")})
            return current_data

        raise PreventUpdate

    @app.callback(
        Output("save_status", "children"),
        Output("dn-bulk-table", "data", allow_duplicate=True),
        Input("save_button", "n_clicks"),
        State("dn-bulk-table", "data"),
        prevent_initial_call=True
    )
    def save_or_update_dn(n_clicks, bulk_data):
        """Save or update DN experiments from bulk table."""
        if not bulk_data:
            raise PreventUpdate

        # Get the most recent DN number in the DB
        last = LimsDnAssignment.objects.order_by("-dn").first()
        next_dn = last.dn if last and isinstance(last.dn, int) else 0

        created = 0
        updated_data = []

        for row in bulk_data:
            # Generate new DN number only if not already present
            if not row.get("dn"):
                next_dn += 1
                row["dn"] = next_dn
            else:
                try:
                    row["dn"] = int(row["dn"])
                except ValueError:
                    continue  # skip non-integer DN

            try:
                assigned_user = User.objects.filter(username=row.get("assigned_to", "")).first()
                created_user = User.objects.filter(username=row.get("created_by", "")).first()

                LimsDnAssignment.objects.update_or_create(
                    dn=row["dn"],
                    defaults={
                        "project_id": row.get("project_id", ""),
                        "study_name": row.get("study_name", ""),
                        "scouting_details": row.get("scouting_details", ""),
                        "assigned_to": assigned_user,
                        "created_by": created_user,
                        "unit_operation": row.get("unit_operation", ""),
                        "notes": row.get("notes", ""),
                        "status": row.get("status", "Pending")
                    }
                )
                created += 1
                updated_data.append(row)
            except Exception as e:
                print(f"❌ Error processing DN row: {e}")

        return f"✅ Created/Updated: {created}", updated_data
