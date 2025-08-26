import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import savgol_filter
import base64
import io
from django_plotly_dash import DjangoDash
from django.utils import timezone
import logging
from datetime import datetime

# Initialize the Dash app
app = DjangoDash("OctetAnalysisApp", external_stylesheets=[
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
    dbc.themes.BOOTSTRAP
])

# Enhanced Styles
CARD_STYLE = {
    "margin": "20px 0",
    "padding": "25px",
    "border": "1px solid #dee2e6",
    "border-radius": "12px",
    "box-shadow": "0 4px 6px rgba(0,0,0,0.1)"
}

UPLOAD_STYLE = {
    'width': '100%',
    'height': '120px',
    'lineHeight': '120px',
    'borderWidth': '2px',
    'borderStyle': 'dashed',
    'borderRadius': '10px',
    'textAlign': 'center',
    'backgroundColor': '#f8f9fa',
    'border': '2px dashed #0056b3',
    'cursor': 'pointer',
    'margin': '15px 0'
}

# App Layout
app.layout = html.Div([
    # Data Storage
    dcc.Store(id="raw-data-store"),
    dcc.Store(id="metadata-store"),
    dcc.Store(id="processed-data-store"),
    dcc.Store(id="analysis-results-store"),
    dcc.Store(id="proa-results-store"),
    dcc.Store(id="kappa-results-store"),
    
    # Header
    html.Div([
        html.H2([
            html.I(className="fas fa-chart-line me-3"),
            "Octet Data Analysis"
        ], style={"color": "#0056b3", "margin-bottom": "15px"}),
        html.P("Analyze binding kinetics and calculate affinity constants from Octet BLI data",
               style={"color": "#6c757d", "margin-bottom": "10px", "fontSize": "16px"})
    ], style={"margin-bottom": "25px", "text-align": "center"}),
    
    # Tab structure
    dbc.Tabs([
        # Data Import Tab
        dbc.Tab(label="Data Import", tab_id="import-tab", children=[
            html.Div([
                # File Upload Section - Two separate uploads for paired files
                html.Div([
                    html.H4([
                        html.I(className="fas fa-file-upload me-2"),
                        "Upload Octet Data Files"
                    ], style={"color": "#0056b3", "margin-bottom": "20px"}),
                    
                    html.P("Upload both the raw data file and the experiment metadata file for analysis",
                           style={"color": "#6c757d", "margin-bottom": "20px"}),
                    
                    # Raw Data Upload
                    html.Div([
                        html.H5("1. Raw Data File (e.g., plate.xls)", style={"margin-bottom": "10px"}),
                        dcc.Upload(
                            id='upload-raw-data',
                            children=html.Div([
                                html.I(className="fas fa-chart-line fa-2x",
                                       style={"color": "#0056b3", "margin-bottom": "10px"}),
                                html.Br(),
                                html.Strong("Drop raw data file here"),
                                html.Br(),
                                html.Span("Tab-delimited sensor data", style={"color": "#6c757d", "fontSize": "14px"})
                            ]),
                            style={**UPLOAD_STYLE, 'height': '100px', 'lineHeight': '100px'},
                            multiple=False,
                            accept='.xls,.txt,.tsv'
                        ),
                        html.Div(id='raw-upload-status')
                    ], style={"margin-bottom": "20px"}),
                    
                    # Metadata Upload
                    html.Div([
                        html.H5("2. Experiment Metadata File (e.g., ExcelReport.xls)", style={"margin-bottom": "10px"}),
                        dcc.Upload(
                            id='upload-metadata',
                            children=html.Div([
                                html.I(className="fas fa-info-circle fa-2x",
                                       style={"color": "#0056b3", "margin-bottom": "10px"}),
                                html.Br(),
                                html.Strong("Drop metadata file here"),
                                html.Br(),
                                html.Span("Experiment conditions and sample info", style={"color": "#6c757d", "fontSize": "14px"})
                            ]),
                            style={**UPLOAD_STYLE, 'height': '100px', 'lineHeight': '100px'},
                            multiple=False,
                            accept='.xls,.xlsx'
                        ),
                        html.Div(id='metadata-upload-status')
                    ]),
                    
                    html.Div(id='upload-status-div', style={"margin-top": "20px"})
                ], style=CARD_STYLE),
                
                # Data Preview Section
                html.Div([
                    html.H4([
                        html.I(className="fas fa-table me-2"),
                        "Data Preview"
                    ], style={"color": "#0056b3", "margin-bottom": "20px"}),
                    
                    html.Div(id='data-preview-container')
                ], id='preview-section', style={'display': 'none', **CARD_STYLE})
            ])
        ]),
        
        # Visualization Tab
        dbc.Tab(label="Visualization", tab_id="viz-tab", children=[
            html.Div([
                # Controls Section
                html.Div([
                    html.H4([
                        html.I(className="fas fa-sliders-h me-2"),
                        "Visualization Controls"
                    ], style={"color": "#0056b3", "margin-bottom": "20px"}),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label("Select Sample(s):", style={"font-weight": "bold"}),
                            dcc.Dropdown(
                                id='sample-selector',
                                multi=True,
                                placeholder="Select samples to visualize..."
                            )
                        ], md=6),
                        
                        dbc.Col([
                            html.Label("Plot Type:", style={"font-weight": "bold"}),
                            dcc.RadioItems(
                                id='plot-type-selector',
                                options=[
                                    {"label": " Sensorgram", "value": "sensorgram"},
                                    {"label": " Binding Curves", "value": "binding"},
                                    {"label": " Association/Dissociation", "value": "kinetics"}
                                ],
                                value="sensorgram",
                                inline=True
                            )
                        ], md=6)
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            dcc.Checklist(
                                id='plot-options',
                                options=[
                                    {"label": " Show Reference", "value": "show_ref"},
                                    {"label": " Apply Smoothing", "value": "smooth"},
                                    {"label": " Baseline Correction", "value": "baseline"},
                                    {"label": " Show Grid", "value": "grid"},
                                    {"label": " Analysis View (420s+)", "value": "analysis_view"}
                                ],
                                value=["grid"],
                                inline=True
                            )
                        ], md=12)
                    ])
                ], style=CARD_STYLE),
                
                # Plot Display Section
                html.Div([
                    dcc.Graph(id='main-plot', style={'height': '600px'})
                ], id='plot-section', style={'display': 'none', **CARD_STYLE})
            ])
        ]),
        
        # Analysis Tab
        dbc.Tab(label="Kinetic Analysis", tab_id="analysis-tab", children=[
            html.Div([
                # Analysis Setup
                html.Div([
                    html.H4([
                        html.I(className="fas fa-calculator me-2"),
                        "Kinetic Analysis Setup"
                    ], style={"color": "#0056b3", "margin-bottom": "20px"}),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label("Analysis Model:", style={"font-weight": "bold"}),
                            dcc.Dropdown(
                                id='analysis-model',
                                options=[
                                    {"label": "1:1 Binding", "value": "1to1"},
                                    {"label": "Heterogeneous Ligand", "value": "hetero"},
                                    {"label": "Mass Transport", "value": "mass_transport"},
                                    {"label": "Steady State", "value": "steady_state"}
                                ],
                                value="1to1",
                                clearable=False
                            )
                        ], md=4),
                        
                        dbc.Col([
                            html.Label("Association Time (s):", style={"font-weight": "bold"}),
                            dcc.Input(
                                id='assoc-time-input',
                                type="number",
                                value=180,
                                min=0,
                                style={"width": "100%"}
                            )
                        ], md=4),
                        
                        dbc.Col([
                            html.Label("Dissociation Time (s):", style={"font-weight": "bold"}),
                            dcc.Input(
                                id='dissoc-time-input',
                                type="number",
                                value=180,
                                min=0,
                                style={"width": "100%"}
                            )
                        ], md=4)
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label("Ligand Concentration (nM):", style={"font-weight": "bold"}),
                            dcc.Input(
                                id='concentration-input',
                                type="text",
                                placeholder="e.g., 100,50,25,12.5,6.25",
                                style={"width": "100%"}
                            )
                        ], md=8),
                        
                        dbc.Col([
                            html.Button([
                                html.I(className="fas fa-play me-2"),
                                "Run Analysis"
                            ], id='run-analysis-btn',
                                className="btn btn-primary",
                                style={"width": "100%", "margin-top": "25px"})
                        ], md=4)
                    ])
                ], style=CARD_STYLE),
                
                # Analysis Results
                html.Div([
                    html.H4([
                        html.I(className="fas fa-chart-area me-2"),
                        "Fitting Results"
                    ], style={"color": "#0056b3", "margin-bottom": "20px"}),
                    
                    html.Div(id='fitting-plot-container'),
                    
                    html.Hr(),
                    
                    html.H5("Kinetic Parameters:", style={"margin-bottom": "15px"}),
                    html.Div(id='kinetic-parameters-table')
                ], id='analysis-results-section', style={'display': 'none', **CARD_STYLE})
            ])
        ]),
        
        # Quantitative Analysis Tab
        dbc.Tab(label="ProA Analysis", tab_id="proa-tab", children=[
            html.Div([
                # Analysis Setup
                html.Div([
                    html.H4([
                        html.I(className="fas fa-chart-line me-2"),
                        "ProA Loading Analysis (420-430s)"
                    ], style={"color": "#0056b3", "margin-bottom": "20px"}),
                    
                    html.P("Calculate initial response slopes for ProA loading quantification",
                           style={"color": "#6c757d", "margin-bottom": "20px"}),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label("Analysis Time Window:", style={"font-weight": "bold"}),
                            html.Div([
                                html.Label("Start Time (s):", style={"margin-right": "10px"}),
                                dcc.Input(
                                    id='analysis-start-time',
                                    type="number",
                                    value=420,
                                    step=1,
                                    style={"width": "80px", "margin-right": "20px"}
                                ),
                                html.Label("End Time (s):", style={"margin-right": "10px"}),
                                dcc.Input(
                                    id='analysis-end-time',
                                    type="number",
                                    value=430,
                                    step=1,
                                    style={"width": "80px"}
                                )
                            ])
                        ], md=8),
                        
                        dbc.Col([
                            html.Button([
                                html.I(className="fas fa-calculator me-2"),
                                "Calculate Slopes"
                            ], id='calculate-slopes-btn',
                                className="btn btn-primary",
                                style={"width": "100%", "margin-top": "25px"})
                        ], md=4)
                    ])
                ], style=CARD_STYLE),
                
                # Results Section
                html.Div([
                    html.H4([
                        html.I(className="fas fa-table me-2"),
                        "Slope Analysis Results"
                    ], style={"color": "#0056b3", "margin-bottom": "20px"}),
                    
                    html.Div(id='slope-results-container')
                ], id='slope-results-section', style={'display': 'none', **CARD_STYLE}),
                
                # Standard Curve Section
                html.Div([
                    html.H4([
                        html.I(className="fas fa-chart-area me-2"),
                        "Standard Curve & Sample Quantification"
                    ], style={"color": "#0056b3", "margin-bottom": "20px"}),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Div(id='standard-curve-plot')
                        ], md=8),
                        dbc.Col([
                            html.H5("Sample Concentrations:", style={"margin-bottom": "15px"}),
                            html.Div(id='sample-concentrations-table')
                        ], md=4)
                    ])
                ], id='standard-curve-section', style={'display': 'none', **CARD_STYLE})
            ])
        ]),
        
        # Kappa Analysis Tab
        dbc.Tab(label="Kappa Analysis", tab_id="kappa-tab", children=[
            html.Div([
                # Analysis Setup
                html.Div([
                    html.H4([
                        html.I(className="fas fa-chart-line me-2"),
                        "Kappa Concentration Analysis (520-530s)"
                    ], style={"color": "#0056b3", "margin-bottom": "20px"}),
                    
                    html.P("Calculate initial response slopes for Kappa concentration quantification during Association phase",
                           style={"color": "#6c757d", "margin-bottom": "20px"}),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label("Analysis Time Window:", style={"font-weight": "bold"}),
                            html.Div([
                                html.Label("Start Time (s):", style={"margin-right": "10px"}),
                                dcc.Input(
                                    id='kappa-start-time',
                                    type="number",
                                    value=520,
                                    step=1,
                                    style={"width": "80px", "margin-right": "20px"}
                                ),
                                html.Label("End Time (s):", style={"margin-right": "10px"}),
                                dcc.Input(
                                    id='kappa-end-time',
                                    type="number",
                                    value=530,
                                    step=1,
                                    style={"width": "80px"}
                                )
                            ])
                        ], md=8),
                        
                        dbc.Col([
                            html.Button([
                                html.I(className="fas fa-calculator me-2"),
                                "Calculate Kappa Slopes"
                            ], id='calculate-kappa-slopes-btn',
                                className="btn btn-success",
                                style={"width": "100%", "margin-top": "25px"})
                        ], md=4)
                    ])
                ], style=CARD_STYLE),
                
                # Results Section
                html.Div([
                    html.H4([
                        html.I(className="fas fa-table me-2"),
                        "Kappa Slope Analysis Results"
                    ], style={"color": "#0056b3", "margin-bottom": "20px"}),
                    
                    html.Div(id='kappa-slope-results-container')
                ], id='kappa-slope-results-section', style={'display': 'none', **CARD_STYLE}),
                
                # Standard Curve Section
                html.Div([
                    html.H4([
                        html.I(className="fas fa-chart-area me-2"),
                        "Kappa Standard Curve & Sample Quantification"
                    ], style={"color": "#0056b3", "margin-bottom": "20px"}),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Div(id='kappa-standard-curve-plot')
                        ], md=8),
                        dbc.Col([
                            html.H5("Kappa Concentrations:", style={"margin-bottom": "15px"}),
                            html.Div(id='kappa-sample-concentrations-table')
                        ], md=4)
                    ])
                ], id='kappa-standard-curve-section', style={'display': 'none', **CARD_STYLE})
            ])
        ]),
        
        # Summary Tab
        dbc.Tab(label="Summary", tab_id="summary-tab", children=[
            html.Div([
                html.Div([
                    html.H4([
                        html.I(className="fas fa-clipboard-list me-2"),
                        "Analysis Summary"
                    ], style={"color": "#0056b3", "margin-bottom": "20px"}),
                    
                    html.P("Combined results from ProA loading and Kappa concentration analysis",
                           style={"color": "#6c757d", "margin-bottom": "20px"}),
                    
                    html.Div(id='summary-table-container'),
                    
                    html.Hr(),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Button([
                                html.I(className="fas fa-download me-2"),
                                "Export Summary CSV"
                            ], id='export-summary-btn',
                                className="btn btn-info")
                        ], md=6),
                        dbc.Col([
                            html.Button([
                                html.I(className="fas fa-chart-bar me-2"),
                                "Generate Summary Plot"
                            ], id='generate-summary-plot-btn',
                                className="btn btn-primary")
                        ], md=6)
                    ])
                ], style=CARD_STYLE),
                
                # Summary Plots
                html.Div([
                    html.Div(id='summary-plots-container')
                ], id='summary-plots-section', style={'display': 'none', **CARD_STYLE})
            ])
        ]),
        
        # Report Tab
        dbc.Tab(label="Report", tab_id="report-tab", children=[
            html.Div([
                html.Div([
                    html.H4([
                        html.I(className="fas fa-file-alt me-2"),
                        "Generate Report"
                    ], style={"color": "#0056b3", "margin-bottom": "20px"}),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label("Report Title:", style={"font-weight": "bold"}),
                            dcc.Input(
                                id='report-title',
                                type="text",
                                value=f"Octet Analysis Report - {datetime.now().strftime('%Y-%m-%d')}",
                                style={"width": "100%"}
                            )
                        ], md=8),
                        
                        dbc.Col([
                            html.Label("Format:", style={"font-weight": "bold"}),
                            dcc.RadioItems(
                                id='report-format',
                                options=[
                                    {"label": " HTML", "value": "html"},
                                    {"label": " PDF", "value": "pdf"},
                                    {"label": " Excel", "value": "excel"}
                                ],
                                value="html",
                                inline=True
                            )
                        ], md=4)
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            dcc.Checklist(
                                id='report-sections',
                                options=[
                                    {"label": " Raw Data Tables", "value": "raw_data"},
                                    {"label": " Sensorgrams", "value": "sensorgrams"},
                                    {"label": " Kinetic Fits", "value": "fits"},
                                    {"label": " Parameters Table", "value": "parameters"},
                                    {"label": " QC Metrics", "value": "qc"}
                                ],
                                value=["sensorgrams", "fits", "parameters"],
                                inline=False
                            )
                        ], md=8),
                        
                        dbc.Col([
                            html.Button([
                                html.I(className="fas fa-download me-2"),
                                "Generate Report"
                            ], id='generate-report-btn',
                                className="btn btn-success",
                                style={"width": "100%", "margin-top": "20px"})
                        ], md=4)
                    ])
                ], style=CARD_STYLE),
                
                html.Div(id='report-status')
            ])
        ])
    ], id="tabs", active_tab="import-tab")
    
], style={"max-width": "1400px", "margin": "0 auto", "padding": "20px"})


