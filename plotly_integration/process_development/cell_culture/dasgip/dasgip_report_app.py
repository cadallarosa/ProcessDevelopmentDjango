"""
DASGIP Data Visualization and Reporting App
Dash application for viewing and analyzing imported DASGIP bioreactor data
"""

import dash
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State, callback_context, dash_table, no_update
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import os

from plotly_integration.models import (
    USPBioreactorRun, USPTimeSeriesData
)

# Initialize the Dash app
app = DjangoDash("DasgipReportApp")

# Enhanced color palette for better visuals
COLOR_PALETTE = {
    "process_value": "#2E86C1",      # Blue
    "setpoint": "#E74C3C",           # Red
    "output": "#F39C12",             # Orange
    "secondary": "#8E44AD",          # Purple
    "success": "#27AE60",            # Green
    "warning": "#F1C40F",            # Yellow
    "danger": "#E74C3C",             # Red (same as setpoint for danger state)
    "background": "#F8F9FA",         # Light gray
    "text": "#2C3E50",               # Dark blue-gray
    "accent": "#3498DB"              # Light blue
}

# Modern styling constants
MODERN_STYLE = {
    "font_family": "'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif",
    "card_shadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
    "border_radius": "8px",
    "spacing": "16px"
}

# Define the process parameters and their corresponding database fields
PROCESS_PARAMETERS = {
    "do": {"label": "Dissolved Oxygen", "unit": "% DO", "fields": ["do_pv", "do_sp", "do_out"]},
    "ph": {"label": "pH", "unit": "pH", "fields": ["ph_pv", "ph_sp", "ph_out"]},
    "temp": {"label": "Temperature", "unit": "°C", "fields": ["temp_pv", "temp_sp", "temp_out"]},
    "rpm": {"label": "Agitation Speed", "unit": "RPM", "fields": ["rpm_pv", "rpm_sp"]},
    "volume": {"label": "Reactor Volume", "unit": "mL", "fields": ["volume_pv"]},
    "air_flow": {"label": "Air Flow", "unit": "sL/h", "fields": ["air_flow_pv", "air_flow_sp"]},
    "feed_a": {"label": "Feed A Flow", "unit": "mL/h", "fields": ["feed_a_pv", "feed_a_sp"]},
    "feed_b": {"label": "Feed B Flow", "unit": "mL/h", "fields": ["feed_b_pv", "feed_b_sp"]},
    "o2_conc": {"label": "O2 Concentration", "unit": "%", "fields": ["o2_conc_pv", "o2_conc_sp"]},
    "co2_conc": {"label": "CO2 Concentration", "unit": "%", "fields": ["co2_conc_pv", "co2_conc_sp"]}
}

def load_bioreactor_runs():
    """Load available bioreactor runs from database"""
    try:
        runs = USPBioreactorRun.objects.all().values(
            'up_number', 'project_name', 'unit_number', 'setup_name',
            'start_timestamp', 'stop_timestamp', 'comment'
        )
        return list(runs)
    except Exception as e:
        print(f"Error loading bioreactor runs: {e}")
        return []

def load_timeseries_data(up_number):
    """Load time series data for a specific UP number"""
    try:
        # Get the run
        run = USPBioreactorRun.objects.get(up_number=up_number)

        # Get all time series data for this run
        data = USPTimeSeriesData.objects.filter(run=run).values(
            'timestamp', 'duration',
            'do_pv', 'do_sp', 'do_out',
            'ph_pv', 'ph_sp', 'ph_out',
            'temp_pv', 'temp_sp', 'temp_out',
            'rpm_pv', 'rpm_sp',
            'volume_pv',
            'air_flow_pv', 'air_flow_sp',
            'feed_a_pv', 'feed_a_sp',
            'feed_b_pv', 'feed_b_sp',
            'o2_conc_pv', 'o2_conc_sp',
            'co2_conc_pv', 'co2_conc_sp'
        ).order_by('timestamp')

        if data:
            df = pd.DataFrame(list(data))
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Always calculate Process_Hours from timestamps for accurate time axis
            # The duration field from import may have calculation errors
            start_time = df['timestamp'].min()
            df['Process_Hours'] = (df['timestamp'] - start_time).dt.total_seconds() / 3600

            return df
        else:
            return pd.DataFrame()
    except USPBioreactorRun.DoesNotExist:
        print(f"Run {up_number} not found")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error loading time series data for {up_number}: {e}")
        return pd.DataFrame()

# Initialize with empty data - will be loaded when user selects a run
dasgip_data = pd.DataFrame()
selected_run = None

