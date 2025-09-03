from dash import Input, Output, State, callback_context
import pandas as pd
from ..app import app
from .utils import calculate_pi_from_time

@app.callback(
    Output("peak-results-table", "data", allow_duplicate=True),
    Input("peak-results-table", "data"),
    Input("pi-regression-data", "data"),
    prevent_initial_call=True
)
def update_pi_values_in_table(table_data, regression_data):
    """Update pI values in table when regression data changes"""
    
    if not table_data or not regression_data:
        return table_data or []
    
    updated_data = []
    for row in table_data:
        updated_row = row.copy()
        retention_time = row.get('retention_time')
        
        if retention_time is not None:
            pi_value = calculate_pi_from_time(retention_time, regression_data)
            updated_row['pi'] = round(pi_value, 2) if pi_value is not None else None
        
        updated_data.append(updated_row)
    
    return updated_data

@app.callback(
    Output("peak-results-table", "data", allow_duplicate=True),
    Input("peak-results-table", "data"),
    State("pi-markers-store", "data"),
    prevent_initial_call=True
)
def auto_assign_pi_markers(table_data, pi_markers_store):
    """Automatically assign pI markers based on default values and peak proximity"""
    
    if not table_data:
        return []
    
    # Get default pI marker values
    default_markers = pi_markers_store.get('default_markers', [10.0, 9.5, 5.5, 4.0])
    
    # Sort table by retention time to find closest peaks to expected markers
    sorted_data = sorted(table_data, key=lambda x: x.get('retention_time', 0))
    
    # For initial assignment, mark the first few peaks as potential markers
    # This is a simple heuristic - in practice, users would manually select
    updated_data = []
    for i, row in enumerate(sorted_data):
        updated_row = row.copy()
        
        # Mark first 4 peaks as potential pI markers (matching default count)
        if i < len(default_markers):
            updated_row['is_pi_marker'] = 'Yes'
        else:
            updated_row['is_pi_marker'] = 'No'
        
        updated_data.append(updated_row)
    
    # Sort back to original peak number order
    final_data = sorted(updated_data, key=lambda x: x.get('peak_num', 0))
    
    return final_data

@app.callback(
    Output("pi-markers-store", "data"),
    Input("peak-results-table", "data"),
    State("pi-markers-store", "data"),
    prevent_initial_call=True
)
def update_pi_markers_store(table_data, current_store):
    """Update the pI markers store with user selections"""
    
    if not table_data:
        return current_store
    
    # Extract selected pI markers
    selected_markers = []
    for row in table_data:
        if row.get('is_pi_marker') == 'Yes':
            selected_markers.append({
                'peak_num': row.get('peak_num'),
                'retention_time': row.get('retention_time'),
                'pi_value': None  # Will be assigned when regression is calculated
            })
    
    updated_store = current_store.copy()
    updated_store['selected_markers'] = selected_markers
    
    return updated_store