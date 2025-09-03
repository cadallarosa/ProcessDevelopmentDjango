# USP view_samples callbacks
from dash import Input, Output, State, ctx, no_update, html
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime, timedelta
import json
from plotly_integration.models import LimsUpstreamSamples, LimsProjectInformation
from plotly_integration.pd_dashboard.main_app import app
from django.db.models import Avg, Count, Q
import numpy as np

print("Configuring USP view_samples callbacks...")


# MAIN DATA LOADING CALLBACK
@app.callback(
    [Output("usp-samples-table", "data"),
     Output("usp-samples-data-store", "data"),
     Output("usp-project-filter", "options"),
     Output("usp-total-samples", "children"),
     Output("usp-total-projects", "children"),
     Output("usp-avg-titer", "children"),
     Output("usp-avg-vcd", "children")],
    [Input("usp-refresh-btn", "n_clicks"),
     Input("usp-samples-search", "value"),
     Input("usp-project-filter", "value"),
     Input("usp-reactor-filter", "value"),
     Input("usp-date-range", "start_date"),
     Input("usp-date-range", "end_date")],
    prevent_initial_call=False
)
def load_usp_samples(n_clicks, search_value, project_filter, reactor_filter, start_date, end_date):
    """Load and filter USP samples from database"""
    try:
        # Start with all USP samples
        samples_query = LimsUpstreamSamples.objects.all()
        
        # Apply filters
        if search_value:
            samples_query = samples_query.filter(
                Q(sample_name__icontains=search_value) |
                Q(cell_line__icontains=search_value) |
                Q(project_id__icontains=search_value) |
                Q(feed_strategy__icontains=search_value)
            )
        
        if project_filter and project_filter != "all":
            samples_query = samples_query.filter(project_id=project_filter)
        
        if reactor_filter and reactor_filter != "all":
            samples_query = samples_query.filter(reactor_type=reactor_filter)
        
        if start_date:
            samples_query = samples_query.filter(harvest_date__gte=start_date)
        
        if end_date:
            samples_query = samples_query.filter(harvest_date__lte=end_date)
        
        # Get samples
        samples = samples_query.order_by('-created_date')
        
        # Convert to dataframe
        data = []
        for sample in samples:
            data.append({
                "sample_number": sample.sample_name,
                "project_id": sample.project_id or "",
                "reactor_type": sample.reactor_type or "",
                "cell_line": sample.cell_line or "",
                "run_date": sample.run_date.strftime("%Y-%m-%d") if sample.run_date else "",
                "harvest_date": sample.harvest_date.strftime("%Y-%m-%d") if sample.harvest_date else "",
                "culture_duration": sample.culture_duration or "",
                "max_vcd": f"{sample.max_vcd:.2e}" if sample.max_vcd else "",
                "viability": sample.viability or "",
                "final_titer": sample.final_titer or "",
                "culture_volume": sample.culture_volume or "",
                "ph": sample.ph or "",
                "do_percent": sample.do_percent or "",
                "temperature": sample.temperature or "",
                "feed_strategy": sample.feed_strategy or "",
                "note": sample.note or "",
                "created_date": sample.created_date.strftime("%Y-%m-%d %H:%M") if sample.created_date else "",
                "id": sample.id  # Keep ID for updates
            })
        
        # Get unique projects for dropdown
        all_projects = LimsUpstreamSamples.objects.values_list('project_id', flat=True).distinct()
        project_options = [{"label": "All Projects", "value": "all"}]
        project_options.extend([{"label": p, "value": p} for p in all_projects if p])
        
        # Calculate statistics
        total_samples = len(data)
        unique_projects = len(set([d["project_id"] for d in data if d["project_id"]]))
        
        # Calculate averages
        titers = [float(d["final_titer"]) for d in data if d["final_titer"] and d["final_titer"] != ""]
        avg_titer = f"{np.mean(titers):.2f}" if titers else "N/A"
        
        vcds = []
        for d in data:
            if d["max_vcd"] and d["max_vcd"] != "":
                try:
                    vcds.append(float(d["max_vcd"]))
                except:
                    pass
        avg_vcd = f"{np.mean(vcds):.2e}" if vcds else "N/A"
        
        # Store original data for comparison
        store_data = {"original": data, "timestamp": datetime.now().isoformat()}
        
        return data, store_data, project_options, str(total_samples), str(unique_projects), avg_titer, avg_vcd
        
    except Exception as e:
        print(f"Error loading USP samples: {e}")
        return [], {}, [{"label": "All Projects", "value": "all"}], "0", "0", "N/A", "N/A"


