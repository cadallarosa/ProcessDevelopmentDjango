import re
from collections import OrderedDict
from datetime import datetime
from difflib import get_close_matches
import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context
from dash.exceptions import PreventUpdate
from django.db import transaction
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
from plotly_integration.models import LimsDnAssignment, LimsSampleAnalysis, LimsSourceMaterial
from django.contrib.auth.models import User

app = DjangoDash("DnAssignmentApp", external_stylesheets=[dbc.themes.BOOTSTRAP])

TABLE_STYLE_CELL = {
    "textAlign": "left",
    "padding": "2px 4px",
    "fontSize": "11px",
    "border": "1px solid #ddd",
    "minWidth": "100px",
    "width": "100px",
    "maxWidth": "200px",
    "overflow": "hidden",
    "textOverflow": "ellipsis",
}

TABLE_STYLE_HEADER = {
    "backgroundColor": "#0056b3",
    "fontWeight": "bold",
    "color": "white",
    "textAlign": "center",
    "fontSize": "11px",
    "padding": "2px 4px"
}

UNIT_OPS = [
    "ProA", "AEX", "CEX", "CHT", "VI",
    "UFDF", "DF"
]

COLUMN_ORDER = [
    ("dn", "DN"), ("link", "Chromatogram"), ("project_id", "Project ID"), ("unit_operation", "Unit Op"),
    ("scouting_details", "Scouting Details")
    , ("notes", "Notes"),
    ("created_by", "Created By"), ("assigned_to", "Assigned To"),
    ("status", "Status"),
    ("date_created", "Date Created"), ("date_updated", "Date Updated")
]

