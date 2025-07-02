# cld_dashboard/samples/callbacks/sample_sets.py - COMPLETE IMPLEMENTATION

from dash import Input, Output, State, callback, html, no_update, ALL
import dash_bootstrap_components as dbc
from django.db.models import Count, Q, Prefetch
from plotly_integration.models import (
    LimsSampleSet, LimsSampleSetMembership,
    LimsSampleAnalysis, LimsAnalysisRequest,
    LimsSecResult, LimsTiterResult, LimsCeSdsResult,
    LimsCiefResult, LimsMassCheckResult, LimsReleasedGlycanResult,
    LimsHcpResult, LimsProaResult, Report
)
from datetime import datetime
import json

# Import the app instance
from plotly_integration.cld_dashboard.main_app import app


@app.callback(
    [Output("sample-sets-grid", "children"),
     Output("total-sets-metric", "children"),
     Output("pending-metric", "children"),
     Output("in-progress-metric", "children"),
     Output("completed-metric", "children")],
    [Input("refresh-sample-sets-btn", "n_clicks"),
     Input("search-sample-sets", "value"),
     Input("project-filter", "value"),
     Input("status-filter", "value"),
     Input("parsed-pathname", "data")]  # Add this to trigger on page load
)
def update_sample_sets_display(n_clicks, search_term, project_filter, status_filter, pathname):
    """Load and display sample sets with analysis status"""

    # Only run on sample-sets page
    if pathname != "/sample-sets":
        return no_update, no_update, no_update, no_update, no_update

    try:
        # Query sample sets
        sample_sets = LimsSampleSet.objects.filter(active=True)

        # Apply filters
        if search_term:
            sample_sets = sample_sets.filter(
                Q(set_name__icontains=search_term) |
                Q(project_id__icontains=search_term) |
                Q(sip_number__icontains=search_term) |
                Q(development_stage__icontains=search_term)
            )

        if project_filter and project_filter != "all":
            sample_sets = sample_sets.filter(project_id=project_filter)

        # Prefetch related data
        sample_sets = sample_sets.prefetch_related(
            'members__sample',
            'analysis_requests'
        ).order_by('-created_at')

        # Create cards and calculate metrics
        cards = []
        total_pending = 0
        total_in_progress = 0
        total_completed = 0

        for sample_set in sample_sets:
            # Get analysis status
            analysis_status = get_analysis_status_for_set(sample_set)

            # Apply status filter
            if status_filter == "pending" and not any(s == 'requested' for s in analysis_status.values()):
                continue
            elif status_filter == "complete" and not all(
                    s == 'completed' for s in analysis_status.values() if s != 'not_requested'):
                continue
            elif status_filter == "none" and any(s != 'not_requested' for s in analysis_status.values()):
                continue

            # Count statuses
            pending_count = sum(1 for s in analysis_status.values() if s == 'requested')
            in_progress_count = sum(1 for s in analysis_status.values() if s == 'in_progress')
            completed_count = sum(1 for s in analysis_status.values() if s == 'completed')

            total_pending += pending_count
            total_in_progress += in_progress_count
            total_completed += completed_count

            # Create card - now full width (1 per row)
            from ..layouts.sample_sets import create_sample_set_card
            card = create_sample_set_card(sample_set, analysis_status)
            cards.append(card)

        if not cards:
            cards = [dbc.Alert("No sample sets found. Create some samples to get started!",
                               color="info", className="w-100")]

        # Count total sample sets
        total_sets = len([s for s in sample_sets])

        return (
            html.Div(cards),  # Changed from dbc.Row to html.Div
            str(total_sets),
            str(total_pending),
            str(total_in_progress),
            str(total_completed)
        )

    except Exception as e:
        print(f"Error in update_sample_sets_display: {e}")
        error_msg = dbc.Alert(f"Error loading sample sets: {str(e)}", color="danger")
        return error_msg, "Error", "Error", "Error", "Error"


def get_analysis_status_for_set(sample_set):
    """Get status of each analysis type for a sample set"""
    analysis_types = ['SEC', 'AKTA', 'Titer', 'CE-SDS', 'cIEF', 'Mass Check', 'Glycan', 'HCP', 'ProA']
    status_dict = {}

    # Get all analysis requests
    requests = {req.analysis_type: req for req in sample_set.analysis_requests.all()}

    # Get member samples
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
    sec_reports = Report.objects.filter(
        analysis_type=1,  # SEC
        project_id=sample_set.project_id
    ).exists()
    if sec_reports:
        status_dict['SEC'] = 'completed'

    return status_dict