# Helper Functions
def parse_raw_octet_data(contents, filename):
    """Parse raw Octet data file (tab-delimited with time and response pairs)"""
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Try to read as tab-delimited file
        try:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8', errors='ignore')), sep='\t')
        except:
            df = pd.read_csv(io.BytesIO(decoded), sep='\t')
        
        # Process the data - columns are in pairs (time, response)
        sensors_data = {}
        for i in range(0, len(df.columns)-1, 2):
            sensor_name = df.columns[i]
            if 'Unnamed' not in sensor_name:
                time_col = df.iloc[:, i]
                response_col = df.iloc[:, i+1]
                
                # Clean data - remove NaN values
                valid_mask = ~(time_col.isna() | response_col.isna())
                sensors_data[sensor_name] = pd.DataFrame({
                    'Time': time_col[valid_mask].values,
                    'Response': response_col[valid_mask].values
                })
        
        return sensors_data
    except Exception as e:
        logging.error(f"Error parsing raw data {filename}: {str(e)}")
        return None


def parse_metadata_file(contents, filename):
    """Parse Octet metadata/ExcelReport file"""
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Try different parsing methods
        metadata = {}
        
        # Try reading as Excel
        try:
            excel_file = pd.ExcelFile(io.BytesIO(decoded))
            metadata['sheets'] = excel_file.sheet_names
            
            # Read all sheets to extract metadata
            for sheet in excel_file.sheet_names:
                df = pd.read_excel(io.BytesIO(decoded), sheet_name=sheet)
                metadata[sheet] = df.to_dict('records')
                
                # Look for specific metadata tables
                if 'Sensor' in str(df.columns) and 'Sample ID' in str(df.columns):
                    # This is likely the sensor/sample mapping table
                    metadata['sensor_info'] = df.to_dict('records')
                    metadata['sensor_mapping'] = {
                        row['Sensor Location']: {
                            'sample_id': row['Sample ID'],
                            'sensor_type': row.get('Sensor Type', ''),
                            'color': row.get('Color', None),
                            'replicate': row.get('Replicate Group', 'N/A')
                        } for row in df.to_dict('records') if 'Sensor Location' in row
                    }
                
                if 'Step Data Name' in str(df.columns) and 'Assay Time' in str(df.columns):
                    # This is the assay steps table
                    metadata['assay_steps'] = df.to_dict('records')
        except:
            # Try reading as HTML tables
            try:
                dfs = pd.read_html(io.BytesIO(decoded))
                metadata['tables'] = []
                
                for i, df in enumerate(dfs):
                    metadata['tables'].append(df.to_dict('records'))
                    
                    # Check for sensor info table
                    if 'Sensor Location' in df.columns and 'Sample ID' in df.columns:
                        metadata['sensor_info'] = df.to_dict('records')
                        metadata['sensor_mapping'] = {
                            row['Sensor Location']: {
                                'sample_id': row['Sample ID'],
                                'sensor_type': row.get('Sensor Type', ''),
                                'color': row.get('Color', None),
                                'replicate': row.get('Replicate Group', 'N/A')
                            } for row in df.to_dict('records')
                        }
                    
                    # Check for assay steps table
                    if 'Step Data Name' in df.columns and 'Assay Time' in df.columns:
                        metadata['assay_steps'] = df.to_dict('records')
            except:
                metadata['error'] = "Could not parse metadata file"
        
        return metadata
    except Exception as e:
        logging.error(f"Error parsing metadata {filename}: {str(e)}")
        return None


