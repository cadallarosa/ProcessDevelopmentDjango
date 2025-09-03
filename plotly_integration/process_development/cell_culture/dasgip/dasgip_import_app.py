"""
DASGIP Data Import App
Dash application for uploading and importing DASGIP bioreactor data files
"""

import os
import base64
import io
import json
from datetime import datetime
import traceback

import dash
from dash import dcc, html, Input, Output, State, callback, dash_table, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd

from django_plotly_dash import DjangoDash
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from plotly_integration.models import (
    USPBioreactorRun, USPTimeSeriesData, User
)
from plotly_integration.process_development.cell_culture.dasgip.helpers.dasgip_parser import DasgipFinalParser as DasgipParser


def detect_file_format(file_path):
    """
    Detect whether the file is a raw DASGIP file or a database export CSV
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            first_line = f.readline().strip()
            second_line = f.readline().strip()
        
        # Check for DASGIP format markers
        if first_line.startswith('"[Info]"') or 'Product' in second_line:
            return 'raw_dasgip'
        
        # Check for database export format (starts with numeric ID)
        if first_line and first_line[0].isdigit() and ',' in first_line:
            parts = first_line.split(',')
            if len(parts) >= 25:  # Should have ~25 columns for database export
                return 'database_export'
        
        # Default to raw DASGIP
        return 'raw_dasgip'
        
    except Exception as e:
        print(f"Error detecting file format: {e}")
        return 'raw_dasgip'


def process_database_export_csv(file_path):
    """
    Process CSV files that are exports from the database (usp_timeseries_data format).
    These have format: id,timestamp,duration,sensor_cols...,up_number
    """
    print(f"Processing database export CSV: {file_path}")
    
    # Define the expected column structure based on USPTimeSeriesData model
    columns = [
        'id', 'timestamp', 'duration', 'do_pv', 'do_sp', 'do_out', 
        'ph_pv', 'ph_sp', 'ph_out', 'temp_pv', 'temp_sp', 'temp_out',
        'rpm_pv', 'rpm_sp', 'volume_pv', 'air_flow_pv', 'air_flow_sp',
        'feed_a_pv', 'feed_a_sp', 'feed_b_pv', 'feed_b_sp', 
        'o2_conc_pv', 'o2_conc_sp', 'co2_conc_pv', 'co2_conc_sp', 'up_number'
    ]
    
    # Read the CSV
    df = pd.read_csv(file_path, names=columns, dtype={'up_number': str})
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # Remove rows where timestamp is null
    df = df.dropna(subset=['timestamp'])
    
    # Convert numeric columns
    numeric_cols = [col for col in columns if col not in ['id', 'timestamp', 'up_number']]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    print(f"Loaded {len(df)} rows with {df['up_number'].nunique()} unique UP numbers: {df['up_number'].unique()}")
    
    # Group by UP number
    results = {}
    for up_number in df['up_number'].unique():
        if pd.isna(up_number) or up_number == '':
            continue
            
        up_df = df[df['up_number'] == up_number].copy()
        up_df = up_df.sort_values('timestamp').reset_index(drop=True)
        
        results[up_number] = {
            'data': up_df,
            'unit_number': 1,  # Default unit number
            'setup_name': f'Unit for {up_number}',
            'start_timestamp': up_df['timestamp'].min(),
            'stop_timestamp': up_df['timestamp'].max(),
        }
        
        print(f"  UP {up_number}: {len(up_df)} rows from {results[up_number]['start_timestamp']} to {results[up_number]['stop_timestamp']}")
    
    return results


# Removed consolidation function - importing all data without consolidation for speed


# Initialize the Dash app
app = DjangoDash(
    'dasgip_import', 
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    add_bootstrap_links=True
)

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("DASGIP Bioreactor Data Import", className="mb-4"),
            html.Hr(),
        ])
    ]),
    
    # File Upload Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("Step 1: Upload DASGIP CSV File")),
                dbc.CardBody([
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select Files', style={'color': '#007bff', 'textDecoration': 'underline'})
                        ]),
                        style={
                            'width': '100%',
                            'height': '100px',
                            'lineHeight': '100px',
                            'borderWidth': '2px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px',
                            'backgroundColor': '#fafafa'
                        },
                        multiple=False
                    ),
                    html.Div(id='upload-status', className="mt-3"),
                ])
            ], className="mb-4")
        ])
    ]),
    
    # File Preview Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("Step 2: File Preview & Unit Detection")),
                dbc.CardBody([
                    html.Div(id='file-preview'),
                    dcc.Store(id='parsed-data-store'),
                    dcc.Store(id='file-path-store'),
                    dcc.Store(id='up-numbers-store'),
                ])
            ], className="mb-4", id="preview-card", style={'display': 'none'})
        ])
    ]),
    
    # Unit Mapping Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("Step 3: Map UP Numbers to Bioreactor Units")),
                dbc.CardBody([
                    html.Div(id='unit-mapping-section'),
                    html.Hr(),
                    dcc.Loading(
                        id="import-loading",
                        type="default",
                        children=[
                            dbc.Button(
                                "Import Data to Database", 
                                id="import-button", 
                                color="primary", 
                                size="lg",
                                disabled=True,
                                className="mt-3"
                            ),
                        ]
                    ),
                    html.Div(id='import-status', className="mt-3"),
                ])
            ], className="mb-4", id="mapping-card", style={'display': 'none'})
        ])
    ]),
    
    # Results Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("Import Results")),
                dbc.CardBody([
                    html.Div(id='import-results'),
                ])
            ], id="results-card", style={'display': 'none'})
        ])
    ]),
    
    # Storage components
    dcc.Store(id='import-progress-store')
], fluid=True, className="p-4")


@app.callback(
    [Output('upload-status', 'children'),
     Output('file-preview', 'children'),
     Output('parsed-data-store', 'data'),
     Output('file-path-store', 'data'),
     Output('preview-card', 'style'),
     Output('mapping-card', 'style')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def upload_and_parse_file(contents, filename):
    """Handle file upload and initial parsing"""
    print(f"UPLOAD DEBUG: File upload callback triggered!")
    print(f"UPLOAD DEBUG: Contents exists: {contents is not None}")
    print(f"UPLOAD DEBUG: Filename: {filename}")
    
    if contents is None:
        print("UPLOAD DEBUG: No contents, returning early")
        return '', '', None, None, {'display': 'none'}, {'display': 'none'}
    
    print("UPLOAD DEBUG: Starting file processing...")
    
    try:
        # Decode the file
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Save file temporarily
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_dasgip')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, filename)
        
        with open(temp_path, 'wb') as f:
            f.write(decoded)
        
        print(f"UPLOAD DEBUG: File saved to: {temp_path}")
        
        # Detect file format and choose appropriate parser
        file_format = detect_file_format(temp_path)
        print(f"UPLOAD DEBUG: Detected file format: {file_format}")
        
        if file_format == 'database_export':
            # Process database export CSV
            export_data = process_database_export_csv(temp_path)
            
            # Convert to parser-like format
            units_info = []
            for up_number, up_data in export_data.items():
                units_info.append({
                    'unit_number': len(units_info) + 1,
                    'setup_name': up_data['setup_name'],
                    'up_number': up_number,
                    'start_timestamp': up_data['start_timestamp'],
                    'stop_timestamp': up_data['stop_timestamp'],
                    'data': up_data['data']
                })
            
            exp_info = {
                'project_name': 'Database Export',
                'host': 'Unknown',
                'units_count': len(units_info),
                'tracks_count': 24  # Approximate sensor count
            }
            success = True
            
        else:
            # Use original DASGIP parser
            parser = DasgipParser(temp_path)
            success = parser.parse()
            print(f"UPLOAD DEBUG: Parser success: {success}")
            
            # Get experiment info
            exp_info = parser.get_experiment_info()
            units_info = parser.get_units_info()
        
        print(f"UPLOAD DEBUG: Found {len(units_info)} units: {[u.get('unit_number', '?') for u in units_info]}")
        print(f"UPLOAD DEBUG: Experiment info: {exp_info}")
        
        # Create data preview for each unit
        unit_previews = []
        for unit in units_info:
            unit_no = unit['unit_number']
            
            if file_format == 'database_export':
                # For database export, we already have the data
                df = unit.get('data', pd.DataFrame()).head(10)
                tracks = [{'parameter_name': col} for col in df.columns if col not in ['id', 'timestamp', 'duration', 'up_number']]
            else:
                # For raw DASGIP files
                tracks = parser.get_unit_tracks(unit_no)
                df = parser.get_sample_data(unit_no, 10)  # Get 10 sample rows
            
            unit_preview = [
                html.H6(f"Unit {unit_no} Preview:", style={'margin-top': '10px'}),
                html.P(f"Parameters: {', '.join([t['parameter_name'] for t in tracks[:5]])}..."),
            ]
            
            if not df.empty:
                # Create a simple time series plot for key parameters
                fig = go.Figure()
                
                # Add key parameters to plot
                key_params = ['do_pv', 'ph_pv', 'temp_pv', 'volume_pv']
                colors = ['blue', 'red', 'green', 'orange']
                
                for i, param in enumerate(key_params):
                    if param in df.columns and df[param].notna().any():
                        fig.add_trace(go.Scatter(
                            x=df['timestamp'],
                            y=df[param],
                            mode='lines+markers',
                            name=param,
                            line=dict(color=colors[i % len(colors)])
                        ))
                
                fig.update_layout(
                    height=200,
                    title=f"Unit {unit_no} Key Parameters",
                    xaxis_title="Time",
                    yaxis_title="Value",
                    showlegend=True,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                
                unit_preview.append(dcc.Graph(figure=fig, style={'height': '200px'}))
                
                # Add data table preview
                preview_df = df[['timestamp', 'duration'] + [col for col in df.columns[2:6]]].head(5)
                unit_preview.append(
                    dash_table.DataTable(
                        data=preview_df.to_dict('records'),
                        columns=[{"name": col, "id": col} for col in preview_df.columns],
                        style_cell={'textAlign': 'left', 'fontSize': '12px'},
                        style_table={'height': '150px', 'overflowY': 'auto'},
                        page_size=5
                    )
                )
            else:
                unit_preview.append(html.P("No data found for this unit", style={'color': 'red'}))
            
            unit_previews.extend(unit_preview + [html.Hr()])
        
        # Create file preview
        preview_children = [
            html.H5(f"File: {filename}"),
            html.Hr(),
            
            # Experiment Information
            html.H6("Experiment Information:"),
            html.Ul([
                html.Li(f"Project: {exp_info['project_name']}"),
                html.Li(f"Host: {exp_info['host']}"),
                html.Li(f"Total Units: {exp_info['units_count']}"),
                html.Li(f"Total Tracks: {exp_info['tracks_count']}"),
            ]),
            
            # Units Detected
            html.H6(f"Detected {len(units_info)} Bioreactor Units:"),
            html.Ul([
                html.Li([
                    html.Strong(f"Unit {unit['unit_number']}: {unit['setup_name']}"),
                    html.Br(),
                    html.Span(f"Start: {unit.get('start_timestamp', 'N/A')}", style={'color': '#666', 'fontSize': '0.9em'}),
                    html.Br(),
                    html.Span(f"End: {unit.get('stop_timestamp', 'N/A')}", style={'color': '#666', 'fontSize': '0.9em'}),
                    html.Br(),
                    html.Span(f"Duration: {((unit.get('stop_timestamp') - unit.get('start_timestamp')).total_seconds() / 3600):.1f} hours" if unit.get('start_timestamp') and unit.get('stop_timestamp') else "Duration: N/A", style={'color': '#007bff', 'fontWeight': 'bold', 'fontSize': '0.9em'})
                ])
                for unit in units_info
            ]),
            
            # Data Preview Section
            html.H6("Time Series Data Preview:"),
            html.Div(unit_previews),
            
            # Data Summary
            html.H6("Data Summary:"),
            html.Ul([
                html.Li(f"Parse successful: {success}"),
                html.Li(f"Total units: {len(units_info)}"),
                html.Li(f"File processed successfully"),
            ])
        ]
        
        upload_status = dbc.Alert(
            f"Successfully parsed {filename}", 
            color="success", 
            dismissable=True
        )
        
        # Create data for storage
        parsed_data = {
            'success': success,
            'experiment': exp_info,
            'units': units_info,
            'parser_type': 'final' if file_format == 'raw_dasgip' else 'database_export',
            'file_format': file_format
        }
        
        print(f"UPLOAD DEBUG: Data stored for import callback")
        print(f"UPLOAD DEBUG: Parsed data keys: {list(parsed_data.keys())}")
        print(f"UPLOAD DEBUG: Temp path: {temp_path}")
        print(f"UPLOAD DEBUG: Upload completed successfully!")
        
        return (
            upload_status,
            preview_children,
            json.dumps(parsed_data, default=str),
            temp_path,
            {'display': 'block'},
            {'display': 'block'}
        )
        
    except Exception as e:
        error_msg = dbc.Alert(
            f"Error parsing file: {str(e)}", 
            color="danger", 
            dismissable=True
        )
        return error_msg, '', None, None, {'display': 'none'}, {'display': 'none'}


@app.callback(
    [Output('unit-mapping-section', 'children'),
     Output('import-button', 'disabled')],
    [Input('parsed-data-store', 'data')]
)
def create_unit_mapping_ui(parsed_data_json):
    """Create UI for mapping UP numbers to units"""
    if not parsed_data_json:
        return '', True
    
    try:
        parsed_data = json.loads(parsed_data_json)
        
        # Get units from the final parser format
        units = parsed_data.get('units', [])
        if not units:
            return dbc.Alert("No units found in parsed data", color="warning"), True
        
        # Create DataTable for UP numbers mapping
        table_data = []
        for unit in units:
            table_data.append({
                'unit_number': unit['unit_number'],
                'setup_name': unit.get('setup_name', f"Unit {unit['unit_number']}"),
                'up_number': unit.get('up_number', f"UP_{unit['unit_number']}")  # Default UP number
            })
        
        mapping_ui = [
            html.P("Enter UP Numbers for each bioreactor unit:"),
            dash_table.DataTable(
                id='up-mapping-table',
                data=table_data,
                columns=[
                    {'name': 'Unit #', 'id': 'unit_number', 'editable': False},
                    {'name': 'Setup Name', 'id': 'setup_name', 'editable': False},
                    {'name': 'UP Number', 'id': 'up_number', 'editable': True}
                ],
                style_cell={'textAlign': 'left'},
                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {
                        'if': {'column_id': 'up_number'},
                        'backgroundColor': '#e3f2fd'
                    }
                ],
                tooltip_data=[
                    {
                        'up_number': {'value': 'Click to edit UP number', 'type': 'markdown'}
                    } for _ in range(len(table_data))
                ]
            ),
            html.P("Click on UP Number cells to edit them.", className="text-muted small mt-2")
        ]
        
        return mapping_ui, False
        
    except Exception as e:
        return dbc.Alert(f"Error creating mapping UI: {str(e)}", color="danger"), True


# Removed old UP number callbacks - now using DataTable


# Test database callback - REMOVED


# Main import callback - simple and reliable
@app.callback(
    Output('import-status', 'children'),
    [Input('import-button', 'n_clicks')],
    [State('parsed-data-store', 'data'),
     State('file-path-store', 'data'),
     State('up-mapping-table', 'data')],
    prevent_initial_call=True
)
def import_to_database(n_clicks, parsed_data_json, file_path, up_table_data):
    """Main import function - imports data to database"""
    import os
    import json
    
    print(f"IMPORT: Button clicked {n_clicks} times")
    print(f"IMPORT: Has parsed data: {parsed_data_json is not None}")
    print(f"IMPORT: File path: {file_path}")
    print(f"IMPORT: UP table data: {up_table_data}")
    
    if not n_clicks:
        return ""
    
    if not parsed_data_json or not file_path:
        return dbc.Alert("Please upload a file first!", color="warning")
    
    try:
        print("IMPORT: Starting import...")
        
        # Parse stored data
        parsed_data = json.loads(parsed_data_json)
        units = parsed_data.get('units', [])
        file_format = parsed_data.get('file_format', 'raw_dasgip')
        
        if not units:
            return dbc.Alert("No units found in uploaded file!", color="warning")
        
        print(f"IMPORT: Found {len(units)} units, format: {file_format}")
        
        # Re-parse/re-process the file based on format
        if file_format == 'database_export':
            # Re-process database export
            export_data = process_database_export_csv(file_path)
            print(f"IMPORT: Re-processed database export with {len(export_data)} UP numbers")
        else:
            # Re-parse raw DASGIP file
            from plotly_integration.process_development.cell_culture.dasgip.helpers.dasgip_parser import DasgipFinalParser
            parser = DasgipFinalParser(file_path)
            success = parser.parse()
            
            if not success:
                return dbc.Alert("Failed to re-parse file!", color="danger")
        
        # Get UP mapping from DataTable
        up_mapping = {}
        
        if up_table_data:
            print(f"IMPORT: Processing UP mapping from table...")
            for row in up_table_data:
                unit_no = row.get('unit_number')
                up_number = row.get('up_number', '').strip()
                if unit_no and up_number:
                    up_mapping[unit_no] = up_number
                    print(f"IMPORT: Unit {unit_no} -> UP {up_number}")
        
        # Auto-generate UP numbers for units without explicit UP numbers
        from django.utils import timezone
        for unit in units:
            unit_no = unit['unit_number']
            if unit_no not in up_mapping:
                up_mapping[unit_no] = f"AUTO_{unit_no}_{timezone.now().strftime('%H%M%S')}"
                print(f"IMPORT: Auto-generated UP for Unit {unit_no}: {up_mapping[unit_no]}")
        
        print(f"IMPORT: Final UP mapping: {up_mapping}")
        
        # Use the appropriate save function based on format
        filename = os.path.basename(file_path) if file_path else "unknown.csv"
        
        if file_format == 'database_export':
            results = save_database_export_to_db(export_data, filename, file_path, up_mapping)
        else:
            results = save_to_database(parser, filename, file_path, up_mapping)
        
        print(f"IMPORT: Results: {results}")
        
        success_msg = dbc.Alert([
            html.H6("Import Successful!"),
            html.Ul([
                html.Li(f"File: {results['file_name']}"),
                html.Li(f"Units imported: {results['units_count']}"),
                html.Li(f"Data points: {results['data_points_count']}"),
                html.Li(f"UP numbers: {list(results['up_mappings'].values())}")
            ])
        ], color="success")
        
        return success_msg
        
    except Exception as e:
        print(f"IMPORT ERROR: {str(e)}")
        import traceback
        print(f"IMPORT TRACEBACK: {traceback.format_exc()}")
        
        return dbc.Alert([
            html.H6("Import Failed!"),
            html.P(f"Error: {str(e)}"),
            html.Pre(traceback.format_exc()[:500])  # Truncate traceback
        ], color="danger")


def save_database_export_to_db(export_data, filename, file_path, up_mapping):
    """Save database export data to simplified database schema with consolidation"""
    from django.db import transaction
    from django.utils import timezone
    from datetime import datetime
    import traceback
    import pandas as pd
    
    try:
        print(f"🔄 Starting database export import for: {filename}")
        
        with transaction.atomic():
            # Get user
            user = User.objects.first()
            if not user:
                raise Exception("No user found in database")
            
            runs_created = 0
            data_points_created = 0
            up_mappings_used = {}
            
            for up_number, up_info in export_data.items():
                print(f"🧪 Processing UP {up_number}")
                
                # Use provided UP mapping or keep the original UP number
                mapped_up = up_mapping.get(up_number, up_number)
                
                # Create bioreactor run record (metadata)
                run = USPBioreactorRun.objects.create(
                    up_number=mapped_up,
                    file_name=filename,
                    file_path=file_path,
                    project_name='Database Export',
                    unit_number=up_info['unit_number'],
                    setup_name=up_info['setup_name'],
                    start_timestamp=up_info['start_timestamp'],
                    stop_timestamp=up_info['stop_timestamp'],
                    uploaded_by=user,
                    host='Database Export',
                    comment=f'Re-imported from {filename}'
                )
                runs_created += 1
                up_mappings_used[up_number] = mapped_up
                print(f"Created run record: {mapped_up}")
                
                # Get the data for this UP number
                df = up_info['data']
                print(f"UP {up_number} raw data shape: {df.shape}")
                
                if not df.empty:
                    print(f"Processing {len(df)} data rows for UP {up_number}...")
                    
                    # Helper function to convert NaN to None
                    def safe_float(value):
                        if pd.isna(value):
                            return None
                        return float(value) if value is not None else None
                    
                    # Prepare time series data - import ALL rows without consolidation
                    timeseries_data = []
                    for _, row in df.iterrows():
                        if pd.notna(row.get('timestamp')):
                            # Create time series record with all parameters
                            timeseries_record = USPTimeSeriesData(
                                run=run,
                                timestamp=row['timestamp'],
                                duration=safe_float(row.get('duration')),
                                # Map all the parameters from DataFrame to model fields
                                do_pv=safe_float(row.get('do_pv')),
                                do_sp=safe_float(row.get('do_sp')), 
                                do_out=safe_float(row.get('do_out')),
                                ph_pv=safe_float(row.get('ph_pv')),
                                ph_sp=safe_float(row.get('ph_sp')),
                                ph_out=safe_float(row.get('ph_out')),
                                temp_pv=safe_float(row.get('temp_pv')),
                                temp_sp=safe_float(row.get('temp_sp')),
                                temp_out=safe_float(row.get('temp_out')),
                                rpm_pv=safe_float(row.get('rpm_pv')),
                                rpm_sp=safe_float(row.get('rpm_sp')),
                                volume_pv=safe_float(row.get('volume_pv')),
                                air_flow_pv=safe_float(row.get('air_flow_pv')),
                                air_flow_sp=safe_float(row.get('air_flow_sp')),
                                feed_a_pv=safe_float(row.get('feed_a_pv')),
                                feed_a_sp=safe_float(row.get('feed_a_sp')),
                                feed_b_pv=safe_float(row.get('feed_b_pv')),
                                feed_b_sp=safe_float(row.get('feed_b_sp')),
                                o2_conc_pv=safe_float(row.get('o2_conc_pv')),
                                o2_conc_sp=safe_float(row.get('o2_conc_sp')),
                                co2_conc_pv=safe_float(row.get('co2_conc_pv')),
                                co2_conc_sp=safe_float(row.get('co2_conc_sp'))
                            )
                            timeseries_data.append(timeseries_record)
                    
                    print(f"Bulk creating {len(timeseries_data)} time series records for {mapped_up}")
                    
                    # Bulk create time series data in batches
                    batch_size = 1000
                    for i in range(0, len(timeseries_data), batch_size):
                        batch = timeseries_data[i:i+batch_size]
                        USPTimeSeriesData.objects.bulk_create(batch)
                        data_points_created += len(batch)
                        print(f"Created batch {i//batch_size + 1}: {len(batch)} records")
                else:
                    print(f"No time series data for UP {up_number}")
            
            print(f"Database export import completed!")
            print(f"Summary:")
            print(f"  - Bioreactor runs created: {runs_created}")
            print(f"  - Time series data points: {data_points_created}")
            print(f"  - UP mappings: {up_mappings_used}")
            
            return {
                'file_name': filename,
                'experiment_name': 'Database Export',
                'units_count': runs_created,
                'tracks_count': 24,  # Approximate sensor count
                'data_points_count': data_points_created,
                'up_mappings': up_mappings_used
            }
            
    except Exception as e:
        print(f"Error during database export import: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise e


def save_to_database(parser, filename, file_path, up_mapping):
    """Save parsed data to simplified database schema"""
    from django.db import transaction
    from django.utils import timezone
    from datetime import datetime
    import traceback
    import pandas as pd
    
    try:
        print(f"Starting simplified database import for: {filename}")
        
        with (transaction.atomic()):
            # Get user
            user = User.objects.first()
            if not user:
                raise Exception("No user found in database")
            
            # Get experiment info
            exp_info = parser.get_experiment_info()
            units_info = parser.get_units_info()
            
            print(f"Processing {len(units_info)} units: {[u['unit_number'] for u in units_info]}")
            
            runs_created = 0
            data_points_created = 0
            up_mappings_used = {}
            
            for unit_info in units_info:
                unit_no = unit_info['unit_number']
                up_number = up_mapping.get(unit_no, f"AUTO_{unit_no}_{timezone.now().strftime('%Y%m%d_%H%M')}")
                
                print(f"Processing Unit {unit_no} -> UP {up_number}")
                
                # Create bioreactor run record (metadata)
                run = USPBioreactorRun.objects.create(
                    up_number=up_number,
                    file_name=filename,
                    file_path=file_path,
                    project_name=exp_info.get('project_name', 'Unknown'),
                    unit_number=unit_no,
                    setup_name=unit_info.get('setup_name', f'Unit {unit_no}'),
                    start_timestamp=unit_info.get('start_timestamp', timezone.now()),
                    stop_timestamp=unit_info.get('stop_timestamp', timezone.now()),
                    uploaded_by=user,
                    host=exp_info.get('host', 'Unknown'),
                    comment=f'Imported from {filename}'
                )
                runs_created += 1
                up_mappings_used[unit_no] = up_number
                print(f"Created run record: {up_number}")
                
                # Get ALL time series data for this unit (no row limit)
                df = parser.get_sample_data(unit_no, None)  # Get ALL data points
                print(f"Unit {unit_no} raw data shape: {df.shape}")
                
                if not df.empty:
                    print(f"Processing {len(df)} data rows for Unit {unit_no}...")
                    
                    # Helper function to convert NaN to None
                    def safe_float(value):
                        if pd.isna(value):
                            return None
                        return float(value) if value is not None else None
                    
                    # Prepare time series data - import ALL rows without consolidation
                    timeseries_data = []
                    for _, row in df.iterrows():
                        if pd.notna(row.get('timestamp')):
                            # Create time series record with all parameters
                            timeseries_record = USPTimeSeriesData(
                                run=run,
                                timestamp=row['timestamp'],
                                duration=safe_float(row.get('duration')),
                                # Map all the parameters from DataFrame to model fields
                                do_pv=safe_float(row.get('do_pv')),
                                do_sp=safe_float(row.get('do_sp')), 
                                do_out=safe_float(row.get('do_out')),
                                ph_pv=safe_float(row.get('ph_pv')),
                                ph_sp=safe_float(row.get('ph_sp')),
                                ph_out=safe_float(row.get('ph_out')),
                                temp_pv=safe_float(row.get('temp_pv')),
                                temp_sp=safe_float(row.get('temp_sp')),
                                temp_out=safe_float(row.get('temp_out')),
                                rpm_pv=safe_float(row.get('rpm_pv')),
                                rpm_sp=safe_float(row.get('rpm_sp')),
                                volume_pv=safe_float(row.get('volume_pv')),
                                air_flow_pv=safe_float(row.get('air_flow_pv')),
                                air_flow_sp=safe_float(row.get('air_flow_sp')),
                                feed_a_pv=safe_float(row.get('feed_a_pv')),
                                feed_a_sp=safe_float(row.get('feed_a_sp')),
                                feed_b_pv=safe_float(row.get('feed_b_pv')),
                                feed_b_sp=safe_float(row.get('feed_b_sp')),
                                o2_conc_pv=safe_float(row.get('o2_conc_pv')),
                                o2_conc_sp=safe_float(row.get('o2_conc_sp')),
                                co2_conc_pv=safe_float(row.get('co2_conc_pv')),
                                co2_conc_sp=safe_float(row.get('co2_conc_sp'))
                            )
                            timeseries_data.append(timeseries_record)
                    
                    print(f"Bulk creating {len(timeseries_data)} time series records for {up_number}")
                    
                    # Bulk create time series data in batches
                    batch_size = 1000
                    for i in range(0, len(timeseries_data), batch_size):
                        batch = timeseries_data[i:i+batch_size]
                        USPTimeSeriesData.objects.bulk_create(batch)
                        data_points_created += len(batch)
                        print(f"Created batch {i//batch_size + 1}: {len(batch)} records")
                else:
                    print(f"No time series data for Unit {unit_no}")
            
            print(f"Simplified import completed!")
            print(f"Summary:")
            print(f"  - Bioreactor runs created: {runs_created}")
            print(f"  - Time series data points: {data_points_created}")
            print(f"  - UP mappings: {up_mappings_used}")
            
            return {
                'file_name': filename,
                'experiment_name': exp_info.get('project_name', 'Unknown'),
                'units_count': runs_created,
                'tracks_count': len(units_info) * 22,  # Approx 22 parameters per unit
                'data_points_count': data_points_created,
                'up_mappings': up_mappings_used
            }
            
    except Exception as e:
        print(f"Error during simplified import: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise e