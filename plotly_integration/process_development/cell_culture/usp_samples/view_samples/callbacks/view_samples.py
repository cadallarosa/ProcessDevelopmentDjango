from dash import Input, Output, State, no_update, html, dcc, ctx, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from plotly_integration.models import LimsUpstreamSamples, LimsProjectInformation
from datetime import datetime, timedelta
from django.db.models import Q

print("🔧 Registering USP view_samples callbacks...")


def register_callbacks(app):
    """Register all USP view samples callbacks"""
    
    @app.callback(
        [Output("usp-samples-table", "data"),
         Output("usp-samples-table", "columns"),
         Output("usp-total-samples-count", "children"),
         Output("usp-filtered-samples-count", "children")],
        [Input("usp-refresh-samples-btn", "n_clicks"),
         Input("usp-apply-filters-btn", "n_clicks")],
        [State("usp-project-filter", "value"),
         State("usp-cell-line-filter", "value"),
         State("usp-vessel-type-filter", "value"),
         State("usp-development-stage-filter", "value"),
         State("usp-date-range-filter", "start_date"),
         State("usp-date-range-filter", "end_date"),
         State("usp-search-input", "value")],
        prevent_initial_call=False
    )
    def update_samples_table(refresh_clicks, filter_clicks, project_filter, cell_line_filter,
                           vessel_type_filter, stage_filter, start_date, end_date, search_term):
        """Update the USP samples table based on filters"""
        
        try:
            # Start with all USP samples (sample_type=1)
            samples_query = LimsUpstreamSamples.objects.filter(sample_type=1).order_by('-id')
            
            # Apply filters
            if project_filter and project_filter != "all":
                samples_query = samples_query.filter(project=project_filter)
            
            if cell_line_filter and cell_line_filter != "all":
                samples_query = samples_query.filter(cell_line=cell_line_filter)
            
            if vessel_type_filter and vessel_type_filter != "all":
                samples_query = samples_query.filter(vessel_type=vessel_type_filter)
            
            if stage_filter and stage_filter != "all":
                samples_query = samples_query.filter(development_stage=stage_filter)
            
            # Date range filter
            if start_date and end_date:
                samples_query = samples_query.filter(
                    harvest_date__gte=start_date,
                    harvest_date__lte=end_date
                )
            
            # Search filter
            if search_term:
                samples_query = samples_query.filter(
                    Q(project__icontains=search_term) |
                    Q(cell_line__icontains=search_term) |
                    Q(description__icontains=search_term) |
                    Q(analyst__icontains=search_term) |
                    Q(unifi_number__icontains=search_term)
                )
            
            samples = list(samples_query)
            
            # Convert to table data
            table_data = []
            for sample in samples:
                table_data.append({
                    'sample_id': f"UP{sample.sample_number:03d}",
                    'project': sample.project or '',
                    'cell_line': sample.cell_line or '',
                    'experiment_number': sample.experiment_number or '',
                    'culture_duration': sample.culture_duration or '',
                    'vessel_type': sample.vessel_type or '',
                    'development_stage': sample.development_stage or '',
                    'analyst': sample.analyst or '',
                    'harvest_date': sample.harvest_date.strftime('%Y-%m-%d') if sample.harvest_date else '',
                    'unifi_number': sample.unifi_number or '',
                    'description': sample.description or '',
                    'actions': f'<button class="btn btn-sm btn-outline-primary" onclick="editSample({sample.id})"><i class="fas fa-edit"></i></button>'
                })
            
            # Define table columns
            columns = [
                {"name": "Sample ID", "id": "sample_id", "type": "text"},
                {"name": "Project", "id": "project", "type": "text"},
                {"name": "Cell Line", "id": "cell_line", "type": "text"},
                {"name": "Exp #", "id": "experiment_number", "type": "numeric"},
                {"name": "Duration", "id": "culture_duration", "type": "numeric"},
                {"name": "Vessel", "id": "vessel_type", "type": "text"},
                {"name": "Stage", "id": "development_stage", "type": "text"},
                {"name": "Analyst", "id": "analyst", "type": "text"},
                {"name": "Harvest Date", "id": "harvest_date", "type": "datetime"},
                {"name": "Unifi #", "id": "unifi_number", "type": "text"},
                {"name": "Description", "id": "description", "type": "text"},
                {"name": "Actions", "id": "actions", "presentation": "markdown"}
            ]
            
            # Get total count for metrics
            total_count = LimsUpstreamSamples.objects.filter(sample_type=1).count()
            filtered_count = len(table_data)
            
            return table_data, columns, str(total_count), str(filtered_count)
            
        except Exception as e:
            print(f"Error updating USP samples table: {e}")
            empty_columns = [{"name": "Error", "id": "error"}]
            error_data = [{"error": f"Error loading samples: {str(e)}"}]
            return error_data, empty_columns, "0", "0"

    @app.callback(
        Output("usp-project-filter", "options"),
        Input("usp-refresh-samples-btn", "n_clicks"),
        prevent_initial_call=False
    )
    def update_project_filter_options(refresh_clicks):
        """Update project filter dropdown options"""
        try:
            projects = LimsUpstreamSamples.objects.filter(
                sample_type=1,
                project__isnull=False
            ).values_list('project', flat=True).distinct()
            
            options = [{"label": "All Projects", "value": "all"}]
            for project in sorted(set(projects)):
                if project:
                    options.append({"label": project, "value": project})
            
            return options
        except Exception as e:
            print(f"Error updating project filter: {e}")
            return [{"label": "All Projects", "value": "all"}]

    @app.callback(
        Output("usp-cell-line-filter", "options"),
        Input("usp-refresh-samples-btn", "n_clicks"),
        prevent_initial_call=False
    )
    def update_cell_line_filter_options(refresh_clicks):
        """Update cell line filter dropdown options"""
        try:
            cell_lines = LimsUpstreamSamples.objects.filter(
                sample_type=1,
                cell_line__isnull=False
            ).values_list('cell_line', flat=True).distinct()
            
            options = [{"label": "All Cell Lines", "value": "all"}]
            for cell_line in sorted(set(cell_lines)):
                if cell_line:
                    options.append({"label": cell_line, "value": cell_line})
            
            return options
        except Exception as e:
            print(f"Error updating cell line filter: {e}")
            return [{"label": "All Cell Lines", "value": "all"}]

    @app.callback(
        Output("usp-vessel-type-filter", "options"),
        Input("usp-refresh-samples-btn", "n_clicks"),
        prevent_initial_call=False
    )
    def update_vessel_type_filter_options(refresh_clicks):
        """Update vessel type filter dropdown options"""
        try:
            vessel_types = LimsUpstreamSamples.objects.filter(
                sample_type=1,
                vessel_type__isnull=False
            ).values_list('vessel_type', flat=True).distinct()
            
            options = [{"label": "All Vessel Types", "value": "all"}]
            for vessel_type in sorted(set(vessel_types)):
                if vessel_type:
                    options.append({"label": vessel_type, "value": vessel_type})
            
            return options
        except Exception as e:
            print(f"Error updating vessel type filter: {e}")
            return [{"label": "All Vessel Types", "value": "all"}]

    @app.callback(
        Output("usp-development-stage-filter", "options"),
        Input("usp-refresh-samples-btn", "n_clicks"),
        prevent_initial_call=False
    )
    def update_development_stage_filter_options(refresh_clicks):
        """Update development stage filter dropdown options"""
        try:
            stages = LimsUpstreamSamples.objects.filter(
                sample_type=1,
                development_stage__isnull=False
            ).values_list('development_stage', flat=True).distinct()
            
            options = [{"label": "All Stages", "value": "all"}]
            for stage in sorted(set(stages)):
                if stage:
                    options.append({"label": stage, "value": stage})
            
            return options
        except Exception as e:
            print(f"Error updating development stage filter: {e}")
            return [{"label": "All Stages", "value": "all"}]

    @app.callback(
        Output("usp-export-data", "data"),
        Input("usp-export-samples-btn", "n_clicks"),
        [State("usp-samples-table", "data")],
        prevent_initial_call=True
    )
    def export_samples_data(export_clicks, table_data):
        """Export filtered samples data as CSV"""
        
        if not export_clicks or not table_data:
            return no_update
        
        try:
            # Convert table data to DataFrame
            df = pd.DataFrame(table_data)
            
            # Remove the actions column for export
            if 'actions' in df.columns:
                df = df.drop('actions', axis=1)
            
            # Generate filename with timestamp
            filename = f"usp_samples_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            return dict(
                content=df.to_csv(index=False),
                filename=filename
            )
            
        except Exception as e:
            print(f"Error exporting USP samples: {e}")
            return no_update

    print("✅ USP View Samples callbacks registered successfully")