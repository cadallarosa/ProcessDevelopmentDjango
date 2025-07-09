# plotly_integration/pd_dashboard/home/cld/sample_sets/callbacks/sample_sets.py
# Updated to support new layout with actions on left, sample range, and request functionality

from dash import callback, Input, Output, State, html, dcc, ALL, no_update
import dash_bootstrap_components as dbc
from plotly_integration.pd_dashboard.main_app import app
from plotly_integration.models import LimsSampleSet, LimsAnalysisRequest, LimsSampleAnalysis


@app.callback(
    [Output("sample-sets-table-container", "children"),
     Output("total-sets-metric", "children"),
     Output("pending-metric", "children"),
     Output("in-progress-metric", "children"),
     Output("completed-metric", "children")],
    [Input("refresh-sample-sets-btn", "n_clicks")],
    prevent_initial_call=False
)
def update_sample_sets_table(n_clicks):
    """Update the sample sets table with enhanced features"""
    try:
        # Get all sample sets
        sample_sets = LimsSampleSet.objects.all().order_by('-created_at')

        if not sample_sets:
            empty_msg = dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                "No sample sets found. Create some samples to get started!"
            ], color="info")
            return empty_msg, "0", "0", "0", "0"

        # Build table data
        table_data = []
        total_pending = 0
        total_in_progress = 0
        total_completed = 0

        for sample_set in sample_sets:
            # Get analysis status for this set
            analysis_status = get_analysis_status_for_set(sample_set)

            # Calculate sample range for FB samples
            sample_range = get_sample_range(sample_set)

            # Count status metrics
            for status in analysis_status.values():
                if status == 'requested':
                    total_pending += 1
                elif status == 'in_progress':
                    total_in_progress += 1
                elif status == 'completed':
                    total_completed += 1

            row = {
                # Actions column - MOVED TO FRONT, REMOVED AKTA
                "actions": create_action_buttons(sample_set.id, analysis_status),
                "project_id": sample_set.project_id or "N/A",
                "sip_number": sample_set.sip_number or "N/A",
                "sample_range": sample_range,  # NEW COLUMN
                "sample_count": sample_set.sample_count,
                "created_date": sample_set.created_at.strftime('%Y-%m-%d') if sample_set.created_at else "Unknown",
                # Analysis status columns (AKTA REMOVED)
                "sec_status": format_analysis_status_badge(analysis_status.get('SEC', 'not_requested')),
                "titer_status": format_analysis_status_badge(analysis_status.get('Titer', 'not_requested')),
                "ce_sds_status": format_analysis_status_badge(analysis_status.get('CE-SDS', 'not_requested')),
                "cief_status": format_analysis_status_badge(analysis_status.get('cIEF', 'not_requested')),
                "mass_check_status": format_analysis_status_badge(analysis_status.get('Mass Check', 'not_requested')),
                "glycan_status": format_analysis_status_badge(analysis_status.get('Glycan', 'not_requested')),
                "hcp_status": format_analysis_status_badge(analysis_status.get('HCP', 'not_requested')),
                "proa_status": format_analysis_status_badge(analysis_status.get('ProA', 'not_requested'))
            }
            table_data.append(row)

        # Create table using the layout function
        from ..layouts.sample_sets import create_sample_sets_table
        table = create_sample_sets_table(table_data)

        return (
            table,
            str(len(table_data)),
            str(total_pending),
            str(total_in_progress),
            str(total_completed)
        )

    except Exception as e:
        print(f"Error in update_sample_sets_table: {e}")
        error_msg = dbc.Alert(f"Error loading sample sets: {str(e)}", color="danger")
        return error_msg, "Error", "Error", "Error", "Error"