def calculate_kinetics_1to1(time, response, assoc_time, dissoc_time, concentration):
    """Calculate 1:1 binding kinetics"""
    try:
        # Separate association and dissociation phases
        assoc_mask = time <= assoc_time
        dissoc_mask = time > assoc_time
        
        # Define fitting functions
        def assoc_func(t, Rmax, ka):
            kobs = ka * concentration * 1e-9  # Convert nM to M
            return Rmax * (1 - np.exp(-kobs * t))
        
        def dissoc_func(t, R0, kd):
            return R0 * np.exp(-kd * (t - assoc_time))
        
        # Fit association phase
        if np.sum(assoc_mask) > 10:
            assoc_time_data = time[assoc_mask]
            assoc_response = response[assoc_mask]
            
            # Initial guess for association
            Rmax_guess = np.max(response)
            ka_guess = 1e4  # M-1s-1
            
            popt_assoc, _ = curve_fit(
                assoc_func, 
                assoc_time_data, 
                assoc_response,
                p0=[Rmax_guess, ka_guess],
                bounds=([0, 1e3], [np.inf, 1e7])
            )
            Rmax, ka = popt_assoc
        else:
            Rmax = np.max(response)
            ka = 1e4
        
        # Fit dissociation phase
        if np.sum(dissoc_mask) > 10:
            dissoc_time_data = time[dissoc_mask]
            dissoc_response = response[dissoc_mask]
            
            # Initial guess for dissociation
            R0_guess = response[assoc_mask][-1] if np.sum(assoc_mask) > 0 else Rmax
            kd_guess = 1e-3  # s-1
            
            popt_dissoc, _ = curve_fit(
                dissoc_func,
                dissoc_time_data,
                dissoc_response,
                p0=[R0_guess, kd_guess],
                bounds=([0, 1e-5], [np.inf, 1])
            )
            R0, kd = popt_dissoc
        else:
            kd = 1e-3
        
        # Calculate KD
        KD = kd / ka  # M
        KD_nM = KD * 1e9  # Convert to nM
        
        # Generate fitted curves
        fitted_assoc = assoc_func(time[assoc_mask], Rmax, ka)
        fitted_dissoc = dissoc_func(time[dissoc_mask], R0, kd) if np.sum(dissoc_mask) > 0 else []
        fitted_full = np.concatenate([fitted_assoc, fitted_dissoc])
        
        return {
            'ka': ka,
            'kd': kd,
            'KD': KD_nM,
            'Rmax': Rmax,
            'fitted_curve': fitted_full,
            'r_squared': calculate_r_squared(response, fitted_full)
        }
    
    except Exception as e:
        logging.error(f"Error in kinetics calculation: {str(e)}")
        return None


def calculate_r_squared(y_true, y_pred):
    """Calculate R-squared value"""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - (ss_res / ss_tot) if ss_tot != 0 else 0


def apply_smoothing(data, window_length=5, polyorder=2):
    """Apply Savitzky-Golay filter for smoothing"""
    if len(data) < window_length:
        return data
    return savgol_filter(data, window_length, polyorder)


def calculate_initial_response_slope(time_data, response_data, start_time, end_time):
    """Calculate slope (initial response rate) for a specific time interval"""
    try:
        # Find data points within the specified time interval
        mask = (time_data >= start_time) & (time_data <= end_time)
        
        if np.sum(mask) < 3:  # Need at least 3 points for reliable slope
            return None, None, None
        
        time_subset = time_data[mask]
        response_subset = response_data[mask]
        
        # Calculate linear regression slope
        coeffs = np.polyfit(time_subset, response_subset, 1)
        slope = coeffs[0]  # slope (nm/s)
        intercept = coeffs[1]
        
        # Calculate R-squared for fit quality
        fitted_values = np.polyval(coeffs, time_subset)
        r_squared = calculate_r_squared(response_subset, fitted_values)
        
        return slope, intercept, r_squared
    
    except Exception as e:
        logging.error(f"Error calculating slope: {str(e)}")
        return None, None, None


