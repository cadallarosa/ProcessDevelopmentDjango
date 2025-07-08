# plotly_integration/pd_dashboard/home/cld/sample_sets/callbacks/sample_set_details.py
# Complete callbacks file for the restructured 2-tab layout

from dash import callback, Input, Output, State, no_update, html, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from datetime import datetime
import json

# Import from the main app
from plotly_integration.pd_dashboard.main_app import app

# Import models - using only existing models from the repo
from plotly_integration.models import (
    LimsSampleSet, LimsSampleSetMembership, LimsSampleAnalysis,
    LimsUpstreamSamples, LimsSecResult, Report
)

# Import layout components
from ..layouts.sample_set_details import (
    create_sample_set_details_table, create_sec_results_table,
    create_analysis_card
)

# Import pandas for summary statistics
try:
    import pandas as pd
except ImportError:
    print("Warning: pandas not available for summary statistics")
    pd = None


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


# ============================================================================
# HEADER CALLBACKS
# ============================================================================

@app.callback(
    Output("sample-set-basic-info", "children"),
    Input("current-sample-set-id", "data")
)
def load_sample_set_basic_info(sample_set_id):
    """Load basic sample set information for header"""
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


# ============================================================================
# OVERVIEW TAB CALLBACKS
# ============================================================================

@app.callback(
    Output("sample-set-summary-stats", "children"),
    Input("current-sample-set-id", "data")
)
def update_sample_set_summary_stats(sample_set_id):
    """Update the summary statistics for the overview tab"""
    if not sample_set_id:
        return ""

    try:
        sample_set = LimsSampleSet.objects.get(id=sample_set_id)
        members = sample_set.members.all()

        # Calculate summary stats
        total_samples = members.count()

        # Count samples with SEC results
        sample_ids = [member.sample.sample_id for member in members]
        sec_results_count = LimsSecResult.objects.filter(
            sample_id__sample_id__in=sample_ids
        ).count()

        return dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(str(total_samples), className="text-primary"),
                        html.P("Total Samples", className="text-muted mb-0")
                    ])
                ], className="text-center")
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(str(sec_results_count), className="text-info"),
                        html.P("SEC Results", className="text-muted mb-0")
                    ])
                ], className="text-center")
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{sample_set.created_at.strftime('%m/%d/%Y')}", className="text-secondary"),
                        html.P("Created Date", className="text-muted mb-0")
                    ])
                ], className="text-center")
            ], md=3)
        ])

    except Exception as e:
        return dbc.Alert(f"Error loading summary: {str(e)}", color="danger")


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


# ============================================================================
# ANALYSIS TAB CALLBACKS
# ============================================================================

@app.callback(
    Output("analysis-cards-container", "children"),
    Input("current-sample-set-id", "data")
)
def create_analysis_cards_container(sample_set_id):
    """Create collapsible cards for each analysis type"""
    if not sample_set_id:
        return dbc.Alert("No sample set selected", color="warning")

    try:
        # Check which analyses have results
        sample_set = LimsSampleSet.objects.get(id=sample_set_id)
        members = sample_set.members.all()
        sample_ids = [member.sample.sample_id for member in members]

        # Count SEC results
        sec_count = LimsSecResult.objects.filter(
            sample_id__sample_id__in=sample_ids
        ).count()

        # Create cards for each analysis type
        cards = [
            create_analysis_card("SEC Analysis", "sec", "fas fa-chart-line", "info",
                                 has_results=(sec_count > 0), result_count=sec_count),
            # NEW: Embedded SEC card
            create_analysis_card("SEC Analysis (Embedded)", "sec-embedded", "fas fa-chart-line", "primary",
                                 has_results=(sec_count > 0), result_count=sec_count),
            # AKTA card with embedding
            create_analysis_card("AKTA Analysis", "akta", "fas fa-wave-square", "success",
                                 has_results=False, result_count=0),
            # Other placeholder cards
            create_analysis_card("Titer Results", "titer", "fas fa-vial", "warning", False, 0),
            create_analysis_card("CE-SDS Analysis", "cesds", "fas fa-bolt", "danger", False, 0),
            create_analysis_card("cIEF Analysis", "cief", "fas fa-chart-area", "primary", False, 0),
        ]

        return cards

    except Exception as e:
        print(f"Error creating analysis cards: {e}")
        return dbc.Alert(f"Error loading analysis cards: {str(e)}", color="danger")


# ============================================================================
# CARD TOGGLE CALLBACK - OPTIMIZED VERSION
# ============================================================================

