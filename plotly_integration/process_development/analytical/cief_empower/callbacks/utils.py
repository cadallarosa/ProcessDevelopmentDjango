from dash import Input, Output, State, callback_context
import base64
import io
import pandas as pd
import numpy as np
from ..app import app

def calculate_pi_from_time(time, regression_data):
    """Calculate pI value from retention time using linear regression parameters"""
    if not regression_data or regression_data.get('slope') == 0:
        return None
    
    slope = regression_data.get('slope', 0)
    intercept = regression_data.get('intercept', 0)
    
    return slope * time + intercept

@app.callback(
    Output("report-list-store", "data"),
    Input("load-once", "n_intervals")
)
def load_initial_reports(n_intervals):
    """Load initial report list on app startup"""
    if n_intervals != 1:
        return []
    
    try:
        from plotly_integration.models import CIEFReport
        
        reports = CIEFReport.objects.all().order_by('-created_at')[:100]
        
        report_list = [
            {
                'value': r.id,
                'label': f"{r.report_name} - {r.sample_set} ({r.created_at.strftime('%Y-%m-%d')})"
            }
            for r in reports
        ]
        
        return report_list
        
    except Exception as e:
        print(f"Error loading reports: {e}")
        return []

def parse_uploaded_file(contents, filename):
    """Parse uploaded CSV or Excel file for cIEF data"""
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        if 'csv' in filename:
            # Assume CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Excel file
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return None
        
        # Validate required columns
        required_cols = ['time', 'absorbance']  # Adjust based on expected format
        
        # Try to identify columns
        time_col = None
        abs_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'time' in col_lower or 'min' in col_lower:
                time_col = col
            elif 'abs' in col_lower or 'au' in col_lower or 'signal' in col_lower:
                abs_col = col
        
        if time_col and abs_col:
            return {
                'time': df[time_col].values.tolist(),
                'signal': df[abs_col].values.tolist(),
                'filename': filename
            }
        
    except Exception as e:
        print(f"Error parsing file: {e}")
        return None
    
    return None

def smooth_signal(signal, window_size=5):
    """Apply smoothing to signal using moving average"""
    
    if window_size % 2 == 0:
        window_size += 1
    
    half_window = window_size // 2
    smoothed = np.copy(signal)
    
    for i in range(half_window, len(signal) - half_window):
        smoothed[i] = np.mean(signal[i - half_window:i + half_window + 1])
    
    return smoothed

def baseline_correction(signal, method='linear'):
    """Apply baseline correction to signal"""
    
    if method == 'linear':
        # Simple linear baseline from first to last point
        x = np.arange(len(signal))
        baseline = np.linspace(signal[0], signal[-1], len(signal))
        corrected = signal - baseline
        
    elif method == 'polynomial':
        # Polynomial baseline fitting
        from scipy.optimize import curve_fit
        
        x = np.arange(len(signal))
        
        # Fit polynomial to valleys
        valleys = []
        for i in range(1, len(signal) - 1):
            if signal[i] < signal[i-1] and signal[i] < signal[i+1]:
                valleys.append(i)
        
        if len(valleys) > 3:
            poly_fit = np.polyfit(valleys, signal[valleys], 2)
            baseline = np.polyval(poly_fit, x)
            corrected = signal - baseline
        else:
            # Fall back to linear
            baseline = np.linspace(signal[0], signal[-1], len(signal))
            corrected = signal - baseline
    
    else:
        corrected = signal
    
    return corrected