def calculate_control_performance(df):
    """Calculate control performance statistics for process parameters"""
    if df.empty:
        return {}
    
    performance_stats = {}
    
    # Define control loop parameters to analyze
    control_params = {
        'do': {'pv': 'do_pv', 'sp': 'do_sp', 'name': 'Dissolved Oxygen', 'unit': '% DO'},
        'ph': {'pv': 'ph_pv', 'sp': 'ph_sp', 'name': 'pH', 'unit': 'pH'},
        'temp': {'pv': 'temp_pv', 'sp': 'temp_sp', 'name': 'Temperature', 'unit': '°C'},
        'rpm': {'pv': 'rpm_pv', 'sp': 'rpm_sp', 'name': 'Agitation Speed', 'unit': 'RPM'}
    }
    
    for param_key, param_info in control_params.items():
        pv_col = param_info['pv']
        sp_col = param_info['sp']
        
        if pv_col in df.columns and sp_col in df.columns:
            # Get valid data points where both PV and SP are available
            valid_data = df[(df[pv_col].notna()) & (df[sp_col].notna())].copy()
            
            if len(valid_data) > 10:  # Need sufficient data points
                pv_data = valid_data[pv_col]
                sp_data = valid_data[sp_col]
                
                # Calculate error (PV - SP)
                error = pv_data - sp_data
                
                # 1. Mean Absolute Error (MAE)
                mae = np.abs(error).mean()
                
                # 2. Root Mean Square Error (RMSE)
                rmse = np.sqrt((error ** 2).mean())
                
                # 3. Setpoint tracking accuracy (% time within ±5% of setpoint)
                sp_mean = sp_data.mean()
                tolerance = sp_mean * 0.05  # 5% tolerance
                within_tolerance = np.abs(error) <= tolerance
                tracking_accuracy = (within_tolerance.sum() / len(within_tolerance)) * 100
                
                # 4. Process variability (CV of PV)
                cv_pv = (pv_data.std() / pv_data.mean()) * 100 if pv_data.mean() != 0 else 0
                
                # 5. Setpoint changes analysis
                sp_changes = np.abs(sp_data.diff()).sum()
                avg_response_time = None
                
                # Calculate average response time for significant setpoint changes
                sp_diff = sp_data.diff().abs()
                significant_changes = sp_diff > (sp_data.std() * 1.5)  # Changes > 1.5 std dev
                
                if significant_changes.sum() > 0:
                    # Simple response time calculation (time to reach 90% of change)
                    response_times = []
                    for idx in valid_data[significant_changes].index:
                        try:
                            # Look at next 10 points after setpoint change
                            post_change = valid_data.loc[idx:idx+10]
                            if len(post_change) > 1:
                                target = post_change[sp_col].iloc[0]  # New setpoint
                                initial = post_change[pv_col].iloc[0]  # Initial PV
                                
                                # Find when PV reaches 90% of the way to new setpoint
                                target_90 = initial + 0.9 * (target - initial)
                                
                                for i, pv_val in enumerate(post_change[pv_col]):
                                    if abs(pv_val - target_90) < abs(initial - target_90) * 0.1:
                                        # Convert index to time (assuming uniform sampling)
                                        response_times.append(i * 5 / 60)  # Convert to minutes (5s sampling)
                                        break
                        except:
                            continue
                    
                    if response_times:
                        avg_response_time = np.mean(response_times)
                
                # 6. Control stability (how much the error varies)
                error_stability = error.std()
                
                performance_stats[param_key] = {
                    'name': param_info['name'],
                    'unit': param_info['unit'],
                    'mae': round(mae, 3),
                    'rmse': round(rmse, 3),
                    'tracking_accuracy': round(tracking_accuracy, 1),
                    'process_variability': round(cv_pv, 2),
                    'error_stability': round(error_stability, 3),
                    'setpoint_changes': int(sp_changes > 0),
                    'avg_response_time': round(avg_response_time, 1) if avg_response_time else 'N/A',
                    'data_points': len(valid_data)
                }
    
    return performance_stats

def detect_process_events(df, parameter_key):
    """Detect significant process events for annotation"""
    events = []
    if df.empty:
        return events

    param_config = PROCESS_PARAMETERS[parameter_key]
    sp_field = None

    # Find SP field
    for field in param_config["fields"]:
        if field.endswith('_sp') and field in df.columns:
            sp_field = field
            break

    if sp_field and sp_field in df.columns:
        # Detect setpoint changes
        sp_data = df[df[sp_field].notna()].copy()
        if len(sp_data) > 1:
            sp_diff = sp_data[sp_field].diff().abs()
            significant_changes = sp_diff > sp_diff.std() * 2

            for idx in sp_data[significant_changes].index:
                events.append({
                    'time': df.loc[idx, 'Process_Hours'],
                    'value': df.loc[idx, sp_field],
                    'type': 'setpoint_change',
                    'text': f"SP Change: {df.loc[idx, sp_field]:.2f}"
                })

    return events

def downsample_data(data, max_points=2000):
    """Downsample data to reduce plotting load while preserving trends"""
    if len(data) <= max_points:
        return data

    # Use every nth point to downsample
    step = len(data) // max_points
    return data.iloc[::step]

