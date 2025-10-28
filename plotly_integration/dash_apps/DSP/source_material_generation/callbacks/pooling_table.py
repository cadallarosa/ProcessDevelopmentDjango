"""Callbacks for the sample pooling DataTable."""
from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate
from ..utils.data_helpers import (
    get_samples_by_project_and_type,
    format_samples_for_pooling_table
)
from ..components.tables import create_pooling_sample_table


def register_pooling_table_callbacks(app):
    """Register callbacks for pooling table."""

    @app.callback(
        Output("sm-gen-pooling-table-container", "children"),
        Input("sm-gen-project-id", "value"),
        Input("sm-gen-sample-type-multi", "value"),
        prevent_initial_call=True
    )
    def populate_pooling_table(project_id, sample_types):
        """
        Populate the pooling table based on selected project and sample types.

        Args:
            project_id: Selected project ID
            sample_types: List of sample type integers [1, 2, 3]

        Returns:
            DataTable with samples available for pooling
        """
        if not project_id or not project_id.strip() or not sample_types:
            return html.Div([
                html.P("Select a project ID and at least one sample type to view available samples.",
                       className="text-muted text-center py-3")
            ])

        # Collect all samples from selected types
        all_samples = []
        for sample_type in sample_types:
            samples = get_samples_by_project_and_type(project_id, sample_type)
            all_samples.extend(samples)

        if not all_samples:
            return html.Div([
                html.P(f"No samples found for project {project_id} with selected sample types.",
                       className="text-muted text-center py-3")
            ])

        # Format for table
        table_data = format_samples_for_pooling_table(all_samples)

        # Create table with data
        table = create_pooling_sample_table()
        table.data = table_data

        return html.Div([
            html.P(f"{len(table_data)} samples available for pooling. Select rows to pool.",
                   className="text-muted mb-2"),
            table
        ])