# DETECT CHANGES CALLBACK
@app.callback(
    [Output("usp-save-btn", "disabled"),
     Output("usp-modified-rows-store", "data")],
    [Input("usp-samples-table", "data")],
    [State("usp-samples-data-store", "data")],
    prevent_initial_call=True
)
def detect_usp_changes(current_data, stored_data):
    """Detect if any changes were made to the table"""
    if not current_data or not stored_data or "original" not in stored_data:
        return True, []
    
    original_data = stored_data["original"]
    
    # Find modified rows
    modified_rows = []
    
    for i, current_row in enumerate(current_data):
        if i < len(original_data):
            original_row = original_data[i]
            # Compare each field
            if any(str(current_row.get(key, "")) != str(original_row.get(key, "")) 
                   for key in current_row.keys() if key != "id"):
                modified_rows.append(i)
    
    # Enable save button if there are changes
    has_changes = len(modified_rows) > 0
    return not has_changes, modified_rows


# SAVE CHANGES CALLBACK
@app.callback(
    Output("usp-update-status", "children"),
    [Input("usp-save-btn", "n_clicks")],
    [State("usp-samples-table", "data"),
     State("usp-modified-rows-store", "data")],
    prevent_initial_call=True
)
def save_usp_changes(n_clicks, table_data, modified_rows):
    """Save modified USP samples back to database"""
    if not n_clicks or not table_data or not modified_rows:
        return no_update
    
    try:
        updated_count = 0
        errors = []
        
        for row_idx in modified_rows:
            if row_idx < len(table_data):
                row = table_data[row_idx]
                
                if "id" in row:
                    try:
                        sample = LimsUpstreamSamples.objects.get(id=row["id"])
                        
                        # Update fields
                        sample.project_id = row.get("project_id") or None
                        sample.reactor_type = row.get("reactor_type") or None
                        sample.cell_line = row.get("cell_line") or None
                        sample.run_date = row.get("run_date") if row.get("run_date") else None
                        sample.harvest_date = row.get("harvest_date") if row.get("harvest_date") else None
                        sample.culture_duration = float(row.get("culture_duration")) if row.get("culture_duration") else None
                        
                        # Handle scientific notation for VCD
                        if row.get("max_vcd"):
                            try:
                                sample.max_vcd = float(row.get("max_vcd"))
                            except:
                                sample.max_vcd = None
                        else:
                            sample.max_vcd = None
                        
                        sample.viability = float(row.get("viability")) if row.get("viability") else None
                        sample.final_titer = float(row.get("final_titer")) if row.get("final_titer") else None
                        sample.culture_volume = float(row.get("culture_volume")) if row.get("culture_volume") else None
                        sample.ph = float(row.get("ph")) if row.get("ph") else None
                        sample.do_percent = float(row.get("do_percent")) if row.get("do_percent") else None
                        sample.temperature = float(row.get("temperature")) if row.get("temperature") else None
                        sample.feed_strategy = row.get("feed_strategy") or None
                        sample.note = row.get("note") or None
                        
                        sample.save()
                        updated_count += 1
                        
                    except LimsUpstreamSamples.DoesNotExist:
                        errors.append(f"Sample {row.get('sample_number')} not found")
                    except Exception as e:
                        errors.append(f"Error updating {row.get('sample_number')}: {str(e)}")
        
        if updated_count > 0:
            if errors:
                return dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Updated {updated_count} samples with {len(errors)} errors: {'; '.join(errors)}"
                ], color="warning", dismissible=True)
            else:
                return dbc.Alert([
                    html.I(className="fas fa-check-circle me-2"),
                    f"Successfully updated {updated_count} USP samples"
                ], color="success", dismissible=True)
        else:
            return dbc.Alert([
                html.I(className="fas fa-times-circle me-2"),
                f"No samples updated. Errors: {'; '.join(errors)}"
            ], color="danger", dismissible=True)
            
    except Exception as e:
        print(f"Error saving USP samples: {e}")
        return dbc.Alert([
            html.I(className="fas fa-times-circle me-2"),
            f"Error saving changes: {str(e)}"
        ], color="danger", dismissible=True)


# EXPORT CALLBACK
@app.callback(
    Output("usp-download-dataframe", "data"),
    [Input("usp-export-samples-btn", "n_clicks")],
    [State("usp-samples-table", "data")],
    prevent_initial_call=True
)
def export_usp_samples(n_clicks, table_data):
    """Export USP samples to Excel"""
    if not n_clicks or not table_data:
        return no_update
    
    try:
        df = pd.DataFrame(table_data)
        
        # Remove the internal ID column before export
        if 'id' in df.columns:
            df = df.drop('id', axis=1)
        
        # Create filename with timestamp
        filename = f"USP_Samples_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return dcc.send_data_frame(df.to_excel, filename, index=False)
        
    except Exception as e:
        print(f"Error exporting USP samples: {e}")
        return no_update


print("USP view_samples callbacks configured successfully")