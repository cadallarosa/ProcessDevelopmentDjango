"""
Sample Management App
Handles sample generation, scheduling, and tracking for formulation experiments
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table, no_update, ALL
import dash
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
import json
from datetime import datetime, timedelta
from django.db import transaction
from plotly_integration.models import (
    FormulationExperiment, 
    FormulationMatrix, 
    FormulationComponent, 
    FormulationSample
)

app = DjangoDash("SampleManagementApp", external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
], suppress_callback_exceptions=True)

# Storage conditions
STORAGE_CONDITIONS = [
    {'label': '4°C (Refrigerator)', 'value': '4C'},
    {'label': '25°C (Room Temperature)', 'value': '25C'}, 
    {'label': '40°C (Accelerated)', 'value': '40C'},
    {'label': '-80°C (Freezer)', 'value': '-80C'},
    {'label': 'Freeze/Thaw Cycling', 'value': 'FT'},
]

# Common timepoints
TIMEPOINT_PRESETS = [
    {'label': 'T0 only', 'value': [0]},
    {'label': 'Early stability (0, 0.1, 0.2, 0.3, 0.5, 1, 3, 6)', 'value': [0, 0.1, 0.2, 0.3, 0.5, 1, 3, 6]},
    {'label': 'Short term (0, 1, 3 months)', 'value': [0, 1, 3]},
    {'label': 'Standard (0, 1, 3, 6 months)', 'value': [0, 1, 3, 6]},
    {'label': 'Long term (0, 1, 3, 6, 12 months)', 'value': [0, 1, 3, 6, 12]},
    {'label': 'Extended (0, 1, 3, 6, 12, 18, 24 months)', 'value': [0, 1, 3, 6, 12, 18, 24]},
    {'label': 'Custom', 'value': 'custom'}
]

def get_experiment_options():
    """Get available experiments for dropdown"""
    experiments = FormulationExperiment.objects.all().order_by('-created_date')
    return [{'label': f"{exp.experiment_id} - {exp.name}", 'value': exp.experiment_id} 
            for exp in experiments]

def get_formulations_for_experiment(experiment_id):
    """Get formulations for selected experiment"""
    if not experiment_id:
        return []
    
    formulations = FormulationMatrix.objects.filter(
        experiment_id=experiment_id
    ).order_by('formulation_number')
    
    return [{'label': f"F{form.formulation_number:02d} (pH {form.target_ph})", 
             'value': form.formulation_id} for form in formulations]

def get_existing_samples(experiment_id):
    """Get existing samples for an experiment"""
    if not experiment_id:
        return []
    
    samples = FormulationSample.objects.filter(
        formulation__experiment_id=experiment_id
    ).select_related('formulation').order_by(
        'formulation__formulation_number', 'storage_condition', 'time_point_months'
    )
    
    data = []
    for sample in samples:
        data.append({
            'sample_id': sample.sample_id,
            'formulation': f"F{sample.formulation.formulation_number:02d}",
            'storage_condition': sample.storage_condition,
            'time_point_months': sample.time_point_months,
            'pull_date': sample.pull_date.strftime('%Y-%m-%d') if sample.pull_date else 'Not scheduled',
            'pulled': 'Yes' if sample.pull_date and sample.pull_date <= datetime.now().date() else 'No',
            'analyzed': 'Yes' if sample.hmw is not None else 'No',
            'appearance': sample.appearance or '',
            'notes': sample.notes or ''
        })
    
    return data

def generate_sample_id(experiment_id, formulation_number, storage_condition, time_point):
    """Generate sample ID following pattern: EXP-FXX-COND-TPT"""
    time_str = f"{int(time_point)}M" if time_point == int(time_point) else f"{time_point:.1f}M"
    return f"{experiment_id}-F{formulation_number:02d}-{storage_condition}-{time_str}"

# Layout
app.layout = dbc.Container([
    dcc.Store(id="selected-experiment-store"),
    dcc.Store(id="sample-generation-params-store"),
    
    # Header
    dbc.Row([
        dbc.Col([
            html.H1([
                html.I(className="fas fa-test-tube text-primary me-3"),
                "Sample Management & Generation"
            ], className="mb-3"),
            html.P("Generate and manage formulation stability samples across conditions and timepoints", 
                   className="lead text-muted")
        ])
    ]),
    
    # Experiment Selection
    dbc.Card([
        dbc.CardHeader([
            html.H5([html.I(className="fas fa-flask me-2"), "Select Experiment"], className="mb-0")
        ]),
        dbc.CardBody([
            dcc.Dropdown(
                id="experiment-dropdown",
                options=[],  # Will be populated by callback
                placeholder="Select an experiment to manage samples...",
                value=None
            )
        ])
    ], className="mb-4"),
    
    # Sample Generation Section
    html.Div(id="sample-generation-section"),
    
    # Existing Samples Section
    html.Div(id="existing-samples-section"),
    
    # Alerts
    html.Div(id="alerts-container")
    
], fluid=True)

@app.callback(
    [Output("sample-generation-section", "children"),
     Output("existing-samples-section", "children")],
    Input("experiment-dropdown", "value")
)
def update_sample_sections(selected_experiment):
    if not selected_experiment:
        return html.Div(), html.Div()
    
    # Get formulations for the experiment
    formulation_options = get_formulations_for_experiment(selected_experiment)
    existing_samples = get_existing_samples(selected_experiment)
    
    # Sample Generation Section
    generation_section = dbc.Card([
        dbc.CardHeader([
            html.H5([html.I(className="fas fa-magic me-2"), "Generate New Samples"], className="mb-0")
        ]),
        dbc.CardBody([
            # Formulations Selection
            dbc.Row([
                dbc.Col([
                    html.Div([
                        dbc.Label("Select Formulations"),
                        dbc.Checklist(
                            id="select-all-formulations",
                            options=[{"label": "Select All", "value": "all"}],
                            value=["all"],
                            inline=True,
                            className="mb-2"
                        )
                    ]),
                    dcc.Dropdown(
                        id="formulation-selection",
                        options=formulation_options,
                        multi=True,
                        value=[opt['value'] for opt in formulation_options],  # Auto-select all
                        placeholder="Select formulations to include..."
                    )
                ], width=12)
            ], className="mb-3"),
            
            # Storage Conditions Selection
            dbc.Row([
                dbc.Col([
                    dbc.Label("Storage Conditions"),
                    dbc.Checklist(
                        id="storage-conditions-checklist",
                        options=STORAGE_CONDITIONS,
                        value=['4C', '25C'],
                        inline=True
                    )
                ], width=12)
            ], className="mb-3"),
            
            # Timepoints Selection
            dbc.Row([
                dbc.Col([
                    dbc.Label("Timepoint Preset"),
                    dcc.Dropdown(
                        id="timepoint-preset",
                        options=TIMEPOINT_PRESETS,
                        value=[0, 1, 3, 6],
                        placeholder="Select a timepoint preset..."
                    )
                ], width=6),
                dbc.Col([
                    dbc.Label("Custom Timepoints (months, comma-separated)"),
                    dbc.Input(
                        id="custom-timepoints",
                        placeholder="e.g., 0, 0.5, 1, 2, 3, 6, 12",
                        disabled=True
                    )
                ], width=6)
            ], className="mb-3"),
            
            # Start Date
            dbc.Row([
                dbc.Col([
                    dbc.Label("Experiment Start Date"),
                    dbc.Input(
                        id="start-date-input",
                        type="date",
                        value=datetime.now().strftime('%Y-%m-%d')
                    )
                ], width=4),
                dbc.Col([
                    html.Div([
                        html.H6("Sample Preview", className="mb-2"),
                        html.Div(id="sample-preview")
                    ])
                ], width=8)
            ], className="mb-3"),
            
            html.Hr(),
            
            # Generate button
            dbc.Button(
                [html.I(className="fas fa-cogs me-2"), "Generate Samples"],
                id="generate-samples-btn",
                color="primary",
                size="lg"
            )
        ])
    ], className="mb-4")
    
    # Existing Samples Section
    if existing_samples:
        samples_table = dash_table.DataTable(
            id="samples-table",
            data=existing_samples,
            columns=[
                {'name': 'Sample ID', 'id': 'sample_id'},
                {'name': 'Form', 'id': 'formulation'},
                {'name': 'Storage', 'id': 'storage_condition'},
                {'name': 'Timepoint', 'id': 'time_point_months', 'type': 'numeric'},
                {'name': 'Pull Date', 'id': 'pull_date'},
                {'name': 'Pulled', 'id': 'pulled'},
                {'name': 'Analyzed', 'id': 'analyzed'},
                {'name': 'Appearance', 'id': 'appearance'},
                {'name': 'Notes', 'id': 'notes'}
            ],
            style_cell={'textAlign': 'left'},
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                },
                {
                    'if': {'filter_query': '{pulled} = Yes', 'column_id': 'pulled'},
                    'backgroundColor': '#d4edda',
                    'color': 'black',
                },
                {
                    'if': {'filter_query': '{analyzed} = Yes', 'column_id': 'analyzed'},
                    'backgroundColor': '#b3e5fc',
                    'color': 'black',
                }
            ],
            page_size=20,
            sort_action="native",
            filter_action="native",
            row_selectable="multi"
        )
        
        existing_section = dbc.Card([
            dbc.CardHeader([
                html.H5([html.I(className="fas fa-list me-2"), f"Existing Samples ({len(existing_samples)})"], 
                       className="mb-0")
            ]),
            dbc.CardBody([
                samples_table,
                html.Hr(),
                dbc.ButtonGroup([
                    dbc.Button(
                        [html.I(className="fas fa-calendar-plus me-2"), "Schedule Pull"],
                        id="schedule-pull-btn",
                        color="primary"
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-check me-2"), "Mark as Pulled"],
                        id="mark-pulled-btn", 
                        color="success"
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-download me-2"), "Export Schedule"],
                        id="export-schedule-btn",
                        color="secondary"
                    )
                ], className="mt-3")
            ])
        ])
    else:
        existing_section = dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "No samples found for this experiment. Generate samples above."
        ], color="info")
    
    return generation_section, existing_section

def create_existing_samples_section(experiment_id):
    """Helper function to create the existing samples section"""
    # Get existing samples
    existing_samples = get_existing_samples(experiment_id)
    
    if existing_samples:
        samples_table = dash_table.DataTable(
            id="samples-table",
            data=existing_samples,
            columns=[
                {'name': 'Sample ID', 'id': 'sample_id'},
                {'name': 'Form', 'id': 'formulation'},
                {'name': 'Storage', 'id': 'storage_condition'},
                {'name': 'Timepoint', 'id': 'time_point_months', 'type': 'numeric'},
                {'name': 'Pull Date', 'id': 'pull_date'},
                {'name': 'Pulled', 'id': 'pulled'},
                {'name': 'Analyzed', 'id': 'analyzed'},
                {'name': 'Appearance', 'id': 'appearance'},
                {'name': 'Notes', 'id': 'notes'}
            ],
            style_cell={'textAlign': 'left'},
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                },
                {
                    'if': {'filter_query': '{pulled} = Yes', 'column_id': 'pulled'},
                    'backgroundColor': '#d4edda',
                    'color': 'black',
                },
                {
                    'if': {'filter_query': '{analyzed} = Yes', 'column_id': 'analyzed'},
                    'backgroundColor': '#b3e5fc',
                    'color': 'black',
                }
            ],
            page_size=20,
            sort_action="native",
            filter_action="native",
            row_selectable="multi"
        )
        
        existing_section = dbc.Card([
            dbc.CardHeader([
                html.H5([html.I(className="fas fa-list me-2"), f"Existing Samples ({len(existing_samples)})"], 
                       className="mb-0")
            ]),
            dbc.CardBody([
                samples_table,
                html.Hr(),
                dbc.ButtonGroup([
                    dbc.Button(
                        [html.I(className="fas fa-calendar-plus me-2"), "Schedule Pull"],
                        id="schedule-pull-btn",
                        color="primary"
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-check me-2"), "Mark as Pulled"],
                        id="mark-pulled-btn", 
                        color="success"
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-download me-2"), "Export Schedule"],
                        id="export-schedule-btn",
                        color="secondary"
                    )
                ], className="mt-3")
            ])
        ])
    else:
        existing_section = dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "No samples found for this experiment. Generate samples above."
        ], color="info")
    
    return existing_section

@app.callback(
    Output("custom-timepoints", "disabled"),
    Input("timepoint-preset", "value")
)
def toggle_custom_timepoints(preset_value):
    return preset_value != 'custom'

@app.callback(
    Output("sample-preview", "children"),
    [Input("formulation-selection", "value"),
     Input("storage-conditions-checklist", "value"),
     Input("timepoint-preset", "value"),
     Input("custom-timepoints", "value")],
    State("experiment-dropdown", "value")
)
def update_sample_preview(selected_formulations, storage_conditions, timepoint_preset, custom_timepoints, experiment_id):
    if not all([selected_formulations, storage_conditions, experiment_id]):
        return html.P("Select formulations and conditions to see preview", className="text-muted")
    
    # Determine timepoints
    if timepoint_preset == 'custom':
        try:
            timepoints = [float(x.strip()) for x in custom_timepoints.split(',') if x.strip()]
        except (ValueError, AttributeError):
            timepoints = [0]
    else:
        timepoints = timepoint_preset if isinstance(timepoint_preset, list) else [0]
    
    # Calculate total samples
    total_samples = len(selected_formulations) * len(storage_conditions) * len(timepoints)
    
    # Create preview table
    preview_data = []
    for form_id in selected_formulations[:3]:  # Show only first 3 formulations
        form_obj = FormulationMatrix.objects.get(formulation_id=form_id)
        form_label = f"F{form_obj.formulation_number:02d}"
        
        for condition in storage_conditions[:2]:  # Show only first 2 conditions
            for timepoint in timepoints[:3]:  # Show only first 3 timepoints
                sample_id = generate_sample_id(experiment_id, form_obj.formulation_number, condition, timepoint)
                preview_data.append({
                    'Sample ID': sample_id,
                    'Formulation': form_label,
                    'Storage': condition,
                    'Timepoint': f"{timepoint} months"
                })
    
    preview_table = dash_table.DataTable(
        data=preview_data,
        columns=[{'name': col, 'id': col} for col in ['Sample ID', 'Formulation', 'Storage', 'Timepoint']],
        style_cell={'textAlign': 'left', 'fontSize': '12px'},
        page_size=6
    )
    
    more_info = ""
    if len(preview_data) < total_samples:
        more_info = f" (showing first {len(preview_data)} of {total_samples} total samples)"
    
    return html.Div([
        html.P(f"Will generate {total_samples} samples{more_info}", className="fw-bold mb-2"),
        preview_table
    ])

@app.callback(
    Output("alerts-container", "children"),
    Input("generate-samples-btn", "n_clicks"),
    [State("experiment-dropdown", "value"),
     State("formulation-selection", "value"),
     State("storage-conditions-checklist", "value"),
     State("timepoint-preset", "value"),
     State("custom-timepoints", "value"),
     State("start-date-input", "value")],
    prevent_initial_call=True
)
def generate_samples(n_clicks, experiment_id, selected_formulations, storage_conditions, 
                    timepoint_preset, custom_timepoints, start_date):
    if not n_clicks or not all([experiment_id, selected_formulations, storage_conditions]):
        return no_update
    
    try:
        # Determine timepoints
        if timepoint_preset == 'custom':
            try:
                timepoints = [float(x.strip()) for x in custom_timepoints.split(',') if x.strip()]
            except (ValueError, AttributeError):
                return dbc.Alert("Invalid custom timepoints format", color="danger", dismissable=True)
        else:
            timepoints = timepoint_preset if isinstance(timepoint_preset, list) else [0]
        
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        with transaction.atomic():
            samples_created = 0
            
            for form_id in selected_formulations:
                formulation = FormulationMatrix.objects.get(formulation_id=form_id)
                
                for condition in storage_conditions:
                    for timepoint in timepoints:
                        # Generate sample ID
                        sample_id = generate_sample_id(
                            experiment_id, formulation.formulation_number, condition, timepoint
                        )
                        
                        # Check if sample already exists
                        if not FormulationSample.objects.filter(sample_id=sample_id).exists():
                            # Calculate pull date (start date + timepoint months)
                            pull_date = start_date_obj + timedelta(days=timepoint * 30.44)  # Average month length
                            
                            FormulationSample.objects.create(
                                sample_id=sample_id,
                                formulation=formulation,
                                storage_condition=condition,
                                time_point_months=timepoint,
                                pull_date=pull_date if timepoint > 0 else start_date_obj
                            )
                            samples_created += 1
            
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Successfully generated {samples_created} samples!"
            ], color="success", dismissable=True)
    
    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error generating samples: {str(e)}"
        ], color="danger", dismissable=True)

# Export schedule functionality
@app.callback(
    Output("alerts-container", "children", allow_duplicate=True),
    Input("export-schedule-btn", "n_clicks"),
    State("experiment-dropdown", "value"),
    prevent_initial_call=True
)
def export_schedule_to_excel(n_clicks, experiment_id):
    if not n_clicks or not experiment_id:
        return no_update
    
    try:
        # Get samples for the experiment
        existing_samples = get_existing_samples(experiment_id)
        
        if not existing_samples:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "No samples found to export for this experiment."
            ], color="warning", dismissable=True)
        
        # Convert to DataFrame for export
        df = pd.DataFrame(existing_samples)
        
        # Create filename with experiment ID and timestamp
        from datetime import datetime
        import os
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sample_schedule_{experiment_id}_{timestamp}.xlsx"
        
        try:
            # Try to save to Downloads folder or current directory
            downloads_path = os.path.expanduser("~/Downloads")
            if os.path.exists(downloads_path):
                filepath = os.path.join(downloads_path, filename)
            else:
                filepath = filename
            
            # Export to Excel
            df.to_excel(filepath, index=False, engine='openpyxl')
            
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Sample schedule exported successfully! ",
                f"({len(existing_samples)} samples saved to {filepath})"
            ], color="success", dismissable=True)
        except Exception as e:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Error saving file: {str(e)}. Data prepared for export ({len(existing_samples)} samples)."
            ], color="warning", dismissable=True)
        
    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error exporting schedule: {str(e)}"
        ], color="danger", dismissable=True)

# Auto-load experiments and select most recent
@app.callback(
    [Output("experiment-dropdown", "options"),
     Output("experiment-dropdown", "value")],
    Input("experiment-dropdown", "id"),  # Trigger on component mount
    prevent_initial_call=False
)
def load_experiments_on_page_load(dropdown_id):
    options = get_experiment_options()
    # Auto-select the most recent experiment (first in list)
    value = options[0]['value'] if options else None
    return options, value

# Handle Select All checkbox for formulations
@app.callback(
    Output("formulation-selection", "value"),
    [Input("select-all-formulations", "value"),
     Input("formulation-selection", "options")],
    prevent_initial_call=True
)
def handle_select_all_formulations(select_all_value, formulation_options):
    if "all" in (select_all_value or []):
        # Select all formulations
        return [opt['value'] for opt in (formulation_options or [])]
    else:
        # Deselect all
        return []

# Handle Schedule Pull and Mark as Pulled buttons
@app.callback(
    [Output("alerts-container", "children", allow_duplicate=True),
     Output("existing-samples-section", "children", allow_duplicate=True)],
    [Input("schedule-pull-btn", "n_clicks"),
     Input("mark-pulled-btn", "n_clicks")],
    [State("samples-table", "selected_rows"),
     State("samples-table", "data"),
     State("experiment-dropdown", "value")],
    prevent_initial_call=True
)
def handle_pull_actions(schedule_clicks, mark_clicks, selected_rows, table_data, experiment_id):
    import dash
    
    if not dash.callback_context.triggered or not selected_rows or not table_data:
        return no_update, no_update
    
    trigger_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
    
    try:
        # Get selected samples
        selected_sample_ids = [table_data[i]['sample_id'] for i in selected_rows]
        
        if trigger_id == "schedule-pull-btn":
            # Schedule pull dates for selected samples
            updated_count = 0
            for sample_id in selected_sample_ids:
                try:
                    sample = FormulationSample.objects.get(sample_id=sample_id)
                    if not sample.pull_date:
                        # Calculate pull date based on timepoint
                        if sample.formulation and sample.formulation.experiment.start_date:
                            start_date = sample.formulation.experiment.start_date
                            pull_date = start_date + timedelta(days=sample.time_point_months * 30.44)
                            sample.pull_date = pull_date
                            sample.save()
                            updated_count += 1
                except FormulationSample.DoesNotExist:
                    continue
            
            alert = dbc.Alert([
                html.I(className="fas fa-calendar-check me-2"),
                f"Pull dates scheduled for {updated_count} samples!"
            ], color="success", dismissable=True)
            refreshed_table = create_existing_samples_section(experiment_id)
            return alert, refreshed_table
        
        elif trigger_id == "mark-pulled-btn":
            # Mark selected samples as pulled (set pull date to today if not already pulled)
            updated_count = 0
            today = datetime.now().date()
            
            for sample_id in selected_sample_ids:
                try:
                    sample = FormulationSample.objects.get(sample_id=sample_id)
                    if not sample.pull_date or sample.pull_date > today:
                        sample.pull_date = today
                        sample.save()
                        updated_count += 1
                except FormulationSample.DoesNotExist:
                    continue
            
            alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Marked {updated_count} samples as pulled!"
            ], color="success", dismissable=True)
            refreshed_table = create_existing_samples_section(experiment_id)
            return alert, refreshed_table
    
    except Exception as e:
        alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error updating samples: {str(e)}"
        ], color="danger", dismissable=True)
        return alert, no_update
    
    return no_update, no_update