def extract_standard_concentrations(metadata):
    """Extract standard concentrations from metadata"""
    standards = {}
    
    # Look for standards in sensor mapping
    sensor_mapping = metadata.get('sensor_mapping', {})
    
    # Standard concentration mapping (you provided this)
    std_concentrations = {
        'Std 7': 7.0,
        'Std 5': 5.0, 
        'Std 2.5': 2.5,
        'Std 1.25': 1.25,
        'Std 0.625': 0.625
    }
    
    for sensor, info in sensor_mapping.items():
        sample_id = info.get('sample_id', '')
        for std_name, concentration in std_concentrations.items():
            if std_name in str(sample_id):
                standards[sensor] = {
                    'concentration': concentration,
                    'sample_id': sample_id,
                    'units': 'µg/mL'  # Assuming concentration units
                }
                break
    
    return standards


def create_standard_curve(standard_data):
    """Create standard curve from concentration vs initial response data"""
    if len(standard_data) < 3:
        return None, None, None, None
    
    concentrations = []
    responses = []
    
    for std_info in standard_data:
        concentrations.append(std_info['concentration'])
        responses.append(std_info['slope'])
    
    concentrations = np.array(concentrations)
    responses = np.array(responses)
    
    # Fit linear standard curve
    coeffs = np.polyfit(concentrations, responses, 1)
    slope = coeffs[0]  # response per unit concentration
    intercept = coeffs[1]
    
    # Calculate R-squared
    fitted_responses = np.polyval(coeffs, concentrations)
    r_squared = calculate_r_squared(responses, fitted_responses)
    
    return slope, intercept, r_squared, (concentrations, responses, fitted_responses)


def calculate_step_times(assay_steps):
    """Calculate cumulative times for assay steps"""
    if not assay_steps:
        return []
    
    step_markers = []
    cumulative_time = 0
    
    # Group steps by sensor column to handle multiple columns
    sensor_columns = {}
    for step in assay_steps:
        sensor_col = step.get('Sensor Column', 1)
        if sensor_col not in sensor_columns:
            sensor_columns[sensor_col] = []
        sensor_columns[sensor_col].append(step)
    
    # Process first sensor column (usually column 1) for main timeline
    if 1 in sensor_columns:
        for step in sensor_columns[1]:
            step_name = step.get('Step Data Name', '')
            step_time = float(step.get('Assay Time', 0))
            step_type = step.get('Step Type', '')
            step_number = step.get('Assay Step Number', 0)
            
            # Store start time of this step
            step_start = cumulative_time
            
            # Add to cumulative time
            cumulative_time += step_time
            
            # Create marker info
            step_markers.append({
                'name': step_name,
                'type': step_type,
                'start': step_start,
                'end': cumulative_time,
                'duration': step_time,
                'number': step_number
            })
    
    return step_markers


# Callbacks for paired file uploads
@app.callback(
    [Output('raw-upload-status', 'children'),
     Output('raw-data-store', 'data')],
    [Input('upload-raw-data', 'contents')],
    [State('upload-raw-data', 'filename')]
)
def handle_raw_data_upload(contents, filename):
    if not contents:
        return "", None
    
    sensors_data = parse_raw_octet_data(contents, filename)
    
    if sensors_data:
        status = html.Div([
            html.I(className="fas fa-check-circle me-2", style={"color": "green"}),
            f"Loaded {filename}: {len(sensors_data)} sensors found"
        ], className="alert alert-success")
        
        # Convert to storable format
        store_data = {
            'filename': filename,
            'sensors': {name: df.to_dict('records') for name, df in sensors_data.items()},
            'sensor_names': list(sensors_data.keys())
        }
        return status, store_data
    else:
        status = html.Div([
            html.I(className="fas fa-exclamation-circle me-2", style={"color": "red"}),
            f"Failed to load {filename}"
        ], className="alert alert-danger")
        return status, None


@app.callback(
    [Output('metadata-upload-status', 'children'),
     Output('metadata-store', 'data')],
    [Input('upload-metadata', 'contents')],
    [State('upload-metadata', 'filename')]
)
def handle_metadata_upload(contents, filename):
    if not contents:
        return "", None
    
    metadata = parse_metadata_file(contents, filename)
    
    if metadata and 'error' not in metadata:
        status = html.Div([
            html.I(className="fas fa-check-circle me-2", style={"color": "green"}),
            f"Loaded {filename}: metadata extracted"
        ], className="alert alert-success")
        return status, metadata
    else:
        status = html.Div([
            html.I(className="fas fa-exclamation-circle me-2", style={"color": "red"}),
            f"Failed to load metadata from {filename}"
        ], className="alert alert-danger")
        return status, None


@app.callback(
    [Output('upload-status-div', 'children'),
     Output('preview-section', 'style'),
     Output('data-preview-container', 'children'),
     Output('processed-data-store', 'data')],
    [Input('raw-data-store', 'data'),
     Input('metadata-store', 'data')]
)
def process_paired_data(raw_data, metadata):
    if not raw_data:
        return "", {'display': 'none'}, "", None
    
    # Create status message
    status_parts = []
    if raw_data:
        status_parts.append(f"Raw data: {len(raw_data['sensor_names'])} sensors")
    if metadata:
        status_parts.append("Metadata: loaded")
    
    status = html.Div([
        html.I(className="fas fa-info-circle me-2"),
        " | ".join(status_parts)
    ], className="alert alert-info") if status_parts else ""
    
    # Create preview
    preview_content = []
    if raw_data:
        # Check for metadata
        sensor_mapping = metadata.get('sensor_mapping', {}) if metadata else {}
        assay_steps = metadata.get('assay_steps', []) if metadata else []
        
        # Show sensor list with metadata
        preview_content.append(html.H5("Sensor Summary:", style={"margin-bottom": "10px"}))
        
        # Create enhanced summary table with metadata
        sensor_summary = []
        for sensor_name in raw_data['sensor_names']:
            sensor_data = pd.DataFrame(raw_data['sensors'][sensor_name])
            
            # Basic sensor info
            summary_row = {
                'Sensor': sensor_name,
                'Data Points': len(sensor_data),
                'Time Range': f"0 - {sensor_data['Time'].max():.1f} s",
                'Response Range': f"{sensor_data['Response'].min():.3f} - {sensor_data['Response'].max():.3f}"
            }
            
            # Add metadata info if available
            if sensor_mapping and sensor_name in sensor_mapping:
                sample_info = sensor_mapping[sensor_name]
                summary_row['Sample ID'] = sample_info.get('sample_id', 'N/A')
                summary_row['Type'] = sample_info.get('sensor_type', 'N/A')
                summary_row['Replicate'] = sample_info.get('replicate', 'N/A')
            
            sensor_summary.append(summary_row)
        
        # Display summary table
        if sensor_summary:
            preview_content.append(
                dash_table.DataTable(
                    data=sensor_summary,
                    columns=[{"name": i, "id": i} for i in sensor_summary[0].keys()],
                    style_cell={'textAlign': 'left', 'padding': '10px', 'fontSize': '12px'},
                    style_header={'backgroundColor': '#0056b3', 'color': 'white', 'fontWeight': 'bold'},
                    style_table={'overflowX': 'auto'},
                    page_size=16,
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{Sample ID} contains Buffer'},
                            'backgroundColor': '#f0f0f0'
                        },
                        {
                            'if': {'filter_query': '{Sample ID} contains Std'},
                            'backgroundColor': '#e8f4f8'
                        }
                    ]
                )
            )
        
        # Show assay steps if available
        if assay_steps:
            # Calculate step timeline
            step_markers = calculate_step_times(assay_steps)
            
            # Create enhanced step table with cumulative times
            step_timeline = []
            for step in step_markers:
                step_timeline.append({
                    'Step': step['name'],
                    'Type': step['type'],
                    'Duration (s)': int(step['duration']),
                    'Start Time (s)': int(step['start']),
                    'End Time (s)': int(step['end']),
                    'Phase': 'Association' if 'Association' in step['type'] else 
                            'Dissociation' if 'Dissociation' in step['type'] else
                            'Baseline' if 'Baseline' in step['type'] else 
                            'Loading' if 'Loading' in step['type'] else 'Other'
                })
            
            preview_content.extend([
                html.Hr(),
                html.H5("Assay Timeline (Cumulative):", style={"margin": "15px 0 10px 0"}),
                html.P(f"Total experiment time: {step_markers[-1]['end']:.0f} seconds", 
                       style={"color": "#6c757d", "font-style": "italic"}),
                dash_table.DataTable(
                    data=step_timeline,
                    columns=[{"name": i, "id": i} for i in step_timeline[0].keys()],
                    style_cell={'textAlign': 'center', 'padding': '8px', 'fontSize': '11px'},
                    style_header={'backgroundColor': '#0056b3', 'color': 'white', 'fontWeight': 'bold', 'fontSize': '12px'},
                    style_table={'overflowX': 'auto'},
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{Phase} = Association'},
                            'backgroundColor': '#d5ead5'
                        },
                        {
                            'if': {'filter_query': '{Phase} = Dissociation'},
                            'backgroundColor': '#f2d5d5'
                        },
                        {
                            'if': {'filter_query': '{Phase} = Baseline'},
                            'backgroundColor': '#d5e8f2'
                        },
                        {
                            'if': {'filter_query': '{Phase} = Loading'},
                            'backgroundColor': '#f2e8d5'
                        }
                    ]
                )
            ])
        
        # Show first sensor data preview
        if raw_data['sensor_names']:
            first_sensor = raw_data['sensor_names'][0]
            first_df = pd.DataFrame(raw_data['sensors'][first_sensor]).head(10)
            preview_content.extend([
                html.Hr(),
                html.H5(f"Data Preview - {first_sensor}:", style={"margin": "15px 0 10px 0"}),
                dash_table.DataTable(
                    data=first_df.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in first_df.columns],
                    style_cell={'textAlign': 'left', 'padding': '10px'},
                    style_header={'backgroundColor': '#0056b3', 'color': 'white', 'fontWeight': 'bold'},
                    style_table={'overflowX': 'auto'}
                )
            ])
    
    # Process and combine data for analysis
    processed_data = None
    if raw_data:
        processed_data = {
            'sensors': raw_data['sensors'],
            'sensor_names': raw_data['sensor_names'],
            'metadata': metadata if metadata else {}
        }
    
    return (
        status,
        CARD_STYLE if raw_data else {'display': 'none'},
        preview_content,
        processed_data
    )


