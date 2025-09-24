"""
Formulation Experiment Manager
A Dash app for creating and managing formulation stability experiments
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table, no_update, ALL
import dash
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
import json
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
from django.db.models import Count, Q
from plotly_integration.models import (
    FormulationExperiment, 
    FormulationMatrix, 
    FormulationComponent, 
    FormulationSample
)

app = DjangoDash("FormulationExperimentManager", external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
], suppress_callback_exceptions=True)

# Color scheme
COLORS = {
    "primary": "#2E86C1",
    "secondary": "#E74C3C", 
    "success": "#27AE60",
    "warning": "#F39C12",
    "info": "#8E44AD",
    "light": "#F8F9FA",
    "dark": "#2C3E50"
}

def get_experiments_data():
    """Get experiments with statistics"""
    experiments = FormulationExperiment.objects.annotate(
        formulation_count=Count('formulations'),
        sample_count=Count('formulations__samples')
    ).order_by('-created_date')
    
    data = []
    for exp in experiments:
        data.append({
            'experiment_id': exp.experiment_id,
            'name': exp.name,
            'molecule': exp.molecule,
            'target_concentration_mg_ml': exp.target_concentration_mg_ml,
            'start_date': exp.start_date.strftime('%Y-%m-%d') if exp.start_date else '',
            'created_date': exp.created_date.strftime('%Y-%m-%d'),
            'created_by': exp.created_by.username if exp.created_by else '',
            'formulation_count': exp.formulation_count,
            'sample_count': exp.sample_count,
            'notes': exp.notes[:100] + '...' if len(exp.notes) > 100 else exp.notes
        })
    return data

def create_experiment_card(experiment):
    """Create a card for an experiment"""
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.H6(experiment['experiment_id'], className="mb-0 fw-bold"),
                html.Small(experiment['name'], className="text-muted")
            ]),
            dbc.Badge(
                experiment['molecule'],
                color="secondary",
                className="ms-2"
            )
        ], className="py-2"),
        dbc.CardBody([
            html.P([
                html.I(className="fas fa-vial me-2"),
                f"{experiment['formulation_count']} formulations, ",
                html.I(className="fas fa-flask me-2"),
                f"{experiment['sample_count']} samples, ",
                html.I(className="fas fa-calendar me-2"),
                f"Created: {experiment['created_date']}"
            ], className="text-muted small mb-2"),
            dbc.ButtonGroup([
                dbc.Button(
                    [html.I(className="fas fa-edit me-1"), "View/Edit"],
                    id={"type": "view-edit-experiment", "index": experiment['experiment_id']},
                    color="primary",
                    size="sm"
                ),
                dbc.DropdownMenu([
                    dbc.DropdownMenuItem(
                        [html.I(className="fas fa-th me-2"), "Matrix View"],
                        href="#!/formulation/design"
                    ),
                    dbc.DropdownMenuItem(
                        [html.I(className="fas fa-flask me-2"), "Manage Samples"],
                        href="#!/formulation/samples"
                    ),
                    dbc.DropdownMenuItem(
                        [html.I(className="fas fa-table me-2"), "Data Entry"],
                        href="#!/formulation/data-entry"
                    ),
                    dbc.DropdownMenuItem(divider=True),
                    dbc.DropdownMenuItem(
                        [html.I(className="fas fa-download me-2"), "Export"],
                        id={"type": "export-experiment", "index": experiment['experiment_id']}
                    ),
                    dbc.DropdownMenuItem(
                        [html.I(className="fas fa-trash me-2"), "Delete"],
                        id={"type": "delete-experiment", "index": experiment['experiment_id']},
                        className="text-danger"
                    ),
                ],
                label=[html.I(className="fas fa-ellipsis-v")],
                size="sm",
                color="light"
                )
            ])
        ])
    ], className="mb-2")

def create_summary_cards():
    """Create summary statistics cards"""
    total_experiments = FormulationExperiment.objects.count()
    total_formulations = FormulationMatrix.objects.count()
    total_samples = FormulationSample.objects.count()
    analyzed_samples = FormulationSample.objects.filter(hmw__isnull=False).count()

    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(total_experiments, className="text-primary mb-0"),
                    html.P("Experiments", className="text-muted mb-0"),
                    html.I(className="fas fa-flask fa-2x text-primary position-absolute top-0 end-0 mt-3 me-3")
                ], className="position-relative")
            ])
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(total_formulations, className="text-info mb-0"),
                    html.P("Formulations", className="text-muted mb-0"),
                    html.I(className="fas fa-vial fa-2x text-info position-absolute top-0 end-0 mt-3 me-3")
                ], className="position-relative")
            ])
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(total_samples, className="text-warning mb-0"),
                    html.P("Total Samples", className="text-muted mb-0"),
                    html.I(className="fas fa-test-tube fa-2x text-warning position-absolute top-0 end-0 mt-3 me-3")
                ], className="position-relative")
            ])
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(analyzed_samples, className="text-success mb-0"),
                    html.P("Analyzed", className="text-muted mb-0"),
                    html.I(className="fas fa-chart-line fa-2x text-success position-absolute top-0 end-0 mt-3 me-3")
                ], className="position-relative")
            ])
        ], md=3),
    ], className="mb-4")

# Layout
app.layout = dbc.Container([
    dcc.Store(id="selected-experiment-store"),
    dcc.Store(id="experiments-data-store"),

    # Header
    dbc.Row([
        dbc.Col([
            html.H1([
                html.I(className="fas fa-flask text-primary me-3"),
                "Formulation Experiment Manager"
            ], className="mb-3"),
            html.P("Create and manage formulation stability experiments", className="lead text-muted")
        ], width=8),
        dbc.Col([
            dbc.Button(
                [html.I(className="fas fa-plus me-2"), "New Experiment"],
                id="new-experiment-btn",
                color="primary",
                size="lg",
                className="mt-3"
            )
        ], width=4, className="text-end")
    ], className="mb-4"),

    # Summary Cards
    html.Div(id="summary-cards"),

    # Search and Filters
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.InputGroup([
                        dbc.InputGroupText(html.I(className="fas fa-search")),
                        dbc.Input(
                            id="search-input",
                            placeholder="Search experiments by ID, name, or molecule...",
                            debounce=True
                        )
                    ])
                ], md=8),
                dbc.Col([
                    dbc.Select(
                        id="molecule-filter",
                        placeholder="Filter by molecule",
                        options=[]
                    )
                ], md=4)
            ])
        ])
    ], className="mb-4"),

    # View Toggle
    dbc.ButtonGroup([
        dbc.Button(
            [html.I(className="fas fa-th me-1"), "Card View"],
            id="card-view-btn",
            color="primary",
            outline=False
        ),
        dbc.Button(
            [html.I(className="fas fa-table me-1"), "Table View"],
            id="table-view-btn",
            color="primary",
            outline=True
        )
    ], className="mb-3"),

    # Main Content Area
    html.Div(id="main-content"),

    # New Experiment Modal with iframe
    dbc.Modal([
        dbc.ModalHeader([
            html.H4([html.I(className="fas fa-plus me-2"), "Create New Experiment"]),
            dbc.Button(
                "×",
                id="close-new-exp-modal",
                className="btn-close",
                style={"background": "none", "border": "none", "font-size": "1.5rem"}
            )
        ]),
        dbc.ModalBody([
            html.Iframe(
                src="/plotly_integration/dash-app/app/ExperimentCreationApp/",
                style={"width": "100%", "height": "600px", "border": "none"},
                id="experiment-creation-iframe"
            )
        ], style={"padding": "0"}),
    ], id="new-experiment-modal", is_open=False, size="xl", centered=True),

    # Edit Experiment Modal
    dbc.Modal([
        dbc.ModalHeader([
            html.H4([html.I(className="fas fa-edit me-2"), "Edit Experiment"])
        ]),
        dbc.ModalBody([
            dbc.Form([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Experiment ID", html_for="edit-exp-id-input"),
                        dbc.Input(
                            id="edit-exp-id-input",
                            disabled=True  # Don't allow changing the ID
                        )
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Molecule", html_for="edit-molecule-input"),
                        dbc.Input(
                            id="edit-molecule-input",
                            required=True
                        )
                    ], md=6)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Experiment Name", html_for="edit-exp-name-input"),
                        dbc.Input(
                            id="edit-exp-name-input",
                            required=True
                        )
                    ], md=12)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Target Concentration (mg/mL)", html_for="edit-target-conc-input"),
                        dbc.Input(
                            id="edit-target-conc-input",
                            type="number",
                            step=0.1
                        )
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Start Date", html_for="edit-start-date-input"),
                        dbc.Input(
                            id="edit-start-date-input",
                            type="date"
                        )
                    ], md=6)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Notes", html_for="edit-notes-input"),
                        dbc.Textarea(
                            id="edit-notes-input",
                            rows=3
                        )
                    ], md=12)
                ])
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-edit-exp", color="secondary"),
            dbc.Button(
                [html.I(className="fas fa-save me-2"), "Save Changes"],
                id="save-edit-exp",
                color="primary"
            )
        ])
    ], id="edit-experiment-modal", is_open=False, size="lg"),

    # Toast notifications
    html.Div(id="toast-container", className="position-fixed top-0 end-0 p-3", style={"z-index": 9999}),

    # Alerts container
    html.Div(id="alerts-container", className="position-fixed top-0 start-50 translate-middle-x mt-3", style={"z-index": 9999})

], fluid=True)

# Callbacks
@app.callback(
    [Output("experiments-data-store", "data"),
     Output("summary-cards", "children"),
     Output("molecule-filter", "options")],
    [Input("search-input", "value"),
     Input("molecule-filter", "value")]
)
def update_experiments_data(search_term, molecule_filter):
    experiments_data = get_experiments_data()

    # Apply filters
    if search_term:
        filtered_data = [
            exp for exp in experiments_data
            if search_term.lower() in exp['experiment_id'].lower() or
               search_term.lower() in exp['name'].lower() or
               search_term.lower() in exp['molecule'].lower()
        ]
    else:
        filtered_data = experiments_data

    if molecule_filter:
        filtered_data = [exp for exp in filtered_data if exp['molecule'] == molecule_filter]

    # Get unique molecules for filter dropdown
    molecules = list(set([exp['molecule'] for exp in experiments_data]))
    molecule_options = [{"label": mol, "value": mol} for mol in sorted(molecules)]
    molecule_options.insert(0, {"label": "All Molecules", "value": ""})

    return filtered_data, create_summary_cards(), molecule_options

@app.callback(
    [Output("card-view-btn", "outline"),
     Output("table-view-btn", "outline"),
     Output("main-content", "children")],
    [Input("card-view-btn", "n_clicks"),
     Input("table-view-btn", "n_clicks"),
     Input("experiments-data-store", "data")],
    prevent_initial_call=False
)
def update_view(card_clicks, table_clicks, experiments_data):
    ctx = dash.callback_context
    view_mode = "card"  # default

    if ctx.triggered:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if button_id == "table-view-btn":
            view_mode = "table"

    if not experiments_data:
        return True, False, html.Div([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-flask fa-3x text-muted mb-3"),
                        html.H4("No experiments found"),
                        html.P("Create your first formulation experiment to get started.", className="text-muted"),
                        dbc.Button(
                            [html.I(className="fas fa-plus me-2"), "Create First Experiment"],
                            id="create-first-exp",
                            color="primary"
                        )
                    ], className="text-center py-5")
                ])
            ])
        ])

    if view_mode == "card":
        # Card view - 1 card per column, shorter cards
        cards = []
        for exp in experiments_data:
            cards.append(
                dbc.Row([
                    dbc.Col([
                        create_experiment_card(exp)
                    ], md=12)
                ], className="mb-2")  # Reduced margin between cards
            )
        return False, True, html.Div(cards)
    else:
        # Table view
        columns = [
            {"name": "Experiment ID", "id": "experiment_id"},
            {"name": "Name", "id": "name"},
            {"name": "Molecule", "id": "molecule"},
            {"name": "Target Conc.", "id": "target_concentration_mg_ml"},
            {"name": "Formulations", "id": "formulation_count"},
            {"name": "Samples", "id": "sample_count"},
            {"name": "Created", "id": "created_date"},
            {"name": "Created By", "id": "created_by"}
        ]

        table = dash_table.DataTable(
            data=experiments_data,
            columns=columns,
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontFamily': 'Arial'
            },
            style_header={
                'backgroundColor': COLORS['primary'],
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ],
            page_size=20,
            sort_action="native"
        )
        return True, False, table

@app.callback(
    Output("new-experiment-modal", "is_open"),
    [Input("new-experiment-btn", "n_clicks"),
     Input("create-first-exp", "n_clicks"),
     Input("close-new-exp-modal", "n_clicks")],
    [State("new-experiment-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_new_experiment_modal(open_btn, first_btn, close_btn, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update

    trigger_info = ctx.triggered[0]
    button_id = trigger_info["prop_id"].split(".")[0]

    if button_id in ["new-experiment-btn", "create-first-exp"]:
        return True
    elif button_id == "close-new-exp-modal":
        return False

    return no_update


# Handle experiment actions including export and delete
@app.callback(
    [Output("alerts-container", "children", allow_duplicate=True),
     Output("edit-experiment-modal", "is_open"),
     Output("edit-exp-id-input", "value"),
     Output("edit-molecule-input", "value"),
     Output("edit-exp-name-input", "value"),
     Output("edit-target-conc-input", "value"),
     Output("edit-start-date-input", "value"),
     Output("edit-notes-input", "value")],
    [Input({"type": "view-edit-experiment", "index": ALL}, "n_clicks"),
     Input({"type": "export-experiment", "index": ALL}, "n_clicks"),
     Input({"type": "delete-experiment", "index": ALL}, "n_clicks"),
     Input("cancel-edit-exp", "n_clicks"),
     Input("save-edit-exp", "n_clicks")],
    [State("edit-experiment-modal", "is_open"),
     State("edit-exp-id-input", "value"),
     State("edit-molecule-input", "value"),
     State("edit-exp-name-input", "value"),
     State("edit-target-conc-input", "value"),
     State("edit-start-date-input", "value"),
     State("edit-notes-input", "value")],
    prevent_initial_call=True
)
def handle_experiment_actions(view_edit_clicks, export_clicks, delete_clicks, cancel_clicks, save_clicks,
                             modal_open, exp_id, molecule, name, target_conc, start_date, notes):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

    # Check if trigger is from initial callback with no real user interaction
    trigger_info = ctx.triggered[0]
    if trigger_info['value'] is None:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

    trigger_info = ctx.triggered[0]
    prop_id = trigger_info['prop_id']

    # Handle modal cancel/save buttons first
    if "cancel-edit-exp" in prop_id:
        return no_update, False, no_update, no_update, no_update, no_update, no_update, no_update

    elif "save-edit-exp" in prop_id:
        # Save experiment changes
        try:
            if exp_id:
                experiment = FormulationExperiment.objects.get(experiment_id=exp_id)
                experiment.molecule = molecule or experiment.molecule
                experiment.name = name or experiment.name
                experiment.target_concentration_mg_ml = target_conc or experiment.target_concentration_mg_ml
                if start_date:
                    experiment.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                experiment.notes = notes or experiment.notes
                experiment.save()

                return (dbc.Alert([
                    html.I(className="fas fa-check-circle me-2"),
                    f"Experiment {exp_id} updated successfully!"
                ], color="success", dismissable=True),
                False, "", "", "", None, "", "")
        except Exception as e:
            return (dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Error saving experiment: {str(e)}"
            ], color="danger", dismissable=True),
            modal_open, no_update, no_update, no_update, no_update, no_update, no_update)

    try:
        # Parse the trigger to get action type and experiment ID
        import json
        trigger_dict = json.loads(prop_id.split('.')[0])
        action_type = trigger_dict['type']
        experiment_id = trigger_dict['index']

        if action_type == "view-edit-experiment":
            # Open edit modal and populate with experiment data
            try:
                experiment = FormulationExperiment.objects.get(experiment_id=experiment_id)
                return (no_update, True, experiment_id, experiment.molecule, experiment.name,
                       experiment.target_concentration_mg_ml,
                       experiment.start_date.strftime('%Y-%m-%d') if experiment.start_date else "",
                       experiment.notes)
            except Exception as e:
                return (dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Error loading experiment: {str(e)}"
                ], color="danger", dismissable=True),
                modal_open, no_update, no_update, no_update, no_update, no_update, no_update)

        elif action_type == "export-experiment":
            # Placeholder for export functionality
            return (dbc.Alert([
                html.I(className="fas fa-download me-2"),
                f"Export functionality for {experiment_id} is under development."
            ], color="warning", dismissable=True),
            modal_open, no_update, no_update, no_update, no_update, no_update, no_update)

        elif action_type == "delete-experiment":
            # Delete experiment with confirmation
            try:
                experiment = FormulationExperiment.objects.get(experiment_id=experiment_id)
                experiment.delete()
                return (dbc.Alert([
                    html.I(className="fas fa-check-circle me-2"),
                    f"Experiment {experiment_id} deleted successfully!"
                ], color="success", dismissable=True),
                modal_open, no_update, no_update, no_update, no_update, no_update, no_update)
            except Exception as e:
                return (dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Error deleting experiment: {str(e)}"
                ], color="danger", dismissable=True),
                modal_open, no_update, no_update, no_update, no_update, no_update, no_update)

    except Exception as e:
        return (dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error handling action: {str(e)}"
        ], color="danger", dismissable=True),
        modal_open, no_update, no_update, no_update, no_update, no_update, no_update)

    return no_update, modal_open, no_update, no_update, no_update, no_update, no_update, no_update

# Client-side callback to handle iframe communication and refresh data
app.clientside_callback(
    """
    function(n_interval) {
        // Listen for messages from iframe
        window.addEventListener('message', function(event) {
            if (event.data && event.data.type === 'experiment_created') {
                // Trigger a refresh of the experiments data
                window.dash_clientside.set_props('search-input', {'n_submit': Date.now()});
            }
        });
        return window.dash_clientside.no_update;
    }
    """,
    Output("experiment-creation-iframe", "style"),
    Input("experiment-creation-iframe", "id"),
    prevent_initial_call=True
)

if __name__ == "__main__":
    app.run_server(debug=True)