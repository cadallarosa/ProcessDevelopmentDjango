# plotly_integration/pd_dashboard/home/cld/sample_sets/callbacks/sample_sets.py

from dash import callback, Input, Output, State, ALL, ctx, no_update
import dash_bootstrap_components as dbc
from dash import html, dash_table
import json
from datetime import datetime

# Import from the main app
from plotly_integration.pd_dashboard.main_app import app

# Import existing models
from plotly_integration.models import (
    LimsSampleSet, LimsSampleAnalysis, SampleMetadata,
    LimsSecResult, Report, LimsUpstreamSamples
)

# Try to import additional analysis models
try:
    from plotly_integration.models import (
        AnalysisRequest, LimsTiterResult, LimsCeSdsResult,
        LimsCiefResult, LimsMassCheckResult, LimsReleasedGlycanResult,
        LimsHcpResult, LimsProaResult
    )
except ImportError as e:
    print(f"Some analysis models not available: {e}")


    # Create placeholder classes for missing models
    class AnalysisRequest:
        objects = None


    class LimsTiterResult:
        objects = None


    class LimsCeSdsResult:
        objects = None


    class LimsCiefResult:
        objects = None


    class LimsMassCheckResult:
        objects = None


    class LimsReleasedGlycanResult:
        objects = None


    class LimsHcpResult:
        objects = None


    class LimsProaResult:
        objects = None


# ============================================================================
# MAIN TABLE UPDATE CALLBACK
# ============================================================================

@app.callback(
    [Output("sample-sets-table-container", "children"),
     Output("total-sets-metric", "children"),
     Output("pending-metric", "children"),
     Output("in-progress-metric", "children"),
     Output("completed-metric", "children")],
    [Input("refresh-sample-sets-btn", "n_clicks"),
     Input("status-filter", "value"),
     Input("search-input", "value"),
     Input("project-filter", "value"),
     Input("apply-filters-btn", "n_clicks")]
)
def update_sample_sets_table(refresh_clicks, status_filter, search_term, project_filter, apply_clicks):
    """Update the sample sets table based on filters"""
    try:
        # Get all sample sets
        sample_sets_query = LimsSampleSet.objects.all().order_by('-id')

        # Apply filters
        if project_filter and project_filter != "all":
            sample_sets_query = sample_sets_query.filter(project_id=project_filter)

        if search_term:
            sample_sets_query = sample_sets_query.filter(set_name__icontains=search_term)

        sample_sets = list(sample_sets_query)

        # Calculate metrics
        total_pending = 0
        total_in_progress = 0
        total_completed = 0

        # Build table data with new structure
        table_data = []
        for sample_set in sample_sets:
            # Get analysis status for all types
            analysis_status = get_analysis_status_for_set(sample_set)

            # Get sample range
            sample_range = get_sample_range(sample_set)

            # Count requested and completed analyses
            requested_analyses = []
            completed_analyses = []

            for analysis_type, status in analysis_status.items():
                if status in ['requested', 'in_progress']:
                    requested_analyses.append(analysis_type)
                    if status == 'requested':
                        total_pending += 1
                    else:
                        total_in_progress += 1
                elif status == 'completed':
                    completed_analyses.append(analysis_type)
                    total_completed += 1

            # Build row with new column structure
            row = {
                "actions": create_action_buttons(sample_set.id, analysis_status),
                "project_id": sample_set.project_id or "N/A",
                "sip_number": sample_set.sip_number or "N/A",
                "development_stage": sample_set.development_stage or "N/A",
                "sample_range": sample_range,
                "sample_count": str(sample_set.sample_count),
                "requested_analysis": ", ".join(requested_analyses) if requested_analyses else "None",
                "completed_analysis": ", ".join(completed_analyses) if completed_analyses else "None",
                "created_date": sample_set.created_at.strftime('%Y-%m-%d') if sample_set.created_at else "",
            }
            table_data.append(row)

        # Filter by status if specified
        if status_filter and status_filter != "all":
            filtered_data = []
            for row in table_data:
                if status_filter == "pending" and row["requested_analysis"] != "None":
                    filtered_data.append(row)
                elif status_filter == "completed" and row["completed_analysis"] != "None":
                    filtered_data.append(row)
            table_data = filtered_data

        # Create table using the layout function
        from ..layouts.sample_sets import create_sample_sets_table
        table = create_sample_sets_table(table_data)

        return (
            table,
            str(len(sample_sets)),
            str(total_pending),
            str(total_in_progress),
            str(total_completed)
        )

    except Exception as e:
        print(f"Error in update_sample_sets_table: {e}")
        error_msg = dbc.Alert(f"Error loading sample sets: {str(e)}", color="danger")
        return error_msg, "0", "0", "0", "0"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_sample_range(sample_set):
    """Get the range of sample numbers in format FB###-FB###"""
    try:
        # Get all sample IDs from the sample set
        members = sample_set.members.select_related('sample').all()
        sample_ids = [m.sample.sample_id for m in members]

        if not sample_ids:
            return "No samples"

        # Extract numeric parts from FB### format
        fb_numbers = []
        for sid in sample_ids:
            sid_str = str(sid)
            if sid_str.startswith('FB'):
                try:
                    num = int(sid_str[2:])
                    fb_numbers.append(num)
                except ValueError:
                    continue

        if not fb_numbers:
            return "Invalid range"

        # Sort and get min/max
        fb_numbers.sort()
        min_num = fb_numbers[0]
        max_num = fb_numbers[-1]

        # Format as FB###-FB###
        if min_num == max_num:
            return f"FB{min_num:03d}"
        else:
            return f"FB{min_num:03d}-FB{max_num:03d}"

    except Exception as e:
        print(f"Error getting sample range: {e}")
        return "Error"


