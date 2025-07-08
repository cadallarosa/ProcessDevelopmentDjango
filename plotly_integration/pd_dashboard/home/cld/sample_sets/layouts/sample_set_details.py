# plotly_integration/pd_dashboard/home/cld/sample_sets/layouts/sample_set_details.py
# Complete file - Restructured with only 2 tabs: Overview and Analysis

from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from plotly_integration.models import (
    LimsSampleSet, LimsSampleSetMembership,
    LimsSampleAnalysis, LimsSecResult
)

# Field definitions for upstream samples table (from view_samples)
UP_SAMPLE_FIELDS = [
    {"name": "Project", "id": "project", "editable": False},
    {"name": "Sample #", "id": "sample_number", "editable": False},
    {"name": "Cell Line", "id": "cell_line", "editable": False},
    {"name": "SIP", "id": "sip_number", "editable": False},
    {"name": "Stage", "id": "development_stage", "editable": False},
    {"name": "Analyst", "id": "analyst", "editable": False},
    {"name": "Harvest Date", "id": "harvest_date", "editable": False},
    {"name": "Unifi #", "id": "unifi_number", "editable": False},
    {"name": "HF Octet", "id": "hf_octet_titer", "editable": False, "type": "numeric", "format": {"specifier": ".1f"}},
    {"name": "ProA QA HF", "id": "pro_aqa_hf_titer", "editable": False, "type": "numeric",
     "format": {"specifier": ".1f"}},
    {"name": "ProA QA E", "id": "pro_aqa_e_titer", "editable": False, "type": "numeric",
     "format": {"specifier": ".1f"}},
    {"name": "ProA Eluate A280", "id": "proa_eluate_a280_conc", "editable": False, "type": "numeric",
     "format": {"specifier": ".1f"}},
    {"name": "HCCF Vol", "id": "hccf_loading_volume", "editable": False, "type": "numeric",
     "format": {"specifier": ".1f"}},
    {"name": "ProA Eluate Vol", "id": "proa_eluate_volume", "editable": False, "type": "numeric",
     "format": {"specifier": ".1f"}},
    {"name": "Fast ProA Rec (%)", "id": "fast_pro_a_recovery", "editable": False, "type": "numeric",
     "format": {"specifier": ".1f"}},
    {"name": "Purif. Rec A280 (%)", "id": "purification_recovery_a280", "editable": False, "type": "numeric",
     "format": {"specifier": ".1f"}},
    {"name": "Notes", "id": "note", "editable": True}
]

# Field definitions for SEC results table
SEC_RESULTS_FIELDS = [
    {"name": "Sample ID", "id": "sample_id", "editable": False},
    {"name": "Main Peak (%)", "id": "main_peak", "editable": False, "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "HMW (%)", "id": "hmw", "editable": False, "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "LMW (%)", "id": "lmw", "editable": False, "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "QC Pass", "id": "qc_pass", "editable": False, "type": "text"},
    {"name": "Status", "id": "status", "editable": False},
    {"name": "Report", "id": "report_name", "editable": False},
    {"name": "Analysis Date", "id": "created_at", "editable": False, "type": "datetime"}
]


def create_sample_set_detail_layout(query_params):
    """Create detailed view layout for a specific sample set with 2 tabs only"""
    sample_set_id = query_params.get('id', [None])[0] if query_params else None

    if not sample_set_id:
        return dbc.Container([
            dbc.Alert("No sample set ID provided", color="warning")
        ])

    return dbc.Container([
        # Store for current sample set ID
        dcc.Store(id="current-sample-set-id", data=sample_set_id),

        # Store for tracking which analysis cards are expanded
        dcc.Store(id="expanded-analysis-cards", data=[]),

        # Store for tracking previous n_clicks to detect new clicks
        dcc.Store(id="previous-n-clicks", data={}),

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
                    ], href="#!/cld/sample-sets", color="outline-secondary", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-sync-alt me-1"),
                        "Refresh"
                    ], color="outline-info", size="sm", id="refresh-sample-set-details-btn")
                ], className="float-end")
            ], md=4)
        ], className="mb-4"),

        # Main content with only 2 tabs
        dbc.Tabs([
            # Tab 1: Sample Set Overview
            dbc.Tab(label="Sample Set Overview", tab_id="overview", children=[
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-list text-primary me-2"),
                            "Sample Results Overview"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        # Summary stats
                        html.Div(id="sample-set-summary-stats", className="mb-4"),

                        # Main results table
                        html.Div(id="sample-set-details-table-container", children=[
                            create_sample_set_details_table()
                        ])
                    ])
                ], className="mt-3")
            ]),

            # Tab 2: Analysis
            dbc.Tab(label="Analysis", tab_id="analysis", children=[
                html.Div([
                    # Analysis cards container
                    html.Div(id="analysis-cards-container", className="mt-3")
                ])
            ])
        ], id="sample-set-detail-tabs", active_tab="overview"),

        # Notifications
        html.Div(id="sample-set-details-notifications")
    ], fluid=True, style={"padding": "20px"})


