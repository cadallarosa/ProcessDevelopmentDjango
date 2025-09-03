from dash import callback, Input, Output, State, ALL, ctx, no_update
import dash_bootstrap_components as dbc
from dash import html, dash_table
import json
from datetime import datetime

# Import the USP models
from plotly_integration.models import (
    UspSampleSet, UspSampleSetMembership, LimsUpstreamSamples,
    UspAnalysisRequest
)

print("🔧 Registering USP sample sets callbacks...")


def register_callbacks(app):
    """Register all USP sample sets callbacks"""

    # ============================================================================
    # MAIN TABLE UPDATE CALLBACK
    # ============================================================================

    @app.callback(
        [Output("usp-sample-sets-table-container", "children"),
         Output("usp-total-sets-metric", "children"),
         Output("usp-pending-metric", "children"),
         Output("usp-in-progress-metric", "children"),
         Output("usp-completed-metric", "children")],
        [Input("usp-refresh-sample-sets-btn", "n_clicks"),
         Input("usp-status-filter", "value"),
         Input("usp-search-input", "value"),
         Input("usp-project-filter", "value"),
         Input("usp-reactor-filter", "value"),
         Input("usp-apply-filters-btn", "n_clicks")]
    )
    def update_usp_sample_sets_table(refresh_clicks, status_filter, search_term, project_filter, 
                                    reactor_filter, apply_clicks):
        """Update the USP sample sets table based on filters"""
        try:
            # Get all USP sample sets
            sample_sets_query = UspSampleSet.objects.all().order_by('-id')

            # Apply filters
            if project_filter and project_filter != "all":
                sample_sets_query = sample_sets_query.filter(project_id=project_filter)

            if reactor_filter and reactor_filter != "all":
                sample_sets_query = sample_sets_query.filter(reactor_type=reactor_filter)

            if search_term:
                sample_sets_query = sample_sets_query.filter(set_name__icontains=search_term)

            sample_sets = list(sample_sets_query)

            # Calculate metrics
            total_pending = 0
            total_in_progress = 0
            total_completed = 0

            # Build table data with USP-specific structure
            table_data = []
            for sample_set in sample_sets:
                # Get analysis status for all types
                analysis_status = get_usp_analysis_status_for_set(sample_set)

                # Get sample range for USP samples
                sample_range = get_usp_sample_range(sample_set)

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

                # Build row with USP-specific columns
                row = {
                    "actions": create_usp_action_buttons(sample_set.id, analysis_status),
                    "project_id": sample_set.project_id or "N/A",
                    "reactor_type": sample_set.reactor_type or "N/A",
                    "experiment_number": str(sample_set.experiment_number) if sample_set.experiment_number else "N/A",
                    "cell_line": sample_set.cell_line or "N/A",
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
            from ..layouts.sample_sets import create_usp_sample_sets_table
            table = create_usp_sample_sets_table(table_data)

            return (
                table,
                str(len(sample_sets)),
                str(total_pending),
                str(total_in_progress),
                str(total_completed)
            )

        except Exception as e:
            print(f"Error in update_usp_sample_sets_table: {e}")
            error_msg = dbc.Alert(f"Error loading USP sample sets: {str(e)}", color="danger")
            return error_msg, "0", "0", "0", "0"


    # ============================================================================
    # HELPER FUNCTIONS
    # ============================================================================

    def get_usp_sample_range(sample_set):
        """Get the range of USP sample numbers in format UP###-UP###"""
        try:
            # Get all sample numbers from the sample set
            members = sample_set.members.select_related('sample').all()
            sample_numbers = [m.sample.sample_number for m in members]

            if not sample_numbers:
                return "No samples"

            # Sort and get min/max
            sample_numbers.sort()
            min_num = sample_numbers[0]
            max_num = sample_numbers[-1]

            # Format as UP###-UP###
            if min_num == max_num:
                return f"UP{min_num:03d}"
            else:
                return f"UP{min_num:03d}-UP{max_num:03d}"

        except Exception as e:
            print(f"Error getting USP sample range: {e}")
            return "Error"


    def create_usp_action_buttons(sample_set_id, analysis_status):
        """Create action buttons for each row in the USP table"""
        # Details button only
        details_btn = f'''<a href="#!/usp/sample-sets/details?id={sample_set_id}" 
                          class="btn btn-info btn-sm">
                          <i class="fas fa-info-circle me-1"></i>Details</a>'''

        return details_btn


    def get_usp_analysis_status_for_set(sample_set):
        """Get analysis status for all USP analysis types"""
        status_dict = {}

        # Define USP-specific analysis types
        analysis_types = ['SEC', 'AKTA', 'Titer', 'Viability', 'Metabolites', 'Flow Cytometry', 'HPLC', 'Mass Spec']

        # Get any analysis requests for this sample set
        requests = {}
        try:
            analysis_requests = UspAnalysisRequest.objects.filter(
                sample_set_id=sample_set.id
            )
            for req in analysis_requests:
                requests[req.analysis_type] = req
        except:
            pass

        # Get sample numbers
        member_samples = sample_set.members.select_related('sample').all()
        sample_numbers = [m.sample.sample_number for m in member_samples]

        for analysis_type in analysis_types:
            if analysis_type in requests:
                status_dict[analysis_type] = requests[analysis_type].status
            else:
                # Check if any data exists in result tables (future implementation)
                has_data = check_usp_analysis_data_exists(analysis_type, sample_numbers)
                if has_data:
                    status_dict[analysis_type] = 'completed'
                else:
                    status_dict[analysis_type] = 'not_requested'

        return status_dict


    def check_usp_analysis_data_exists(analysis_type, sample_numbers):
        """Check if USP analysis data exists for any samples"""
        # Placeholder for future implementation when USP analysis result models are created
        # This would check specific analysis result tables based on analysis_type
        return False


    # ============================================================================
    # FILTER CALLBACKS
    # ============================================================================

    @app.callback(
        Output("usp-project-filter", "options"),
        [Input("usp-refresh-sample-sets-btn", "n_clicks")],
        prevent_initial_call=False
    )
    def update_usp_project_filter(n_clicks):
        """Update project filter dropdown options"""
        try:
            projects = UspSampleSet.objects.values_list('project_id', flat=True).distinct()
            options = [{"label": "All Projects", "value": "all"}]

            for project in sorted(projects):
                if project:
                    options.append({"label": project, "value": project})

            return options
        except Exception as e:
            print(f"Error updating USP project filter: {e}")
            return [{"label": "All Projects", "value": "all"}]


    @app.callback(
        Output("usp-reactor-filter", "options"),
        [Input("usp-refresh-sample-sets-btn", "n_clicks")],
        prevent_initial_call=False
    )
    def update_usp_reactor_filter(n_clicks):
        """Update reactor type filter dropdown options"""
        try:
            reactor_types = UspSampleSet.objects.values_list('reactor_type', flat=True).distinct()
            options = [{"label": "All Reactor Types", "value": "all"}]

            for reactor_type in sorted(reactor_types):
                if reactor_type:
                    options.append({"label": reactor_type, "value": reactor_type})

            return options
        except Exception as e:
            print(f"Error updating USP reactor filter: {e}")
            return [{"label": "All Reactor Types", "value": "all"}]


    # ============================================================================
    # SAMPLE SET CREATION CALLBACK
    # ============================================================================

    @app.callback(
        [Output("usp-create-set-modal", "is_open"),
         Output("usp-set-creation-status", "children"),
         Output("usp-set-name-input", "value"),
         Output("usp-set-project-input", "value"),
         Output("usp-set-reactor-type-input", "value"),
         Output("usp-set-experiment-input", "value"),
         Output("usp-set-cell-line-input", "value")],
        [Input("usp-create-new-set-btn", "n_clicks"),
         Input("usp-close-create-modal", "n_clicks"),
         Input("usp-submit-create-set", "n_clicks")],
        [State("usp-create-set-modal", "is_open"),
         State("usp-set-name-input", "value"),
         State("usp-set-project-input", "value"),
         State("usp-set-reactor-type-input", "value"),
         State("usp-set-experiment-input", "value"),
         State("usp-set-cell-line-input", "value"),
         State("usp-selected-samples", "data")],
        prevent_initial_call=True
    )
    def handle_usp_sample_set_creation(open_clicks, close_clicks, submit_clicks, is_open,
                                      set_name, project_id, reactor_type, experiment_number,
                                      cell_line, selected_samples):
        """Handle USP sample set creation modal operations"""
        ctx_triggered = ctx.triggered_id

        # Close modal
        if ctx_triggered == "usp-close-create-modal":
            return False, "", "", "", "", "", ""

        # Open modal
        if ctx_triggered == "usp-create-new-set-btn":
            return True, "", "", "", "", "", ""

        # Create sample set
        if ctx_triggered == "usp-submit-create-set" and submit_clicks:
            try:
                # Validation
                if not set_name or not project_id or not reactor_type:
                    error_msg = dbc.Alert("Set name, project, and reactor type are required!", color="danger")
                    return True, error_msg, set_name, project_id, reactor_type, experiment_number, cell_line

                # Check if set name already exists
                if UspSampleSet.objects.filter(set_name=set_name).exists():
                    error_msg = dbc.Alert("A sample set with this name already exists!", color="warning")
                    return True, error_msg, set_name, project_id, reactor_type, experiment_number, cell_line

                # Create the sample set
                sample_set = UspSampleSet.objects.create(
                    set_name=set_name,
                    project_id=project_id,
                    reactor_type=reactor_type,
                    experiment_number=int(experiment_number) if experiment_number else None,
                    cell_line=cell_line,
                    sample_count=0,  # Will be updated when samples are added
                    created_by="System"  # Replace with actual user when auth is implemented
                )

                success_msg = dbc.Alert([
                    html.I(className="fas fa-check-circle me-2"),
                    f"Successfully created USP sample set '{set_name}'!"
                ], color="success", dismissable=True)

                return False, success_msg, "", "", "", "", ""

            except Exception as e:
                error_msg = dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Error creating sample set: {str(e)}"
                ], color="danger", dismissable=True)

                return True, error_msg, set_name, project_id, reactor_type, experiment_number, cell_line

        return is_open, no_update, no_update, no_update, no_update, no_update, no_update


    print("✅ USP Sample Sets callbacks registered successfully")