@app.callback(
    [Output({"type": "analysis-card-collapse", "index": ALL}, "is_open"),
     Output({"type": "analysis-card-content", "index": ALL}, "children"),
     Output({"type": "analysis-card-toggle", "index": ALL}, "children")],
    [Input({"type": "analysis-card-toggle", "index": ALL}, "n_clicks")],
    [State({"type": "analysis-card-collapse", "index": ALL}, "is_open"),
     State({"type": "analysis-card-content", "index": ALL}, "children"),
     State("current-sample-set-id", "data"),
     State({"type": "analysis-card-toggle", "index": ALL}, "id")]
)
def toggle_analysis_cards(n_clicks_list, is_open_list, current_content, sample_set_id, button_ids):
    """Handle card expansion and load data only when expanded"""
    if not n_clicks_list:
        raise PreventUpdate

    # Initialize states if empty
    num_cards = len(n_clicks_list)
    if not is_open_list:
        is_open_list = [False] * num_cards
    if not current_content:
        current_content = [no_update] * num_cards

    # Check if this is initial load (all n_clicks are None or 0)
    if all(not n for n in n_clicks_list):
        raise PreventUpdate

    # Find which button was clicked (most recently)
    # We'll use a simple approach - the button with n_clicks > 0
    clicked_pos = None
    for i, n_clicks in enumerate(n_clicks_list):
        if n_clicks and n_clicks > 0:
            # This is a potential click - we'll use the last one found
            clicked_pos = i

    if clicked_pos is None:
        raise PreventUpdate

    # Get the card ID
    clicked_id = button_ids[clicked_pos]["index"]

    # Prepare outputs - use no_update for unchanged items
    new_is_open = []
    new_content = []
    new_icons = []

    for i in range(num_cards):
        if i == clicked_pos:
            # Toggle this card
            is_open = not is_open_list[i]
            new_is_open.append(is_open)

            # Update icon
            new_icons.append(html.I(className=f"fas fa-chevron-{'up' if is_open else 'down'}"))

            # Load content if opening and not already loaded
            if is_open and sample_set_id:
                content_str = str(current_content[i])
                if "Loading" in content_str or current_content[i] == no_update:
                    new_content.append(load_analysis_content(clicked_id, sample_set_id))
                else:
                    new_content.append(no_update)
            else:
                new_content.append(no_update)
        else:
            # Keep other cards unchanged
            new_is_open.append(no_update)
            new_content.append(no_update)
            new_icons.append(no_update)

    return new_is_open, new_content, new_icons


# ============================================================================
# CONTENT LOADING FUNCTIONS
# ============================================================================

def load_analysis_content(analysis_type, sample_set_id):
    """Load specific analysis content based on type"""
    try:
        sample_set = LimsSampleSet.objects.get(id=sample_set_id)
        members = sample_set.members.all()
        sample_ids = [member.sample.sample_id for member in members]

        if analysis_type == "sec":
            return load_sec_content(sample_ids, sample_set_id)
        elif analysis_type == "sec-embedded":
            return load_sec_embedded_content(sample_ids, sample_set_id)
        elif analysis_type == "akta":
            return load_akta_embedded_content(sample_ids, sample_set_id)
        else:
            return html.Div([
                html.P(f"No {analysis_type.upper()} results available for this sample set.",
                       className="text-muted text-center")
            ])

    except Exception as e:
        return dbc.Alert(f"Error loading {analysis_type} data: {str(e)}", color="danger")


def load_sec_content(sample_ids, sample_set_id):
    """Load SEC results content"""
    # Get SEC results
    sample_analyses = LimsSampleAnalysis.objects.filter(
        sample_id__in=sample_ids,
        sample_type=2  # FB samples
    )

    sec_results = LimsSecResult.objects.filter(
        sample_id__in=sample_analyses
    ).select_related('sample_id', 'report')

    if not sec_results:
        return html.Div([
            html.P("No SEC results found for this sample set.", className="text-muted text-center")
        ])

    # Get the report ID from the first SEC result (or most recent)
    report_id = None
    if sec_results:
        # Get the most recent report
        result_with_report = sec_results.filter(report__isnull=False).first()
        if result_with_report and result_with_report.report:
            report_id = result_with_report.report.report_id

    # Create SEC content with action buttons and table
    return html.Div([
        # Action buttons
        dbc.Row([
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-chart-line me-1"),
                        "Open SEC App"
                    ],
                        href=f"#!/analytical/sec/report?report_id={report_id}" if report_id else "#!/analytical/sec/report",
                        color="primary",
                        size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-file-excel me-1"),
                        "Export Results"
                    ], id="export-sec-results", color="success", size="sm")
                ])
            ], className="mb-3")
        ]),

        # Results table container
        html.Div(id="sec-results-table-container", children=[
            create_sec_results_table()
        ])
    ])