app.layout = html.Div([
    dcc.Store(id="dn-context", data={"mode": "", "dn": ""}),
    html.Div([
        dcc.Tabs(id="dn-tabs", value="select-tab", children=[
            dcc.Tab(label="View Experiments", value="select-tab", children=[
                html.Div([
                    html.Div([
                        dbc.Button("Refresh Table", id="manual-refresh", size="sm", color="secondary",
                                   className="me-2"),
                        dbc.Button("Create New DN", id="create-new-dn", size="sm", color="primary")
                    ], className="mb-2 d-flex gap-2"),
                    dash_table.DataTable(
                        id="dn-table",
                        columns=[
                            {
                                "name": label,
                                "id": key,
                                "presentation": "markdown" if key == "link" else None,
                                "type": "numeric" if key == "dn" else "text"  # Add this line
                            } for key, label in COLUMN_ORDER
                        ],
                        data=[],
                        editable=False,
                        row_selectable="single",
                        page_action="native",
                        page_current=0,
                        page_size=20,
                        style_table={"height": "75vh", "overflowY": "auto"},
                        style_cell=TABLE_STYLE_CELL,
                        style_header=TABLE_STYLE_HEADER,
                        filter_action="native",
                        sort_action="native",
                        markdown_options={"link_target": "_blank"},
                        style_data_conditional=[]
                    ),
                ], style={"padding": "10px"})
            ]),
            dcc.Tab(label="Create New Experiments", value="edit-tab", children=[
                html.Div([
                    html.Div(id="dn-bulk-table-container", children=[
                        dbc.Button("\u2795 Add Row", id="add-row-btn", color="secondary", size="sm", className="mt-2"),
                        dbc.Button("🧹 Clear Table", id="clear-dn-btn", color="danger", size="sm",
                                   className="ms-2 mt-2"),
                        dash_table.DataTable(
                            id="dn-bulk-table",
                            columns=[{"name": label, "id": key, "editable": True} for key, label in COLUMN_ORDER if
                                     key not in ("dn", "date_created", "date_updated", "id")],
                            data=[{col: "" for col in [
                                "dn",
                                "project_id",
                                "study_name",
                                "assigned_to",
                                "created_by",
                                "scouting_details",
                                "unit_operation",
                                "notes",
                                "status"
                            ]}],
                            editable=True,
                            row_deletable=True,
                            style_cell=TABLE_STYLE_CELL,
                            style_header=TABLE_STYLE_HEADER,
                            style_table={"overflowX": "auto"}
                        ),
                    ]),
                    dbc.Row([
                        dbc.Col(dbc.Button("Save / Update", id="save_button", color="primary", size="sm"),
                                width="auto"),
                        dbc.Col(html.Div(id="save_status", style={"fontSize": "11px", "marginTop": "5px"}),
                                width="auto"),
                    ])
                ], style={"padding": "10px"})
            ]),
            dcc.Tab(label="Edit DN", value="edit-dn-tab", children=[
                html.Div([
                    dbc.Row([
                        dbc.Col(html.H5("Edit DN Details"), width="auto"),
                    ], className="mb-2 g-2"),

                    dash_table.DataTable(
                        id="edit-dn-table",
                        columns=[{"name": label, "id": key, "editable": True}
                                 for key, label in COLUMN_ORDER
                                 if key not in ("date_created", "date_updated", "id")],
                        data=[],
                        editable=True,
                        style_cell=TABLE_STYLE_CELL,
                        style_header=TABLE_STYLE_HEADER,
                        style_table={"overflowX": "auto"}
                    ),

                    dbc.Row([
                        dbc.Col(dbc.Button("🔄 Refresh", id="refresh-edit-dn", size="sm", color="secondary"),
                                width="auto"),
                        dbc.Col(dbc.Button("💾 Save Changes", id="save-edit-dn", size="sm", color="primary"),
                                width="auto")
                    ], className="mb-2 g-2"),

                    html.Br(),

                    dcc.Tabs(id="edit-dn-subtabs", value="source-material-tab", children=[
                        dcc.Tab(label="Source Material", value="source-material-tab", children=[
                            dbc.Form([

                                # Mode Selection
                                dbc.Row([
                                    dbc.Col([
                                        html.Div([
                                            dbc.Label("Mode", style={"marginRight": "20px"}),
                                            dcc.RadioItems(
                                                id="source-material-mode",
                                                options=[
                                                    {"label": "Use Existing", "value": "existing"},
                                                    {"label": "Create New", "value": "new"}
                                                ],
                                                value="existing",
                                                inline=True,
                                                labelStyle={"marginRight": "25px"}
                                            )
                                        ], style={"display": "flex", "alignItems": "center"})
                                    ])
                                ], className="mb-3"),

                                # Existing SM dropdown
                                html.Div(id="existing-sm-section", children=[
                                    dbc.Row([
                                        dbc.Col([
                                            html.Div([
                                                dbc.Label("Select Existing Source Material",
                                                          style={"marginRight": "10px"}),
                                                dcc.Dropdown(
                                                    id="source-material-id-dropdown",
                                                    placeholder="Select...",
                                                    options=[],
                                                    value=None,
                                                    clearable=True,
                                                    style={"flex": 1}
                                                )
                                            ], style={"display": "flex", "alignItems": "center"})
                                        ])
                                    ], className="mb-3")
                                ]),

                                # SM Name
                                html.Div(id="new-sm-section", children=[
                                    dbc.Row([
                                        dbc.Col([
                                            html.Div([
                                                dbc.Label("Source Material Name", style={"marginRight": "10px"}),
                                                dbc.Input(id="source-material-name", type="text",
                                                          placeholder="Enter name",
                                                          style={"flex": 1})
                                            ], style={"display": "flex", "alignItems": "center"})
                                        ])
                                    ], className="mb-3"),

                                    # Pooled Samples with Sample Type Filter
                                    dbc.Row([
                                        dbc.Col([
                                            html.Div([
                                                dbc.Label("Sample Type", style={"marginRight": "10px"}),
                                                dcc.Dropdown(
                                                    id="sample-type-filter",
                                                    options=[
                                                        {"label": "UP", "value": 1},
                                                        {"label": "FB", "value": 2},
                                                        {"label": "PD", "value": 3}
                                                    ],
                                                    value=3,  # Default to PD
                                                    clearable=False,
                                                    style={"width": "150px"}
                                                ),
                                            ], style={"display": "flex", "alignItems": "center",
                                                      "marginBottom": "10px"}),

                                            html.Div([
                                                dbc.Label("Samples Pooled", style={"marginRight": "10px"}),
                                                dcc.Dropdown(
                                                    id="pooled-samples-dropdown",
                                                    multi=True,
                                                    placeholder="Select samples...",
                                                    options=[],
                                                    value=[],
                                                    style={"flex": 1}
                                                )
                                            ], style={"display": "flex", "alignItems": "center"})
                                        ])
                                    ], className="mb-3"),

                                    # --- Sample Details Header ---
                                    dbc.Row([
                                        dbc.Col(html.H5("Sample Details"), width=12)
                                    ], className="mt-4 mb-2"),

                                    # --- Final pH, Conductivity, Concentration, Volume ---
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Label("Final pH"),
                                            dbc.Input(id="final-ph", type="number", placeholder="Final pH", value=None)
                                        ], width=3),
                                        dbc.Col([
                                            dbc.Label("Final Conductivity (mS/cm)"),
                                            dbc.Input(id="final-conductivity", type="number",
                                                      placeholder="Conductivity", value=None)
                                        ], width=3),
                                        dbc.Col([
                                            dbc.Label("Final Concentration (mg/mL)"),
                                            dbc.Input(id="final-concentration", type="number",
                                                      placeholder="Concentration", value=None)
                                        ], width=3),
                                        dbc.Col([
                                            dbc.Label("Final Volume (mL)"),
                                            dbc.Input(id="final-volume", type="number", placeholder="Volume",
                                                      value=None)
                                        ], width=3)
                                    ], className="mb-3"),

                                    # --- Resulting Sample ID ---
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Label("Resulting Sample ID"),
                                            html.Div(id="result-sample-id", style={
                                                "padding": "6px 12px",
                                                "border": "1px solid #ced4da",
                                                "borderRadius": "4px",
                                                "backgroundColor": "#f8f9fa",
                                                "fontSize": "14px"
                                            })
                                        ], width=3)
                                    ], className="mb-3"),

                                    # Process Steps
                                    html.H5("Process Steps", style={"fontWeight": "bold", "marginTop": "15px"}),
                                    dash_table.DataTable(
                                        id='source-material-table',
                                        columns=[
                                            {'name': 'Step', 'id': 'step', 'editable': False},
                                            {'name': 'Process', 'id': 'process', 'editable': True},
                                            {'name': 'Notes', 'id': 'notes', 'editable': True}
                                        ],
                                        editable=True,
                                        style_cell=TABLE_STYLE_CELL,
                                        style_header=TABLE_STYLE_HEADER,
                                        style_table={"overflowX": "auto"}
                                    ),

                                    # Controls
                                    dbc.Row([
                                        dbc.Col(
                                            dbc.Button("➕ Add Step", id="add-source-step", size="sm",
                                                       color="secondary"),
                                            width="auto"),
                                        dbc.Col(dbc.Checkbox(id="confirm-sm-overwrite", className="ms-2"),
                                                width="auto"),
                                        dbc.Col(html.Span("Confirm Overwrite"), width="auto"),
                                        dbc.Col(dbc.Button("💾 Save Source Material", id="save-source-btn", size="sm",
                                                           color="primary"), width="auto"),
                                        dbc.Col(html.Div(id="save_source_status",
                                                         style={"fontSize": "11px", "marginTop": "5px"}))
                                    ], className="mt-2 g-2")
                                ])
                            ]),
                        ]),

                        dcc.Tab(label="Sample Info", value="sample-info-tab", children=[
                            html.H5("Existing Samples"),
                            dash_table.DataTable(
                                id="existing-sample-table",
                                columns=[
                                    {"name": "Sample ID", "id": "sample_id", "editable": False},
                                    {"name": "Sample Date (YYYY-MM-DD)", "id": "sample_date", "editable": True,
                                     "type": "datetime"},
                                    {"name": "Description", "id": "description", "editable": True},
                                    {"name": "A280", "id": "a280_result", "editable": True, "type": "numeric"},
                                    {"name": "Notes", "id": "notes", "editable": True}
                                ],
                                data=[],
                                editable=True,
                                style_cell=TABLE_STYLE_CELL,
                                style_header=TABLE_STYLE_HEADER,
                                style_table={"overflowX": "auto"}
                            ),

                            dbc.Row([
                                dbc.Col(
                                    dbc.Button("💾 Save Existing Samples", id="save-existing-samples", color="primary",
                                               size="sm"), width="auto"),
                                dbc.Col(dbc.Button("🔄 Refresh", id="refresh-existing-samples", color="secondary",
                                                   size="sm"), width="auto")
                            ], className="mt-2 g-2"),

                            html.Br(),
                            html.H5("Create New Samples"),

                            dbc.Button("➕ Add Sample Row", id="add-sample-row", size="sm", color="secondary",
                                       className="mt-2 me-2"),
                            dbc.Button("🧹 Clear Table", id="clear-sample-btn", size="sm", color="danger",
                                       className="mt-2 me-2"),

                            dash_table.DataTable(
                                id="new-sample-table",
                                columns=[
                                    {"name": "Sample ID", "id": "sample_id", "editable": False},
                                    {"name": "Sample Date (YYYY-MM-DD)", "id": "sample_date", "editable": True,
                                     "type": "datetime"},
                                    {"name": "Description", "id": "description", "editable": True},
                                    {"name": "A280", "id": "a280_result", "editable": True, "type": "numeric"},
                                    {"name": "Notes", "id": "notes", "editable": True}
                                ],
                                data=[],
                                editable=True,
                                row_deletable=True,
                                style_cell=TABLE_STYLE_CELL,
                                style_header=TABLE_STYLE_HEADER,
                                style_table={"overflowX": "auto"}
                            ),

                            dbc.Button("💾 Save New Samples", id="save-samples-btn", size="sm", color="primary",
                                       className="mt-2"),
                            html.Div(id="save_samples_status", style={"fontSize": "11px", "marginTop": "5px"})
                        ])
                    ])
                ])
            ]),
            dcc.Tab(label="PD Samples", value="view-pd-tab", children=[
                html.Div([
                    dcc.Store(id="reset-save-pd-trigger", data=False),
                    dcc.Interval(id="reset-save-pd-timer", interval=3000, n_intervals=0, disabled=True),
                    dbc.Row([
                        dbc.Col(dbc.Button("🔄 Refresh", id="refresh-pd-table", color="primary", size="sm"),
                                width="auto"),
                        dbc.Col(dbc.Button("💾 Save", id="update-pd-table", color="primary", size="sm"),
                                width="auto"),
                    ], className="mb-2"),

                    dash_table.DataTable(
                        id="view-pd-table",
                        columns=[
                            {"name": "PD#", "id": "sample_id", "editable": False},
                            {"name": "Project ID", "id": "project_id", "editable": True},
                            {"name": "Linked DN", "id": "dn", "editable": True},
                            {"name": "Description", "id": "description", "editable": True},
                            {"name": "Sample Date (YYYY-MM-DD)", "id": "sample_date", "editable": True},
                            {"name": "A280 (mg/mL)", "id": "a280", "editable": True},
                            {"name": "Analyst", "id": "analyst", "editable": True},
                            {"name": "Notes", "id": "notes", "editable": True},
                        ],
                        data=[],  # Filled by callback
                        style_cell=TABLE_STYLE_CELL,
                        style_header=TABLE_STYLE_HEADER,
                        style_table={"overflowX": "auto"},
                        page_size=25,
                        page_current=0,
                        filter_action="native",
                        sort_action="native",
                    )
                ], style={"padding": "10px"})
            ]),
            dcc.Tab(label="Create New PD#", value="create-pd-tab", children=[
                html.Div([
                    html.Div(id="pd-bulk-table-container", children=[
                        dbc.Button("➕ Add Row", id="add-row-pd-btn", color="secondary", size="sm", className="mt-2"),
                        dbc.Button("🧹 Clear Table", id="clear-pd-btn", color="danger", size="sm",
                                   className="ms-2 mt-2"),

                        dash_table.DataTable(
                            id="pd-bulk-table",
                            columns=[
                                # {"name": "PD#", "id": "sample_id", "editable": False},
                                {"name": "Project ID", "id": "project_id", "editable": True},
                                {"name": "Linked DN", "id": "dn", "editable": True},
                                {"name": "Description", "id": "description", "editable": True},
                                {"name": "Sample Date (YYYY-MM-DD)", "id": "sample_date", "editable": True},
                                {"name": "A280", "id": "a280", "editable": True},
                                {"name": "Analyst", "id": "analyst", "editable": True},
                                {"name": "Notes", "id": "notes", "editable": True},

                            ],
                            data=[{
                                "sample_id": "", "sample_date": "", "description": "",
                                "a280": "", "notes": "", "dn": ""
                            }],
                            editable=True,
                            row_deletable=True,
                            style_cell=TABLE_STYLE_CELL,
                            style_header=TABLE_STYLE_HEADER,
                            style_table={"overflowX": "auto"}
                        ),
                    ]),

                    dbc.Row([
                        dbc.Col(dbc.Button("💾 Save PD Samples", id="save-pd-btn", color="primary", size="sm"),
                                width="auto"),
                        dbc.Col(html.Div(id="save-pd-status", style={"fontSize": "11px", "marginTop": "5px"}),
                                width="auto")
                    ])
                ], style={"padding": "10px"})
            ]),

        ])
    ])
])