def check_analysis_data_exists(analysis_type, sample_ids):
    """Check if analysis data exists for any samples"""
    if not sample_ids:
        return False

    # ✅ SPECIAL HANDLING FOR AKTA
    if analysis_type == 'AKTA':
        return check_akta_data_exists(sample_ids)

    # Map other analysis types to result models and field names
    model_map = {
        'SEC': ('sec_result', LimsSecResult),
        'Titer': ('titer_result', LimsTiterResult),
        'CE-SDS': ('ce_sds_result', LimsCeSdsResult),
        'cIEF': ('cief_result', LimsCiefResult),
        'Mass Check': ('mass_check_result', LimsMassCheckResult),
        'Glycan': ('glycan_result', LimsReleasedGlycanResult),
        'HCP': ('hcp_result', LimsHcpResult),
        'ProA': ('proa_result', LimsProaResult)
    }

    field_name, model = model_map.get(analysis_type, (None, None))
    if field_name:
        # Check if any samples have results
        return LimsSampleAnalysis.objects.filter(
            sample_id__in=sample_ids
        ).exclude(
            **{field_name: None}
        ).exists()

    return False


def check_akta_data_exists(sample_ids):
    """
    Check if AKTA data exists for any samples

    Args:
        sample_ids (list): List of sample IDs

    Returns:
        bool: True if AKTA data exists
    """
    if not sample_ids:
        return False

    # ✅ REPLACE THIS with your actual AKTA data detection logic
    #
    # Option 1: If you have a specific AKTA results table
    # try:
    #     from plotly_integration.models import AktaResults  # Adjust model name
    #     return AktaResults.objects.filter(sample_id__in=sample_ids).exists()
    # except ImportError:
    #     pass

    # Option 2: If AKTA data is in LimsSampleAnalysis with a specific field
    # try:
    #     return LimsSampleAnalysis.objects.filter(
    #         sample_id__in=sample_ids,
    #         akta_result__isnull=False  # Adjust field name
    #     ).exists()
    # except:
    #     pass

    # Option 3: Check if AKTA data exists in another table/way
    # You might check for files, database entries, etc.

    # ✅ PLACEHOLDER: Always return True for now (shows AKTA button as available)
    # Change this to your actual logic
    return True


@app.callback(
    [Output("analysis-request-modal", "is_open"),
     Output("modal-sample-set-info", "children"),
     Output("selected-sample-set", "data")],
    [Input({"type": "request-analysis-btn", "index": ALL}, "n_clicks"),
     Input("cancel-analysis-request", "n_clicks")],
    [State("analysis-request-modal", "is_open"),
     State({"type": "request-analysis-btn", "index": ALL}, "id")]
)
def toggle_analysis_modal(request_clicks, cancel_clicks, is_open, button_ids):
    """Handle opening/closing of analysis request modal"""

    # Check if cancel button was clicked
    if cancel_clicks:
        return False, "", {}

    # Check if any request button was clicked
    if request_clicks and any(request_clicks):
        # Find which button was clicked by checking which n_clicks is not None and > 0
        for i, (n_clicks, button_id) in enumerate(zip(request_clicks, button_ids)):
            if n_clicks and n_clicks > 0:
                sample_set_id = button_id["index"]

                try:
                    sample_set = LimsSampleSet.objects.get(id=sample_set_id)

                    # Get sample IDs for this set
                    sample_ids = [m.sample.sample_id for m in sample_set.members.all()]

                    info = html.Div([
                        html.H6(f"Sample Set: {sample_set.set_name}"),
                        html.P([
                            html.Strong("Project: "), sample_set.project_id, html.Br(),
                            html.Strong("Samples: "), f"{sample_set.sample_count} samples", html.Br(),
                            html.Strong("Sample IDs: "), ", ".join(sample_ids[:5]),
                            "..." if len(sample_ids) > 5 else ""
                        ], className="mb-0")
                    ])

                    return True, info, {
                        "id": sample_set_id,
                        "name": sample_set.set_name,
                        "sample_ids": sample_ids
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
                    'status': 'requested'
                }
            )

            if created:
                created_count += 1

                # Create entries in result tables (skip for AKTA for now)
                if analysis_type != 'AKTA':
                    create_result_entries(analysis_type, member_samples)

        return dbc.Toast([
            html.P(f"✅ Successfully requested {created_count} analyses for {selected_set['name']}")
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
            html.P(f"❌ Error: {str(e)}")
        ],
            header="Request Failed",
            is_open=True,
            dismissable=True,
            duration=4000,
            color="danger",
            style={"position": "fixed", "top": 66, "right": 10}
        )


