"""
Callbacks for formulation selection and study management
"""

from dash import Input, Output, State, callback_context
from ..formulation_stability_app import app
from ..utils.data_processing import get_formulation_data
from plotly_integration.models import FormulationStudy, FormulationCondition

@app.callback(
    Output('formulation-selector', 'options'),
    Output('formulation-selector', 'value'),
    Input('study-selector', 'value'),
    State('formulation-selector', 'value')
)
def update_formulation_options(selected_study_id, current_formulation_values):
    """Update formulation dropdown when study is selected"""
    if not selected_study_id:
        return [], []
    
    try:
        formulations = FormulationCondition.objects.filter(
            study_id=selected_study_id
        ).order_by('formulation_number')
        
        options = [
            {
                'label': f"Formulation {f.formulation_number} (pH {f.ph})",
                'value': f.id
            } 
            for f in formulations
        ]
        
        # Preserve existing selections if they're still valid
        valid_values = [opt['value'] for opt in options]
        preserved_values = [v for v in (current_formulation_values or []) if v in valid_values]
        
        return options, preserved_values
        
    except Exception as e:
        print(f"Error updating formulation options: {e}")
        return [], []

@app.callback(
    Output('formulation-data-store', 'data'),
    Input('formulation-selector', 'value'),
    Input('storage-condition-selector', 'value'),
    prevent_initial_call=True
)
def load_formulation_data(selected_formulations, selected_storage_conditions):
    """Load formulation data when selections change"""
    if not selected_formulations or not selected_storage_conditions:
        return {}
    
    try:
        data = get_formulation_data(selected_formulations, selected_storage_conditions)
        return data
        
    except Exception as e:
        print(f"Error loading formulation data: {e}")
        return {}