# Tab Switching logic
@app.callback(
    Output("dn-tabs", "value"),
    Output("dn-context", "data"),
    Input("create-new-dn", "n_clicks"),
    Input("dn-table", "selected_rows"),
    State("dn-table", "data"),
    prevent_initial_call=True
)
def handle_dn_tab_actions(n_create, selected_rows, table_data):
    from dash import callback_context
    triggered = callback_context.triggered
    if not triggered:
        raise PreventUpdate

    triggered_id = triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "create-new-dn":
        latest = LimsDnAssignment.objects.order_by("-dn").first()
        next_dn = str(int(latest.dn) + 1).zfill(len(latest.dn)) if latest and latest.dn.isdigit() else "0001"
        return "edit-tab", {"mode": "create", "dn": next_dn}

    if triggered_id == "dn-table" and selected_rows and table_data:
        row = table_data[selected_rows[0]]
        return "edit-dn-tab", {"mode": "edit", "dn": row.get("dn"), "source_material_id": row.get("source_material_id")}

    raise PreventUpdate


# Main DN Table Display Logic
@app.callback(
    Output("dn-table", "data"),
    Output("dn-table", "style_data_conditional"),
    Input("manual-refresh", "n_clicks"),
    Input("dn-tabs", "value"),
    prevent_initial_call=False
)
def load_dn_table(n_clicks, tab):
    if tab != "select-tab":
        raise PreventUpdate

    assignments = LimsDnAssignment.objects.all()
    df = pd.DataFrame([{
        "dn": a.dn,
        "project_id": a.project_id,
        "unit_operation": a.unit_operation,
        "scouting_details": a.scouting_details,
        "created_by": a.created_by.username if a.created_by else "",
        "assigned_to": a.assigned_to.username if a.assigned_to else "",
        "notes": a.notes,
        "status": a.status,
        "date_created": a.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "date_updated": a.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        # Add the link column with markdown format
        "link": f'[📊 View](/plotly_integration/dash-app/app/AktaChromatogramApp/?dn={a.dn})'
    } for a in assignments])

    if df.empty:
        return [], []

    try:
        df["dn_numeric"] = pd.to_numeric(df["dn"], errors="coerce")
        df = df.sort_values(by="dn_numeric", ascending=False).drop(columns="dn_numeric")
    except Exception:
        df = df.sort_values(by="dn", ascending=False)

    style_data_conditional = [
        {"if": {"filter_query": '{status} = "Completed"', "column_id": "dn"}, "backgroundColor": "#d4edda",
         "color": "#155724"},
        {"if": {"filter_query": '{status} = "Pending"', "column_id": "dn"}, "backgroundColor": "#fff3cd",
         "color": "#856404"}
    ]
    return df.to_dict("records"), style_data_conditional


