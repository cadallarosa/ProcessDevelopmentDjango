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
    
    # Upload Data Button (Small, top-right)
    html.Div([
        html.Button([
            html.I(className="fas fa-upload me-1"),
            "Upload Data"
        ], id="upload-modal-btn", className="btn btn-primary btn-sm",
           style={"float": "right", "margin-bottom": "10px"})
    ], style={"margin-bottom": "5px"}),
    
    html.Div(style={"clear": "both"}),  # Clear float
    
    # Upload Modal
    dbc.Modal([
        dbc.ModalHeader([
            html.H4([
                html.I(className="fas fa-file-upload me-2"),
                "Upload Octet Data Files"
            ], style={"color": "#0056b3"})
        ]),
        dbc.ModalBody([
            dbc.Row([
                # Raw Data Upload
                dbc.Col([
                    html.H5("Raw Data File", style={"margin-bottom": "10px"}),
                    dcc.Upload(
                        id='upload-raw-data',
                        children=html.Div([
                            html.I(className="fas fa-chart-line fa-2x",
                                   style={"color": "#0056b3", "margin-bottom": "10px"}),
                            html.Br(),
                            html.Strong("Drop raw data file here")
                        ]),
                        style={**UPLOAD_STYLE, 'height': '100px', 'lineHeight': '100px'},
                        multiple=False,
                        accept='.xls,.txt,.tsv'
                    ),
                    html.Div(id='raw-upload-status', style={"margin-top": "15px"})
                ], md=6),
                
                # Metadata Upload
                dbc.Col([
                    html.H5("Metadata File", style={"margin-bottom": "10px"}),
                    dcc.Upload(
                        id='upload-metadata',
                        children=html.Div([
                            html.I(className="fas fa-info-circle fa-2x",
                                   style={"color": "#0056b3", "margin-bottom": "10px"}),
                            html.Br(),
                            html.Strong("Drop metadata file here")
                        ]),
                        style={**UPLOAD_STYLE, 'height': '100px', 'lineHeight': '100px'},
                        multiple=False,
                        accept='.xls,.xlsx'
                    ),
                    html.Div(id='metadata-upload-status', style={"margin-top": "15px"})
                ], md=6)
            ]),
            
            html.Div(id='upload-status-div', style={"margin-top": "20px"}),
            
            # Data Preview Section
            html.Div([
                html.H5([
                    html.I(className="fas fa-table me-2"),
                    "Data Preview"
                ], style={"color": "#0056b3", "margin-bottom": "15px"}),
                
                html.Div(id='data-preview-container')
            ], id='preview-section', style={'display': 'none', 'margin-top': '20px'})
        ]),
        dbc.ModalFooter([
            html.Button("Close", id="close-modal-btn", className="btn btn-secondary")
        ])
    ], id="upload-modal", is_open=True, size="xl"),
    
    # Sample Selection and Analysis Parameters Section (Compact)
    html.Div([
        # First Row - Sample Selection (full width) and Run Button
        dbc.Row([
            dbc.Col([
                html.Label("Sample Selection:", style={"font-weight": "bold", "margin-bottom": "3px", "font-size": "12px"}),
                dcc.Dropdown(
                    id='sample-selector',
                    multi=True,
                    placeholder="Select samples to analyze...",
                    style={"font-size": "12px"}
                )
            ], md=6),

            dbc.Col([
                dcc.Checklist(
                    id='plot-options',
                    options=[
                        {"label": " Ref Lines", "value": "show_ref"},
                        {"label": " Smooth", "value": "smooth"},
                        {"label": " Grid", "value": "grid"},
                        {"label": " 420s+", "value": "analysis_view"}
                    ],
                    value=["baseline", "grid", "analysis_view"],
                    inline=True,
                    style={"font-size": "11px", "margin-top": "20px"},
                    inputStyle={"margin-right": "6px", "margin-left": "12px"}
                ),
                # Hidden baseline option (always enabled)
                html.Div([
                    dcc.Checklist(
                        id='baseline-option',
                        options=[{"label": "Buffer Baseline Correction", "value": "baseline"}],
                        value=["baseline"],
                        style={"display": "none"}
                    )
                ])
            ], md=3),

            dbc.Col([
                dcc.Checklist(
                    id='include-standards-option',
                    options=[{"label": " Show Standards", "value": "include_standards"}],
                    value=[],
                    inline=True,
                    style={"font-size": "11px", "margin-top": "20px"},
                    inputStyle={"margin-right": "6px"}
                )
            ], md=1),

            dbc.Col([
                html.Button([
                    html.I(className="fas fa-play me-1"),
                    "Run Analysis"
                ], id='run-all-analysis-btn', className="btn btn-primary",
                   style={"width": "100%", "margin-top": "18px"})
            ], md=2)
        ], className="mb-2"),

        # Standards Selection Row
        dbc.Row([
            dbc.Col([
                html.Label("Standards for Curve (select which to include):",
                          style={"font-weight": "bold", "margin-bottom": "3px", "font-size": "12px"}),
                dcc.Dropdown(
                    id='standards-selector',
                    multi=True,
                    placeholder="All detected standards selected by default...",
                    style={"font-size": "12px"}
                )
            ], md=12)
        ], className="mb-3", id='standards-selection-row', style={'display': 'none'}),

        # Third Row - Analysis Parameters
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Label("ProA Loading", style={"font-weight": "bold", "color": "#28a745", "margin-bottom": "5px", "text-align": "center", "font-size": "12px"}),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Start", style={"font-size": "10px", "margin-bottom": "1px"}),
                            dcc.Input(id='proa-start', type="number", value=420, step=1, 
                                     style={"width": "100%", "font-size": "11px"})
                        ], md=6),
                        dbc.Col([
                            html.Label("Stop", style={"font-size": "10px", "margin-bottom": "1px"}),
                            dcc.Input(id='proa-end', type="number", value=430, step=1, 
                                     style={"width": "100%", "font-size": "11px"})
                        ], md=6)
                    ])
                ], style={"border": "2px solid #28a745", "border-radius": "6px", "padding": "6px", "background-color": "#f8f9fa"})
            ], md=4),
            
            dbc.Col([
                html.Div([
                    html.Label("%BB Analysis", style={"font-weight": "bold", "color": "#dc3545", "margin-bottom": "5px", "text-align": "center", "font-size": "12px"}),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Start", style={"font-size": "10px", "margin-bottom": "1px"}),
                            dcc.Input(id='bb-time1', type="number", value=440, step=1, 
                                     style={"width": "100%", "font-size": "11px"})
                        ], md=6),
                        dbc.Col([
                            html.Label("Stop", style={"font-size": "10px", "margin-bottom": "1px"}),
                            dcc.Input(id='bb-time2', type="number", value=450, step=1, 
                                     style={"width": "100%", "font-size": "11px"})
                        ], md=6)
                    ])
                ], style={"border": "2px solid #dc3545", "border-radius": "6px", "padding": "6px", "background-color": "#f8f9fa"})
            ], md=4),
            
            dbc.Col([
                html.Div([
                    html.Label("Kappa Concentration", style={"font-weight": "bold", "color": "#007bff", "margin-bottom": "5px", "text-align": "center", "font-size": "12px"}),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Start", style={"font-size": "10px", "margin-bottom": "1px"}),
                            dcc.Input(id='kappa-start', type="number", value=520, step=1, 
                                     style={"width": "100%", "font-size": "11px"})
                        ], md=6),
                        dbc.Col([
                            html.Label("Stop", style={"font-size": "10px", "margin-bottom": "1px"}),
                            dcc.Input(id='kappa-end', type="number", value=530, step=1, 
                                     style={"width": "100%", "font-size": "11px"})
                        ], md=6)
                    ])
                ], style={"border": "2px solid #007bff", "border-radius": "6px", "padding": "6px", "background-color": "#f8f9fa"})
            ], md=4)
        ])
    ], style={"border": "1px solid #dee2e6", "border-radius": "8px", "padding": "10px", "margin-bottom": "15px"}),  # More compact card
    
    # Content Tabs - Horizontal Layout using dcc.Tabs
    dcc.Tabs(id="content-tabs", value="graph-tab", style={'display': 'none'}, children=[
        # Graph Tab
        dcc.Tab(label="Graph", value="graph-tab", children=[
            html.Div([
                dcc.Graph(id='main-plot', style={'height': '650px'})
            ], style={"padding": "15px"})
        ]),
        
        # Results Table Tab
        dcc.Tab(label="Results Table", value="results-tab", children=[
            html.Div([
                html.Div([
                    html.Button([
                        html.I(className="fas fa-download me-2"),
                        "Export Results"
                    ], id='export-results-btn', className="btn btn-success btn-sm",
                       style={"float": "right", "margin-bottom": "10px"}),
                    html.Div(style={"clear": "both"})
                ]),
                html.Div(id='integrated-results-container')
            ], style={"padding": "15px"})
        ]),
        
        # Standard Curves Tab
        dcc.Tab(label="Standard Curves", value="std-curves-tab", children=[
            html.Div([
                dbc.Row([
                    # ProA Standard Curve
                    dbc.Col([
                        html.Div([
                            html.H5("ProA Loading", style={"color": "#28a745", "margin-bottom": "10px", "text-align": "center", "font-size": "16px"}),
                            dcc.Graph(id='proa-std-curve', style={'height': '500px'})
                        ], style={"border": "1px solid #28a745", "border-radius": "8px", "padding": "10px"})
                    ], md=4, id='proa-std-curve-section', style={'display': 'none'}),
                    
                    # %BB Standard Curve
                    dbc.Col([
                        html.Div([
                            html.H5("%BB Analysis", style={"color": "#dc3545", "margin-bottom": "10px", "text-align": "center", "font-size": "16px"}),
                            dcc.Graph(id='bb-std-curve', style={'height': '500px'})
                        ], style={"border": "1px solid #dc3545", "border-radius": "8px", "padding": "10px"})
                    ], md=4, id='bb-std-curve-section', style={'display': 'none'}),
                    
                    # Kappa Standard Curve
                    dbc.Col([
                        html.Div([
                            html.H5("Kappa Concentration", style={"color": "#007bff", "margin-bottom": "10px", "text-align": "center", "font-size": "16px"}),
                            dcc.Graph(id='kappa-std-curve', style={'height': '500px'})
                        ], style={"border": "1px solid #007bff", "border-radius": "8px", "padding": "10px"})
                    ], md=4, id='kappa-std-curve-section', style={'display': 'none'})
                ])
            ], id='standard-curves-section', style={"padding": "15px", 'display': 'none'})
        ])
    ]),
    
], style={"max-width": "95%", "margin": "0 auto", "padding": "20px"})


