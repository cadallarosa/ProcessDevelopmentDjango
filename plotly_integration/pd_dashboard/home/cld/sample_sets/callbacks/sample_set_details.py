# plotly_integration/pd_dashboard/home/cld/sample_sets/callbacks/sample_set_details.py
# Corrected callbacks with proper model relationships

from dash import callback, Input, Output, State, ALL, ctx, no_update
import dash_bootstrap_components as dbc
from dash import html
import json
from datetime import datetime

# Import from the main app
from plotly_integration.pd_dashboard.main_app import app

# Import models
from plotly_integration.models import (
    LimsSampleSet, LimsUpstreamSamples, LimsSampleAnalysis,
    LimsSecResult, Report, SampleMetadata
)

# Import layout functions
from ..layouts.sample_set_details import (
    create_samples_table_for_set, create_analysis_result_card
)


@app.callback(
    Output("sample-set-basic-info", "children"),
    Input("current-sample-set-id", "data")
)
def update_sample_set_basic_info(sample_set_id):
    """Update the basic sample set information at the top"""
    if not sample_set_id:
        return dbc.Alert("No sample set selected", color="warning")

    try:
        sample_set = LimsSampleSet.objects.get(id=sample_set_id)

        return dbc.Row([
            dbc.Col([
                html.H4(sample_set.set_name, className="text-primary mb-1"),
                html.P([
                    html.Strong("Project: "), sample_set.project_id, " | ",
                    html.Strong("SIP: "), sample_set.sip_number or "N/A", " | ",
                    html.Strong("Stage: "), sample_set.development_stage or "N/A", " | ",
                    html.Strong("Samples: "), str(sample_set.sample_count)
                ], className="text-muted mb-0")
            ])
        ])

    except Exception as e:
        print(f"Error loading sample set basic info: {e}")
        return dbc.Alert(f"Error loading sample set: {str(e)}", color="danger")


@app.callback(
    Output("sample-set-samples-table", "children"),
    Input("current-sample-set-id", "data")
)
def update_sample_set_samples_table(sample_set_id):
    """Update the samples table filtered to the sample set (same as view_samples)"""
    if not sample_set_id:
        return dbc.Alert("No sample set selected", color="warning")

    try:
        sample_set = LimsSampleSet.objects.get(id=sample_set_id)

        # Get all LimsSampleAnalysis records in this set
        member_samples = sample_set.members.select_related('sample').all()
        sample_analysis_ids = [m.sample.sample_id for m in member_samples]

        if not sample_analysis_ids:
            return dbc.Alert("No samples found in this set", color="info")

        # Get the corresponding LimsUpstreamSamples records
        # Need to match through the 'up' relationship in LimsSampleAnalysis
        sample_analysis_records = LimsSampleAnalysis.objects.filter(
            sample_id__in=sample_analysis_ids
        ).select_related('up')

        # Convert to table data format (same as view_samples)
        table_data = []
        for analysis_record in sample_analysis_records:
            if analysis_record.up:  # If there's a related upstream sample
                upstream = analysis_record.up
                table_data.append({
                    "project": upstream.project,
                    "sample_number": upstream.sample_number,
                    "cell_line": upstream.cell_line or "",
                    "sip_number": upstream.sip_number or "",
                    "development_stage": upstream.development_stage or "",
                    "analyst": upstream.analyst or "",
                    "harvest_date": upstream.harvest_date.strftime('%Y-%m-%d') if upstream.harvest_date else "",
                    "unifi_number": upstream.unifi_number or "",
                    "hf_octet_titer": upstream.hf_octet_titer,
                    "pro_aqa_hf_titer": upstream.pro_aqa_hf_titer,
                    "pro_aqa_e_titer": upstream.pro_aqa_e_titer,
                    "proa_eluate_a280_conc": upstream.proa_eluate_a280_conc,
                    "hccf_loading_volume": upstream.hccf_loading_volume,
                    "proa_eluate_volume": upstream.proa_eluate_volume,
                    "fast_pro_a_recovery": upstream.fast_pro_a_recovery,
                    "purification_recovery_a280": upstream.purification_recovery_a280,
                    "note": upstream.note or ""
                })
            else:
                # If no upstream sample linked, use basic info from analysis record
                table_data.append({
                    "project": analysis_record.project_id,
                    "sample_number": analysis_record.sample_id,
                    "cell_line": "",
                    "sip_number": "",
                    "development_stage": "",
                    "analyst": analysis_record.analyst,
                    "harvest_date": "",
                    "unifi_number": "",
                    "hf_octet_titer": None,
                    "pro_aqa_hf_titer": None,
                    "pro_aqa_e_titer": None,
                    "proa_eluate_a280_conc": None,
                    "hccf_loading_volume": None,
                    "proa_eluate_volume": None,
                    "fast_pro_a_recovery": None,
                    "purification_recovery_a280": None,
                    "note": ""
                })

        # Create the table using the same structure as view_samples
        table = create_samples_table_for_set()
        table.data = table_data

        return html.Div([
            html.P(f"Showing {len(table_data)} samples from this sample set",
                   className="text-muted small mb-3"),
            table
        ])

    except Exception as e:
        print(f"Error loading sample set samples: {e}")
        return dbc.Alert(f"Error loading samples: {str(e)}", color="danger")


