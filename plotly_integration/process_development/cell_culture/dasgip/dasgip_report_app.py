import dash
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State, callback_context
from django_plotly_dash import DjangoDash
import pandas as pd
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import os

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

# Define the process parameters and their corresponding labels
PROCESS_PARAMETERS = {
    "do": {"label": "Dissolved Oxygen", "unit": "% DO", "cols": ["Unit 1.DO1.PV", "Unit 1.DO1.SP", "Unit 1.DO1.Out"]},
    "ph": {"label": "pH", "unit": "pH", "cols": ["Unit 1.pH1.PV", "Unit 1.pH1.SP", "Unit 1.pH1.Out"]},
    "temp": {"label": "Temperature", "unit": "°C", "cols": ["Unit 1.T1.PV", "Unit 1.T1.SP", "Unit 1.T1.Out"]},
    "rpm": {"label": "Agitation Speed", "unit": "RPM", "cols": ["Unit 1.N1.PV", "Unit 1.N1.SP"]},
    "volume": {"label": "Reactor Volume", "unit": "mL", "cols": ["Unit 1.V1.VPV"]},
    "air_flow": {"label": "Air Flow", "unit": "sL/h", "cols": ["Unit 1.FAir1.PV", "Unit 1.FAir1.SP"]},
    "feed_a": {"label": "Feed A Flow", "unit": "mL/h", "cols": ["Unit 1.FA1.PV", "Unit 1.FA1.SP"]},
    "feed_b": {"label": "Feed B Flow", "unit": "mL/h", "cols": ["Unit 1.FB1.PV", "Unit 1.FB1.SP"]},
    "o2_conc": {"label": "O2 Concentration", "unit": "%", "cols": ["Unit 1.XO21.PV", "Unit 1.XO21.SP"]},
    "co2_conc": {"label": "CO2 Concentration", "unit": "%", "cols": ["Unit 1.XCO21.PV", "Unit 1.XCO21.SP"]}
}

def load_dasgip_data():
    """Load DASGIP data from the clean CSV file"""
    try:
        # Path to the clean data file
        data_file = os.path.join(
            os.path.dirname(__file__), 
            "CTPCNK808814_E59BRX_Control_clean.csv"
        )
        
        if os.path.exists(data_file):
            df = pd.read_csv(data_file)
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            
            # Calculate process hours from start
            start_time = df['Timestamp'].min()
            df['Process_Hours'] = (df['Timestamp'] - start_time).dt.total_seconds() / 3600
            
            return df
        else:
            # Return empty dataframe if file doesn't exist
            return pd.DataFrame()
    except Exception as e:
        print(f"Error loading DASGIP data: {e}")
        return pd.DataFrame()

# Load data once when app starts
dasgip_data = load_dasgip_data()