# Helper Functions
def parse_raw_octet_data(contents, filename):
    """Parse raw Octet data file (tab-delimited with time and response pairs)"""
    try:
        print(f"\n{'='*80}")
        print(f"DEBUG: Starting parse_raw_octet_data for file: {filename}")
        print(f"{'='*80}")

        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        print(f"DEBUG: Decoded file size: {len(decoded)} bytes")

        # Try to read as tab-delimited file
        df = None
        try:
            print("DEBUG: Attempting to read as UTF-8 CSV with tab delimiter...")
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8', errors='ignore')), sep='\t')
            print(f"DEBUG: Successfully read as UTF-8 CSV")
        except Exception as e:
            print(f"DEBUG: UTF-8 reading failed: {str(e)}")
            print("DEBUG: Attempting to read as BytesIO CSV with tab delimiter...")
            df = pd.read_csv(io.BytesIO(decoded), sep='\t')
            print(f"DEBUG: Successfully read as BytesIO CSV")

        print(f"\nDEBUG: DataFrame shape: {df.shape}")
        print(f"DEBUG: Number of columns: {len(df.columns)}")
        print(f"DEBUG: Number of rows: {len(df)}")
        print(f"\nDEBUG: Column names (first 10):")
        for idx, col in enumerate(df.columns[:10]):
            print(f"  [{idx}]: '{col}'")
        if len(df.columns) > 10:
            print(f"  ... and {len(df.columns) - 10} more columns")

        print(f"\nDEBUG: First 5 rows of data:")
        print(df.head())

        # Process the data - columns are in pairs (time, response)
        sensors_data = {}
        print(f"\nDEBUG: Processing sensor columns (expecting pairs)...")

        for i in range(0, len(df.columns)-1, 2):
            sensor_name = df.columns[i]
            next_col_name = df.columns[i+1] if i+1 < len(df.columns) else "N/A"

            print(f"\nDEBUG: Processing column pair [{i}, {i+1}]:")
            print(f"  Column {i} name: '{sensor_name}'")
            print(f"  Column {i+1} name: '{next_col_name}'")

            if 'Unnamed' not in sensor_name:
                print(f"  -> Processing sensor: {sensor_name}")
                time_col = df.iloc[:, i]
                response_col = df.iloc[:, i+1]

                # Clean data - remove NaN values
                valid_mask = ~(time_col.isna() | response_col.isna())
                valid_count = valid_mask.sum()
                total_count = len(valid_mask)

                print(f"  -> Valid data points: {valid_count}/{total_count}")
                print(f"  -> Time range: {time_col[valid_mask].min():.2f} to {time_col[valid_mask].max():.2f}")
                print(f"  -> Response range: {response_col[valid_mask].min():.4f} to {response_col[valid_mask].max():.4f}")

                sensors_data[sensor_name] = pd.DataFrame({
                    'Time': time_col[valid_mask].values,
                    'Response': response_col[valid_mask].values
                })
            else:
                print(f"  -> Skipping unnamed column")

        print(f"\n{'='*80}")
        print(f"DEBUG: Parsing complete!")
        print(f"DEBUG: Total sensors extracted: {len(sensors_data)}")
        print(f"DEBUG: Sensor names: {list(sensors_data.keys())}")
        print(f"{'='*80}\n")

        return sensors_data
    except Exception as e:
        print(f"\n{'!'*80}")
        print(f"ERROR: Exception in parse_raw_octet_data for {filename}")
        print(f"ERROR: {str(e)}")
        print(f"ERROR: Exception type: {type(e).__name__}")
        import traceback
        print(f"ERROR: Traceback:")
        traceback.print_exc()
        print(f"{'!'*80}\n")
        logging.error(f"Error parsing raw data {filename}: {str(e)}")
        return None


