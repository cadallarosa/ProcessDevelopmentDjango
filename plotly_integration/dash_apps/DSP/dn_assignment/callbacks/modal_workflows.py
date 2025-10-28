"""Callbacks for modal-based workflows (Edit and Create DN)."""
from dash import Input, Output, State, dash_table, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import html
from django.contrib.auth.models import User
from plotly_integration.models import LimsDnAssignment
from ..components.tables import COLUMN_ORDER


def register_modal_callbacks(app):
    """Register callbacks for modal workflows."""

    # ===== EDIT DN MODAL =====

    @app.callback(
        Output("edit-dn-modal", "is_open"),
        Output("edit-dn-modal-header", "children"),
        Output("edit-dn-number", "value"),
        Output("edit-dn-project", "value"),
        Output("edit-dn-unit-op", "value"),
        Output("edit-dn-status", "value"),
        Output("edit-dn-created-by", "value"),
        Output("edit-dn-assigned-to", "value"),
        Output("edit-dn-scouting", "value"),
        Output("edit-dn-notes", "value"),
        Output("edit-dn-input-vol", "value"),
        Output("edit-dn-input-conc", "value"),
        Output("edit-dn-output-vol", "value"),
        Output("edit-dn-output-conc", "value"),
        Output("dn-selected-id", "data"),
        Input("dn-table", "selected_rows"),
        State("dn-table", "data"),
        prevent_initial_call=True
    )
    def open_edit_modal(selected_rows, table_data):
        """Open edit modal when row is selected."""
        if not selected_rows or not table_data:
            return False, "", None, None, None, None, None, None, None, None, None, None, None, None, None

        row = table_data[selected_rows[0]]
        dn_value = row.get("dn")

        # Load DN from database
        dn_obj = LimsDnAssignment.objects.filter(dn=dn_value).first()
        if not dn_obj:
            return False, "", None, None, None, None, None, None, None, None, None, None, None, None, None

        return (
            True,  # Open modal
            f"Edit DN Experiment: DN{dn_value}",
            str(dn_obj.dn),
            dn_obj.project_id or "",
            dn_obj.unit_operation or "",
            dn_obj.status or "Pending",
            dn_obj.created_by.username if dn_obj.created_by else "",
            dn_obj.assigned_to.username if dn_obj.assigned_to else "",
            dn_obj.scouting_details or "",
            dn_obj.notes or "",
            dn_obj.input_volume if dn_obj.input_volume else "",
            dn_obj.input_concentration if dn_obj.input_concentration else "",
            dn_obj.output_volume if dn_obj.output_volume else "",
            dn_obj.output_concentration if dn_obj.output_concentration else "",
            dn_value  # Store DN ID
        )

    @app.callback(
        Output("edit-dn-alert", "children"),
        Output("dn-table", "data", allow_duplicate=True),
        Output("edit-dn-modal", "is_open", allow_duplicate=True),
        Output("dn-table", "selected_rows", allow_duplicate=True),
        Input("edit-dn-save", "n_clicks"),
        State("dn-selected-id", "data"),
        State("edit-dn-project", "value"),
        State("edit-dn-unit-op", "value"),
        State("edit-dn-status", "value"),
        State("edit-dn-created-by", "value"),
        State("edit-dn-assigned-to", "value"),
        State("edit-dn-scouting", "value"),
        State("edit-dn-notes", "value"),
        State("edit-dn-input-vol", "value"),
        State("edit-dn-input-conc", "value"),
        State("edit-dn-output-vol", "value"),
        State("edit-dn-output-conc", "value"),
        prevent_initial_call=True
    )
    def save_edit_dn(n_clicks, dn_id, project, unit_op, status, created_by, assigned_to, scouting, notes,
                     input_vol, input_conc, output_vol, output_conc):
        """Save changes to DN."""
        if not dn_id:
            raise PreventUpdate

        try:
            dn_obj = LimsDnAssignment.objects.get(dn=dn_id)

            # Update fields
            dn_obj.project_id = project or ""
            dn_obj.unit_operation = unit_op or ""
            dn_obj.status = status or "Pending"
            dn_obj.scouting_details = scouting or ""
            dn_obj.notes = notes or ""

            # Update mass balance fields
            dn_obj.input_volume = float(input_vol) if input_vol else None
            dn_obj.input_concentration = float(input_conc) if input_conc else None
            dn_obj.output_volume = float(output_vol) if output_vol else None
            dn_obj.output_concentration = float(output_conc) if output_conc else None

            # Update user assignments
            if created_by:
                user = User.objects.filter(username=created_by).first()
                dn_obj.created_by = user

            if assigned_to:
                user = User.objects.filter(username=assigned_to).first()
                dn_obj.assigned_to = user

            dn_obj.save()

            # Success alert
            alert = dbc.Alert(
                [html.I(className="bi bi-check-circle me-2"), f"DN{dn_id} updated successfully!"],
                color="success",
                dismissable=True,
                duration=3000
            )

            # Refresh table data
            from ..utils.data_helpers import get_all_dn_assignments
            updated_table = get_all_dn_assignments()

            return alert, updated_table, False, []  # Close modal, clear selection

        except Exception as e:
            alert = dbc.Alert(
                [html.I(className="bi bi-exclamation-triangle me-2"), f"Error: {str(e)}"],
                color="danger",
                dismissable=True
            )
            return alert, no_update, no_update, no_update

    @app.callback(
        Output("edit-dn-modal", "is_open", allow_duplicate=True),
        Output("dn-table", "selected_rows", allow_duplicate=True),
        Input("edit-dn-cancel", "n_clicks"),
        prevent_initial_call=True
    )
    def cancel_edit_dn(n_clicks):
        """Cancel editing and close modal."""
        return False, []

    # ===== CREATE DN MODAL =====

    @app.callback(
        Output("create-dn-modal", "is_open"),
        Output("create-dn-table-container", "children"),
        Input("open-create-dn-modal", "n_clicks"),
        prevent_initial_call=True
    )
    def open_create_modal(n_clicks):
        """Open create DN modal with empty table."""
        from ..components.tables import UNIT_OPS

        table = dash_table.DataTable(
            id="create-dn-table",
            columns=[
                {"name": label, "id": key, "editable": True, "presentation": "dropdown"}
                if key in ("created_by", "assigned_to", "unit_operation", "status")
                else {"name": label, "id": key, "editable": True}
                for key, label in COLUMN_ORDER
                if key not in ("dn", "date_created", "date_updated", "sm_id", "resulting_pd", "link")
            ],
            data=[{
                "project_id": "",
                "unit_operation": "",
                "scouting_details": "",
                "notes": "",
                "created_by": "",
                "assigned_to": "",
                "status": "Pending"
            }],
            editable=True,
            row_deletable=True,
            style_cell={
                "textAlign": "left",
                "padding": "12px",
                "fontSize": "13px",
                "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                "border": "1px solid #dee2e6",
            },
            style_header={
                "backgroundColor": "#0d6efd",
                "fontWeight": "600",
                "color": "#ffffff",
                "textAlign": "left",
                "fontSize": "12px",
                "textTransform": "uppercase",
                "padding": "12px",
                "border": "1px solid #0a58ca",
            },
            style_data={
                "backgroundColor": "#ffffff",
                "border": "1px solid #dee2e6",
            },
            dropdown={
                "created_by": {"options": []},
                "assigned_to": {"options": []},
                "unit_operation": {
                    "options": [{"label": op, "value": op} for op in UNIT_OPS]
                },
                "status": {
                    "options": [
                        {"label": "Pending", "value": "Pending"},
                        {"label": "In Progress", "value": "In Progress"},
                        {"label": "Completed", "value": "Completed"},
                    ]
                }
            },
            dropdown_conditional=[
                {
                    "if": {"column_id": "unit_operation"},
                    "options": [{"label": op, "value": op} for op in UNIT_OPS]
                }
            ]
        )
        return True, table

    @app.callback(
        Output("create-dn-table", "data"),
        Input("add-dn-row-btn", "n_clicks"),
        Input("clear-dn-rows-btn", "n_clicks"),
        State("create-dn-table", "data"),
        prevent_initial_call=True
    )
    def modify_create_table(add_clicks, clear_clicks, current_data):
        """Add or clear rows in create table."""
        from dash import callback_context
        triggered = callback_context.triggered[0]["prop_id"].split(".")[0]

        if triggered == "clear-dn-rows-btn":
            return [{
                "project_id": "",
                "unit_operation": "",
                "scouting_details": "",
                "notes": "",
                "created_by": "",
                "assigned_to": "",
                "status": "Pending"
            }]

        if triggered == "add-dn-row-btn":
            current_data.append({
                "project_id": "",
                "unit_operation": "",
                "scouting_details": "",
                "notes": "",
                "created_by": "",
                "assigned_to": "",
                "status": "Pending"
            })
            return current_data

        raise PreventUpdate

    @app.callback(
        Output("create-dn-alert", "children"),
        Output("dn-table", "data", allow_duplicate=True),
        Output("create-dn-modal", "is_open", allow_duplicate=True),
        Output("create-dn-table", "data", allow_duplicate=True),
        Input("create-dn-save", "n_clicks"),
        State("create-dn-table", "data"),
        prevent_initial_call=True
    )
    def save_create_dn(n_clicks, table_data):
        """Create new DN experiments."""
        if not table_data:
            raise PreventUpdate

        # Get next DN number
        from ..utils.data_helpers import get_next_dn_number
        next_dn = get_next_dn_number()

        created = 0
        for row in table_data:
            next_dn += 1

            try:
                assigned_user = User.objects.filter(username=row.get("assigned_to", "")).first()
                created_user = User.objects.filter(username=row.get("created_by", "")).first()

                LimsDnAssignment.objects.create(
                    dn=next_dn,
                    project_id=row.get("project_id", ""),
                    unit_operation=row.get("unit_operation", ""),
                    scouting_details=row.get("scouting_details", ""),
                    notes=row.get("notes", ""),
                    assigned_to=assigned_user,
                    created_by=created_user,
                    status=row.get("status", "Pending")
                )
                created += 1
            except Exception as e:
                print(f"Error creating DN: {e}")

        # Success alert
        alert = dbc.Alert(
            [html.I(className="bi bi-check-circle me-2"), f"Created {created} DN experiment(s)!"],
            color="success",
            dismissable=True,
            duration=3000
        )

        # Refresh table
        from ..utils.data_helpers import get_all_dn_assignments
        updated_table = get_all_dn_assignments()

        # Reset create table
        empty_row = [{
            "project_id": "",
            "unit_operation": "",
            "scouting_details": "",
            "notes": "",
            "created_by": "",
            "assigned_to": "",
            "status": "Pending"
        }]

        return alert, updated_table, False, empty_row  # Close modal

    @app.callback(
        Output("create-dn-modal", "is_open", allow_duplicate=True),
        Input("create-dn-cancel", "n_clicks"),
        prevent_initial_call=True
    )
    def cancel_create_dn(n_clicks):
        """Cancel create and close modal."""
        return False

    @app.callback(
        Output("create-dn-table", "dropdown"),
        Input("create-dn-table", "data"),
        State("user-options", "data"),
        prevent_initial_call=False
    )
    def update_create_table_dropdowns(table_data, user_options):
        """Update user dropdowns in create table."""
        from ..components.tables import UNIT_OPS

        return {
            "created_by": {"options": user_options or []},
            "assigned_to": {"options": user_options or []},
            "unit_operation": {
                "options": [{"label": op, "value": op} for op in UNIT_OPS]
            },
            "status": {
                "options": [
                    {"label": "Pending", "value": "Pending"},
                    {"label": "In Progress", "value": "In Progress"},
                    {"label": "Completed", "value": "Completed"},
                ]
            }
        }

    # ===== MASS BALANCE CALCULATIONS =====

    @app.callback(
        Output("calc-input-protein", "children"),
        Output("calc-output-protein", "children"),
        Output("calc-yield", "children"),
        Output("calc-conc-factor", "children"),
        Input("edit-dn-input-vol", "value"),
        Input("edit-dn-input-conc", "value"),
        Input("edit-dn-output-vol", "value"),
        Input("edit-dn-output-conc", "value"),
        prevent_initial_call=False
    )
    def calculate_mass_balance(input_vol, input_conc, output_vol, output_conc):
        """Calculate mass balance metrics in real-time."""
        try:
            # Convert to float, default to 0 if empty
            in_vol = float(input_vol) if input_vol else 0
            in_conc = float(input_conc) if input_conc else 0
            out_vol = float(output_vol) if output_vol else 0
            out_conc = float(output_conc) if output_conc else 0

            # Calculate input and output protein
            input_protein = in_vol * in_conc
            output_protein = out_vol * out_conc

            # Calculate yield
            if input_protein > 0:
                yield_pct = (output_protein / input_protein) * 100
            else:
                yield_pct = 0

            # Calculate concentration factor
            if in_conc > 0:
                conc_factor = out_conc / in_conc
            else:
                conc_factor = 0

            return (
                f"{input_protein:.2f} mg",
                f"{output_protein:.2f} mg",
                f"{yield_pct:.1f}%",
                f"{conc_factor:.2f}x"
            )

        except (ValueError, TypeError):
            return "0.0 mg", "0.0 mg", "0.0%", "0.0x"
