from dash import html, dash_table, dcc
import dash_bootstrap_components as dbc

# Import field definitions
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


def create_sample_set_detail_layout(query_params):
    """Create detailed view layout for a specific sample set"""
    sample_set_id = query_params.get('id', [None])[0] if query_params else None

    if not sample_set_id:
        return dbc.Container([
            dbc.Alert("No sample set ID provided", color="warning")
        ])

    return dbc.Container([
        # Store for current sample set ID
        dcc.Store(id="current-sample-set-id", data=sample_set_id),

        # Header
        dbc.Row([
            dbc.Col([
                html.Div(id="sample-set-basic-info", children=[
                    dbc.Spinner(html.Div("Loading...", className="text-center"), color="primary")
                ])
            ], md=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-arrow-left me-1"),
                        "Back to Sets"
                    ], href="#!/sample-sets", color="outline-secondary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-sync-alt me-1"),
                        "Refresh"
                    ], id="refresh-details-btn", color="outline-primary", size="sm")
                ], className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Tabs Section
        dbc.Row([
            dbc.Col([
                dbc.Tabs([
                    dbc.Tab([
                        # Samples Table
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5([
                                    html.I(className="fas fa-table me-2"),
                                    "Sample Details"
                                ], className="mb-0")
                            ]),
                            dbc.CardBody([
                                # The actual DataTable with correct fields
                                dash_table.DataTable(
                                    id="sample-set-details-table",
                                    columns=[
                                        {
                                            "name": col["name"],
                                            "id": col["id"],
                                            "editable": col.get("editable", False),
                                            "type": col.get("type", "text")
                                        } for col in UP_SAMPLE_FIELDS
                                    ],
                                    data=[],  # Will be populated by callback
                                    editable=False,
                                    sort_action="native",
                                    filter_action="native",
                                    page_action="native",
                                    page_current=0,
                                    page_size=15,
                                    style_table={"overflowX": "auto"},
                                    style_cell={
                                        "textAlign": "left",
                                        "padding": "8px",
                                        "fontSize": "14px",
                                        "fontFamily": "system-ui",
                                        "whiteSpace": "normal",
                                        "height": "auto",
                                        "minWidth": "100px"
                                    },
                                    style_header={
                                        "backgroundColor": "#f8f9fa",
                                        "fontWeight": "bold",
                                        "border": "1px solid #dee2e6",
                                        "textAlign": "center"
                                    },
                                    style_data_conditional=[
                                        {
                                            "if": {"row_index": "odd"},
                                            "backgroundColor": "#f8f9fa"
                                        }
                                    ]
                                )
                            ])
                        ], className="shadow-sm mt-3")
                    ], label="Sample Details", tab_id="samples-tab"),

                    dbc.Tab([
                        # Analysis Cards Section
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5([
                                    html.I(className="fas fa-chart-line me-2"),
                                    "Analysis Status"
                                ], className="mb-0")
                            ]),
                            dbc.CardBody([
                                html.Div(id="analysis-status-cards", children=[
                                    dbc.Spinner(html.Div("Loading analysis status...", className="text-center"),
                                                color="primary")
                                ])
                            ])
                        ], className="shadow-sm mt-3")
                    ], label="Analysis Status", tab_id="analysis-tab")

                ], active_tab="samples-tab")
            ])
        ])

    ], fluid=True, style={"padding": "20px"})


# ==============================================================================
# CALLBACKS: plotly_integration/pd_dashboard/home/cld/sample_sets/callbacks/sample_set_details.py
# ==============================================================================

from dash import callback, Input, Output, State
import dash_bootstrap_components as dbc
from dash import html
from plotly_integration.pd_dashboard.main_app import app
from plotly_integration.models import LimsSampleSet, LimsUpstreamSamples


def build_sample_row_with_recoveries(s):
    """Build sample row data (same as view_samples)"""
    try:
        # Calculate recoveries if possible
        fast_pro_a_recovery = None
        purification_recovery_a280 = None

        if s.pro_aqa_hf_titer and s.pro_aqa_e_titer and s.pro_aqa_hf_titer > 0:
            fast_pro_a_recovery = round((s.pro_aqa_e_titer / s.pro_aqa_hf_titer) * 100, 1)

        if s.proa_eluate_a280_conc and s.hccf_loading_volume and s.proa_eluate_volume:
            if s.proa_eluate_a280_conc > 0 and s.hccf_loading_volume > 0:
                purification_recovery_a280 = round(
                    (s.proa_eluate_a280_conc * s.proa_eluate_volume) /
                    (s.hccf_loading_volume * 100), 1
                )

        return {
            "project": s.project or "",
            "sample_number": s.sample_number or "",
            "cell_line": s.cell_line or "",
            "sip_number": s.sip_number or "",
            "development_stage": s.development_stage or "",
            "analyst": s.analyst or "",
            "harvest_date": s.harvest_date.strftime('%Y-%m-%d') if s.harvest_date else "",
            "unifi_number": s.unifi_number or "",
            "hf_octet_titer": s.hf_octet_titer,
            "pro_aqa_hf_titer": s.pro_aqa_hf_titer,
            "pro_aqa_e_titer": s.pro_aqa_e_titer,
            "proa_eluate_a280_conc": s.proa_eluate_a280_conc,
            "hccf_loading_volume": s.hccf_loading_volume,
            "proa_eluate_volume": s.proa_eluate_volume,
            "fast_pro_a_recovery": fast_pro_a_recovery,
            "purification_recovery_a280": purification_recovery_a280,
            "note": s.note or ""
        }
    except Exception as e:
        print(f"Error building row for sample {s.sample_number}: {e}")
        return {}


