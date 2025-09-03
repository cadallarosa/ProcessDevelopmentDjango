# USP sample_sets callbacks - Grouped by Project ID and Reactor Type
from dash import callback, Input, Output, State, ALL, ctx, no_update, html
import dash_bootstrap_components as dbc
from dash import dash_table
import json
from datetime import datetime
import pandas as pd
import numpy as np

# Import from the main app
from plotly_integration.pd_dashboard.main_app import app

# Import models
from plotly_integration.models import LimsUpstreamSamples
from django.db.models import Count, Avg, Min, Max, Q

print("Configuring USP sample_sets callbacks...")


# MAIN DATA LOADING CALLBACK
@app.callback(
    [Output("usp-sample-sets-table", "data"),
     Output("usp-total-projects-metric", "children"),
     Output("usp-total-sets-metric", "children"),
     Output("usp-total-samples-metric", "children"),
     Output("usp-avg-samples-metric", "children"),
     Output("usp-project-set-filter", "options")],
    [Input("usp-refresh-sample-sets-btn", "n_clicks"),
     Input("usp-apply-filters-btn", "n_clicks")],
    [State("usp-project-set-filter", "value"),
     State("usp-reactor-set-filter", "value"),
     State("usp-search-input", "value")],
    prevent_initial_call=False
)
def load_usp_sample_sets(refresh_clicks, apply_clicks, project_filter, reactor_filter, search_value):
    """Load USP sample sets grouped by project and reactor type"""
    try:
        # Start with all USP samples
        samples_query = LimsUpstreamSamples.objects.all()
        
        # Apply filters
        if project_filter and project_filter != "all":
            samples_query = samples_query.filter(project_id=project_filter)
        
        if reactor_filter and reactor_filter != "all":
            samples_query = samples_query.filter(reactor_type=reactor_filter)
        
        if search_value:
            samples_query = samples_query.filter(
                Q(project_id__icontains=search_value) |
                Q(cell_line__icontains=search_value) |
                Q(sample_name__icontains=search_value)
            )
        
        # Group samples by project_id and reactor_type
        sample_sets = samples_query.values('project_id', 'reactor_type').annotate(
            sample_count=Count('id'),
            min_date=Min('harvest_date'),
            max_date=Max('harvest_date'),
            avg_titer=Avg('final_titer'),
            avg_vcd=Avg('max_vcd'),
            avg_viability=Avg('viability'),
            min_created=Min('created_date')
        ).filter(project_id__isnull=False, reactor_type__isnull=False)
        
        # Format data for table
        table_data = []
        for set_data in sample_sets:
            # Get unique clones for this set
            clones = samples_query.filter(
                project_id=set_data['project_id'],
                reactor_type=set_data['reactor_type']
            ).values_list('cell_line', flat=True).distinct()
            clone_list = ', '.join([c for c in clones if c][:3])  # Show first 3 clones
            if len(clones) > 3:
                clone_list += f" (+{len(clones)-3} more)"
            
            # Format date range
            date_range = ""
            if set_data['min_date'] and set_data['max_date']:
                if set_data['min_date'] == set_data['max_date']:
                    date_range = set_data['min_date'].strftime("%Y-%m-%d")
                else:
                    date_range = f"{set_data['min_date'].strftime('%Y-%m-%d')} to {set_data['max_date'].strftime('%Y-%m-%d')}"
            
            # Create action buttons as markdown links
            project_id_encoded = set_data['project_id'].replace(' ', '_')
            reactor_type_encoded = set_data['reactor_type'].replace(' ', '_')
            actions = f"[View](#!/usp/sample-set/{project_id_encoded}/{reactor_type_encoded}) | [Export](#!/export/{project_id_encoded}/{reactor_type_encoded})"
            
            table_data.append({
                "project_id": set_data['project_id'],
                "reactor_type": set_data['reactor_type'],
                "sample_count": set_data['sample_count'],
                "date_range": date_range,
                "avg_titer": f"{set_data['avg_titer']:.2f}" if set_data['avg_titer'] else "N/A",
                "avg_vcd": f"{set_data['avg_vcd']:.2e}" if set_data['avg_vcd'] else "N/A",
                "avg_viability": f"{set_data['avg_viability']:.1f}" if set_data['avg_viability'] else "N/A",
                "clones": clone_list,
                "created_date": set_data['min_created'].strftime("%Y-%m-%d") if set_data['min_created'] else "",
                "actions": actions
            })
        
        # Calculate metrics
        unique_projects = samples_query.values('project_id').distinct().count()
        total_sets = len(table_data)
        total_samples = samples_query.count()
        avg_samples_per_set = f"{total_samples / total_sets:.1f}" if total_sets > 0 else "0"
        
        # Get project options for dropdown
        all_projects = LimsUpstreamSamples.objects.values_list('project_id', flat=True).distinct()
        project_options = [{"label": "All Projects", "value": "all"}]
        project_options.extend([{"label": p, "value": p} for p in all_projects if p])
        
        return (
            table_data,
            str(unique_projects),
            str(total_sets),
            str(total_samples),
            avg_samples_per_set,
            project_options
        )
        
    except Exception as e:
        print(f"Error loading USP sample sets: {e}")
        return [], "0", "0", "0", "0", [{"label": "All Projects", "value": "all"}]