def create_analysis_card(analysis_type, card_id, icon_class, color, has_results=False, result_count=0):
    """Create a collapsible analysis card that loads data on expansion"""
    badge_color = "success" if has_results else "secondary"
    badge_text = f"{result_count} Results" if has_results else "No Data"

    return dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.H5([
                        html.I(className=f"{icon_class} text-{color} me-2"),
                        analysis_type,
                        html.Span([
                            " ",
                            dbc.Badge(badge_text, color=badge_color, className="ms-2")
                        ])
                    ], className="mb-0")
                ], width=8),
                dbc.Col([
                    dbc.Button(
                        html.I(className="fas fa-chevron-down"),
                        id={"type": "analysis-card-toggle", "index": card_id},
                        color="link",
                        className="float-end p-0"
                    )
                ], width=4, className="text-end")
            ])
        ], className="py-2"),
        dbc.Collapse([
            dbc.CardBody([
                # Loading spinner by default
                dbc.Spinner(
                    html.Div([
                        html.P(f"Loading {analysis_type} results...",
                               className="text-muted text-center")
                    ], id={"type": "analysis-card-content", "index": card_id}),
                    color=color,
                    spinner_style={"width": "2rem", "height": "2rem"}
                )
            ])
        ], id={"type": "analysis-card-collapse", "index": card_id}, is_open=False)
    ], className="mb-3")


def create_sec_results_table():
    """Create SEC results data table with proper formatting and features"""
    return dash_table.DataTable(
        id="sec-results-table",
        columns=SEC_RESULTS_FIELDS,
        data=[],
        style_table={
            'overflowX': 'auto',
            'minWidth': '100%'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontFamily': 'Arial',
            'fontSize': '14px',
            'whiteSpace': 'normal',
            'height': 'auto'
        },
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold',
            'border': '1px solid #dee2e6'
        },
        style_data={
            'border': '1px solid #dee2e6'
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'qc_pass', 'filter_query': '{qc_pass} = Pass'},
                'backgroundColor': '#d4edda',
                'color': 'black'
            },
            {
                'if': {'column_id': 'qc_pass', 'filter_query': '{qc_pass} = Fail'},
                'backgroundColor': '#f8d7da',
                'color': 'black'
            },
            {
                'if': {'column_id': 'status', 'filter_query': '{status} = complete'},
                'backgroundColor': '#d1ecf1'
            }
        ],
        sort_action="native",
        filter_action="native",
        page_action="native",
        page_current=0,
        page_size=20,
        export_format="xlsx",
        export_headers="display"
    )


def create_sample_set_details_table():
    """Create sample details data table"""
    return dash_table.DataTable(
        id="sample-set-details-table",
        columns=UP_SAMPLE_FIELDS,
        data=[],
        editable=True,
        style_table={
            'overflowX': 'auto',
            'minWidth': '100%'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontFamily': 'Arial',
            'fontSize': '14px',
            'whiteSpace': 'normal',
            'height': 'auto'
        },
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold',
            'border': '1px solid #dee2e6'
        },
        style_data={
            'border': '1px solid #dee2e6'
        },
        style_data_conditional=[
            {
                'if': {'column_editable': False},
                'backgroundColor': '#f8f9fa'
            }
        ],
        sort_action="native",
        filter_action="native",
        page_action="native",
        page_current=0,
        page_size=20,
        export_format="xlsx",
        export_headers="display"
    )


# Additional improvements to add to the end of the file

def create_empty_analysis_content(analysis_type):
    """Create empty state content for analyses with no data"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className="fas fa-inbox fa-3x text-muted mb-3"),
                html.H5("No Results Available", className="text-muted"),
                html.P(f"No {analysis_type} analysis results found for this sample set.",
                       className="text-muted"),
                dbc.Button([
                    html.I(className="fas fa-plus me-1"),
                    f"Request {analysis_type} Analysis"
                ],
                    color="primary",
                    size="sm",
                    id={"type": "request-analysis-btn", "index": analysis_type.lower()})
            ], className="text-center py-4")
        ])
    ], className="border-0 bg-light")


def create_analysis_loading_spinner(analysis_type):
    """Create a loading spinner for analysis content"""
    return html.Div([
        dbc.Spinner(
            html.Div([
                html.P(f"Loading {analysis_type} results...", className="mt-3")
            ]),
            color="primary",
            spinner_style={"width": "3rem", "height": "3rem"}
        )
    ], className="text-center py-5")


print("✅ Complete sample set details layout loaded - 2 tab structure")