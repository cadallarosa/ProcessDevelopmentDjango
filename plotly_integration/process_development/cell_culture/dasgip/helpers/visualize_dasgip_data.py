import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime
import numpy as np

def load_clean_data(file_path):
    """Load the cleaned DASGIP data"""
    print("Loading cleaned DASGIP data...")
    df = pd.read_csv(file_path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    print(f"Loaded {len(df)} data points from {df['Timestamp'].min()} to {df['Timestamp'].max()}")
    return df

def create_process_overview(df):
    """Create overview dashboard of key process parameters"""
    print("Creating process overview dashboard...")
    
    # Create subplots with secondary y-axis for different parameter scales
    fig = make_subplots(
        rows=4, cols=2,
        subplot_titles=[
            'Dissolved Oxygen (DO)', 'pH Control',
            'Temperature Control', 'Agitation Speed',
            'Air Flow Rate', 'Reactor Volume',
            'Gas Concentrations (O2 & CO2)', 'Feed Flows'
        ],
        specs=[[{"secondary_y": True}, {"secondary_y": True}],
               [{"secondary_y": True}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": True}, {"secondary_y": True}]],
        vertical_spacing=0.08,
        horizontal_spacing=0.1
    )
    
    # 1. Dissolved Oxygen
    if 'Unit 1.DO1.PV' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.DO1.PV'], 
                      name='DO PV', line=dict(color='blue'), showlegend=False),
            row=1, col=1
        )
    if 'Unit 1.DO1.SP' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.DO1.SP'], 
                      name='DO SP', line=dict(color='red', dash='dash'), showlegend=False),
            row=1, col=1
        )
    if 'Unit 1.DO1.Out' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.DO1.Out'], 
                      name='DO Out', line=dict(color='orange'), showlegend=False),
            row=1, col=1, secondary_y=True
        )
    
    # 2. pH Control
    if 'Unit 1.pH1.PV' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.pH1.PV'], 
                      name='pH PV', line=dict(color='green'), showlegend=False),
            row=1, col=2
        )
    if 'Unit 1.pH1.SP' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.pH1.SP'], 
                      name='pH SP', line=dict(color='red', dash='dash'), showlegend=False),
            row=1, col=2
        )
    if 'Unit 1.pH1.Out' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.pH1.Out'], 
                      name='pH Out', line=dict(color='purple'), showlegend=False),
            row=1, col=2, secondary_y=True
        )
    
    # 3. Temperature Control
    if 'Unit 1.T1.PV' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.T1.PV'], 
                      name='Temp PV', line=dict(color='red'), showlegend=False),
            row=2, col=1
        )
    if 'Unit 1.T1.SP' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.T1.SP'], 
                      name='Temp SP', line=dict(color='darkred', dash='dash'), showlegend=False),
            row=2, col=1
        )
    if 'Unit 1.T1.Out' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.T1.Out'], 
                      name='Temp Out', line=dict(color='orange'), showlegend=False),
            row=2, col=1, secondary_y=True
        )
    
    # 4. Agitation Speed
    if 'Unit 1.N1.PV' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.N1.PV'], 
                      name='RPM PV', line=dict(color='brown'), showlegend=False),
            row=2, col=2
        )
    if 'Unit 1.N1.SP' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.N1.SP'], 
                      name='RPM SP', line=dict(color='red', dash='dash'), showlegend=False),
            row=2, col=2
        )
    
    # 5. Air Flow
    if 'Unit 1.FAir1.PV' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.FAir1.PV'], 
                      name='Air Flow PV', line=dict(color='cyan'), showlegend=False),
            row=3, col=1
        )
    if 'Unit 1.FAir1.SP' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.FAir1.SP'], 
                      name='Air Flow SP', line=dict(color='red', dash='dash'), showlegend=False),
            row=3, col=1
        )
    
    # 6. Reactor Volume
    if 'Unit 1.V1.VPV' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.V1.VPV'], 
                      name='Volume', line=dict(color='navy'), showlegend=False),
            row=3, col=2
        )
    
    # 7. Gas Concentrations
    if 'Unit 1.XO21.PV' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.XO21.PV'], 
                      name='O2 %', line=dict(color='lightblue'), showlegend=False),
            row=4, col=1
        )
    if 'Unit 1.XCO21.PV' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.XCO21.PV'], 
                      name='CO2 %', line=dict(color='gray'), showlegend=False),
            row=4, col=1, secondary_y=True
        )
    
    # 8. Feed Flows
    if 'Unit 1.FA1.PV' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.FA1.PV'], 
                      name='Feed A', line=dict(color='magenta'), showlegend=False),
            row=4, col=2
        )
    if 'Unit 1.FB1.PV' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.FB1.PV'], 
                      name='Feed B', line=dict(color='yellow'), showlegend=False),
            row=4, col=2, secondary_y=True
        )
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'DASGIP Bioreactor Process Overview<br><sub>Key Process Parameters Over Time</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        height=1200,
        showlegend=False,
        template='plotly_white'
    )
    
    # Update y-axis labels
    fig.update_yaxes(title_text="% DO", row=1, col=1)
    fig.update_yaxes(title_text="% Output", row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text="pH", row=1, col=2)
    fig.update_yaxes(title_text="% Output", row=1, col=2, secondary_y=True)
    fig.update_yaxes(title_text="°C", row=2, col=1)
    fig.update_yaxes(title_text="% Output", row=2, col=1, secondary_y=True)
    fig.update_yaxes(title_text="RPM", row=2, col=2)
    fig.update_yaxes(title_text="sL/h", row=3, col=1)
    fig.update_yaxes(title_text="mL", row=3, col=2)
    fig.update_yaxes(title_text="% O2", row=4, col=1)
    fig.update_yaxes(title_text="% CO2", row=4, col=1, secondary_y=True)
    fig.update_yaxes(title_text="mL/h Feed A", row=4, col=2)
    fig.update_yaxes(title_text="mL/h Feed B", row=4, col=2, secondary_y=True)
    
    return fig