# SAMPLE SET DETAILS CALLBACK
@app.callback(
    Output("usp-sample-set-details-container", "children"),
    [Input("usp-sample-sets-table", "active_cell")],
    [State("usp-sample-sets-table", "data")],
    prevent_initial_call=True
)
def show_usp_sample_set_details(active_cell, table_data):
    """Show detailed view for selected sample set"""
    if not active_cell or not table_data:
        return no_update
    
    row_idx = active_cell["row"]
    if row_idx >= len(table_data):
        return no_update
    
    selected_set = table_data[row_idx]
    project_id = selected_set["project_id"]
    reactor_type = selected_set["reactor_type"]
    
    try:
        # Get samples for this set
        samples = LimsUpstreamSamples.objects.filter(
            project_id=project_id,
            reactor_type=reactor_type
        ).order_by('-harvest_date')
        
        # Create detailed view
        from ..layouts.sample_sets import create_sample_set_details_view
        details_view = create_sample_set_details_view(project_id, reactor_type)
        
        return details_view
        
    except Exception as e:
        print(f"Error showing sample set details: {e}")
        return dbc.Alert(f"Error loading details: {str(e)}", color="danger")


# LOAD SAMPLES FOR SPECIFIC SET
@app.callback(
    [Output("usp-set-samples-table", "data"),
     Output("usp-set-project-info", "children"),
     Output("usp-set-performance-metrics", "children"),
     Output("usp-set-culture-conditions", "children")],
    [Input("usp-sample-set-details-container", "children")],
    [State("usp-selected-set-store", "data")],
    prevent_initial_call=True
)
def load_usp_set_samples(details_container, selected_set_data):
    """Load samples and statistics for a specific set"""
    if not details_container or not selected_set_data:
        return [], "", "", ""
    
    try:
        project_id = selected_set_data.get("project_id")
        reactor_type = selected_set_data.get("reactor_type")
        
        if not project_id or not reactor_type:
            return [], "", "", ""
        
        # Get samples
        samples = LimsUpstreamSamples.objects.filter(
            project_id=project_id,
            reactor_type=reactor_type
        ).order_by('-harvest_date')
        
        # Convert to table data
        samples_data = []
        for sample in samples:
            samples_data.append({
                "sample_number": sample.sample_name,
                "cell_line": sample.cell_line or "",
                "run_date": sample.run_date.strftime("%Y-%m-%d") if sample.run_date else "",
                "harvest_date": sample.harvest_date.strftime("%Y-%m-%d") if sample.harvest_date else "",
                "culture_duration": sample.culture_duration or "",
                "max_vcd": f"{sample.max_vcd:.2e}" if sample.max_vcd else "",
                "viability": sample.viability or "",
                "final_titer": sample.final_titer or "",
                "culture_volume": sample.culture_volume or "",
                "feed_strategy": sample.feed_strategy or "",
                "note": sample.note or ""
            })
        
        # Calculate statistics
        project_info = html.Div([
            html.P([html.Strong("Project: "), project_id]),
            html.P([html.Strong("Reactor: "), reactor_type]),
            html.P([html.Strong("Samples: "), str(len(samples_data))])
        ])
        
        # Performance metrics
        titers = [s.final_titer for s in samples if s.final_titer]
        vcds = [s.max_vcd for s in samples if s.max_vcd]
        viabilities = [s.viability for s in samples if s.viability]
        
        performance_metrics = html.Div([
            html.P([html.Strong("Avg Titer: "), 
                   f"{np.mean(titers):.2f} g/L" if titers else "N/A"]),
            html.P([html.Strong("Max Titer: "), 
                   f"{np.max(titers):.2f} g/L" if titers else "N/A"]),
            html.P([html.Strong("Avg VCD: "), 
                   f"{np.mean(vcds):.2e}" if vcds else "N/A"]),
            html.P([html.Strong("Avg Viability: "), 
                   f"{np.mean(viabilities):.1f}%" if viabilities else "N/A"])
        ])
        
        # Culture conditions
        phs = [s.ph for s in samples if s.ph]
        dos = [s.do_percent for s in samples if s.do_percent]
        temps = [s.temperature for s in samples if s.temperature]
        
        culture_conditions = html.Div([
            html.P([html.Strong("Avg pH: "), 
                   f"{np.mean(phs):.2f}" if phs else "N/A"]),
            html.P([html.Strong("Avg DO: "), 
                   f"{np.mean(dos):.1f}%" if dos else "N/A"]),
            html.P([html.Strong("Avg Temp: "), 
                   f"{np.mean(temps):.1f}°C" if temps else "N/A"])
        ])
        
        return samples_data, project_info, performance_metrics, culture_conditions
        
    except Exception as e:
        print(f"Error loading set samples: {e}")
        return [], "Error loading data", "", ""


# EXPORT SAMPLE SET CALLBACK
@app.callback(
    Output("usp-export-set-btn", "n_clicks"),
    [Input("usp-export-set-btn", "n_clicks")],
    [State("usp-set-samples-table", "data"),
     State("usp-selected-set-store", "data")],
    prevent_initial_call=True
)
def export_usp_sample_set(n_clicks, samples_data, selected_set_data):
    """Export sample set to Excel"""
    if not n_clicks or not samples_data:
        return no_update
    
    try:
        project_id = selected_set_data.get("project_id", "unknown")
        reactor_type = selected_set_data.get("reactor_type", "unknown")
        
        # Convert to DataFrame
        df = pd.DataFrame(samples_data)
        
        # Create filename
        filename = f"USP_Set_{project_id}_{reactor_type}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        # Would normally trigger download here
        print(f"Would export {len(samples_data)} samples to {filename}")
        
        return n_clicks
        
    except Exception as e:
        print(f"Error exporting sample set: {e}")
        return no_update


print("USP sample_sets callbacks configured successfully")