# Create/Edit Experiment Logic

def fuzzy_match_username(input_name):
    all_usernames = list(User.objects.values_list("username", flat=True))
    matches = get_close_matches(input_name.strip(), all_usernames, n=1, cutoff=0.6)
    return matches[0] if matches else None


@app.callback(
    Output("dn-bulk-table", "data"),
    Input("add-row-btn", "n_clicks_timestamp"),
    Input("clear-dn-btn", "n_clicks_timestamp"),
    State("dn-bulk-table", "data"),
    prevent_initial_call=True
)
def modify_bulk_table(add_ts, clear_ts, current_data):
    if current_data is None:
        current_data = []

    timestamps = {
        "add": add_ts or 0,
        "clear": clear_ts or 0,
    }
    latest_action = max(timestamps, key=timestamps.get)

    if latest_action == "clear":
        return [{key: "" for key, _ in COLUMN_ORDER if key not in ("date_created", "date_updated", "id")}]

    if latest_action == "add":
        current_data.append({key: "" for key, _ in COLUMN_ORDER if key not in ("date_created", "date_updated", "id")})
        return current_data

    raise PreventUpdate


# Saving or Updating DN database table
@app.callback(
    Output("save_status", "children"),
    Output("dn-bulk-table", "data", allow_duplicate=True),
    Input("save_button", "n_clicks"),
    State("dn-bulk-table", "data"),
    prevent_initial_call=True
)
def save_or_update_dn(n_clicks, bulk_data):
    from plotly_integration.models import LimsDnAssignment
    from django.contrib.auth.models import User
    import datetime

    if not bulk_data:
        raise PreventUpdate

    # Get the most recent DN number in the DB
    last = LimsDnAssignment.objects.order_by("-dn").first()
    next_dn = last.dn if last and isinstance(last.dn, int) else 0

    created = 0
    updated_data = []

    for row in bulk_data:
        # Generate new DN number only if not already present
        if not row.get("dn"):
            next_dn += 1
            row["dn"] = next_dn
        else:
            try:
                row["dn"] = int(row["dn"])
            except ValueError:
                continue  # skip non-integer DN

        try:
            assigned_user = User.objects.filter(username=row.get("assigned_to", "")).first()
            created_user = User.objects.filter(username=row.get("created_by", "")).first()

            LimsDnAssignment.objects.update_or_create(
                dn=row["dn"],
                defaults={
                    "project_id": row.get("project_id", ""),
                    "study_name": row.get("study_name", ""),
                    "scouting_details": row.get("scouting_details", ""),
                    "assigned_to": assigned_user,
                    "created_by": created_user,
                    "unit_operation": row.get("unit_operation", ""),
                    "notes": row.get("notes", ""),
                    "status": row.get("status", "Pending")
                }
            )
            created += 1
            updated_data.append(row)
        except Exception as e:
            print(f"❌ Error processing DN row: {e}")

    return f"✅ Created/Updated: {created}", updated_data


# Edit DN Tab, editing DN save and upload
@app.callback(
    Output("save-edit-dn", "children"),
    Input("save-edit-dn", "n_clicks"),
    State("edit-dn-table", "data"),
    prevent_initial_call=True
)
def save_edit_dn_changes(n_clicks, table_data):
    if not table_data:
        raise PreventUpdate

    updated = 0
    for row in table_data:
        dn_value = row.get("dn")
        if not dn_value:
            continue

        # Resolve ForeignKeys (set to None if not valid)
        assigned_user = User.objects.filter(username=row.get("assigned_to")).first()
        created_user = User.objects.filter(username=row.get("created_by")).first()

        _, created = LimsDnAssignment.objects.update_or_create(
            dn=dn_value,
            defaults={
                "project_id": row.get("project_id", ""),
                "scouting_details": row.get("scouting_details"),
                "assigned_to": assigned_user,
                "created_by": created_user,
                "unit_operation": row.get("unit_operation", ""),
                "notes": row.get("notes", ""),
                "status": row.get("status", "Pending")
            }
        )
        updated += 1

    return f"✅ {updated} DNs saved"


# Edit DN Tab Logic for PD sample Linking
@app.callback(
    Output("edit-dn-table", "data"),
    Output("existing-sample-table", "data"),
    Input("dn-context", "data"),
    prevent_initial_call=True
)
def populate_edit_dn_tab(dn_context):
    if not dn_context or dn_context.get("mode") != "edit":
        raise PreventUpdate

    dn_value = dn_context.get("dn")
    try:
        dn = LimsDnAssignment.objects.get(dn=dn_value)

        dn_row = {
            "dn": dn.dn,
            "project_id": dn.project_id,
            "unit_operation": dn.unit_operation,
            "scouting_details": dn.scouting_details,
            "created_by": dn.created_by.username if dn.created_by else "",
            "assigned_to": dn.assigned_to.username if dn.assigned_to else "",
            "notes": dn.notes,
            "status": dn.status
        }

        samples = LimsSampleAnalysis.objects.filter(dn=dn)
        sample_rows = [{
            "sample_id": s.sample_id,
            "sample_date": s.sample_date.strftime("%Y-%m-%d") if s.sample_date else "",
            "description": s.description,
            "a280_result": s.a280_result,
            "notes": s.notes
        } for s in samples]

        return [dn_row], sample_rows

    except LimsDnAssignment.DoesNotExist:
        return [], []


# Update Existing PD Samples
@app.callback(
    Output("save-existing-samples", "children", allow_duplicate=True),
    Input("save-existing-samples", "n_clicks"),
    State("existing-sample-table", "data"),
    prevent_initial_call=True
)
def save_existing_pd_samples(n_clicks, table_data):
    from plotly_integration.models import LimsSampleAnalysis
    from datetime import datetime

    if not table_data:
        raise PreventUpdate

    updated = 0
    for row in table_data:
        sample_id = row.get("sample_id")
        if not sample_id:
            continue

        try:
            sample = LimsSampleAnalysis.objects.get(sample_id=sample_id)
        except LimsSampleAnalysis.DoesNotExist:
            continue

        try:
            sample.sample_date = datetime.strptime(row.get("sample_date", ""), "%Y-%m-%d").date() if row.get(
                "sample_date") else None
        except Exception:
            sample.sample_date = None

        sample.description = row.get("description", "")
        sample.a280_result = row.get("a280_result") or None
        sample.notes = row.get("notes", "")

        sample.save()
        updated += 1

    return f"✅ {updated} sample(s) updated"


