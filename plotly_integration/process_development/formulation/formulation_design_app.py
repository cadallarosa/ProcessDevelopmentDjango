"""
Formulation Design App
Focused interface for creating and managing formulation matrix designs with flexible components
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table, no_update, ALL, MATCH
import dash
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
import json
from datetime import datetime
from django.db import transaction
from plotly_integration.models import (
    FormulationExperiment, 
    FormulationMatrix, 
    FormulationComponent, 
    FormulationSample
)

app = DjangoDash("FormulationDesignApp", external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
], suppress_callback_exceptions=True)

# Component type options
COMPONENT_TYPES = [
    {'label': 'Buffer', 'value': 'buffer'},
    {'label': 'Excipient', 'value': 'excipient'},
    {'label': 'Surfactant', 'value': 'surfactant'},
    {'label': 'Salt', 'value': 'salt'},
    {'label': 'Sugar/Polyol', 'value': 'sugar'},
    {'label': 'Amino Acid', 'value': 'amino_acid'},
    {'label': 'Preservative', 'value': 'preservative'},
    {'label': 'Other', 'value': 'other'},
]

CONCENTRATION_UNITS = [
    {'label': 'mg/mL', 'value': 'mg/mL'},
    {'label': 'mM', 'value': 'mM'},
    {'label': '%', 'value': '%'},
    {'label': 'M', 'value': 'M'},
    {'label': 'μM', 'value': 'μM'},
    {'label': 'g/L', 'value': 'g/L'},
    {'label': 'μg/mL', 'value': 'μg/mL'},
]

def get_experiment_options():
    """Get available experiments for dropdown"""
    experiments = FormulationExperiment.objects.all().order_by('-created_date')
    return [{'label': f"{exp.experiment_id} - {exp.name}", 'value': exp.experiment_id} 
            for exp in experiments]

def get_formulation_data(experiment_id):
    """Get existing formulations for an experiment"""
    if not experiment_id:
        return []
    
    formulations = FormulationMatrix.objects.filter(
        experiment_id=experiment_id
    ).prefetch_related('components').order_by('formulation_number')
    
    data = []
    for form in formulations:
        components = form.components.all()
        component_summary = []
        for comp in components:
            component_summary.append(f"{comp.name} ({comp.concentration} {comp.unit})")
        
        data.append({
            'formulation_id': form.formulation_id,
            'formulation_number': form.formulation_number,
            'target_ph': form.target_ph,
            'osmolality': form.osmolality or '',
            'components': ', '.join(component_summary),
            'component_count': len(components),
            'notes': form.notes
        })
    
    return data

def create_component_input_row(index):
    """Create a row for entering component data"""
    return dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                options=COMPONENT_TYPES,
                placeholder="Select type...",
                id={'type': 'component-type', 'index': index}
            )
        ], width=3),
        dbc.Col([
            dbc.Input(
                placeholder="Component name (e.g., Histidine)",
                id={'type': 'component-name', 'index': index}
            )
        ], width=4),
        dbc.Col([
            dbc.Input(
                type="number",
                placeholder="Amount",
                id={'type': 'component-concentration', 'index': index}
            )
        ], width=2),
        dbc.Col([
            dcc.Dropdown(
                options=CONCENTRATION_UNITS,
                value="mM",
                id={'type': 'component-unit', 'index': index}
            )
        ], width=2),
        dbc.Col([
            dbc.Button(
                html.I(className="fas fa-trash"),
                color="danger",
                size="sm",
                id={'type': 'remove-component', 'index': index}
            )
        ], width=1)
    ], className="mb-2", id={'type': 'component-row', 'index': index})

# Layout
app.layout = dbc.Container([
    dcc.Store(id="selected-experiment-store"),
    dcc.Store(id="formulations-data-store"),
    dcc.Store(id="component-counter-store", data={'counter': 0}),
    
    # Header
    dbc.Row([
        dbc.Col([
            html.H1([
                html.I(className="fas fa-vials text-primary me-3"),
                "Formulation Design Matrix"
            ], className="mb-3"),
            html.P("Design and manage formulation compositions with flexible components", className="lead text-muted")
        ], width=8),
    ]),
    
    # Experiment Selection
    dbc.Card([
        dbc.CardHeader([
            html.H5([html.I(className="fas fa-flask me-2"), "Select Experiment"], className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id="experiment-dropdown",
                        options=[],  # Will be populated by callback
                        placeholder="Select an experiment to design formulations...",
                        value=None
                    )
                ], width=8),
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-sync me-2"), "Refresh"],
                        id="refresh-experiments-btn",
                        color="secondary",
                        outline=True
                    )
                ], width=4)
            ])
        ])
    ], className="mb-4"),
    
    # Existing Formulations Table
    html.Div(id="existing-formulations-section"),
    
    # New Formulation Design
    html.Div(id="new-formulation-section"),
    
    # Alerts and messages
    html.Div(id="alerts-container")
    
], fluid=True)

@app.callback(
    [Output("existing-formulations-section", "children"),
     Output("new-formulation-section", "children")],
    Input("experiment-dropdown", "value")
)
def update_formulation_sections(selected_experiment):
    if not selected_experiment:
        return html.Div(), html.Div()
    
    # Get existing formulations
    formulation_data = get_formulation_data(selected_experiment)
    
    # Existing formulations section
    if formulation_data:
        existing_table = dash_table.DataTable(
            id="formulations-table",
            data=formulation_data,
            columns=[
                {'name': 'Form #', 'id': 'formulation_number', 'type': 'numeric'},
                {'name': 'Target pH', 'id': 'target_ph', 'type': 'numeric'},
                {'name': 'Osmolality', 'id': 'osmolality'},
                {'name': 'Components', 'id': 'components'},
                {'name': '# Components', 'id': 'component_count', 'type': 'numeric'},
                {'name': 'Notes', 'id': 'notes'}
            ],
            style_cell={'textAlign': 'left'},
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ],
            page_size=10,
            sort_action="native",
            row_selectable="single"
        )
        
        existing_section = dbc.Card([
            dbc.CardHeader([
                html.H5([html.I(className="fas fa-list me-2"), "Existing Formulations"], className="mb-0")
            ]),
            dbc.CardBody([
                existing_table,
                html.Hr(),
                dbc.ButtonGroup([
                    dbc.Button(
                        [html.I(className="fas fa-edit me-2"), "Edit Selected"],
                        id="edit-formulation-btn",
                        color="primary"
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-copy me-2"), "Clone Selected"],
                        id="clone-formulation-btn",
                        color="secondary"
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-trash me-2"), "Delete Selected"],
                        id="delete-formulation-btn",
                        color="danger"
                    )
                ], className="mt-3")
            ])
        ], className="mb-4")
    else:
        existing_section = dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "No formulations found for this experiment. Create your first formulation below."
        ], color="info")
    
    # New formulation section
    new_formulation_section = dbc.Card([
        dbc.CardHeader([
            html.H5([html.I(className="fas fa-plus me-2"), "Design New Formulation"], className="mb-0")
        ]),
        dbc.CardBody([
            # Basic formulation properties
            dbc.Row([
                dbc.Col([
                    dbc.Label("Target pH"),
                    dbc.Input(id="new-formulation-ph", type="number", step=0.1, placeholder="e.g., 6.0")
                ], width=3),
                dbc.Col([
                    dbc.Label("Target Osmolality (mOsm/kg)"),
                    dbc.Input(id="new-formulation-osmolality", type="number", placeholder="e.g., 300")
                ], width=3),
                dbc.Col([
                    dbc.Label("Notes"),
                    dbc.Input(id="new-formulation-notes", placeholder="Optional notes")
                ], width=6)
            ], className="mb-4"),
            
            # Component section header
            html.H6([html.I(className="fas fa-atom me-2"), "Formulation Components"]),
            dbc.Row([
                dbc.Col("Type", width=3),
                dbc.Col("Component Name", width=4),
                dbc.Col("Concentration", width=2),
                dbc.Col("Unit", width=2),
                dbc.Col("Action", width=1)
            ], className="fw-bold border-bottom pb-2 mb-2"),
            
            # Dynamic component rows container
            html.Div(id="components-container", children=[
                create_component_input_row(0)
            ]),
            
            # Add component button
            dbc.Button(
                [html.I(className="fas fa-plus me-2"), "Add Component"],
                id="add-component-btn",
                color="success",
                outline=True,
                className="mb-3"
            ),
            
            html.Hr(),
            
            # Action buttons
            dbc.ButtonGroup([
                dbc.Button(
                    [html.I(className="fas fa-save me-2"), "Save Formulation"],
                    id="save-formulation-btn",
                    color="primary",
                    size="lg"
                ),
                dbc.Button(
                    [html.I(className="fas fa-broom me-2"), "Clear Components"],
                    id="clear-components-btn",
                    color="secondary",
                    outline=True,
                    size="lg"
                )
            ])
        ])
    ])
    
    return existing_section, new_formulation_section

@app.callback(
    [Output("components-container", "children"),
     Output("component-counter-store", "data")],
    [Input("add-component-btn", "n_clicks"),
     Input({'type': 'remove-component', 'index': ALL}, "n_clicks")],
    [State("components-container", "children"),
     State("component-counter-store", "data")],
    prevent_initial_call=True
)
def manage_component_rows(add_clicks, remove_clicks, current_components, counter_data):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return current_components, counter_data
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    if 'add-component-btn' in trigger_id:
        # Add new component row
        counter_data['counter'] += 1
        new_component = create_component_input_row(counter_data['counter'])
        current_components.append(new_component)
        
    elif 'remove-component' in trigger_id:
        # Remove component row
        trigger_info = json.loads(trigger_id.split('.')[0])
        remove_index = trigger_info['index']
        
        current_components = [
            comp for comp in current_components 
            if comp['props']['id']['index'] != remove_index
        ]
    
    return current_components, counter_data

@app.callback(
    [Output("alerts-container", "children"),
     Output("existing-formulations-section", "children", allow_duplicate=True)],
    Input("save-formulation-btn", "n_clicks"),
    [State("experiment-dropdown", "value"),
     State("new-formulation-ph", "value"),
     State("new-formulation-osmolality", "value"),
     State("new-formulation-notes", "value"),
     State({'type': 'component-type', 'index': ALL}, "value"),
     State({'type': 'component-name', 'index': ALL}, "value"),
     State({'type': 'component-concentration', 'index': ALL}, "value"),
     State({'type': 'component-unit', 'index': ALL}, "value")],
    prevent_initial_call=True
)
def save_new_formulation(n_clicks, experiment_id, ph, osmolality, notes,
                        component_types, component_names, concentrations, 
                        units):
    if not n_clicks or not experiment_id:
        return no_update, no_update
    
    try:
        with transaction.atomic():
            # Get experiment
            experiment = FormulationExperiment.objects.get(experiment_id=experiment_id)
            
            # Determine next formulation number
            last_formulation = FormulationMatrix.objects.filter(
                experiment=experiment
            ).order_by('-formulation_number').first()
            
            next_number = 1 if not last_formulation else last_formulation.formulation_number + 1
            
            # Create formulation
            formulation = FormulationMatrix.objects.create(
                experiment=experiment,
                formulation_number=next_number,
                target_ph=ph or 7.0,
                osmolality=osmolality,
                notes=notes or ''
            )
            
            # Create components
            for i, (comp_type, name, conc, unit) in enumerate(
                zip(component_types, component_names, concentrations, units)
            ):
                if name and conc is not None:  # Only save if name and concentration are provided
                    FormulationComponent.objects.create(
                        formulation=formulation,
                        component_type=comp_type or 'other',
                        name=name,
                        concentration=conc,
                        unit=unit or 'mM'
                    )
            
            # Refresh formulations table
            formulation_data = get_formulation_data(experiment_id)
            
            if formulation_data:
                existing_table = dash_table.DataTable(
                    data=formulation_data,
                    columns=[
                        {'name': 'Form #', 'id': 'formulation_number', 'type': 'numeric'},
                        {'name': 'Target pH', 'id': 'target_ph', 'type': 'numeric'},
                        {'name': 'Osmolality', 'id': 'osmolality'},
                        {'name': 'Components', 'id': 'components'},
                        {'name': '# Components', 'id': 'component_count', 'type': 'numeric'},
                        {'name': 'Notes', 'id': 'notes'}
                    ],
                    style_cell={'textAlign': 'left'},
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }
                    ],
                    page_size=10,
                    sort_action="native",
                    row_selectable="single"
                )
                
                existing_section = dbc.Card([
                    dbc.CardHeader([
                        html.H5([html.I(className="fas fa-list me-2"), "Existing Formulations"], className="mb-0")
                    ]),
                    dbc.CardBody([
                        existing_table,
                        html.Hr(),
                        dbc.ButtonGroup([
                            dbc.Button(
                                [html.I(className="fas fa-edit me-2"), "Edit Selected"],
                                id="edit-formulation-btn",
                                color="primary"
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-copy me-2"), "Clone Selected"],
                                id="clone-formulation-btn",
                                color="secondary"
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-trash me-2"), "Delete Selected"],
                                id="delete-formulation-btn",
                                color="danger"
                            )
                        ], className="mt-3")
                    ])
                ], className="mb-4")
            else:
                existing_section = dbc.Alert([
                    html.I(className="fas fa-info-circle me-2"),
                    "No formulations found for this experiment. Create your first formulation below."
                ], color="info")
            
            return (dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Formulation #{next_number} saved successfully!"
            ], color="success", dismissable=True), existing_section)
    
    except Exception as e:
        return (dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error saving formulation: {str(e)}"
        ], color="danger", dismissable=True), no_update)

# Clear components callback
@app.callback(
    [Output("components-container", "children", allow_duplicate=True),
     Output("component-counter-store", "data", allow_duplicate=True),
     Output("new-formulation-ph", "value"),
     Output("new-formulation-osmolality", "value"),
     Output("new-formulation-notes", "value")],
    Input("clear-components-btn", "n_clicks"),
    prevent_initial_call=True
)
def clear_components(n_clicks):
    if n_clicks:
        # Reset to one empty component row
        return ([create_component_input_row(0)], {'counter': 0}, None, None, "")
    return no_update, no_update, no_update, no_update, no_update

# Auto-load experiments on page load and refresh button, auto-select most recent
@app.callback(
    [Output("experiment-dropdown", "options"),
     Output("experiment-dropdown", "value")],
    [Input("refresh-experiments-btn", "n_clicks")],
    prevent_initial_call=False  # Load on page load
)
def refresh_experiments(n_clicks):
    options = get_experiment_options()
    # Auto-select the most recent experiment (first in list)
    value = options[0]['value'] if options else None
    return options, value