@app.callback(
    Output("sample-set-basic-info", "children"),
    Input("current-sample-set-id", "data")
)
def update_sample_set_basic_info(sample_set_id):
    """Update the basic sample set information at the top"""
    print(f"DEBUG: update_sample_set_basic_info called with ID: {sample_set_id}")

    if not sample_set_id:
        return dbc.Alert("No sample set selected", color="warning")

    try:
        sample_set = LimsSampleSet.objects.get(id=sample_set_id)
        print(f"DEBUG: Found sample set: {sample_set.set_name}")

        return html.Div([
            html.H2([
                html.I(className="fas fa-info-circle text-primary me-2"),
                sample_set.set_name
            ], className="mb-2"),
            html.P([
                html.Strong("Project: "), sample_set.project_id, " | ",
                html.Strong("SIP: "), sample_set.sip_number or "N/A", " | ",
                html.Strong("Stage: "), sample_set.development_stage or "N/A", " | ",
                html.Strong("Sample Count: "), str(sample_set.sample_count)
            ], className="text-muted mb-0")
        ])

    except Exception as e:
        print(f"ERROR: loading sample set basic info: {e}")
        return dbc.Alert(f"Error loading sample set: {str(e)}", color="danger")


@app.callback(
    Output("sample-set-details-table", "data"),
    Input("current-sample-set-id", "data")
)
def load_sample_set_details_table(sample_set_id):
    """Load sample set details using the same method as view samples"""
    print(f"DEBUG: load_sample_set_details_table called with ID: {sample_set_id}")

    if not sample_set_id:
        print("DEBUG: No sample set ID provided")
        return []

    try:
        # Get the sample set
        sample_set = LimsSampleSet.objects.get(id=sample_set_id)
        print(f"DEBUG: Found sample set: {sample_set.set_name}")

        # Get members and extract sample_ids
        members = sample_set.members.all()
        print(f"DEBUG: Found {len(members)} members")

        if not members:
            print("DEBUG: No members found")
            return []

        # Extract sample numbers from members (FB123 -> 123)
        sample_numbers = []
        for member in members:
            sample_id = member.sample.sample_id
            print(f"DEBUG: Found sample_id: {sample_id}")
            if sample_id.startswith('FB'):
                sample_number = sample_id[2:]  # Remove 'FB' prefix
                sample_numbers.append(sample_number)
                print(f"DEBUG: Extracted sample_number: {sample_number}")

        if not sample_numbers:
            print("DEBUG: No valid sample numbers found")
            return []

        # Query upstream samples using the same method as view samples
        samples_query = LimsUpstreamSamples.objects.filter(
            sample_type=2,
            sample_number__in=sample_numbers
        ).order_by("sample_number")

        samples = list(samples_query)
        print(f"DEBUG: Found {len(samples)} upstream samples")

        # Build data using the same method as view samples
        data = []
        for s in samples:
            row = build_sample_row_with_recoveries(s)
            if row:  # Only add if row was built successfully
                data.append(row)

        print(f"DEBUG: Built {len(data)} rows")
        return data

    except Exception as e:
        print(f"ERROR: in load_sample_set_details_table: {e}")
        return []


@app.callback(
    Output("analysis-status-cards", "children"),
    Input("current-sample-set-id", "data")
)
def update_analysis_status_cards(sample_set_id):
    """Update analysis status cards in single column layout"""
    print(f"DEBUG: update_analysis_status_cards called with ID: {sample_set_id}")

    if not sample_set_id:
        return dbc.Alert("No sample set selected", color="warning")

    try:
        # Analysis types
        analysis_types = ['SEC', 'AKTA', 'Titer', 'CE-SDS', 'cIEF', 'Mass Check', 'Glycan', 'HCP', 'ProA']

        # Create cards in single column layout
        cards = []
        for analysis_type in analysis_types:
            card = dbc.Card([
                dbc.CardHeader([
                    html.H6([
                        html.I(className="fas fa-flask me-2"),
                        analysis_type
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Badge("Not Requested", color="secondary", className="me-2"),
                            html.Span("No analysis requested", className="text-muted")
                        ], md=8),
                        dbc.Col([
                            dbc.Button([
                                html.I(className="fas fa-play me-1"),
                                "Request"
                            ], color="outline-primary", size="sm", className="w-100")
                        ], md=4)
                    ])
                ])
            ], className="mb-2")
            cards.append(card)

        return cards

    except Exception as e:
        print(f"ERROR: loading analysis status: {e}")
        return dbc.Alert(f"Error loading analysis status: {str(e)}", color="danger")


print("Complete sample set details layout and callbacks loaded")