def create_process_plot(df, parameter_key, height=400):
    """Create a plot for a specific process parameter"""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available - Please select a run",
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(height=height)
        return fig

    param_config = PROCESS_PARAMETERS[parameter_key]
    available_fields = [field for field in param_config["fields"] if field in df.columns]

    if not available_fields:
        fig = go.Figure()
        error_text = f"No {param_config['label']} data available<br>"
        error_text += f"Looking for fields: {', '.join(param_config['fields'])}<br>"
        available_in_df = [col for col in df.columns if any(field.split('_')[0] in col for field in param_config["fields"])]
        if available_in_df:
            error_text += f"Available fields: {', '.join(available_in_df[:5])}"

        fig.add_annotation(
            text=error_text,
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=12, color="gray")
        )
        fig.update_layout(height=height)
        return fig

    # Create subplot with secondary y-axis if we have output values
    has_output = any(field.endswith('_out') for field in available_fields)
    fig = make_subplots(specs=[[{"secondary_y": has_output}]])

    # Enhanced color mapping using our palette
    colors = {
        "pv": COLOR_PALETTE["process_value"],
        "sp": COLOR_PALETTE["setpoint"],
        "out": COLOR_PALETTE["output"]
    }

    traces_added = 0
    for field in available_fields:
        data_subset = df[df[field].notna()]
        if len(data_subset) == 0:
            print(f"Skipping {field}: no valid data points")
            continue

        # Downsample data for better performance
        data_subset = downsample_data(data_subset, max_points=2000)

        # Determine trace type and color based on field suffix
        if field.endswith('_pv'):
            trace_name = "Process Value"
            color = colors["pv"]
            secondary_y = False
            line_style = dict(color=color, width=2)
        elif field.endswith('_sp'):
            trace_name = "Setpoint"
            color = colors["sp"]
            secondary_y = False
            line_style = dict(color=color, dash='dash', width=2)
        elif field.endswith('_out'):
            trace_name = "Controller Output"
            color = colors["out"]
            secondary_y = True
            line_style = dict(color=color, width=2)
        else:
            # Fallback for any other field types
            trace_name = field.replace('_', ' ').title()
            color = colors["pv"]
            secondary_y = False
            line_style = dict(color=color, width=2)

        fig.add_trace(
            go.Scatter(
                x=data_subset['Process_Hours'],
                y=data_subset[field],
                name=trace_name,
                line=line_style,
                hovertemplate=f"<b>{trace_name}</b><br>" +
                             "Time: %{x:.1f} hours<br>" +
                             f"Value: %{{y:.2f}} {param_config['unit']}<br>" +
                             "Timestamp: %{customdata}<br>" +
                             "<extra></extra>",
                customdata=data_subset['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S'),
                connectgaps=True
            ),
            secondary_y=secondary_y
        )
        traces_added += 1

    # Add process event annotations
    events = detect_process_events(df, parameter_key)
    for event in events:
        fig.add_annotation(
            x=event['time'],
            y=event['value'],
            text=event['text'],
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor=COLOR_PALETTE['warning'],
            ax=0,
            ay=-40,
            bgcolor=COLOR_PALETTE['warning'],
            bordercolor=COLOR_PALETTE['text'],
            borderwidth=1,
            font=dict(color='white', size=10)
        )

    # Update layout with enhanced styling
    fig.update_layout(
        title={
            'text': f"{param_config['label']} Over Time",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'family': MODERN_STYLE['font_family'], 'color': COLOR_PALETTE['text']}
        },
        height=height,
        template='plotly_white',
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor=COLOR_PALETTE['background'],
        font={'family': MODERN_STYLE['font_family']},
        margin={'t': 60, 'l': 60, 'r': 60, 'b': 60},
        legend={
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'right',
            'x': 1,
            'bgcolor': 'rgba(255,255,255,0.8)',
            'bordercolor': COLOR_PALETTE['text'],
            'borderwidth': 1
        }
    )

    # Update x-axis with enhanced styling and range selector
    fig.update_xaxes(
        title_text="Process Time (hours)",
        title_font={'size': 14, 'family': MODERN_STYLE['font_family']},
        gridcolor='rgba(0,0,0,0.1)',
        showgrid=True,
        zeroline=False,
        rangeslider=dict(
            visible=True,
            thickness=0.05,
            bgcolor=COLOR_PALETTE['background'],
            bordercolor=COLOR_PALETTE['accent'],
            borderwidth=1
        ),
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1h", step="hour", stepmode="backward"),
                dict(count=6, label="6h", step="hour", stepmode="backward"),
                dict(count=12, label="12h", step="hour", stepmode="backward"),
                dict(count=1, label="1d", step="day", stepmode="backward"),
                dict(step="all", label="All")
            ]),
            bgcolor=COLOR_PALETTE['background'],
            activecolor=COLOR_PALETTE['accent'],
            bordercolor=COLOR_PALETTE['text'],
            borderwidth=1
        )
    )

    # Update y-axes with enhanced styling and color-coded labels
    fig.update_yaxes(
        title_text=f"{param_config['label']} ({param_config['unit']})",
        secondary_y=False,
        title_font={'size': 14, 'family': MODERN_STYLE['font_family'], 'color': colors['pv']},
        gridcolor='rgba(0,0,0,0.1)',
        showgrid=True,
        zeroline=False
    )
    if has_output:
        fig.update_yaxes(
            title_text="Controller Output (%)",
            secondary_y=True,
            title_font={'size': 14, 'family': MODERN_STYLE['font_family'], 'color': colors['out']},
            gridcolor='rgba(0,0,0,0.05)',
            showgrid=True,
            zeroline=False
        )

    # Add debugging info if no traces were added
    if traces_added == 0:
        print(f"Warning: No traces added for parameter {parameter_key}")
        print(f"Available fields: {available_fields}")

    return fig

