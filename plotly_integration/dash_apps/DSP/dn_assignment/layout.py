"""Main layout for DN Assignment app - Modern Single Page Design."""
import dash_bootstrap_components as dbc
from dash import html, dcc
from .components.tables import create_dn_view_table


def create_layout():
    """Create the modern single-page layout with modals."""
    return html.Div([
        # Data stores
        dcc.Store(id="dn-context", data={"mode": "", "dn": ""}),
        dcc.Store(id="user-options", data=[]),
        dcc.Store(id="dn-selected-id", data=None),

        # Edit DN Modal with Tabs
        dbc.Modal([
            dbc.ModalHeader([
                html.H5(id="edit-dn-modal-header", className="mb-0")
            ], close_button=True),
            dbc.ModalBody([
                html.Div(id="edit-dn-alert", className="mb-3"),

                # Tabs for Edit DN and Mass Balance
                dbc.Tabs([
                    # Tab 1: Edit DN
                    dbc.Tab([
                        html.Div([
                            # DN Fields
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("DN Number"),
                                    dbc.Input(id="edit-dn-number", type="text", disabled=True)
                                ], md=3),
                                dbc.Col([
                                    dbc.Label("Project ID"),
                                    dbc.Input(id="edit-dn-project", type="text", placeholder="Project ID")
                                ], md=3),
                                dbc.Col([
                                    dbc.Label("Unit Operation"),
                                    dcc.Dropdown(
                                        id="edit-dn-unit-op",
                                        options=[
                                            {"label": "ProA", "value": "ProA"},
                                            {"label": "AEX", "value": "AEX"},
                                            {"label": "CEX", "value": "CEX"},
                                            {"label": "CHT", "value": "CHT"},
                                            {"label": "VI", "value": "VI"},
                                            {"label": "UFDF", "value": "UFDF"},
                                            {"label": "DF", "value": "DF"},
                                        ],
                                        placeholder="Select..."
                                    )
                                ], md=3),
                                dbc.Col([
                                    dbc.Label("Status"),
                                    dcc.Dropdown(
                                        id="edit-dn-status",
                                        options=[
                                            {"label": "Pending", "value": "Pending"},
                                            {"label": "In Progress", "value": "In Progress"},
                                            {"label": "Completed", "value": "Completed"},
                                        ],
                                        placeholder="Select..."
                                    )
                                ], md=3),
                            ], className="mb-3"),

                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Created By"),
                                    dcc.Dropdown(id="edit-dn-created-by", placeholder="Select user...")
                                ], md=6),
                                dbc.Col([
                                    dbc.Label("Assigned To"),
                                    dcc.Dropdown(id="edit-dn-assigned-to", placeholder="Select user...")
                                ], md=6),
                            ], className="mb-3"),

                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Scouting Details"),
                                    dbc.Textarea(id="edit-dn-scouting", placeholder="Enter details...", rows=3)
                                ], md=12),
                            ], className="mb-3"),

                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Notes"),
                                    dbc.Textarea(id="edit-dn-notes", placeholder="Enter notes...", rows=3)
                                ], md=12),
                            ]),
                        ], className="p-3")
                    ], label="Edit DN", tab_id="edit-dn-tab"),

                    # Tab 2: Mass Balance
                    dbc.Tab([
                        html.Div([
                            html.H6("Mass Balance Calculation", className="mb-3"),

                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Input Volume (mL)"),
                                    dbc.Input(id="edit-dn-input-vol", type="number", placeholder="0.0", step="0.1")
                                ], md=3),
                                dbc.Col([
                                    dbc.Label("Input Concentration (mg/mL)"),
                                    dbc.Input(id="edit-dn-input-conc", type="number", placeholder="0.0", step="0.01")
                                ], md=3),
                                dbc.Col([
                                    dbc.Label("Output Volume (mL)"),
                                    dbc.Input(id="edit-dn-output-vol", type="number", placeholder="0.0", step="0.1")
                                ], md=3),
                                dbc.Col([
                                    dbc.Label("Output Concentration (mg/mL)"),
                                    dbc.Input(id="edit-dn-output-conc", type="number", placeholder="0.0", step="0.01")
                                ], md=3),
                            ], className="mb-4"),

                            # Calculated Results
                            dbc.Card([
                                dbc.CardHeader(html.H6("Calculated Results", className="mb-0")),
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            html.Div([
                                                html.P("Input Protein (mg):", className="fw-bold mb-1"),
                                                html.H4(id="calc-input-protein", children="0.0", className="text-primary")
                                            ])
                                        ], md=3),
                                        dbc.Col([
                                            html.Div([
                                                html.P("Output Protein (mg):", className="fw-bold mb-1"),
                                                html.H4(id="calc-output-protein", children="0.0", className="text-primary")
                                            ])
                                        ], md=3),
                                        dbc.Col([
                                            html.Div([
                                                html.P("Yield (%):", className="fw-bold mb-1"),
                                                html.H4(id="calc-yield", children="0.0", className="text-success")
                                            ])
                                        ], md=3),
                                        dbc.Col([
                                            html.Div([
                                                html.P("Concentration Factor:", className="fw-bold mb-1"),
                                                html.H4(id="calc-conc-factor", children="0.0", className="text-info")
                                            ])
                                        ], md=3),
                                    ])
                                ])
                            ], className="shadow-sm")
                        ], className="p-3")
                    ], label="Mass Balance", tab_id="mass-balance-tab"),
                ], id="edit-dn-modal-tabs", active_tab="edit-dn-tab"),
            ], style={"maxHeight": "70vh", "overflowY": "auto"}),
            dbc.ModalFooter([
                dbc.Button(
                    [html.I(className="bi bi-x-circle me-2"), "Cancel"],
                    id="edit-dn-cancel",
                    color="secondary",
                    size="sm",
                    outline=True,
                    className="me-2"
                ),
                dbc.Button(
                    [html.I(className="bi bi-save me-2"), "Save Changes"],
                    id="edit-dn-save",
                    color="primary",
                    size="sm"
                )
            ])
        ], id="edit-dn-modal", is_open=False, size="xl", backdrop="static", scrollable=True),

        # Create DN Modal
        dbc.Modal([
            dbc.ModalHeader([
                html.H5("Create New DN Experiments", className="mb-0")
            ], close_button=True),
            dbc.ModalBody([
                html.Div(id="create-dn-alert", className="mb-3"),

                html.Div([
                    dbc.Button("➕ Add Row", id="add-dn-row-btn", color="secondary", size="sm", className="me-2"),
                    dbc.Button("🧹 Clear All", id="clear-dn-rows-btn", color="danger", size="sm", outline=True),
                ], className="mb-3"),

                html.Div(id="create-dn-table-container"),
            ], style={"maxHeight": "70vh", "overflowY": "auto"}),
            dbc.ModalFooter([
                dbc.Button(
                    [html.I(className="bi bi-x-circle me-2"), "Cancel"],
                    id="create-dn-cancel",
                    color="secondary",
                    size="sm",
                    outline=True,
                    className="me-2"
                ),
                dbc.Button(
                    [html.I(className="bi bi-save me-2"), "Create DN(s)"],
                    id="create-dn-save",
                    color="success",
                    size="sm"
                )
            ])
        ], id="create-dn-modal", is_open=False, size="xl", backdrop="static", scrollable=True),

        # Main Content
        html.Div([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H3([
                        html.I(className="bi bi-clipboard-data me-2"),
                        "DN Experiments"
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
                                id="dn-filter-project",
                                placeholder="All projects...",
                                clearable=True,
                                style={"minWidth": "200px"}
                            )
                        ], md=3),
                        dbc.Col([
                            dbc.Label("Status", className="fw-bold"),
                            dcc.Dropdown(
                                id="dn-filter-status",
                                options=[
                                    {"label": "All", "value": "all"},
                                    {"label": "Pending", "value": "Pending"},
                                    {"label": "In Progress", "value": "In Progress"},
                                    {"label": "Completed", "value": "Completed"},
                                ],
                                value="all",
                                clearable=False,
                                style={"minWidth": "150px"}
                            )
                        ], md=2),
                        dbc.Col([
                            dbc.Label("Search", className="fw-bold"),
                            dbc.Input(
                                id="dn-filter-search",
                                type="text",
                                placeholder="Search DN, Project, Notes...",
                                debounce=True
                            )
                        ], md=4),
                        dbc.Col([
                            dbc.Label(html.Span([html.I(className="bi bi-blank")]), style={"visibility": "hidden"}),
                            html.Div([
                                dbc.Button(
                                    [html.I(className="bi bi-plus-circle me-2"), "Create New DN"],
                                    id="open-create-dn-modal",
                                    color="success",
                                    size="sm",
                                    className="me-2"
                                ),
                                dbc.Button(
                                    [html.I(className="bi bi-arrow-clockwise me-2"), "Refresh"],
                                    id="dn-refresh-btn",
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
                    html.Div(id="dn-save-status", className="mb-2", style={"fontSize": "12px"}),
                    create_dn_view_table(table_id="dn-table"),
                ])
            ], className="shadow-sm"),
        ], style={"padding": "20px", "backgroundColor": "#f8f9fa", "minHeight": "100vh"})
    ])


def register_user_options_callback(app):
    """Register callback to preload user options."""
    from dash import Input, Output
    from django.contrib.auth.models import User
    from dash.exceptions import PreventUpdate

    @app.callback(
        Output("user-options", "data"),
        Output("edit-dn-created-by", "options"),
        Output("edit-dn-assigned-to", "options"),
        Input("dn-table", "data"),
        prevent_initial_call=False
    )
    def preload_user_options(table_data):
        """Preload all usernames for dropdown menus."""
        users = User.objects.all().values_list("username", flat=True)
        user_options = [{"label": u, "value": u} for u in users]

        return user_options, user_options, user_options