def detect_process_events(df, parameter_key):
    """Detect significant process events for annotation"""
    events = []
    if df.empty:
        return events
    
    param_config = PROCESS_PARAMETERS[parameter_key]
    pv_col = None
    sp_col = None
    
    # Find PV and SP columns
    for col in param_config["cols"]:
        if col in df.columns:
            if '.PV' in col:
                pv_col = col
            elif '.SP' in col:
                sp_col = col
    
    if sp_col and sp_col in df.columns:
        # Detect setpoint changes
        sp_data = df[df[sp_col].notna()].copy()
        if len(sp_data) > 1:
            sp_diff = sp_data[sp_col].diff().abs()
            significant_changes = sp_diff > sp_diff.std() * 2
            
            for idx in sp_data[significant_changes].index:
                events.append({
                    'time': df.loc[idx, 'Process_Hours'],
                    'value': df.loc[idx, sp_col],
                    'type': 'setpoint_change',
                    'text': f"SP Change: {df.loc[idx, sp_col]:.2f}"
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
            text="No data available",
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(height=height)
        return fig
    
    param_config = PROCESS_PARAMETERS[parameter_key]
    available_cols = [col for col in param_config["cols"] if col in df.columns]
    
    if not available_cols:
        fig = go.Figure()
        # More detailed error message for debugging
        missing_cols = [col for col in param_config["cols"] if col not in df.columns]
        available_in_df = [col for col in df.columns if any(param_col.split('.')[-2] in col for param_col in param_config["cols"])]
        
        error_text = f"No {param_config['label']} data available<br>"
        error_text += f"Looking for: {', '.join(param_config['cols'])}<br>"
        if available_in_df:
            error_text += f"Similar columns found: {', '.join(available_in_df[:3])}"
        
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
    has_output = any('.Out' in col for col in available_cols)
    fig = make_subplots(specs=[[{"secondary_y": has_output}]])
    
    # Enhanced color mapping using our palette
    colors = {
        "PV": COLOR_PALETTE["process_value"], 
        "SP": COLOR_PALETTE["setpoint"], 
        "Out": COLOR_PALETTE["output"]
    }
    
    traces_added = 0
    for col in available_cols:
        data_subset = df[df[col].notna()]
        if len(data_subset) == 0:
            print(f"Skipping {col}: no valid data points")
            continue
            
        # Downsample data for better performance
        data_subset = downsample_data(data_subset, max_points=2000)
            
        # Determine trace type and color - improved logic
        if '.PV' in col or '.VPV' in col:  # Handle both PV and VPV (volume)
            trace_name = "Process Value"
            color = colors["PV"]
            secondary_y = False
            line_style = dict(color=color, width=2)
        elif '.SP' in col:
            trace_name = "Setpoint"
            color = colors["SP"]
            secondary_y = False
            line_style = dict(color=color, dash='dash', width=2)
        elif '.Out' in col:
            trace_name = "Controller Output"
            color = colors["Out"]
            secondary_y = True
            line_style = dict(color=color, width=2)
        else:
            # Fallback for any other column types
            trace_name = col.replace('Unit 1.', '').replace('1', '')
            color = colors["PV"]
            secondary_y = False
            line_style = dict(color=color, width=2)
        
        fig.add_trace(
            go.Scatter(
                x=data_subset['Process_Hours'],
                y=data_subset[col],
                name=trace_name,
                line=line_style,
                hovertemplate=f"<b>{trace_name}</b><br>" +
                             "Time: %{x:.1f} hours<br>" +
                             f"Value: %{{y:.2f}} {param_config['unit']}<br>" +
                             "Timestamp: %{customdata}<br>" +
                             "<extra></extra>",
                customdata=data_subset['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S'),
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
        title_font={'size': 14, 'family': MODERN_STYLE['font_family'], 'color': colors['PV']},
        gridcolor='rgba(0,0,0,0.1)',
        showgrid=True,
        zeroline=False
    )
    if has_output:
        fig.update_yaxes(
            title_text="Controller Output (%)", 
            secondary_y=True,
            title_font={'size': 14, 'family': MODERN_STYLE['font_family'], 'color': colors['Out']},
            gridcolor='rgba(0,0,0,0.05)',
            showgrid=True,
            zeroline=False
        )
    
    # Add debugging info if no traces were added
    if traces_added == 0:
        print(f"Warning: No traces added for parameter {parameter_key}")
        print(f"Available columns: {available_cols}")
    
    return fig

def create_overview_dashboard(df):
    """Create the main overview dashboard with multiple subplots"""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available - Please check data file",
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
    do_cols = ['Unit 1.DO1.PV', 'Unit 1.DO1.SP', 'Unit 1.DO1.Out']
    for col in do_cols:
        if col in df.columns:
            data_subset = df[df[col].notna()]
            if len(data_subset) > 0:
                # Downsample for overview performance
                data_subset = downsample_data(data_subset, max_points=1000)
                trace_type = 'PV' if 'PV' in col else 'SP' if 'SP' in col else 'Out'
                color = overview_colors['do'][trace_type]
                line_style = dict(color=color, width=2) if trace_type != 'SP' else dict(color=color, dash='dash', width=2)
                secondary_y = 'Out' in col
                
                fig.add_trace(
                    go.Scatter(
                        x=data_subset['Process_Hours'], 
                        y=data_subset[col],
                        name=col.replace('Unit 1.DO1.', 'DO '), 
                        line=line_style,
                        hovertemplate=f"<b>DO {trace_type}</b><br>Time: %{{x:.1f}}h<br>Value: %{{y:.2f}}<extra></extra>"
                    ),
                    row=1, col=1, secondary_y=secondary_y
                )
    
    # 2. pH Control (row=1, col=2)
    ph_cols = ['Unit 1.pH1.PV', 'Unit 1.pH1.SP', 'Unit 1.pH1.Out']
    for col in ph_cols:
        if col in df.columns:
            data_subset = df[df[col].notna()]
            if len(data_subset) > 0:
                data_subset = downsample_data(data_subset, max_points=1000)
                trace_type = 'PV' if 'PV' in col else 'SP' if 'SP' in col else 'Out'
                color = overview_colors['ph'][trace_type]
                line_style = dict(color=color, width=2) if trace_type != 'SP' else dict(color=color, dash='dash', width=2)
                secondary_y = 'Out' in col
                
                fig.add_trace(
                    go.Scatter(
                        x=data_subset['Process_Hours'], 
                        y=data_subset[col],
                        name=col.replace('Unit 1.pH1.', 'pH '), 
                        line=line_style,
                        hovertemplate=f"<b>pH {trace_type}</b><br>Time: %{{x:.1f}}h<br>Value: %{{y:.2f}}<extra></extra>"
                    ),
                    row=1, col=2, secondary_y=secondary_y
                )
    
    # 3. Temperature Control (row=2, col=1)
    temp_cols = ['Unit 1.T1.PV', 'Unit 1.T1.SP', 'Unit 1.T1.Out']
    for col in temp_cols:
        if col in df.columns:
            data_subset = df[df[col].notna()]
            if len(data_subset) > 0:
                data_subset = downsample_data(data_subset, max_points=1000)
                color = 'red' if 'PV' in col else 'darkred' if 'SP' in col else 'orange'
                line_style = dict(color=color) if 'PV' in col or 'Out' in col else dict(color=color, dash='dash')
                secondary_y = 'Out' in col
                
                fig.add_trace(
                    go.Scatter(x=data_subset['Process_Hours'], y=data_subset[col],
                              name=col.replace('Unit 1.T1.', 'Temp '), line=line_style),
                    row=2, col=1, secondary_y=secondary_y
                )
    
    # 4. Agitation Speed (row=2, col=2)
    rpm_cols = ['Unit 1.N1.PV', 'Unit 1.N1.SP']
    for col in rpm_cols:
        if col in df.columns:
            data_subset = df[df[col].notna()]
            if len(data_subset) > 0:
                data_subset = downsample_data(data_subset, max_points=1000)
                color = 'brown' if 'PV' in col else 'red'
                line_style = dict(color=color) if 'PV' in col else dict(color=color, dash='dash')
                
                fig.add_trace(
                    go.Scatter(x=data_subset['Process_Hours'], y=data_subset[col],
                              name=col.replace('Unit 1.N1.', 'RPM '), line=line_style),
                    row=2, col=2
                )
    
    # 5. Volume and Air Flow (row=3, col=1)
    if 'Unit 1.V1.VPV' in df.columns:
        vol_data = df[df['Unit 1.V1.VPV'].notna()]
        if len(vol_data) > 0:
            vol_data = downsample_data(vol_data, max_points=1000)
            fig.add_trace(
                go.Scatter(x=vol_data['Process_Hours'], y=vol_data['Unit 1.V1.VPV'],
                          name='Volume', line=dict(color='navy')),
                row=3, col=1
            )
    
    if 'Unit 1.FAir1.PV' in df.columns:
        air_data = df[df['Unit 1.FAir1.PV'].notna()]
        if len(air_data) > 0:
            air_data = downsample_data(air_data, max_points=1000)
            fig.add_trace(
                go.Scatter(x=air_data['Process_Hours'], y=air_data['Unit 1.FAir1.PV'],
                          name='Air Flow', line=dict(color='cyan')),
                row=3, col=1, secondary_y=True
            )
    
    # 6. Gas Concentrations (row=3, col=2)
    if 'Unit 1.XO21.PV' in df.columns:
        o2_data = df[df['Unit 1.XO21.PV'].notna()]
        if len(o2_data) > 0:
            o2_data = downsample_data(o2_data, max_points=1000)
            fig.add_trace(
                go.Scatter(x=o2_data['Process_Hours'], y=o2_data['Unit 1.XO21.PV'],
                          name='O2 %', line=dict(color='lightblue')),
                row=3, col=2
            )
    
    if 'Unit 1.XCO21.PV' in df.columns:
        co2_data = df[df['Unit 1.XCO21.PV'].notna()]
        if len(co2_data) > 0:
            co2_data = downsample_data(co2_data, max_points=1000)
            fig.add_trace(
                go.Scatter(x=co2_data['Process_Hours'], y=co2_data['Unit 1.XCO21.PV'],
                          name='CO2 %', line=dict(color='gray')),
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

# App layout with enhanced styling
app.layout = html.Div([
    # Header section with modern card styling
    html.Div([
        html.Div([
            html.H1("🧬 DASGIP Bioreactor Data Analysis", 
                    style={
                        'textAlign': 'center', 
                        'color': COLOR_PALETTE['text'], 
                        'marginBottom': '5px',
                        'fontFamily': MODERN_STYLE['font_family'],
                        'fontSize': '1.8rem',
                        'fontWeight': '400'
                    }),
            html.P("Advanced bioprocess monitoring and control analytics", 
                   style={
                       'textAlign': 'center', 
                       'color': COLOR_PALETTE['secondary'], 
                       'marginBottom': '0px',
                       'fontFamily': MODERN_STYLE['font_family'],
                       'fontSize': '0.9rem'
                   })
        ], style={
            'backgroundColor': 'white',
            'padding': '15px',
            'borderRadius': MODERN_STYLE['border_radius'],
            'boxShadow': MODERN_STYLE['card_shadow'],
            'margin': '10px'
        })
    ]),
    
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
    
    # Main content area with card styling
    html.Div([
        html.Div(id="main-content", style={
            'backgroundColor': 'white',
            'borderRadius': MODERN_STYLE['border_radius'],
            'boxShadow': MODERN_STYLE['card_shadow'],
            'padding': '20px',
            'minHeight': '600px'
        })
    ], style={'margin': '20px'})
], style={
    'backgroundColor': COLOR_PALETTE['background'],
    'minHeight': '100vh',
    'fontFamily': MODERN_STYLE['font_family']
})

# Callbacks
@app.callback(
    Output('main-content', 'children'),
    Input('main-tabs', 'value')
)
def update_main_content(tab_value):
    if tab_value == "overview":
        return dcc.Graph(
            figure=create_overview_dashboard(dasgip_data),
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
        return html.Div([
            html.Div([
                html.H3("🎯 Control Performance Analysis", 
                       style={'color': COLOR_PALETTE['text'], 'fontFamily': MODERN_STYLE['font_family'], 'marginBottom': '20px'}),
                html.P("Advanced control loop performance metrics and statistical analysis.",
                       style={'color': COLOR_PALETTE['secondary'], 'fontFamily': MODERN_STYLE['font_family'], 'marginBottom': '30px'})
            ]),
            
            html.Div([
                html.Div([
                    html.H4("🚧 Coming Soon", style={'color': COLOR_PALETTE['warning'], 'textAlign': 'center', 'marginBottom': '20px'}),
                    html.P("Control loop performance metrics including:", style={'marginBottom': '15px', 'fontWeight': 'bold'}),
                    html.Ul([
                        html.Li("📊 Setpoint tracking accuracy"),
                        html.Li("⚡ Response time analysis"),
                        html.Li("📈 Overshoot and settling time"),
                        html.Li("🎯 Control stability metrics"),
                        html.Li("📉 Disturbance rejection performance")
                    ], style={'color': COLOR_PALETTE['text'], 'lineHeight': '1.8'})
                ], style={
                    'backgroundColor': COLOR_PALETTE['background'],
                    'padding': '40px',
                    'borderRadius': MODERN_STYLE['border_radius'],
                    'textAlign': 'center',
                    'maxWidth': '600px',
                    'margin': '0 auto'
                })
            ], style={'marginTop': '50px'})
        ])

@app.callback(
    Output('parameter-plot', 'figure'),
    Input('parameter-dropdown', 'value')
)
def update_parameter_plot(selected_parameter):
    if selected_parameter and not dasgip_data.empty:
        return create_process_plot(dasgip_data, selected_parameter, height=600)
    else:
        fig = go.Figure()
        fig.add_annotation(
            text="Select a parameter to view",
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(height=600)
        return fig

if __name__ == '__main__':
    app.run_server(debug=True)