# New Sample Logic
@app.callback(
    Output("new-sample-table", "data"),
    Input("add-sample-row", "n_clicks"),
    Input("clear-sample-btn", "n_clicks"),
    State("new-sample-table", "data"),
    prevent_initial_call=True
)
def handle_new_sample_buttons(add_clicks, clear_clicks, current_data):
    from plotly_integration.models import LimsSampleAnalysis
    import re

    if current_data is None:
        current_data = []

    ctx = dash.callback_context
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "clear-sample-btn":
        return []

    if button_id == "add-sample-row":
        # Get all existing PD numbers (strip 'PD' prefix and convert to int)
        existing_ids = list(
            LimsSampleAnalysis.objects.filter(sample_id__startswith="PD")
            .values_list("sample_id", flat=True)
        )
        current_ids = [row["sample_id"] for row in current_data if row.get("sample_id", "").startswith("PD")]

        all_ids = existing_ids + current_ids
        suffixes = [
            int(re.sub(r"\D", "", sid))
            for sid in all_ids
            if re.match(r"PD\d+$", sid)
        ]
        next_num = max(suffixes, default=0) + 1

        current_data.append({
            "sample_id": f"PD{next_num}",
            "sample_date": "",
            "description": "",
            "a280_result": "",
            "notes": ""
        })

        return current_data

    raise PreventUpdate


@app.callback(
    Output("save_samples_status", "children"),
    Input("save-samples-btn", "n_clicks"),
    State("new-sample-table", "data"),
    State("dn-context", "data"),
    prevent_initial_call=True
)
def save_new_samples(n_clicks, sample_data, dn_context):
    if not dn_context or dn_context.get("mode") != "edit":
        return "❌ Invalid DN context."

    from plotly_integration.models import LimsSampleAnalysis, LimsDnAssignment

    dn_value = dn_context["dn"]
    dn_instance = LimsDnAssignment.objects.filter(dn=dn_value).first()
    if not dn_instance:
        return f"❌ DN {dn_value} not found."

    created, skipped, errors = 0, 0, 0
    for row in sample_data:
        if not row.get("sample_id"):
            skipped += 1
            continue
        try:
            LimsSampleAnalysis.objects.update_or_create(
                sample_id=row["sample_id"],
                sample_type=3,
                defaults={
                    "sample_date": row.get("sample_date") or None,
                    "project_id": dn_instance.project_id,
                    "description": row.get("description", ""),
                    "a280_result": row.get("a280_result") or None,
                    "notes": row.get("notes", ""),
                    "dn": dn_instance,
                    "analyst": "",  # Set this if needed
                }
            )
            created += 1
        except Exception as e:
            print(f"Error saving sample {row['sample_id']}: {e}")
            errors += 1

    return f"✅ Created: {created} | Skipped: {skipped} | Errors: {errors}"


# Source Material Logic
@app.callback(
    Output("existing-sm-section", "style"),
    Output("new-sm-section", "style"),
    Input("source-material-mode", "value"),
    prevent_initial_call=False
)
def toggle_source_material_mode(mode):
    if mode == "existing":
        return {"display": "block"}, {"display": "block"}
    elif mode == "new":
        return {"display": "none"}, {"display": "block"}
    raise PreventUpdate


# Callback to populate dropdowns and preload existing SM info
@app.callback(
    Output("source-material-name", "value"),
    Output("source-material-id-dropdown", "value"),
    Output("source-material-id-dropdown", "options"),
    Output("final-ph", "value"),
    Output("final-conductivity", "value"),
    Output("final-concentration", "value"),
    Output("final-volume", "value"),
    Input("source-material-mode", "value"),
    Input("edit-dn-subtabs", "value"),
    Input("dn-context", "data"),
    Input("source-material-id-dropdown", "value"),  # NEW
    prevent_initial_call=True
)
def preload_source_material(mode, active_subtab, dn_context, selected_sm_id):
    from plotly_integration.models import LimsSourceMaterial, LimsDnAssignment

    if not dn_context or "dn" not in dn_context or active_subtab != "source-material-tab":
        raise PreventUpdate

    try:
        dn_val = int(dn_context["dn"])
    except Exception:
        raise PreventUpdate

    current_dn = LimsDnAssignment.objects.select_related("source_material").filter(dn=dn_val).first()
    if not current_dn:
        raise PreventUpdate

    project_id = current_dn.project_id.strip()
    sm_qs = LimsSourceMaterial.objects.filter(project_id__iexact=project_id).order_by("sm_id")

    sm_dropdown_options = [
        {"label": f"SM{sm.sm_id}: {sm.name or 'Unnamed'}", "value": sm.sm_id}
        for sm in sm_qs
    ]

    sm_name = None
    sm_id = None
    final_ph = None
    final_conductivity = None
    final_concentration = None
    final_volume = None

    if mode == "existing" and selected_sm_id:
        selected_sm = LimsSourceMaterial.objects.filter(sm_id=selected_sm_id).first()
        if selected_sm:
            sm_id = selected_sm.sm_id
            sm_name = selected_sm.name
            final_ph = selected_sm.final_pH
            final_conductivity = selected_sm.final_conductivity
            final_concentration = selected_sm.final_concentration
            final_volume = selected_sm.final_total_volume

    return sm_name, sm_id, sm_dropdown_options, final_ph, final_conductivity, final_concentration, final_volume


