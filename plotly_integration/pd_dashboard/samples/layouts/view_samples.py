# Simplified view_samples.py layout without annoying intervals
import dash
from dash import html, dcc, dash_table, Output, Input, State
import dash_bootstrap_components as dbc

from ...main_app import app
from ...shared.styles.common_styles import TABLE_STYLE_CELL, TABLE_STYLE_HEADER

# Field definitions
UP_SAMPLE_FIELDS = [
    {"name": "Project", "id": "project", "editable": False},
    {"name": "Sample #", "id": "sample_number", "editable": False},
    {"name": "Clone", "id": "cell_line", "editable": True},
    {"name": "SIP #", "id": "sip_number", "editable": True},
    {"name": "Dev Stage", "id": "development_stage", "editable": True},
    {"name": "Analyst", "id": "analyst", "editable": True},
    {"name": "Harvest Date", "id": "harvest_date", "editable": True, "type": "datetime"},
    {"name": "Unifi #", "id": "unifi_number", "editable": True},
    {"name": "HF Octet Titer", "id": "hf_octet_titer", "editable": True, "type": "numeric"},
    {"name": "ProAqa HF Titer", "id": "pro_aqa_hf_titer", "editable": True, "type": "numeric"},
    {"name": "ProAqa Eluate Titer", "id": "pro_aqa_e_titer", "editable": True, "type": "numeric"},
    {"name": "Eluate A280", "id": "proa_eluate_a280_conc", "editable": True, "type": "numeric"},
    {"name": "HF Volume", "id": "hccf_loading_volume", "editable": True, "type": "numeric"},
    {"name": "Eluate Volume", "id": "proa_eluate_volume", "editable": True, "type": "numeric"},
    {"name": "ProAqa Recovery", "id": "fast_pro_a_recovery", "editable": False, "type": "numeric"},
    {"name": "A280 Recovery", "id": "purification_recovery_a280", "editable": False, "type": "numeric"},
    {"name": "Note", "id": "note", "editable": True}
]