@app.callback(
    [Output("analysis-request-modal", "is_open"),
     Output("modal-sample-set-info", "children"),
     Output("selected-sample-set", "data")],
    [Input({"type": "request-analysis-btn", "index": ALL}, "n_clicks"),
     Input("cancel-analysis-request", "n_clicks")],
    [State("analysis-request-modal", "is_open"),
     State({"type": "request-analysis-btn", "index": ALL}, "id")],
    prevent_initial_call=True
)
def toggle_analysis_modal(request_clicks, cancel_clicks, is_open, button_ids):
    """Handle opening/closing of analysis request modal"""

    # Check if cancel button was clicked
    if cancel_clicks:
        return False, "", {}

    # Check if any request button was clicked
    if request_clicks and any(request_clicks):
        # Find which button was clicked
        for i, (n_clicks, button_id) in enumerate(zip(request_clicks, button_ids)):
            if n_clicks and n_clicks > 0:
                sample_set_id = button_id["index"]

                try:
                    sample_set = LimsSampleSet.objects.get(id=sample_set_id)

                    # Get sample IDs and range for this set
                    sample_ids = [m.sample.sample_id for m in sample_set.members.all()]
                    sample_range = get_sample_range(sample_set)

                    info = html.Div([
                        html.H6(f"Project: {sample_set.project_id}"),
                        html.P([
                            html.Strong("SIP: "), sample_set.sip_number or "N/A", html.Br(),
                            html.Strong("Sample Range: "), sample_range, html.Br(),
                            html.Strong("Total Samples: "), f"{sample_set.sample_count} samples", html.Br(),
                            html.Strong("Sample IDs: "), ", ".join(sample_ids[:5]),
                            "..." if len(sample_ids) > 5 else ""
                        ], className="mb-0")
                    ])

                    return True, info, {
                        "id": sample_set_id,
                        "project": sample_set.project_id,
                        "sample_ids": sample_ids,
                        "sample_range": sample_range
                    }

                except LimsSampleSet.DoesNotExist:
                    return False, "Sample set not found", {}

    return False, "", {}


