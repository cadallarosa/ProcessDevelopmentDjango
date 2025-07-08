# plotly_integration/pd_dashboard/home/cld/sample_sets/callbacks/sample_set_details.py
# Complete callbacks file with SEC analysis results integration

from dash import callback, Input, Output, State, no_update, html
import dash_bootstrap_components as dbc
from datetime import datetime

# Import from the main app
from plotly_integration.pd_dashboard.main_app import app

# Import models
from plotly_integration.models import (
    LimsSampleSet, LimsSampleAnalysis, LimsUpstreamSamples,
    LimsSecResult, Report
)

# Import layout components
from ..layouts.sample_set_details import (
    create_sample_set_details_table, create_sec_results_table
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
# EXISTING CALLBACKS (UPDATED)
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


@app.callback(
    Output("sample-set-details-table-container", "children"),
    Input("current-sample-set-id", "data")
)
def load_sample_set_details_table_container(sample_set_id):
    """Load sample set details table container"""
    if not sample_set_id:
        return dbc.Alert("No sample set selected", color="warning")

    return create_sample_set_details_table()


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


# ============================================================================
# NEW SEC RESULTS CALLBACKS
# ============================================================================

@app.callback(
    Output("sec-results-table-container", "children"),
    Input("current-sample-set-id", "data")
)
def load_sec_results_table_container(sample_set_id):
    """Load SEC results table container"""
    if not sample_set_id:
        return dbc.Alert("No sample set selected", color="warning")

    return create_sec_results_table()


@app.callback(
    [Output("sec-results-table", "data"),
     Output("sec-results-count-badge", "children")],
    Input("current-sample-set-id", "data")
)
def load_sec_results_data(sample_set_id):
    """Load SEC analysis results for samples in the sample set"""
    print(f"DEBUG: load_sec_results_data called with ID: {sample_set_id}")

    if not sample_set_id:
        print("DEBUG: No sample set ID provided")
        return [], "0 Results"

    try:
        # Get the sample set and its members
        sample_set = LimsSampleSet.objects.get(id=sample_set_id)
        members = sample_set.members.all()

        if not members:
            print("DEBUG: No members found")
            return [], "0 Results"

        # Get sample IDs from members
        sample_ids = [member.sample.sample_id for member in members]
        print(f"DEBUG: Looking for SEC results for samples: {sample_ids}")

        # Query LimsSampleAnalysis for these sample IDs
        sample_analyses = LimsSampleAnalysis.objects.filter(
            sample_id__in=sample_ids,
            sample_type=2  # FB samples
        )

        # Get SEC results for these samples
        sec_results = LimsSecResult.objects.filter(
            sample_id__in=sample_analyses
        ).select_related('sample_id', 'report')

        print(f"DEBUG: Found {len(sec_results)} SEC results")

        # Build table data
        table_data = []
        for sec_result in sec_results:
            # Format the data for display
            row = {
                'sample_id': sec_result.sample_id.sample_id,
                'main_peak': sec_result.main_peak if sec_result.main_peak is not None else 'N/A',
                'hmw': sec_result.hmw if sec_result.hmw is not None else 'N/A',
                'lmw': sec_result.lmw if sec_result.lmw is not None else 'N/A',
                'qc_pass': 'Pass' if sec_result.qc_pass else 'Fail',
                'status': sec_result.status,
                'report_name': sec_result.report.report_name if sec_result.report else 'N/A',
                'created_at': sec_result.created_at.strftime('%Y-%m-%d %H:%M') if sec_result.created_at else 'N/A'
            }
            table_data.append(row)

        # Sort by sample_id for consistent display
        table_data.sort(key=lambda x: x['sample_id'])

        badge_text = f"{len(table_data)} Results"
        print(f"DEBUG: Returning {len(table_data)} SEC results")

        return table_data, badge_text

    except Exception as e:
        print(f"ERROR: in load_sec_results_data: {e}")
        return [], "Error"


@app.callback(
    [Output("avg-main-peak", "children"),
     Output("avg-hmw", "children"),
     Output("avg-lmw", "children"),
     Output("qc-pass-count", "children")],
    Input("sec-results-table", "data")
)
def update_sec_summary_stats(sec_results_data):
    """Update SEC results summary statistics"""
    if not sec_results_data:
        return "--", "--", "--", "--"

    try:
        # Manual calculation if pandas is not available
        if pd is None:
            # Manual calculations
            main_peaks = []
            hmws = []
            lmws = []
            qc_passes = 0
            total_samples = len(sec_results_data)

            for row in sec_results_data:
                # Convert to numeric, skip 'N/A' values
                if row['main_peak'] != 'N/A':
                    try:
                        main_peaks.append(float(row['main_peak']))
                    except (ValueError, TypeError):
                        pass

                if row['hmw'] != 'N/A':
                    try:
                        hmws.append(float(row['hmw']))
                    except (ValueError, TypeError):
                        pass

                if row['lmw'] != 'N/A':
                    try:
                        lmws.append(float(row['lmw']))
                    except (ValueError, TypeError):
                        pass

                if row['qc_pass'] == 'Pass':
                    qc_passes += 1

            # Calculate averages
            avg_main_peak = sum(main_peaks) / len(main_peaks) if main_peaks else None
            avg_hmw = sum(hmws) / len(hmws) if hmws else None
            avg_lmw = sum(lmws) / len(lmws) if lmws else None
            qc_pass_rate = (qc_passes / total_samples * 100) if total_samples > 0 else 0

        else:
            # Use pandas for calculations
            df = pd.DataFrame(sec_results_data)

            # Filter out 'N/A' values and convert to numeric
            numeric_cols = ['main_peak', 'hmw', 'lmw']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Calculate averages (excluding NaN values)
            avg_main_peak = df['main_peak'].mean()
            avg_hmw = df['hmw'].mean()
            avg_lmw = df['lmw'].mean()

            # Calculate QC pass rate
            total_samples = len(df)
            qc_passes = len(df[df['qc_pass'] == 'Pass'])
            qc_pass_rate = (qc_passes / total_samples * 100) if total_samples > 0 else 0

        # Format the outputs
        if pd is None:
            main_peak_text = f"{avg_main_peak:.1f}%" if avg_main_peak is not None else "--"
            hmw_text = f"{avg_hmw:.2f}%" if avg_hmw is not None else "--"
            lmw_text = f"{avg_lmw:.2f}%" if avg_lmw is not None else "--"
        else:
            main_peak_text = f"{avg_main_peak:.1f}%" if not pd.isna(avg_main_peak) else "--"
            hmw_text = f"{avg_hmw:.2f}%" if not pd.isna(avg_hmw) else "--"
            lmw_text = f"{avg_lmw:.2f}%" if not pd.isna(avg_lmw) else "--"

        qc_text = f"{qc_pass_rate:.0f}% ({qc_passes}/{total_samples})"

        return main_peak_text, hmw_text, lmw_text, qc_text

    except Exception as e:
        print(f"ERROR: calculating SEC summary stats: {e}")
        return "--", "--", "--", "--"


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


print("Complete sample set details layout and callbacks with SEC integration loaded")