def create_overview_dashboard(df):
    """Create the main overview dashboard with multiple subplots"""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available - Please select a bioreactor run",
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=18, color="gray")
        )
        fig.update_layout(height=800)
        return fig

    # Create subplots - 3 rows, 2 columns with enhanced spacing
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=[
            'Dissolved Oxygen Control', 'pH Control',
            'Temperature Control', 'Agitation Speed',
            'Reactor Volume & Air Flow', 'Gas Concentrations'
        ],
        specs=[[{"secondary_y": True}, {"secondary_y": True}],
               [{"secondary_y": True}, {"secondary_y": False}],
               [{"secondary_y": True}, {"secondary_y": True}]],
        vertical_spacing=0.15,
        horizontal_spacing=0.08
    )

    # Enhanced color scheme for overview
    overview_colors = {
        'do': {'PV': COLOR_PALETTE['process_value'], 'SP': COLOR_PALETTE['setpoint'], 'Out': COLOR_PALETTE['output']},
        'ph': {'PV': COLOR_PALETTE['success'], 'SP': COLOR_PALETTE['setpoint'], 'Out': COLOR_PALETTE['secondary']},
        'temp': {'PV': '#E67E22', 'SP': COLOR_PALETTE['setpoint'], 'Out': COLOR_PALETTE['warning']},
        'rpm': {'PV': '#8B4513', 'SP': COLOR_PALETTE['setpoint']},
        'volume': COLOR_PALETTE['accent'],
        'air': '#17A2B8',
        'o2': '#20B2AA',
        'co2': '#708090'
    }

    # 1. DO Control (row=1, col=1)
    do_fields = ['do_pv', 'do_sp', 'do_out']
    for field in do_fields:
        if field in df.columns:
            data_subset = df[df[field].notna()]
            if len(data_subset) > 0:
                # Downsample for overview performance
                data_subset = downsample_data(data_subset, max_points=1000)
                trace_type = 'PV' if field.endswith('_pv') else 'SP' if field.endswith('_sp') else 'Out'
                color = overview_colors['do'][trace_type]
                line_style = dict(color=color, width=2) if trace_type != 'SP' else dict(color=color, dash='dash', width=2)
                secondary_y = field.endswith('_out')

                fig.add_trace(
                    go.Scatter(
                        x=data_subset['Process_Hours'],
                        y=data_subset[field],
                        name=f'DO {trace_type}',
                        line=line_style,
                        hovertemplate=f"<b>DO {trace_type}</b><br>Time: %{{x:.1f}}h<br>Value: %{{y:.2f}}<extra></extra>"
                    ),
                    row=1, col=1, secondary_y=secondary_y
                )

    # 2. pH Control (row=1, col=2)
    ph_fields = ['ph_pv', 'ph_sp', 'ph_out']
    for field in ph_fields:
        if field in df.columns:
            data_subset = df[df[field].notna()]
            if len(data_subset) > 0:
                data_subset = downsample_data(data_subset, max_points=1000)
                trace_type = 'PV' if field.endswith('_pv') else 'SP' if field.endswith('_sp') else 'Out'
                color = overview_colors['ph'][trace_type]
                line_style = dict(color=color, width=2) if trace_type != 'SP' else dict(color=color, dash='dash', width=2)
                secondary_y = field.endswith('_out')

                fig.add_trace(
                    go.Scatter(
                        x=data_subset['Process_Hours'],
                        y=data_subset[field],
                        name=f'pH {trace_type}',
                        line=line_style,
                        hovertemplate=f"<b>pH {trace_type}</b><br>Time: %{{x:.1f}}h<br>Value: %{{y:.2f}}<extra></extra>"
                    ),
                    row=1, col=2, secondary_y=secondary_y
                )

    # 3. Temperature Control (row=2, col=1)
    temp_fields = ['temp_pv', 'temp_sp', 'temp_out']
    for field in temp_fields:
        if field in df.columns:
            data_subset = df[df[field].notna()]
            if len(data_subset) > 0:
                data_subset = downsample_data(data_subset, max_points=1000)
                trace_type = 'PV' if field.endswith('_pv') else 'SP' if field.endswith('_sp') else 'Out'
                color = overview_colors['temp'][trace_type]
                line_style = dict(color=color, width=2) if trace_type != 'SP' else dict(color=color, dash='dash', width=2)
                secondary_y = field.endswith('_out')

                fig.add_trace(
                    go.Scatter(x=data_subset['Process_Hours'], y=data_subset[field],
                              name=f'Temp {trace_type}', line=line_style),
                    row=2, col=1, secondary_y=secondary_y
                )

    # 4. Agitation Speed (row=2, col=2)
    rpm_fields = ['rpm_pv', 'rpm_sp']
    for field in rpm_fields:
        if field in df.columns:
            data_subset = df[df[field].notna()]
            if len(data_subset) > 0:
                data_subset = downsample_data(data_subset, max_points=1000)
                trace_type = 'PV' if field.endswith('_pv') else 'SP'
                color = overview_colors['rpm'][trace_type]
                line_style = dict(color=color, width=2) if trace_type == 'PV' else dict(color=color, dash='dash', width=2)

                fig.add_trace(
                    go.Scatter(x=data_subset['Process_Hours'], y=data_subset[field],
                              name=f'RPM {trace_type}', line=line_style),
                    row=2, col=2
                )

    # 5. Volume and Air Flow (row=3, col=1)
    if 'volume_pv' in df.columns:
        vol_data = df[df['volume_pv'].notna()]
        if len(vol_data) > 0:
            vol_data = downsample_data(vol_data, max_points=1000)
            fig.add_trace(
                go.Scatter(x=vol_data['Process_Hours'], y=vol_data['volume_pv'],
                          name='Volume', line=dict(color=overview_colors['volume'], width=2)),
                row=3, col=1
            )

    if 'air_flow_pv' in df.columns:
        air_data = df[df['air_flow_pv'].notna()]
        if len(air_data) > 0:
            air_data = downsample_data(air_data, max_points=1000)
            fig.add_trace(
                go.Scatter(x=air_data['Process_Hours'], y=air_data['air_flow_pv'],
                          name='Air Flow', line=dict(color=overview_colors['air'], width=2)),
                row=3, col=1, secondary_y=True
            )

    # 6. Gas Concentrations (row=3, col=2)
    if 'o2_conc_pv' in df.columns:
        o2_data = df[df['o2_conc_pv'].notna()]
        if len(o2_data) > 0:
            o2_data = downsample_data(o2_data, max_points=1000)
            fig.add_trace(
                go.Scatter(x=o2_data['Process_Hours'], y=o2_data['o2_conc_pv'],
                          name='O2 %', line=dict(color=overview_colors['o2'], width=2)),
                row=3, col=2
            )

    if 'co2_conc_pv' in df.columns:
        co2_data = df[df['co2_conc_pv'].notna()]
        if len(co2_data) > 0:
            co2_data = downsample_data(co2_data, max_points=1000)
            fig.add_trace(
                go.Scatter(x=co2_data['Process_Hours'], y=co2_data['co2_conc_pv'],
                          name='CO2 %', line=dict(color=overview_colors['co2'], width=2)),
                row=3, col=2, secondary_y=True
            )

    # Update layout with enhanced styling
    fig.update_layout(
        title={
            'text': "DASGIP Bioreactor Process Overview",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'family': MODERN_STYLE['font_family'], 'color': COLOR_PALETTE['text']}
        },
        height=1000,
        showlegend=True,
        template='plotly_white',
        plot_bgcolor='white',
        paper_bgcolor=COLOR_PALETTE['background'],
        font={'family': MODERN_STYLE['font_family']},
        margin={'t': 80, 'l': 60, 'r': 60, 'b': 60},
        legend={
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': -0.15,
            'xanchor': 'center',
            'x': 0.5,
            'bgcolor': 'rgba(255,255,255,0.9)',
            'bordercolor': COLOR_PALETTE['text'],
            'borderwidth': 1
        }
    )

    # Update x-axes
    for row in range(1, 4):
        for col in range(1, 3):
            fig.update_xaxes(title_text="Process Time (hours)", row=row, col=col)

    # Update y-axes with appropriate units and color-coded labels
    fig.update_yaxes(title_text="% DO", row=1, col=1, title_font={'color': overview_colors['do']['PV']})
    fig.update_yaxes(title_text="% Output", row=1, col=1, secondary_y=True, title_font={'color': overview_colors['do']['Out']})
    fig.update_yaxes(title_text="pH", row=1, col=2, title_font={'color': overview_colors['ph']['PV']})
    fig.update_yaxes(title_text="% Output", row=1, col=2, secondary_y=True, title_font={'color': overview_colors['ph']['Out']})
    fig.update_yaxes(title_text="°C", row=2, col=1, title_font={'color': overview_colors['temp']['PV']})
    fig.update_yaxes(title_text="% Output", row=2, col=1, secondary_y=True, title_font={'color': overview_colors['temp']['Out']})
    fig.update_yaxes(title_text="RPM", row=2, col=2, title_font={'color': overview_colors['rpm']['PV']})
    fig.update_yaxes(title_text="mL", row=3, col=1, title_font={'color': overview_colors['volume']})
    fig.update_yaxes(title_text="sL/h", row=3, col=1, secondary_y=True, title_font={'color': overview_colors['air']})
    fig.update_yaxes(title_text="% O2", row=3, col=2, title_font={'color': overview_colors['o2']})
    fig.update_yaxes(title_text="% CO2", row=3, col=2, secondary_y=True, title_font={'color': overview_colors['co2']})

    return fig