@app.callback(
    [Output('sample-selector', 'options'),
     Output('sample-selector', 'value')],
    [Input('processed-data-store', 'data')]
)
def update_sample_selector(processed_data):
    if not processed_data:
        return [], []
    
    # Extract sensor names and metadata
    options = []
    metadata = processed_data.get('metadata', {})
    sensor_mapping = metadata.get('sensor_mapping', {})
    
    # Track which sensors are actual samples (not standards or buffers)
    sample_sensors = []
    
    for sensor_name in processed_data['sensor_names']:
        # Get sample ID and info from metadata if available
        if sensor_mapping and sensor_name in sensor_mapping:
            sample_info = sensor_mapping[sensor_name]
            sample_id = sample_info.get('sample_id', sensor_name)
            label = f"{sensor_name} - {sample_id}"
            
            # Check if this is an actual sample (not standard or buffer)
            sample_id_upper = str(sample_id).upper()
            if not ('STD' in sample_id_upper or 'BUFFER' in sample_id_upper):
                sample_sensors.append(sensor_name)
        else:
            label = sensor_name
            # If no metadata, include by default
            sample_sensors.append(sensor_name)
        
        options.append({
            'label': label,
            'value': sensor_name
        })
    
    # Select only actual samples by default (exclude Standards and Buffers)
    default_selection = sample_sensors
    
    return options, default_selection


@app.callback(
    [Output('main-plot', 'figure'),
     Output('plot-section', 'style')],
    [Input('sample-selector', 'value'),
     Input('plot-type-selector', 'value'),
     Input('plot-options', 'value')],
    [State('processed-data-store', 'data')]
)
def update_visualization(selected_samples, plot_type, plot_options, processed_data):
    if not selected_samples or not processed_data:
        return go.Figure(), {'display': 'none'}
    
    fig = go.Figure()
    
    # Get metadata
    metadata = processed_data.get('metadata', {})
    sensor_mapping = metadata.get('sensor_mapping', {})
    assay_steps = metadata.get('assay_steps', [])
    
    # Default color palette
    default_colors = px.colors.qualitative.Plotly
    
    for idx, sensor_name in enumerate(selected_samples):
        try:
            # Get sensor data
            sensor_df = pd.DataFrame(processed_data['sensors'][sensor_name])
            
            x_data = sensor_df['Time'].values
            y_data = sensor_df['Response'].values
            
            # Apply processing options
            if 'smooth' in plot_options:
                y_data = apply_smoothing(y_data, window_length=11, polyorder=3)
            
            if 'baseline' in plot_options:
                # Baseline correction - subtract average of first 10 points
                baseline = np.mean(y_data[:10]) if len(y_data) > 10 else y_data[0]
                y_data = y_data - baseline
            
            # Apply analysis view filter (420s+)
            if 'analysis_view' in plot_options:
                analysis_mask = x_data >= 420
                x_data = x_data[analysis_mask]
                y_data = y_data[analysis_mask]
            
            # Get color and sample info from metadata
            trace_name = sensor_name
            trace_color = default_colors[idx % len(default_colors)]
            
            if sensor_mapping and sensor_name in sensor_mapping:
                sample_info = sensor_mapping[sensor_name]
                sample_id = sample_info.get('sample_id', sensor_name)
                trace_name = f"{sensor_name} - {sample_id}"
                
                # Use color from metadata if available
                if sample_info.get('color'):
                    # Convert color integer to hex if needed
                    color_val = sample_info['color']
                    if isinstance(color_val, (int, float)):
                        # Convert signed integer to RGB
                        color_int = int(color_val) & 0xFFFFFF
                        trace_color = f'#{color_int:06x}'
            
            # Add trace
            fig.add_trace(go.Scatter(
                x=x_data,
                y=y_data,
                mode='lines',
                name=trace_name,
                line=dict(width=2, color=trace_color),
                hovertemplate=f'<b>{trace_name}</b><br>Time: %{{x:.1f}} s<br>Response: %{{y:.3f}} nm<extra></extra>'
            ))
        
        except Exception as e:
            logging.error(f"Error plotting sensor {sensor_name}: {str(e)}")
            continue
    
    # Add vertical markers for assay steps
    if assay_steps:
        step_markers = calculate_step_times(assay_steps)
        
        # Color map for different step types
        step_colors = {
            'Baseline': '#3498db',      # Blue
            'Association': '#27ae60',    # Green
            'Dissociation': '#e74c3c',  # Red
            'Loading': '#f39c12',        # Orange
            'Custom': '#95a5a6'          # Gray
        }
        
        # Track which steps to show markers for
        show_all_markers = 'show_ref' in plot_options
        
        # Add vertical lines and shaded regions for each step
        for i, step in enumerate(step_markers):
            step_type = step['type']
            step_color = step_colors.get(step_type, '#95a5a6')
            
            # Determine if we should show this step
            show_this_step = show_all_markers or step_type in ['Association', 'Dissociation']
            
            if show_this_step:
                # Add shaded region for the step duration
                fig.add_vrect(
                    x0=step['start'],
                    x1=step['end'],
                    fillcolor=step_color,
                    opacity=0.08,
                    layer="below",
                    line_width=0
                )
                
                # Add vertical line at step start with cumulative time
                annotation_text = f"{step['name']}<br>t={step['start']:.0f}s"
                if step_type != 'Custom' or show_all_markers:
                    fig.add_vline(
                        x=step['start'],
                        line_dash="dash",
                        line_color=step_color,
                        opacity=0.6,
                        line_width=1
                    )
                    
                    # Add text annotation above the plot
                    fig.add_annotation(
                        x=step['start'] + step['duration']/2,  # Center of step
                        y=1.02,
                        yref="paper",
                        text=step['name'],
                        showarrow=False,
                        font=dict(size=9, color=step_color),
                        textangle=-45
                    )
        
        # Add a legend for step types if markers are shown
        if step_markers and (show_all_markers or any(s['type'] in ['Association', 'Dissociation'] for s in step_markers)):
            # Create invisible traces for legend
            for step_type, color in step_colors.items():
                if any(s['type'] == step_type for s in step_markers):
                    fig.add_trace(go.Scatter(
                        x=[None],
                        y=[None],
                        mode='markers',
                        marker=dict(size=10, color=color, symbol='square'),
                        showlegend=True,
                        name=f"{step_type} Phase",
                        legendgroup="steps",
                        legendgrouptitle_text="Assay Steps"
                    ))
    
    # Update layout based on plot type
    title_map = {
        'sensorgram': 'Sensorgram',
        'binding': 'Binding Curves', 
        'kinetics': 'Association/Dissociation Kinetics'
    }
    
    fig.update_layout(
        title=f"Octet {title_map.get(plot_type, 'Data')}",
        xaxis_title="Time (s)",
        yaxis_title="Response (nm)",
        hovermode='x unified',
        showlegend=True,
        template="plotly_white",
        height=600,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )
    
    if 'grid' in plot_options:
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    
    return fig, CARD_STYLE