def create_control_performance_analysis(df):
    """Create control loop performance analysis"""
    print("Creating control performance analysis...")
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            'DO Control Performance', 'pH Control Performance',
            'Temperature Control Performance', 'Process Variables Correlation'
        ],
        specs=[[{"secondary_y": True}, {"secondary_y": True}],
               [{"secondary_y": True}, {}]]
    )
    
    # DO Control Performance
    if all(col in df.columns for col in ['Unit 1.DO1.PV', 'Unit 1.DO1.SP', 'Unit 1.DO1.Out']):
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.DO1.PV'], 
                      name='DO PV', line=dict(color='blue')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.DO1.SP'], 
                      name='DO SP', line=dict(color='red', dash='dash')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.DO1.Out'], 
                      name='DO Output', line=dict(color='orange')),
            row=1, col=1, secondary_y=True
        )
    
    # pH Control Performance
    if all(col in df.columns for col in ['Unit 1.pH1.PV', 'Unit 1.pH1.SP', 'Unit 1.pH1.Out']):
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.pH1.PV'], 
                      name='pH PV', line=dict(color='green')),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.pH1.SP'], 
                      name='pH SP', line=dict(color='red', dash='dash')),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.pH1.Out'], 
                      name='pH Output', line=dict(color='purple')),
            row=1, col=2, secondary_y=True
        )
    
    # Temperature Control Performance
    if all(col in df.columns for col in ['Unit 1.T1.PV', 'Unit 1.T1.SP', 'Unit 1.T1.Out']):
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.T1.PV'], 
                      name='Temp PV', line=dict(color='red')),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.T1.SP'], 
                      name='Temp SP', line=dict(color='red', dash='dash')),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['Timestamp'], y=df['Unit 1.T1.Out'], 
                      name='Temp Output', line=dict(color='orange')),
            row=2, col=1, secondary_y=True
        )
    
    # Correlation analysis
    corr_cols = ['Unit 1.DO1.PV', 'Unit 1.pH1.PV', 'Unit 1.T1.PV', 'Unit 1.N1.PV']
    available_cols = [col for col in corr_cols if col in df.columns]
    
    if len(available_cols) > 1:
        corr_data = df[available_cols].corr()
        
        fig.add_trace(
            go.Heatmap(
                z=corr_data.values,
                x=[col.replace('Unit 1.', '').replace('.PV', '') for col in corr_data.columns],
                y=[col.replace('Unit 1.', '').replace('.PV', '') for col in corr_data.columns],
                colorscale='RdBu',
                zmid=0,
                showscale=True,
                text=np.round(corr_data.values, 2),
                texttemplate="%{text}",
                textfont={"size": 10}
            ),
            row=2, col=2
        )
    
    fig.update_layout(
        title='Control Loop Performance Analysis',
        height=800,
        showlegend=True,
        template='plotly_white'
    )
    
    return fig