# Callback to populate pooled samples dropdown
@app.callback(
    Output("pooled-samples-dropdown", "options"),
    Output("pooled-samples-dropdown", "value"),
    Input("dn-context", "data"),
    Input("source-material-mode", "value"),
    Input("source-material-id-dropdown", "value"),
    Input("sample-type-filter", "value"),
    prevent_initial_call=True
)
def populate_pooled_sample_dropdown(dn_context, mode, sm_id_dropdown, sample_type_filter):
    from plotly_integration.models import LimsSampleAnalysis, LimsDnAssignment, LimsSourceMaterial

    if not dn_context or "dn" not in dn_context:
        raise PreventUpdate

    current_dn = LimsDnAssignment.objects.filter(dn=dn_context["dn"]).first()
    if not current_dn:
        raise PreventUpdate

    project_id = current_dn.project_id

    # Filter samples by project and type
    filtered_samples = LimsSampleAnalysis.objects.filter(
        project_id=project_id,
        sample_type=sample_type_filter
    )

    sample_dict = {s.sample_id: s for s in filtered_samples}
    pooled_values = []

    if mode == "existing" and sm_id_dropdown:
        current_sm = LimsSourceMaterial.objects.filter(sm_id=sm_id_dropdown).first()
        if current_sm:
            pooled_samples = current_sm.samples.all()
            pooled_values = [s.sample_id for s in pooled_samples]

            for s in pooled_samples:
                if s.sample_id not in sample_dict:
                    sample_dict[s.sample_id] = s

    # Build labels with description and date
    options = []
    for sid in sorted(sample_dict):
        s = sample_dict[sid]
        desc = s.description or "No description"
        date_str = f" ({s.sample_date.strftime('%Y-%m-%d')})" if s.sample_date else ""
        label = f"{s.sample_id} — {desc}{date_str}"
        options.append({"label": label, "value": s.sample_id})

    return options, pooled_values


# Callback to handle adding process steps
@app.callback(
    Output("source-material-table", "data"),
    Input("add-source-step", "n_clicks"),
    Input("source-material-id-dropdown", "value"),
    State("source-material-mode", "value"),
    State("dn-context", "data"),
    State("source-material-table", "data"),
    prevent_initial_call=True
)
def update_source_step_table(n_clicks, selected_sm_id, mode, dn_context, current_data):
    from plotly_integration.models import LimsDnAssignment, LimsSourceMaterial, LimsSourceMaterialStep

    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else ""

    if not dn_context or "dn" not in dn_context:
        raise PreventUpdate

    dn_value = dn_context["dn"]
    current_dn = LimsDnAssignment.objects.filter(dn=dn_value).first()
    if not current_dn:
        raise PreventUpdate

    # Auto-load steps from existing source material
    if triggered_id == "source-material-id-dropdown" and mode == "existing":
        if selected_sm_id:
            sm = LimsSourceMaterial.objects.filter(sm_id=selected_sm_id).first()
            if sm:
                steps = LimsSourceMaterialStep.objects.filter(
                    source_material=sm
                ).order_by("step_number")

                return [{
                    "step": step.step_number,
                    "process": step.process,
                    "notes": step.notes
                } for step in steps]

        return []  # No SM linked

    # For "new" mode, start with one blank row
    if triggered_id == "source-material-id-dropdown" and mode == "new":
        return [{
            "step": 1,
            "process": "",
            "notes": ""
        }]

    # If add-source-step button was clicked
    if triggered_id == "add-source-step":
        if not current_data:
            current_data = []

        current_data.append({
            "step": len(current_data) + 1,
            "process": "",
            "notes": ""
        })
        return current_data

    raise PreventUpdate


# Callback to display resulting sample ID independently
@app.callback(
    Output("result-sample-id", "children"),
    [Input("source-material-mode", "value"),
     Input("source-material-id-dropdown", "value")]
)
def update_result_sample_display(mode, selected_sm_id):
    from plotly_integration.models import LimsSourceMaterial

    if mode == "new":
        return ""  # Force clear for new mode

    if mode == "existing" and selected_sm_id:
        sm = LimsSourceMaterial.objects.filter(sm_id=selected_sm_id).first()
        if sm and sm.resulting_sample:
            return sm.resulting_sample.sample_id

    return ""


# # Callback to save or overwrite source material
# @app.callback(
#     Output("save_source_status", "children"),
#     Input("save-source-btn", "n_clicks"),
#     State("confirm-sm-overwrite", "value"),
#     State("source-material-mode", "value"),
#     State("source-material-id-dropdown", "value"),
#     State("source-material-name", "value"),
#     State("final-ph", "value"),
#     State("final-conductivity", "value"),
#     State("final-concentration", "value"),
#     State("final-volume", "value"),
#     State("dn-context", "data"),
#     State("pooled-samples-dropdown", "value"),
#     State("source-material-table", "data"),
#     prevent_initial_call=True
# )
# def save_source_material(n_clicks, confirm_overwrite, mode, selected_sm_id, name,
#                          final_ph, final_cond, final_conc, final_vol, dn_context,
#                          pooled_samples, step_table_data):
#     from datetime import datetime
#     from plotly_integration.models import (
#         LimsSourceMaterial,
#         LimsDnAssignment,
#         LimsSampleAnalysis,
#         LimsSourceMaterialStep
#     )
#
#     if not dn_context or "dn" not in dn_context:
#         return "❌ Missing DN context."
#
#     # Get DN and project info
#     dn_val = dn_context["dn"]
#     dn_record = LimsDnAssignment.objects.filter(dn=dn_val).first()
#     if not dn_record:
#         return f"❌ DN {dn_val} not found."
#
#     project_id = dn_record.project_id
#     sm_id = selected_sm_id if mode == "existing" else dn_val  # Use DN as SM ID if creating new
#
#     existing_sm = LimsSourceMaterial.objects.filter(sm_id=sm_id).first()
#
#     if existing_sm:
#         if not confirm_overwrite:
#             return f"⚠️ SM {sm_id} exists. Confirm overwrite to update."
#
#         # ✅ Update existing SM
#         sm = existing_sm
#         sm.name = name
#         sm.final_pH = final_ph
#         sm.final_conductivity = final_cond
#         sm.final_concentration = final_conc
#         sm.final_total_volume = final_vol
#         sm.project_id = project_id
#         sm.save()
#
#         # Link to DN
#         dn_record.source_material = sm
#         dn_record.save()
#     else:
#         # ✅ Create new PD sample
#         last_pd = LimsSampleAnalysis.objects.filter(sample_id__startswith="PD").order_by("-sample_id").first()
#         next_pd_num = int(last_pd.sample_id[2:]) + 1 if last_pd and last_pd.sample_id[2:].isdigit() else 1
#         pd_id = f"PD{next_pd_num}"
#
#         pd_sample = LimsSampleAnalysis.objects.create(
#             sample_id=pd_id,
#             sample_type=3,
#             sample_date=datetime.today().date(),
#             project_id=project_id,
#             description=f"SM{sm_id}-{name}",
#             analyst="",
#             status="in_progress",
#             dn=dn_record
#         )
#
#         # ✅ Create SM and link PD
#         sm = LimsSourceMaterial.objects.create(
#             sm_id=sm_id,
#             name=name,
#             final_pH=final_ph,
#             final_conductivity=final_cond,
#             final_concentration=final_conc,
#             final_total_volume=final_vol,
#             project_id=project_id,
#             resulting_sample=pd_sample
#         )
#
#         # Link to DN
#         dn_record.source_material = sm
#         dn_record.save()
#
#     # ✅ Link pooled samples
#     if pooled_samples:
#         linked_samples = LimsSampleAnalysis.objects.filter(sample_id__in=pooled_samples)
#         sm.samples.set(linked_samples)
#
#     # ✅ Save process steps
#     LimsSourceMaterialStep.objects.filter(source_material=sm).delete()
#     for i, step in enumerate(step_table_data or [], start=1):
#         process = step.get("process", "").strip()
#         notes = step.get("notes", "").strip()
#         if process:
#             LimsSourceMaterialStep.objects.create(
#                 source_material=sm,
#                 step_number=i,
#                 process=process,
#                 notes=notes
#             )
#
#     return f"✅ Source Material SM{sm_id} {'updated' if existing_sm else 'created'} and linked to PD#{sm.resulting_sample.sample_id}"


