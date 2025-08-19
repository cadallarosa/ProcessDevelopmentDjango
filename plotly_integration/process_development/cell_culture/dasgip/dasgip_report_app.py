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
        fig.add_annotation(
            text=f"No {param_config['label']} data available",
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=14, color="gray")
        )
        fig.update_layout(height=height)
        return fig
    
    # Create subplot with secondary y-axis if we have output values
    has_output = any('.Out' in col for col in available_cols)
    fig = make_subplots(specs=[[{"secondary_y": has_output}]])
    
    # Color mapping
    colors = {"PV": "blue", "SP": "red", "Out": "orange"}
    
    for col in available_cols:
        data_subset = df[df[col].notna()]
        if len(data_subset) == 0:
            continue
            
        # Determine trace type and color
        if '.PV' in col:
            trace_name = "Process Value"
            color = colors["PV"]
            secondary_y = False
            line_style = dict(color=color)
        elif '.SP' in col:
            trace_name = "Setpoint"
            color = colors["SP"]
            secondary_y = False
            line_style = dict(color=color, dash='dash')
        elif '.Out' in col:
            trace_name = "Controller Output"
            color = colors["Out"]
            secondary_y = True
            line_style = dict(color=color)
        else:
            trace_name = col.replace('Unit 1.', '').replace('1', '')
            color = colors["PV"]
            secondary_y = False
            line_style = dict(color=color)
        
        fig.add_trace(
            go.Scatter(
                x=data_subset['Process_Hours'],
                y=data_subset[col],
                name=trace_name,
                line=line_style,
                hovertemplate=f"<b>{trace_name}</b><br>" +
                             "Time: %{x:.1f} hours<br>" +
                             f"Value: %{{y:.2f}} {param_config['unit']}<br>" +
                             "<extra></extra>"
            ),
            secondary_y=secondary_y
        )
    
    # Update layout
    fig.update_layout(
        title=f"{param_config['label']} Over Time",
        height=height,
        template='plotly_white',
        hovermode='x unified'
    )
    
    # Update x-axis
    fig.update_xaxes(title_text="Process Time (hours)")
    
    # Update y-axes
    fig.update_yaxes(title_text=f"{param_config['label']} ({param_config['unit']})", secondary_y=False)
    if has_output:
        fig.update_yaxes(title_text="Controller Output (%)", secondary_y=True)
    
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
    
    # Create subplots - 3 rows, 2 columns
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
        vertical_spacing=0.12
    )
    
    # 1. DO Control (row=1, col=1)
    do_cols = ['Unit 1.DO1.PV', 'Unit 1.DO1.SP', 'Unit 1.DO1.Out']
    for col in do_cols:
        if col in df.columns:
            data_subset = df[df[col].notna()]
            if len(data_subset) > 0:
                color = 'blue' if 'PV' in col else 'red' if 'SP' in col else 'orange'
                line_style = dict(color=color) if 'PV' in col or 'Out' in col else dict(color=color, dash='dash')
                secondary_y = 'Out' in col
                
                fig.add_trace(
                    go.Scatter(x=data_subset['Process_Hours'], y=data_subset[col],
                              name=col.replace('Unit 1.DO1.', 'DO '), line=line_style),
                    row=1, col=1, secondary_y=secondary_y
                )
    
    # 2. pH Control (row=1, col=2)
    ph_cols = ['Unit 1.pH1.PV', 'Unit 1.pH1.SP', 'Unit 1.pH1.Out']
    for col in ph_cols:
        if col in df.columns:
            data_subset = df[df[col].notna()]
            if len(data_subset) > 0:
                color = 'green' if 'PV' in col else 'red' if 'SP' in col else 'purple'
                line_style = dict(color=color) if 'PV' in col or 'Out' in col else dict(color=color, dash='dash')
                secondary_y = 'Out' in col
                
                fig.add_trace(
                    go.Scatter(x=data_subset['Process_Hours'], y=data_subset[col],
                              name=col.replace('Unit 1.pH1.', 'pH '), line=line_style),
                    row=1, col=2, secondary_y=secondary_y
                )
    
    # 3. Temperature Control (row=2, col=1)
    temp_cols = ['Unit 1.T1.PV', 'Unit 1.T1.SP', 'Unit 1.T1.Out']
    for col in temp_cols:
        if col in df.columns:
            data_subset = df[df[col].notna()]
            if len(data_subset) > 0:
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
            fig.add_trace(
                go.Scatter(x=vol_data['Process_Hours'], y=vol_data['Unit 1.V1.VPV'],
                          name='Volume', line=dict(color='navy')),
                row=3, col=1
            )
    
    if 'Unit 1.FAir1.PV' in df.columns:
        air_data = df[df['Unit 1.FAir1.PV'].notna()]
        if len(air_data) > 0:
            fig.add_trace(
                go.Scatter(x=air_data['Process_Hours'], y=air_data['Unit 1.FAir1.PV'],
                          name='Air Flow', line=dict(color='cyan')),
                row=3, col=1, secondary_y=True
            )
    
    # 6. Gas Concentrations (row=3, col=2)
    if 'Unit 1.XO21.PV' in df.columns:
        o2_data = df[df['Unit 1.XO21.PV'].notna()]
        if len(o2_data) > 0:
            fig.add_trace(
                go.Scatter(x=o2_data['Process_Hours'], y=o2_data['Unit 1.XO21.PV'],
                          name='O2 %', line=dict(color='lightblue')),
                row=3, col=2
            )
    
    if 'Unit 1.XCO21.PV' in df.columns:
        co2_data = df[df['Unit 1.XCO21.PV'].notna()]
        if len(co2_data) > 0:
            fig.add_trace(
                go.Scatter(x=co2_data['Process_Hours'], y=co2_data['Unit 1.XCO21.PV'],
                          name='CO2 %', line=dict(color='gray')),
                row=3, col=2, secondary_y=True
            )
    
    # Update layout
    fig.update_layout(
        title="DASGIP Bioreactor Process Overview",
        height=900,
        showlegend=True,
        template='plotly_white'
    )
    
    # Update x-axes
    for row in range(1, 4):
        for col in range(1, 3):
            fig.update_xaxes(title_text="Process Time (hours)", row=row, col=col)
    
    # Update y-axes with appropriate units
    fig.update_yaxes(title_text="% DO", row=1, col=1)
    fig.update_yaxes(title_text="% Output", row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text="pH", row=1, col=2)
    fig.update_yaxes(title_text="% Output", row=1, col=2, secondary_y=True)
    fig.update_yaxes(title_text="°C", row=2, col=1)
    fig.update_yaxes(title_text="% Output", row=2, col=1, secondary_y=True)
    fig.update_yaxes(title_text="RPM", row=2, col=2)
    fig.update_yaxes(title_text="mL", row=3, col=1)
    fig.update_yaxes(title_text="sL/h", row=3, col=1, secondary_y=True)
    fig.update_yaxes(title_text="% O2", row=3, col=2)
    fig.update_yaxes(title_text="% CO2", row=3, col=2, secondary_y=True)
    
    return fig

