from dash import Input, Output, State, callback_context
import json

from ..app import app
from plotly_integration.models import Report, LimsCiefResult

@app.callback(
    Output("report-results-btn", "style"),
    Input("report-results-btn", "n_clicks"),
    State("selected-report", "data"),
    State("peak-results-table", "data"),
    State("pi-regression-data", "data"),
    prevent_initial_call=True
)
def handle_report_results(n_clicks, report_id, table_data, regression_data):
    if not n_clicks or not report_id or not table_data:
        # Default button style
        return {
            'backgroundColor': '#0891b2',
            'color': 'white',
            'border': 'none',
            'padding': '12px 20px',
            'fontSize': '14px',
            'cursor': 'pointer',
            'borderRadius': '10px',
            'fontWeight': '600',
            'transition': 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            'boxShadow': '0 4px 12px rgba(8, 145, 178, 0.25)',
            'position': 'relative',
            'overflow': 'hidden'
        }
    
    try:
        # Save results to LIMS cIEF results table
        report = Report.objects.get(id=report_id)
        
        for row in table_data:
            if row.get('area', 0) > 0:  # Only save peaks with area
                # Create or update LimsCiefResult
                result, created = LimsCiefResult.objects.get_or_create(
                    report=report,
                    peak_number=row.get('peak_num'),
                    defaults={
                        'retention_time': row.get('retention_time', 0),
                        'height': row.get('height', 0),
                        'area': row.get('area', 0),
                        'percent_area': row.get('percent_area', 0),
                        'pi_value': row.get('pi', None),
                        'is_pi_marker': row.get('is_pi_marker') == 'Yes'
                    }
                )
                
                if not created:
                    # Update existing result
                    result.retention_time = row.get('retention_time', 0)
                    result.height = row.get('height', 0)
                    result.area = row.get('area', 0)
                    result.percent_area = row.get('percent_area', 0)
                    result.pi_value = row.get('pi', None)
                    result.is_pi_marker = row.get('is_pi_marker') == 'Yes'
                    result.save()
        
        # Update report settings with regression data
        if regression_data:
            settings = {
                'pi_regression': regression_data,
                'results_reported': True,
                'reported_at': str(callback_context.triggered[0]['timestamp']) if callback_context.triggered else None
            }
            
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
        
        # Success button style (green)
        return {
            'backgroundColor': '#059669',
            'color': 'white',
            'border': 'none',
            'padding': '12px 20px',
            'fontSize': '14px',
            'cursor': 'pointer',
            'borderRadius': '10px',
            'fontWeight': '600',
            'transition': 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            'boxShadow': '0 4px 12px rgba(5, 150, 105, 0.25)',
            'position': 'relative',
            'overflow': 'hidden'
        }
        
    except Exception as e:
        print(f"Error reporting results: {e}")
        # Error button style (red)
        return {
            'backgroundColor': '#dc2626',
            'color': 'white',
            'border': 'none',
            'padding': '12px 20px',
            'fontSize': '14px',
            'cursor': 'pointer',
            'borderRadius': '10px',
            'fontWeight': '600',
            'transition': 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            'boxShadow': '0 4px 12px rgba(220, 38, 38, 0.25)',
            'position': 'relative',
            'overflow': 'hidden'
        }