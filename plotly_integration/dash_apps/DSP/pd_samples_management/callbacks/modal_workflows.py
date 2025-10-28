"""Callbacks for PD Samples modal workflows (Add and Edit)."""
from dash import Input, Output, State, html, dash_table, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from django.utils import timezone
from plotly_integration.models import LimsSampleAnalysis, LimsDnAssignment
from ..utils.data_helpers import get_pd_sample_by_id, get_next_pd_number, get_available_dns, get_sample_genealogy
from ..components import create_genealogy_flowchart


def register_modal_callbacks(app):
    """Register callbacks for modal workflows."""

    # ===========================
    # EDIT PD SAMPLE MODAL - OPEN
    # ===========================

    @app.callback(
        Output("edit-pd-modal", "is_open"),
        Output("edit-pd-modal-header", "children"),
        Output("edit-pd-number", "value"),
        Output("edit-pd-project", "value"),
        Output("edit-pd-dn", "options"),
        Output("edit-pd-dn", "value"),
        Output("edit-pd-status", "value"),
        Output("edit-pd-date", "value"),
        Output("edit-pd-a280", "value"),
        Output("edit-pd-analyst", "value"),
        Output("edit-pd-description", "value"),
        Output("edit-pd-notes", "value"),
        Output("pd-selected-id", "data"),
        Input("pd-samples-table", "selected_rows"),
        State("pd-samples-table", "data"),
        prevent_initial_call=True
    )
    def open_edit_modal(selected_rows, table_data):
        """Open edit modal when row is selected."""
        if not selected_rows or not table_data:
            return False, "", "", "", [], None, "", "", "", "", "", "", None

        row_idx = selected_rows[0]
        row_data = table_data[row_idx]
        sample_id = row_data.get("sample_id")

        # Get DN options
        dn_options = get_available_dns()

        # Load from database
        sample = get_pd_sample_by_id(sample_id)
        if not sample:
            return False, "", "", "", dn_options, None, "", "", "", "", "", "", None

        dn_value = sample.dn.dn if sample.dn else None

        return (
            True,  # is_open
            f"Edit {sample_id}",  # header
            sample_id,  # PD number (disabled)
            sample.project_id or "",  # project
            dn_options,  # DN options
            dn_value,  # DN value
            sample.status or "In Progress",  # status
            sample.sample_date.strftime("%Y-%m-%d") if sample.sample_date else "",  # date
            sample.a280_result if sample.a280_result else "",  # A280
            sample.analyst or "",  # analyst
            sample.description or "",  # description
            sample.notes or "",  # notes
            sample_id  # store selected ID
        )

    # ===========================
    # EDIT PD SAMPLE MODAL - SAVE
    # ===========================

    @app.callback(
        Output("edit-pd-alert", "children"),
        Output("pd-samples-table", "data", allow_duplicate=True),
        Output("edit-pd-modal", "is_open", allow_duplicate=True),
        Output("pd-samples-table", "selected_rows", allow_duplicate=True),
        Input("edit-pd-save", "n_clicks"),
        State("pd-selected-id", "data"),
        State("edit-pd-project", "value"),
        State("edit-pd-dn", "value"),
        State("edit-pd-status", "value"),
        State("edit-pd-date", "value"),
        State("edit-pd-a280", "value"),
        State("edit-pd-analyst", "value"),
        State("edit-pd-description", "value"),
        State("edit-pd-notes", "value"),
        prevent_initial_call=True
    )
    def save_edit_modal(
        n_clicks, selected_id, project_val, dn_val, status_val, date_val,
        a280_val, analyst_val, description_val, notes_val
    ):
        """Save changes to PD sample."""
        if not selected_id:
            raise PreventUpdate

        try:
            sample = get_pd_sample_by_id(selected_id)
            if not sample:
                raise PreventUpdate

            # Update fields
            sample.project_id = project_val or None
            sample.status = status_val or "In Progress"
            sample.description = description_val or None
            sample.notes = notes_val or None
            sample.analyst = analyst_val or None

            # Update DN if changed
            if dn_val:
                dn_obj = LimsDnAssignment.objects.filter(dn=dn_val).first()
                sample.dn = dn_obj
            else:
                sample.dn = None

            # Update date
            if date_val:
                sample.sample_date = date_val
            else:
                sample.sample_date = None

            # Update A280
            if a280_val:
                try:
                    sample.a280_result = float(a280_val)
                except (ValueError, TypeError):
                    sample.a280_result = None
            else:
                sample.a280_result = None

            sample.save()

            alert = dbc.Alert(f"Successfully saved changes to {selected_id}", color="success", dismissable=True, duration=3000)
            return alert, no_update, False, []

        except Exception as e:
            print(f"Error saving PD sample: {e}")
            alert = dbc.Alert(f"Error saving: {str(e)}", color="danger", dismissable=True)
            return alert, no_update, True, no_update

    # ===========================
    # EDIT PD SAMPLE MODAL - CANCEL
    # ===========================

    @app.callback(
        Output("edit-pd-modal", "is_open", allow_duplicate=True),
        Output("pd-samples-table", "selected_rows", allow_duplicate=True),
        Input("edit-pd-cancel", "n_clicks"),
        prevent_initial_call=True
    )
    def cancel_edit_modal(n_clicks):
        """Close edit modal without saving."""
        return False, []

    # ===========================
    # GENEALOGY TAB - POPULATE
    # ===========================

    @app.callback(
        Output("genealogy-container", "children"),
        Input("edit-modal-tabs", "active_tab"),
        State("pd-selected-id", "data"),
        prevent_initial_call=True
    )
    def load_genealogy(active_tab, sample_id):
        """Load genealogy flowchart when tab is clicked."""
        if active_tab != "genealogy-tab" or not sample_id:
            raise PreventUpdate

        # Get genealogy data
        genealogy_data = get_sample_genealogy(sample_id)

        # Create flowchart
        flowchart = create_genealogy_flowchart(genealogy_data)

        return flowchart

    # ===========================
    # ADD PD SAMPLES MODAL - OPEN
    # ===========================

    @app.callback(
        Output("add-pd-modal", "is_open"),
        Output("add-pd-table-container", "children"),
        Output("single-dn-section", "style"),
        Output("single-dn-dropdown", "options"),
        Output("single-dn-dropdown", "value"),
        Output("single-dn-project-display", "children"),
        Output("add-mode", "data"),
        Input("open-add-pd-modal", "n_clicks"),
        Input("add-pd-mode", "value"),
        Input("add-pd-row-btn", "n_clicks"),
        Input("clear-pd-rows-btn", "n_clicks"),
        Input("single-dn-dropdown", "value"),
        State("add-pd-table-container", "children"),
        State("add-mode", "data"),
        prevent_initial_call=True
    )
    def handle_add_modal_ui(
        open_clicks, mode_value, add_row_clicks, clear_clicks,
        selected_dn, table_state, current_mode
    ):
        """Handle Add modal UI updates (mode changes, row operations)."""
        # Get DN options
        dn_options = get_available_dns()

        # Determine which input triggered
        from dash import callback_context
        if not callback_context.triggered:
            raise PreventUpdate

        trigger_id = callback_context.triggered[0]["prop_id"].split(".")[0]

        # OPEN modal
        if trigger_id == "open-add-pd-modal":
            table = _create_add_table("bulk", None, 3)
            return True, table, {"display": "none"}, dn_options, None, "", "bulk"

        # MODE CHANGE
        if trigger_id == "add-pd-mode":
            mode = mode_value
            show_dn_section = {"display": "block"} if mode == "single" else {"display": "none"}
            table = _create_add_table(mode, selected_dn, 3)
            return True, table, show_dn_section, dn_options, selected_dn, _get_project_display(selected_dn), mode

        # DN SELECTION (for single mode)
        if trigger_id == "single-dn-dropdown":
            table = _create_add_table(current_mode, selected_dn, 3)
            return True, table, {"display": "block"}, dn_options, selected_dn, _get_project_display(selected_dn), current_mode

        # ADD ROW
        if trigger_id == "add-pd-row-btn":
            if table_state and isinstance(table_state, dict):
                current_data = table_state.get("props", {}).get("data", [])
                num_rows = len(current_data) + 1
            else:
                num_rows = 4
            table = _create_add_table(current_mode, selected_dn, num_rows)
            show_dn_section = {"display": "block"} if current_mode == "single" else {"display": "none"}
            return True, table, show_dn_section, dn_options, selected_dn, _get_project_display(selected_dn), current_mode

        # CLEAR ROWS
        if trigger_id == "clear-pd-rows-btn":
            table = _create_add_table(current_mode, selected_dn, 3)
            show_dn_section = {"display": "block"} if current_mode == "single" else {"display": "none"}
            return True, table, show_dn_section, dn_options, selected_dn, _get_project_display(selected_dn), current_mode

        raise PreventUpdate

    # ===========================
    # ADD PD SAMPLES MODAL - SAVE
    # ===========================

    @app.callback(
        Output("add-pd-alert", "children"),
        Output("pd-samples-table", "data", allow_duplicate=True),
        Output("add-pd-modal", "is_open", allow_duplicate=True),
        Input("add-pd-save", "n_clicks"),
        State("add-pd-table-container", "children"),
        State("add-mode", "data"),
        prevent_initial_call=True
    )
    def save_add_modal(n_clicks, table_state, current_mode):
        """Save new PD samples."""
        if not table_state:
            raise PreventUpdate

        try:
            # Extract table data
            if isinstance(table_state, dict):
                table_data = table_state.get("props", {}).get("data", [])

                if not table_data:
                    alert = dbc.Alert("No samples to create", color="warning", dismissable=True)
                    return alert, no_update, True

                # Create samples
                created_count = 0
                for row in table_data:
                    # Skip empty rows
                    if not row.get("sample_id"):
                        continue

                    # Create new PD sample
                    sample = LimsSampleAnalysis(
                        sample_id=row.get("sample_id"),
                        sample_type=3,  # PD type
                        project_id=row.get("project_id") or None,
                        description=row.get("description") or None,
                        notes=row.get("notes") or None,
                        analyst=row.get("analyst") or None,
                        status=row.get("status") or "In Progress",
                    )

                    # Link DN if provided
                    dn_value = row.get("dn")
                    if dn_value:
                        # Handle DN formats (DN123 or 123)
                        if isinstance(dn_value, str) and dn_value.startswith("DN"):
                            dn_num = int(dn_value[2:])
                        else:
                            dn_num = int(dn_value)
                        dn_obj = LimsDnAssignment.objects.filter(dn=dn_num).first()
                        if dn_obj:
                            sample.dn = dn_obj

                    # Date
                    if row.get("sample_date"):
                        sample.sample_date = row.get("sample_date")

                    # A280
                    if row.get("a280"):
                        try:
                            sample.a280_result = float(row.get("a280"))
                        except (ValueError, TypeError):
                            pass

                    sample.save()
                    created_count += 1

                alert = dbc.Alert(f"Successfully created {created_count} PD sample(s)", color="success", dismissable=True, duration=3000)
                return alert, no_update, False

        except Exception as e:
            print(f"Error creating PD samples: {e}")
            alert = dbc.Alert(f"Error creating samples: {str(e)}", color="danger", dismissable=True)
            return alert, no_update, True

    # ===========================
    # ADD PD SAMPLES MODAL - CANCEL
    # ===========================

    @app.callback(
        Output("add-pd-modal", "is_open", allow_duplicate=True),
        Input("add-pd-cancel", "n_clicks"),
        prevent_initial_call=True
    )
    def cancel_add_modal(n_clicks):
        """Close add modal without saving."""
        return False


