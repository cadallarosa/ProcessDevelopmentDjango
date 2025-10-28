"""Main layout for PD Samples Management app - Modern Single Page Design."""
import dash_bootstrap_components as dbc
from dash import html, dcc
from datetime import datetime
from .components.tables import create_pd_samples_table


def create_layout():
    """Create the modern single-page layout with modals."""
    return html.Div([
        # Data stores
        dcc.Store(id="pd-selected-id", data=None),
        dcc.Store(id="add-mode", data="bulk"),  # bulk or single

        # Hidden button for inline edit trigger
        html.Button(id="pd-samples-table-inline-save", style={"display": "none"}),

        # Inline edit alert
        dbc.Alert(id="pd-inline-edit-alert", is_open=False, dismissable=True, className="position-fixed top-0 end-0 m-3", style={"zIndex": "9999"}),

        # Edit PD Sample Modal with Tabs
        dbc.Modal([
            dbc.ModalHeader([
                html.H5(id="edit-pd-modal-header", className="mb-0")
            ], close_button=True),
            dbc.ModalBody([
                html.Div(id="edit-pd-alert", className="mb-3"),

                # Tabs for Edit and Genealogy
                dbc.Tabs([
                    # Tab 1: Edit Sample
                    dbc.Tab([
                        html.Div([
                            # PD Sample Fields
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("PD Number"),
                                    dbc.Input(id="edit-pd-number", type="text", disabled=True)
                                ], md=3),
                                dbc.Col([
                                    dbc.Label("Project ID"),
                                    dbc.Input(id="edit-pd-project", type="text", placeholder="Project ID")
                                ], md=3),
                                dbc.Col([
                                    dbc.Label("Linked DN"),
                                    dcc.Dropdown(id="edit-pd-dn", placeholder="Select DN...", clearable=True)
                                ], md=3),
                                dbc.Col([
                                    dbc.Label("Status"),
                                    dcc.Dropdown(
                                        id="edit-pd-status",
                                        options=[
                                            {"label": "In Progress", "value": "In Progress"},
                                            {"label": "Complete", "value": "Complete"},
                                            {"label": "Review", "value": "Review"},
                                        ],
                                        placeholder="Select..."
                                    )
                                ], md=3),
                            ], className="mb-3"),

                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Sample Date (YYYY-MM-DD)"),
                                    dbc.Input(id="edit-pd-date", type="date")
                                ], md=4),
                                dbc.Col([
                                    dbc.Label("A280 (mg/mL)"),
                                    dbc.Input(id="edit-pd-a280", type="number", placeholder="A280")
                                ], md=4),
                                dbc.Col([
                                    dbc.Label("Analyst"),
                                    dbc.Input(id="edit-pd-analyst", type="text", placeholder="Analyst name")
                                ], md=4),
                            ], className="mb-3"),

                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Description"),
                                    dbc.Textarea(id="edit-pd-description", placeholder="Enter description...", rows=3)
                                ], md=12),
                            ], className="mb-3"),

                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Notes"),
                                    dbc.Textarea(id="edit-pd-notes", placeholder="Enter notes...", rows=3)
                                ], md=12),
                            ]),
                        ], className="p-3")
                    ], label="Edit Sample", tab_id="edit-tab"),

                    # Tab 2: Sample Genealogy
                    dbc.Tab([
                        html.Div(
                            id="genealogy-container",
                            className="p-3"
                        )
                    ], label="Sample Genealogy", tab_id="genealogy-tab"),
                ], id="edit-modal-tabs", active_tab="edit-tab"),
            ], style={"maxHeight": "70vh", "overflowY": "auto"}),
            dbc.ModalFooter([
                dbc.Button(
                    [html.I(className="bi bi-x-circle me-2"), "Cancel"],
                    id="edit-pd-cancel",
                    color="secondary",
                    size="sm",
                    outline=True,
                    className="me-2"
                ),
                dbc.Button(
                    [html.I(className="bi bi-save me-2"), "Save Changes"],
                    id="edit-pd-save",
                    color="primary",
                    size="sm"
                )
            ])
        ], id="edit-pd-modal", is_open=False, size="xl", backdrop="static", scrollable=True),

        # Add PD Samples Modal
        dbc.Modal([
            dbc.ModalHeader([
                html.H5("Add PD Samples", className="mb-0")
            ], close_button=True),
            dbc.ModalBody([
                html.Div(id="add-pd-alert", className="mb-3"),

                # Mode Selector
                dbc.Card([
                    dbc.CardBody([
                        dbc.Label("Mode:", className="fw-bold me-3"),
                        dbc.RadioItems(
                            id="add-pd-mode",
                            options=[
                                {"label": "Bulk Add", "value": "bulk"},
                                {"label": "Single Experiment", "value": "single"},
                            ],
                            value="bulk",
                            inline=True,
                            className="d-inline"
                        )
                    ], className="py-2")
                ], className="mb-3", color="light"),

                # Single Experiment Section
                html.Div(id="single-dn-section", children=[
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Select DN Experiment", className="fw-bold"),
                            dcc.Dropdown(
                                id="single-dn-dropdown",
                                placeholder="Select DN...",
                                clearable=False
                            )
                        ], md=6),
                        dbc.Col([
                            dbc.Label("Project ID (Auto-filled)", className="fw-bold"),
                            html.Div(id="single-dn-project-display", style={
                                "padding": "8px 12px",
                                "border": "1px solid #ced4da",
                                "borderRadius": "4px",
                                "backgroundColor": "#f8f9fa",
                                "fontSize": "14px"
                            })
                        ], md=4),
                    ], className="mb-3")
                ], style={"display": "none"}),

                # Buttons
                html.Div([
                    dbc.Button("➕ Add Row", id="add-pd-row-btn", color="secondary", size="sm", className="me-2"),
                    dbc.Button("🧹 Clear All", id="clear-pd-rows-btn", color="danger", size="sm", outline=True),
                ], className="mb-3"),

                # Table Container
                html.Div(id="add-pd-table-container"),
            ], style={"maxHeight": "70vh", "overflowY": "auto"}),
            dbc.ModalFooter([
                dbc.Button(
                    [html.I(className="bi bi-x-circle me-2"), "Cancel"],
                    id="add-pd-cancel",
                    color="secondary",
                    size="sm",
                    outline=True,
                    className="me-2"
                ),
                dbc.Button(
                    [html.I(className="bi bi-save me-2"), "Create PD Sample(s)"],
                    id="add-pd-save",
                    color="success",
                    size="sm"
                )
            ])
        ], id="add-pd-modal", is_open=False, size="xl", backdrop="static", scrollable=True),

        # Main Content
        html.Div([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H3([
                        html.I(className="bi bi-droplet me-2"),
                        "PD Samples"
                    ], className="mb-0")
                ], width="auto"),
            ], className="mb-4"),

            # Filters Card
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Project ID", className="fw-bold"),
                            dcc.Dropdown(
                                id="pd-filter-project",
                                placeholder="All projects...",
                                clearable=True,
                                style={"minWidth": "200px"}
                            )
                        ], md=2),
                        dbc.Col([
                            dbc.Label("DN Filter", className="fw-bold"),
                            dcc.Dropdown(
                                id="pd-filter-dn",
                                placeholder="All DNs...",
                                clearable=True,
                                style={"minWidth": "150px"}
                            )
                        ], md=2),
                        dbc.Col([
                            dbc.Label("Status", className="fw-bold"),
                            dcc.Dropdown(
                                id="pd-filter-status",
                                options=[
                                    {"label": "All", "value": "all"},
                                    {"label": "In Progress", "value": "In Progress"},
                                    {"label": "Complete", "value": "Complete"},
                                    {"label": "Review", "value": "Review"},
                                ],
                                value="all",
                                clearable=False,
                                style={"minWidth": "150px"}
                            )
                        ], md=2),
                        dbc.Col([
                            dbc.Label("Search", className="fw-bold"),
                            dbc.Input(
                                id="pd-filter-search",
                                type="text",
                                placeholder="Search PD#, Description...",
                                debounce=True
                            )
                        ], md=3),
                        dbc.Col([
                            dbc.Label(html.Span([html.I(className="bi bi-blank")]), style={"visibility": "hidden"}),
                            html.Div([
                                dbc.Button(
                                    [html.I(className="bi bi-plus-circle me-2"), "Add PD Samples"],
                                    id="open-add-pd-modal",
                                    color="success",
                                    size="sm",
                                    className="me-2"
                                ),
                                dbc.Button(
                                    [html.I(className="bi bi-arrow-clockwise me-2"), "Refresh"],
                                    id="pd-refresh-btn",
                                    color="secondary",
                                    size="sm",
                                    outline=True
                                ),
                            ])
                        ], md=3, className="d-flex align-items-end"),
                    ], align="end")
                ])
            ], className="mb-3 shadow-sm"),

            # Table Card
            dbc.Card([
                dbc.CardBody([
                    create_pd_samples_table(table_id="pd-samples-table"),
                ])
            ], className="shadow-sm"),
        ], style={"padding": "20px", "backgroundColor": "#f8f9fa", "minHeight": "100vh"})
    ])