def parse_metadata_file(contents, filename):
    """Parse Octet metadata/ExcelReport file"""
    try:
        print(f"\n{'='*80}")
        print(f"DEBUG: Starting parse_metadata_file for file: {filename}")
        print(f"{'='*80}")

        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        print(f"DEBUG: Decoded file size: {len(decoded)} bytes")

        # Try different parsing methods
        metadata = {}

        # Try reading as Excel
        try:
            print("\nDEBUG: Attempting to read as Excel file...")
            excel_file = pd.ExcelFile(io.BytesIO(decoded))
            metadata['sheets'] = excel_file.sheet_names
            print(f"DEBUG: Successfully read as Excel file")
            print(f"DEBUG: Sheet names: {excel_file.sheet_names}")

            # Read all sheets to extract metadata
            for sheet_idx, sheet in enumerate(excel_file.sheet_names):
                print(f"\n  DEBUG: Processing sheet [{sheet_idx}]: '{sheet}'")
                df = pd.read_excel(io.BytesIO(decoded), sheet_name=sheet)
                print(f"  DEBUG: Sheet shape: {df.shape}")
                print(f"  DEBUG: Columns: {list(df.columns)}")
                print(f"  DEBUG: First 3 rows:")
                print(df.head(3))

                metadata[sheet] = df.to_dict('records')

                # Look for specific metadata tables
                columns_str = str(df.columns)
                print(f"  DEBUG: Checking for 'Sensor' in columns: {'Sensor' in columns_str}")
                print(f"  DEBUG: Checking for 'Sample ID' in columns: {'Sample ID' in columns_str}")

                if 'Sensor' in columns_str and 'Sample ID' in columns_str:
                    # This is likely the sensor/sample mapping table
                    print(f"  -> Found sensor/sample mapping table!")
                    metadata['sensor_info'] = df.to_dict('records')

                    # Check if 'Sensor Location' column exists
                    if 'Sensor Location' in df.columns:
                        print(f"  -> Creating sensor_mapping with {len(df)} entries")
                        metadata['sensor_mapping'] = {
                            row['Sensor Location']: {
                                'sample_id': row['Sample ID'],
                                'sensor_type': row.get('Sensor Type', ''),
                                'color': row.get('Color', None),
                                'replicate': row.get('Replicate Group', 'N/A')
                            } for row in df.to_dict('records') if 'Sensor Location' in row
                        }
                        print(f"  -> Sensor locations: {list(metadata['sensor_mapping'].keys())}")
                    else:
                        print(f"  WARNING: 'Sensor Location' column not found in sensor mapping table")
                        print(f"  Available columns: {list(df.columns)}")

                print(f"  DEBUG: Checking for 'Step Data Name' in columns: {'Step Data Name' in columns_str}")
                print(f"  DEBUG: Checking for 'Assay Time' in columns: {'Assay Time' in columns_str}")

                if 'Step Data Name' in columns_str and 'Assay Time' in columns_str:
                    # This is the assay steps table
                    print(f"  -> Found assay steps table with {len(df)} steps")
                    metadata['assay_steps'] = df.to_dict('records')

        except Exception as excel_error:
            # Try reading as HTML tables
            print(f"\nDEBUG: Excel parsing failed: {str(excel_error)}")
            print(f"DEBUG: Exception type: {type(excel_error).__name__}")
            print("\nDEBUG: Attempting to read as HTML file...")

            try:
                dfs = pd.read_html(io.BytesIO(decoded))
                print(f"DEBUG: Successfully read as HTML")
                print(f"DEBUG: Found {len(dfs)} tables")
                metadata['tables'] = []

                for i, df in enumerate(dfs):
                    print(f"\n  DEBUG: Processing HTML table [{i}]:")
                    print(f"  DEBUG: Table shape: {df.shape}")
                    print(f"  DEBUG: Columns: {list(df.columns)}")
                    print(f"  DEBUG: First 3 rows:")
                    print(df.head(3))

                    metadata['tables'].append(df.to_dict('records'))

                    # Check for sensor info table
                    if 'Sensor Location' in df.columns and 'Sample ID' in df.columns:
                        print(f"  -> Found sensor info table!")
                        metadata['sensor_info'] = df.to_dict('records')
                        metadata['sensor_mapping'] = {
                            row['Sensor Location']: {
                                'sample_id': row['Sample ID'],
                                'sensor_type': row.get('Sensor Type', ''),
                                'color': row.get('Color', None),
                                'replicate': row.get('Replicate Group', 'N/A')
                            } for row in df.to_dict('records')
                        }
                        print(f"  -> Sensor locations: {list(metadata['sensor_mapping'].keys())}")

                    # Check for assay steps table
                    if 'Step Data Name' in df.columns and 'Assay Time' in df.columns:
                        print(f"  -> Found assay steps table with {len(df)} steps")
                        metadata['assay_steps'] = df.to_dict('records')

            except Exception as html_error:
                print(f"\nDEBUG: HTML parsing also failed: {str(html_error)}")
                print(f"DEBUG: Exception type: {type(html_error).__name__}")
                metadata['error'] = "Could not parse metadata file"

        print(f"\n{'='*80}")
        print(f"DEBUG: Metadata parsing complete!")
        print(f"DEBUG: Metadata keys: {list(metadata.keys())}")
        if 'sensor_mapping' in metadata:
            print(f"DEBUG: Found sensor_mapping with {len(metadata['sensor_mapping'])} entries")
        if 'assay_steps' in metadata:
            print(f"DEBUG: Found assay_steps with {len(metadata['assay_steps'])} steps")
        if 'error' in metadata:
            print(f"ERROR: Parsing failed with error: {metadata['error']}")
        print(f"{'='*80}\n")

        return metadata
    except Exception as e:
        print(f"\n{'!'*80}")
        print(f"ERROR: Exception in parse_metadata_file for {filename}")
        print(f"ERROR: {str(e)}")
        print(f"ERROR: Exception type: {type(e).__name__}")
        import traceback
        print(f"ERROR: Traceback:")
        traceback.print_exc()
        print(f"{'!'*80}\n")
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


def identify_buffer_samples(processed_data):
    """Identify buffer samples from the data for baseline correction"""
    if not processed_data:
        return []
    
    metadata = processed_data.get('metadata', {})
    sensor_mapping = metadata.get('sensor_mapping', {})
    buffer_sensors = []
    
    # Look for sensors with "Buffer" in their sample ID
    for sensor_name in processed_data['sensor_names']:
        if sensor_mapping and sensor_name in sensor_mapping:
            sample_id = sensor_mapping[sensor_name].get('sample_id', '')
            if 'BUFFER' in str(sample_id).upper() or 'Buffer' in str(sample_id):
                buffer_sensors.append(sensor_name)
    
    return buffer_sensors


def calculate_buffer_baseline(processed_data, buffer_sensors=None):
    """Calculate average buffer response for baseline correction"""
    if not processed_data:
        return None, None
    
    if buffer_sensors is None:
        buffer_sensors = identify_buffer_samples(processed_data)
    
    if not buffer_sensors:
        logging.warning("No buffer samples found for baseline correction")
        return None, None
    
    # Get time points from first sensor (assuming all have same time points)
    first_sensor = processed_data['sensor_names'][0]
    sensor_df = pd.DataFrame(processed_data['sensors'][first_sensor])
    time_points = sensor_df['Time'].values
    
    # Average buffer responses across all buffer sensors
    buffer_responses = []
    for buffer_sensor in buffer_sensors:
        if buffer_sensor in processed_data['sensors']:
            buffer_df = pd.DataFrame(processed_data['sensors'][buffer_sensor])
            buffer_responses.append(buffer_df['Response'].values)
    
    if buffer_responses:
        # Calculate average buffer response at each time point
        avg_buffer_response = np.mean(buffer_responses, axis=0)
        return time_points, avg_buffer_response
    
    return None, None


def apply_buffer_baseline_correction(time_data, response_data, buffer_time, buffer_response):
    """Apply buffer-based baseline correction to sensor data"""
    try:
        if buffer_time is None or buffer_response is None:
            # Fallback to simple baseline correction if no buffer available
            baseline = np.mean(response_data[:10]) if len(response_data) > 10 else response_data[0]
            return response_data - baseline
        
        # Interpolate buffer response to match sensor time points
        # This handles cases where time points might not exactly match
        from scipy.interpolate import interp1d
        
        # Create interpolation function for buffer
        buffer_interp = interp1d(buffer_time, buffer_response, 
                               kind='linear', bounds_error=False, fill_value='extrapolate')
        
        # Get buffer values at sensor time points
        buffer_at_sensor_times = buffer_interp(time_data)
        
        # Subtract buffer response
        corrected_response = response_data - buffer_at_sensor_times
        
        return corrected_response
        
    except Exception as e:
        logging.error(f"Error in buffer baseline correction: {str(e)}")
        # Fallback to simple correction
        baseline = np.mean(response_data[:10]) if len(response_data) > 10 else response_data[0]
        return response_data - baseline


def calculate_initial_response_slope(time_data, response_data, start_time, end_time):
    """Calculate average slope using all points in the time interval (not just endpoints)"""
    try:
        # Find data points within the specified time interval
        mask = (time_data >= start_time) & (time_data <= end_time)
        
        if np.sum(mask) < 3:  # Need at least 3 points for reliable slope
            return None, None, None
        
        time_subset = time_data[mask]
        response_subset = response_data[mask]
        
        # Calculate linear regression slope using ALL points in the range
        # This gives us the average slope across all data points
        coeffs = np.polyfit(time_subset, response_subset, 1)
        slope = coeffs[0]  # Average slope (nm/s) across all points
        intercept = coeffs[1]
        
        # Calculate R-squared for fit quality
        fitted_values = np.polyval(coeffs, time_subset)
        r_squared = calculate_r_squared(response_subset, fitted_values)
        
        return slope, intercept, r_squared
    
    except Exception as e:
        logging.error(f"Error calculating slope: {str(e)}")
        return None, None, None


