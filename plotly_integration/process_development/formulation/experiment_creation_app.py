"""
Experiment Creation App
Simplified focused interface for creating new formulation experiments
"""

import dash
from dash import dcc, html, Input, Output, State, no_update
import dash
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
from datetime import datetime, date
from django.contrib.auth.models import User
from plotly_integration.models import FormulationExperiment

app = DjangoDash("ExperimentCreationApp", external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
], suppress_callback_exceptions=True)

def generate_next_experiment_id():
    """Generate the next sequential experiment ID"""
    # Get all experiments that match the FD-XXX pattern
    experiments = FormulationExperiment.objects.filter(experiment_id__startswith='FD-').order_by('experiment_id')
    
    if not experiments.exists():
        return "FD-001"
    
    # Extract numbers and find the highest
    max_number = 0
    for exp in experiments:
        exp_id = exp.experiment_id
        if exp_id.startswith("FD-") and len(exp_id.split("-")) == 2:
            try:
                number = int(exp_id.split("-")[1])
                max_number = max(max_number, number)
            except (ValueError, IndexError):
                continue
    
    next_number = max_number + 1
    return f"FD-{next_number:03d}"

# Layout
app.layout = dbc.Container([
    dcc.Store(id="form-validation-store"),
    
    # Header
    dbc.Row([
        dbc.Col([
            html.H1([
                html.I(className="fas fa-plus-circle text-success me-3"),
                "Create New Experiment"
            ], className="mb-3"),
            html.P("Set up a new formulation stability experiment", className="lead text-muted")
        ])
    ]),
    
    # Main Form
    dbc.Card([
        dbc.CardHeader([
            html.H5([html.I(className="fas fa-flask me-2"), "Experiment Details"], className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Form([
                # Experiment ID
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Experiment ID", className="fw-bold"),
                        dbc.Input(
                            id="experiment-id-input",
                            placeholder="Auto-generated (e.g., FD-003)",
                            value=generate_next_experiment_id(),
                            disabled=False
                        ),
                        dbc.FormText("Unique identifier for this experiment")
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Molecule/Protein", className="fw-bold"),
                        dbc.Input(
                            id="molecule-input",
                            placeholder="e.g., mAb-X, Protein-ABC"
                        ),
                        dbc.FormText("Name of the molecule being formulated")
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Target Concentration (mg/mL)", className="fw-bold"),
                        dbc.Input(
                            id="concentration-input",
                            type="number",
                            value=2,
                            min=0,
                            step=0.1
                        ),
                        dbc.FormText("Target protein concentration")
                    ], width=4)
                ], className="mb-3"),
                
                # Experiment Name
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Experiment Name", className="fw-bold"),
                        dbc.Input(
                            id="experiment-name-input",
                            placeholder="Descriptive name for the experiment"
                        ),
                        dbc.FormText("Brief descriptive name for this experiment")
                    ], width=12)
                ], className="mb-3"),
                
                # Start Date
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Start Date", className="fw-bold"),
                        dbc.Input(
                            id="start-date-input",
                            type="date",
                            value=datetime.now().strftime('%Y-%m-%d')
                        ),
                        dbc.FormText("When the experiment will begin")
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Created By", className="fw-bold"),
                        dbc.Input(
                            id="created-by-input",
                            placeholder="Your username"
                        ),
                        dbc.FormText("Person responsible for this experiment")
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Priority", className="fw-bold"),
                        dcc.Dropdown(
                            id="priority-dropdown",
                            options=[
                                {'label': 'Low', 'value': 'low'},
                                {'label': 'Normal', 'value': 'normal'},
                                {'label': 'High', 'value': 'high'},
                                {'label': 'Critical', 'value': 'critical'}
                            ],
                            value='normal'
                        ),
                        dbc.FormText("Priority level for this experiment")
                    ], width=4)
                ], className="mb-3"),
                
                # Notes
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Notes", className="fw-bold"),
                        dbc.Textarea(
                            id="notes-input",
                            placeholder="Additional notes, objectives, or special considerations...",
                            rows=4
                        ),
                        dbc.FormText("Optional: Any additional information about this experiment")
                    ], width=12)
                ], className="mb-3"),
                
                html.Hr(),
                
                # Form Actions
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-save me-2"), "Create Experiment"],
                            id="create-experiment-btn",
                            color="success",
                            size="lg",
                            className="me-2"
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-times me-2"), "Clear Form"],
                            id="clear-form-btn",
                            color="secondary",
                            outline=True,
                            size="lg"
                        )
                    ], width=6),
                    dbc.Col([
                        html.Div(id="form-validation-feedback")
                    ], width=6, className="text-end")
                ])
            ])
        ])
    ], className="mb-4"),
    
    # Next Steps Card (appears after creation)
    html.Div(id="next-steps-section"),
    
    # Recent Experiments
    dbc.Card([
        dbc.CardHeader([
            html.H5([html.I(className="fas fa-history me-2"), "Recent Experiments"], className="mb-0")
        ]),
        dbc.CardBody([
            html.Div(id="recent-experiments-list")
        ])
    ]),
    
    # Alerts
    html.Div(id="alerts-container")
    
], className="my-4")

