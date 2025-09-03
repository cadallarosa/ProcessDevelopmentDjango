"""
Callbacks for data loading and management
"""

from dash import Input, Output, State, callback_context, no_update
from ..formulation_stability_app import app

@app.callback(
    Output('main-content-area', 'children'),
    Input('main-tabs', 'active_tab'),
    Input('formulation-data-store', 'data'),
    prevent_initial_call=True
)
def update_main_content(active_tab, formulation_data):
    """Update main content area based on active tab and data"""
    if not formulation_data:
        from ..layout.layout import create_empty_state
        return create_empty_state()
    
    try:
        if active_tab == "stability-trends":
            from ..layout.layout import create_stability_trends_layout
            return create_stability_trends_layout()
        elif active_tab == "formulation-details":
            from ..layout.layout import create_formulation_details_layout
            return create_formulation_details_layout()
        elif active_tab == "statistical-summary":
            from ..layout.layout import create_statistical_summary_layout
            return create_statistical_summary_layout()
        else:
            from ..layout.layout import create_empty_state
            return create_empty_state("Invalid tab selection")
            
    except Exception as e:
        from ..layout.layout import create_error_message
        return create_error_message(f"Error loading content: {str(e)}")

@app.callback(
    Output('selected-data-store', 'data'),
    Input('formulation-selector', 'value'),
    Input('storage-condition-selector', 'value'),
    Input('analysis-type-selector', 'value'),
    prevent_initial_call=True
)
def update_selected_data(selected_formulations, selected_storage_conditions, analysis_type):
    """Store selected parameters for use across callbacks"""
    return {
        'formulations': selected_formulations or [],
        'storage_conditions': selected_storage_conditions or [],
        'analysis_type': analysis_type or 'time_series'
    }