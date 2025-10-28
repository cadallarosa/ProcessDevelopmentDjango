"""Callbacks for DN table view, filtering, and loading."""
from dash import Input, Output, State
from dash.exceptions import PreventUpdate
from ..utils.data_helpers import get_all_dn_assignments


def register_dn_table_callbacks(app):
    """Register callbacks for DN table functionality."""

    @app.callback(
        Output("dn-table", "data"),
        Input("dn-refresh-btn", "n_clicks"),
        Input("dn-filter-project", "value"),
        Input("dn-filter-status", "value"),
        Input("dn-filter-search", "value"),
        Input("edit-dn-save", "n_clicks"),
        Input("create-dn-save", "n_clicks"),
        prevent_initial_call=False
    )
    def load_and_filter_dn_table(refresh, project_filter, status_filter, search_filter, edit_save, create_save):
        """Load and filter DN table data."""
        # Get all data
        data = get_all_dn_assignments()

        if not data:
            return []

        # Apply filters
        filtered_data = data

        # Project filter
        if project_filter:
            filtered_data = [row for row in filtered_data if row.get("project_id") == project_filter]

        # Status filter
        if status_filter and status_filter != "all":
            filtered_data = [row for row in filtered_data if row.get("status") == status_filter]

        # Search filter
        if search_filter:
            search_lower = search_filter.lower()
            filtered_data = [
                row for row in filtered_data
                if search_lower in str(row.get("dn", "")).lower()
                or search_lower in str(row.get("project_id", "")).lower()
                or search_lower in str(row.get("notes", "")).lower()
                or search_lower in str(row.get("scouting_details", "")).lower()
            ]

        return filtered_data

    @app.callback(
        Output("dn-filter-project", "options"),
        Input("dn-table", "data"),
        prevent_initial_call=False
    )
    def update_project_filter_options(table_data):
        """Populate project filter dropdown with unique project IDs."""
        if not table_data:
            return []

        projects = sorted(list(set([row.get("project_id", "") for row in table_data if row.get("project_id")])))
        return [{"label": p, "value": p} for p in projects]