@app.callback(
    Output("sample-sets-notifications", "children"),
    [Input("submit-analysis-request", "n_clicks")],
    [State("selected-sample-set", "data"),
     State("analysis-type-checklist", "value"),
     State("analysis-priority", "value"),
     State("analysis-notes", "value")],
    prevent_initial_call=True
)
def submit_analysis_request(n_clicks, selected_set, analysis_types, priority, notes):
    """Submit analysis requests for a sample set"""
    if not n_clicks or not selected_set or not analysis_types:
        return no_update

    try:
        sample_set = LimsSampleSet.objects.get(id=selected_set["id"])
        created_count = 0

        # Get member samples
        member_samples = sample_set.members.select_related('sample').all()

        for analysis_type in analysis_types:
            # Create analysis request
            request, created = LimsAnalysisRequest.objects.get_or_create(
                sample_set=sample_set,
                analysis_type=analysis_type,
                defaults={
                    'requested_by': 'current_user',  # Replace with actual user
                    'priority': priority,
                    'status': 'requested',
                    'notes': notes
                }
            )

            if created:
                created_count += 1
                # Create entries in result tables (implement as needed)
                create_result_entries(analysis_type, member_samples)

        return dbc.Toast([
            html.P(f"Successfully requested {created_count} analyses for {selected_set['sample_range']}")
        ],
            header="Analysis Requested",
            is_open=True,
            dismissable=True,
            duration=4000,
            color="success",
            style={"position": "fixed", "top": 66, "right": 10}
        )

    except Exception as e:
        return dbc.Toast([
            html.P(f"Error: {str(e)}")
        ],
            header="Request Failed",
            is_open=True,
            dismissable=True,
            duration=4000,
            color="danger",
            style={"position": "fixed", "top": 66, "right": 10}
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_sample_range(sample_set):
    """Calculate the sample range (FB lowest to highest) for a sample set"""
    try:
        # Get all sample IDs for this set
        sample_ids = [m.sample.sample_id for m in sample_set.members.all()]

        # Filter for FB samples and extract numbers
        fb_numbers = []
        for sample_id in sample_ids:
            if str(sample_id).startswith('FB'):
                try:
                    number = int(str(sample_id)[2:])  # Remove 'FB' prefix and convert to int
                    fb_numbers.append(number)
                except ValueError:
                    continue

        if fb_numbers:
            fb_numbers.sort()
            lowest = fb_numbers[0]
            highest = fb_numbers[-1]

            if lowest == highest:
                return f"FB{lowest}"
            else:
                return f"FB{lowest} - FB{highest}"
        else:
            # No FB samples, just show count
            return f"{len(sample_ids)} samples"

    except Exception as e:
        print(f"Error calculating sample range: {e}")
        return "Unknown range"


def get_analysis_status_for_set(sample_set):
    """Get analysis status for all analysis types for a sample set"""
    status_dict = {}

    # Get all analysis requests for this sample set
    requests = LimsAnalysisRequest.objects.filter(sample_set=sample_set)

    # Map analysis requests to status
    for request in requests:
        status_dict[request.analysis_type] = request.status

    # Set default status for analysis types not requested
    analysis_types = ['SEC', 'Titer', 'CE-SDS', 'cIEF', 'Mass Check', 'Glycan', 'HCP', 'ProA']
    for analysis_type in analysis_types:
        if analysis_type not in status_dict:
            status_dict[analysis_type] = 'not_requested'

    return status_dict


def format_analysis_status_badge(status):
    """Format analysis status as colored badge"""
    status_config = {
        "not_requested": {"color": "secondary", "icon": "circle", "text": "Not Requested"},
        "requested": {"color": "warning", "icon": "clock", "text": "Requested"},
        "in_progress": {"color": "info", "icon": "spinner", "text": "In Progress"},
        "completed": {"color": "success", "icon": "check", "text": "Complete"},
        "failed": {"color": "danger", "icon": "times", "text": "Failed"}
    }

    config = status_config.get(status, status_config["not_requested"])

    return f'<span class="badge bg-{config["color"]} d-inline-flex align-items-center">' \
           f'<i class="fas fa-{config["icon"]} me-1"></i>{config["text"]}</span>'


def create_action_buttons(sample_set_id, analysis_status):
    """Create action buttons for each row - Details and conditional Request/SEC"""
    # Details button (always available)
    details_btn = f'<a href="#!/cld/sample-sets/details?id={sample_set_id}" ' \
                  f'class="btn btn-outline-info btn-sm me-1">' \
                  f'<i class="fas fa-info-circle me-1"></i>Details</a>'

    # Request Analysis button (only if no analyses are completed)
    request_btn = ""
    has_completed_analysis = any(status == 'completed' for status in analysis_status.values())

    if not has_completed_analysis:
        request_btn = f'<button class="btn btn-outline-primary btn-sm me-1" ' \
                      f'type="button" ' \
                      f'id="{{"type": "request-analysis-btn", "index": {sample_set_id}}}">' \
                      f'<i class="fas fa-flask me-1"></i>Request</button>'

    # SEC button if SEC analysis is completed
    sec_btn = ""
    if analysis_status.get('SEC', 'not_requested') == 'completed':
        sec_btn = f'<a href="#!/analysis/sec/report" ' \
                  f'class="btn btn-outline-success btn-sm">' \
                  f'<i class="fas fa-chart-line me-1"></i>SEC</a>'

    return details_btn + request_btn + sec_btn


def create_result_entries(analysis_type, member_samples):
    """Create entries in the appropriate result table for requested analysis"""
    # This function should create entries in the corresponding result tables
    # based on the analysis type. Implementation depends on your specific
    # result table models (LimsSecResult, LimsTiterResult, etc.)

    # Example implementation - adjust based on your models:
    try:
        if analysis_type == 'SEC':
            from plotly_integration.models import LimsSecResult
            for member in member_samples:
                LimsSecResult.objects.get_or_create(
                    sample=member.sample,
                    defaults={'status': 'pending'}
                )
        elif analysis_type == 'Titer':
            from plotly_integration.models import LimsTiterResult
            for member in member_samples:
                LimsTiterResult.objects.get_or_create(
                    sample=member.sample,
                    defaults={'status': 'pending'}
                )
        # Add other analysis types as needed

    except Exception as e:
        print(f"Error creating result entries for {analysis_type}: {e}")


print("Updated sample sets callbacks loaded successfully")