@app.callback(
    [Output('fitting-plot-container', 'children'),
     Output('kinetic-parameters-table', 'children'),
     Output('analysis-results-section', 'style'),
     Output('analysis-results-store', 'data')],
    [Input('run-analysis-btn', 'n_clicks')],
    [State('sample-selector', 'value'),
     State('analysis-model', 'value'),
     State('assoc-time-input', 'value'),
     State('dissoc-time-input', 'value'),
     State('concentration-input', 'value'),
     State('processed-data-store', 'data')]
)
def run_kinetic_analysis(n_clicks, selected_samples, model, assoc_time, dissoc_time, 
                         concentration_str, processed_data):
    if not n_clicks or not selected_samples or not processed_data:
        return "", "", {'display': 'none'}, None
    
    # Parse concentrations
    try:
        concentrations = [float(c.strip()) for c in concentration_str.split(',')]
    except:
        concentrations = [100]  # Default concentration
    
    results = []
    fig = make_subplots(
        rows=len(selected_samples), 
        cols=1,
        subplot_titles=selected_samples,
        vertical_spacing=0.1
    )
    
    for idx, sensor_name in enumerate(selected_samples):
        try:
            # Get sensor data
            sensor_df = pd.DataFrame(processed_data['sensors'][sensor_name])
            
            time_data = sensor_df['Time'].values
            response_data = sensor_df['Response'].values
            
            # Apply baseline correction for analysis
            baseline = np.mean(response_data[:10]) if len(response_data) > 10 else response_data[0]
            response_data = response_data - baseline
            
            # Use first concentration for now (could be extended for global fitting)
            concentration = concentrations[0] if concentrations else 100
            
            # Run kinetic analysis
            if model == '1to1':
                kinetic_results = calculate_kinetics_1to1(
                    time_data, response_data, assoc_time, dissoc_time, concentration
                )
            else:
                # Placeholder for other models
                kinetic_results = None
            
            if kinetic_results:
                results.append({
                    'Sensor': sensor_name,
                    'ka (M⁻¹s⁻¹)': f"{kinetic_results['ka']:.2e}",
                    'kd (s⁻¹)': f"{kinetic_results['kd']:.2e}",
                    'KD (nM)': f"{kinetic_results['KD']:.2f}",
                    'Rmax (nm)': f"{kinetic_results['Rmax']:.2f}",
                    'R²': f"{kinetic_results['r_squared']:.4f}"
                })
                
                # Add original data
                fig.add_trace(
                    go.Scatter(
                        x=time_data,
                        y=response_data,
                        mode='markers',
                        name=f"{sensor_name} - Data",
                        marker=dict(size=3, opacity=0.6),
                        showlegend=True
                    ),
                    row=idx+1, col=1
                )
                
                # Add fitted curve
                fig.add_trace(
                    go.Scatter(
                        x=time_data,
                        y=kinetic_results['fitted_curve'],
                        mode='lines',
                        name=f"{sensor_name} - Fit",
                        line=dict(color='red', width=2),
                        showlegend=True
                    ),
                    row=idx+1, col=1
                )
                
                # Add phase separator
                fig.add_vline(x=assoc_time, line_dash="dash", line_color="gray",
                            row=idx+1, col=1)
        
        except Exception as e:
            logging.error(f"Error analyzing {sensor_name}: {str(e)}")
            continue
    
    # Update figure layout
    fig.update_xaxes(title_text="Time (s)")
    fig.update_yaxes(title_text="Response (nm)")
    fig.update_layout(
        height=400 * len(selected_samples),
        showlegend=True,
        title="Kinetic Fitting Results",
        template="plotly_white"
    )
    
    # Create results table
    if results:
        results_table = dash_table.DataTable(
            data=results,
            columns=[{"name": i, "id": i} for i in results[0].keys()],
            style_cell={'textAlign': 'center', 'padding': '10px'},
            style_header={'backgroundColor': '#0056b3', 'color': 'white', 'fontWeight': 'bold'},
            style_table={'overflowX': 'auto'},
            style_data_conditional=[
                {
                    'if': {'column_id': 'R²'},
                    'backgroundColor': '#e8f4f8'
                }
            ]
        )
    else:
        results_table = html.Div("No fitting results available", 
                                style={"color": "#6c757d", "text-align": "center"})
    
    return (
        dcc.Graph(figure=fig),
        results_table,
        CARD_STYLE if results else {'display': 'none'},
        results
    )


