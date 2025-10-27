"""Main layout for Source Material Generation app using DBC components."""
import dash_bootstrap_components as dbc
from dash import dcc, html
from .components.forms import (
    create_labeled_input,
    create_labeled_dropdown,
    create_labeled_radio,
    create_info_display,
    create_searchable_dropdown
)
from .components.tables import create_process_steps_table, create_sm_management_table
from .layout_helpers import create_manage_existing_tab


def create_layout():
    """Create the main app layout with modern DBC components."""

    return dbc.Container([
        # Store components for state management
        dcc.Store(id="sm-gen-context", data={}),
        dcc.Store(id="sm-edit-selected-id", data=None),

        # Confirmation Modal
        dbc.Modal([
            dbc.ModalHeader("Confirm Source Material Changes"),
            dbc.ModalBody(
                id="sm-gen-modal-body",
                children="Changes detected. Do you want to overwrite the existing Source Material?"
            ),
            dbc.ModalFooter([
                dbc.Button(
                    "Cancel",
                    id="sm-gen-cancel-overwrite",
                    color="secondary",
                    size="sm",
                    className="me-2"
                ),
                dbc.Button(
                    "Confirm Overwrite",
                    id="sm-gen-confirm-overwrite",
                    color="primary",
                    size="sm"
                )
            ])
        ], id="sm-gen-overwrite-modal", is_open=False, centered=True),

        # Header
        dbc.Row([
            dbc.Col([
                html.H3(
                    "Source Material Generation",
                    className="mb-1",
                    style={"color": "#0d6efd", "fontWeight": "600"}
                ),
                html.P(
                    "Create and manage source materials for downstream processing experiments",
                    className="text-muted mb-0",
                    style={"fontSize": "14px"}
                )
            ])
        ], className="mb-4 pb-3", style={"borderBottom": "2px solid #e9ecef"}),

        # Alert for feedback messages
        html.Div(id="sm-gen-alert-container", className="mb-3"),

        # Main Tabs
        dcc.Tabs(id="sm-gen-tabs", value="create-tab", children=[
            # CREATE NEW TAB
            dcc.Tab(label="Create New Source Material", value="create-tab", children=[
                html.Div([
        # Main Content Card (CREATE TAB CONTENT START)
        dbc.Card([
            dbc.CardHeader([
                html.H5("Source Material Configuration", className="mb-0")
            ]),
            dbc.CardBody([
                # Mode Selection
                create_labeled_radio(
                    label="Mode",
                    radio_id="sm-gen-mode",
                    options=[
                        {"label": "Use Existing Source Material", "value": "existing"},
                        {"label": "Create New Source Material", "value": "new"}
                    ],
                    value="new"
                ),

                html.Hr(),

                # Project ID Searchable Dropdown (required for filtering)
                create_searchable_dropdown(
                    label="Project ID",
                    dropdown_id="sm-gen-project-id",
                    placeholder="Select existing or type new project ID...",
                    help_text="Required to filter samples and source materials. Select from existing or type a new one.",
                    required=True
                ),

                # Existing SM Section (conditional visibility)
                html.Div(
                    id="sm-gen-existing-section",
                    children=[
                        create_labeled_dropdown(
                            label="Select Existing Source Material",
                            dropdown_id="sm-gen-existing-dropdown",
                            placeholder="Choose a source material...",
                            help_text="Available source materials for this project"
                        )
                    ],
                    style={"display": "none"}
                ),

                # New SM Section (always visible but fields may be populated from existing)
                html.Div(id="sm-gen-new-section", children=[
                    create_labeled_input(
                        label="Source Material Name",
                        input_id="sm-gen-name",
                        placeholder="Enter descriptive name",
                        required=True
                    )
                ])
            ])
        ], className="mb-4"),

        # Sample Pooling Card
        dbc.Card([
            dbc.CardHeader([
                html.H5("Sample Pooling", className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        create_labeled_dropdown(
                            label="Sample Type Filter",
                            dropdown_id="sm-gen-sample-type",
                            options=[
                                {"label": "Upstream (UP)", "value": 1},
                                {"label": "Formulation Buffer (FB)", "value": 2},
                                {"label": "Process Development (PD)", "value": 3}
                            ],
                            value=3,
                            clearable=False,
                            help_text="Filter available samples by type"
                        )
                    ], md=4),
                    dbc.Col([
                        create_labeled_dropdown(
                            label="Pooled Samples",
                            dropdown_id="sm-gen-pooled-samples",
                            multi=True,
                            placeholder="Select samples to pool...",
                            help_text="Select one or more samples to combine"
                        )
                    ], md=8)
                ])
            ])
        ], className="mb-4"),

        # Sample Details Card
        dbc.Card([
            dbc.CardHeader([
                html.H5("Final Sample Properties", className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        create_labeled_input(
                            label="Final pH",
                            input_id="sm-gen-final-ph",
                            input_type="number",
                            placeholder="pH"
                        )
                    ], md=3),
                    dbc.Col([
                        create_labeled_input(
                            label="Conductivity (mS/cm)",
                            input_id="sm-gen-final-conductivity",
                            input_type="number",
                            placeholder="Conductivity"
                        )
                    ], md=3),
                    dbc.Col([
                        create_labeled_input(
                            label="Concentration (mg/mL)",
                            input_id="sm-gen-final-concentration",
                            input_type="number",
                            placeholder="Concentration"
                        )
                    ], md=3),
                    dbc.Col([
                        create_labeled_input(
                            label="Volume (mL)",
                            input_id="sm-gen-final-volume",
                            input_type="number",
                            placeholder="Volume"
                        )
                    ], md=3)
                ]),

                html.Hr(),

                # Resulting Sample ID Display
                create_info_display(
                    label="Resulting Sample ID",
                    display_id="sm-gen-result-sample-id",
                    value="Will be auto-generated"
                )
            ])
        ], className="mb-4"),

        # Process Steps Card
        dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H5("Process Steps", className="mb-0")
                    ], width="auto"),
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="bi bi-plus-circle me-1"), "Add Step"],
                            id="sm-gen-add-step",
                            color="secondary",
                            size="sm",
                            outline=True
                        )
                    ], width="auto", className="ms-auto")
                ])
            ]),
            dbc.CardBody([
                create_process_steps_table(
                    table_id="sm-gen-process-table",
                    data=[{"step": 1, "process": "", "notes": ""}]
                )
            ])
        ], className="mb-4"),

        # Action Buttons
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    [html.I(className="bi bi-save me-2"), "Save Source Material"],
                    id="sm-gen-save-btn",
                    color="primary",
                    size="lg",
                    className="w-100"
                )
            ], md=6, className="mx-auto")
        ], className="mb-3"),
                ], style={"padding": "10px"})  # Close CREATE TAB content div
            ]),  # Close CREATE TAB

            # MANAGE EXISTING TAB
            dcc.Tab(label="Manage Existing Source Materials", value="manage-tab", children=[
                create_manage_existing_tab()
            ])
        ])  # Close Tabs

    ], fluid=True, className="py-4")
