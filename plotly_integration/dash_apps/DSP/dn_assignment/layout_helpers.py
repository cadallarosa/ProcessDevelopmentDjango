"""Helper functions for creating tab layouts."""
import dash_bootstrap_components as dbc
from dash import html, dcc
from .components.tables import (
    create_dn_view_table,
    create_dn_bulk_table,
    create_dn_edit_table,
    create_pd_sample_table,
    create_pd_bulk_table,
    create_sample_info_existing_table,
    create_sample_info_new_table
)


def create_view_experiments_tab():
    """Create the View Experiments tab content."""
    return html.Div([
        html.Div([
            dbc.Button("Refresh Table", id="manual-refresh", size="sm", color="secondary", className="me-2"),
            dbc.Button("Create New DN", id="create-new-dn", size="sm", color="primary")
        ], className="mb-2 d-flex gap-2"),
        create_dn_view_table(table_id="dn-table"),
        html.Div(id="inline-save-status", style={"fontSize": "11px", "marginTop": "5px", "padding": "5px"}),
    ], style={"padding": "10px"})


def create_new_experiments_tab():
    """Create the Create New Experiments tab content."""
    return html.Div([
        html.Div(id="dn-bulk-table-container", children=[
            dbc.Button("➕ Add Row", id="add-row-btn", color="secondary", size="sm", className="mt-2"),
            dbc.Button("🧹 Clear Table", id="clear-dn-btn", color="danger", size="sm", className="ms-2 mt-2"),
            create_dn_bulk_table(table_id="dn-bulk-table"),
        ]),
        dbc.Row([
            dbc.Col(dbc.Button("Save / Update", id="save_button", color="primary", size="sm"), width="auto"),
            dbc.Col(html.Div(id="save_status", style={"fontSize": "11px", "marginTop": "5px"}), width="auto"),
        ])
    ], style={"padding": "10px"})


def create_edit_dn_tab():
    """Create the Edit DN tab content (with Sample Info sub-tab)."""
    return html.Div([
        dbc.Row([
            dbc.Col(html.H5("Edit DN Details"), width="auto"),
        ], className="mb-2 g-2"),

        create_dn_edit_table(table_id="edit-dn-table"),

        dbc.Row([
            dbc.Col(dbc.Button("🔄 Refresh", id="refresh-edit-dn", size="sm", color="secondary"), width="auto"),
            dbc.Col(dbc.Button("💾 Save Changes", id="save-edit-dn", size="sm", color="primary"), width="auto")
        ], className="mb-2 g-2"),

        html.Br(),

        # Sample Info Sub-tab
        html.Div([
            html.H5("Existing Samples"),
            create_sample_info_existing_table(table_id="existing-sample-table"),

            dbc.Row([
                dbc.Col(
                    dbc.Button("💾 Save Existing Samples", id="save-existing-samples", color="primary", size="sm"),
                    width="auto"),
                dbc.Col(dbc.Button("🔄 Refresh", id="refresh-existing-samples", color="secondary", size="sm"),
                        width="auto")
            ], className="mt-2 g-2"),

            html.Br(),
            html.H5("Create New Samples"),

            dbc.Button("➕ Add Sample Row", id="add-sample-row", size="sm", color="secondary",
                       className="mt-2 me-2"),
            dbc.Button("🧹 Clear Table", id="clear-sample-btn", size="sm", color="danger",
                       className="mt-2 me-2"),

            create_sample_info_new_table(table_id="new-sample-table"),

            dbc.Button("💾 Save New Samples", id="save-samples-btn", size="sm", color="primary",
                       className="mt-2"),
            html.Div(id="save_samples_status", style={"fontSize": "11px", "marginTop": "5px"})
        ])
    ])


def create_pd_samples_tab():
    """Create the PD Samples tab content."""
    return html.Div([
        dcc.Store(id="reset-save-pd-trigger", data=False),
        dcc.Interval(id="reset-save-pd-timer", interval=3000, n_intervals=0, disabled=True),

        html.H5("Existing PD Samples"),
        dbc.Row([
            dbc.Col(dbc.Button("🔄 Refresh", id="refresh-pd-table", color="secondary", size="sm"), width="auto"),
            dbc.Col(dbc.Button("💾 Save Changes", id="update-pd-table", color="primary", size="sm"), width="auto"),
        ], className="mb-2"),

        create_pd_sample_table(table_id="view-pd-table"),

        html.Br(),
        html.H5("Create New PD Samples"),

        create_pd_bulk_table(table_id="pd-bulk-table"),

        dbc.Row([
            dbc.Col(dbc.Button("💾 Save PD Samples", id="save-pd-btn", color="primary", size="sm"), width="auto"),
            dbc.Col(html.Div(id="save-pd-status", style={"fontSize": "11px", "marginTop": "5px"}), width="auto")
        ], className="mt-2")
    ], style={"padding": "10px"})