# App layout following SEC app pattern
app.layout = html.Div([
    # Toolbar section matching SEC app pattern
    html.Div(
        id='toolbar-container',
        style={
            'display': 'flex',
            'justifyContent': 'space-between',
            'alignItems': 'center',
            'padding': '15px 20px',
            'backgroundColor': '#ffffff',
            'borderBottom': '1px solid #e3e6ea',
            'gap': '10px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.08)',
            'position': 'relative',
            'zIndex': '10'
        },
        children=[
            # Left side - Select Run button
            html.Div(
                style={'display': 'flex', 'gap': '20px', 'alignItems': 'center'},
                children=[
                    html.Button([
                        html.Span("🧬 ", style={'marginRight': '5px'}),
                        "Select Bioreactor Run"
                    ], id="select-run-btn", style={
                        'backgroundColor': '#2563eb',
                        'color': 'white',
                        'border': 'none',
                        'padding': '12px 24px',
                        'fontSize': '14px',
                        'cursor': 'pointer',
                        'borderRadius': '12px',
                        'fontWeight': '600',
                        'transition': 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                        'boxShadow': '0 4px 12px rgba(37, 99, 235, 0.25)',
                        'position': 'relative',
                        'overflow': 'hidden'
                    }),
                    html.Div([
                        html.Span(id="current-run-text", children="No run selected",
                                  style={'color': '#6c757d', 'fontSize': '14px'})
                    ])
                ]
            ),

            # Right side - Title
            html.Div([
                html.H1("🧬 DASGIP Bioreactor Analysis", 
                        style={
                            'color': COLOR_PALETTE['text'], 
                            'marginBottom': '0px',
                            'fontFamily': MODERN_STYLE['font_family'],
                            'fontSize': '1.5rem',
                            'fontWeight': '600'
                        })
            ])
        ]
    ),

    # Enhanced tabs with modern styling
    html.Div([
        dcc.Tabs(
            id="main-tabs",
            value="overview",
            children=[
                dcc.Tab(label="📊 Process Overview", value="overview",
                       style={'fontFamily': MODERN_STYLE['font_family']}),
                dcc.Tab(label="📈 Individual Parameters", value="parameters",
                       style={'fontFamily': MODERN_STYLE['font_family']}),
                dcc.Tab(label="🎯 Control Performance", value="control",
                       style={'fontFamily': MODERN_STYLE['font_family']})
            ],
            style={
                'fontFamily': MODERN_STYLE['font_family'],
                'fontSize': '16px'
            },
            colors={
                'border': COLOR_PALETTE['accent'],
                'primary': COLOR_PALETTE['accent'],
                'background': COLOR_PALETTE['background']
            }
        )
    ], style={'margin': '0px 20px'}),

    # Run selection modal with tabs
    html.Div(
        id="run-modal",
        style={
            'display': 'none',
            'position': 'fixed',
            'zIndex': '1000',
            'left': '0',
            'top': '0',
            'width': '100%',
            'height': '100%',
            'backgroundColor': 'rgba(0,0,0,0.6)',
            'backdropFilter': 'blur(4px)',
            'overflow': 'auto',
            'animation': 'fadeIn 0.3s ease-out'
        },
        children=[
            html.Div(
                style={
                    'backgroundColor': 'white',
                    'margin': '40px auto',
                    'padding': '32px',
                    'border': 'none',
                    'borderRadius': '20px',
                    'width': '90%',
                    'maxWidth': '1200px',
                    'maxHeight': '85vh',
                    'overflow': 'auto',
                    'boxShadow': '0 25px 50px -12px rgba(0,0,0,0.25)',
                    'position': 'relative',
                    'transform': 'scale(1)',
                    'animation': 'modalSlideUp 0.3s ease-out'
                },
                children=[
                    # Modal header
                    html.Div([
                        html.H3("Bioreactor Data Management", style={
                            'margin': '0 0 20px 0',
                            'color': COLOR_PALETTE['text'],
                            'fontFamily': MODERN_STYLE['font_family'],
                            'fontSize': '1.5rem',
                            'fontWeight': '600'
                        }),
                        html.Button("×", id="close-run-modal-btn", style={
                            'position': 'absolute',
                            'top': '16px',
                            'right': '16px',
                            'background': '#f3f4f6',
                            'border': 'none',
                            'fontSize': '20px',
                            'cursor': 'pointer',
                            'color': '#6b7280',
                            'padding': '8px',
                            'width': '36px',
                            'height': '36px',
                            'borderRadius': '50%',
                            'display': 'flex',
                            'alignItems': 'center',
                            'justifyContent': 'center',
                            'transition': 'all 0.2s ease',
                            'hover': {'backgroundColor': '#e5e7eb', 'transform': 'scale(1.1)'}
                        })
                    ], style={'position': 'relative', 'borderBottom': '1px solid #dee2e6', 'paddingBottom': '15px',
                              'marginBottom': '20px'}),
                    
                    # Tabs for modal content
                    dcc.Tabs(
                        id="modal-tabs",
                        value="select-run",
                        children=[
                            dcc.Tab(
                                label="Select Bioreactor Run",
                                value="select-run",
                                style={'fontFamily': MODERN_STYLE['font_family']},
                                children=[
                                    html.Div([
                                        # Runs table container
                                        html.Div(id="runs-table-container", children=[
                                            html.P("Loading available runs...", style={'textAlign': 'center', 'color': COLOR_PALETTE['secondary']})
                                        ], style={
                                            'width': '100%',
                                            'margin': 'auto',
                                            'padding': '20px',
                                            'border': 'none',
                                            'borderRadius': '16px',
                                            'backgroundColor': '#ffffff',
                                            'marginBottom': '20px',
                                            'marginTop': '20px',
                                            'display': 'block',
                                            'boxShadow': '0 2px 4px rgba(0,0,0,0.05)',
                                            'transition': 'all 0.2s ease'
                                        }),
                                        
                                        # Status area
                                        html.Div(id="run-status", style={
                                            "textAlign": "center",
                                            "color": "green",
                                            "fontWeight": "bold",
                                            "fontSize": "16px",
                                            "marginBottom": "10px"
                                        }),
                                        
                                        # Action buttons
                                        html.Div([
                                            html.Button("Cancel", id="cancel-run-btn", style={
                                                'backgroundColor': '#6b7280',
                                                'color': 'white',
                                                'padding': '12px 20px',
                                                'border': 'none',
                                                'borderRadius': '10px',
                                                'cursor': 'pointer',
                                                'fontSize': '14px',
                                                'fontWeight': '600',
                                                'marginRight': '12px',
                                                'transition': 'all 0.2s ease',
                                                'boxShadow': '0 2px 4px rgba(107, 114, 128, 0.2)'
                                            }),
                                            html.Button("Confirm Selection", id="confirm-run-selection", style={
                                                'backgroundColor': '#2563eb',
                                                'color': 'white',
                                                'padding': '12px 24px',
                                                'border': 'none',
                                                'borderRadius': '10px',
                                                'cursor': 'pointer',
                                                'fontSize': '14px',
                                                'fontWeight': '600',
                                                'transition': 'all 0.2s ease',
                                                'boxShadow': '0 4px 12px rgba(37, 99, 235, 0.25)'
                                            })
                                        ], style={'display': 'flex', 'justifyContent': 'flex-end', 'gap': '12px', 'marginTop': '16px'})
                                    ])
                                ]
                            ),
                            dcc.Tab(
                                label="Import Process Data",
                                value="import-data",
                                style={'fontFamily': MODERN_STYLE['font_family']},
                                children=[
                                    html.Div([
                                        html.Iframe(
                                            id="import-iframe",
                                            src="/plotly_integration/dash-app/app/dasgip_import",
                                            style={
                                                'width': '100%',
                                                'height': '600px',
                                                'border': 'none',
                                                'borderRadius': '8px',
                                                'marginTop': '20px',
                                                'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
                                            }
                                        )
                                    ])
                                ]
                            )
                        ],
                        style={
                            'fontFamily': MODERN_STYLE['font_family'],
                            'fontSize': '14px'
                        },
                        colors={
                            'border': COLOR_PALETTE['accent'],
                            'primary': COLOR_PALETTE['accent'],
                            'background': COLOR_PALETTE['background']
                        }
                    )
                ]
            )
        ]
    ),

    # Main content area with card styling
    html.Div([
        html.Div(id="main-content", style={
            'backgroundColor': 'white',
            'borderRadius': MODERN_STYLE['border_radius'],
            'boxShadow': MODERN_STYLE['card_shadow'],
            'padding': '20px',
            'minHeight': '600px'
        })
    ], style={'margin': '20px'}),

    # Hidden divs to store state
    dcc.Store(id='selected-run-store', data=None),
    dcc.Store(id='runs-data-store', data=[])
], style={
    'backgroundColor': COLOR_PALETTE['background'],
    'minHeight': '100vh',
    'fontFamily': MODERN_STYLE['font_family']
})

# Callback to handle modal open/close following SEC app pattern
@app.callback(
    Output("run-modal", "style"),
    [Input("select-run-btn", "n_clicks"),
     Input("close-run-modal-btn", "n_clicks"),
     Input("cancel-run-btn", "n_clicks"),
     Input("confirm-run-selection", "n_clicks")],
    [State("run-modal", "style"),
     State("selected-run-store", "data")],
    prevent_initial_call=True
)
def toggle_run_modal(open_clicks, close_clicks, cancel_clicks, confirm_clicks, current_style, selected_run):
    # Get all click counts (they may be None initially)
    open_clicks = open_clicks or 0
    close_clicks = close_clicks or 0
    cancel_clicks = cancel_clicks or 0
    confirm_clicks = confirm_clicks or 0
    
    # Initialize style if None
    if not current_style:
        current_style = {
            'display': 'none',
            'position': 'fixed',
            'zIndex': '1000',
            'left': '0',
            'top': '0',
            'width': '100%',
            'height': '100%',
            'backgroundColor': 'rgba(0,0,0,0.6)',
            'backdropFilter': 'blur(4px)',
            'overflow': 'auto',
            'animation': 'fadeIn 0.3s ease-out'
        }
    
    # Calculate total close clicks
    total_close_clicks = close_clicks + cancel_clicks + confirm_clicks
    
    # If open clicks is greater than close clicks, show modal
    if open_clicks > total_close_clicks:
        new_style = current_style.copy()
        new_style['display'] = 'block'
        return new_style
    else:
        new_style = current_style.copy() 
        new_style['display'] = 'none'
        return new_style