def create_result_entries(analysis_type, member_samples):
    """Create entries in the appropriate result table"""
    # Map analysis types to result models (excluding AKTA for now)
    model_map = {
        'SEC': LimsSecResult,
        'Titer': LimsTiterResult,
        'CE-SDS': LimsCeSdsResult,
        'cIEF': LimsCiefResult,
        'Mass Check': LimsMassCheckResult,
        'Glycan': LimsReleasedGlycanResult,
        'HCP': LimsHcpResult,
        'ProA': LimsProaResult
        # Note: AKTA not included here - handle separately if needed
    }

    model = model_map.get(analysis_type)
    if not model:
        return

    # Create result entries for each sample
    for membership in member_samples:
        sample_analysis = membership.sample

        # For SEC, check if we need special handling
        if analysis_type == 'SEC':
            # Just create a placeholder - actual data will come from SEC app
            result, created = model.objects.get_or_create(
                sample_id=sample_analysis.sample_id,
                defaults={
                    'created_at': datetime.now()
                }
            )
        else:
            # Create result entry if it doesn't exist
            result, created = model.objects.get_or_create(
                sample_id=sample_analysis.sample_id,
                defaults={
                    'status': 'pending',
                    'created_at': datetime.now()
                }
            )

        # Link to sample analysis
        if created:
            field_map = {
                'SEC': 'sec_result',
                'Titer': 'titer_result',
                'CE-SDS': 'ce_sds_result',
                'cIEF': 'cief_result',
                'Mass Check': 'mass_check_result',
                'Glycan': 'glycan_result',
                'HCP': 'hcp_result',
                'ProA': 'proa_result'
            }

            field_name = field_map.get(analysis_type)
            if field_name:
                setattr(sample_analysis, field_name, result)
                sample_analysis.save()


@app.callback(
    Output("project-filter", "options"),
    [Input("refresh-sample-sets-btn", "n_clicks"),
     Input("parsed-pathname", "data")]
)
def update_project_filter(n_clicks, pathname):
    """Update project filter dropdown options"""
    if pathname != "/sample-sets":
        return no_update

    try:
        projects = LimsSampleSet.objects.values_list('project_id', flat=True).distinct()
        options = [{"label": "All Projects", "value": "all"}]

        for project in sorted(projects):
            if project:
                options.append({"label": project, "value": project})

        return options
    except:
        return [{"label": "All Projects", "value": "all"}]


# UPDATED CALLBACK: Handle SEC view button clicks
# This creates a link button instead of navigation
@app.callback(
    Output("dummy-output", "children", allow_duplicate=True),
    [Input({"type": "view-sec-btn", "index": ALL}, "n_clicks")],
    prevent_initial_call=True
)
def handle_view_sec_click(n_clicks_list):
    """This callback is just to prevent errors - actual navigation is handled by href in the button"""
    return ""