def load_sec_embedded_content(sample_ids, sample_set_id):
    """Load embedded SEC app in iframe"""
    # Get SEC results to find report ID
    sample_analyses = LimsSampleAnalysis.objects.filter(
        sample_id__in=sample_ids,
        sample_type=2  # FB samples
    )

    sec_results = LimsSecResult.objects.filter(
        sample_id__in=sample_analyses
    ).select_related('sample_id', 'report')

    # Get the report ID
    report_id = None
    if sec_results:
        result_with_report = sec_results.filter(report__isnull=False).first()
        if result_with_report and result_with_report.report:
            report_id = result_with_report.report.report_id

    # Build the SEC URL
    sec_url = f"/analytical/sec/report?report_id={report_id}" if report_id else "/analytical/sec/report"

    # Create embedded iframe
    return html.Div([
        html.Iframe(
            src=sec_url,
            style={
                "width": "100%",
                "height": "800px",
                "border": "1px solid #dee2e6",
                "borderRadius": "0.25rem"
            }
        )
    ])


def load_akta_embedded_content(sample_ids, sample_set_id):
    """Load embedded AKTA app in iframe"""
    # Clean FB sample IDs for AKTA (remove FB prefix)
    clean_fb_numbers = []
    for sample_id in sample_ids:
        if str(sample_id).startswith('FB'):
            clean_fb_numbers.append(str(sample_id)[2:])  # Remove FB prefix
        else:
            clean_fb_numbers.append(str(sample_id))

    # Build AKTA URL with sample parameters
    from urllib.parse import urlencode
    params = {
        'fb': ','.join(clean_fb_numbers),
        'embed': 'true'
    }
    akta_url = f"/plotly_integration/dash-app/app/AktaChromatogramApp/?{urlencode(params)}"

    # Create embedded iframe
    return html.Div([
        html.Iframe(
            src=akta_url,
            style={
                "width": "100%",
                "height": "800px",
                "border": "1px solid #dee2e6",
                "borderRadius": "0.25rem"
            }
        )
    ])


# ============================================================================
# SEC RESULTS TABLE DATA CALLBACK
# ============================================================================

@app.callback(
    [Output("sec-results-table", "data"),
     Output("sec-results-table", "columns", allow_duplicate=True)],
    Input({"type": "analysis-card-collapse", "index": "sec"}, "is_open"),
    State("current-sample-set-id", "data"),
    prevent_initial_call=True
)
def load_sec_results_data(is_open, sample_set_id):
    """Load SEC results data when SEC card is expanded"""
    print(f"DEBUG: load_sec_results_data called - is_open: {is_open}, sample_set_id: {sample_set_id}")

    if not is_open or not sample_set_id:
        return [], no_update

    try:
        # Get the sample set and its members
        sample_set = LimsSampleSet.objects.get(id=sample_set_id)
        members = sample_set.members.all()
        sample_ids = [member.sample.sample_id for member in members]

        print(f"DEBUG: Looking for SEC results for samples: {sample_ids}")

        # Query LimsSampleAnalysis for these sample IDs
        sample_analyses = LimsSampleAnalysis.objects.filter(
            sample_id__in=sample_ids,
            sample_type=2  # FB samples
        )

        # Get SEC results
        sec_results = LimsSecResult.objects.filter(
            sample_id__in=sample_analyses
        ).select_related('sample_id', 'report')

        print(f"DEBUG: Found {len(sec_results)} SEC results")

        # Build table data
        table_data = []
        for sec_result in sec_results:
            row = {
                'sample_id': sec_result.sample_id.sample_id,
                'main_peak': f"{sec_result.main_peak:.2f}" if sec_result.main_peak else 'N/A',
                'hmw': f"{sec_result.hmw:.2f}" if sec_result.hmw else 'N/A',
                'lmw': f"{sec_result.lmw:.2f}" if sec_result.lmw else 'N/A',
                'qc_pass': 'Pass' if sec_result.qc_pass else 'Fail',
                'status': sec_result.status or 'complete',
                'report_name': sec_result.report.report_name if sec_result.report else 'N/A',
                'created_at': sec_result.created_at.strftime('%Y-%m-%d %H:%M') if sec_result.created_at else 'N/A'
            }
            table_data.append(row)

        from ..layouts.sample_set_details import SEC_RESULTS_FIELDS
        return table_data, SEC_RESULTS_FIELDS

    except Exception as e:
        print(f"Error loading SEC results: {e}")
        return [], no_update


# ============================================================================
# REFRESH CALLBACKS
# ============================================================================

@app.callback(
    Output("sample-set-details-notifications", "children"),
    Input("refresh-sample-set-details-btn", "n_clicks"),
    prevent_initial_call=True
)
def refresh_sample_set_details(n_clicks):
    """Handle refresh button click"""
    if n_clicks:
        return dbc.Toast(
            "Sample set details refreshed successfully!",
            header="Refresh Complete",
            is_open=True,
            dismissable=True,
            duration=3000,
            icon="success",
            style={"position": "fixed", "top": 66, "right": 10, "width": 350}
        )
    return no_update


print("✅ Complete sample set details callbacks loaded - 2 tab structure")