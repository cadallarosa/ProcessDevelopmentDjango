#!/usr/bin/env python
import os
import django
import plotly.graph_objects as go
import pandas as pd

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from plotly_integration.models import TimeSeriesData

def create_sec_plot():
    # Query TimeSeriesData for YIVO system with result_id 23617
    data = TimeSeriesData.objects.filter(
        system_name='YIVO and FMA',
        result_id=23617
    ).order_by('time')
    
    if not data.exists():
        print("No data found for result_id 23617 in YIVO system")
        return
    
    # Convert to pandas DataFrame
    df = pd.DataFrame(list(data.values('time', 'channel_1', 'channel_2', 'channel_3')))
    
    print(f"Found {len(df)} data points")
    print(f"Time range: {df['time'].min():.3f} - {df['time'].max():.3f} minutes")
    print(f"Available channels: {[col for col in ['channel_1', 'channel_2', 'channel_3'] if df[col].notna().any()]}")
    
    # Create the plot
    fig = go.Figure()
    
    # Add time series data (assuming AU is in channel_1, adjust if needed)
    # Check which channel has data
    for channel in ['channel_1']:
        if df[channel].notna().any():
            fig.add_trace(go.Scatter(
                x=df['time'],
                y=df[channel],
                mode='lines',
                name=f'{channel.replace("_", " ").title()} (AU)',
                line=dict(width=2)
            ))
    
    # Add shaded regions
    regions = [
        (7.201, 7.701, 'Fraction 1 (HMW)'),
        (7.722, 8.001, 'Fraction 2 (Main)'),
        (8.023, 8.501, 'Fraction 3 (LMW)')
    ]
    
    colors = ['rgba(255, 0, 0, 0.2)', 'rgba(0, 255, 0, 0.2)', 'rgba(0, 0, 255, 0.2)']
    
    for i, (start, end, name) in enumerate(regions):
        fig.add_vrect(
            x0=start, x1=end,
            fillcolor=colors[i],
            opacity=0.3,
            layer="below",
            line_width=0,
            annotation_text=name,
            annotation_position="top left"
        )
    
    # Update layout
    fig.update_layout(
        title=f'SEC Time Series Data - Result ID: 23617 (YIVO System)',
        xaxis_title='Time (minutes)',
        yaxis_title='AU (Absorbance Units)',
        template='plotly_white',
        showlegend=True,
        width=1000,
        height=600
    )
    
    # Show the plot
    fig.show()
    
    # Optional: Save as HTML
    fig.write_html('sec_plot_23617.html')
    print("Plot saved as sec_plot_23617.html")

if __name__ == "__main__":
    create_sec_plot()