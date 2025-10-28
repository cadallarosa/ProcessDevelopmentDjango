"""Callbacks for PD Samples table operations."""
from dash import Input, Output, State, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from ..utils.data_helpers import get_all_pd_samples, get_unique_project_ids, get_unique_dn_numbers, get_pd_sample_by_id


def register_samples_table_callbacks(app):
    """Register callbacks for PD samples table loading and filtering."""

    @app.callback(
        Output("pd-samples-table", "data"),
        Output("pd-filter-project", "options"),
        Output("pd-filter-dn", "options"),
        Input("pd-refresh-btn", "n_clicks"),
        Input("pd-filter-project", "value"),
        Input("pd-filter-dn", "value"),
        Input("pd-filter-status", "value"),
        Input("pd-filter-search", "value"),
        # Triggers from modal save operations
        Input("edit-pd-save", "n_clicks"),
        Input("add-pd-save", "n_clicks"),
        # Trigger from inline editing
        Input("pd-samples-table-inline-save", "n_clicks"),
        prevent_initial_call=False
    )
    def load_and_filter_pd_table(
        refresh, project_filter, dn_filter, status_filter, search_filter,
        edit_save, add_save, inline_save
    ):
        """Load PD samples data and apply filters."""
        # Get all PD samples
        data = get_all_pd_samples()

        # Get unique values for filter dropdowns
        project_options = [{"label": p, "value": p} for p in get_unique_project_ids()]
        dn_options = get_unique_dn_numbers()

        if not data:
            return [], project_options, dn_options

        # Apply filters
        filtered_data = data.copy()

        # Project filter
        if project_filter:
            filtered_data = [row for row in filtered_data if row.get("project_id") == project_filter]

        # DN filter
        if dn_filter:
            filtered_data = [row for row in filtered_data if row.get("dn") == dn_filter]

        # Status filter
        if status_filter and status_filter != "all":
            filtered_data = [row for row in filtered_data if row.get("status") == status_filter]

        # Search filter (search in PD#, Description, Notes)
        if search_filter:
            search_lower = search_filter.lower()
            filtered_data = [
                row for row in filtered_data
                if search_lower in row.get("sample_id", "").lower()
                or search_lower in row.get("description", "").lower()
                or search_lower in row.get("notes", "").lower()
            ]

        return filtered_data, project_options, dn_options

    # ===========================
    # INLINE EDITING - SAVE
    # ===========================

    @app.callback(
        Output("pd-inline-edit-alert", "children"),
        Output("pd-inline-edit-alert", "is_open"),
        Output("pd-samples-table-inline-save", "n_clicks"),
        Input("pd-samples-table", "data"),
        State("pd-samples-table", "data_previous"),
        prevent_initial_call=True
    )
    def save_inline_edits(current_data, previous_data):
        """Auto-save inline edits to database."""
        from plotly_integration.models import LimsSampleAnalysis

        if not previous_data or not current_data:
            raise PreventUpdate

        # Find changed rows
        changed_rows = []
        for curr_row, prev_row in zip(current_data, previous_data):
            if curr_row != prev_row:
                changed_rows.append((curr_row, prev_row))

        if not changed_rows:
            raise PreventUpdate

        try:
            # Save changes
            for curr_row, prev_row in changed_rows:
                sample_id = curr_row.get("sample_id")
                sample = get_pd_sample_by_id(sample_id)

                if sample:
                    # Update editable fields
                    sample.project_id = curr_row.get("project_id") or None
                    sample.description = curr_row.get("description") or None
                    sample.analyst = curr_row.get("analyst") or None
                    sample.notes = curr_row.get("notes") or None
                    sample.status = curr_row.get("status") or "In Progress"

                    sample.save()

            alert = dbc.Alert(
                f"Successfully saved {len(changed_rows)} change(s)",
                color="success",
                dismissable=True,
                duration=3000
            )
            return alert, True, 1  # Trigger refresh

        except Exception as e:
            print(f"Error saving inline edits: {e}")
            alert = dbc.Alert(
                f"Error saving changes: {str(e)}",
                color="danger",
                dismissable=True
            )
            return alert, True, no_update