# NEW CALLBACK: Handle details view
@app.callback(
    [Output("sample-set-details-modal", "is_open"),
     Output("modal-sample-set-details", "children")],
    [Input({"type": "view-details-btn", "index": ALL}, "n_clicks"),
     Input("close-details-modal", "n_clicks")],
    [State({"type": "view-details-btn", "index": ALL}, "id")],
    prevent_initial_call=True
)
def handle_view_details(view_clicks, close_clicks, button_ids):
    """Show detailed information about a sample set"""

    # Check if close button was clicked
    if close_clicks:
        return False, ""

    # Check if any details button was clicked
    if view_clicks and any(view_clicks):
        # Find which button was clicked
        for i, (n_clicks, button_id) in enumerate(zip(view_clicks, button_ids)):
            if n_clicks and n_clicks > 0:
                sample_set_id = button_id["index"]

                try:
                    sample_set = LimsSampleSet.objects.get(id=sample_set_id)

                    # Get all samples in this set
                    members = sample_set.members.select_related('sample').all()

                    # Get analysis status
                    analysis_status = get_analysis_status_for_set(sample_set)

                    # Check for SEC reports - FIX: use date_created instead of created_at
                    sample_ids = [m.sample.sample_id for m in members]
                    sec_reports = Report.objects.filter(
                        analysis_type=1,  # SEC
                        project_id=sample_set.project_id
                    ).order_by('-date_created')[:5]  # Last 5 reports - FIXED field name

                    details = html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.H4(sample_set.set_name),
                                html.Hr()
                            ])
                        ]),

                        dbc.Row([
                            # Basic Information
                            dbc.Col([
                                html.H6("Basic Information", className="text-primary"),
                                html.P([
                                    html.Strong("Project ID: "), sample_set.project_id, html.Br(),
                                    html.Strong("SIP Number: "), sample_set.sip_number or "N/A", html.Br(),
                                    html.Strong("Development Stage: "), sample_set.development_stage or "N/A",
                                    html.Br(),
                                    html.Strong("Total Samples: "), str(sample_set.sample_count), html.Br(),
                                    html.Strong("Created: "), sample_set.created_at.strftime(
                                        "%Y-%m-%d %H:%M") if sample_set.created_at else "Unknown", html.Br(),
                                    html.Strong("Created By: "), sample_set.created_by or "Unknown"
                                ])
                            ], md=4),

                            # Analysis Status
                            dbc.Col([
                                html.H6("Analysis Status", className="text-primary"),
                                html.Div([
                                    html.Div([
                                        html.Strong(f"{analysis_type}: "),
                                        create_status_badge(status)
                                    ], className="mb-1")
                                    for analysis_type, status in analysis_status.items()
                                ])
                            ], md=4),

                            # Recent Reports
                            dbc.Col([
                                html.H6("Recent SEC Reports", className="text-primary"),
                                html.Div([
                                    html.Ul([
                                        html.Li([
                                            html.A(
                                                f"Report #{report.report_id} - {report.date_created.strftime('%Y-%m-%d')}",
                                                href=f"#!/analysis/sec/report?report_id={report.report_id}",
                                                target="_blank"
                                            )
                                        ])
                                        for report in sec_reports
                                    ]) if sec_reports else html.P("No SEC reports found", className="text-muted")
                                ])
                            ], md=4)
                        ]),

                        html.Hr(),

                        # Samples Table
                        html.H6("Samples in Set", className="text-primary mt-3"),
                        create_samples_table(members),

                        html.Hr(),

                        # Action Buttons
                        dbc.Row([
                            dbc.Col([
                                dbc.ButtonGroup([
                                    dbc.Button([
                                        html.I(className="fas fa-microscope me-2"),
                                        "Request New Analysis"
                                    ],
                                        id={"type": "request-analysis-from-details", "index": sample_set.id},
                                        color="primary"),

                                    dbc.Button([
                                        html.I(className="fas fa-chart-line me-2"),
                                        "Open SEC App (Embedded)"
                                    ],
                                        href=f"#!/analysis/sec/report",
                                        color="success"),

                                    dbc.Button([
                                        html.I(className="fas fa-external-link-alt me-2"),
                                        "Open SEC App (Full)"
                                    ],
                                        href="/plotly_integration/dash-app/app/SecReportApp2/",
                                        target="_blank",
                                        color="outline-success"),

                                    dbc.Button([
                                        html.I(className="fas fa-file-export me-2"),
                                        "Export Data"
                                    ],
                                        id={"type": "export-sample-set", "index": sample_set.id},
                                        color="outline-info")
                                ])
                            ])
                        ], className="mt-3")
                    ])

                    return True, details

                except LimsSampleSet.DoesNotExist:
                    return False, "Sample set not found"

    return False, ""


def create_status_badge(status):
    """Create a status badge"""
    status_config = {
        'not_requested': {'color': 'secondary', 'text': 'Not Requested'},
        'requested': {'color': 'warning', 'text': 'Requested'},
        'in_progress': {'color': 'info', 'text': 'In Progress'},
        'completed': {'color': 'success', 'text': 'Completed'}
    }

    config = status_config.get(status, status_config['not_requested'])

    return dbc.Badge(config['text'], color=config['color'])


def create_samples_table(members):
    """Create a table of samples in the set"""
    if not members:
        return html.P("No samples found", className="text-muted")

    from dash import dash_table

    data = []
    for member in members:
        sample = member.sample
        data.append({
            "Sample ID": sample.sample_id,
            "Project": sample.project_id,
            "Sample Date": sample.sample_date.strftime("%Y-%m-%d") if sample.sample_date else "N/A",
            "Analyst": sample.analyst or "N/A",
            "Status": sample.status or "N/A"
        })

    return dash_table.DataTable(
        data=data,
        columns=[{"name": i, "id": i} for i in data[0].keys()] if data else [],
        style_cell={'textAlign': 'left', 'fontSize': '12px'},
        style_header={'backgroundColor': '#007bff', 'color': 'white', 'fontWeight': 'bold'},
        page_size=10,
        sort_action="native"
    )


print("✅ sample_sets callbacks loaded successfully")