def create_offline_measurements_plot(df):
    """Create visualization of offline measurements if any data exists"""
    print("Creating offline measurements visualization...")
    
    # Find offline columns with data
    offline_cols = [col for col in df.columns if 'Offline' in col]
    offline_cols_with_data = []
    
    for col in offline_cols:
        if df[col].notna().sum() > 0:
            offline_cols_with_data.append(col)
    
    if not offline_cols_with_data:
        print("No offline measurement data found")
        return None
    
    print(f"Found {len(offline_cols_with_data)} offline parameters with data")
    
    # Create subplot for offline measurements
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set3
    
    for i, col in enumerate(offline_cols_with_data):
        # Only plot non-null values
        data_subset = df[df[col].notna()]
        if len(data_subset) > 0:
            fig.add_trace(
                go.Scatter(
                    x=data_subset['Timestamp'],
                    y=data_subset[col],
                    mode='markers+lines',
                    name=col.replace('Unit 1.', '').replace('.Offline', ''),
                    line=dict(color=colors[i % len(colors)]),
                    marker=dict(size=8)
                )
            )
    
    fig.update_layout(
        title='Offline Measurements Over Time',
        xaxis_title='Time',
        yaxis_title='Measurement Value',
        template='plotly_white',
        height=600
    )
    
    return fig

def generate_process_report(df):
    """Generate a summary report of the process"""
    print("Generating process summary report...")
    
    report = {
        'run_duration': (df['Timestamp'].max() - df['Timestamp'].min()).total_seconds() / 3600,  # hours
        'total_samples': len(df),
        'sampling_interval': df['Duration'].diff().median() * 24 * 60,  # minutes
    }
    
    # Key parameter statistics
    key_params = {
        'DO': 'Unit 1.DO1.PV',
        'pH': 'Unit 1.pH1.PV', 
        'Temperature': 'Unit 1.T1.PV',
        'RPM': 'Unit 1.N1.PV',
        'Volume': 'Unit 1.V1.VPV'
    }
    
    for param_name, col_name in key_params.items():
        if col_name in df.columns:
            data = df[col_name].dropna()
            if len(data) > 0:
                report[f'{param_name}_mean'] = data.mean()
                report[f'{param_name}_std'] = data.std()
                report[f'{param_name}_min'] = data.min()
                report[f'{param_name}_max'] = data.max()
    
    return report

if __name__ == "__main__":
    # Load data
    data_file = r"/plotly_integration/process_development/cell_culture/dasgip/CTPCNK808814_E59BRX_Control_clean.csv"
    df = load_clean_data(data_file)
    
    # Generate process report
    report = generate_process_report(df)
    print("\n" + "="*50)
    print("PROCESS SUMMARY REPORT")
    print("="*50)
    print(f"Run Duration: {report['run_duration']:.1f} hours ({report['run_duration']/24:.1f} days)")
    print(f"Total Samples: {report['total_samples']:,}")
    print(f"Sampling Interval: ~{report['sampling_interval']:.1f} minutes")
    print()
    
    for key, value in report.items():
        if key.endswith('_mean'):
            param = key.replace('_mean', '')
            if f'{param}_std' in report:
                print(f"{param}: {value:.2f} ± {report[f'{param}_std']:.2f} (range: {report[f'{param}_min']:.2f} - {report[f'{param}_max']:.2f})")
    
    # Create visualizations
    print("\n" + "="*50)
    print("CREATING VISUALIZATIONS")
    print("="*50)
    
    # 1. Process Overview
    overview_fig = create_process_overview(df)
    overview_fig.write_html("DASGIP_Process_Overview.html")
    print(">> Process Overview saved as: DASGIP_Process_Overview.html")
    
    # 2. Control Performance
    control_fig = create_control_performance_analysis(df)
    control_fig.write_html("DASGIP_Control_Performance.html")
    print(">> Control Performance Analysis saved as: DASGIP_Control_Performance.html")
    
    # 3. Offline Measurements
    offline_fig = create_offline_measurements_plot(df)
    if offline_fig:
        offline_fig.write_html("DASGIP_Offline_Measurements.html")
        print(">> Offline Measurements saved as: DASGIP_Offline_Measurements.html")
    
    print("\n** Visualization complete! Open the HTML files to view interactive plots.")
    print("\nFiles created:")
    print("  - DASGIP_Process_Overview.html (Main dashboard)")
    print("  - DASGIP_Control_Performance.html (Control analysis)")
    if offline_fig:
        print("  - DASGIP_Offline_Measurements.html (Offline data)")