def create_action_buttons(sample_set_id, analysis_status):
    """Create action buttons for each row in the table"""
    # Details button only
    details_btn = f'''<a href="#!/cld/sample-sets/details?id={sample_set_id}" 
                      class="btn btn-info btn-sm">
                      <i class="fas fa-info-circle me-1"></i>Details</a>'''

    return details_btn


def get_analysis_status_for_set(sample_set):
    """Get analysis status for all analysis types"""
    status_dict = {}

    # Define all analysis types to check
    analysis_types = ['SEC', 'Titer', 'CE-SDS', 'cIEF', 'Mass Spec', 'Glycan', 'HCP', 'ProA']

    # Get any analysis requests for this sample set
    requests = {}
    if AnalysisRequest and AnalysisRequest.objects:
        try:
            analysis_requests = AnalysisRequest.objects.filter(
                sample_set_id=sample_set.id
            )
            for req in analysis_requests:
                requests[req.analysis_type] = req
        except:
            pass

    # Get sample IDs
    member_samples = sample_set.members.select_related('sample').all()
    sample_ids = [m.sample.sample_id for m in member_samples]

    for analysis_type in analysis_types:
        if analysis_type in requests:
            status_dict[analysis_type] = requests[analysis_type].status
        else:
            # Check if any data exists in result tables
            has_data = check_analysis_data_exists(analysis_type, sample_ids)
            if has_data:
                status_dict[analysis_type] = 'completed'
            else:
                status_dict[analysis_type] = 'not_requested'

    # Special check for SEC - also look for reports
    try:
        sec_reports = Report.objects.filter(
            analysis_type=1,  # SEC
            project_id=sample_set.project_id
        ).exists()
        if sec_reports:
            status_dict['SEC'] = 'completed'
    except:
        pass

    return status_dict


def check_analysis_data_exists(analysis_type, sample_ids):
    """Check if analysis data exists for any samples"""
    if not sample_ids:
        return False

    try:
        # Convert sample_ids to sample_numbers for database queries
        sample_numbers = []
        for sample_id in sample_ids:
            sample_id_str = str(sample_id)
            if sample_id_str.startswith('FB'):
                try:
                    sample_numbers.append(int(sample_id_str[2:]))
                except ValueError:
                    continue
            else:
                try:
                    sample_numbers.append(int(sample_id_str))
                except ValueError:
                    continue

        if not sample_numbers:
            return False

        # Check each analysis type
        if analysis_type == 'SEC':
            # Check LimsSampleAnalysis for SEC results
            sec_analyses = LimsSampleAnalysis.objects.filter(
                sample_id__in=sample_ids,
                sample_type=2  # FB samples
            ).values_list('id', flat=True)

            if sec_analyses:
                return LimsSecResult.objects.filter(
                    sample_id__in=sec_analyses
                ).exists()
            return False

        elif analysis_type == 'Titer' and LimsTiterResult and LimsTiterResult.objects:
            return LimsTiterResult.objects.filter(
                sample_id__sample_number__in=sample_numbers
            ).exists()

        elif analysis_type == 'CE-SDS' and LimsCeSdsResult and LimsCeSdsResult.objects:
            return LimsCeSdsResult.objects.filter(
                sample_id__sample_number__in=sample_numbers
            ).exists()

        # Add other analysis types as needed

        return False

    except Exception as e:
        print(f"Error checking {analysis_type} data: {e}")
        return False


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

    return f'''<span class="badge bg-{config["color"]} d-inline-flex align-items-center">
               <i class="fas fa-{config["icon"]} me-1"></i>{config["text"]}</span>'''


# ============================================================================
# FILTER CALLBACKS
# ============================================================================