# App layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("DASGIP Bioreactor Data Analysis", 
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '20px'}),
        html.Hr()
    ]),
    
    # Data info section
    html.Div([
        html.Div(id="data-info", style={'textAlign': 'center', 'marginBottom': '20px'})
    ]),
    
    # Control tabs
    dcc.Tabs(id="main-tabs", value="overview", children=[
        dcc.Tab(label="Process Overview", value="overview"),
        dcc.Tab(label="Individual Parameters", value="parameters"),
        dcc.Tab(label="Control Performance", value="control")
    ]),
    
    # Main content area
    html.Div(id="main-content", style={'padding': '20px'})
])

# Callbacks
@app.callback(
    Output('data-info', 'children'),
    Input('main-tabs', 'value')
)
def update_data_info(tab_value):
    if dasgip_data.empty:
        return html.Div([
            html.P("⚠️ No data available. Please ensure the clean data file exists in the dasgip folder.",
                   style={'color': 'orange', 'fontSize': '16px'})
        ])
    
    start_time = dasgip_data['Timestamp'].min()
    end_time = dasgip_data['Timestamp'].max()
    duration_hours = (end_time - start_time).total_seconds() / 3600
    
    return html.Div([
        html.P(f"📊 Data loaded: {len(dasgip_data):,} data points", style={'display': 'inline-block', 'marginRight': '20px'}),
        html.P(f"⏱️ Duration: {duration_hours:.1f} hours ({duration_hours/24:.1f} days)", style={'display': 'inline-block', 'marginRight': '20px'}),
        html.P(f"📅 Period: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}", style={'display': 'inline-block'})
    ])

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
        # Create dropdown for parameter selection and individual plots
        return html.Div([
            html.H3("Individual Parameter Analysis"),
            html.Div([
                html.Label("Select Parameter:", style={'marginBottom': '10px', 'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='parameter-dropdown',
                    options=[
                        {'label': config['label'], 'value': key} 
                        for key, config in PROCESS_PARAMETERS.items()
                    ],
                    value='do',
                    style={'marginBottom': '20px'}
                )
            ]),
            dcc.Graph(id='parameter-plot')
        ])
    
    elif tab_value == "control":
        return html.Div([
            html.H3("Control Performance Analysis"),
            html.P("Control loop performance metrics and analysis coming soon...",
                   style={'textAlign': 'center', 'color': 'gray', 'fontSize': '16px', 'marginTop': '50px'})
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