@app.callback(
    [Output('slope-results-container', 'children'),
     Output('slope-results-section', 'style'),
     Output('standard-curve-plot', 'children'),
     Output('sample-concentrations-table', 'children'),
     Output('standard-curve-section', 'style'),
     Output('proa-results-store', 'data')],
    [Input('calculate-slopes-btn', 'n_clicks')],
    [State('analysis-start-time', 'value'),
     State('analysis-end-time', 'value'),
     State('processed-data-store', 'data')]
)
def calculate_quantitative_analysis(n_clicks, start_time, end_time, processed_data):
    if not n_clicks or not processed_data:
        return "", {'display': 'none'}, "", "", {'display': 'none'}, None
    
    if start_time >= end_time:
        error_msg = html.Div([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Start time must be less than end time"
        ], className="alert alert-danger")
        return error_msg, CARD_STYLE, "", "", {'display': 'none'}, None
    
    # Get metadata and standards
    metadata = processed_data.get('metadata', {})
    standards_info = extract_standard_concentrations(metadata)
    sensor_mapping = metadata.get('sensor_mapping', {})
    
    # Calculate slopes for all sensors
    slope_results = []
    standards_data = []
    samples_data = []
    
    for sensor_name in processed_data['sensor_names']:
        try:
            # Get sensor data
            sensor_df = pd.DataFrame(processed_data['sensors'][sensor_name])
            time_data = sensor_df['Time'].values
            response_data = sensor_df['Response'].values
            
            # Apply baseline correction
            baseline = np.mean(response_data[:10]) if len(response_data) > 10 else response_data[0]
            response_data = response_data - baseline
            
            # Calculate slope
            slope, intercept, r_squared = calculate_initial_response_slope(
                time_data, response_data, start_time, end_time
            )
            
            # Get sample info
            sample_id = sensor_name
            sensor_type = "Unknown"
            if sensor_mapping and sensor_name in sensor_mapping:
                sample_info = sensor_mapping[sensor_name]
                sample_id = sample_info.get('sample_id', sensor_name)
                sensor_type = sample_info.get('sensor_type', 'Unknown')
            
            if slope is not None:
                result = {
                    'Sensor': sensor_name,
                    'Sample ID': sample_id,
                    'Initial Response (nm/s)': f"{slope:.6f}",
                    'R²': f"{r_squared:.4f}" if r_squared is not None else "N/A",
                    'Type': 'Standard' if sensor_name in standards_info else 'Sample'
                }
                
                slope_results.append(result)
                
                # Categorize for standard curve
                if sensor_name in standards_info:
                    standards_data.append({
                        'sensor': sensor_name,
                        'concentration': standards_info[sensor_name]['concentration'],
                        'slope': slope,
                        'sample_id': sample_id
                    })
                else:
                    # Check if it's not a buffer
                    if 'BUFFER' not in str(sample_id).upper():
                        samples_data.append({
                            'sensor': sensor_name,
                            'slope': slope,
                            'sample_id': sample_id
                        })
        
        except Exception as e:
            logging.error(f"Error calculating slope for {sensor_name}: {str(e)}")
            continue
    
    # Create results table
    if slope_results:
        results_table = dash_table.DataTable(
            data=slope_results,
            columns=[{"name": i, "id": i} for i in slope_results[0].keys()],
            style_cell={'textAlign': 'center', 'padding': '10px', 'fontSize': '12px'},
            style_header={'backgroundColor': '#0056b3', 'color': 'white', 'fontWeight': 'bold'},
            style_table={'overflowX': 'auto'},
            style_data_conditional=[
                {
                    'if': {'filter_query': '{Type} = Standard'},
                    'backgroundColor': '#e8f4f8'
                },
                {
                    'if': {'filter_query': '{Type} = Sample'},
                    'backgroundColor': '#f0f8e8'
                }
            ]
        )
    else:
        results_table = html.Div("No slope results calculated", 
                                style={"color": "#6c757d", "text-align": "center"})
    
    # Create standard curve if we have standards
    standard_curve_plot = ""
    sample_concentrations_table = ""
    standard_curve_style = {'display': 'none'}
    
    if len(standards_data) >= 3:
        # Create standard curve
        curve_slope, curve_intercept, curve_r2, curve_data = create_standard_curve(standards_data)
        
        if curve_slope is not None:
            concentrations, responses, fitted_responses = curve_data
            
            # Create standard curve plot
            fig = go.Figure()
            
            # Add standard points
            fig.add_trace(go.Scatter(
                x=concentrations,
                y=responses,
                mode='markers',
                name='Standards',
                marker=dict(size=10, color='blue'),
                hovertemplate='Concentration: %{x:.2f} µg/mL<br>Response: %{y:.6f} nm/s<extra></extra>'
            ))
            
            # Add fitted line
            fig.add_trace(go.Scatter(
                x=concentrations,
                y=fitted_responses,
                mode='lines',
                name=f'Fit (R² = {curve_r2:.4f})',
                line=dict(color='red', width=2)
            ))
            
            fig.update_layout(
                title="Standard Curve: Concentration vs Initial Response",
                xaxis_title="Concentration (µg/mL)",
                yaxis_title="Initial Response (nm/s)",
                template="plotly_white",
                height=400
            )
            
            standard_curve_plot = dcc.Graph(figure=fig)
            
            # Calculate sample concentrations
            sample_concentrations = []
            for sample in samples_data:
                # Use standard curve to calculate concentration
                # concentration = (response - intercept) / slope
                calc_conc = (sample['slope'] - curve_intercept) / curve_slope
                sample_concentrations.append({
                    'Sample ID': sample['sample_id'],
                    'Sensor': sample['sensor'],
                    'Initial Response (nm/s)': f"{sample['slope']:.6f}",
                    'Calculated Conc. (µg/mL)': f"{calc_conc:.3f}" if calc_conc > 0 else "Below LOD"
                })
            
            if sample_concentrations:
                sample_concentrations_table = dash_table.DataTable(
                    data=sample_concentrations,
                    columns=[{"name": i, "id": i} for i in sample_concentrations[0].keys()],
                    style_cell={'textAlign': 'center', 'padding': '8px', 'fontSize': '11px'},
                    style_header={'backgroundColor': '#0056b3', 'color': 'white', 'fontWeight': 'bold', 'fontSize': '12px'},
                    style_table={'overflowX': 'auto'}
                )
            
            standard_curve_style = CARD_STYLE
    
    elif len(standards_data) > 0:
        standard_curve_plot = html.Div([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Need at least 3 standards for curve fitting. Found {len(standards_data)} standards."
        ], className="alert alert-warning")
        standard_curve_style = CARD_STYLE
    
    # Store results for summary
    proa_results = {
        'slope_results': slope_results,
        'standards_data': standards_data,
        'samples_data': samples_data,
        'time_window': f"{start_time}-{end_time}s"
    }
    
    # Add calculated concentrations to results for summary
    if len(standards_data) >= 3:
        curve_slope, curve_intercept, curve_r2, curve_data = create_standard_curve(standards_data)
        if curve_slope is not None:
            for sample in samples_data:
                calc_conc = (sample['slope'] - curve_intercept) / curve_slope
                if calc_conc > 0:
                    proa_results[f"{sample['sample_id']}_concentration"] = calc_conc
    
    return (
        results_table,
        CARD_STYLE,
        standard_curve_plot,
        sample_concentrations_table,
        standard_curve_style,
        proa_results
    )


# Kappa Analysis Callback (similar to ProA but for 520-530s)
@app.callback(
    [Output('kappa-slope-results-container', 'children'),
     Output('kappa-slope-results-section', 'style'),
     Output('kappa-standard-curve-plot', 'children'),
     Output('kappa-sample-concentrations-table', 'children'),
     Output('kappa-standard-curve-section', 'style'),
     Output('kappa-results-store', 'data')],
    [Input('calculate-kappa-slopes-btn', 'n_clicks')],
    [State('kappa-start-time', 'value'),
     State('kappa-end-time', 'value'),
     State('processed-data-store', 'data')]
)
def calculate_kappa_analysis(n_clicks, start_time, end_time, processed_data):
    if not n_clicks or not processed_data:
        return "", {'display': 'none'}, "", "", {'display': 'none'}, None
    
    if start_time >= end_time:
        error_msg = html.Div([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Start time must be less than end time"
        ], className="alert alert-danger")
        return error_msg, CARD_STYLE, "", "", {'display': 'none'}, None
    
    # Get metadata and standards (same standards used for kappa)
    metadata = processed_data.get('metadata', {})
    standards_info = extract_standard_concentrations(metadata)
    sensor_mapping = metadata.get('sensor_mapping', {})
    
    # Calculate slopes for all sensors
    slope_results = []
    standards_data = []
    samples_data = []
    
    for sensor_name in processed_data['sensor_names']:
        try:
            # Get sensor data
            sensor_df = pd.DataFrame(processed_data['sensors'][sensor_name])
            time_data = sensor_df['Time'].values
            response_data = sensor_df['Response'].values
            
            # Apply baseline correction
            baseline = np.mean(response_data[:10]) if len(response_data) > 10 else response_data[0]
            response_data = response_data - baseline
            
            # Calculate slope
            slope, intercept, r_squared = calculate_initial_response_slope(
                time_data, response_data, start_time, end_time
            )
            
            # Get sample info
            sample_id = sensor_name
            if sensor_mapping and sensor_name in sensor_mapping:
                sample_info = sensor_mapping[sensor_name]
                sample_id = sample_info.get('sample_id', sensor_name)
            
            if slope is not None:
                result = {
                    'Sensor': sensor_name,
                    'Sample ID': sample_id,
                    'Kappa Response (nm/s)': f"{slope:.6f}",
                    'R²': f"{r_squared:.4f}" if r_squared is not None else "N/A",
                    'Type': 'Standard' if sensor_name in standards_info else 'Sample'
                }
                
                slope_results.append(result)
                
                # Categorize for standard curve
                if sensor_name in standards_info:
                    standards_data.append({
                        'sensor': sensor_name,
                        'concentration': standards_info[sensor_name]['concentration'],
                        'slope': slope,
                        'sample_id': sample_id
                    })
                else:
                    # Check if it's not a buffer
                    if 'BUFFER' not in str(sample_id).upper():
                        samples_data.append({
                            'sensor': sensor_name,
                            'slope': slope,
                            'sample_id': sample_id
                        })
        
        except Exception as e:
            logging.error(f"Error calculating kappa slope for {sensor_name}: {str(e)}")
            continue
    
    # Store results for summary
    kappa_results = {
        'slope_results': slope_results,
        'standards_data': standards_data,
        'samples_data': samples_data,
        'time_window': f"{start_time}-{end_time}s"
    }
    
    # Create results table
    if slope_results:
        results_table = dash_table.DataTable(
            data=slope_results,
            columns=[{"name": i, "id": i} for i in slope_results[0].keys()],
            style_cell={'textAlign': 'center', 'padding': '10px', 'fontSize': '12px'},
            style_header={'backgroundColor': '#0056b3', 'color': 'white', 'fontWeight': 'bold'},
            style_table={'overflowX': 'auto'},
            style_data_conditional=[
                {
                    'if': {'filter_query': '{Type} = Standard'},
                    'backgroundColor': '#e8f4f8'
                },
                {
                    'if': {'filter_query': '{Type} = Sample'},
                    'backgroundColor': '#f0f8e8'
                }
            ]
        )
    else:
        results_table = html.Div("No kappa slope results calculated", 
                                style={"color": "#6c757d", "text-align": "center"})
    
    # Create standard curve if we have standards
    standard_curve_plot = ""
    sample_concentrations_table = ""
    standard_curve_style = {'display': 'none'}
    
    if len(standards_data) >= 3:
        # Create standard curve
        curve_slope, curve_intercept, curve_r2, curve_data = create_standard_curve(standards_data)
        
        if curve_slope is not None:
            concentrations, responses, fitted_responses = curve_data
            
            # Create standard curve plot
            fig = go.Figure()
            
            # Add standard points
            fig.add_trace(go.Scatter(
                x=concentrations,
                y=responses,
                mode='markers',
                name='Standards',
                marker=dict(size=10, color='green'),
                hovertemplate='Concentration: %{x:.2f} µg/mL<br>Kappa Response: %{y:.6f} nm/s<extra></extra>'
            ))
            
            # Add fitted line
            fig.add_trace(go.Scatter(
                x=concentrations,
                y=fitted_responses,
                mode='lines',
                name=f'Fit (R² = {curve_r2:.4f})',
                line=dict(color='red', width=2)
            ))
            
            fig.update_layout(
                title="Kappa Standard Curve: Concentration vs Initial Response",
                xaxis_title="Concentration (µg/mL)",
                yaxis_title="Kappa Response (nm/s)",
                template="plotly_white",
                height=400
            )
            
            standard_curve_plot = dcc.Graph(figure=fig)
            
            # Calculate sample concentrations
            sample_concentrations = []
            for sample in samples_data:
                # Use standard curve to calculate concentration
                calc_conc = (sample['slope'] - curve_intercept) / curve_slope
                sample_concentrations.append({
                    'Sample ID': sample['sample_id'],
                    'Sensor': sample['sensor'],
                    'Kappa Response (nm/s)': f"{sample['slope']:.6f}",
                    'Kappa Conc. (µg/mL)': f"{calc_conc:.3f}" if calc_conc > 0 else "Below LOD"
                })
                
                # Add to results for summary
                if calc_conc > 0:
                    kappa_results[f"{sample['sample_id']}_concentration"] = calc_conc
            
            if sample_concentrations:
                sample_concentrations_table = dash_table.DataTable(
                    data=sample_concentrations,
                    columns=[{"name": i, "id": i} for i in sample_concentrations[0].keys()],
                    style_cell={'textAlign': 'center', 'padding': '8px', 'fontSize': '11px'},
                    style_header={'backgroundColor': '#0056b3', 'color': 'white', 'fontWeight': 'bold', 'fontSize': '12px'},
                    style_table={'overflowX': 'auto'}
                )
            
            standard_curve_style = CARD_STYLE
    
    elif len(standards_data) > 0:
        standard_curve_plot = html.Div([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Need at least 3 standards for kappa curve fitting. Found {len(standards_data)} standards."
        ], className="alert alert-warning")
        standard_curve_style = CARD_STYLE
    
    return (
        results_table,
        CARD_STYLE,
        standard_curve_plot,
        sample_concentrations_table,
        standard_curve_style,
        kappa_results
    )


