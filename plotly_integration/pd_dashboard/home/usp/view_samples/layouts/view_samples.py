# USP view_samples layout
import dash
from dash import html, dcc, dash_table, Output, Input, State
import dash_bootstrap_components as dbc

from plotly_integration.pd_dashboard.main_app import app
from plotly_integration.pd_dashboard.shared.styles.common_styles import TABLE_STYLE_CELL, TABLE_STYLE_HEADER

# Field definitions for USP samples
USP_SAMPLE_FIELDS = [
    {"name": "Sample #", "id": "sample_number", "editable": False},
    {"name": "Project ID", "id": "project_id", "editable": True},
    {"name": "Reactor Type", "id": "reactor_type", "editable": True, "presentation": "dropdown"},
    {"name": "Clone", "id": "cell_line", "editable": True},
    {"name": "Run Date", "id": "run_date", "editable": True, "type": "datetime"},
    {"name": "Harvest Date", "id": "harvest_date", "editable": True, "type": "datetime"},
    {"name": "Duration (days)", "id": "culture_duration", "editable": True, "type": "numeric"},
    {"name": "Max VCD", "id": "max_vcd", "editable": True, "type": "numeric"},
    {"name": "Viability %", "id": "viability", "editable": True, "type": "numeric"},
    {"name": "Titer (g/L)", "id": "final_titer", "editable": True, "type": "numeric"},
    {"name": "Volume (L)", "id": "culture_volume", "editable": True, "type": "numeric"},
    {"name": "pH", "id": "ph", "editable": True, "type": "numeric"},
    {"name": "DO %", "id": "do_percent", "editable": True, "type": "numeric"},
    {"name": "Temp (°C)", "id": "temperature", "editable": True, "type": "numeric"},
    {"name": "Feed Strategy", "id": "feed_strategy", "editable": True},
    {"name": "Note", "id": "note", "editable": True},
    {"name": "Created Date", "id": "created_date", "editable": False, "type": "datetime"}
]

# Reactor type options for dropdown
REACTOR_TYPE_OPTIONS = [
    {"label": "Bioreactor", "value": "bioreactor"},
    {"label": "Flask", "value": "flask"},
    {"label": "Wave Bag", "value": "wave"},
    {"label": "AMBR", "value": "ambr"},
    {"label": "DasGip", "value": "dasgip"},
    {"label": "Other", "value": "other"}
]


def create_view_samples_layout():
    """Create USP view samples layout"""
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-biohazard text-primary me-2"),
                    "View USP Samples"
                ]),
                html.P("Browse and edit upstream process samples", className="text-muted")
            ], md=8),
            dbc.Col([
                # Action buttons
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-plus me-1"),
                        "Add Samples"
                    ], href="#!/usp/samples/create", color="primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-layer-group me-1"),
                        "Sample Sets"
                    ], href="#!/usp/samples/sets", color="outline-primary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-save me-1"),
                        "Save Changes"
                    ], id="usp-save-btn", color="success", size="sm", disabled=True),
                    dbc.Button([
                        html.I(className="fas fa-sync-alt me-1"),
                        "Refresh"
                    ], id="usp-refresh-btn", color="outline-secondary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-download me-1"),
                        "Export"
                    ], id="usp-export-samples-btn", color="outline-info", size="sm")
                ], className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Status display
        dbc.Row([
            dbc.Col([
                html.Div(id="usp-update-status", children="")
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
                                        id="usp-samples-search",
                                        placeholder="Search by sample #, clone, project...",
                                        type="text",
                                        debounce=True
                                    )
                                ])
                            ], md=3),
                            dbc.Col([
                                html.Label("Project ID Filter", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="usp-project-filter",
                                    placeholder="All projects",
                                    clearable=True,
                                    value="all"
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("Reactor Type Filter", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="usp-reactor-filter",
                                    options=REACTOR_TYPE_OPTIONS + [{"label": "All", "value": "all"}],
                                    placeholder="All reactor types",
                                    clearable=True,
                                    value="all"
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("Date Range", className="fw-bold small"),
                                dcc.DatePickerRange(
                                    id="usp-date-range",
                                    display_format="YYYY-MM-DD",
                                    style={"width": "100%"}
                                )
                            ], md=3)
                        ])
                    ])
                ], className="shadow-sm mb-4")
            ])
        ]),

        # Sample Statistics
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.I(className="fas fa-vials fa-2x text-primary mb-2"),
                                    html.H5(id="usp-total-samples", className="mb-1"),
                                    html.P("Total Samples", className="text-muted small mb-0")
                                ], className="text-center")
                            ], md=3),
                            dbc.Col([
                                html.Div([
                                    html.I(className="fas fa-project-diagram fa-2x text-info mb-2"),
                                    html.H5(id="usp-total-projects", className="mb-1"),
                                    html.P("Active Projects", className="text-muted small mb-0")
                                ], className="text-center")
                            ], md=3),
                            dbc.Col([
                                html.Div([
                                    html.I(className="fas fa-flask fa-2x text-success mb-2"),
                                    html.H5(id="usp-avg-titer", className="mb-1"),
                                    html.P("Avg. Titer (g/L)", className="text-muted small mb-0")
                                ], className="text-center")
                            ], md=3),
                            dbc.Col([
                                html.Div([
                                    html.I(className="fas fa-microscope fa-2x text-warning mb-2"),
                                    html.H5(id="usp-avg-vcd", className="mb-1"),
                                    html.P("Avg. Max VCD", className="text-muted small mb-0")
                                ], className="text-center")
                            ], md=3)
                        ])
                    ])
                ], className="shadow-sm mb-4")
            ])
        ]),

        # Main data table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dash_table.DataTable(
                            id="usp-samples-table",
                            columns=[{"name": field["name"], "id": field["id"], "type": field.get("type", "text"),
                                    "editable": field["editable"], 
                                    "presentation": field.get("presentation", "input")} 
                                   for field in USP_SAMPLE_FIELDS],
                            data=[],
                            editable=True,
                            filter_action="native",
                            sort_action="native",
                            sort_mode="multi",
                            row_deletable=False,
                            selected_columns=[],
                            selected_rows=[],
                            page_action="native",
                            page_current=0,
                            page_size=25,
                            style_cell=TABLE_STYLE_CELL,
                            style_header=TABLE_STYLE_HEADER,
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': 'rgb(248, 248, 248)'
                                },
                                {
                                    'if': {'state': 'selected'},
                                    'backgroundColor': 'rgb(230, 240, 255)',
                                    'border': '1px solid rgb(100, 150, 255)'
                                },
                                # Highlight cells by reactor type
                                {
                                    'if': {
                                        'filter_query': '{reactor_type} = bioreactor',
                                        'column_id': 'reactor_type'
                                    },
                                    'backgroundColor': '#e3f2fd',
                                    'fontWeight': 'bold'
                                },
                                {
                                    'if': {
                                        'filter_query': '{reactor_type} = dasgip',
                                        'column_id': 'reactor_type'
                                    },
                                    'backgroundColor': '#f3e5f5',
                                    'fontWeight': 'bold'
                                }
                            ],
                            dropdown={
                                "reactor_type": {
                                    "options": REACTOR_TYPE_OPTIONS
                                }
                            },
                            export_format="xlsx",
                            export_headers="display"
                        )
                    ], className="p-0")
                ], className="shadow-sm")
            ])
        ]),

        # Hidden stores for state management
        dcc.Store(id="usp-samples-data-store", data={}),
        dcc.Store(id="usp-modified-rows-store", data=[]),
        dcc.Download(id="usp-download-dataframe"),
        
        # No interval component - refresh is manual only
        
    ], fluid=True)