def _create_add_table(mode: str, selected_dn: int = None, num_rows: int = 3):
    """Create the add samples table based on mode."""
    next_pd = get_next_pd_number()
    dn_options = get_available_dns()

    # Determine project_id if DN is selected
    project_id = ""
    if selected_dn:
        dn_obj = LimsDnAssignment.objects.filter(dn=selected_dn).first()
        if dn_obj:
            project_id = dn_obj.project_id or ""

    if mode == "bulk":
        # Bulk mode: All fields editable
        columns = [
            {"name": "PD#", "id": "sample_id", "editable": False},
            {"name": "Project ID", "id": "project_id", "editable": True},
            {"name": "Linked DN", "id": "dn", "editable": True, "presentation": "dropdown"},
            {"name": "Description", "id": "description", "editable": True},
            {"name": "Sample Date", "id": "sample_date", "editable": True, "type": "datetime"},
            {"name": "A280 (mg/mL)", "id": "a280", "editable": True, "type": "numeric"},
            {"name": "Analyst", "id": "analyst", "editable": True},
            {"name": "Status", "id": "status", "editable": True, "presentation": "dropdown"},
            {"name": "Notes", "id": "notes", "editable": True},
        ]

        data = [
            {
                "sample_id": f"PD{next_pd + i + 1}",
                "project_id": "",
                "dn": "",
                "description": "",
                "sample_date": "",
                "a280": "",
                "analyst": "",
                "status": "In Progress",
                "notes": "",
            }
            for i in range(num_rows)
        ]

        dropdown = {
            "dn": {"options": dn_options},
            "status": {
                "options": [
                    {"label": "In Progress", "value": "In Progress"},
                    {"label": "Complete", "value": "Complete"},
                    {"label": "Review", "value": "Review"},
                ]
            }
        }

    else:  # single mode
        # Single mode: Simpler, DN and Project auto-filled
        columns = [
            {"name": "PD#", "id": "sample_id", "editable": False},
            {"name": "Description", "id": "description", "editable": True},
            {"name": "Sample Date", "id": "sample_date", "editable": True, "type": "datetime"},
            {"name": "A280 (mg/mL)", "id": "a280", "editable": True, "type": "numeric"},
            {"name": "Analyst", "id": "analyst", "editable": True},
            {"name": "Notes", "id": "notes", "editable": True},
        ]

        data = [
            {
                "sample_id": f"PD{next_pd + i + 1}",
                "project_id": project_id,  # Hidden but stored
                "dn": selected_dn,  # Hidden but stored
                "description": "",
                "sample_date": "",
                "a280": "",
                "analyst": "",
                "status": "In Progress",  # Default
                "notes": "",
            }
            for i in range(num_rows)
        ]

        dropdown = {}

    return dash_table.DataTable(
        id="add-pd-table",
        columns=columns,
        data=data,
        editable=True,
        row_deletable=False,
        style_table={"overflowX": "auto"},
        style_cell={
            "textAlign": "left",
            "padding": "10px",
            "fontSize": "13px",
            "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            "border": "1px solid #e9ecef",
        },
        style_header={
            "backgroundColor": "#0d6efd",
            "fontWeight": "600",
            "color": "#ffffff",
            "textAlign": "left",
            "fontSize": "12px",
            "textTransform": "uppercase",
            "letterSpacing": "0.5px",
            "padding": "10px",
            "border": "1px solid #0a58ca",
        },
        style_data={
            "backgroundColor": "#ffffff",
            "color": "#212529",
        },
        dropdown=dropdown,
    )


def _get_project_display(selected_dn: int = None) -> str:
    """Get project display text for selected DN."""
    if not selected_dn:
        return "Select a DN to see the project"

    dn_obj = LimsDnAssignment.objects.filter(dn=selected_dn).first()
    if dn_obj and dn_obj.project_id:
        return dn_obj.project_id
    return "No project assigned to this DN"