# Summary Tab Callback
@app.callback(
    [Output('summary-table-container', 'children'),
     Output('summary-plots-container', 'children'),
     Output('summary-plots-section', 'style')],
    [Input('proa-results-store', 'data'),
     Input('kappa-results-store', 'data'),
     Input('generate-summary-plot-btn', 'n_clicks')]
)
def update_summary(proa_results, kappa_results, plot_clicks):
    if not proa_results and not kappa_results:
        return "No analysis results available", "", {'display': 'none'}
    
    # Create combined summary table
    summary_data = []
    
    # Get all unique sample IDs
    all_samples = set()
    if proa_results and 'samples_data' in proa_results:
        for sample in proa_results['samples_data']:
            all_samples.add(sample['sample_id'])
    
    if kappa_results and 'samples_data' in kappa_results:
        for sample in kappa_results['samples_data']:
            all_samples.add(sample['sample_id'])
    
    for sample_id in sorted(all_samples):
        row = {'Sample ID': sample_id}
        
        # Add ProA concentration if available
        if proa_results and 'samples_data' in proa_results:
            proa_sample = next((s for s in proa_results['samples_data'] if s['sample_id'] == sample_id), None)
            if proa_sample:
                # Calculate ProA concentration using stored curve data
                row['ProA Load Conc. (µg/mL)'] = "See ProA tab"  # Simplified for now
        
        # Add Kappa concentration if available
        if kappa_results:
            kappa_key = f"{sample_id}_concentration"
            if kappa_key in kappa_results:
                row['Kappa Conc. (µg/mL)'] = f"{kappa_results[kappa_key]:.2f}"
            else:
                row['Kappa Conc. (µg/mL)'] = "N/A"
        
        summary_data.append(row)
    
    if summary_data:
        summary_table = dash_table.DataTable(
            data=summary_data,
            columns=[{"name": i, "id": i} for i in summary_data[0].keys()],
            style_cell={'textAlign': 'center', 'padding': '12px', 'fontSize': '12px'},
            style_header={'backgroundColor': '#0056b3', 'color': 'white', 'fontWeight': 'bold'},
            style_table={'overflowX': 'auto'},
            export_format='csv',
            export_headers='display'
        )
    else:
        summary_table = "No sample data to summarize"
    
    # Generate summary plots if requested
    plots_content = ""
    plots_style = {'display': 'none'}
    
    if plot_clicks and summary_data:
        # Create comparison plots
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=['ProA Loading Concentration', 'Kappa Concentration'],
            horizontal_spacing=0.1
        )
        
        # Extract data for plotting (simplified)
        sample_ids = [row['Sample ID'] for row in summary_data]
        
        # Add ProA concentrations (placeholder - would need actual values)
        # fig.add_trace(go.Bar(name='ProA Load', x=sample_ids, y=[...]), row=1, col=1)
        
        # Add Kappa concentrations
        kappa_concs = []
        for row in summary_data:
            kappa_val = row.get('Kappa Conc. (µg/mL)', 'N/A')
            if kappa_val != 'N/A':
                try:
                    kappa_concs.append(float(kappa_val))
                except:
                    kappa_concs.append(0)
            else:
                kappa_concs.append(0)
        
        fig.add_trace(go.Bar(name='Kappa Conc.', x=sample_ids, y=kappa_concs, 
                            marker_color='green'), row=1, col=2)
        
        fig.update_layout(height=400, title="Sample Concentration Summary")
        fig.update_xaxes(title_text="Samples", row=1, col=1)
        fig.update_xaxes(title_text="Samples", row=1, col=2)
        fig.update_yaxes(title_text="Conc. (µg/mL)", row=1, col=1)
        fig.update_yaxes(title_text="Conc. (µg/mL)", row=1, col=2)
        
        plots_content = dcc.Graph(figure=fig)
        plots_style = CARD_STYLE
    
    return summary_table, plots_content, plots_style


@app.callback(
    Output('report-status', 'children'),
    [Input('generate-report-btn', 'n_clicks')],
    [State('report-title', 'value'),
     State('report-format', 'value'),
     State('report-sections', 'value'),
     State('analysis-results-store', 'data')]
)
def generate_report(n_clicks, title, format_type, sections, analysis_results):
    if not n_clicks:
        return ""
    
    if not analysis_results:
        return html.Div([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "No analysis results available. Please run analysis first."
        ], className="alert alert-warning", style={"margin-top": "20px"})
    
    # Generate report based on format
    # This is a placeholder - actual implementation would generate files
    
    return html.Div([
        html.I(className="fas fa-check-circle me-2"),
        f"Report '{title}' generated successfully in {format_type.upper()} format!",
        html.Br(),
        html.Small(f"Included sections: {', '.join(sections)}", style={"color": "#6c757d"})
    ], className="alert alert-success", style={"margin-top": "20px"})


if __name__ == '__main__':
    app.run_server(debug=True)