def extract_standard_concentrations(metadata):
    """Extract standard concentrations from metadata by parsing 'Std' or 'STD' followed by a number"""
    import re

    print(f"\n{'='*80}")
    print(f"DEBUG: extract_standard_concentrations called")
    print(f"{'='*80}")

    standards = {}

    # Look for standards in sensor mapping
    sensor_mapping = metadata.get('sensor_mapping', {})
    print(f"DEBUG: sensor_mapping has {len(sensor_mapping)} entries")
    print(f"DEBUG: Sensor mapping keys: {list(sensor_mapping.keys())}")

    # Regex pattern to match "Std" or "STD" followed by a number (int or float)
    # Examples: "Std 7", "STD 0.5", "Std 2.5", "std 0.125"
    std_pattern = re.compile(r'\b(?:std|STD)\s*(\d+\.?\d*)\b', re.IGNORECASE)

    print(f"\nDEBUG: Using dynamic pattern matching for standards...")

    for sensor, info in sensor_mapping.items():
        sample_id = str(info.get('sample_id', ''))
        print(f"\nDEBUG: Checking sensor '{sensor}' with sample_id '{sample_id}'")

        # Try to find "Std" or "STD" followed by a concentration value
        match = std_pattern.search(sample_id)

        if match:
            try:
                concentration = float(match.group(1))
                standards[sensor] = {
                    'concentration': concentration,
                    'sample_id': sample_id,
                    'units': 'µg/mL'  # Assuming concentration units
                }
                print(f"  -> MATCHED! Standard detected: '{sample_id}', concentration: {concentration} µg/mL")
            except ValueError as e:
                print(f"  -> ERROR: Could not parse concentration from '{match.group(1)}': {e}")
        else:
            print(f"  -> No standard pattern found in '{sample_id}'")

    print(f"\n{'='*80}")
    print(f"DEBUG: extract_standard_concentrations complete")
    print(f"DEBUG: Found {len(standards)} standards: {list(standards.keys())}")
    for sensor, std_info in standards.items():
        print(f"  {sensor}: {std_info['sample_id']} = {std_info['concentration']} {std_info['units']}")
    print(f"{'='*80}\n")

    return standards


def calculate_bb_percentage(time_data, response_data, time1, time2, buffer_time=None, buffer_response=None):
    """Calculate %BB (percentage of binding blocked) analysis"""
    try:
        # Apply buffer baseline correction first
        if buffer_time is not None and buffer_response is not None:
            response_data = apply_buffer_baseline_correction(time_data, response_data, buffer_time, buffer_response)
        
        # Find response values at the two time points
        time1_idx = np.argmin(np.abs(time_data - time1))
        time2_idx = np.argmin(np.abs(time_data - time2))
        
        response_time1 = response_data[time1_idx]  # value1
        response_time2 = response_data[time2_idx]  # value2
        
        # Calculate %BB using the correct formula: (1 - value2/value1 - 0.1) * 100
        if response_time1 != 0:  # Avoid division by zero
            bb_percentage = (1 - response_time2/response_time1 - 0.1) * 100
        else:
            bb_percentage = 0
        
        return bb_percentage, response_time1, response_time2
        
    except Exception as e:
        logging.error(f"Error calculating %BB: {str(e)}")
        return None, None, None


def create_standard_curve(standard_data):
    """Create standard curve from concentration vs initial response data"""
    print(f"\n{'='*80}")
    print(f"STD CURVE: create_standard_curve called")
    print(f"STD CURVE: Number of standards: {len(standard_data)}")
    print(f"{'='*80}")

    if len(standard_data) < 3:
        print(f"STD CURVE: INSUFFICIENT data points ({len(standard_data)} < 3), returning None")
        return None, None, None, None

    concentrations = []
    responses = []

    print(f"\nSTD CURVE: Processing standard data points:")
    for idx, std_info in enumerate(standard_data):
        conc = std_info['concentration']
        slope = std_info['slope']
        sensor = std_info.get('sensor', 'Unknown')
        concentrations.append(conc)
        responses.append(slope)
        print(f"  [{idx}] {sensor}: conc={conc}, response={slope:.6f}")

    concentrations = np.array(concentrations)
    responses = np.array(responses)

    print(f"\nSTD CURVE: Fitting linear curve...")
    print(f"STD CURVE: X (concentrations): {concentrations}")
    print(f"STD CURVE: Y (responses): {responses}")

    # Fit linear standard curve
    coeffs = np.polyfit(concentrations, responses, 1)
    slope = coeffs[0]  # response per unit concentration
    intercept = coeffs[1]

    print(f"\nSTD CURVE: Linear fit results:")
    print(f"  Slope: {slope:.6f}")
    print(f"  Intercept: {intercept:.6f}")
    print(f"  Equation: y = {slope:.6f}x + {intercept:.6f}")

    # Calculate R-squared
    fitted_responses = np.polyval(coeffs, concentrations)
    r_squared = calculate_r_squared(responses, fitted_responses)

    print(f"  R²: {r_squared:.4f}")
    print(f"{'='*80}\n")

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


