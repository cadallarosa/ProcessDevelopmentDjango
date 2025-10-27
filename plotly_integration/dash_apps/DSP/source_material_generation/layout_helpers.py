"""Helper functions for creating layout sections."""
import dash_bootstrap_components as dbc
from dash import html
from .components.forms import (
    create_labeled_input,
    create_labeled_dropdown,
    create_searchable_dropdown
)
from .components.tables import create_sm_management_table, create_process_steps_table


def create_manage_existing_tab():
    """Create the 'Manage Existing' tab content."""

    return html.Div([
        # Filters Card
        dbc.Card([
            dbc.CardHeader([
                html.H5("Filters", className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        create_searchable_dropdown(
                            label="Filter by Project",
                            dropdown_id="sm-manage-project-filter",
                            placeholder="All projects...",
                            help_text="Filter source materials by project ID"
                        )
                    ], md=4),
                    dbc.Col([
                        html.Div([
                            dbc.Label("Search"),
                            dbc.Input(
                                id="sm-manage-search",
                                placeholder="Search by name, DN, PD...",
                                type="text"
                            ),
                            dbc.FormText("Search across all fields", color="muted")
                        ])
                    ], md=6),
                    dbc.Col([
                        html.Div([
                            dbc.Label(html.Span([html.I(className="bi bi-blank")]), style={"visibility": "hidden"}),
                            dbc.Button(
                                [html.I(className="bi bi-arrow-clockwise me-2"), "Refresh"],
                                id="sm-manage-refresh",
                                color="secondary",
                                size="sm",
                                className="w-100"
                            )
                        ])
                    ], md=2)
                ])
            ])
        ], className="mb-3"),

        # Source Materials Table
        dbc.Card([
            dbc.CardHeader([
                html.H5("Source Materials", className="mb-0")
            ]),
            dbc.CardBody([
                create_sm_management_table(table_id="sm-manage-table")
            ])
        ], className="mb-3"),

        # Edit Modal (shown when row selected)
        dbc.Modal([
            dbc.ModalHeader([
                html.H5(id="sm-edit-header", className="mb-0")
            ], close_button=True),
            dbc.ModalBody([
                # Alert area for save feedback
                html.Div(id="sm-edit-alert", className="mb-3"),
                        # SM Name
                        create_labeled_input(
                            label="Source Material Name",
                            input_id="sm-edit-name",
                            placeholder="Enter name",
                            required=True
                        ),

                        # Sample Properties Row
                        dbc.Row([
                            dbc.Col([
                                create_labeled_input(
                                    label="Final pH",
                                    input_id="sm-edit-ph",
                                    input_type="number",
                                    placeholder="pH"
                                )
                            ], md=3),
                            dbc.Col([
                                create_labeled_input(
                                    label="Conductivity (mS/cm)",
                                    input_id="sm-edit-conductivity",
                                    input_type="number",
                                    placeholder="Conductivity"
                                )
                            ], md=3),
                            dbc.Col([
                                create_labeled_input(
                                    label="Concentration (mg/mL)",
                                    input_id="sm-edit-concentration",
                                    input_type="number",
                                    placeholder="Concentration"
                                )
                            ], md=3),
                            dbc.Col([
                                create_labeled_input(
                                    label="Volume (mL)",
                                    input_id="sm-edit-volume",
                                    input_type="number",
                                    placeholder="Volume"
                                )
                            ], md=3)
                        ]),

                        html.Hr(),

                        # DN Link
                        create_labeled_dropdown(
                            label="Linked DN Experiment",
                            dropdown_id="sm-edit-dn",
                            placeholder="Select DN...",
                            help_text="Change which DN this source material is linked to"
                        ),

                        # Pooled Samples
                        create_labeled_dropdown(
                            label="Pooled Samples",
                            dropdown_id="sm-edit-pooled-samples",
                            multi=True,
                            placeholder="Select samples...",
                            help_text="Add or remove pooled samples"
                        ),

                        html.Hr(),

                        # Process Steps
                        html.H6("Process Steps", className="mb-2"),
                        create_process_steps_table(
                            table_id="sm-edit-process-table",
                            data=[{"step": 1, "process": "", "notes": ""}]
                        ),
                        dbc.Button(
                            [html.I(className="bi bi-plus-circle me-1"), "Add Step"],
                            id="sm-edit-add-step",
                            color="secondary",
                            size="sm",
                            outline=True,
                            className="mt-2"
                        ),

                        html.Hr(),

                        # Resulting PD Sample (read-only)
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Resulting PD Sample (Read-Only)"),
                                html.Div(
                                    id="sm-edit-pd-sample",
                                    style={
                                        "padding": "8px 12px",
                                        "border": "1px solid #ced4da",
                                        "borderRadius": "4px",
                                        "backgroundColor": "#f8f9fa",
                                        "fontSize": "14px"
                                    }
                                )
                            ], md=6)
                        ], className="mb-3")
            ], style={"maxHeight": "70vh", "overflowY": "auto"}),
            dbc.ModalFooter([
                dbc.Button(
                    [html.I(className="bi bi-x-circle me-2"), "Cancel"],
                    id="sm-edit-cancel",
                    color="secondary",
                    size="sm",
                    outline=True,
                    className="me-2"
                ),
                dbc.Button(
                    [html.I(className="bi bi-save me-2"), "Save Changes"],
                    id="sm-edit-save",
                    color="primary",
                    size="sm"
                )
            ])
        ], id="sm-edit-modal", is_open=False, size="xl", backdrop="static", scrollable=True)
    ], style={"padding": "10px"})
