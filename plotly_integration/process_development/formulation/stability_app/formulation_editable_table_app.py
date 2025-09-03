"""
Editable Formulation Data Table App
Direct editing of formulation data with save functionality
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table, no_update
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
import json

from plotly_integration.models import FormulationData

app = DjangoDash("FormulationEditableTableApp")

def get_experiments():
    """Get all available experiments using the property"""
    try:
        experiments = set()
        for sample in FormulationData.objects.all():
            experiments.add(sample.experiment_id)
        return [{'label': exp, 'value': exp} for exp in sorted(list(experiments))]
    except Exception as e:
        print(f"Error fetching experiments: {e}")
        return []

def create_header():
    return html.Div([
        html.H1([
            html.I(className="fas fa-edit me-3", style={"color": "#2E86C1"}),
            "Formulation Data Editor"
        ], className="mb-2"),
        html.P("Edit formulation data directly in the table", className="text-muted mb-4")
    ])

def create_controls():
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Select Experiment:"),
                    dcc.Dropdown(
                        id="experiment-dropdown",
                        options=get_experiments(),
                        value="FD-003",  # Default to FD-003
                        placeholder="Choose experiment...",
                        clearable=False
                    )
                ], width=4),
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-save me-2"),
                        "Save Changes"
                    ], id="save-btn", color="success", className="mt-4", disabled=True),
                    dbc.Button([
                        html.I(className="fas fa-plus me-2"),
                        "Add Row"
                    ], id="add-row-btn", color="primary", className="mt-4 ms-2")
                ], width=4),
                dbc.Col([
                    html.Div(id="save-status", className="mt-4")
                ], width=4)
            ])
        ])
    ], className="mb-4")

# Define columns exactly matching Excel structure
COLUMNS = [
    {"name": "Sample Number", "id": "sample_number", "editable": False, "type": "text"},
    {"name": "Buffer", "id": "buffer", "editable": True, "type": "text"},
    {"name": "pH", "id": "ph", "editable": True, "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "Excipients", "id": "excipients", "editable": True, "type": "text"},
    {"name": "Formulation", "id": "formulation", "editable": True, "type": "text"},
    {"name": "Condition", "id": "condition", "editable": True, "type": "text"},
    {"name": "Pull Day", "id": "pull_day", "editable": True, "type": "numeric"},
    {"name": "Time Point (months)", "id": "time_point_months", "editable": True, "type": "numeric", "format": {"specifier": ".1f"}},
    {"name": "Appearance", "id": "appearance", "editable": True, "type": "text"},
    {"name": "Concentration (mg/mL)", "id": "concentration", "editable": True, "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "pH (measured)", "id": "ph_measured", "editable": True, "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "Result ID", "id": "result_id", "editable": True, "type": "text"},
    {"name": "HMW", "id": "hmw", "editable": True, "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "Main", "id": "main", "editable": True, "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "LMW", "id": "lmw", "editable": True, "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "Total Area", "id": "total_area", "editable": True, "type": "numeric"},
    {"name": "Osmolality (mOsm/kg)", "id": "osmolality", "editable": True, "type": "numeric"},
    {"name": "Tm (°C)", "id": "tm_celsius", "editable": True, "type": "numeric", "format": {"specifier": ".1f"}},
    {"name": "Scattering Onset", "id": "scattering_onset", "editable": True, "type": "numeric", "format": {"specifier": ".1f"}},
]

# Main Layout
app.layout = dbc.Container([
    dcc.Store(id='original-data-store'),
    dcc.Store(id='has-changes-store', data=False),
    
    create_header(),
    create_controls(),
    
    html.Div([
        html.Div(id="data-table-container")
    ]),
    
    dcc.Loading(
        id="loading",
        children=html.Div(id="loading-output"),
        type="default",
    )
], fluid=True, className="p-4")

# Callbacks
@app.callback(
    [Output('data-table-container', 'children'),
     Output('original-data-store', 'data')],
    Input('experiment-dropdown', 'value')
)
def load_table(experiment_id):
    if not experiment_id:
        return html.Div([
            dbc.Alert("Please select an experiment to view data.", color="info", className="text-center")
        ]), {}
    
    try:
        # Get data for selected experiment using the property
        all_samples = FormulationData.objects.all()
        filtered_samples = [s for s in all_samples if s.experiment_id == experiment_id]
        
        if not filtered_samples:
            return html.Div([
                dbc.Alert(f"No data found for experiment {experiment_id}.", color="warning", className="text-center")
            ]), {}
        
        # Convert to DataFrame-like structure
        data = []
        for sample in filtered_samples:
            data.append({
                'id': sample.id,
                'sample_number': sample.sample_number,
                'buffer': sample.buffer,
                'ph': sample.ph,
                'excipients': sample.excipients,
                'formulation': sample.formulation,
                'condition': sample.condition,
                'pull_day': sample.pull_day,
                'time_point_months': sample.time_point_months,
                'appearance': sample.appearance,
                'concentration': sample.concentration,
                'ph_measured': sample.ph_measured,
                'result_id': sample.result_id,
                'hmw': sample.hmw,
                'main': sample.main,
                'lmw': sample.lmw,
                'total_area': sample.total_area,
                'osmolality': sample.osmolality,
                'tm_celsius': sample.tm_celsius,
                'scattering_onset': sample.scattering_onset,
            })
        
        # Sort by sample number
        data.sort(key=lambda x: x['sample_number'])
        
        table = html.Div([
            html.H5(f"Data for Experiment: {experiment_id} ({len(data)} samples)", className="mb-3"),
            dash_table.DataTable(
                id='editable-table',
                data=data,
                columns=COLUMNS,
                editable=True,
                row_deletable=True,
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left', 
                    'fontSize': 12, 
                    'fontFamily': 'Arial',
                    'padding': '8px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'minWidth': '100px',
                    'maxWidth': '200px',
                },
                style_header={
                    'backgroundColor': '#2E86C1', 
                    'color': 'white',
                    'fontWeight': 'bold',
                    'textAlign': 'center'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#F8F9FA'
                    },
                    {
                        'if': {'column_id': 'sample_number'},
                        'backgroundColor': '#E3F2FD',
                        'fontWeight': 'bold'
                    }
                ],
                page_size=25,
                sort_action="native",
                filter_action="native",
                export_format="xlsx",
                export_headers="display",
                fill_width=False
            )
        ])
        
        return table, data
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return html.Div([
            dbc.Alert(f"Error loading data: {str(e)}", color="danger")
        ]), {}

@app.callback(
    [Output('has-changes-store', 'data'),
     Output('save-btn', 'disabled')],
    [Input('editable-table', 'data'),
     Input('editable-table', 'data_previous')],
    [State('original-data-store', 'data')],
    prevent_initial_call=True
)
def detect_changes(current_data, previous_data, original_data):
    if not current_data or not original_data:
        return False, True
    
    # Compare current data with original
    has_changes = current_data != original_data
    return has_changes, not has_changes

@app.callback(
    Output('save-status', 'children'),
    Input('save-btn', 'n_clicks'),
    [State('editable-table', 'data'),
     State('original-data-store', 'data')],
    prevent_initial_call=True
)
def save_changes(n_clicks, current_data, original_data):
    if not n_clicks or not current_data:
        return ""
    
    try:
        saved_count = 0
        errors = []
        
        # Create a map of original data by ID for quick lookup
        original_map = {item.get('id'): item for item in original_data if item.get('id')}
        
        for row in current_data:
            try:
                row_id = row.get('id')
                if not row_id:
                    continue
                
                # Get the database object
                sample = FormulationData.objects.get(id=row_id)
                
                # Update fields if they changed
                original_row = original_map.get(row_id, {})
                
                if row.get('buffer') != original_row.get('buffer'):
                    sample.buffer = row.get('buffer')
                if row.get('ph') != original_row.get('ph'):
                    sample.ph = row.get('ph')
                if row.get('excipients') != original_row.get('excipients'):
                    sample.excipients = row.get('excipients')
                if row.get('formulation') != original_row.get('formulation'):
                    sample.formulation = row.get('formulation')
                if row.get('condition') != original_row.get('condition'):
                    sample.condition = row.get('condition')
                if row.get('pull_day') != original_row.get('pull_day'):
                    sample.pull_day = row.get('pull_day')
                if row.get('time_point_months') != original_row.get('time_point_months'):
                    sample.time_point_months = row.get('time_point_months')
                if row.get('appearance') != original_row.get('appearance'):
                    sample.appearance = row.get('appearance')
                if row.get('concentration') != original_row.get('concentration'):
                    sample.concentration = row.get('concentration')
                if row.get('ph_measured') != original_row.get('ph_measured'):
                    sample.ph_measured = row.get('ph_measured')
                if row.get('result_id') != original_row.get('result_id'):
                    sample.result_id = row.get('result_id')
                if row.get('hmw') != original_row.get('hmw'):
                    sample.hmw = row.get('hmw')
                if row.get('main') != original_row.get('main'):
                    sample.main = row.get('main')
                if row.get('lmw') != original_row.get('lmw'):
                    sample.lmw = row.get('lmw')
                if row.get('total_area') != original_row.get('total_area'):
                    sample.total_area = row.get('total_area')
                if row.get('osmolality') != original_row.get('osmolality'):
                    sample.osmolality = row.get('osmolality')
                if row.get('tm_celsius') != original_row.get('tm_celsius'):
                    sample.tm_celsius = row.get('tm_celsius')
                if row.get('scattering_onset') != original_row.get('scattering_onset'):
                    sample.scattering_onset = row.get('scattering_onset')
                
                sample.save()
                saved_count += 1
                
            except Exception as e:
                errors.append(f"Row {row.get('sample_number', 'Unknown')}: {str(e)}")
        
        if errors:
            return dbc.Alert([
                html.Strong(f"Saved {saved_count} records with {len(errors)} errors:"),
                html.Ul([html.Li(error) for error in errors[:5]])  # Show first 5 errors
            ], color="warning", dismissable=True)
        else:
            return dbc.Alert(f"Successfully saved {saved_count} records!", color="success", dismissable=True)
            
    except Exception as e:
        return dbc.Alert(f"Error saving data: {str(e)}", color="danger", dismissable=True)

@app.callback(
    Output('editable-table', 'data', allow_duplicate=True),
    Input('add-row-btn', 'n_clicks'),
    [State('editable-table', 'data'),
     State('experiment-dropdown', 'value')],
    prevent_initial_call=True
)
def add_new_row(n_clicks, current_data, experiment_id):
    if not n_clicks or not experiment_id:
        return no_update
    
    # Find next sample number
    existing_numbers = []
    for row in current_data:
        sample_num = row.get('sample_number', '')
        if sample_num.startswith(f"{experiment_id}-"):
            try:
                num = int(sample_num.split('-')[2])
                existing_numbers.append(num)
            except:
                pass
    
    next_num = max(existing_numbers) + 1 if existing_numbers else 1
    new_sample_number = f"{experiment_id}-{next_num:03d}"
    
    # Add new row
    new_row = {
        'id': None,  # Will be assigned when saved
        'sample_number': new_sample_number,
        'buffer': '',
        'ph': None,
        'excipients': '',
        'formulation': '',
        'condition': '',
        'pull_day': None,
        'time_point_months': None,
        'appearance': '',
        'concentration': None,
        'ph_measured': None,
        'result_id': '',
        'hmw': None,
        'main': None,
        'lmw': None,
        'total_area': None,
        'osmolality': None,
        'tm_celsius': None,
        'scattering_onset': None,
    }
    
    # Add to current data
    new_data = current_data + [new_row]
    return new_data

if __name__ == '__main__':
    app.run_server(debug=True)