@app.callback(
    Output("analysis-results-cards", "children"),
    Input("current-sample-set-id", "data")
)
def update_analysis_results_cards(sample_set_id):
    """Update the analysis results cards for each analysis type"""
    if not sample_set_id:
        return dbc.Alert("No sample set selected", color="warning")

    try:
        sample_set = LimsSampleSet.objects.get(id=sample_set_id)

        # Get analysis status (reuse existing function)
        from .sample_sets import get_analysis_status_for_set
        analysis_status = get_analysis_status_for_set(sample_set)

        # Get member sample IDs from LimsSampleAnalysis
        member_samples = sample_set.members.select_related('sample').all()
        sample_analysis_ids = [m.sample.sample_id for m in member_samples]

        # Analysis types to display
        analysis_types = ['SEC', 'AKTA', 'Titer', 'CE-SDS', 'cIEF', 'Mass Check', 'Glycan', 'HCP', 'ProA']

        cards = []

        for analysis_type in analysis_types:
            status = analysis_status.get(analysis_type, 'not_requested')

            # Get results data and report ID if analysis is completed
            results_data = None
            report_id = None

            if status == 'completed':
                results_data, report_id = get_analysis_results_data(analysis_type, sample_analysis_ids,
                                                                    sample_set.project_id)

            # Create card for this analysis
            card = create_analysis_result_card(
                analysis_type=analysis_type,
                status=status,
                results_data=results_data,
                report_id=report_id
            )
            cards.append(card)

        # Arrange cards in grid
        card_rows = []
        for i in range(0, len(cards), 3):  # 3 cards per row
            row_cards = cards[i:i + 3]
            card_row = dbc.Row([
                dbc.Col(card, md=4) for card in row_cards
            ], className="mb-3")
            card_rows.append(card_row)

        return html.Div(card_rows)

    except Exception as e:
        print(f"Error loading analysis results: {e}")
        return dbc.Alert(f"Error loading analysis results: {str(e)}", color="danger")


def get_analysis_results_data(analysis_type, sample_analysis_ids, project_id):
    """Get results data and report ID for a specific analysis type"""
    try:
        if analysis_type == "SEC":
            return get_sec_results_data(sample_analysis_ids, project_id)
        elif analysis_type == "AKTA":
            return get_akta_results_data(sample_analysis_ids, project_id)
        elif analysis_type == "Titer":
            return get_titer_results_data(sample_analysis_ids, project_id)
        # Add other analysis types as needed
        else:
            return None, None

    except Exception as e:
        print(f"Error getting {analysis_type} results: {e}")
        return None, None