def create_view_samples_layout():
    """Create simplified view samples layout with save-time conflict detection"""
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-flask text-primary me-2"),
                    "View Fed Batch"
                ]),
                html.P("Browse and edit upstream process samples", className="text-muted")
            ], md=8),
            dbc.Col([
                # Action buttons
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-plus me-1"),
                        "Add Samples"
                    ], href="#!/samples/create", color="primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-save me-1"),
                        "Save Changes"
                    ], id="save-btn", color="success", size="sm", disabled=True),
                    dbc.Button([
                        html.I(className="fas fa-sync-alt me-1"),
                        "Refresh"
                    ], id="refresh-btn", color="outline-secondary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-download me-1"),
                        "Export"
                    ], id="export-samples-btn", color="outline-info", size="sm")
                ], className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Status display
        dbc.Row([
            dbc.Col([
                html.Div(id="update-up-view-status", children="")
            ])
        ], className="mb-2"),

        # Sample Filtering Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Search Samples", className="fw-bold small"),
                                dbc.InputGroup([
                                    dbc.InputGroupText(html.I(className="fas fa-search")),
                                    dbc.Input(
                                        id="samples-search",
                                        placeholder="Search by sample #, clone, project...",
                                        type="text",
                                        debounce=True
                                    )
                                ])
                            ], md=4),
                            dbc.Col([
                                html.Label("Project Filter", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="samples-project-filter",
                                    placeholder="All projects",
                                    clearable=True,
                                    value="all"
                                )
                            ], md=4),
                            dbc.Col([
                                html.Label("Development Stage", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="samples-stage-filter",
                                    options=[
                                        {"label": "All Stages", "value": "all"},
                                        {"label": "MP", "value": "MP"},
                                        {"label": "pMP", "value": "pMP"},
                                        {"label": "BP", "value": "BP"},
                                        {"label": "BP SCC", "value": "BP SCC"},
                                        {"label": "MP SCC", "value": "MP SCC"}
                                    ],
                                    value="all"
                                )
                            ], md=4)
                        ])
                    ])
                ], className="shadow-sm")
            ])
        ], className="mb-3"),

        # Data Table
        dbc.Row([
            dbc.Col([
                dash_table.DataTable(
                    id="view-sample-table",
                    columns=[
                        {
                            "name": col["name"],
                            "id": col["id"],
                            "editable": col["editable"],
                            "type": col.get("type", "text")
                        } for col in UP_SAMPLE_FIELDS
                    ],
                    data=[],
                    editable=True,
                    sort_action="native",
                    filter_action="native",
                    page_action="native",
                    page_size=25,
                    row_deletable=False,
                    row_selectable=False,

                    # Styling
                    style_cell={
                        'textAlign': 'left',
                        'padding': '8px 12px',
                        'fontSize': '13px',
                        'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                        'border': '1px solid #dee2e6',
                        'backgroundColor': 'white',
                        'whiteSpace': 'normal',
                        'overflow': 'hidden',
                        'textOverflow': 'ellipsis',
                        'maxWidth': '150px',
                        'minWidth': '80px'
                    },

                    style_header={
                        'backgroundColor': '#1976d2',
                        'color': 'white',
                        'fontWeight': '600',
                        'textAlign': 'center',
                        'padding': '12px',
                        'border': '1px solid #1976d2',
                        'fontSize': '13px',
                        'textTransform': 'uppercase',
                        'letterSpacing': '0.5px'
                    },

                    # Column widths
                    style_cell_conditional=[
                        {'if': {'column_id': 'sample_number'}, 'width': '90px'},
                        {'if': {'column_id': 'project'}, 'width': '120px'},
                        {'if': {'column_id': 'cell_line'}, 'width': '100px'},
                        {'if': {'column_id': 'sip_number'}, 'width': '80px'},
                        {'if': {'column_id': 'development_stage'}, 'width': '90px'},
                        {'if': {'column_id': 'analyst'}, 'width': '80px'},
                        {'if': {'column_id': 'harvest_date'}, 'width': '110px'},
                        {'if': {'column_id': 'unifi_number'}, 'width': '90px'},
                        {'if': {'column_id': 'note'}, 'width': '150px'},
                        # Recovery fields styling
                        {'if': {'column_id': 'fast_pro_a_recovery'},
                         'backgroundColor': '#f8f9fa', 'fontStyle': 'italic'},
                        {'if': {'column_id': 'purification_recovery_a280'},
                         'backgroundColor': '#f8f9fa', 'fontStyle': 'italic'},
                    ],

                    style_data_conditional=[
                                               # Read-only fields
                                               {
                                                   "if": {"column_id": col["id"]},
                                                   "backgroundColor": "#f8fafc",
                                                   "color": "#4a5568"
                                               } for col in UP_SAMPLE_FIELDS if not col["editable"]
                                           ] + [
                                               # Recovery highlighting
                                               {
                                                   'if': {'column_id': 'fast_pro_a_recovery',
                                                          'filter_query': '{fast_pro_a_recovery} > 80'},
                                                   'backgroundColor': '#d4edda',
                                                   'color': '#155724'
                                               },
                                               {
                                                   'if': {'column_id': 'purification_recovery_a280',
                                                          'filter_query': '{purification_recovery_a280} > 80'},
                                                   'backgroundColor': '#d4edda',
                                                   'color': '#155724'
                                               },
                                               {
                                                   'if': {'column_id': 'fast_pro_a_recovery',
                                                          'filter_query': '{fast_pro_a_recovery} < 50'},
                                                   'backgroundColor': '#f8d7da',
                                                   'color': '#721c24'
                                               },
                                               {
                                                   'if': {'column_id': 'purification_recovery_a280',
                                                          'filter_query': '{purification_recovery_a280} < 50'},
                                                   'backgroundColor': '#f8d7da',
                                                   'color': '#721c24'
                                               }
                                           ],

                    style_table={
                        'overflowX': 'auto',
                        'width': '100%',
                        'minWidth': '100%',
                        'border': '2px solid #1976d2',
                        'borderRadius': '8px'
                    },
                )
            ])
        ]),

        # Hidden stores
        dcc.Store(id="filtered-sample-data", data=[]),
        dcc.Store(id="original-data-store", data={}),
        dcc.Store(id="edited-samples-store", data=[]),

        dcc.Download(id="download-excel"),

    ], fluid=True, style={"padding": "20px", "backgroundColor": "#fafbfc"})