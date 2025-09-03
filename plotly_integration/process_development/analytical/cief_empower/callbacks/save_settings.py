from dash import Input, Output, State, callback_context
import json
from datetime import datetime

from ..app import app
from plotly_integration.models import Report

@app.callback(
    Output('button-success-trigger', 'data'),
    Input('save-plot-settings', 'n_clicks'),
    State('selected-report', 'data'),
    State('pi-regression-data', 'data'),
    State('peak-results-table', 'data'),
    State('height-threshold', 'value'),
    State('prominence', 'value'),
    State('smoothing-window', 'value'),
    prevent_initial_call=True
)
def save_plot_settings(n_clicks, report_id, regression_data, table_data, height_threshold, prominence, smoothing_window):
    if not n_clicks or not report_id:
        return 0
    
    try:
        # Get the report
        report = Report.objects.get(id=report_id)
        
        # Prepare settings to save
        settings = {
            'pi_regression': regression_data,
            'peak_detection_settings': {
                'height_threshold': height_threshold,
                'prominence': prominence,
                'smoothing_window': smoothing_window
            },
            'peak_results': table_data,
            'saved_at': datetime.now().isoformat(),
            'app_type': 'cief_empower'
        }
        
        # Save to report settings
        if report.settings:
            try:
                current_settings = json.loads(report.settings)
                current_settings.update(settings)
                report.settings = json.dumps(current_settings)
            except json.JSONDecodeError:
                report.settings = json.dumps(settings)
        else:
            report.settings = json.dumps(settings)
        
        report.save()
        
        return n_clicks  # Trigger success animation
        
    except Exception as e:
        print(f"Error saving settings: {e}")
        return 0

@app.callback(
    Output('button-reset-interval', 'disabled'),
    Input('button-success-trigger', 'data'),
    prevent_initial_call=True
)
def reset_button_animation(trigger):
    if trigger > 0:
        return False  # Enable interval to reset animation
    return True