@app.callback(
    Output("project-filter", "options"),
    [Input("refresh-sample-sets-btn", "n_clicks")],
    prevent_initial_call=False
)
def update_project_filter(n_clicks):
    """Update project filter dropdown options"""
    try:
        projects = LimsSampleSet.objects.values_list('project_id', flat=True).distinct()
        options = [{"label": "All Projects", "value": "all"}]

        for project in sorted(projects):
            if project:
                options.append({"label": project, "value": project})

        return options
    except Exception as e:
        print(f"Error updating project filter: {e}")
        return [{"label": "All Projects", "value": "all"}]


# ============================================================================
# SEC INTEGRATION CALLBACKS
# ============================================================================

@app.callback(
    [Output("sec-modal", "is_open"),
     Output("sec-report-created", "data"),
     Output("sec-selected-sample-set", "data")],
    [Input({"type": "sec-btn", "index": ALL}, "n_clicks"),
     Input("close-sec-modal", "n_clicks"),
     Input("create-sec-report-btn", "n_clicks")],
    [State("sec-modal", "is_open"),
     State("sec-report-name", "value"),
     State("sec-selected-sample-set", "data")],
    prevent_initial_call=True
)
def handle_sec_modal(sec_clicks, close_click, create_click, is_open, report_name, selected_set):
    """Handle SEC modal operations"""
    ctx_triggered = ctx.triggered_id

    # Close modal
    if ctx_triggered == "close-sec-modal":
        return False, no_update, no_update

    # Open modal from SEC button
    if isinstance(ctx_triggered, dict) and ctx_triggered.get("type") == "sec-btn":
        sample_set_id = ctx_triggered["index"]
        return True, no_update, {"sample_set_id": sample_set_id}

    # Create SEC report
    if ctx_triggered == "create-sec-report-btn" and report_name and selected_set:
        try:
            sample_set_id = selected_set.get("sample_set_id")
            sample_set = LimsSampleSet.objects.get(id=sample_set_id)

            # Create report logic here
            # This would integrate with your SEC app

            return False, {"created": True, "report_name": report_name}, no_update
        except Exception as e:
            print(f"Error creating SEC report: {e}")
            return True, {"created": False, "error": str(e)}, no_update

    return is_open, no_update, no_update


@app.callback(
    Output("sec-modal-body", "children"),
    Input("sec-selected-sample-set", "data"),
    prevent_initial_call=True
)
def update_sec_modal_content(selected_set):
    """Update SEC modal content when opened"""
    if not selected_set:
        return "No sample set selected"

    try:
        sample_set_id = selected_set.get("sample_set_id")
        sample_set = LimsSampleSet.objects.get(id=sample_set_id)

        return dbc.Form([
            dbc.Row([
                dbc.Col([
                    html.H6(f"Sample Set: {sample_set.set_name}"),
                    html.P(f"Samples: {sample_set.sample_count}", className="text-muted")
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Report Name"),
                    dbc.Input(
                        id="sec-report-name",
                        placeholder="Enter report name...",
                        value=f"SEC Report - {sample_set.set_name}"
                    )
                ])
            ], className="mt-3")
        ])
    except Exception as e:
        return f"Error loading sample set: {str(e)}"


# ============================================================================
# NOTIFICATION CALLBACKS
# ============================================================================

@app.callback(
    Output("sample-sets-notifications", "children"),
    [Input("sec-report-created", "data")],
    prevent_initial_call=True
)
def show_notifications(sec_created):
    """Show notifications for various actions"""
    if sec_created and sec_created.get("created"):
        return dbc.Toast(
            f"SEC report '{sec_created.get('report_name')}' created successfully!",
            header="Success",
            is_open=True,
            dismissable=True,
            duration=4000,
            icon="success",
            style={"position": "fixed", "top": 66, "right": 10, "width": 350}
        )
    elif sec_created and not sec_created.get("created"):
        return dbc.Toast(
            f"Error creating SEC report: {sec_created.get('error')}",
            header="Error",
            is_open=True,
            dismissable=True,
            duration=4000,
            icon="danger",
            style={"position": "fixed", "top": 66, "right": 10, "width": 350}
        )

    return no_update


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_info_row(label, value):
    """Create an information row for the summary"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Strong(f"{label}:")
            ], md=4),
            dbc.Col([
                html.Span(value)
            ], md=8)
        ], className="mb-2")
    ])


def create_analysis_status_row(analysis_type, status):
    """Create a row showing analysis type and status"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Strong(f"{analysis_type}:")
            ], md=4),
            dbc.Col([
                html.Span(
                    format_analysis_status_badge(status),
                    dangerously_allow_html=True
                )
            ], md=8)
        ], className="mb-1")
    ])


print("✅ Complete Sample Sets Callbacks - Simplified table structure loaded")