@app.callback(
    Output("save_source_status", "children"),
    Input("save-source-btn", "n_clicks"),
    State("confirm-sm-overwrite", "value"),
    State("source-material-mode", "value"),
    State("source-material-id-dropdown", "value"),
    State("source-material-name", "value"),
    State("final-ph", "value"),
    State("final-conductivity", "value"),
    State("final-concentration", "value"),
    State("final-volume", "value"),
    State("dn-context", "data"),
    State("pooled-samples-dropdown", "value"),
    State("source-material-table", "data"),
    prevent_initial_call=True
)
def save_source_material(n_clicks, confirm_overwrite, mode, selected_sm_id, name,
                         final_ph, final_cond, final_conc, final_vol, dn_context,
                         pooled_samples, step_table_data):
    from datetime import datetime
    from plotly_integration.models import (
        LimsSourceMaterial,
        LimsDnAssignment,
        LimsSampleAnalysis,
        LimsSourceMaterialStep
    )

    if not dn_context or "dn" not in dn_context:
        return "❌ Missing DN context."

    dn_val = dn_context["dn"]
    dn_record = LimsDnAssignment.objects.filter(dn=dn_val).first()
    if not dn_record:
        return f"❌ DN {dn_val} not found."

    project_id = dn_record.project_id
    sm_id = selected_sm_id if mode == "existing" else dn_val
    existing_sm = LimsSourceMaterial.objects.filter(sm_id=selected_sm_id).first() if mode == "existing" else None

    def has_changes(sm):
        if not sm:
            return True
        if sm.name != name or sm.final_pH != final_ph or sm.final_conductivity != final_cond or \
                sm.final_concentration != final_conc or sm.final_total_volume != final_vol:
            return True
        current_samples = set(sm.samples.values_list("sample_id", flat=True))
        if set(pooled_samples or []) != current_samples:
            return True
        existing_steps = list(
            LimsSourceMaterialStep.objects.filter(source_material=sm).order_by("step_number").values("process",
                                                                                                     "notes"))
        incoming_steps = list(filter(lambda s: s.get("process", "").strip(), step_table_data or []))
        incoming_steps_clean = [{"process": s["process"].strip(), "notes": s.get("notes", "").strip()} for s in
                                incoming_steps]
        return existing_steps != incoming_steps_clean

    if mode == "existing" and existing_sm:
        changed = has_changes(existing_sm)

        if changed and not confirm_overwrite:
            return f"⚠️ Changes detected in SM {selected_sm_id}. Check 'Confirm Overwrite' to apply changes."

        if changed and confirm_overwrite:
            # ✅ Overwrite existing SM
            sm = existing_sm
            sm.name = name
            sm.final_pH = final_ph
            sm.final_conductivity = final_cond
            sm.final_concentration = final_conc
            sm.final_total_volume = final_vol
            sm.project_id = project_id
            sm.save()

            dn_record.source_material = sm
            dn_record.save()
        else:
            # ✅ Just link existing SM with no changes
            dn_record.source_material = existing_sm
            dn_record.save()
            return f"✅ Linked existing Source Material SM{selected_sm_id} to DN {dn_val} without changes."

    else:
        # ✅ Create new PD sample
        last_pd = LimsSampleAnalysis.objects.filter(sample_id__startswith="PD").order_by("-sample_id").first()
        next_pd_num = int(last_pd.sample_id[2:]) + 1 if last_pd and last_pd.sample_id[2:].isdigit() else 1
        pd_id = f"PD{next_pd_num}"

        pd_sample = LimsSampleAnalysis.objects.create(
            sample_id=pd_id,
            sample_type=3,
            sample_date=datetime.today().date(),
            project_id=project_id,
            description=f"SM{dn_val}-{name}",
            analyst="",
            status="in_progress",
            dn=dn_record
        )

        sm = LimsSourceMaterial.objects.create(
            sm_id=dn_val,
            name=name,
            final_pH=final_ph,
            final_conductivity=final_cond,
            final_concentration=final_conc,
            final_total_volume=final_vol,
            project_id=project_id,
            resulting_sample=pd_sample
        )

        dn_record.source_material = sm
        dn_record.save()

    # ✅ Link pooled samples
    if pooled_samples:
        linked_samples = LimsSampleAnalysis.objects.filter(sample_id__in=pooled_samples)
        sm.samples.set(linked_samples)

    # ✅ Save process steps
    LimsSourceMaterialStep.objects.filter(source_material=sm).delete()
    for i, step in enumerate(step_table_data or [], start=1):
        process = step.get("process", "").strip()
        notes = step.get("notes", "").strip()
        if process:
            LimsSourceMaterialStep.objects.create(
                source_material=sm,
                step_number=i,
                process=process,
                notes=notes
            )

    return f"✅ Source Material SM{sm.sm_id} {'updated' if existing_sm and confirm_overwrite else 'created'} and linked to PD#{sm.resulting_sample.sample_id}"