# Modal callbacks
@app.callback(
    Output("upload-modal", "is_open"),
    [Input("upload-modal-btn", "n_clicks"), Input("close-modal-btn", "n_clicks")],
    [State("upload-modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


# Show content tabs when data is processed
@app.callback(
    Output('content-tabs', 'style'),
    [Input('processed-data-store', 'data')]
)
def show_content_tabs(processed_data):
    if processed_data:
        return {'display': 'block'}
    return {'display': 'none'}


# Callbacks for paired file uploads
@app.callback(
    [Output('raw-upload-status', 'children'),
     Output('raw-data-store', 'data')],
    [Input('upload-raw-data', 'contents')],
    [State('upload-raw-data', 'filename')]
)
def handle_raw_data_upload(contents, filename):
    print(f"\n{'*'*80}")
    print(f"CALLBACK: handle_raw_data_upload triggered")
    print(f"CALLBACK: Filename: {filename}")
    print(f"CALLBACK: Contents provided: {contents is not None}")
    print(f"{'*'*80}\n")

    if not contents:
        print("CALLBACK: No contents provided, returning empty status")
        return "", None

    print(f"CALLBACK: Calling parse_raw_octet_data...")
    sensors_data = parse_raw_octet_data(contents, filename)

    if sensors_data:
        print(f"\nCALLBACK: parse_raw_octet_data returned {len(sensors_data)} sensors")
        print(f"CALLBACK: Sensor names: {list(sensors_data.keys())}")

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

        print(f"CALLBACK: Successfully created store_data with {len(store_data['sensor_names'])} sensors")
        print(f"{'*'*80}\n")
        return status, store_data
    else:
        print(f"\nCALLBACK: parse_raw_octet_data returned None (FAILED)")
        status = html.Div([
            html.I(className="fas fa-exclamation-circle me-2", style={"color": "red"}),
            f"Failed to load {filename}"
        ], className="alert alert-danger")
        print(f"{'*'*80}\n")
        return status, None


@app.callback(
    [Output('metadata-upload-status', 'children'),
     Output('metadata-store', 'data')],
    [Input('upload-metadata', 'contents')],
    [State('upload-metadata', 'filename')]
)
def handle_metadata_upload(contents, filename):
    print(f"\n{'*'*80}")
    print(f"CALLBACK: handle_metadata_upload triggered")
    print(f"CALLBACK: Filename: {filename}")
    print(f"CALLBACK: Contents provided: {contents is not None}")
    print(f"{'*'*80}\n")

    if not contents:
        print("CALLBACK: No contents provided, returning empty status")
        return "", None

    print(f"CALLBACK: Calling parse_metadata_file...")
    metadata = parse_metadata_file(contents, filename)

    if metadata and 'error' not in metadata:
        print(f"\nCALLBACK: parse_metadata_file succeeded")
        print(f"CALLBACK: Metadata keys: {list(metadata.keys())}")
        if 'sensor_mapping' in metadata:
            print(f"CALLBACK: Found sensor_mapping with {len(metadata['sensor_mapping'])} entries")

        status = html.Div([
            html.I(className="fas fa-check-circle me-2", style={"color": "green"}),
            f"Loaded {filename}: metadata extracted"
        ], className="alert alert-success")

        print(f"CALLBACK: Returning success status")
        print(f"{'*'*80}\n")
        return status, metadata
    else:
        print(f"\nCALLBACK: parse_metadata_file FAILED")
        if metadata:
            print(f"CALLBACK: Error: {metadata.get('error', 'Unknown error')}")

        status = html.Div([
            html.I(className="fas fa-exclamation-circle me-2", style={"color": "red"}),
            f"Failed to load metadata from {filename}"
        ], className="alert alert-danger")

        print(f"CALLBACK: Returning error status")
        print(f"{'*'*80}\n")
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
    print(f"\n{'*'*80}")
    print(f"CALLBACK: process_paired_data triggered")
    print(f"CALLBACK: raw_data provided: {raw_data is not None}")
    print(f"CALLBACK: metadata provided: {metadata is not None}")

    if raw_data:
        print(f"CALLBACK: Raw data contains {len(raw_data['sensor_names'])} sensors")
        print(f"CALLBACK: Sensor names: {raw_data['sensor_names']}")

    if metadata:
        print(f"CALLBACK: Metadata keys: {list(metadata.keys())}")
        if 'sensor_mapping' in metadata:
            print(f"CALLBACK: Metadata contains sensor_mapping with {len(metadata['sensor_mapping'])} entries")
            print(f"CALLBACK: Mapped sensors: {list(metadata['sensor_mapping'].keys())}")
    print(f"{'*'*80}\n")

    if not raw_data:
        print("CALLBACK: No raw data, returning empty")
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
        
        # Identify buffer samples for baseline correction
        buffer_sensors = identify_buffer_samples({'sensors': raw_data['sensors'], 
                                                 'sensor_names': raw_data['sensor_names'],
                                                 'metadata': metadata})
        
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
                
                # Mark buffer samples
                if sensor_name in buffer_sensors:
                    summary_row['Sample ID'] = f"{summary_row['Sample ID']} (Buffer*)"
            
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
        
        # Add buffer baseline correction info
        if buffer_sensors:
            preview_content.extend([
                html.Hr(),
                html.Div([
                    html.I(className="fas fa-info-circle me-2", style={"color": "#17a2b8"}),
                    html.Strong(f"Buffer Baseline Correction: "),
                    f"Using {len(buffer_sensors)} buffer samples for baseline correction: {', '.join(buffer_sensors)}"
                ], className="alert alert-info", style={"fontSize": "14px", "margin": "10px 0"})
            ])
        
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
    [Input('processed-data-store', 'data'),
     Input('include-standards-option', 'value')]
)
def update_sample_selector(processed_data, include_standards_option):
    print(f"\n{'*'*80}")
    print(f"CALLBACK: update_sample_selector triggered")
    print(f"CALLBACK: include_standards_option = {include_standards_option}")
    print(f"{'*'*80}\n")

    if not processed_data:
        return [], []

    # Extract sensor names and metadata
    options = []
    metadata = processed_data.get('metadata', {})
    sensor_mapping = metadata.get('sensor_mapping', {})

    # Track which sensors are actual samples (not standards or buffers)
    sample_sensors = []
    standard_sensors = []

    include_standards = 'include_standards' in (include_standards_option or [])

    print(f"SELECTOR: Processing {len(processed_data['sensor_names'])} sensors...")
    print(f"SELECTOR: Include standards = {include_standards}")

    for sensor_name in processed_data['sensor_names']:
        # Get sample ID and info from metadata if available
        if sensor_mapping and sensor_name in sensor_mapping:
            sample_info = sensor_mapping[sensor_name]
            sample_id = sample_info.get('sample_id', sensor_name)
            label = f"{sensor_name} - {sample_id}"

            # Check if this is an actual sample (not standard or buffer)
            sample_id_upper = str(sample_id).upper()
            is_standard = 'STD' in sample_id_upper
            is_buffer = 'BUFFER' in sample_id_upper

            print(f"  {sensor_name} ({sample_id}): standard={is_standard}, buffer={is_buffer}")

            if is_standard:
                standard_sensors.append(sensor_name)
            elif not is_buffer:
                sample_sensors.append(sensor_name)
        else:
            label = sensor_name
            # If no metadata, include by default
            sample_sensors.append(sensor_name)

        options.append({
            'label': label,
            'value': sensor_name
        })

    # Select samples by default, optionally include standards
    if include_standards:
        default_selection = sample_sensors + standard_sensors
        print(f"SELECTOR: Selecting {len(sample_sensors)} samples + {len(standard_sensors)} standards")
    else:
        default_selection = sample_sensors
        print(f"SELECTOR: Selecting {len(sample_sensors)} samples only")

    print(f"{'*'*80}\n")
    
    return options, default_selection


@app.callback(
    [Output('standards-selector', 'options'),
     Output('standards-selector', 'value'),
     Output('standards-selection-row', 'style')],
    [Input('processed-data-store', 'data')]
)
def update_standards_selector(processed_data):
    """Populate standards selector with detected standards"""
    print(f"\n{'*'*80}")
    print(f"CALLBACK: update_standards_selector triggered")
    print(f"{'*'*80}\n")

    if not processed_data:
        return [], [], {'display': 'none'}

    metadata = processed_data.get('metadata', {})
    sensor_mapping = metadata.get('sensor_mapping', {})

    # Extract standards
    standards_options = []
    standards_list = []

    print(f"STANDARDS SELECTOR: Searching for standards...")

    for sensor_name in processed_data['sensor_names']:
        if sensor_mapping and sensor_name in sensor_mapping:
            sample_info = sensor_mapping[sensor_name]
            sample_id = sample_info.get('sample_id', sensor_name)
            sample_id_upper = str(sample_id).upper()

            # Check if this is a standard
            if 'STD' in sample_id_upper:
                label = f"{sensor_name} - {sample_id}"
                standards_options.append({
                    'label': label,
                    'value': sensor_name
                })
                standards_list.append(sensor_name)
                print(f"  -> Found standard: {sensor_name} ({sample_id})")

    if standards_list:
        print(f"\nSTANDARDS SELECTOR: Found {len(standards_list)} standards")
        print(f"STANDARDS SELECTOR: Showing standards selection row")
        # Select all standards by default
        return standards_options, standards_list, {'display': 'block'}
    else:
        print(f"\nSTANDARDS SELECTOR: No standards found, hiding selection row")
        return [], [], {'display': 'none'}


@app.callback(
    Output('main-plot', 'figure'),
    [Input('sample-selector', 'value'),
     Input('plot-options', 'value'),
     Input('baseline-option', 'value'),
     Input('proa-start', 'value'),
     Input('proa-end', 'value'),
     Input('bb-time1', 'value'),
     Input('bb-time2', 'value'),
     Input('kappa-start', 'value'),
     Input('kappa-end', 'value')],
    [State('processed-data-store', 'data')]
)
def update_integrated_visualization(selected_samples, plot_options, baseline_options, 
                                   proa_start, proa_end, bb_time1, bb_time2, 
                                   kappa_start, kappa_end, processed_data):
    if not selected_samples or not processed_data:
        return go.Figure()
    
    fig = go.Figure()
    
    # Get metadata and buffer baseline
    metadata = processed_data.get('metadata', {})
    sensor_mapping = metadata.get('sensor_mapping', {})
    assay_steps = metadata.get('assay_steps', [])
    
    # Calculate buffer baseline for correction
    buffer_time, buffer_response = calculate_buffer_baseline(processed_data)
    buffer_sensors = identify_buffer_samples(processed_data)
    
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
            
            # Always apply buffer-based baseline correction (baseline is always enabled)
            y_data = apply_buffer_baseline_correction(x_data, y_data, buffer_time, buffer_response)
            
            # Apply analysis view filter (420s+)
            if 'analysis_view' in plot_options:
                analysis_mask = x_data >= 420
                x_data = x_data[analysis_mask]
                y_data = y_data[analysis_mask]
            
            # Get color and sample info from metadata
            trace_name = sensor_name
            trace_color = default_colors[idx % len(default_colors)]
            line_style = dict(width=2, color=trace_color)
            
            if sensor_mapping and sensor_name in sensor_mapping:
                sample_info = sensor_mapping[sensor_name]
                sample_id = sample_info.get('sample_id', sensor_name)
                trace_name = f"{sensor_name} - {sample_id}"

                # Check if this is a standard
                sample_id_upper = str(sample_id).upper()
                is_standard = 'STD' in sample_id_upper

                # Use color from metadata if available
                if sample_info.get('color'):
                    # Convert color integer to hex if needed
                    color_val = sample_info['color']
                    if isinstance(color_val, (int, float)):
                        # Convert signed integer to RGB
                        color_int = int(color_val) & 0xFFFFFF
                        trace_color = f'#{color_int:06x}'
                        line_style['color'] = trace_color

                # Style standards differently - dotted line and thinner
                if is_standard:
                    trace_name += " (Standard)"
                    line_style['dash'] = 'dot'  # Dotted line for standards
                    line_style['width'] = 1.5

                # Style buffer samples differently
                if sensor_name in buffer_sensors:
                    trace_name += " (Buffer)"
                    line_style['dash'] = 'dash'  # Dashed line for buffers
                    line_style['width'] = 1.5
            
            # Add trace
            fig.add_trace(go.Scatter(
                x=x_data,
                y=y_data,
                mode='lines',
                name=trace_name,
                line=line_style,
                hovertemplate=f'<b>{trace_name}</b><br>Time: %{{x:.1f}} s<br>Response: %{{y:.3f}} nm<extra></extra>'
            ))
        
        except Exception as e:
            logging.error(f"Error plotting sensor {sensor_name}: {str(e)}")
            continue
    
    # Add goal posts for analysis regions
    analysis_regions = [
        {'name': 'ProA', 'start': proa_start, 'end': proa_end, 'color': '#28a745'},
        {'name': '%BB', 'times': [bb_time1, bb_time2], 'color': '#dc3545'}, 
        {'name': 'Kappa', 'start': kappa_start, 'end': kappa_end, 'color': '#007bff'}
    ]
    
    for region in analysis_regions:
        if region['name'] == '%BB':
            # Add shaded region for %BB between the two time points
            fig.add_vrect(
                x0=region['times'][0],
                x1=region['times'][1],
                fillcolor=region['color'],
                opacity=0.2,
                layer="below",
                line_width=0
            )
            
            # Add goal posts (vertical lines at both time points)
            fig.add_vline(
                x=region['times'][0],
                line_dash="solid",
                line_color=region['color'],
                line_width=3,
                opacity=0.7
            )
            fig.add_vline(
                x=region['times'][1],
                line_dash="solid",
                line_color=region['color'],
                line_width=3,
                opacity=0.7
            )
            
            # Add annotation at top of plot
            fig.add_annotation(
                x=(region['times'][0] + region['times'][1]) / 2,
                y=1.05,
                yref="paper",
                text=f"<b>{region['name']}</b>",
                showarrow=False,
                font=dict(size=14, color=region['color']),
                bgcolor="white",
                bordercolor=region['color'],
                borderwidth=1
            )
        else:
            # Add shaded region for ProA and Kappa
            fig.add_vrect(
                x0=region['start'],
                x1=region['end'],
                fillcolor=region['color'],
                opacity=0.2,
                layer="below",
                line_width=0
            )
            
            # Add goal posts (vertical lines at start and end)
            fig.add_vline(
                x=region['start'],
                line_dash="solid",
                line_color=region['color'],
                line_width=3,
                opacity=0.7
            )
            fig.add_vline(
                x=region['end'],
                line_dash="solid",
                line_color=region['color'],
                line_width=3,
                opacity=0.7
            )
            
            # Add annotation at top of plot
            fig.add_annotation(
                x=(region['start'] + region['end']) / 2,
                y=1.05,
                yref="paper",
                text=f"<b>{region['name']}</b>",
                showarrow=False,
                font=dict(size=14, color=region['color']),
                bgcolor="white",
                bordercolor=region['color'],
                borderwidth=1
            )
    
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
    
    # Update layout
    fig.update_layout(
        title=None,
        xaxis_title="Time (s)",
        yaxis_title="Response (nm)",
        hovermode='x unified',
        showlegend=True,
        template="plotly_white",
        height=650,
        margin=dict(t=60),  # Add top margin for labels
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
    
    return fig


# Integrated Analysis Callback - Runs all three analyses at once
@app.callback(
    [Output('integrated-results-container', 'children'),
     Output('standard-curves-section', 'style'),
     Output('proa-std-curve-section', 'style'),
     Output('bb-std-curve-section', 'style'),
     Output('kappa-std-curve-section', 'style')],
    [Input('run-all-analysis-btn', 'n_clicks')],
    [State('sample-selector', 'value'),
     State('proa-start', 'value'),
     State('proa-end', 'value'),
     State('bb-time1', 'value'),
     State('bb-time2', 'value'),
     State('kappa-start', 'value'),
     State('kappa-end', 'value'),
     State('standards-selector', 'value'),
     State('processed-data-store', 'data')]
)
def run_integrated_analysis(n_clicks, selected_samples, proa_start, proa_end,
                           bb_time1, bb_time2, kappa_start, kappa_end, selected_standards, processed_data):
    print(f"\n{'#'*80}")
    print(f"ANALYSIS: run_integrated_analysis called")
    print(f"ANALYSIS: n_clicks={n_clicks}")
    print(f"ANALYSIS: selected_samples={selected_samples}")
    print(f"ANALYSIS: selected_standards={selected_standards}")
    print(f"ANALYSIS: ProA range: {proa_start}-{proa_end}s")
    print(f"ANALYSIS: Kappa range: {kappa_start}-{kappa_end}s")
    print(f"ANALYSIS: BB times: {bb_time1}s, {bb_time2}s")
    print(f"{'#'*80}\n")

    if not n_clicks or not processed_data:
        print("ANALYSIS: No clicks or no processed data, returning empty")
        return "", {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}

    # Get metadata and buffer baseline
    metadata = processed_data.get('metadata', {})
    sensor_mapping = metadata.get('sensor_mapping', {})

    print(f"ANALYSIS: Extracting standard concentrations...")
    standards_info = extract_standard_concentrations(metadata)
    print(f"ANALYSIS: Standards extracted: {len(standards_info)} standards found")

    print(f"\nANALYSIS: Calculating buffer baseline...")
    buffer_time, buffer_response = calculate_buffer_baseline(processed_data)
    print(f"ANALYSIS: Buffer baseline calculated: {len(buffer_time) if buffer_time is not None else 0} points")
    
    # Results storage
    all_results = []
    proa_standards = []
    kappa_standards = []
    
    # Process all samples (not just selected ones for comprehensive results)
    for sensor_name in processed_data['sensor_names']:
        try:
            # Get sensor data
            sensor_df = pd.DataFrame(processed_data['sensors'][sensor_name])
            time_data = sensor_df['Time'].values
            response_data = sensor_df['Response'].values
            
            # Get sample info
            sample_id = sensor_name
            if sensor_mapping and sensor_name in sensor_mapping:
                sample_info = sensor_mapping[sensor_name]
                sample_id = sample_info.get('sample_id', sensor_name)
            
            # Skip buffer samples from results
            if 'BUFFER' in str(sample_id).upper():
                continue
            
            # Apply buffer baseline correction
            corrected_response = apply_buffer_baseline_correction(time_data, response_data, buffer_time, buffer_response)
            
            result_row = {
                'Sample ID': sample_id,
                'Sensor': sensor_name
            }
            
            # 1. ProA Analysis
            proa_slope, _, proa_r2 = calculate_initial_response_slope(
                time_data, corrected_response, proa_start, proa_end
            )
            if proa_slope is not None:
                result_row['ProA Slope (nm/s)'] = f"{proa_slope:.6f}"
                result_row['ProA R²'] = f"{proa_r2:.4f}" if proa_r2 else "N/A"

                # Store for standard curve if it's a standard AND selected by user
                if sensor_name in standards_info:
                    # Check if this standard is selected (if no selection, use all)
                    if not selected_standards or sensor_name in selected_standards:
                        print(f"  ANALYSIS: {sensor_name} is a SELECTED STANDARD - adding to ProA standards")
                        print(f"    Concentration: {standards_info[sensor_name]['concentration']}")
                        print(f"    Slope: {proa_slope:.6f}")
                        proa_standards.append({
                            'concentration': standards_info[sensor_name]['concentration'],
                            'slope': proa_slope,
                            'sensor': sensor_name
                        })
                    else:
                        print(f"  ANALYSIS: {sensor_name} is a standard but NOT SELECTED - skipping")
            
            # 2. %BB Analysis  
            bb_percentage, bb_resp1, bb_resp2 = calculate_bb_percentage(
                time_data, response_data, bb_time1, bb_time2, buffer_time, buffer_response
            )
            if bb_percentage is not None:
                result_row['%BB'] = f"{bb_percentage:.1f}%"
                result_row[f'Resp@{bb_time1}s'] = f"{bb_resp1:.4f}"
                result_row[f'Resp@{bb_time2}s'] = f"{bb_resp2:.4f}"
            
            # 3. Kappa Analysis
            kappa_slope, _, kappa_r2 = calculate_initial_response_slope(
                time_data, corrected_response, kappa_start, kappa_end
            )
            if kappa_slope is not None:
                result_row['Kappa Slope (nm/s)'] = f"{kappa_slope:.6f}"
                result_row['Kappa R²'] = f"{kappa_r2:.4f}" if kappa_r2 else "N/A"

                # Store for standard curve if it's a standard AND selected by user
                if sensor_name in standards_info:
                    # Check if this standard is selected (if no selection, use all)
                    if not selected_standards or sensor_name in selected_standards:
                        print(f"  ANALYSIS: {sensor_name} is a SELECTED STANDARD - adding to Kappa standards")
                        print(f"    Concentration: {standards_info[sensor_name]['concentration']}")
                        print(f"    Slope: {kappa_slope:.6f}")
                        kappa_standards.append({
                            'concentration': standards_info[sensor_name]['concentration'],
                            'slope': kappa_slope,
                            'sensor': sensor_name
                        })
                    else:
                        print(f"  ANALYSIS: {sensor_name} is a standard but NOT SELECTED - skipping")
            
            all_results.append(result_row)
            
        except Exception as e:
            logging.error(f"Error analyzing {sensor_name}: {str(e)}")
            continue
    
    if not all_results:
        print("ANALYSIS: No results generated, returning empty")
        return "No analysis results available", {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}

    print(f"\n{'='*80}")
    print(f"ANALYSIS: Sample processing complete")
    print(f"ANALYSIS: Total results: {len(all_results)}")
    print(f"ANALYSIS: ProA standards collected: {len(proa_standards)}")
    print(f"ANALYSIS: Kappa standards collected: {len(kappa_standards)}")
    print(f"{'='*80}\n")

    # Create standard curves and calculate concentrations
    proa_concentrations = {}
    kappa_concentrations = {}

    # ProA standard curve
    print(f"ANALYSIS: Checking ProA standard curve generation...")
    print(f"ANALYSIS: ProA standards count: {len(proa_standards)} (need >= 3)")
    if len(proa_standards) >= 3:
        print(f"ANALYSIS: Creating ProA standard curve with {len(proa_standards)} points...")
        for std in proa_standards:
            print(f"  - {std['sensor']}: conc={std['concentration']}, slope={std['slope']:.6f}")

        proa_curve_slope, proa_curve_intercept, proa_curve_r2, _ = create_standard_curve(proa_standards)
        print(f"ANALYSIS: ProA curve created: slope={proa_curve_slope}, intercept={proa_curve_intercept}, R²={proa_curve_r2}")

        if proa_curve_slope is not None:
            print(f"ANALYSIS: ProA curve is VALID, calculating concentrations for samples...")
            for row in all_results:
                if 'ProA Slope (nm/s)' in row:
                    slope_val = float(row['ProA Slope (nm/s)'])
                    conc = (slope_val - proa_curve_intercept) / proa_curve_slope
                    if conc > 0:
                        row['ProA Conc. (µg/mL)'] = f"{conc:.2f}"
                        proa_concentrations[row['Sample ID']] = conc
                    else:
                        row['ProA Conc. (µg/mL)'] = "Below LOD"
    
    else:
        print(f"ANALYSIS: NOT enough ProA standards ({len(proa_standards)} < 3), skipping ProA curve")

    # Kappa standard curve
    print(f"\nANALYSIS: Checking Kappa standard curve generation...")
    print(f"ANALYSIS: Kappa standards count: {len(kappa_standards)} (need >= 3)")
    if len(kappa_standards) >= 3:
        print(f"ANALYSIS: Creating Kappa standard curve with {len(kappa_standards)} points...")
        for std in kappa_standards:
            print(f"  - {std['sensor']}: conc={std['concentration']}, slope={std['slope']:.6f}")

        kappa_curve_slope, kappa_curve_intercept, kappa_curve_r2, _ = create_standard_curve(kappa_standards)
        print(f"ANALYSIS: Kappa curve created: slope={kappa_curve_slope}, intercept={kappa_curve_intercept}, R²={kappa_curve_r2}")

        if kappa_curve_slope is not None:
            print(f"ANALYSIS: Kappa curve is VALID, calculating concentrations for samples...")
            for row in all_results:
                if 'Kappa Slope (nm/s)' in row:
                    slope_val = float(row['Kappa Slope (nm/s)'])
                    conc = (slope_val - kappa_curve_intercept) / kappa_curve_slope
                    if conc > 0:
                        row['Kappa Conc. (µg/mL)'] = f"{conc:.2f}"
                        kappa_concentrations[row['Sample ID']] = conc
                    else:
                        row['Kappa Conc. (µg/mL)'] = "Below LOD"
    else:
        print(f"ANALYSIS: NOT enough Kappa standards ({len(kappa_standards)} < 3), skipping Kappa curve")

    print(f"\n{'='*80}")
    print(f"ANALYSIS: Standard curve generation complete")
    print(f"ANALYSIS: ProA concentrations calculated: {len(proa_concentrations)}")
    print(f"ANALYSIS: Kappa concentrations calculated: {len(kappa_concentrations)}")
    print(f"{'='*80}\n")
    
    # Create simplified results table with only essential columns
    simplified_results = []
    for row in all_results:
        simplified_row = {
            'Sample Name': row['Sample ID'],
            'ProA Conc. (µg/mL)': row.get('ProA Conc. (µg/mL)', 'N/A'),
            '%BB': row.get('%BB', 'N/A'),
            'Kappa Conc. (µg/mL)': row.get('Kappa Conc. (µg/mL)', 'N/A')
        }
        simplified_results.append(simplified_row)
    
    results_table = dash_table.DataTable(
        data=simplified_results,
        columns=[{"name": i, "id": i} for i in simplified_results[0].keys()],
        style_cell={'textAlign': 'center', 'padding': '12px', 'fontSize': '13px'},
        style_header={'backgroundColor': '#0056b3', 'color': 'white', 'fontWeight': 'bold', 'fontSize': '14px'},
        style_table={'overflowX': 'auto'},
        export_format='csv',
        export_headers='display',
        page_size=20,
        style_data_conditional=[
            {
                'if': {'column_id': 'ProA Conc. (µg/mL)'},
                'backgroundColor': '#d5ead5'
            },
            {
                'if': {'column_id': '%BB'},
                'backgroundColor': '#f2d5d5'
            },
            {
                'if': {'column_id': 'Kappa Conc. (µg/mL)'},
                'backgroundColor': '#d5e8f2'
            }
        ]
    )
    
    # Determine which standard curves to show
    proa_std_style = {'display': 'block'} if len(proa_standards) >= 3 else {'display': 'none'}
    bb_std_style = {'display': 'none'}  # %BB doesn't use standard curve typically
    kappa_std_style = {'display': 'block'} if len(kappa_standards) >= 3 else {'display': 'none'}
    
    std_curves_style = {'display': 'block'} if (len(proa_standards) >= 3 or len(kappa_standards) >= 3) else {'display': 'none'}
    
    # Return just the table without summary
    return results_table, std_curves_style, proa_std_style, bb_std_style, kappa_std_style


# ProA Standard Curve Callback
@app.callback(
    Output('proa-std-curve', 'figure'),
    [Input('run-all-analysis-btn', 'n_clicks')],
    [State('proa-start', 'value'),
     State('proa-end', 'value'),
     State('standards-selector', 'value'),
     State('processed-data-store', 'data')]
)
def update_proa_std_curve(n_clicks, proa_start, proa_end, selected_standards, processed_data):
    if not n_clicks or not processed_data:
        return go.Figure()

    # Get metadata and standards
    metadata = processed_data.get('metadata', {})
    standards_info = extract_standard_concentrations(metadata)
    buffer_time, buffer_response = calculate_buffer_baseline(processed_data)

    # Calculate ProA slopes for standards (only selected ones)
    proa_standards = []
    for sensor_name in processed_data['sensor_names']:
        if sensor_name in standards_info:
            # Only include if selected (or if no selection, use all)
            if not selected_standards or sensor_name in selected_standards:
                try:
                    sensor_df = pd.DataFrame(processed_data['sensors'][sensor_name])
                    time_data = sensor_df['Time'].values
                    response_data = sensor_df['Response'].values
                    corrected_response = apply_buffer_baseline_correction(time_data, response_data, buffer_time, buffer_response)

                    proa_slope, _, proa_r2 = calculate_initial_response_slope(time_data, corrected_response, proa_start, proa_end)
                    if proa_slope is not None:
                        proa_standards.append({
                            'concentration': standards_info[sensor_name]['concentration'],
                            'slope': proa_slope,
                            'sensor': sensor_name
                        })
                except:
                    continue
    
    if len(proa_standards) < 3:
        fig = go.Figure()
        fig.add_annotation(text="Need at least 3 standards", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Create standard curve
    curve_slope, curve_intercept, curve_r2, curve_data = create_standard_curve(proa_standards)
    
    if curve_slope is None:
        return go.Figure()
    
    concentrations, responses, fitted_responses = curve_data
    
    fig = go.Figure()
    
    # Add standard points
    fig.add_trace(go.Scatter(
        x=concentrations,
        y=responses,
        mode='markers',
        name='Standards',
        marker=dict(size=8, color='#28a745'),
        hovertemplate='Concentration: %{x:.2f} µg/mL<br>Response: %{y:.6f} nm/s<extra></extra>'
    ))
    
    # Add fitted line
    fig.add_trace(go.Scatter(
        x=concentrations,
        y=fitted_responses,
        mode='lines',
        name=f'R² = {curve_r2:.4f}',
        line=dict(color='red', width=2)
    ))
    
    fig.update_layout(
        xaxis_title="Concentration (µg/mL)",
        yaxis_title="ProA Response (nm/s)",
        template="plotly_white",
        height=450,
        margin=dict(l=50, r=50, t=30, b=50),
        showlegend=True
    )
    
    return fig


# Kappa Standard Curve Callback
@app.callback(
    Output('kappa-std-curve', 'figure'),
    [Input('run-all-analysis-btn', 'n_clicks')],
    [State('kappa-start', 'value'),
     State('kappa-end', 'value'),
     State('standards-selector', 'value'),
     State('processed-data-store', 'data')]
)
def update_kappa_std_curve(n_clicks, kappa_start, kappa_end, selected_standards, processed_data):
    if not n_clicks or not processed_data:
        return go.Figure()

    # Get metadata and standards
    metadata = processed_data.get('metadata', {})
    standards_info = extract_standard_concentrations(metadata)
    buffer_time, buffer_response = calculate_buffer_baseline(processed_data)

    # Calculate Kappa slopes for standards (only selected ones)
    kappa_standards = []
    for sensor_name in processed_data['sensor_names']:
        if sensor_name in standards_info:
            # Only include if selected (or if no selection, use all)
            if not selected_standards or sensor_name in selected_standards:
                try:
                    sensor_df = pd.DataFrame(processed_data['sensors'][sensor_name])
                    time_data = sensor_df['Time'].values
                    response_data = sensor_df['Response'].values
                    corrected_response = apply_buffer_baseline_correction(time_data, response_data, buffer_time, buffer_response)

                    kappa_slope, _, kappa_r2 = calculate_initial_response_slope(time_data, corrected_response, kappa_start, kappa_end)
                    if kappa_slope is not None:
                        kappa_standards.append({
                            'concentration': standards_info[sensor_name]['concentration'],
                            'slope': kappa_slope,
                            'sensor': sensor_name
                        })
                except:
                    continue
    
    if len(kappa_standards) < 3:
        fig = go.Figure()
        fig.add_annotation(text="Need at least 3 standards", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Create standard curve
    curve_slope, curve_intercept, curve_r2, curve_data = create_standard_curve(kappa_standards)
    
    if curve_slope is None:
        return go.Figure()
    
    concentrations, responses, fitted_responses = curve_data
    
    fig = go.Figure()
    
    # Add standard points
    fig.add_trace(go.Scatter(
        x=concentrations,
        y=responses,
        mode='markers',
        name='Standards',
        marker=dict(size=8, color='#007bff'),
        hovertemplate='Concentration: %{x:.2f} µg/mL<br>Response: %{y:.6f} nm/s<extra></extra>'
    ))
    
    # Add fitted line
    fig.add_trace(go.Scatter(
        x=concentrations,
        y=fitted_responses,
        mode='lines',
        name=f'R² = {curve_r2:.4f}',
        line=dict(color='red', width=2)
    ))
    
    fig.update_layout(
        xaxis_title="Concentration (µg/mL)",
        yaxis_title="Kappa Response (nm/s)",
        template="plotly_white",
        height=450,
        margin=dict(l=50, r=50, t=30, b=50),
        showlegend=True
    )
    
    return fig


# %BB Standard Curve Callback (placeholder - typically no standard curve for %BB)
@app.callback(
    Output('bb-std-curve', 'figure'),
    [Input('run-all-analysis-btn', 'n_clicks')],
    [State('processed-data-store', 'data')]
)
def update_bb_std_curve(n_clicks, processed_data):
    fig = go.Figure()
    fig.add_annotation(
        text="%BB analysis typically doesn't use standard curves",
        xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
    )
    fig.update_layout(
        template="plotly_white",
        height=450,
        margin=dict(l=50, r=50, t=30, b=50)
    )
    return fig


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
    
    # Calculate buffer baseline for correction
    buffer_time, buffer_response = calculate_buffer_baseline(processed_data)
    
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
            
            # Apply buffer-based baseline correction
            response_data = apply_buffer_baseline_correction(time_data, response_data, buffer_time, buffer_response)
            
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
    
    # Calculate buffer baseline for correction
    buffer_time, buffer_response = calculate_buffer_baseline(processed_data)
    
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
            
            # Apply buffer-based baseline correction
            response_data = apply_buffer_baseline_correction(time_data, response_data, buffer_time, buffer_response)
            
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




if __name__ == '__main__':
    app.run_server(debug=True)