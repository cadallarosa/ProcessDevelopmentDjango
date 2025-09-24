"""
Data Entry App
Excel-like interface for bulk analytical data entry with validation and import/export
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table, no_update, ALL
import dash
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
import json
import io
import base64
from datetime import datetime
from django.db import transaction
from django.contrib.auth.models import User
from plotly_integration.models import (
    FormulationExperiment, 
    FormulationMatrix, 
    FormulationComponent, 
    FormulationSample
)

app = DjangoDash("DataEntryApp", external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
], suppress_callback_exceptions=True)

def get_experiment_options():
    """Get available experiments for dropdown"""
    experiments = FormulationExperiment.objects.all().order_by('-created_date')
    return [{'label': f"{exp.experiment_id} - {exp.name}", 'value': exp.experiment_id} 
            for exp in experiments]

def get_data_entry_samples(experiment_id, storage_condition, timepoint):
    """Get samples for data entry based on filters"""
    if not experiment_id:
        return []

    query = FormulationSample.objects.filter(
        formulation__experiment_id=experiment_id
    ).select_related('formulation').prefetch_related('formulation__components')

    if storage_condition and storage_condition != 'all':
        query = query.filter(storage_condition=storage_condition)

    if timepoint is not None:
        query = query.filter(time_point_months=timepoint)

    samples = query.order_by('formulation__formulation_number', 'storage_condition', 'time_point_months')

    # Get day 0 pull date for calculating actual timepoints
    day_0_sample = FormulationSample.objects.filter(
        formulation__experiment_id=experiment_id,
        time_point_months=0
    ).first()

    data = []
    for sample in samples:
        # Get buffer components for display
        buffers = sample.formulation.components.filter(component_type='buffer')
        buffer_summary = ', '.join([f"{b.name} {b.concentration}{b.unit}" for b in buffers])

        # Calculate actual timepoint in months if both pull dates exist
        actual_timepoint_months = None
        if sample.pull_date and day_0_sample and day_0_sample.pull_date:
            days_diff = (sample.pull_date - day_0_sample.pull_date).days
            actual_timepoint_months = round(days_diff / 30.44, 2)  # Convert to months

        data.append({
            'sample_id': sample.sample_id,
            'formulation_number': sample.formulation.formulation_number,
            'formulation_display': f"F{sample.formulation.formulation_number:02d}",
            'buffer_system': buffer_summary,
            'target_ph': sample.formulation.target_ph,
            'storage_condition': sample.storage_condition,
            'time_point_months': sample.time_point_months,
            'actual_timepoint_months': actual_timepoint_months,  # Calculated months from T0
            'pull_date': sample.pull_date.strftime('%Y-%m-%d') if sample.pull_date else '',
            
            # Editable analytical data
            'appearance': sample.appearance or '',
            'concentration_mg_ml': sample.concentration_mg_ml,
            'ph_measured': sample.ph_measured,
            'osmolality_measured': sample.osmolality_measured,
            
            # SEC data
            'sec_result_id': sample.sec_result_id or '',
            'hmw': sample.hmw,
            'main': sample.main,
            'lmw': sample.lmw,
            'total_area': sample.total_area,
            
            # Thermal data
            'tm_celsius': sample.tm_celsius,
            'scattering_onset': sample.scattering_onset,
            
            # Metadata
            'analysis_date': sample.analysis_date.strftime('%Y-%m-%d') if sample.analysis_date else '',
            'notes': sample.notes or ''
        })
    
    return data

def validate_data_entry(data):
    """Validate data entry for common issues"""
    errors = []
    warnings = []
    
    for i, row in enumerate(data):
        row_num = i + 1
        
        # SEC validation - should sum to ~100%
        hmw = row.get('hmw')
        main = row.get('main') 
        lmw = row.get('lmw')
        
        if all(x is not None for x in [hmw, main, lmw]):
            total_pct = hmw + main + lmw
            if abs(total_pct - 100) > 5:  # Allow 5% tolerance
                warnings.append(f"Row {row_num}: SEC percentages sum to {total_pct:.1f}% (should be ~100%)")
        
        # pH validation
        ph = row.get('ph_measured')
        if ph is not None:
            if ph < 3 or ph > 11:
                warnings.append(f"Row {row_num}: pH {ph} seems unusual for protein formulation")
        
        # Concentration validation
        conc = row.get('concentration_mg_ml')
        if conc is not None:
            if conc < 0 or conc > 300:
                warnings.append(f"Row {row_num}: Concentration {conc} mg/mL seems unusual")
        
        # Tm validation
        tm = row.get('tm_celsius')
        if tm is not None:
            if tm < 30 or tm > 100:
                warnings.append(f"Row {row_num}: Tm {tm}°C seems unusual for protein")
    
    return errors, warnings

# Layout
app.layout = dbc.Container([
    dcc.Store(id="data-entry-store"),
    dcc.Store(id="validation-results-store"),
    
    # Header
    dbc.Row([
        dbc.Col([
            html.H1([
                html.I(className="fas fa-table text-primary me-3"),
                "Analytical Data Entry"
            ], className="mb-3"),
            html.P("Excel-like interface for bulk analytical data entry with validation", 
                   className="lead text-muted")
        ])
    ]),
    
    # Filters and Controls
    dbc.Card([
        dbc.CardHeader([
            html.H5([html.I(className="fas fa-filter me-2"), "Data Entry Filters"], className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Experiment"),
                    dcc.Dropdown(
                        id="experiment-dropdown",
                        options=[],  # Will be populated by callback
                        placeholder="Select experiment...",
                        value=None
                    )
                ], width=4),
                dbc.Col([
                    dbc.Label("Storage Condition"),
                    dcc.Dropdown(
                        id="storage-condition-dropdown",
                        options=[
                            {'label': 'All Conditions', 'value': 'all'},
                            {'label': '4°C', 'value': '4C'},
                            {'label': '25°C', 'value': '25C'},
                            {'label': '40°C', 'value': '40C'},
                            {'label': '-80°C', 'value': '-80C'},
                            {'label': 'Freeze/Thaw', 'value': 'FT'}
                        ],
                        value="all"
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("Timepoint (months)"),
                    dcc.Dropdown(
                        id="timepoint-dropdown",
                        placeholder="Select timepoint...",
                        value=None
                    )
                ], width=3),
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-sync me-2"), "Load Data"],
                        id="load-data-btn",
                        color="primary",
                        className="mt-4"
                    )
                ], width=2)
            ])
        ])
    ], className="mb-4"),
    
    # Import/Export Controls
    dbc.Card([
        dbc.CardHeader([
            html.H5([html.I(className="fas fa-exchange-alt me-2"), "Import/Export"], className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dcc.Upload(
                        id="upload-data",
                        children=dbc.Button(
                            [html.I(className="fas fa-upload me-2"), "Import Excel/CSV"],
                            color="success"
                        ),
                        multiple=False
                    )
                ], width=3),
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-download me-2"), "Export Template"],
                        id="export-template-btn",
                        color="secondary"
                    )
                ], width=3),
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-download me-2"), "Export Data"],
                        id="export-data-btn",
                        color="info"
                    )
                ], width=3),
            ])
        ])
    ], className="mb-4"),
    
    
    # Data Entry Table
    html.Div(id="data-entry-table-container"),
    
    # Save Controls
    html.Div([
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-save me-2"), "Save All Changes"],
                            id="save-data-btn",
                            color="primary",
                            size="lg"
                        )
                    ], width=3),
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-undo me-2"), "Discard Changes"],
                            id="discard-changes-btn",
                            color="secondary",
                            size="lg"
                        )
                    ], width=3),
                    dbc.Col([
                        html.Div(id="save-status")
                    ], width=6)
                ])
            ])
        ])
    ], id="save-controls", style={'display': 'none'}, className="mt-4"),
    
    # Alerts
    html.Div(id="alerts-container")
    
], fluid=True)

@app.callback(
    Output("timepoint-dropdown", "options"),
    Input("experiment-dropdown", "value")
)
def update_timepoint_options(experiment_id):
    if not experiment_id:
        return []
    
    # Get unique timepoints for this experiment
    timepoints = FormulationSample.objects.filter(
        formulation__experiment_id=experiment_id
    ).values_list('time_point_months', flat=True).distinct().order_by('time_point_months')
    
    return [{'label': f"{tp} months", 'value': tp} for tp in timepoints]

@app.callback(
    [Output("data-entry-table-container", "children"),
     Output("save-controls", "style")],
    Input("load-data-btn", "n_clicks"),
    [State("experiment-dropdown", "value"),
     State("storage-condition-dropdown", "value"),
     State("timepoint-dropdown", "value")],
    prevent_initial_call=True
)
def load_data_entry_table(n_clicks, experiment_id, storage_condition, timepoint):
    if not n_clicks or not experiment_id:
        return html.Div(), {'display': 'none'}
    
    data = get_data_entry_samples(experiment_id, storage_condition, timepoint)
    
    if not data:
        return dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "No samples found for the selected criteria."
        ], color="info"), {'display': 'none'}
    
    # Define columns for the data table
    columns = [
        # Read-only identification columns
        {'name': 'Sample ID', 'id': 'sample_id', 'editable': False},
        {'name': 'Form', 'id': 'formulation_display', 'editable': False},
        {'name': 'Buffer System', 'id': 'buffer_system', 'editable': False},
        {'name': 'Target pH', 'id': 'target_ph', 'type': 'numeric', 'editable': False},
        {'name': 'Storage', 'id': 'storage_condition', 'editable': False},
        {'name': 'Nominal\nTimepoint', 'id': 'time_point_months', 'type': 'numeric', 'editable': False},
        {'name': 'Pull Date', 'id': 'pull_date', 'editable': True},
        {'name': 'Actual\nTimepoint', 'id': 'actual_timepoint_months', 'type': 'numeric', 'format': {'specifier': '.2f'}, 'editable': False},
        
        # Editable analytical data columns
        {'name': 'Appearance', 'id': 'appearance', 'editable': True},
        {'name': 'Conc (mg/mL)', 'id': 'concentration_mg_ml', 'type': 'numeric', 'editable': True},
        {'name': 'pH Measured', 'id': 'ph_measured', 'type': 'numeric', 'format': {'specifier': '.2f'}, 'editable': True},
        {'name': 'Osmolality', 'id': 'osmolality_measured', 'type': 'numeric', 'editable': True},
        
        # SEC columns
        {'name': 'SEC Result ID', 'id': 'sec_result_id', 'editable': True},
        {'name': 'HMW %', 'id': 'hmw', 'type': 'numeric', 'format': {'specifier': '.2f'}, 'editable': True},
        {'name': 'Main %', 'id': 'main', 'type': 'numeric', 'format': {'specifier': '.2f'}, 'editable': True},
        {'name': 'LMW %', 'id': 'lmw', 'type': 'numeric', 'format': {'specifier': '.2f'}, 'editable': True},
        {'name': 'Total Area', 'id': 'total_area', 'type': 'numeric', 'editable': True},
        
        # Thermal columns
        {'name': 'Tm (°C)', 'id': 'tm_celsius', 'type': 'numeric', 'format': {'specifier': '.1f'}, 'editable': True},
        {'name': 'Scattering Onset', 'id': 'scattering_onset', 'type': 'numeric', 'format': {'specifier': '.1f'}, 'editable': True},
        
        # Metadata
        {'name': 'Analysis Date', 'id': 'analysis_date', 'editable': True},
        {'name': 'Notes', 'id': 'notes', 'editable': True}
    ]
    
    data_table = dash_table.DataTable(
        id="data-entry-table",
        data=data,
        columns=columns,
        editable=True,
        style_cell={
            'textAlign': 'left',
            'minWidth': '80px',
            'width': 'auto',
            'whiteSpace': 'normal',
            'padding': '8px'
        },
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold',
            'padding': '8px'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            },
            # Highlight editable columns
            {
                'if': {'column_editable': True},
                'backgroundColor': 'rgb(255, 255, 240)'
            }
        ],
        fixed_columns={'headers': True, 'data': 2},  # Fix first 2 columns
        style_table={
            'overflowX': 'auto',
            'width': '100%',
            'minWidth': '100%'
        },
        export_format="xlsx",
        export_headers="display",
        fill_width=True
    )
    
    table_container = dbc.Card([
        dbc.CardHeader([
            html.H5([html.I(className="fas fa-edit me-2"), f"Data Entry ({len(data)} samples)"], className="mb-0"),
            html.P("Click cells to edit. Yellow cells are editable.", className="text-muted small mb-0")
        ]),
        dbc.CardBody([
            data_table
        ])
    ])
    
    return table_container, {'display': 'block'}


@app.callback(
    Output("data-entry-table", "data"),
    [Input("upload-data", "contents"),
     Input("data-entry-table", "data_timestamp")],
    [State("upload-data", "filename"),
     State("data-entry-table", "data"),
     State("experiment-dropdown", "value")],
    prevent_initial_call=True
)
def update_table_data(contents, data_timestamp, filename, current_data, experiment_id):
    ctx = dash.callback_context

    if not ctx.triggered:
        return no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Handle file upload
    if trigger_id == "upload-data" and contents is not None:
        try:
            # Parse the uploaded file
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)

            if filename.endswith('.csv'):
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            elif filename.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(io.BytesIO(decoded))
            else:
                return current_data  # Return unchanged data for unsupported files

            # Map imported data to current format
            imported_data = df.to_dict('records')

            # Update current data with imported values
            if current_data:
                sample_id_map = {row['sample_id']: i for i, row in enumerate(current_data)}

                for import_row in imported_data:
                    sample_id = import_row.get('sample_id')
                    if sample_id in sample_id_map:
                        idx = sample_id_map[sample_id]
                        # Update editable fields only
                        editable_fields = [
                            'pull_date', 'appearance', 'concentration_mg_ml', 'ph_measured', 'osmolality_measured',
                            'sec_result_id', 'hmw', 'main', 'lmw', 'total_area',
                            'tm_celsius', 'scattering_onset', 'analysis_date', 'notes'
                        ]

                        for field in editable_fields:
                            if field in import_row:
                                current_data[idx][field] = import_row[field]

            return current_data

        except Exception as e:
            print(f"Import error: {e}")
            return current_data

    # Handle dynamic updates for Days from T0 calculation
    elif trigger_id == "data-entry-table" and current_data:
        # Get day 0 pull date for this experiment
        if experiment_id:
            day_0_sample = FormulationSample.objects.filter(
                formulation__experiment_id=experiment_id,
                time_point_months=0
            ).first()

            if day_0_sample and day_0_sample.pull_date:
                # Update the actual_timepoint_months for each row based on pull_date
                for row in current_data:
                    pull_date_str = row.get('pull_date')
                    if pull_date_str:
                        try:
                            from datetime import datetime
                            pull_date_obj = datetime.strptime(pull_date_str, '%Y-%m-%d').date()
                            days_diff = (pull_date_obj - day_0_sample.pull_date).days
                            months_diff = round(days_diff / 30.44, 2)  # Convert to months
                            row['actual_timepoint_months'] = months_diff
                        except (ValueError, TypeError):
                            row['actual_timepoint_months'] = None
                    else:
                        row['actual_timepoint_months'] = None

        return current_data

    return no_update

@app.callback(
    Output("alerts-container", "children", allow_duplicate=True),
    [Input("export-template-btn", "n_clicks"),
     Input("export-data-btn", "n_clicks")],
    [State("experiment-dropdown", "value"),
     State("storage-condition-dropdown", "value"),
     State("timepoint-dropdown", "value"),
     State("data-entry-table", "data")],
    prevent_initial_call=True
)
def handle_exports(template_clicks, data_clicks, experiment_id, storage_condition, timepoint, table_data):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return no_update
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == "export-template-btn":
        if not experiment_id:
            return dbc.Alert("Please select an experiment first", color="warning", dismissable=True)
        
        # Create template with sample structure
        template_data = get_data_entry_samples(experiment_id, storage_condition, timepoint)
        
        if template_data:
            # Clear analytical data for template
            for row in template_data:
                analytical_fields = [
                    'appearance', 'concentration_mg_ml', 'ph_measured', 'osmolality_measured',
                    'sec_result_id', 'hmw', 'main', 'lmw', 'total_area',
                    'tm_celsius', 'scattering_onset', 'analysis_date', 'notes'
                ]
                for field in analytical_fields:
                    row[field] = ''
            
            df = pd.DataFrame(template_data)
            
            # Save to Downloads folder
            try:
                import os
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"data_entry_template_{experiment_id}_{timestamp}.xlsx"
                
                downloads_path = os.path.expanduser("~/Downloads")
                if os.path.exists(downloads_path):
                    filepath = os.path.join(downloads_path, filename)
                else:
                    filepath = filename
                
                df.to_excel(filepath, index=False, engine='openpyxl')
                
                return dbc.Alert([
                    html.I(className="fas fa-download me-2"),
                    f"Template exported successfully! ({len(template_data)} samples saved to {filepath})"
                ], color="success", dismissable=True)
            except Exception as e:
                return dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Error saving template: {str(e)}. Template prepared with {len(template_data)} samples."
                ], color="warning", dismissable=True)
        
        return dbc.Alert("No samples found to create template", color="warning", dismissable=True)
    
    elif trigger_id == "export-data-btn":
        if not table_data:
            return dbc.Alert("No data to export", color="warning", dismissable=True)
        
        df = pd.DataFrame(table_data)
        
        # Save to Downloads folder
        try:
            import os
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analytical_data_export_{timestamp}.xlsx"
            
            downloads_path = os.path.expanduser("~/Downloads")
            if os.path.exists(downloads_path):
                filepath = os.path.join(downloads_path, filename)
            else:
                filepath = filename
            
            df.to_excel(filepath, index=False, engine='openpyxl')
            
            return dbc.Alert([
                html.I(className="fas fa-download me-2"),
                f"Data exported successfully! ({len(table_data)} samples saved to {filepath})"
            ], color="success", dismissable=True)
        except Exception as e:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Error saving data: {str(e)}. Data prepared for export ({len(table_data)} samples)."
            ], color="warning", dismissable=True)
    
    return no_update

@app.callback(
    Output("alerts-container", "children"),
    Input("save-data-btn", "n_clicks"),
    State("data-entry-table", "data"),
    prevent_initial_call=True
)
def save_data(n_clicks, table_data):
    if not n_clicks or not table_data:
        return no_update
    
    try:
        with transaction.atomic():
            updated_count = 0
            
            for row in table_data:
                sample_id = row['sample_id']
                sample = FormulationSample.objects.get(sample_id=sample_id)
                
                # Update fields
                fields_to_update = [
                    'appearance', 'concentration_mg_ml', 'ph_measured', 'osmolality_measured',
                    'sec_result_id', 'hmw', 'main', 'lmw', 'total_area',
                    'tm_celsius', 'scattering_onset', 'notes'
                ]

                updated = False
                for field in fields_to_update:
                    new_value = row.get(field)
                    # Allow empty strings to be saved as None for text fields (appearance, notes, sec_result_id)
                    # and for numeric fields
                    if new_value == '' or new_value is None:
                        new_value = None
                    
                    if getattr(sample, field) != new_value:
                        setattr(sample, field, new_value)
                        updated = True
                
                # Handle analysis date
                analysis_date = row.get('analysis_date')
                if analysis_date:
                    try:
                        analysis_date_obj = datetime.strptime(analysis_date, '%Y-%m-%d').date()
                        if sample.analysis_date != analysis_date_obj:
                            sample.analysis_date = analysis_date_obj
                            updated = True
                    except ValueError:
                        pass  # Skip invalid dates

                # Handle pull date and calculate timepoint from day 0
                pull_date_str = row.get('pull_date')
                if pull_date_str:
                    try:
                        pull_date_obj = datetime.strptime(pull_date_str, '%Y-%m-%d').date()
                        if sample.pull_date != pull_date_obj:
                            sample.pull_date = pull_date_obj

                            # Get day 0 pull date (first timepoint for this experiment)
                            day_0_sample = FormulationSample.objects.filter(
                                formulation__experiment=sample.formulation.experiment,
                                time_point_months=0
                            ).first()

                            if day_0_sample and day_0_sample.pull_date:
                                # Calculate days between pull dates
                                days_diff = (pull_date_obj - day_0_sample.pull_date).days
                                # Calculate timepoint in months (using 30.44 days per month average)
                                calculated_timepoint = round(days_diff / 30.44, 2)
                                sample.time_point_months = calculated_timepoint
                                sample.pull_day = days_diff  # Store days difference as pull_day

                            updated = True
                    except ValueError:
                        pass  # Skip invalid dates
                
                if updated:
                    sample.save()
                    updated_count += 1
            
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Successfully updated {updated_count} samples! Pull dates automatically calculate timepoints from day 0."
            ], color="success", dismissable=True)
    
    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error saving data: {str(e)}"
        ], color="danger", dismissable=True)

# Auto-load experiments and select most recent, load all timepoint data
@app.callback(
    [Output("experiment-dropdown", "options"),
     Output("experiment-dropdown", "value"),
     Output("timepoint-dropdown", "value")],
    Input("experiment-dropdown", "id"),  # Trigger on component mount
    prevent_initial_call=False
)
def load_experiments_on_page_load(dropdown_id):
    options = get_experiment_options()
    # Auto-select the most recent experiment (first in list)
    value = options[0]['value'] if options else None
    # Auto-select all timepoints (None means all timepoints)
    return options, value, None