# View PD Samples
@app.callback(
    Output("view-pd-table", "data"),
    Output("view-pd-table", "style_data_conditional"),
    Input("refresh-pd-table", "n_clicks"),
    Input("dn-tabs", "value"),
    prevent_initial_call=False
)
def load_pd_table(n_clicks, tab_value):
    """
        Load PD sample table.
        Triggers on refresh button click or tab selection.
        """

    if tab_value != "view-pd-tab":
        raise PreventUpdate

    samples = LimsSampleAnalysis.objects.filter(sample_type=3)
    df = pd.DataFrame([{
        "sample_id": s.sample_id,
        "sample_date": s.sample_date.isoformat() if s.sample_date else "",
        "project_id": s.project_id,
        "analyst": s.analyst,
        "description": s.description,
        "a280": s.a280_result,
        "notes": s.notes,
        "dn": s.dn.dn if s.dn else "",
        "status": s.status,
        "date_created": s.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "date_updated": s.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
    } for s in samples])

    if df.empty:
        return [], []

    # Optional sort by descending PD#
    try:
        df["pd_numeric"] = pd.to_numeric(df["sample_id"].str.extract(r"PD(\d+)", expand=False), errors="coerce")
        df = df.sort_values(by="pd_numeric", ascending=False).drop(columns="pd_numeric")
    except Exception:
        df = df.sort_values(by="sample_id", ascending=False)

    style_data_conditional = [
        {"if": {"filter_query": '{status} = "complete"', "column_id": "sample_id"},
         "backgroundColor": "#d4edda", "color": "#155724"},
        {"if": {"filter_query": '{status} = "in_progress"', "column_id": "sample_id"},
         "backgroundColor": "#fff3cd", "color": "#856404"},
        {"if": {"filter_query": '{status} = "review"', "column_id": "sample_id"},
         "backgroundColor": "#d1ecf1", "color": "#0c5460"},
    ]

    return df.to_dict("records"), style_data_conditional


# Saving Samples in view PD samples
@app.callback(
    Output("update-pd-table", "children"),
    Output("reset-save-pd-timer", "disabled"),
    Input("update-pd-table", "n_clicks_timestamp"),
    Input("reset-save-pd-timer", "n_intervals"),
    State("reset-save-pd-timer", "disabled"),
    State("view-pd-table", "derived_virtual_data"),  # ✅ Correct source of all visible rows
    State("view-pd-table", "page_current"),
    State("view-pd-table", "page_size"),
    prevent_initial_call=True
)
def save_or_reset_button(save_ts, interval_n, interval_disabled, visible_data, page_current, page_size):
    from plotly_integration.models import LimsSampleAnalysis, LimsDnAssignment
    import datetime

    if not interval_disabled:
        return "💾 Save", True

    if not visible_data:
        return "💾 Save", True

    start = page_current * page_size
    end = start + page_size
    page_rows = visible_data[start:end]  # ✅ Slice to current page

    created, updated, skipped, errors = 0, 0, 0, 0

    for row in page_rows:
        try:
            sample_id = row.get("sample_id")
            if not sample_id:
                skipped += 1
                continue

            existing = LimsSampleAnalysis.objects.filter(sample_id=sample_id).first()
            dn_val = row.get("dn")
            dn_obj = LimsDnAssignment.objects.filter(dn=dn_val).first() if dn_val else None

            sample_date = row.get("sample_date")
            if sample_date and isinstance(sample_date, str):
                try:
                    sample_date = datetime.datetime.fromisoformat(sample_date).date()
                except ValueError:
                    sample_date = None

            new_data = {
                "sample_type": 3,
                "sample_date": sample_date if isinstance(sample_date, datetime.date) else None,
                "project_id": row.get("project_id") or "",
                "description": row.get("description", ""),
                "analyst": row.get("analyst", ""),
                "a280_result": float(row.get("a280")) if row.get("a280") not in [None, ""] else None,
                "notes": row.get("notes", ""),
                "dn": dn_obj,
                "status": row.get("status", "in_progress"),
            }

            if existing:
                has_changes = any(getattr(existing, k) != v for k, v in new_data.items())
                if has_changes:
                    for k, v in new_data.items():
                        setattr(existing, k, v)
                    existing.save()
                    updated += 1
                else:
                    skipped += 1
            else:
                LimsSampleAnalysis.objects.create(sample_id=sample_id, **new_data)
                created += 1

        except Exception as e:
            print(f"❌ Error saving PD sample {sample_id}: {e}")
            errors += 1

    return f"✅ Saved! ({created} new, {updated} updated)", False


# PD Samples Bulk Table Logic
@app.callback(
    Output("pd-bulk-table", "data"),
    Input("add-row-pd-btn", "n_clicks"),
    Input("clear-pd-btn", "n_clicks"),
    State("pd-bulk-table", "data"),
    prevent_initial_call=True
)
def handle_pd_sample_buttons(add_clicks, clear_clicks, current_data):
    import dash

    if current_data is None:
        current_data = []

    ctx = dash.callback_context
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    default_row = {
        "sample_date": "",
        "description": "",
        "a280": "",
        "notes": "",
        "dn": "",
        "project_id": "",
        "analyst": "",
        "status": "in_progress"
    }

    if button_id == "clear-pd-btn":
        return [default_row]

    if button_id == "add-row-pd-btn":
        return current_data + [default_row]

    return current_data


@app.callback(
    Output("save-pd-status", "children"),
    Output("pd-bulk-table", "data", allow_duplicate=True),
    Input("save-pd-btn", "n_clicks"),
    State("pd-bulk-table", "data"),
    prevent_initial_call=True
)
def save_pd_samples(n_clicks, table_data):
    if not table_data:
        raise PreventUpdate

    # Get the current highest PD number
    last = LimsSampleAnalysis.objects.filter(sample_id__startswith="PD").order_by("-sample_id").first()
    if last and last.sample_id[2:].isdigit():
        next_pd_num = int(last.sample_id[2:])
    else:
        next_pd_num = 0

    saved = 0
    new_rows = []
    for row in table_data:
        # Increment for each sample
        next_pd_num += 1
        pd_id = f"PD{next_pd_num}"

        try:
            sample_date = datetime.strptime(row.get("sample_date", ""), "%Y-%m-%d").date()
        except Exception:
            sample_date = None

        project_id = row.get("project_id", "").strip()
        analyst = row.get("analyst", "").strip()
        status = row.get("status", "in_progress")

        # if not project_id or not analyst:
        #     continue

        dn_value = row.get("dn")
        dn_obj = LimsDnAssignment.objects.filter(dn=dn_value).first() if dn_value else None

        LimsSampleAnalysis.objects.update_or_create(
            sample_id=pd_id,
            defaults={
                "sample_type": 3,
                "sample_date": sample_date,
                "project_id": project_id,
                "description": row.get("description", ""),
                "analyst": analyst,
                "dn": dn_obj,
                "a280_result": row.get("a280") or None,
                "notes": row.get("notes", ""),
                "status": status
            }
        )
        saved += 1

    return f"✅ {saved} PD sample(s) created.", [{
        "sample_id": "", "sample_date": "", "description": "",
        "a280": "", "notes": "", "dn": "", "project_id": "", "analyst": "", "status": "in_progress"
    }]