def get_sec_results_data(sample_analysis_ids, project_id):
    """Get SEC results data and report ID"""
    try:
        # Get SEC results for these sample analysis IDs
        # LimsSecResult has sample_id as OneToOneField to LimsSampleAnalysis
        sec_results = LimsSecResult.objects.filter(
            sample_id__in=sample_analysis_ids
        ).select_related('sample_id').order_by('-created_at')

        # Get associated reports
        reports = Report.objects.filter(
            analysis_type=1,  # SEC
            project_id=project_id
        ).order_by('-date_created')

        results_data = []
        for result in sec_results:
            results_data.append({
                'sample_id': result.sample_id.sample_id,
                'date_analyzed': result.created_at.strftime('%Y-%m-%d') if result.created_at else None,
                'main_peak_percent': result.main_peak,
                'hmw_percent': result.hmw,
                'lmw_percent': result.lmw,
                'qc_pass': result.qc_pass,
                'status': result.status
            })

        report_id = reports.first().report_id if reports.exists() else None

        return results_data, report_id

    except Exception as e:
        print(f"Error getting SEC results: {e}")
        return None, None


def get_akta_results_data(sample_analysis_ids, project_id):
    """Get AKTA results data and report ID"""
    try:
        # Get AKTA data from SampleMetadata
        # Match by converting sample_analysis_ids to sample numbers if needed
        akta_data = SampleMetadata.objects.filter(
            # You'll need to determine how AKTA data relates to your sample analysis IDs
            # This might require a different approach based on your data structure
        ).order_by('-date_acquired')

        results_data = []
        for data in akta_data:
            results_data.append({
                'sample_id': data.sample_name,  # or appropriate field
                'run_date': data.date_acquired.strftime('%Y-%m-%d') if data.date_acquired else None,
                'sample_name': data.sample_name,
                'injection_volume': data.injection_volume,
                'column_name': data.column_name,
                'processing_method': data.processing_method
            })

        # AKTA reports might be in a different structure
        report_id = None

        return results_data, report_id

    except Exception as e:
        print(f"Error getting AKTA results: {e}")
        return None, None


def get_titer_results_data(sample_analysis_ids, project_id):
    """Get Titer results data and report ID"""
    try:
        # Get Titer results using the OneToOneField relationship
        from plotly_integration.models import LimsTiterResult

        titer_results = LimsTiterResult.objects.filter(
            sample_id__in=sample_analysis_ids
        ).select_related('sample_id').order_by('-created_at')

        results_data = []
        for result in titer_results:
            results_data.append({
                'sample_id': result.sample_id.sample_id,
                'date_analyzed': result.created_at.strftime('%Y-%m-%d') if result.created_at else None,
                'titer_value': result.titer_value,  # Adjust field name as needed
                'status': result.status
            })

        report_id = None  # Set based on your Titer report structure

        return results_data, report_id

    except Exception as e:
        print(f"Error getting Titer results: {e}")
        return None, None


# Callback for analysis request buttons in detail cards
@app.callback(
    Output("detail-dummy-output", "children"),
    Input({"type": "request-analysis-detail", "analysis": ALL}, "n_clicks"),
    State("current-sample-set-id", "data"),
    prevent_initial_call=True
)
def handle_analysis_request_from_detail(n_clicks_list, sample_set_id):
    """Handle analysis request from detail page cards"""
    if not any(n_clicks_list) or not sample_set_id:
        return no_update

    # Find which button was clicked
    triggered_id = ctx.triggered_id
    if triggered_id:
        analysis_type = triggered_id["analysis"]
        print(f"Analysis request for {analysis_type} from sample set {sample_set_id}")
        # Implement analysis request logic here

    return ""


# Callback for download results buttons
@app.callback(
    Output("detail-dummy-output", "children", allow_duplicate=True),
    Input({"type": "download-results", "analysis": ALL}, "n_clicks"),
    State("current-sample-set-id", "data"),
    prevent_initial_call=True
)
def handle_download_results(n_clicks_list, sample_set_id):
    """Handle download results from detail page cards"""
    if not any(n_clicks_list) or not sample_set_id:
        return no_update

    # Find which button was clicked
    triggered_id = ctx.triggered_id
    if triggered_id:
        analysis_type = triggered_id["analysis"]
        print(f"Download request for {analysis_type} from sample set {sample_set_id}")
        # Implement download logic here

    return ""


print("✅ Sample Set Details Callbacks - Corrected with proper model relationships")