# Callback to load runs data when modal opens
@app.callback(
    [Output('runs-table-container', 'children'),
     Output('runs-data-store', 'data')],
    Input('run-modal', 'style'),
    prevent_initial_call=True
)
def load_runs_table(modal_style):
    # Only populate if modal is visible
    if modal_style and modal_style.get("display") == "block":
        runs_data = load_bioreactor_runs()
        
        if runs_data:
            # Format the data for display
            table_data = []
            for run in runs_data:
                table_data.append({
                    'UP Number': run['up_number'],
                    'Project': run['project_name'] or 'N/A',
                    'Unit': f"Unit {run['unit_number']}",
                    'Setup': run['setup_name'] or 'N/A',
                    'Start Time': run['start_timestamp'].strftime('%Y-%m-%d %H:%M') if run['start_timestamp'] else 'N/A',
                    'Duration (h)': f"{((run['stop_timestamp'] - run['start_timestamp']).total_seconds() / 3600):.1f}" if run['start_timestamp'] and run['stop_timestamp'] else 'N/A',
                    'Comment': run['comment'][:50] + '...' if run['comment'] and len(run['comment']) > 50 else (run['comment'] or '')
                })
            
            table = [
                html.H4("Select a Run", style={'textAlign': 'center', 'color': '#0056b3'}),
                dash_table.DataTable(
                    id='runs-selection-table',
                    columns=[
                        {'name': 'UP Number', 'id': 'UP Number', 'type': 'text'},
                        {'name': 'Project', 'id': 'Project', 'type': 'text'},
                        {'name': 'Unit', 'id': 'Unit', 'type': 'text'},
                        {'name': 'Setup', 'id': 'Setup', 'type': 'text'},
                        {'name': 'Start Time', 'id': 'Start Time', 'type': 'text'},
                        {'name': 'Duration (h)', 'id': 'Duration (h)', 'type': 'numeric'},
                        {'name': 'Comment', 'id': 'Comment', 'type': 'text'}
                    ],
                    data=table_data,
                    page_size=10,
                    sort_action="native",
                    filter_action="native", 
                    row_selectable='single',
                    selected_rows=[],
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'center',
                        'padding': '12px 16px',
                        'fontFamily': 'system-ui, -apple-system, sans-serif',
                        'fontSize': '14px',
                        'border': '1px solid #e5e7eb',
                        'borderCollapse': 'collapse'
                    },
                    style_header={
                        'backgroundColor': '#f8fafc',
                        'fontWeight': '700',
                        'border': '1px solid #d1d5db',
                        'color': '#374151',
                        'textTransform': 'uppercase',
                        'fontSize': '12px',
                        'letterSpacing': '0.5px'
                    },
                    style_data={
                        'backgroundColor': 'white',
                        'color': '#374151',
                        'border': '1px solid #e5e7eb'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': '#fafbfc'
                        },
                        {
                            "if": {"state": "active"},
                            "backgroundColor": "#eff6ff",
                            "border": "1px solid #3b82f6",
                            "borderRadius": "8px",
                            "boxShadow": "0 0 0 3px rgba(59, 130, 246, 0.1)"
                        },
                        {
                            "if": {"state": "selected"},
                            "backgroundColor": "#dbeafe",
                            "fontWeight": "600",
                            "color": "#1e40af",
                            "borderRadius": "8px"
                        }
                    ]
                )
            ]
            
            return table, runs_data
        else:
            return html.P("No runs available in database.", 
                         style={'textAlign': 'center', 'color': COLOR_PALETTE['secondary']}), []
    
    return html.P("Loading...", style={'textAlign': 'center'}), []

# Callback to load selected run data
@app.callback(
    Output('selected-run-store', 'data'),
    Input('confirm-run-selection', 'n_clicks'),
    [State('runs-selection-table', 'selected_rows'),
     State('runs-data-store', 'data')],
    prevent_initial_call=True
)
def load_selected_run_data(n_clicks, selected_rows, runs_data):
    if n_clicks and selected_rows and runs_data:
        selected_run_data = runs_data[selected_rows[0]]
        up_number = selected_run_data['up_number']
        return up_number
    
    return no_update

# Callback to update current run text when a run is selected
@app.callback(
    Output('current-run-text', 'children'),
    Input('selected-run-store', 'data'),
    prevent_initial_call=True
)
def update_current_run_text(selected_run):
    if selected_run:
        return f"Run: {selected_run}"
    return "No run selected"

