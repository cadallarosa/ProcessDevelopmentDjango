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
    """Update the samples table filtered to the sample set - SIMPLIFIED like view_samples"""
    if not sample_set_id:
        return dbc.Alert("No sample set selected", color="warning")

    try:
        sample_set = LimsSampleSet.objects.get(id=sample_set_id)

        # Get the sample numbers that are in this sample set
        # First get the LimsSampleAnalysis records in the set
        member_samples = sample_set.members.select_related('sample__up').all()

        # Extract the sample numbers from the upstream samples
        sample_numbers = []
        for member in member_samples:
            if member.sample.up:  # If there's an upstream sample linked
                sample_numbers.append(member.sample.up.sample_number)

        if not sample_numbers:
            return dbc.Alert("No upstream samples found for this sample set", color="info")

        # Query LimsUpstreamSamples directly with the sample numbers (same as view_samples)
        samples_query = LimsUpstreamSamples.objects.filter(
            sample_number=sample_numbers,
            sample_type=2
        ).order_by('sample_number')

        # Convert to table data (same logic as view_samples)
        table_data = []
        for sample_obj in samples_query:
            row_data = build_sample_row_with_recoveries(sample_obj)
            table_data.append(row_data)

        # Create the table
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


def build_sample_row_with_recoveries(sample_obj):
    """Build a row dictionary from a sample object - EXACT same as view_samples"""
    # Calculate recoveries (copied from view_samples)
    fast_recovery = ""
    a280_recovery = ""

    try:
        if sample_obj.pro_aqa_hf_titer and sample_obj.pro_aqa_e_titer and sample_obj.pro_aqa_hf_titer > 0:
            fast_recovery = round((sample_obj.pro_aqa_e_titer / sample_obj.pro_aqa_hf_titer) * 100, 1)
    except:
        pass

    try:
        if all([sample_obj.hccf_loading_volume, sample_obj.proa_eluate_volume,
                sample_obj.hf_octet_titer, sample_obj.proa_eluate_a280_conc]):
            if all([x > 0 for x in [sample_obj.hccf_loading_volume, sample_obj.proa_eluate_volume,
                                    sample_obj.hf_octet_titer, sample_obj.proa_eluate_a280_conc]]):
                total_protein_in = sample_obj.hccf_loading_volume * sample_obj.hf_octet_titer
                total_protein_out = sample_obj.proa_eluate_volume * sample_obj.proa_eluate_a280_conc
                a280_recovery = round((total_protein_out / total_protein_in) * 100, 1)
    except:
        pass

    # Return row data (exact same format as view_samples)
    return {
        "project": sample_obj.project or "",
        "sample_number": sample_obj.sample_number,
        "cell_line": sample_obj.cell_line or "",
        "sip_number": sample_obj.sip_number or "",
        "development_stage": sample_obj.development_stage or "",
        "analyst": sample_obj.analyst or "",
        "harvest_date": sample_obj.harvest_date.strftime('%Y-%m-%d') if sample_obj.harvest_date else "",
        "unifi_number": sample_obj.unifi_number or "",
        "hf_octet_titer": sample_obj.hf_octet_titer,
        "pro_aqa_hf_titer": sample_obj.pro_aqa_hf_titer,
        "pro_aqa_e_titer": sample_obj.pro_aqa_e_titer,
        "proa_eluate_a280_conc": sample_obj.proa_eluate_a280_conc,
        "hccf_loading_volume": sample_obj.hccf_loading_volume,
        "proa_eluate_volume": sample_obj.proa_eluate_volume,
        "fast_pro_a_recovery": fast_recovery,
        "purification_recovery_a280": a280_recovery,
        "note": sample_obj.note or ""
    }


print("✅ Simplified overview table callback - directly matches view_samples")

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