@app.callback(
    Output("recent-experiments-list", "children"),
    Input("create-experiment-btn", "n_clicks"),  # Refresh after creation
    prevent_initial_call=False
)
def update_recent_experiments(n_clicks):
    """Display recent experiments"""
    recent_experiments = FormulationExperiment.objects.order_by('-created_date')[:5]
    
    if not recent_experiments:
        return html.P("No experiments found. Create your first experiment above!", className="text-muted")
    
    experiment_cards = []
    for exp in recent_experiments:
        card = dbc.ListGroupItem([
            html.Div([
                html.H6(f"{exp.experiment_id} - {exp.name}", className="mb-1"),
                html.P([
                    html.I(className="fas fa-dna me-2"),
                    f"Molecule: {exp.molecule} | ",
                    html.I(className="fas fa-calendar me-2"),
                    f"Created: {exp.created_date.strftime('%Y-%m-%d')} | ",
                    html.I(className="fas fa-user me-2"),
                    f"By: {exp.created_by.username if exp.created_by else 'Unknown'}"
                ], className="mb-0 small text-muted")
            ])
        ])
        experiment_cards.append(card)
    
    return dbc.ListGroup(experiment_cards, flush=True)

@app.callback(
    [Output("alerts-container", "children"),
     Output("next-steps-section", "children"),
     Output("experiment-id-input", "value"),
     Output("experiment-name-input", "value"),
     Output("molecule-input", "value"),
     Output("concentration-input", "value"),
     Output("start-date-input", "value"),
     Output("notes-input", "value")],
    Input("create-experiment-btn", "n_clicks"),
    [State("experiment-id-input", "value"),
     State("experiment-name-input", "value"),
     State("molecule-input", "value"),
     State("concentration-input", "value"),
     State("start-date-input", "value"),
     State("created-by-input", "value"),
     State("notes-input", "value")],
    prevent_initial_call=True
)
def create_experiment(n_clicks, experiment_id, name, molecule, concentration, start_date, created_by, notes):
    if not n_clicks:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    # Validation
    if not all([experiment_id, name, molecule]):
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Please fill in all required fields (ID, Name, Molecule)"
        ], color="danger", dismissable=True), no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    # Check if experiment ID already exists
    if FormulationExperiment.objects.filter(experiment_id=experiment_id).exists():
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Experiment ID '{experiment_id}' already exists. Please use a different ID."
        ], color="danger", dismissable=True), no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    try:
        # Parse start date
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        
        # Get or create user
        user = None
        if created_by:
            try:
                user = User.objects.get(username=created_by)
            except User.DoesNotExist:
                # Create a simple user record if it doesn't exist
                user = User.objects.create_user(username=created_by)
        
        # Create experiment
        experiment = FormulationExperiment.objects.create(
            experiment_id=experiment_id,
            name=name,
            molecule=molecule,
            target_concentration_mg_ml=concentration or 50.0,
            start_date=start_date_obj,
            created_by=user,
            notes=notes or ''
        )
        
        # Success alert
        success_alert = dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            f"Experiment '{experiment_id}' created successfully!"
        ], color="success", dismissable=True)
        
        # Next steps card
        next_steps = dbc.Card([
            dbc.CardHeader([
                html.H5([html.I(className="fas fa-arrow-right me-2"), "Next Steps"], className="mb-0 text-success")
            ]),
            dbc.CardBody([
                html.P("Your experiment has been created! Here's what you can do next:", className="mb-3"),
                dbc.ListGroup([
                    html.A([
                        dbc.ListGroupItem([
                            html.I(className="fas fa-vials me-3 text-primary"),
                            html.Strong("Design Formulations"),
                            html.P("Create different buffer formulations for your experiment", className="mb-0 small text-muted")
                        ], action=True)
                    ], href="#!/formulation/design", style={"textDecoration": "none"}),
                    html.A([
                        dbc.ListGroupItem([
                            html.I(className="fas fa-calendar-plus me-3 text-info"),
                            html.Strong("Generate Samples"),
                            html.P("Auto-generate sample schedule based on your formulations", className="mb-0 small text-muted")
                        ], action=True)
                    ], href="#!/formulation/samples", style={"textDecoration": "none"}),
                    html.A([
                        dbc.ListGroupItem([
                            html.I(className="fas fa-table me-3 text-warning"),
                            html.Strong("Set up Data Entry"),
                            html.P("Prepare data entry templates for analytical results", className="mb-0 small text-muted")
                        ], action=True)
                    ], href="#!/formulation/data-entry", style={"textDecoration": "none"}),
                    html.A([
                        dbc.ListGroupItem([
                            html.I(className="fas fa-chart-line me-3 text-success"),
                            html.Strong("View Dashboard"),
                            html.P("Monitor progress and analyze stability trends", className="mb-0 small text-muted")
                        ], action=True)
                    ], href="#!/formulation/dashboard", style={"textDecoration": "none"})
                ], flush=True),
                
                html.Hr(),
                dbc.Button(
                    [html.I(className="fas fa-plus me-2"), "Create Another Experiment"],
                    id="create-another-btn",
                    color="outline-primary",
                    className="me-2"
                ),
                html.A(
                    dbc.Button(
                        [html.I(className="fas fa-vials me-2"), "Start Designing Formulations"],
                        color="primary"
                    ),
                    href="#!/formulation/design"
                )
            ])
        ], className="mb-4")
        
        # Clear form for next experiment
        next_exp_id = generate_next_experiment_id()
        
        return (success_alert, next_steps, next_exp_id, "", "", 2, 
                datetime.now().strftime('%Y-%m-%d'), "")
    
    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error creating experiment: {str(e)}"
        ], color="danger", dismissable=True), no_update, no_update, no_update, no_update, no_update, no_update, no_update