# Callbacks
@app.callback(
    Output('main-content', 'children'),
    [Input('main-tabs', 'value'),
     Input('selected-run-store', 'data')]
)
def update_main_content(tab_value, selected_run_up):
    # Load data for selected run
    current_data = pd.DataFrame()
    if selected_run_up:
        current_data = load_timeseries_data(selected_run_up)

    if tab_value == "overview":
        return dcc.Graph(
            figure=create_overview_dashboard(current_data),
            style={'height': '900px'}
        )

    elif tab_value == "parameters":
        # Enhanced parameter selection interface
        return html.Div([
            html.Div([
                html.H3("📈 Individual Parameter Analysis",
                       style={'color': COLOR_PALETTE['text'], 'fontFamily': MODERN_STYLE['font_family'], 'marginBottom': '20px'}),
                html.P("Select a process parameter to view detailed time-series analysis with process value, setpoint, and controller output.",
                       style={'color': COLOR_PALETTE['secondary'], 'fontFamily': MODERN_STYLE['font_family'], 'marginBottom': '20px'})
            ]),

            html.Div([
                html.Label("Select Parameter:",
                          style={'marginBottom': '10px', 'fontWeight': 'bold', 'fontSize': '16px', 'color': COLOR_PALETTE['text'], 'fontFamily': MODERN_STYLE['font_family']}),
                dcc.Dropdown(
                    id='parameter-dropdown',
                    options=[
                        {'label': f"🔬 {config['label']} ({config['unit']})", 'value': key}
                        for key, config in PROCESS_PARAMETERS.items()
                    ],
                    value='do',
                    style={'marginBottom': '30px', 'fontFamily': MODERN_STYLE['font_family']},
                    placeholder="Choose a process parameter..."
                )
            ], style={
                'backgroundColor': COLOR_PALETTE['background'],
                'padding': '20px',
                'borderRadius': MODERN_STYLE['border_radius'],
                'marginBottom': '20px'
            }),

            dcc.Graph(id='parameter-plot', style={'borderRadius': MODERN_STYLE['border_radius']})
        ])

    elif tab_value == "control":
        # Calculate control performance statistics
        performance_stats = calculate_control_performance(current_data)
        
        if not performance_stats:
            return html.Div([
                html.Div([
                    html.H3("🎯 Control Performance Analysis",
                           style={'color': COLOR_PALETTE['text'], 'fontFamily': MODERN_STYLE['font_family'], 'marginBottom': '20px'}),
                    html.P("Select a bioreactor run to view control performance metrics.",
                           style={'color': COLOR_PALETTE['secondary'], 'fontFamily': MODERN_STYLE['font_family'], 'textAlign': 'center', 'fontSize': '18px'})
                ], style={
                    'backgroundColor': COLOR_PALETTE['background'],
                    'padding': '40px',
                    'borderRadius': MODERN_STYLE['border_radius'],
                    'textAlign': 'center',
                    'maxWidth': '600px',
                    'margin': '50px auto'
                })
            ])
        
        # Create performance cards for each parameter
        performance_cards = []
        
        for param_key, stats in performance_stats.items():
            # Color coding based on tracking accuracy
            if stats['tracking_accuracy'] >= 90:
                card_color = COLOR_PALETTE['success']
                grade = "A"
            elif stats['tracking_accuracy'] >= 75:
                card_color = COLOR_PALETTE['process_value']
                grade = "B"
            elif stats['tracking_accuracy'] >= 60:
                card_color = COLOR_PALETTE['warning']
                grade = "C"
            else:
                card_color = COLOR_PALETTE['danger']
                grade = "D"
            
            card = html.Div([
                # Header with parameter name and grade
                html.Div([
                    html.H4(f"🔬 {stats['name']}", style={
                        'color': 'white', 
                        'margin': '0', 
                        'fontSize': '1.2rem',
                        'fontWeight': 'bold'
                    }),
                    html.Div(f"Grade: {grade}", style={
                        'backgroundColor': 'rgba(255,255,255,0.2)',
                        'color': 'white',
                        'padding': '4px 12px',
                        'borderRadius': '12px',
                        'fontSize': '0.9rem',
                        'fontWeight': 'bold'
                    })
                ], style={
                    'backgroundColor': card_color,
                    'padding': '15px 20px',
                    'borderRadius': '12px 12px 0 0',
                    'display': 'flex',
                    'justifyContent': 'space-between',
                    'alignItems': 'center'
                }),
                
                # Stats content
                html.Div([
                    html.Div([
                        html.Div([
                            html.Span("📊 Tracking Accuracy", style={'fontWeight': 'bold', 'color': COLOR_PALETTE['text']}),
                            html.Br(),
                            html.Span(f"{stats['tracking_accuracy']}%", style={'fontSize': '1.5rem', 'fontWeight': 'bold', 'color': card_color})
                        ], style={'textAlign': 'center', 'marginBottom': '15px'}),
                        
                        html.Div([
                            html.Div([
                                html.Span("📉 Mean Abs. Error", style={'fontSize': '0.85rem', 'color': COLOR_PALETTE['secondary']}),
                                html.Br(),
                                html.Span(f"{stats['mae']} {stats['unit']}", style={'fontWeight': 'bold'})
                            ], style={'textAlign': 'center'}, className='col-6'),
                            
                            html.Div([
                                html.Span("📈 RMSE", style={'fontSize': '0.85rem', 'color': COLOR_PALETTE['secondary']}),
                                html.Br(), 
                                html.Span(f"{stats['rmse']} {stats['unit']}", style={'fontWeight': 'bold'})
                            ], style={'textAlign': 'center'}, className='col-6')
                        ], className='row', style={'marginBottom': '15px'}),
                        
                        html.Div([
                            html.Div([
                                html.Span("⚡ Avg Response Time", style={'fontSize': '0.85rem', 'color': COLOR_PALETTE['secondary']}),
                                html.Br(),
                                html.Span(f"{stats['avg_response_time']} min" if stats['avg_response_time'] != 'N/A' else 'N/A', style={'fontWeight': 'bold'})
                            ], style={'textAlign': 'center'}, className='col-6'),
                            
                            html.Div([
                                html.Span("📊 Process Variability", style={'fontSize': '0.85rem', 'color': COLOR_PALETTE['secondary']}),
                                html.Br(),
                                html.Span(f"{stats['process_variability']}% CV", style={'fontWeight': 'bold'})
                            ], style={'textAlign': 'center'}, className='col-6')
                        ], className='row', style={'marginBottom': '10px'}),
                        
                        html.Div([
                            html.Span(f"📍 {stats['data_points']:,} data points analyzed", 
                                     style={'fontSize': '0.8rem', 'color': COLOR_PALETTE['secondary'], 'textAlign': 'center'})
                        ], style={'textAlign': 'center'})
                        
                    ], style={'padding': '20px'})
                ])
            ], style={
                'backgroundColor': 'white',
                'borderRadius': MODERN_STYLE['border_radius'],
                'boxShadow': MODERN_STYLE['card_shadow'],
                'margin': '10px',
                'overflow': 'hidden'
            })
            
            performance_cards.append(card)
        
        return html.Div([
            html.Div([
                html.H3("🎯 Control Performance Analysis",
                       style={'color': COLOR_PALETTE['text'], 'fontFamily': MODERN_STYLE['font_family'], 'marginBottom': '10px', 'textAlign': 'center'}),
                html.P("Statistical analysis of control loop performance and setpoint tracking accuracy",
                       style={'color': COLOR_PALETTE['secondary'], 'fontFamily': MODERN_STYLE['font_family'], 'marginBottom': '30px', 'textAlign': 'center'})
            ]),
            
            # Performance metrics cards
            html.Div(performance_cards, className='row'),
            
            # Summary insights
            html.Div([
                html.H4("📈 Performance Insights", style={'color': COLOR_PALETTE['text'], 'marginBottom': '15px'}),
                html.Div([
                    html.P("• Tracking accuracy shows percentage of time the process variable stayed within ±5% of setpoint", style={'marginBottom': '8px'}),
                    html.P("• Response time measures average time to reach 90% of setpoint change", style={'marginBottom': '8px'}), 
                    html.P("• Process variability (CV) indicates consistency - lower values show better control", style={'marginBottom': '8px'}),
                    html.P("• Grades: A (≥90%), B (75-89%), C (60-74%), D (<60%) tracking accuracy", style={'marginBottom': '0px'})
                ], style={'color': COLOR_PALETTE['text'], 'fontSize': '0.9rem', 'lineHeight': '1.5'})
            ], style={
                'backgroundColor': COLOR_PALETTE['background'],
                'padding': '20px',
                'borderRadius': MODERN_STYLE['border_radius'],
                'margin': '30px 0'
            })
        ])

@app.callback(
    Output('parameter-plot', 'figure'),
    [Input('parameter-dropdown', 'value'),
     Input('selected-run-store', 'data')]
)
def update_parameter_plot(selected_parameter, selected_run_up):
    # Load data for selected run
    current_data = pd.DataFrame()
    if selected_run_up:
        current_data = load_timeseries_data(selected_run_up)

    if selected_parameter and not current_data.empty:
        return create_process_plot(current_data, selected_parameter, height=600)
    else:
        fig = go.Figure()
        message = "Select a parameter to view" if selected_run_up else "Select a run first, then choose a parameter"
        fig.add_annotation(
            text=message,
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(height=600)
        return fig

