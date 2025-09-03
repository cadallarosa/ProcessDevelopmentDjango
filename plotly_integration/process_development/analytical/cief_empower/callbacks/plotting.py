from dash import Input, Output, State, callback_context
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from scipy.signal import find_peaks, savgol_filter
from scipy.integrate import simpson
import pandas as pd

from ..app import app
from plotly_integration.models import Report, TimeSeriesData, SampleMetadata
from .utils import calculate_pi_from_time

@app.callback(
    Output("cief-plot", "figure"),
    Output("peak-results-table", "data"),
    Input("selected-report", "data"),
    Input("height-threshold", "value"),
    Input("prominence", "value"),
    Input("smoothing-window", "value"),
    State("pi-regression-data", "data")
)
def update_cief_plot(report_id, height_threshold, prominence, smoothing_window, regression_data):
    if not report_id:
        # Return empty plot
        fig = go.Figure()
        fig.update_layout(
            title="Select a report to view data",
            xaxis_title="Time (min)",
            yaxis_title="Absorbance (AU)",
            height=600,
            template="plotly_white"
        )
        return fig, []
    
    # Fetch data from database using SEC models
    try:
        # Get samples for this report
        samples = SampleMetadata.objects.filter(report_id=report_id)
        
        if not samples.exists():
            fig = go.Figure()
            fig.update_layout(
                title="No samples found for selected report",
                xaxis_title="Time (min)",
                yaxis_title="Absorbance (AU)",
                height=600,
                template="plotly_white"
            )
            return fig, []
        
        # Get first sample's time series data for plotting
        first_sample = samples.first()
        timeseries = TimeSeriesData.objects.filter(result_id=first_sample.result_id).order_by('time')
        
        if not timeseries.exists():
            fig = go.Figure()
            fig.update_layout(
                title="No time series data found",
                xaxis_title="Time (min)",
                yaxis_title="Absorbance (AU)", 
                height=600,
                template="plotly_white"
            )
            return fig, []
        
        # Convert to DataFrame
        data = pd.DataFrame(list(timeseries.values('time', 'absorbance')))
        data.rename(columns={'time': 'time_min', 'absorbance': 'channel_1'}, inplace=True)
        
        # Apply smoothing if specified
        if smoothing_window and smoothing_window > 0:
            # Ensure odd window size
            if smoothing_window % 2 == 0:
                smoothing_window += 1
            if len(data) > smoothing_window:
                data['channel_1_smooth'] = savgol_filter(data['channel_1'], smoothing_window, 3)
                signal = data['channel_1_smooth'].values
            else:
                signal = data['channel_1'].values
        else:
            signal = data['channel_1'].values
        
        time = data['time_min'].values
        
        # Detect peaks
        distance = 10  # Default distance for cIEF
        peaks, properties = find_peaks(
            signal,
            height=height_threshold or 0.01,
            prominence=prominence or 0.005,
            distance=distance
        )
        
        # Calculate peak areas
        peak_data = []
        for i, peak_idx in enumerate(peaks):
            # Find peak boundaries (valley to valley)
            left_idx = peak_idx
            right_idx = peak_idx
            
            # Find left boundary
            while left_idx > 0 and signal[left_idx-1] < signal[left_idx]:
                left_idx -= 1
            
            # Find right boundary  
            while right_idx < len(signal)-1 and signal[right_idx+1] < signal[right_idx]:
                right_idx += 1
            
            # Calculate area using Simpson's rule
            peak_time = time[left_idx:right_idx+1]
            peak_signal = signal[left_idx:right_idx+1]
            
            if len(peak_time) > 1:
                area = simpson(peak_signal, x=peak_time)
            else:
                area = 0
            
            # Calculate pI if regression is available
            pi_value = calculate_pi_from_time(time[peak_idx], regression_data) if regression_data else None
            
            peak_data.append({
                'peak_num': i + 1,
                'time': time[peak_idx],
                'height': signal[peak_idx],
                'area': area,
                'pi': pi_value,
                'left_idx': left_idx,
                'right_idx': right_idx
            })
        
        # Create plot
        fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3],
                           subplot_titles=("cIEF Electropherogram", "Peak Detection"))
        
        # Main trace
        fig.add_trace(
            go.Scatter(x=time, y=data['channel_1'], 
                      mode='lines', name='Raw Signal',
                      line=dict(color='lightblue', width=1)),
            row=1, col=1
        )
        
        if 'channel_1_smooth' in data.columns:
            fig.add_trace(
                go.Scatter(x=time, y=data['channel_1_smooth'], 
                          mode='lines', name='Smoothed Signal',
                          line=dict(color='navy', width=2)),
                row=1, col=1
            )
        
        # Add peak markers
        if peaks.size > 0:
            fig.add_trace(
                go.Scatter(x=time[peaks], y=signal[peaks],
                          mode='markers', name='Detected Peaks',
                          marker=dict(color='red', size=8, symbol='x')),
                row=1, col=1
            )
            
            # Add peak labels with pI values
            for peak in peak_data:
                label = f"Peak {peak['peak_num']}"
                if peak['pi'] is not None:
                    label += f"<br>pI: {peak['pi']:.2f}"
                
                fig.add_annotation(
                    x=peak['time'], y=peak['height'],
                    text=label,
                    showarrow=True,
                    arrowhead=2,
                    ax=0, ay=-40,
                    row=1, col=1
                )
        
        # Add derivative plot for peak detection visualization
        if len(signal) > 0:
            # Calculate first derivative
            dt = np.mean(np.diff(time))
            first_deriv = np.gradient(signal, dt)
            
            fig.add_trace(
                go.Scatter(x=time, y=first_deriv,
                          mode='lines', name='First Derivative',
                          line=dict(color='green', width=1)),
                row=2, col=1
            )
            
            # Add zero line
            fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
        
        # Update layout
        fig.update_xaxes(title_text="Time (min)", row=2, col=1)
        fig.update_xaxes(title_text="", row=1, col=1)
        fig.update_yaxes(title_text="Absorbance (AU)", row=1, col=1)
        fig.update_yaxes(title_text="dA/dt", row=2, col=1)
        
        fig.update_layout(
            height=600,
            showlegend=True,
            template="plotly_white",
            title=f"cIEF Analysis - Report ID: {report_id}"
        )
        
        # Convert peak data to table format
        table_data = []
        total_area = sum(p['area'] for p in peak_data) if peak_data else 1
        
        for peak in peak_data:
            table_data.append({
                'peak_num': peak['peak_num'],
                'retention_time': round(peak['time'], 2),
                'height': round(peak['height'], 4),
                'area': round(peak['area'], 2),
                'percent_area': round((peak['area'] / total_area * 100) if total_area > 0 else 0, 2),
                'pi': round(peak['pi'], 2) if peak['pi'] is not None else None,
                'is_pi_marker': 'No'  # Default, user can change
            })
        
        return fig, table_data
        
    except Exception as e:
        print(f"Error in plotting: {e}")
        fig = go.Figure()
        fig.update_layout(
            title=f"Error loading data: {str(e)}",
            xaxis_title="Time (min)",
            yaxis_title="Absorbance (AU)",
            height=600,
            template="plotly_white"
        )
        return fig, []