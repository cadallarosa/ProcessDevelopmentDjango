"""Callbacks for analytics table operations."""
from dash import Input, Output, html
import dash_bootstrap_components as dbc
from ..utils.data_helpers import get_all_analytics_data, get_unique_projects


def register_analytics_callbacks(app):
    """Register callbacks for analytics dashboard."""

    @app.callback(
        Output("analytics-table", "data"),
        Output("analytics-filter-project", "options"),
        Output("analytics-stats", "children"),
        Input("analytics-refresh-btn", "n_clicks"),
        Input("analytics-filter-project", "value"),
        Input("analytics-filter-assay", "value"),
        Input("analytics-filter-qc", "value"),
        Input("analytics-filter-search", "value"),
        prevent_initial_call=False
    )
    def load_and_filter_analytics(refresh, project_filter, assay_filter, qc_filter, search_filter):
        """Load and filter analytics data."""
        # Get all data
        data = get_all_analytics_data()
        project_options = [{"label": p, "value": p} for p in get_unique_projects()]

        if not data:
            return [], project_options, dbc.Alert("No analytical data available", color="info")

        total_samples = len(data)
        filtered_data = data.copy()

        # Project filter
        if project_filter:
            filtered_data = [row for row in filtered_data if row.get("project_id") == project_filter]

        # Assay type filter
        if assay_filter == "sec":
            filtered_data = [row for row in filtered_data if row.get("sec_main_peak")]
        elif assay_filter == "titer":
            filtered_data = [row for row in filtered_data if row.get("titer")]
        elif assay_filter == "mass":
            filtered_data = [row for row in filtered_data if row.get("mass_expected")]
        elif assay_filter == "complete":
            # Only samples with SEC, Titer, and Mass Check
            filtered_data = [
                row for row in filtered_data
                if row.get("sec_main_peak") and row.get("titer") and row.get("mass_expected")
            ]

        # QC filter
        if qc_filter == "pass":
            filtered_data = [
                row for row in filtered_data
                if row.get("sec_qc") == "Pass" or row.get("titer_qc") == "Pass"
            ]
        elif qc_filter == "fail":
            filtered_data = [
                row for row in filtered_data
                if row.get("sec_qc") == "Fail" or row.get("titer_qc") == "Fail"
            ]

        # Search filter
        if search_filter:
            search_lower = search_filter.lower()
            filtered_data = [
                row for row in filtered_data
                if search_lower in row.get("sample_id", "").lower()
                or search_lower in row.get("project_id", "").lower()
                or search_lower in row.get("dn", "").lower()
            ]

        # Create stats
        stats = dbc.Row([
            dbc.Col([
                html.Div([
                    html.Span("Total Samples: ", className="fw-bold"),
                    html.Span(f"{total_samples}", className="badge bg-primary")
                ])
            ], width="auto"),
            dbc.Col([
                html.Div([
                    html.Span("Filtered: ", className="fw-bold"),
                    html.Span(f"{len(filtered_data)}", className="badge bg-success")
                ])
            ], width="auto"),
            dbc.Col([
                html.Div([
                    html.Span("With SEC: ", className="fw-bold"),
                    html.Span(f"{sum(1 for r in filtered_data if r.get('sec_main_peak'))}", className="badge bg-info")
                ])
            ], width="auto"),
            dbc.Col([
                html.Div([
                    html.Span("With Titer: ", className="fw-bold"),
                    html.Span(f"{sum(1 for r in filtered_data if r.get('titer'))}", className="badge bg-info")
                ])
            ], width="auto"),
        ])

        return filtered_data, project_options, stats