@app.callback(
    [Output("experiment-id-input", "value", allow_duplicate=True),
     Output("experiment-name-input", "value", allow_duplicate=True),
     Output("molecule-input", "value", allow_duplicate=True),
     Output("concentration-input", "value", allow_duplicate=True),
     Output("start-date-input", "value", allow_duplicate=True),
     Output("notes-input", "value", allow_duplicate=True)],
    Input("clear-form-btn", "n_clicks"),
    prevent_initial_call=True
)
def clear_form(n_clicks):
    if n_clicks:
        return (generate_next_experiment_id(), "", "", 2, 
                datetime.now().strftime('%Y-%m-%d'), "")
    return no_update, no_update, no_update, no_update, no_update, no_update

@app.callback(
    Output("form-validation-feedback", "children"),
    [Input("experiment-id-input", "value"),
     Input("experiment-name-input", "value"),
     Input("molecule-input", "value")],
    prevent_initial_call=True
)
def validate_form_inputs(experiment_id, name, molecule):
    """Real-time form validation feedback"""
    if not experiment_id or not name or not molecule:
        missing_fields = []
        if not experiment_id:
            missing_fields.append("ID")
        if not name:
            missing_fields.append("Name") 
        if not molecule:
            missing_fields.append("Molecule")
        
        return dbc.Badge([
            html.I(className="fas fa-exclamation-triangle me-1"),
            f"Missing: {', '.join(missing_fields)}"
        ], color="warning")
    
    # Check if ID exists
    if FormulationExperiment.objects.filter(experiment_id=experiment_id).exists():
        return dbc.Badge([
            html.I(className="fas fa-times me-1"),
            "ID already exists"
        ], color="danger")
    
    return dbc.Badge([
        html.I(className="fas fa-check me-1"),
        "Ready to create"
    ], color="success")

# Navigation callback for create another button only
@app.callback(
    Output("alerts-container", "children", allow_duplicate=True),
    Input("create-another-btn", "n_clicks"),
    prevent_initial_call=True
)
def handle_create_another_click(another_clicks):
    """Handle clicks on create another button"""
    if another_clicks:
        # For "Create Another Experiment", we'll reload by returning JavaScript
        return dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "Page will reload to create another experiment..."
        ], color="info", dismissable=True)
    
    return no_update

# Add JavaScript reload functionality for the "Create Another" button
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks) {
            setTimeout(function() {
                window.location.reload();
            }, 1000);
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("create-another-btn", "style"),
    Input("create-another-btn", "n_clicks"),
    prevent_initial_call=True
)

# Notify parent window when experiment is created
app.clientside_callback(
    """
    function(children) {
        if (children && children.props && children.props.children) {
            const alertText = children.props.children;
            if (typeof alertText === 'string' && alertText.includes('created successfully')) {
                // Notify parent window that an experiment was created
                if (window.parent && window.parent !== window) {
                    window.parent.postMessage({
                        type: 'experiment_created',
                        message: 'Experiment created successfully'
                    }, '*');
                }
            }
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("alerts-container", "style"),
    Input("alerts-container", "children"),
    prevent_initial_call=True
)