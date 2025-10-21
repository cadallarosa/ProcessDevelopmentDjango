"""
USP Experiment Management Dashboard App
Main dashboard for tracking USP experiments with bioreactors, shake flasks, and seed trains
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table, no_update, ALL, MATCH
from dash.exceptions import PreventUpdate
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, date
from django.db.models import Count, Q, F, Avg
from plotly_integration.models import USPExperiment, USPProcessStep, USPVessel, USPSeedTrain, USPMediaPrep

def generate_usp_experiment_number():
    """Generate the next USP experiment number in format USP####"""
    try:
        # Get the highest existing experiment number
        last_experiment = USPExperiment.objects.filter(
            experiment_id__startswith='USP'
        ).order_by('-experiment_id').first()

        if last_experiment:
            # Extract the number from the last experiment ID (e.g., "USP0001" -> 1)
            last_number = int(last_experiment.experiment_id[3:])
            next_number = last_number + 1
        else:
            next_number = 1

        # Format as USP#### (4 digits with leading zeros)
        return f"USP{next_number:04d}"
    except:
        # Fallback if there's any error
        return "USP0001"

def generate_seed_train_id():
    """Generate the next Seed Train ID in format UPST####"""
    try:
        last_seed_train = USPSeedTrain.objects.filter(
            seed_train_id__startswith='UPST'
        ).order_by('-seed_train_id').first()

        if last_seed_train:
            last_number = int(last_seed_train.seed_train_id[4:])
            next_number = last_number + 1
        else:
            next_number = 1

        return f"UPST{next_number:04d}"
    except:
        return "UPST0001"

def generate_fed_batch_id():
    """Generate the next Fed Batch ID in format UPFB####"""
    try:
        last_vessel = USPVessel.objects.filter(
            vessel_id__startswith='UPFB'
        ).order_by('-vessel_id').first()

        if last_vessel:
            last_number = int(last_vessel.vessel_id[4:])
            next_number = last_number + 1
        else:
            next_number = 1

        return f"UPFB{next_number:04d}"
    except:
        return "UPFB0001"

def generate_fed_batch_id():
    """Generate the next Fed Batch ID in format UPFB####"""
    try:
        # Get the highest existing Fed Batch ID
        last_vessel = USPVessel.objects.filter(
            vessel_id__startswith='UPFB'
        ).order_by('-vessel_id').first()

        if last_vessel:
            # Extract the number from the last ID
            last_number = int(last_vessel.vessel_id[4:])
            next_number = last_number + 1
        else:
            next_number = 1

        return f"UPFB{next_number:04d}"
    except:
        return "UPFB0001"

def generate_seed_train_id():
    """Generate the next Seed Train ID in format UPST####"""
    try:
        # Get the highest existing Seed Train ID from USPSeedTrain model
        last_seed_train = USPSeedTrain.objects.filter(
            seed_train_id__startswith='UPST'
        ).order_by('-seed_train_id').first()

        if last_seed_train:
            # Extract the number from the last ID
            last_number = int(last_seed_train.seed_train_id[4:])
            next_number = last_number + 1
        else:
            next_number = 1

        return f"UPST{next_number:04d}"
    except:
        return "UPST0001"

def get_vessel_type_options_for_step(step_type):
    """Return filtered vessel type options based on step type"""
    if step_type == "Seed_Train":
        return [
            {"label": "T25 Flask", "value": "T25"},
            {"label": "T75 Flask", "value": "T75"},
            {"label": "T175 Flask", "value": "T175"},
            {"label": "T225 Flask", "value": "T225"},
            {"label": "125mL Shake Flask", "value": "125mL_SF"},
            {"label": "250mL Shake Flask", "value": "250mL_SF"},
            {"label": "500mL Shake Flask", "value": "500mL_SF"},
        ]
    elif step_type == "Bioreactor":
        return [
            {"label": "2L Bioreactor", "value": "2L_BRX"},
            {"label": "5L Bioreactor", "value": "5L_BRX"},
            {"label": "10L Bioreactor", "value": "10L_BRX"},
            {"label": "15L Bioreactor", "value": "15L_BRX"},
        ]
    elif step_type == "Shake_Flask":
        return [
            {"label": "250mL Shake Flask", "value": "250mL_SF"},
            {"label": "500mL Shake Flask", "value": "500mL_SF"},
            {"label": "1L Shake Flask", "value": "1L_SF"},
            {"label": "2L Shake Flask", "value": "2L_SF"},
        ]
    else:  # Bioreactor_and_Shake_Flask or other
        return [
            {"label": "2L Bioreactor", "value": "2L_BRX"},
            {"label": "5L Bioreactor", "value": "5L_BRX"},
            {"label": "10L Bioreactor", "value": "10L_BRX"},
            {"label": "15L Bioreactor", "value": "15L_BRX"},
            {"label": "250mL Shake Flask", "value": "250mL_SF"},
            {"label": "500mL Shake Flask", "value": "500mL_SF"},
            {"label": "1L Shake Flask", "value": "1L_SF"},
            {"label": "2L Shake Flask", "value": "2L_SF"},
        ]

app = DjangoDash("USPExperimentManagementApp", external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
], suppress_callback_exceptions=True)

def get_dashboard_statistics():
    """Get overall experiment statistics"""
    today = date.today()

    try:
        stats = {
            'total_experiments': USPExperiment.objects.count(),
            'active_experiments': USPExperiment.objects.filter(status='In Progress').count(),
            'planning_experiments': USPExperiment.objects.filter(status='Planning').count(),
            'completed_experiments': USPExperiment.objects.filter(status='Complete').count(),
            'upcoming_harvests': USPExperiment.objects.filter(
                target_end_date__gte=today,
                target_end_date__lte=today + timedelta(days=7)
            ).count(),
            'bioreactor_runs': USPProcessStep.objects.filter(step_type='Bioreactor').count(),
            'shake_flask_runs': USPProcessStep.objects.filter(step_type='Shake_Flask').count(),
            'seed_train_runs': USPProcessStep.objects.filter(step_type='Seed_Train').count(),
            'active_vessels': USPVessel.objects.filter(
                process_step__status='In Progress'
            ).count(),
        }

        # Calculate completion rate
        total_steps = USPProcessStep.objects.count()
        completed_steps = USPProcessStep.objects.filter(status='Complete').count()

        if total_steps > 0:
            stats['completion_rate'] = round((completed_steps / total_steps) * 100, 1)
        else:
            stats['completion_rate'] = 0

        return stats
    except Exception as e:
        print(f"Error getting dashboard statistics: {e}")
        # Return default stats if there's an error
        return {
            'total_experiments': 0,
            'active_experiments': 0,
            'planning_experiments': 0,
            'completed_experiments': 0,
            'upcoming_harvests': 0,
            'bioreactor_runs': 0,
            'shake_flask_runs': 0,
            'seed_train_runs': 0,
            'active_vessels': 0,
            'completion_rate': 0
        }

def get_experiment_gantt_data():
    """Prepare USP experiment data for Gantt chart visualization"""
    try:
        experiments = USPExperiment.objects.all().order_by('-start_date')

        gantt_data = []
        for experiment in experiments:
            # Add process steps timeline
            try:
                steps = experiment.process_steps.all()
                for step in steps:
                    if step.planned_start_date and step.planned_end_date:
                        gantt_data.append({
                            'Task': f"{experiment.experiment_id} - {experiment.experiment_name}",
                            'Start': step.planned_start_date,
                            'Finish': step.planned_end_date,
                            'Resource': step.step_type,
                            'experiment_id': experiment.id,
                            'status': step.status,
                            'step_name': step.step_name,
                            'step_type': step.step_type,
                        })
            except Exception as e:
                print(f"Error loading steps for experiment {experiment.experiment_id}: {e}")
                continue

        return pd.DataFrame(gantt_data)
    except Exception as e:
        print(f"Error creating Gantt data: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

def create_gantt_chart(df, status_filter='all', step_type_filter='all', start_date=None, end_date=None):
    """Create interactive Gantt chart for USP experiments"""
    try:
        fig = go.Figure()

        # Define the USP workflow steps in display order (reversed)
        workflow_steps = [
            {'step': 'Shake_Flask', 'y_pos': 0, 'color': '#45B7D1'},
            {'step': 'Bioreactor', 'y_pos': 1, 'color': '#4ECDC4'},
            {'step': 'Seed_Train', 'y_pos': 2, 'color': '#FF6B6B'}
        ]

        # Get experiments from database with filtering
        experiments_query = USPExperiment.objects.all()

        # Apply filters
        if status_filter != 'all':
            experiments_query = experiments_query.filter(status=status_filter)

        experiments = list(experiments_query.order_by('-created_date')[:15])

        # Generate colors for experiments
        colors = px.colors.qualitative.Plotly

        # Track all experiment names for legend
        added_experiments = set()

        # Calculate offset for each experiment to avoid overlaps
        bar_height = 0.6
        experiment_height = bar_height / max(len(experiments), 1)

        for idx, experiment in enumerate(experiments):
            color = colors[idx % len(colors)]
            experiment_name = experiment.experiment_id

            # Calculate y-offset for this experiment to prevent overlaps
            y_offset = (idx * experiment_height) - (bar_height / 2)

            # Get process steps for this experiment
            steps = experiment.process_steps.all()

            for step_info in workflow_steps:
                step_type = step_info['step']
                y_pos = step_info['y_pos']

                # Find the corresponding step data
                step_data = None
                for s in steps:
                    if s.step_type == step_type:
                        step_data = s
                        break

                if not step_data:
                    continue

                # Use actual dates if available, otherwise planned dates
                bar_start = step_data.actual_start_date or step_data.planned_start_date
                if step_data.actual_end_date:
                    bar_end = step_data.actual_end_date
                elif step_data.actual_duration_days:
                    bar_end = bar_start + timedelta(days=step_data.actual_duration_days)
                else:
                    bar_end = step_data.planned_end_date or bar_start + timedelta(days=1)

                # Skip if we don't have valid dates
                if not bar_start or not bar_end:
                    continue

                # Convert to datetime if needed
                if bar_start and not isinstance(bar_start, datetime):
                    bar_start = datetime.combine(bar_start, datetime.min.time())
                if bar_end and not isinstance(bar_end, datetime):
                    bar_end = datetime.combine(bar_end, datetime.min.time())

                # Determine status and styling based on step status
                if step_data.status == 'Complete':
                    opacity = 1.0
                    dash = None
                elif step_data.status == 'In Progress':
                    opacity = 0.7
                    dash = 'dash'
                elif step_data.status == 'Skipped':
                    opacity = 0.2
                    dash = 'dashdot'
                else:
                    opacity = 0.3
                    dash = 'dot'

                # Create step label
                step_label = f"{step_data.step_name} ({step_data.planned_duration_days}d)"

                # Only add to legend once per experiment
                show_legend = experiment_name not in added_experiments
                if show_legend:
                    added_experiments.add(experiment_name)

                # Create bar for this step with y-offset to avoid overlaps
                bar_bottom = y_pos + y_offset - (experiment_height / 2)
                bar_top = y_pos + y_offset + (experiment_height / 2)

                fig.add_trace(go.Scatter(
                    x=[bar_start, bar_end, bar_end, bar_start, bar_start],
                    y=[bar_bottom, bar_bottom, bar_top, bar_top, bar_bottom],
                    fill='toself',
                    fillcolor=color,
                    opacity=opacity,
                    line=dict(color=color, dash=dash, width=2 if step_data.status == 'In Progress' else 1),
                    mode='lines',
                    name=experiment_name,
                    legendgroup=experiment_name,
                    showlegend=show_legend,
                    hovertemplate=f'<b>{experiment_name}</b><br>{step_label}<br>Start: %{{x[0]|%Y-%m-%d}}<br>End: %{{x[1]|%Y-%m-%d}}<br>Status: {step_data.status}<extra></extra>'
                ))

        # Add today line
        today = datetime.now()
        fig.add_shape(
            type="line",
            x0=today, x1=today,
            y0=-0.5, y1=len(workflow_steps) - 0.5,
            line=dict(color="red", width=2, dash="dash")
        )

        # Add text annotation for today
        fig.add_annotation(
            x=today, y=len(workflow_steps),
            text="Today",
            showarrow=False,
            font=dict(color="red", size=12),
            yshift=10
        )

        # Use date range from filters if provided, otherwise default
        if start_date and end_date:
            from datetime import datetime as dt
            x_start = dt.strptime(start_date, '%Y-%m-%d') if isinstance(start_date, str) else datetime.combine(start_date, datetime.min.time())
            x_end = dt.strptime(end_date, '%Y-%m-%d') if isinstance(end_date, str) else datetime.combine(end_date, datetime.min.time())
        else:
            x_start = datetime.now() - timedelta(days=30)
            x_end = datetime.now() + timedelta(days=60)

        # Update layout
        fig.update_layout(
            height=500,
            title="USP Experiment Process Timeline",
            xaxis_title="Timeline",
            yaxis_title="Process Steps",
            xaxis=dict(
                type='date',
                showgrid=True,
                gridcolor='lightgray',
                range=[x_start, x_end]
            ),
            yaxis=dict(
                tickmode='array',
                tickvals=[s['y_pos'] for s in workflow_steps],
                ticktext=[s['step'].replace('_', ' ') for s in workflow_steps],
                showgrid=True,
                gridcolor='lightgray',
                range=[-1, len(workflow_steps)]
            ),
            showlegend=True,
            legend=dict(
                title="Experiments",
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            ),
            margin=dict(l=100, r=150, t=80, b=50),
            hovermode='closest'
        )

        return fig

    except Exception as e:
        print(f"Error creating Gantt chart: {e}")
        import traceback
        traceback.print_exc()
        # Return empty figure on error
        fig = go.Figure()
        fig.update_layout(
            title="Error creating Gantt chart",
            height=400
        )
        return fig

def get_workflow_template(template_type='standard'):
    """Get workflow steps based on template type with individual start dates"""
    today = date.today()

    templates = {
        'standard': [
            {'step_name': 'Seed Train', 'step_type': 'Seed_Train', 'duration': 7, 'order': 1, 'start_date': today},
            {'step_name': 'Bioreactor Run', 'step_type': 'Bioreactor', 'duration': 14, 'order': 2, 'start_date': today + timedelta(days=7)},
            {'step_name': 'Shake Flask Run', 'step_type': 'Shake_Flask', 'duration': 14, 'order': 3, 'start_date': today + timedelta(days=21)},
        ],
        'seed_train_bioreactor': [
            {'step_name': 'Seed Train', 'step_type': 'Seed_Train', 'duration': 7, 'order': 1, 'start_date': today},
            {'step_name': 'Bioreactor Run', 'step_type': 'Bioreactor', 'duration': 14, 'order': 2, 'start_date': today + timedelta(days=7)},
        ],
        'seed_train_shake_flask': [
            {'step_name': 'Seed Train', 'step_type': 'Seed_Train', 'duration': 3, 'order': 1, 'start_date': today},
            {'step_name': 'Shake Flask Run', 'step_type': 'Shake_Flask', 'duration': 14, 'order': 2, 'start_date': today + timedelta(days=3)},
        ],
        'custom': []  # Empty for custom workflows
    }
    return templates.get(template_type, templates['standard'])

def get_default_workflow_steps():
    """Get default workflow steps for new experiments"""
    return get_workflow_template('standard')

def create_step_card(index, step_name, duration, step_type='Seed_Train', start_date=None):
    """Create a workflow step card with individual start date"""
    if start_date is None:
        start_date = date.today()

    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Step Name"),
                    dbc.Input(
                        id={"type": "step-name", "index": index},
                        value=step_name,
                        placeholder="Enter step name"
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("Step Type"),
                    dcc.Dropdown(
                        id={"type": "step-type", "index": index},
                        options=[
                            {'label': 'Seed Train', 'value': 'Seed_Train'},
                            {'label': 'Bioreactor', 'value': 'Bioreactor'},
                            {'label': 'Shake Flask', 'value': 'Shake_Flask'},
                        ],
                        value=step_type
                    )
                ], width=3),
                dbc.Col([
                    dbc.Label("Start Date"),
                    dcc.DatePickerSingle(
                        id={"type": "step-start-date", "index": index},
                        date=start_date,
                        display_format="YYYY-MM-DD",
                        style={'width': '100%'}
                    )
                ], width=2),
                dbc.Col([
                    dbc.Label("Duration (days)"),
                    dbc.Input(
                        id={"type": "step-duration", "index": index},
                        type="number",
                        value=duration,
                        min=1
                    )
                ], width=2),
                dbc.Col([
                    dbc.Button(
                        html.I(className="fas fa-trash"),
                        id={"type": "remove-step", "index": index},
                        color="danger",
                        size="sm",
                        className="mt-4"
                    )
                ], width=1)
            ])
        ])
    ], className="mb-2")

# Layout
app.layout = dbc.Container([
    dcc.Store(id="selected-experiment-store"),
    dcc.Store(id="selected-experiment-data"),
    dcc.Interval(id="refresh-interval", interval=300000, n_intervals=0),  # Refresh every 5 minutes

    # Header
    dbc.Row([
        dbc.Col([
            html.H1("USP Experiment Management Dashboard",
                   className="display-4 fw-bold text-primary mb-3"),
            html.P("Track USP experiments with bioreactors, shake flasks, and seed trains",
                   className="lead text-muted")
        ], width=8),
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button(
                    [html.I(className="fas fa-cogs me-2"), "Manage Experiments"],
                    id="manage-experiments-btn",
                    color="primary"
                ),
                dbc.Button(
                    [html.I(className="fas fa-plus me-2"), "New Experiment"],
                    id="open-new-experiment-modal",
                    color="success"
                ),
                dbc.Button(
                    [html.I(className="fas fa-refresh me-2"), "Refresh"],
                    id="refresh-btn",
                    color="secondary"
                )
            ], className="mb-3")
        ], width=4, className="text-end")
    ], className="mb-4"),

    # Statistics Cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("0", id="total-experiments", className="text-primary"),
                    html.P("Total Experiments", className="text-muted mb-0")
                ])
            ])
        ], width=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("0", id="active-experiments", className="text-success"),
                    html.P("Active", className="text-muted mb-0")
                ])
            ])
        ], width=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("0", id="bioreactor-runs", className="text-info"),
                    html.P("Bioreactor Runs", className="text-muted mb-0")
                ])
            ])
        ], width=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("0", id="shake-flask-runs", className="text-warning"),
                    html.P("Shake Flask Runs", className="text-muted mb-0")
                ])
            ])
        ], width=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("0", id="seed-train-runs", className="text-secondary"),
                    html.P("Seed Train Runs", className="text-muted mb-0")
                ])
            ])
        ], width=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("0%", id="completion-rate", className="text-dark"),
                    html.P("Completion Rate", className="text-muted mb-0")
                ])
            ])
        ], width=2)
    ], className="mb-4"),

    # Main Content
    dbc.Row([
        dbc.Col([
            # Gantt Chart
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H5("Process Timeline", className="mb-0")
                        ], width=4),
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button("All", id="filter-all", size="sm", outline=True),
                                dbc.Button("Planning", id="filter-planning", size="sm", outline=True),
                                dbc.Button("In Progress", id="filter-active", size="sm", outline=True),
                                dbc.Button("Complete", id="filter-complete", size="sm", outline=True)
                            ])
                        ], width=8, className="text-end")
                    ])
                ]),
                dbc.CardBody([
                    dcc.Graph(id="gantt-chart", style={'height': '500px'})
                ])
            ], className="mb-4")
        ], width=12)
    ]),

    # New Experiment Modal
    dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle("Create New Experiment", id="experiment-modal-title")
        ]),
        dbc.ModalBody([
            # Alert container for validation messages
            html.Div(id="alert-container"),

            # Basic experiment info
            dbc.Row([
                dbc.Col([
                    dbc.Label("Experiment ID", html_for="experiment-id-input"),
                    dbc.Input(
                        id="experiment-id-input",
                        placeholder="Auto-generated (USP####)",
                        disabled=True,
                        value=generate_usp_experiment_number()
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("Project ID", html_for="project-id-input"),
                    dbc.Input(
                        id="project-id-input",
                        placeholder="Enter project ID"
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("Experiment Name", html_for="experiment-name-input"),
                    dbc.Input(
                        id="experiment-name-input",
                        placeholder="Enter experiment name",
                        required=True
                    ),
                ], md=4),
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Experiment Type", html_for="experiment-type-select"),
                    dcc.Dropdown(
                        id="experiment-type-select",
                        options=[
                            {'label': 'Conformance', 'value': 'Conformance'},
                            {'label': 'pH Test', 'value': 'pH_Test'},
                            {'label': 'Temperature Test', 'value': 'Temperature_Test'},
                            {'label': 'Media Optimization', 'value': 'Media_Optimization'},
                            {'label': 'Feed Optimization', 'value': 'Feed_Optimization'},
                            {'label': 'Scale Up', 'value': 'Scale_Up'},
                            {'label': 'Process Characterization', 'value': 'Process_Characterization'},
                            {'label': 'Other', 'value': 'Other'},
                        ],
                        placeholder='Select experiment type...'
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("Start Date", html_for="start-date"),
                    dcc.DatePickerSingle(
                        id="start-date",
                        date=date.today(),
                        display_format="YYYY-MM-DD",
                        style={'width': '100%'}
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("Status", html_for="status-select"),
                    dcc.Dropdown(
                        id="status-select",
                        options=[
                            {'label': 'Planning', 'value': 'Planning'},
                            {'label': 'In Progress', 'value': 'In Progress'},
                            {'label': 'Complete', 'value': 'Complete'},
                            {'label': 'On Hold', 'value': 'On Hold'},
                            {'label': 'Cancelled', 'value': 'Cancelled'},
                        ],
                        value='Planning'
                    ),
                ], md=4),
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Description"),
                    dbc.Textarea(
                        id="description-input",
                        placeholder="Enter experiment description",
                        rows=3
                    ),
                ], md=12),
            ], className="mb-3"),

            # Process Template Selection
            dbc.Row([
                dbc.Col([
                    dbc.Label("Process Template"),
                    dcc.Dropdown(
                        id="workflow-template-select",
                        options=[
                            {'label': 'Standard Process (Seed Train → Bioreactor → Shake Flask)', 'value': 'standard'},
                            {'label': 'Seed Train + Bioreactor', 'value': 'seed_train_bioreactor'},
                            {'label': 'Seed Train + Shake Flask', 'value': 'seed_train_shake_flask'},
                            {'label': 'Custom', 'value': 'custom'},
                        ],
                        value='standard'
                    ),
                ], md=6),
                dbc.Col([
                    dbc.Button(
                        "Load Template",
                        id="load-template-btn",
                        color="secondary",
                        className="mt-4"
                    )
                ], md=6)
            ], className="mb-3"),

            # Process Steps
            html.H6("Process Steps"),
            dcc.Store(id="workflow-steps-data", data=[]),  # Store step data separately
            html.Div(id="workflow-steps-container"),
            dbc.Button(
                [html.I(className="fas fa-plus me-2"), "Add Step"],
                id="add-step-btn",
                color="success",
                size="sm",
                className="mb-3"
            ),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Notes"),
                    dbc.Textarea(
                        id="notes-input",
                        placeholder="Additional notes",
                        rows=2
                    ),
                ], md=12),
            ]),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-modal", color="secondary", className="me-2"),
            dbc.Button("Save Experiment", id="save-experiment", color="primary")
        ])
    ], id="experiment-modal", size="xl", is_open=False),

    # Process Registration Modal
    dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle("Register Process Run", id="process-modal-title")
        ]),
        dbc.ModalBody([
            # Store for experiment ID
            dcc.Store(id="process-modal-experiment-id"),

            # Alert container for validation messages
            html.Div(id="process-alert-container"),

            # Experiment info display
            dbc.Card([
                dbc.CardBody([
                    html.H6(id="selected-experiment-display", className="text-primary mb-2"),
                    html.P(id="selected-experiment-info", className="text-muted small")
                ])
            ], className="mb-3"),

            # Process Step Selection
            dbc.Row([
                dbc.Col([
                    dbc.Label("Select Process Step", html_for="process-step-select"),
                    dcc.Dropdown(
                        id="process-step-select",
                        options=[],
                        placeholder="Select a process step to register vessels"
                    ),
                ], width=12),
            ], className="mb-3"),

            # Vessel Registration Section
            html.H6("Vessel Information"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Process Type"),
                    dcc.Dropdown(
                        id="process-type-select",
                        options=[
                            {'label': 'Seed Train', 'value': 'seed_train'},
                            {'label': 'Fed-Batch/Production', 'value': 'production'}
                        ],
                        value='production'
                    ),
                ], md=6),
                dbc.Col([
                    dbc.Label("Number of Vessels"),
                    dbc.Input(
                        id="num-vessels-input",
                        type="number",
                        value=1,
                        min=1,
                        max=24
                    ),
                ], md=6),
            ], className="mb-3"),

            # Common vessel parameters
            dbc.Row([
                dbc.Col([
                    dbc.Label("Inoculation Date"),
                    dcc.DatePickerSingle(
                        id="inoculation-date",
                        date=date.today(),
                        display_format="YYYY-MM-DD",
                        style={'width': '100%'}
                    ),
                ], md=3),
                dbc.Col([
                    dbc.Label("Seed Density (cells/mL)"),
                    dbc.Input(
                        id="seed-density-input",
                        type="number",
                        placeholder="e.g., 0.5E6",
                        step=0.1
                    ),
                ], md=3),
                dbc.Col([
                    dbc.Label("Vessel Type"),
                    dcc.Dropdown(
                        id="vessel-type-select",
                        options=[
                            {'label': '2L Bioreactor', 'value': '2L_BR'},
                            {'label': '5L Bioreactor', 'value': '5L_BR'},
                            {'label': '250mL Shake Flask', 'value': '250mL_SF'},
                            {'label': '500mL Shake Flask', 'value': '500mL_SF'},
                            {'label': '1L Shake Flask', 'value': '1L_SF'},
                            {'label': 'T175 Flask', 'value': 'T175'},
                            {'label': 'T225 Flask', 'value': 'T225'},
                        ],
                        value='2L_BR'
                    ),
                ], md=3),
                dbc.Col([
                    dbc.Label("Cell Line"),
                    dbc.Input(
                        id="cell-line-input",
                        placeholder="e.g., CHO-K1"
                    ),
                ], md=3),
            ], className="mb-3"),

            # Production-specific fields
            dbc.Row([
                dbc.Col([
                    dbc.Label("Seed Train ID (for Production)"),
                    dcc.Dropdown(
                        id="seed-train-id-select",
                        options=[],
                        placeholder="Select seed train used",
                        disabled=False
                    ),
                ], md=6),
                dbc.Col([
                    dbc.Label("Media Type"),
                    dbc.Input(
                        id="media-type-input",
                        placeholder="e.g., CDM4"
                    ),
                ], md=6),
            ], className="mb-3"),

            # DasGip Unit Assignment (for bioreactors)
            html.Div([
                html.H6("DasGip Unit Assignment", className="mt-3"),
                html.P("Assign DasGip unit numbers for bioreactors:", className="text-muted small"),
                html.Div(id="dasgip-units-container")
            ], id="dasgip-section", style={'display': 'none'}),

            # Vessel Preview Table
            html.H6("Vessel Preview", className="mt-4"),
            dash_table.DataTable(
                id="vessel-preview-table",
                columns=[
                    {'name': 'Vessel ID', 'id': 'vessel_id', 'editable': True},
                    {'name': 'Vessel Type', 'id': 'vessel_type'},
                    {'name': 'DasGip Unit', 'id': 'dasgip_unit', 'editable': True},
                    {'name': 'Inoculation Date', 'id': 'inoculation_date'},
                    {'name': 'Seed Density', 'id': 'seed_density'},
                    {'name': 'Cell Line', 'id': 'cell_line', 'editable': True},
                ],
                data=[],
                editable=True,
                style_cell={'textAlign': 'left'},
                style_data_conditional=[
                    {
                        'if': {'column_id': 'vessel_id'},
                        'backgroundColor': '#f8f9fa',
                    }
                ]
            )
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-process-modal", color="secondary", className="me-2"),
            dbc.Button("Register Vessels", id="save-process", color="primary")
        ])
    ], id="process-modal", size="xl", is_open=False),

    # Notification Toast
    html.Div([
        dbc.Toast(
            id="save-notification",
            header="Success",
            is_open=False,
            dismissable=True,
            icon="success",
            duration=4000,
            style={"position": "fixed", "top": 66, "right": 10, "width": 350, "z-index": 9999},
        ),
    ]),

    # Manage Experiments Modal - Redesigned with 5 tabs
    dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle("USP Experiment Tracker")
        ]),
        dbc.ModalBody([
            dcc.Store(id="selected-experiment-id", data=None),
            dcc.Store(id="manage-modal-refresh", data=0),
            dbc.Tabs([
                # Tab 1: Overview Dashboard
                dbc.Tab(label="📊 Overview", tab_id="overview-tab", children=[
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Dashboard Statistics", className="mb-4"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardBody([
                                            html.H6("Total Experiments", className="text-muted mb-2"),
                                            html.H3(id="overview-total-experiments", children="0"),
                                        ])
                                    ], color="primary", outline=True, className="mb-3")
                                ], width=3),
                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardBody([
                                            html.H6("Active Experiments", className="text-muted mb-2"),
                                            html.H3(id="overview-active-experiments", children="0"),
                                        ])
                                    ], color="success", outline=True, className="mb-3")
                                ], width=3),
                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardBody([
                                            html.H6("Total Seed Trains", className="text-muted mb-2"),
                                            html.H3(id="overview-seed-trains", children="0"),
                                        ])
                                    ], color="info", outline=True, className="mb-3")
                                ], width=3),
                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardBody([
                                            html.H6("Total Vessels", className="text-muted mb-2"),
                                            html.H3(id="overview-vessels", children="0"),
                                        ])
                                    ], color="warning", outline=True, className="mb-3")
                                ], width=3),
                            ]),
                            html.Hr(),
                            html.Div(id="overview-charts")
                        ])
                    ], className="mt-3")
                ]),

                # Tab 2: Experiments Table
                dbc.Tab(label="🧪 Experiments", tab_id="experiments-tab", children=[
                    dbc.Card([
                        dbc.CardHeader([
                            dbc.Row([
                                dbc.Col([
                                    html.H6("All Experiments", className="mb-0")
                                ], width=4),
                                dbc.Col([
                                    dbc.Input(
                                        id="experiment-search",
                                        placeholder="Search experiments...",
                                        type="text",
                                        size="sm"
                                    )
                                ], width=4),
                                dbc.Col([
                                    dbc.Button(
                                        [html.I(className="fas fa-download me-2"), "Export Excel"],
                                        id="export-experiments-btn",
                                        color="success",
                                        size="sm",
                                        className="float-end"
                                    )
                                ], width=4)
                            ])
                        ]),
                        dbc.CardBody([
                            html.Div([
                                dash_table.DataTable(
                                    id="experiments-datatable",
                                    columns=[
                                        {"name": "Experiment ID", "id": "experiment_id"},
                                        {"name": "Project ID", "id": "project_id", "editable": True},
                                        {"name": "Name/Goal", "id": "experiment_name", "editable": True},
                                        {"name": "Status", "id": "status", "editable": True, "presentation": "dropdown"},
                                        {"name": "Start Date", "id": "start_date", "editable": True, "type": "datetime"},
                                        {"name": "Target End", "id": "target_end_date", "editable": True, "type": "datetime"},
                                        {"name": "Steps", "id": "steps_count"},
                                        {"name": "Vessels", "id": "vessels_count"},
                                    ],
                                    data=[],
                                    editable=True,
                                    filter_action="native",
                                    sort_action="native",
                                    sort_mode="multi",
                                    page_action="native",
                                    page_size=15,
                                    style_table={'overflowX': 'auto'},
                                    style_cell={
                                        'textAlign': 'left',
                                        'padding': '10px',
                                        'fontSize': '13px'
                                    },
                                    style_header={
                                        'backgroundColor': 'rgb(230, 230, 230)',
                                        'fontWeight': 'bold'
                                    },
                                    style_data_conditional=[
                                        {
                                            'if': {'column_id': 'status', 'filter_query': '{status} = "Planning"'},
                                            'backgroundColor': '#fff3cd',
                                        },
                                        {
                                            'if': {'column_id': 'status', 'filter_query': '{status} = "In Progress"'},
                                            'backgroundColor': '#d1ecf1',
                                        },
                                        {
                                            'if': {'column_id': 'status', 'filter_query': '{status} = "Complete"'},
                                            'backgroundColor': '#d4edda',
                                        },
                                    ],
                                    dropdown={
                                        'status': {
                                            'options': [
                                                {'label': 'Planning', 'value': 'Planning'},
                                                {'label': 'In Progress', 'value': 'In Progress'},
                                                {'label': 'Complete', 'value': 'Complete'},
                                                {'label': 'On Hold', 'value': 'On Hold'},
                                                {'label': 'Cancelled', 'value': 'Cancelled'}
                                            ]
                                        }
                                    }
                                )
                            ])
                        ])
                    ], className="mt-3")
                ]),

                # Tab 3: Seed Trains
                dbc.Tab(label="🌱 Seed Trains", tab_id="seed-trains-tab", children=[
                    dbc.Card([
                        dbc.CardHeader([
                            dbc.Row([
                                dbc.Col([
                                    html.H6("All Seed Trains", className="mb-0")
                                ], width=6),
                                dbc.Col([
                                    dbc.ButtonGroup([
                                        dbc.Button(
                                            [html.I(className="fas fa-plus me-2"), "Register Seed Train"],
                                            id="register-seedtrain-btn",
                                            color="primary",
                                            size="sm"
                                        ),
                                        dbc.Button(
                                            [html.I(className="fas fa-trash me-2"), "Bulk Discard"],
                                            id="bulk-discard-seedtrains-btn",
                                            color="warning",
                                            size="sm"
                                        ),
                                        dbc.Button(
                                            [html.I(className="fas fa-download me-2"), "Export Excel"],
                                            id="export-seedtrains-btn",
                                            color="success",
                                            size="sm"
                                        )
                                    ], className="float-end")
                                ], width=6)
                            ])
                        ]),
                        dbc.CardBody([
                            dash_table.DataTable(
                                id="seedtrains-datatable",
                                columns=[
                                    {"name": "Experiment", "id": "experiment_id"},
                                    {"name": "Seed Train ID", "id": "seed_train_id"},
                                    {"name": "Cell Line", "id": "cell_line", "editable": True},
                                    {"name": "Thaw Date", "id": "thaw_date", "editable": True, "type": "datetime"},
                                    {"name": "Bank Age", "id": "bank_age", "editable": True},
                                    {"name": "Pool/Clone", "id": "pool_or_clone", "editable": True, "presentation": "dropdown"},
                                    {"name": "Program", "id": "program", "editable": True},
                                    {"name": "Clone", "id": "clone", "editable": True},
                                    {"name": "Media", "id": "media_type", "editable": True},
                                    {"name": "Media Lot", "id": "media_lot", "editable": True},
                                    {"name": "Discarded", "id": "is_discarded", "editable": True, "presentation": "dropdown"},
                                ],
                                data=[],
                                editable=True,
                                row_selectable="multi",
                                selected_rows=[],
                                filter_action="native",
                                sort_action="native",
                                sort_mode="multi",
                                page_action="native",
                                page_size=20,
                                style_table={'overflowX': 'auto'},
                                style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '12px'},
                                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                                style_data_conditional=[
                                    {
                                        'if': {'filter_query': '{is_discarded} = True'},
                                        'backgroundColor': '#f8d7da',
                                        'color': '#721c24',
                                    },
                                ],
                                dropdown={
                                    'pool_or_clone': {
                                        'options': [
                                            {'label': 'Pool', 'value': 'Pool'},
                                            {'label': 'Clone', 'value': 'Clone'}
                                        ]
                                    },
                                    'is_discarded': {
                                        'options': [
                                            {'label': 'No', 'value': 'False'},
                                            {'label': 'Yes', 'value': 'True'}
                                        ]
                                    }
                                }
                            )
                        ])
                    ], className="mt-3")
                ]),

                # Tab 4: Fed Batch/Vessels
                dbc.Tab(label="🔬 Fed Batch", tab_id="fedbatch-tab", children=[
                    dbc.Card([
                        dbc.CardHeader([
                            dbc.Row([
                                dbc.Col([
                                    html.H6("All Production Vessels", className="mb-0")
                                ], width=6),
                                dbc.Col([
                                    dbc.ButtonGroup([
                                        dbc.Button(
                                            [html.I(className="fas fa-plus me-2"), "Register Vessel"],
                                            id="register-vessel-btn",
                                            color="primary",
                                            size="sm"
                                        ),
                                        dbc.Button(
                                            [html.I(className="fas fa-archive me-2"), "Bulk Archive"],
                                            id="bulk-archive-vessels-btn",
                                            color="warning",
                                            size="sm"
                                        ),
                                        dbc.Button(
                                            [html.I(className="fas fa-download me-2"), "Export Excel"],
                                            id="export-vessels-btn",
                                            color="success",
                                            size="sm"
                                        )
                                    ], className="float-end")
                                ], width=6)
                            ])
                        ]),
                        dbc.CardBody([
                            dash_table.DataTable(
                                id="vessels-datatable",
                                columns=[
                                    {"name": "Experiment", "id": "experiment_id"},
                                    {"name": "Vessel ID", "id": "vessel_id"},
                                    {"name": "Cell Line", "id": "cell_line", "editable": True},
                                    {"name": "Inoc. Date", "id": "inoculation_date", "editable": True, "type": "datetime"},
                                    {"name": "Inoc. Density", "id": "inoculation_density", "editable": True},
                                    {"name": "Source", "id": "seed_train_id"},
                                    {"name": "Pool/Clone", "id": "pool_or_clone", "editable": True, "presentation": "dropdown"},
                                    {"name": "Program", "id": "program", "editable": True},
                                    {"name": "Clone", "id": "clone", "editable": True},
                                    {"name": "Media", "id": "media_type", "editable": True},
                                    {"name": "Feed Strategy", "id": "feeding_strategy", "editable": True, "presentation": "dropdown"},
                                    {"name": "Vessel Type", "id": "vessel_type", "editable": True},
                                    {"name": "Volume (L)", "id": "start_volume", "editable": True},
                                    {"name": "Vessel Size", "id": "vessel_size", "editable": True},
                                    {"name": "Status", "id": "status", "editable": True, "presentation": "dropdown"},
                                ],
                                data=[],
                                editable=True,
                                row_selectable="multi",
                                selected_rows=[],
                                filter_action="native",
                                sort_action="native",
                                sort_mode="multi",
                                page_action="native",
                                page_size=20,
                                style_table={'overflowX': 'auto'},
                                style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '12px'},
                                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                                style_data_conditional=[
                                    {
                                        'if': {'filter_query': '{status} = Archived'},
                                        'backgroundColor': '#d6d8db',
                                        'color': '#383d41',
                                    },
                                ],
                                dropdown={
                                    'pool_or_clone': {
                                        'options': [
                                            {'label': 'Pool', 'value': 'Pool'},
                                            {'label': 'Clone', 'value': 'Clone'}
                                        ]
                                    },
                                    'feeding_strategy': {
                                        'options': [
                                            {'label': 'Platform', 'value': 'Platform'},
                                            {'label': 'Standard', 'value': 'Standard'},
                                            {'label': 'Other', 'value': 'Other'}
                                        ]
                                    },
                                    'status': {
                                        'options': [
                                            {'label': 'Active', 'value': 'Active'},
                                            {'label': 'Complete', 'value': 'Complete'},
                                            {'label': 'Archived', 'value': 'Archived'}
                                        ]
                                    }
                                }
                            )
                        ])
                    ], className="mt-3")
                ]),

                # Tab 5: Cell Banks (Placeholder)
                dbc.Tab(label="🧬 Cell Banks", tab_id="banks-tab", children=[
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.H5("Cell Bank Tracking", className="mb-3"),
                                html.P("This section is reserved for future cell bank tracking functionality.", className="text-muted"),
                                html.P("Coming soon: Track cell bank information, passage numbers, and vial inventories.", className="text-muted")
                            ], className="text-center", style={"padding": "50px"})
                        ])
                    ], className="mt-3")
                ]),
            ], id="manage-tabs", active_tab="overview-tab")
        ]),
        dbc.ModalFooter([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Small("Last updated: ", className="text-muted me-2"),
                        html.Small(id="last-update-time", children=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), className="text-muted")
                    ])
                ], width=8),
                dbc.Col([
                    dbc.Button("Close", id="close-manage-modal", color="secondary", className="float-end")
                ], width=4)
            ], className="w-100")
        ])
    ], id="manage-experiments-modal", fullscreen=True, is_open=False, scrollable=True),

    # Register Seed Train Modal
    dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle("Register Seed Train")
        ]),
        dbc.ModalBody([
            # Selection Section
            dbc.Row([
                dbc.Col([
                    dbc.Label("Experiment"),
                    dcc.Dropdown(
                        id="seedtrain-experiment-select",
                        placeholder="Select experiment"
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("Process Step"),
                    dcc.Dropdown(
                        id="seedtrain-step-select",
                        placeholder="Select process step"
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("Project"),
                    dbc.Input(
                        id="seedtrain-project",
                        type="text",
                        placeholder="e.g., SI-49T5, 205X1"
                    ),
                ], md=4),
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-plus me-2"), "Add Seed Train"],
                        id="add-seedtrain-row-btn",
                        color="primary",
                        size="sm"
                    ),
                ], width="auto"),
            ], className="mb-3"),

            html.Hr(),

            # Unified Seed Trains Table
            dcc.Store(id="seedtrain-table-data", data=[]),  # Stores table rows as list of dicts
            dcc.Store(id="seedtrain-row-counter", data=0),
            html.Div(id="unified-seedtrains-table", children=[
                html.P("Select an experiment above to load existing seed trains, or click 'Add Seed Train' to add new rows",
                       className="text-muted text-center")
            ]),
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id="cancel-seedtrain-modal", color="secondary", className="me-2"),
            dbc.Button("Save All Changes", id="save-all-seedtrains", color="success")
        ])
    ], id="register-seedtrain-modal", is_open=False, scrollable=True, fullscreen=True),

    # Register Vessel Modal
    dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle("Register Vessel (Fed Batch)")
        ]),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Experiment"),
                    dcc.Dropdown(
                        id="vessel-experiment-select",
                        placeholder="Select experiment"
                    ),
                ], md=6),
                dbc.Col([
                    dbc.Label("Process Step"),
                    dcc.Dropdown(
                        id="vessel-step-select",
                        placeholder="Select process step"
                    ),
                ], md=6),
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Number of Vessels"),
                    dbc.Input(
                        id="vessel-count",
                        type="number",
                        value=1,
                        min=1,
                        max=24
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("Source Seed Train", className="text-danger"),
                    dcc.Dropdown(
                        id="vessel-source-seedtrain",
                        placeholder="Select seed train (required)"
                    ),
                ], md=8),
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Vessel Type"),
                    dcc.Dropdown(
                        id="vessel-vessel-type",
                        options=[
                            {'label': '2L Bioreactor', 'value': '2L_BRX'},
                            {'label': '5L Bioreactor', 'value': '5L_BRX'},
                            {'label': '10L Bioreactor', 'value': '10L_BRX'},
                            {'label': '15L Bioreactor', 'value': '15L_BRX'},
                            {'label': '250mL Shake Flask', 'value': '250mL_SF'},
                            {'label': '500mL Shake Flask', 'value': '500mL_SF'},
                            {'label': '1L Shake Flask', 'value': '1L_SF'},
                            {'label': '2L Shake Flask', 'value': '2L_SF'},
                        ],
                        placeholder="Select vessel type"
                    ),
                ], md=6),
                dbc.Col([
                    dbc.Label("Vessel Size"),
                    dbc.Input(
                        id="vessel-size",
                        placeholder="e.g., 3L, 500 mL"
                    ),
                ], md=6),
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Inoculation Date"),
                    dbc.Input(
                        id="vessel-inoc-date",
                        type="date",
                        value=date.today().strftime('%Y-%m-%d')
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("Inoculation Density (cells/mL)"),
                    dbc.Input(
                        id="vessel-inoc-density",
                        type="number",
                        placeholder="e.g., 3e5"
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("Cell Line"),
                    dbc.Input(
                        id="vessel-cell-line",
                        placeholder="e.g., CHO-K1"
                    ),
                ], md=4),
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Start Volume (L)"),
                    dbc.Input(
                        id="vessel-volume",
                        type="number",
                        placeholder="e.g., 1.5"
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("Feed Strategy"),
                    dcc.Dropdown(
                        id="vessel-feed-strategy",
                        options=[
                            {'label': 'Platform', 'value': 'Platform'},
                            {'label': 'Standard', 'value': 'Standard'},
                            {'label': 'Other', 'value': 'Other'}
                        ],
                        placeholder="Select strategy"
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("Media Prep"),
                    dcc.Dropdown(
                        id="vessel-media-prep",
                        placeholder="Select media preparation"
                    ),
                ], md=4),
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Pool/Clone"),
                    dcc.Dropdown(
                        id="vessel-pool-clone",
                        options=[
                            {'label': 'Pool', 'value': 'Pool'},
                            {'label': 'Clone', 'value': 'Clone'}
                        ],
                        placeholder="Select pool or clone"
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("Program"),
                    dbc.Input(
                        id="vessel-program",
                        placeholder="e.g., SI-49T5"
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("Clone"),
                    dbc.Input(
                        id="vessel-clone",
                        placeholder="e.g., 1B2"
                    ),
                ], md=4),
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Temperature (°C)"),
                    dbc.Input(
                        id="vessel-temperature",
                        type="number",
                        value=37.0,
                        step=0.1
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("pH Setpoint"),
                    dbc.Input(
                        id="vessel-ph",
                        type="number",
                        value=7.0,
                        step=0.1
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("DO (%)"),
                    dbc.Input(
                        id="vessel-do",
                        type="number",
                        value=40,
                        min=0,
                        max=100
                    ),
                ], md=4),
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Notes"),
                    dbc.Textarea(
                        id="vessel-notes",
                        placeholder="Additional notes..."
                    ),
                ], width=12),
            ], className="mb-3"),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-vessel-modal", color="secondary", className="me-2"),
            dbc.Button("Register", id="save-vessel", color="primary")
        ])
    ], id="register-vessel-modal", size="xl", is_open=False),

    # Add Process Step Modal
    dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle("Add Process Step")
        ]),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Step Name"),
                    dbc.Input(id="new-step-name", placeholder="e.g., N-1 Seed Train"),
                ], width=6),
                dbc.Col([
                    dbc.Label("Step Type"),
                    dbc.Select(
                        id="new-step-type",
                        options=[
                            {"label": "Seed Train", "value": "Seed_Train"},
                            {"label": "Bioreactor", "value": "Bioreactor"},
                            {"label": "Shake Flask", "value": "Shake_Flask"},
                            {"label": "Bioreactor and Shake Flask", "value": "Bioreactor_and_Shake_Flask"}
                        ],
                        value="Bioreactor"
                    ),
                ], width=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Planned Start Date"),
                    dbc.Input(id="new-step-start-date", type="date"),
                ], width=6),
                dbc.Col([
                    dbc.Label("Duration (days)"),
                    dbc.Input(id="new-step-duration", type="number", value=7, min=1),
                ], width=6),
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-add-step", color="secondary", className="me-2"),
            dbc.Button("Add Step", id="save-new-step", color="primary")
        ])
    ], id="add-step-modal", size="lg", is_open=False),

], fluid=True)

# Callbacks

@app.callback(
    [Output("total-experiments", "children"),
     Output("active-experiments", "children"),
     Output("bioreactor-runs", "children"),
     Output("shake-flask-runs", "children"),
     Output("seed-train-runs", "children"),
     Output("completion-rate", "children")],
    [Input("refresh-interval", "n_intervals"),
     Input("refresh-btn", "n_clicks")]
)
def update_statistics(n_intervals, refresh_clicks):
    """Update dashboard statistics"""
    stats = get_dashboard_statistics()
    return (
        stats['total_experiments'],
        stats['active_experiments'],
        stats['bioreactor_runs'],
        stats['shake_flask_runs'],
        stats['seed_train_runs'],
        f"{stats['completion_rate']}%"
    )

# Callback for Recent Activity Display
@app.callback(
    Output("recent-activity-display", "children"),
    [Input("refresh-interval", "n_intervals")]
)
def update_recent_activity(n_intervals):
    """Update recent activity display"""
    try:
        recent_experiments = USPExperiment.objects.order_by('-created_date')[:3]
        print(f"[DEBUG] Recent activity found {recent_experiments.count()} experiments")
        if recent_experiments:
            activity_items = []
            for exp in recent_experiments:
                print(f"[DEBUG] Recent activity: {exp.experiment_id}")
                activity_items.append(
                    html.P([
                        html.Strong(exp.experiment_id),
                        f" - {exp.experiment_name} ({exp.status})"
                    ], className="small mb-1")
                )
            return activity_items
        else:
            print("[DEBUG] No recent experiments found")
            return [html.P("No recent experiments found. Create a new experiment to get started!", className="text-muted small")]
    except Exception as e:
        print(f"Error updating recent activity: {e}")
        import traceback
        traceback.print_exc()
        return [html.P("Error loading activity", className="text-muted small")]

@app.callback(
    Output("gantt-chart", "figure"),
    [Input("refresh-interval", "n_intervals"),
     Input("filter-all", "n_clicks"),
     Input("filter-planning", "n_clicks"),
     Input("filter-active", "n_clicks"),
     Input("filter-complete", "n_clicks")]
)
def update_gantt_chart(n_intervals, all_clicks, planning_clicks, active_clicks, complete_clicks):
    """Update Gantt chart"""
    ctx = dash.callback_context

    # Determine which filter was clicked
    status_filter = 'all'
    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == "filter-planning":
            status_filter = 'Planning'
        elif button_id == "filter-active":
            status_filter = 'In Progress'
        elif button_id == "filter-complete":
            status_filter = 'Complete'

    df = get_experiment_gantt_data()
    return create_gantt_chart(df, status_filter=status_filter)

@app.callback(
    [Output("experiment-modal", "is_open"),
     Output("experiment-id-input", "value")],
    [Input("open-new-experiment-modal", "n_clicks"),
     Input("cancel-modal", "n_clicks")],
    [State("experiment-modal", "is_open")]
)
def handle_experiment_modal(new_clicks, cancel_clicks, is_open):
    """Handle experiment modal open/close"""
    ctx = dash.callback_context

    if not ctx.triggered:
        return is_open, generate_usp_experiment_number()

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "open-new-experiment-modal":
        return True, generate_usp_experiment_number()
    elif button_id == "cancel-modal":
        return False, generate_usp_experiment_number()

    return is_open, generate_usp_experiment_number()

@app.callback(
    [Output("workflow-steps-container", "children"),
     Output("workflow-steps-data", "data")],
    [Input("load-template-btn", "n_clicks"),
     Input("add-step-btn", "n_clicks")],
    [State("workflow-template-select", "value"),
     State("workflow-steps-container", "children"),
     State("workflow-steps-data", "data")]
)
def update_workflow_steps(load_clicks, add_clicks, template_type, current_steps, current_data):
    """Update workflow steps based on template or add new step"""
    ctx = dash.callback_context

    if not ctx.triggered:
        # Initialize with default template
        template_steps = get_default_workflow_steps()
        step_components = [
            create_step_card(i, step['step_name'], step['duration'], step['step_type'], step.get('start_date'))
            for i, step in enumerate(template_steps)
        ]
        step_data = [
            {
                'step_name': step['step_name'],
                'step_type': step['step_type'],
                'duration': step['duration'],
                'start_date': step.get('start_date').isoformat() if step.get('start_date') else date.today().isoformat(),
                'order': step['order']
            }
            for step in template_steps
        ]
        return step_components, step_data

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "load-template-btn" and template_type:
        template_steps = get_workflow_template(template_type)
        step_components = [
            create_step_card(i, step['step_name'], step['duration'], step['step_type'], step.get('start_date'))
            for i, step in enumerate(template_steps)
        ]
        step_data = [
            {
                'step_name': step['step_name'],
                'step_type': step['step_type'],
                'duration': step['duration'],
                'start_date': step.get('start_date').isoformat() if step.get('start_date') else date.today().isoformat(),
                'order': step['order']
            }
            for step in template_steps
        ]
        return step_components, step_data
    elif button_id == "add-step-btn":
        if current_steps is None:
            current_steps = []
        if current_data is None:
            current_data = []

        new_index = len(current_steps)
        new_step = create_step_card(new_index, "", 1, 'Seed_Train', date.today())
        new_data = {
            'step_name': '',
            'step_type': 'Seed_Train',
            'duration': 1,
            'start_date': date.today().isoformat(),
            'order': new_index + 1
        }

        return current_steps + [new_step], current_data + [new_data]

    return current_steps or [], current_data or []

@app.callback(
    [Output("alert-container", "children"),
     Output("experiment-modal", "is_open", allow_duplicate=True)],
    [Input("save-experiment", "n_clicks")],
    [State("experiment-id-input", "value"),
     State("experiment-name-input", "value"),
     State("project-id-input", "value"),
     State("experiment-type-select", "value"),
     State("description-input", "value"),
     State("start-date", "date"),
     State("status-select", "value"),
     State("notes-input", "value"),
     State("workflow-steps-data", "data")],
    prevent_initial_call=True
)
def save_experiment(save_clicks, experiment_id, experiment_name, project_id, experiment_type, description, start_date, status, notes, workflow_steps_data):
    """Save new USP experiment"""
    if not save_clicks:
        return [], no_update

    # Validation
    if not experiment_name or not start_date:
        return dbc.Alert(
            "Please fill in all required fields (Experiment Name, Start Date).",
            color="danger",
            dismissable=True,
            duration=5000
        ), no_update

    try:
        # Create new experiment
        experiment = USPExperiment.objects.create(
            experiment_id=experiment_id,
            experiment_name=experiment_name,
            project_id=project_id or None,
            experiment_type=experiment_type,
            description=description or "",
            start_date=pd.to_datetime(start_date).date(),
            status=status,
            notes=notes or "",
            created_by="System"  # You can get this from user context
        )

        # Create workflow steps if provided
        if workflow_steps_data:
            for i, step_data in enumerate(workflow_steps_data):
                try:
                    step_name = step_data.get('step_name', f"Step {i+1}")
                    step_type = step_data.get('step_type', 'Seed_Train')
                    duration = int(step_data.get('duration', 7))

                    # Parse start date
                    step_start_date = step_data.get('start_date')
                    if step_start_date:
                        step_start_date = pd.to_datetime(step_start_date).date()
                    else:
                        step_start_date = experiment.start_date + timedelta(days=i*7)

                    # Calculate end date
                    planned_end_date = step_start_date + timedelta(days=duration)

                    # Create the process step
                    USPProcessStep.objects.create(
                        experiment=experiment,
                        step_name=step_name if step_name else f"Step {i+1}",
                        step_type=step_type,
                        step_order=i+1,
                        planned_duration_days=duration,
                        planned_start_date=step_start_date,
                        planned_end_date=planned_end_date,
                        status='Pending'
                    )
                    print(f"Created step: {step_name} ({step_type}) - {duration} days")
                except Exception as e:
                    print(f"Error creating step {i}: {e}")
                    # Fallback to creating a default step
                    USPProcessStep.objects.create(
                        experiment=experiment,
                        step_name=f"Step {i+1}",
                        step_type="Seed_Train",
                        step_order=i+1,
                        planned_duration_days=7,
                        planned_start_date=experiment.start_date + timedelta(days=i*7),
                        status='Pending'
                    )

        return dbc.Alert(
            f"Experiment {experiment_id} created successfully!",
            color="success",
            dismissable=True,
            duration=3000
        ), False  # Close modal after successful save

    except Exception as e:
        print(f"Error creating experiment: {e}")
        return dbc.Alert(
            f"Error creating experiment: {str(e)}",
            color="danger",
            dismissable=True,
            duration=5000
        ), no_update

# Callback for opening manage experiments modal and loading all data
@app.callback(
    [Output("manage-experiments-modal", "is_open"),
     Output("overview-total-experiments", "children"),
     Output("overview-active-experiments", "children"),
     Output("overview-seed-trains", "children"),
     Output("overview-vessels", "children"),
     Output("experiments-datatable", "data"),
     Output("seedtrains-datatable", "data"),
     Output("vessels-datatable", "data"),
     Output("last-update-time", "children")],
    [Input("manage-experiments-btn", "n_clicks"),
     Input("close-manage-modal", "n_clicks")],
    [State("manage-experiments-modal", "is_open")]
)
def handle_manage_experiments_modal(manage_clicks, close_clicks, is_open):
    """Open/close manage experiments modal and load all data for tabs"""
    ctx = dash.callback_context

    if not ctx.triggered:
        return [is_open, "0", "0", "0", "0", [], [], [], datetime.now().strftime("%Y-%m-%d %H:%M:%S")]

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "manage-experiments-btn":
        try:
            # Get statistics for Overview tab
            total_experiments = USPExperiment.objects.count()
            active_experiments = USPExperiment.objects.filter(status='In Progress').count()
            total_seed_trains = USPSeedTrain.objects.count()
            total_vessels = USPVessel.objects.count()

            # Load Experiments data
            experiments = USPExperiment.objects.all().order_by('-created_date')
            experiments_data = []
            for exp in experiments:
                step_count = exp.process_steps.count()
                vessel_count = USPVessel.objects.filter(process_step__experiment=exp).count()
                experiments_data.append({
                    'experiment_id': exp.experiment_id,
                    'project_id': exp.project_id or '',
                    'experiment_name': exp.experiment_name,
                    'status': exp.status,
                    'start_date': exp.start_date.strftime('%Y-%m-%d') if exp.start_date else '',
                    'target_end_date': exp.target_end_date.strftime('%Y-%m-%d') if exp.target_end_date else '',
                    'steps_count': step_count,
                    'vessels_count': vessel_count,
                })

            # Load Seed Trains data
            seed_trains = USPSeedTrain.objects.select_related('process_step__experiment').all()
            seedtrains_data = []
            for st in seed_trains:
                seedtrains_data.append({
                    'experiment_id': st.process_step.experiment.experiment_id,
                    'seed_train_id': st.seed_train_id,
                    'cell_line': st.cell_line or '',
                    'thaw_date': st.thaw_date.strftime('%Y-%m-%d') if st.thaw_date else '',
                    'bank_age': st.bank_age or '',
                    'pool_or_clone': st.pool_or_clone or '',
                    'program': st.program or '',
                    'clone': st.clone or '',
                    'media_type': st.media_type or '',
                    'media_lot': st.media_lot or '',
                    'is_discarded': 'True' if st.is_discarded else 'False',
                })

            # Load Vessels data
            vessels = USPVessel.objects.select_related('process_step__experiment', 'seed_train').all()
            vessels_data = []
            for v in vessels:
                vessels_data.append({
                    'experiment_id': v.process_step.experiment.experiment_id,
                    'vessel_id': v.vessel_id,
                    'cell_line': v.cell_line or '',
                    'inoculation_date': v.inoculation_date.strftime('%Y-%m-%d') if v.inoculation_date else '',
                    'inoculation_density': v.inoculation_density or '',
                    'seed_train_id': v.seed_train.seed_train_id if v.seed_train else '',
                    'pool_or_clone': v.pool_or_clone or '',
                    'program': v.program or '',
                    'clone': v.clone or '',
                    'media_type': v.media_type or '',
                    'feeding_strategy': v.feeding_strategy or '',
                    'vessel_type': v.vessel_type or '',
                    'start_volume': v.start_volume or '',
                    'vessel_size': v.vessel_size or '',
                    'status': v.status or 'Active',
                })

            return [
                True,  # Open modal
                str(total_experiments),
                str(active_experiments),
                str(total_seed_trains),
                str(total_vessels),
                experiments_data,
                seedtrains_data,
                vessels_data,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ]

        except Exception as e:
            print(f"Error loading manage experiments data: {e}")
            import traceback
            traceback.print_exc()
            return [True, "0", "0", "0", "0", [], [], [], datetime.now().strftime("%Y-%m-%d %H:%M:%S")]

    elif button_id == "close-manage-modal":
        return [False, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update]

    return [is_open, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update]

# Callback for handling Edit button clicks
@app.callback(
    [Output("manage-tabs", "active_tab"),
     Output("selected-experiment-id", "data"),
     Output("edit-exp-id", "value"),
     Output("edit-exp-name", "value"),
     Output("edit-exp-type", "value"),
     Output("edit-exp-status", "value"),
     Output("edit-exp-start-date", "value"),
     Output("edit-exp-target-date", "value"),
     Output("edit-exp-description", "value"),
     Output("process-steps-edit-section", "children"),
     Output("vessels-edit-section", "children")],
    [Input({'type': 'edit-experiment-btn', 'index': ALL}, 'n_clicks')],
    [State("manage-tabs", "active_tab")]
)
def handle_edit_click(n_clicks_list, current_tab):
    """Handle edit button click and load experiment data"""
    # Get the button that was clicked
    ctx = dash.callback_context
    if not ctx.triggered or not any(n_clicks_list):
        raise dash.exceptions.PreventUpdate

    # Extract the experiment ID from the button ID
    button_id = ctx.triggered[0]['prop_id']
    experiment_id = eval(button_id.split('.')[0])['index']

    print(f"[DEBUG] Edit button clicked for experiment ID: {experiment_id}")

    try:
        # Load the experiment
        experiment = USPExperiment.objects.get(id=experiment_id)
        print(f"[DEBUG] Loaded experiment: {experiment.experiment_id} - {experiment.experiment_name}")

        # Load process steps
        steps = experiment.process_steps.all().order_by('step_order')
        steps_table = html.Table(
            className="table table-sm",
            children=[
                html.Thead([
                    html.Tr([
                        html.Th("Step Name"),
                        html.Th("Type"),
                        html.Th("Order"),
                        html.Th("Start Date"),
                        html.Th("Duration (days)"),
                        html.Th("Status"),
                        html.Th("Vessels"),
                        html.Th("Actions")
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(step.step_name),
                        html.Td(step.step_type.replace('_', ' ')),
                        html.Td(str(step.step_order)),
                        html.Td(step.planned_start_date.strftime('%Y-%m-%d') if step.planned_start_date else 'Not set'),
                        html.Td(str(step.planned_duration_days)),
                        html.Td(dbc.Badge(step.status, color="primary" if step.status == "Complete" else "warning")),
                        html.Td(str(step.vessels.count())),
                        html.Td([
                            dbc.ButtonGroup([
                                dbc.Button("Edit", id={'type': 'edit-step-btn', 'index': step.id}, size="sm", color="info", className="me-1"),
                                dbc.Button("Delete", id={'type': 'delete-step-btn', 'index': step.id}, size="sm", color="danger")
                            ], size="sm")
                        ])
                    ]) for step in steps
                ])
            ]
        )

        # Load both seed trains and vessels
        seed_trains = USPSeedTrain.objects.filter(process_step__experiment=experiment)
        vessels = USPVessel.objects.filter(process_step__experiment=experiment)

        # Combine into one table
        table_rows = []

        # Add seed trains
        for st in seed_trains:
            table_rows.append(html.Tr([
                html.Td(st.seed_train_id, style={'backgroundColor': '#e7f3ff'}),
                html.Td(st.vessel_type),
                html.Td(st.process_step.step_name),
                html.Td(st.cell_line),
                html.Td(st.thaw_date.strftime('%Y-%m-%d')),
                html.Td([
                    dbc.ButtonGroup([
                        dbc.Button("Edit", size="sm", color="info", className="me-1"),
                        dbc.Button("Delete", size="sm", color="danger")
                    ], size="sm")
                ])
            ]))

        # Add vessels
        for vessel in vessels:
            seed_train_label = f"← {vessel.seed_train.seed_train_id}" if vessel.seed_train else ""
            table_rows.append(html.Tr([
                html.Td([vessel.vessel_id, html.Small(f" {seed_train_label}", className="text-muted ms-1")]),
                html.Td(vessel.vessel_type),
                html.Td(vessel.process_step.step_name),
                html.Td(vessel.cell_line or 'N/A'),
                html.Td(vessel.inoculation_date.strftime('%Y-%m-%d') if vessel.inoculation_date else 'Not set'),
                html.Td([
                    dbc.ButtonGroup([
                        dbc.Button("Edit", size="sm", color="info", className="me-1"),
                        dbc.Button("Delete", size="sm", color="danger")
                    ], size="sm")
                ])
            ]))

        vessels_table = html.Table(
            className="table table-sm table-hover",
            children=[
                html.Thead([
                    html.Tr([
                        html.Th("Vessel/Seed Train ID"),
                        html.Th("Type"),
                        html.Th("Process Step"),
                        html.Th("Cell Line"),
                        html.Th("Date"),
                        html.Th("Actions")
                    ])
                ]),
                html.Tbody(table_rows)
            ]
        )

        # Debug: Print what we're about to return
        print(f"[DEBUG] Returning values:")
        print(f"  - Tab: edit-tab")
        print(f"  - Experiment ID for store: {experiment.id}")
        print(f"  - Experiment ID field: {experiment.experiment_id}")
        print(f"  - Name: {experiment.experiment_name}")
        print(f"  - Type: {experiment.experiment_type or ''}")
        print(f"  - Status: {experiment.status}")
        print(f"  - Start date: {experiment.start_date.strftime('%Y-%m-%d') if experiment.start_date else ''}")
        print(f"  - Target date: {experiment.target_end_date.strftime('%Y-%m-%d') if experiment.target_end_date else ''}")
        print(f"  - Description: {experiment.description or ''}")
        print(f"  - Steps table: {'Generated' if steps.exists() else 'None'}")
        print(f"  - Modal open: True")

        return (
            "edit-tab",  # Switch to edit tab
            experiment.id,
            experiment.experiment_id,
            experiment.experiment_name,
            experiment.experiment_type or "",  # Add experiment type
            experiment.status,
            experiment.start_date.strftime('%Y-%m-%d') if experiment.start_date else "",
            experiment.target_end_date.strftime('%Y-%m-%d') if experiment.target_end_date else "",
            experiment.description or "",
            steps_table if steps.exists() else html.P("No process steps defined", className="text-muted"),
            html.Div()  # vessels-edit-section is now handled by per-step-vessels-section
        )
    except Exception as e:
        print(f"Error loading experiment: {e}")
        import traceback
        traceback.print_exc()
        return [dash.no_update] * 11

# Callback to generate per-step vessel sections
@app.callback(
    [Output("per-step-vessels-section", "children"),
     Output("step-filter-dropdown", "options")],
    [Input("selected-experiment-id", "data"),
     Input("step-filter-dropdown", "value")]
)
def generate_per_step_sections(experiment_id, filter_value):
    """Generate collapsible sections for each process step with vessels"""
    print(f"[DEBUG] generate_per_step_sections called with experiment_id: {experiment_id} (type: {type(experiment_id)}), filter_value: {filter_value}")

    # Check callback context
    ctx = dash.callback_context
    if ctx.triggered:
        print(f"[DEBUG] Triggered by: {ctx.triggered[0]['prop_id']}")
    else:
        print(f"[DEBUG] No trigger context")

    if not experiment_id:
        print(f"[DEBUG] No experiment_id provided, returning 'No experiment selected'")
        return html.P("No experiment selected", className="text-muted"), [{"label": "All Steps", "value": "all"}]

    try:
        print(f"[DEBUG] Fetching experiment with ID: {experiment_id}")
        experiment = USPExperiment.objects.get(id=experiment_id)
        steps = experiment.process_steps.all().order_by('step_order')

        if not steps.exists():
            return html.P("No process steps defined. Add steps first.", className="text-muted"), [{"label": "All Steps", "value": "all"}]

        # Build filter options
        filter_options = [{"label": "All Steps", "value": "all"}]
        filter_options.extend([
            {"label": f"Step {step.step_order}: {step.step_name}", "value": str(step.id)}
            for step in steps
        ])

        # Generate sections for each step
        step_sections = []
        for step in steps:
            # Skip if filtered out
            if filter_value != "all" and str(step.id) != filter_value:
                continue

            # Get vessels and seed trains for this step
            vessels = USPVessel.objects.filter(process_step=step, is_archived=False)
            seed_trains = USPSeedTrain.objects.filter(process_step=step, is_archived=False)

            # Build vessel table
            vessel_rows = []
            for st in seed_trains:
                vessel_rows.append(html.Tr([
                    html.Td(st.seed_train_id, style={'backgroundColor': '#e7f3ff'}),
                    html.Td(st.vessel_type),
                    html.Td(f"{st.start_volume} mL" if st.start_volume else "N/A"),
                    html.Td(st.cell_line),
                    html.Td(st.thaw_date.strftime('%Y-%m-%d') if st.thaw_date else "N/A"),
                    html.Td([
                        dbc.ButtonGroup([
                            dbc.Button("Edit", size="sm", color="info", className="me-1"),
                            dbc.Button("Archive", size="sm", color="warning", className="me-1"),
                            dbc.Button("Discard", size="sm", color="danger")
                        ], size="sm")
                    ])
                ]))

            for v in vessels:
                vessel_rows.append(html.Tr([
                    html.Td(v.vessel_id),
                    html.Td(v.vessel_type),
                    html.Td(f"{v.start_volume} mL" if v.start_volume else "N/A"),
                    html.Td(v.cell_line or "N/A"),
                    html.Td(v.inoculation_date.strftime('%Y-%m-%d') if v.inoculation_date else "Not set"),
                    html.Td([
                        dbc.ButtonGroup([
                            dbc.Button("Edit", size="sm", color="info", className="me-1"),
                            dbc.Button("Archive", size="sm", color="warning", className="me-1"),
                            dbc.Button("Discard", size="sm", color="danger")
                        ], size="sm")
                    ])
                ]))

            vessel_table = html.Table(
                className="table table-striped table-hover table-sm",
                children=[
                    html.Thead([
                        html.Tr([
                            html.Th("ID"),
                            html.Th("Type"),
                            html.Th("Volume"),
                            html.Th("Cell Line"),
                            html.Th("Date"),
                            html.Th("Actions")
                        ])
                    ]),
                    html.Tbody(vessel_rows) if vessel_rows else html.Tbody([
                        html.Tr([html.Td("No vessels added yet", colSpan=6, className="text-muted text-center")])
                    ])
                ]
            )

            # Get filtered vessel type options for this step
            vessel_type_options = get_vessel_type_options_for_step(step.step_type)

            # Create collapsible section for this step
            step_section = dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H6(f"Step {step.step_order}: {step.step_name}", className="mb-0"),
                            html.Small(f"{step.step_type.replace('_', ' ')} | {step.status}", className="text-muted")
                        ], width=10),
                        dbc.Col([
                            dbc.Button(
                                [html.I(className="fas fa-plus me-1"), "Add Vessel"],
                                id={'type': 'add-vessel-btn', 'index': step.id},
                                size="sm",
                                color="success"
                            )
                        ], width=2, className="text-end")
                    ])
                ]),
                dbc.Collapse([
                    dbc.CardBody([
                        # Vessel table
                        vessel_table,

                        # Add vessel form (initially hidden)
                        html.Div([
                            html.Hr(),
                            html.H6("Add New Vessels", className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Vessel Type"),
                                    dbc.Select(
                                        id={'type': 'new-vessel-type', 'index': step.id},
                                        options=vessel_type_options
                                    )
                                ], width=3),
                                dbc.Col([
                                    dbc.Label("Start Volume (mL)"),
                                    dbc.Input(
                                        id={'type': 'new-vessel-volume', 'index': step.id},
                                        type="number"
                                    )
                                ], width=2),
                                dbc.Col([
                                    dbc.Label("Date"),
                                    dbc.Input(
                                        id={'type': 'new-vessel-date', 'index': step.id},
                                        type="date"
                                    )
                                ], width=2),
                                dbc.Col([
                                    dbc.Label("Count"),
                                    dbc.Input(
                                        id={'type': 'new-vessel-count', 'index': step.id},
                                        type="number",
                                        value=1,
                                        min=1
                                    )
                                ], width=2),
                                dbc.Col([
                                    html.Label("\u00A0"),  # Spacer
                                    html.Div([
                                        dbc.Button("Generate", id={'type': 'gen-vessel-btn', 'index': step.id}, color="primary", size="sm", className="me-2"),
                                        dbc.Button("Cancel", id={'type': 'cancel-vessel-btn', 'index': step.id}, color="secondary", size="sm")
                                    ])
                                ], width=3)
                            ]),
                            html.Div(id={'type': 'vessel-preview', 'index': step.id}, className="mt-3")
                        ], id={'type': 'add-vessel-form', 'index': step.id}, style={"display": "none"})
                    ])
                ], id={'type': 'step-collapse', 'index': step.id}, is_open=True)
            ], className="mb-2")

            step_sections.append(step_section)

        if not step_sections:
            return html.P("No steps match the selected filter", className="text-muted"), filter_options

        return html.Div(step_sections), filter_options

    except Exception as e:
        print(f"Error generating per-step sections: {e}")
        import traceback
        traceback.print_exc()
        return html.P(f"Error: {str(e)}", className="text-danger"), [{"label": "All Steps", "value": "all"}]

# Callback to toggle add vessel form visibility
@app.callback(
    Output({'type': 'add-vessel-form', 'index': MATCH}, 'style'),
    [Input({'type': 'add-vessel-btn', 'index': MATCH}, 'n_clicks'),
     Input({'type': 'cancel-vessel-btn', 'index': MATCH}, 'n_clicks')],
    [State({'type': 'add-vessel-form', 'index': MATCH}, 'style')],
    prevent_initial_call=True
)
def toggle_add_vessel_form(add_clicks, cancel_clicks, current_style):
    """Toggle visibility of add vessel form"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return {"display": "none"}

    button_id = ctx.triggered[0]['prop_id']

    if 'add-vessel-btn' in button_id:
        return {"display": "block"}
    elif 'cancel-vessel-btn' in button_id:
        return {"display": "none"}

    return current_style or {"display": "none"}

# Callback to show/hide vessel config section based on step selection and type
@app.callback(
    [Output("vessel-config-section", "style"),
     Output("seed-train-config-section", "style"),
     Output("seed-train-source", "options")],
    [Input("vessel-step-select", "value")],
    [State("selected-experiment-id", "data")]
)
def show_vessel_config(step_id, experiment_id):
    """Show appropriate configuration based on step type"""
    if not step_id or not experiment_id:
        return {"display": "none"}, {"display": "none"}, []

    try:
        # Get the selected step
        step = USPProcessStep.objects.get(id=step_id)

        # Get seed trains for this experiment from USPSeedTrain model
        seed_trains = USPSeedTrain.objects.filter(
            process_step__experiment_id=experiment_id
        )

        seed_options = [{"label": "No seed train", "value": None}]
        seed_options.extend([
            {"label": f"{st.seed_train_id} ({st.cell_line})", "value": st.id}
            for st in seed_trains
        ])

        # Show different sections based on step type
        if step.step_type == 'Seed_Train':
            # Show seed train configuration
            return {"display": "none"}, {"display": "block"}, seed_options
        else:
            # Show regular vessel configuration
            return {"display": "block"}, {"display": "none"}, seed_options
    except:
        return {"display": "none"}, {"display": "none"}, []

# Callback to generate vessel preview with editable DataTable
@app.callback(
    Output("vessel-preview-container", "children"),
    [Input("generate-vessels-btn", "n_clicks"),
     Input("clear-vessels-btn", "n_clicks")],
    [State("vessel-step-select", "value"),
     State("edit-vessel-type-select", "value"),
     State("vessel-start-volume", "value"),
     State("vessel-inoc-date", "value"),
     State("vessel-inoc-density", "value"),
     State("vessel-feeding-strategy", "value"),
     State("vessel-count", "value"),
     State("selected-experiment-id", "data")]
)
def generate_vessel_preview(generate_clicks, clear_clicks, step_id, vessel_type, start_volume, inoc_date,
                           inoc_density, feeding_strategy, vessel_count, experiment_id):
    """Generate editable DataTable for bioreactor/shake flask vessels"""
    ctx = dash.callback_context

    if not ctx.triggered:
        return html.P("No vessels to add", className="text-muted")

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "clear-vessels-btn":
        return html.P("No vessels to add", className="text-muted")

    if button_id == "generate-vessels-btn":
        if not all([step_id, vessel_type, inoc_date, vessel_count]):
            return dbc.Alert("Please fill in all required fields", color="warning")

        try:
            # Get the starting fed batch number
            last_vessel = USPVessel.objects.filter(
                vessel_id__startswith='UPFB'
            ).order_by('-vessel_id').first()

            if last_vessel:
                start_number = int(last_vessel.vessel_id[4:]) + 1
            else:
                start_number = 1

            # Get seed train options for dropdown
            seed_train_options = []
            if experiment_id:
                experiment = USPExperiment.objects.get(id=experiment_id)
                seed_trains = USPSeedTrain.objects.filter(process_step__experiment=experiment)
                seed_train_options = [
                    {'label': st.seed_train_id, 'value': st.seed_train_id}
                    for st in seed_trains
                ]
                print(f"[DEBUG] Seed train options for dropdown: {seed_train_options}")

            # Generate vessel data with incrementing IDs
            vessels = []
            for i in range(int(vessel_count)):
                fed_batch_id = f"UPFB{(start_number + i):04d}"
                reactor_number = i + 1

                vessel_data = {
                    "fed_batch_id": fed_batch_id,
                    "seed_train_id": "",  # User will select
                    "vessel_type": vessel_type,
                    "start_volume": start_volume or "",
                    "reactor_number": reactor_number,
                    "inoculation_date": inoc_date,
                    "inoculation_density": inoc_density or "",
                    "feeding_strategy": feeding_strategy or ""
                }

                vessels.append(vessel_data)

            # Create editable DataTable
            table = dash_table.DataTable(
                id="vessels-data-table",
                data=vessels,
                columns=[
                    {'id': 'fed_batch_id', 'name': 'Fed Batch ID', 'editable': False},
                    {'id': 'seed_train_id', 'name': 'Seed Train ID', 'presentation': 'dropdown'},
                    {'id': 'vessel_type', 'name': 'Vessel Type', 'editable': False},
                    {'id': 'start_volume', 'name': 'Start Volume (mL)', 'type': 'numeric', 'editable': True},
                    {'id': 'reactor_number', 'name': 'Reactor #', 'editable': False},
                    {'id': 'inoculation_date', 'name': 'Inoc. Date', 'editable': False},
                    {'id': 'inoculation_density', 'name': 'Inoc. Density (cells/mL)', 'type': 'numeric', 'editable': True},
                    {'id': 'feeding_strategy', 'name': 'Feeding Strategy', 'editable': True}
                ],
                editable=True,
                row_deletable=True,
                dropdown={
                    'seed_train_id': {
                        'options': seed_train_options,
                        'clearable': True
                    }
                },
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'fontSize': '14px',
                    'minWidth': '100px'
                },
                style_cell_conditional=[
                    {
                        'if': {'column_id': 'seed_train_id'},
                        'backgroundColor': 'rgb(255, 255, 230)',
                        'cursor': 'pointer'
                    }
                ],
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'column_editable': True},
                        'backgroundColor': 'rgb(248, 248, 255)'
                    }
                ],
                css=[{
                    'selector': '.Select-menu-outer',
                    'rule': 'display: block !important'
                }]
            )

            # Add save button
            return html.Div([
                html.H6(f"Bioreactor/Shake Flask Vessels ({len(vessels)} vessels):", className="mb-3"),
                table,
                html.Hr(className="mt-3"),
                dbc.Button(
                    f"Save {len(vessels)} Vessels",
                    id="save-vessels-btn",
                    color="success",
                    className="mt-2"
                )
            ])

        except Exception as e:
            print(f"Error generating vessels: {e}")
            return dbc.Alert(f"Error: {str(e)}", color="danger")

    return html.P("No vessels to add", className="text-muted")

# Callback to generate seed train preview table
@app.callback(
    Output("seed-train-preview-table", "children"),
    [Input("generate-seed-trains-btn", "n_clicks"),
     Input("clear-seed-trains-btn", "n_clicks")],
    [State("seed-train-thaw-date", "value"),
     State("seed-train-start-volume", "value"),
     State("seed-train-sample-count", "value"),
     State("seed-train-media", "value"),
     State("vessel-step-select", "value")]
)
def generate_seed_train_preview(generate_clicks, clear_clicks, thaw_date, start_volume, sample_count, media, step_id):
    """Generate editable table for seed train samples"""
    ctx = dash.callback_context

    if not ctx.triggered:
        return html.P("No seed train samples to add", className="text-muted")

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "clear-seed-trains-btn":
        return html.P("No seed train samples to add", className="text-muted")

    if button_id == "generate-seed-trains-btn":
        if not all([thaw_date, sample_count, media]):
            return dbc.Alert("Please fill in Thaw Date, Number of Samples, and Media Type", color="warning")

        try:
            # Get the starting seed train number
            last_seed_train = USPSeedTrain.objects.filter(
                seed_train_id__startswith='UPST'
            ).order_by('-seed_train_id').first()

            if last_seed_train:
                start_number = int(last_seed_train.seed_train_id[4:]) + 1
            else:
                start_number = 1

            # Generate seed train samples with incrementing IDs
            samples = []
            for i in range(int(sample_count)):
                seed_train_id = f"UPST{(start_number + i):04d}"
                samples.append({
                    "seed_train_id": seed_train_id,
                    "vessel_size": "",  # User will fill
                    "start_volume": start_volume or "",  # From input
                    "cell_line": "",  # User will fill
                    "thaw_date": thaw_date,
                    "media": media
                })

            # Create editable DataTable with reordered columns
            table = dash_table.DataTable(
                id="seed-train-data-table",
                data=samples,
                columns=[
                    {'id': 'cell_line', 'name': 'Cell Line', 'editable': True},
                    {'id': 'seed_train_id', 'name': 'Seed Train ID', 'editable': False},
                    {'id': 'vessel_size', 'name': 'Vessel Size', 'editable': True, 'presentation': 'dropdown'},
                    {'id': 'start_volume', 'name': 'Start Volume (mL)', 'type': 'numeric', 'editable': True},
                    {'id': 'thaw_date', 'name': 'Thaw Date', 'editable': True},
                    {'id': 'media', 'name': 'Media', 'editable': True}
                ],
                editable=True,
                row_deletable=True,
                dropdown={
                    'vessel_size': {
                        'options': [
                            {'label': 'T25 Flask', 'value': 'T25'},
                            {'label': 'T75 Flask', 'value': 'T75'},
                            {'label': 'T175 Flask', 'value': 'T175'},
                            {'label': 'T225 Flask', 'value': 'T225'},
                            {'label': '125mL Shake Flask', 'value': '125mL_SF'},
                            {'label': '250mL Shake Flask', 'value': '250mL_SF'},
                            {'label': '500mL Shake Flask', 'value': '500mL_SF'},
                        ]
                    }
                },
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'fontSize': '14px'
                },
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'column_editable': True},
                        'backgroundColor': 'rgb(248, 248, 255)'
                    }
                ]
            )

            return html.Div([
                html.H6(f"Seed Train Samples ({len(samples)} samples):", className="mb-3"),
                table,
                html.Hr(className="mt-3"),
                dbc.Button(
                    f"Save {len(samples)} Seed Train Samples",
                    id="save-seed-trains-btn",
                    color="success",
                    className="mt-2"
                )
            ])

        except Exception as e:
            print(f"Error generating seed train samples: {e}")
            return dbc.Alert(f"Error: {str(e)}", color="danger")

    return html.P("No seed train samples to add", className="text-muted")

# Callback to save seed trains
@app.callback(
    [Output("vessels-edit-section", "children", allow_duplicate=True),
     Output("seed-train-preview-table", "children", allow_duplicate=True),
     Output("save-notification", "is_open", allow_duplicate=True),
     Output("save-notification", "children", allow_duplicate=True)],
    [Input("save-seed-trains-btn", "n_clicks")],
    [State("seed-train-data-table", "data"),
     State("vessel-step-select", "value"),
     State("selected-experiment-id", "data")],
    prevent_initial_call=True
)
def save_seed_trains_to_database(n_clicks, seed_train_data, step_id, experiment_id):
    """Save seed train samples to the database"""
    if not n_clicks or not seed_train_data or not step_id:
        return dash.no_update, dash.no_update, False, ""

    try:
        # Validate that all required fields are filled
        for sample in seed_train_data:
            if not all([sample.get('vessel_size'), sample.get('start_volume'), sample.get('cell_line')]):
                return (
                    dash.no_update,
                    dbc.Alert("Please fill in Vessel Size, Start Volume, and Cell Line for all samples",
                             color="danger"),
                    True,
                    "Please fill in all required fields before saving"
                )

        # Save each seed train sample using USPSeedTrain model
        for sample in seed_train_data:
            USPSeedTrain.objects.create(
                process_step_id=step_id,
                seed_train_id=sample['seed_train_id'],
                vessel_type=sample['vessel_size'],
                thaw_date=pd.to_datetime(sample['thaw_date']).date(),
                start_volume=float(sample['start_volume']),
                cell_line=sample['cell_line'],
                media_type=sample['media']
            )
            print(f"[DEBUG] Created seed train: {sample['seed_train_id']}")

        # Reload all vessels and seed trains for display
        experiment = USPExperiment.objects.get(id=experiment_id)
        all_vessels = USPVessel.objects.filter(process_step__experiment=experiment)
        all_seed_trains = USPSeedTrain.objects.filter(process_step__experiment=experiment)

        # Combine into one display table
        table_rows = []

        # Add seed trains
        for st in all_seed_trains:
            table_rows.append(html.Tr([
                html.Td(st.seed_train_id, style={'backgroundColor': '#e7f3ff'}),
                html.Td(st.vessel_type),
                html.Td(st.process_step.step_name),
                html.Td(st.cell_line),
                html.Td(st.thaw_date.strftime('%Y-%m-%d')),
                html.Td([
                    dbc.ButtonGroup([
                        dbc.Button("Edit", size="sm", color="info", className="me-1"),
                        dbc.Button("Delete", size="sm", color="danger")
                    ], size="sm")
                ])
            ]))

        # Add vessels
        for v in all_vessels:
            seed_train_label = f"← {v.seed_train.seed_train_id}" if v.seed_train else ""
            table_rows.append(html.Tr([
                html.Td([v.vessel_id, html.Small(f" {seed_train_label}", className="text-muted ms-1")]),
                html.Td(v.vessel_type),
                html.Td(v.process_step.step_name),
                html.Td(v.cell_line or 'N/A'),
                html.Td(v.inoculation_date.strftime('%Y-%m-%d') if v.inoculation_date else 'Not set'),
                html.Td([
                    dbc.ButtonGroup([
                        dbc.Button("Edit", size="sm", color="info", className="me-1"),
                        dbc.Button("Delete", size="sm", color="danger")
                    ], size="sm")
                ])
            ]))

        vessels_table = html.Table(
            className="table table-sm table-hover",
            children=[
                html.Thead([
                    html.Tr([
                        html.Th("Vessel/Seed Train ID"),
                        html.Th("Type"),
                        html.Th("Process Step"),
                        html.Th("Cell Line"),
                        html.Th("Date"),
                        html.Th("Actions")
                    ])
                ]),
                html.Tbody(table_rows)
            ]
        )

        success_msg = dbc.Alert(
            f"Successfully saved {len(seed_train_data)} seed train samples!",
            color="success",
            dismissable=True
        )

        notification_text = f"Successfully saved {len(seed_train_data)} seed train samples to the database!"

        return (
            vessels_table if (all_vessels.exists() or all_seed_trains.exists()) else html.P("No vessels registered", className="text-muted"),
            success_msg,
            True,
            notification_text
        )

    except Exception as e:
        print(f"Error saving seed trains: {e}")
        import traceback
        traceback.print_exc()
        return (
            dash.no_update,
            dbc.Alert(f"Error saving seed trains: {str(e)}", color="danger"),
            True,
            f"Error saving seed trains: {str(e)}"
        )

# Callback to save vessels
@app.callback(
    [Output("vessels-edit-section", "children", allow_duplicate=True),
     Output("vessel-preview-container", "children", allow_duplicate=True),
     Output("save-notification", "is_open", allow_duplicate=True),
     Output("save-notification", "children", allow_duplicate=True)],
    [Input("save-vessels-btn", "n_clicks")],
    [State("vessels-data-table", "data"),
     State("vessel-step-select", "value"),
     State("selected-experiment-id", "data")],
    prevent_initial_call=True
)
def save_vessels_to_database(n_clicks, vessels_data, step_id, experiment_id):
    """Save vessels to the database"""
    if not n_clicks or not vessels_data or not step_id or not experiment_id:
        return dash.no_update, dash.no_update, False, ""

    try:
        # Save each vessel
        for vessel in vessels_data:
            # Get the seed train FK if specified
            seed_train_fk = None
            if vessel.get("seed_train_id"):
                try:
                    seed_train_fk = USPSeedTrain.objects.get(seed_train_id=vessel["seed_train_id"])
                except:
                    pass

            # Create the vessel with FK to seed train
            new_vessel = USPVessel.objects.create(
                process_step_id=step_id,
                seed_train=seed_train_fk,
                vessel_id=vessel["fed_batch_id"],
                vessel_type=vessel["vessel_type"],
                start_volume=float(vessel["start_volume"]) if vessel.get("start_volume") else None,
                inoculation_date=pd.to_datetime(vessel["inoculation_date"]).date(),
                inoculation_density=float(vessel["inoculation_density"]) if vessel.get("inoculation_density") else None,
                feeding_strategy=vessel.get("feeding_strategy"),
                notes=f"Reactor #{vessel['reactor_number']}"
            )

            print(f"[DEBUG] Created vessel: {new_vessel.vessel_id} linked to seed train: {seed_train_fk.seed_train_id if seed_train_fk else 'None'}")

        # Reload all vessels and seed trains for display
        experiment = USPExperiment.objects.get(id=experiment_id)
        all_vessels = USPVessel.objects.filter(process_step__experiment=experiment)
        all_seed_trains = USPSeedTrain.objects.filter(process_step__experiment=experiment)

        # Combine into one display table
        table_rows = []

        # Add seed trains
        for st in all_seed_trains:
            table_rows.append(html.Tr([
                html.Td(st.seed_train_id, style={'backgroundColor': '#e7f3ff'}),
                html.Td(st.vessel_type),
                html.Td(st.process_step.step_name),
                html.Td(st.cell_line),
                html.Td(st.thaw_date.strftime('%Y-%m-%d')),
                html.Td([
                    dbc.ButtonGroup([
                        dbc.Button("Edit", size="sm", color="info", className="me-1"),
                        dbc.Button("Delete", size="sm", color="danger")
                    ], size="sm")
                ])
            ]))

        # Add vessels
        for v in all_vessels:
            seed_train_label = f"← {v.seed_train.seed_train_id}" if v.seed_train else ""
            table_rows.append(html.Tr([
                html.Td([v.vessel_id, html.Small(f" {seed_train_label}", className="text-muted ms-1")]),
                html.Td(v.vessel_type),
                html.Td(v.process_step.step_name),
                html.Td(v.cell_line or 'N/A'),
                html.Td(v.inoculation_date.strftime('%Y-%m-%d') if v.inoculation_date else 'Not set'),
                html.Td([
                    dbc.ButtonGroup([
                        dbc.Button("Edit", size="sm", color="info", className="me-1"),
                        dbc.Button("Delete", size="sm", color="danger")
                    ], size="sm")
                ])
            ]))

        vessels_table = html.Table(
            className="table table-sm table-hover",
            children=[
                html.Thead([
                    html.Tr([
                        html.Th("Vessel/Seed Train ID"),
                        html.Th("Type"),
                        html.Th("Process Step"),
                        html.Th("Cell Line"),
                        html.Th("Date"),
                        html.Th("Actions")
                    ])
                ]),
                html.Tbody(table_rows)
            ]
        )

        notification_text = f"Successfully saved {len(vessels_data)} vessels to the database!"

        return (
            vessels_table if (all_vessels.exists() or all_seed_trains.exists()) else html.P("No vessels registered", className="text-muted"),
            html.P("Vessels saved successfully", className="text-success"),
            True,
            notification_text
        )

    except Exception as e:
        print(f"Error saving vessels: {e}")
        import traceback
        traceback.print_exc()
        return (
            dash.no_update,
            dbc.Alert(f"Error saving vessels: {str(e)}", color="danger"),
            True,
            f"Error saving vessels: {str(e)}"
        )

# Callback for Add Vessels button in Edit tab
@app.callback(
    [Output("process-modal", "is_open", allow_duplicate=True),
     Output("process-modal-experiment-id", "data"),
     Output("selected-experiment-display", "children", allow_duplicate=True),
     Output("selected-experiment-info", "children", allow_duplicate=True),
     Output("process-step-select", "options", allow_duplicate=True),
     Output("seed-train-id-select", "options", allow_duplicate=True)],
    [Input("add-vessels-edit-btn", "n_clicks")],
    [State("selected-experiment-id", "data")],
    prevent_initial_call=True
)
def open_add_vessels_modal(n_clicks, experiment_id):
    """Open modal to add vessels from edit tab"""
    if not n_clicks or not experiment_id:
        return dash.no_update

    try:
        experiment = USPExperiment.objects.get(id=experiment_id)

        # Get process steps for dropdown
        steps = experiment.process_steps.all().order_by('step_order')
        step_options = [
            {"label": f"Step {step.step_order}: {step.step_name} ({step.step_type})",
             "value": step.id}
            for step in steps
        ]

        # Get seed trains for dropdown (vessels that are seed trains)
        seed_trains = USPVessel.objects.filter(
            process_step__experiment=experiment,
            process_step__step_type='Seed_Train'
        )
        seed_train_options = [
            {"label": f"{v.vessel_id} ({v.vessel_type})", "value": v.id}
            for v in seed_trains
        ]

        return (
            True,  # Open modal
            experiment.id,  # Store the experiment ID
            f"Experiment: {experiment.experiment_id} - {experiment.experiment_name}",
            f"Adding vessels to {experiment.experiment_name}",
            step_options,
            seed_train_options if seed_train_options else [{"label": "No seed trains available", "value": None}]
        )
    except Exception as e:
        print(f"Error opening add vessels modal: {e}")
        return dash.no_update

# Callback for Add Step button in Edit tab
@app.callback(
    Output("add-step-modal", "is_open"),
    [Input("add-step-btn", "n_clicks"),
     Input("cancel-add-step", "n_clicks")],
    [State("add-step-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_add_step_modal(add_clicks, cancel_clicks, is_open):
    """Toggle the add step modal"""
    ctx = dash.callback_context
    if ctx.triggered:
        return not is_open
    return is_open

# Callback to save new process step
@app.callback(
    [Output("process-steps-edit-section", "children", allow_duplicate=True),
     Output("add-step-modal", "is_open", allow_duplicate=True)],
    [Input("save-new-step", "n_clicks")],
    [State("selected-experiment-id", "data"),
     State("new-step-name", "value"),
     State("new-step-type", "value"),
     State("new-step-start-date", "value"),
     State("new-step-duration", "value")],
    prevent_initial_call=True
)
def save_new_process_step(n_clicks, experiment_id, step_name, step_type, start_date, duration):
    """Save a new process step to the experiment"""
    if not n_clicks or not experiment_id or not step_name:
        return dash.no_update

    try:
        experiment = USPExperiment.objects.get(id=experiment_id)

        # Get next step order
        existing_steps = experiment.process_steps.all()
        next_order = existing_steps.count() + 1

        # Create the new step
        new_step = USPProcessStep.objects.create(
            experiment=experiment,
            step_name=step_name,
            step_type=step_type,
            step_order=next_order,
            planned_duration_days=duration or 7,
            planned_start_date=pd.to_datetime(start_date).date() if start_date else None,
            status="Pending"
        )

        print(f"[DEBUG] Created new step: {new_step.step_name} for experiment {experiment.experiment_id}")

        # Reload all steps for display
        steps = experiment.process_steps.all().order_by('step_order')
        steps_table = html.Table(
            className="table table-sm",
            children=[
                html.Thead([
                    html.Tr([
                        html.Th("Step Name"),
                        html.Th("Type"),
                        html.Th("Order"),
                        html.Th("Start Date"),
                        html.Th("Duration (days)"),
                        html.Th("Status"),
                        html.Th("Vessels"),
                        html.Th("Actions")
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(step.step_name),
                        html.Td(step.step_type.replace('_', ' ')),
                        html.Td(str(step.step_order)),
                        html.Td(step.planned_start_date.strftime('%Y-%m-%d') if step.planned_start_date else 'Not set'),
                        html.Td(str(step.planned_duration_days)),
                        html.Td(dbc.Badge(step.status, color="primary" if step.status == "Complete" else "warning")),
                        html.Td(str(step.vessels.count())),
                        html.Td([
                            dbc.ButtonGroup([
                                dbc.Button("Edit", id={'type': 'edit-step-btn', 'index': step.id}, size="sm", color="info", className="me-1"),
                                dbc.Button("Delete", id={'type': 'delete-step-btn', 'index': step.id}, size="sm", color="danger")
                            ], size="sm")
                        ])
                    ]) for step in steps
                ])
            ]
        )

        return steps_table, False  # Update table and close modal

    except Exception as e:
        print(f"Error saving new step: {e}")
        return dash.no_update

# Callback for opening process registration modal
@app.callback(
    [Output("process-modal", "is_open"),
     Output("selected-experiment-display", "children"),
     Output("selected-experiment-info", "children"),
     Output("process-step-select", "options"),
     Output("seed-train-id-select", "options")],
    [Input("register-process-btn", "n_clicks"),
     Input("cancel-process-modal", "n_clicks")],
    [State("process-modal", "is_open"),
     State("selected-experiment-data", "data")]
)
def handle_process_modal(register_clicks, cancel_clicks, is_open, selected_exp):
    """Open/close process registration modal and load experiment data"""
    ctx = dash.callback_context

    if not ctx.triggered:
        return is_open, "", "", [], []

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "register-process-btn" and selected_exp:
        try:
            # Get experiment and its steps
            experiment = USPExperiment.objects.get(id=selected_exp['id'])
            steps = experiment.process_steps.all()

            # Create step options
            step_options = [
                {
                    'label': f"{step.step_name} ({step.step_type.replace('_', ' ')}) - {step.status}",
                    'value': step.id
                }
                for step in steps
            ]

            # Get seed train options (only completed seed train steps)
            seed_train_steps = USPProcessStep.objects.filter(
                step_type='Seed_Train',
                status='Complete'
            ).select_related('experiment')

            seed_train_options = [
                {
                    'label': f"{st.experiment.experiment_id} - {st.step_name}",
                    'value': st.id
                }
                for st in seed_train_steps
            ]

            exp_display = f"{experiment.experiment_id} - {experiment.experiment_name}"
            exp_info = f"Status: {experiment.status} | Start: {experiment.start_date}"

            return True, exp_display, exp_info, step_options, seed_train_options

        except Exception as e:
            print(f"Error opening process modal: {e}")
            return False, "", "", [], []

    elif button_id == "cancel-process-modal":
        return False, "", "", [], []

    return is_open, "", "", [], []

# Callback to show/hide DasGip section based on vessel type
@app.callback(
    Output("dasgip-section", "style"),
    [Input("vessel-type-select", "value")]
)
def toggle_dasgip_section(vessel_type):
    """Show DasGip section only for bioreactors"""
    if vessel_type and '_BR' in vessel_type:
        return {'display': 'block'}
    return {'display': 'none'}

# Callback to generate vessel preview table
@app.callback(
    Output("vessel-preview-table", "data"),
    [Input("num-vessels-input", "value"),
     Input("vessel-type-select", "value"),
     Input("inoculation-date", "date"),
     Input("seed-density-input", "value"),
     Input("cell-line-input", "value")],
    [State("selected-experiment-data", "data")]
)
def update_vessel_preview(num_vessels, vessel_type, inoc_date, seed_density, cell_line, selected_exp):
    """Generate preview of vessels to be created"""
    if not num_vessels or num_vessels < 1 or not vessel_type:
        return []

    data = []
    exp_id = selected_exp['experiment_id'] if selected_exp else 'EXP'

    for i in range(int(num_vessels)):
        vessel_num = i + 1
        vessel_id = f"{exp_id}-{vessel_type.split('_')[0] if vessel_type else 'V'}-{vessel_num:02d}"

        data.append({
            'vessel_id': vessel_id,
            'vessel_type': vessel_type or "",
            'dasgip_unit': f"Unit {vessel_num}" if vessel_type and '_BR' in vessel_type else "",
            'inoculation_date': inoc_date,
            'seed_density': seed_density or 0,
            'cell_line': cell_line or "",
        })

    return data

# Callback to save process registration
@app.callback(
    Output("process-alert-container", "children"),
    [Input("save-process", "n_clicks")],
    [State("process-step-select", "value"),
     State("vessel-preview-table", "data"),
     State("seed-train-id-select", "value"),
     State("media-type-input", "value")],
    prevent_initial_call=True
)
def save_process_registration(save_clicks, step_id, vessels_data, seed_train_id, media_type):
    """Save vessel registration to database"""
    if not save_clicks or not step_id or not vessels_data:
        return []

    try:
        step = USPProcessStep.objects.get(id=step_id)
        print(f"[DEBUG] Saving {len(vessels_data)} vessels for step: {step.step_name}")

        # Create vessels
        for vessel_data in vessels_data:
            USPVessel.objects.create(
                process_step=step,
                vessel_id=vessel_data['vessel_id'],
                vessel_type=vessel_data['vessel_type'],
                inoculation_date=pd.to_datetime(vessel_data['inoculation_date']).date() if vessel_data['inoculation_date'] else None,
                inoculation_density=float(vessel_data['seed_density']) if vessel_data['seed_density'] else None,
                cell_line=vessel_data['cell_line'],
                media_type=media_type,
                notes=f"DasGip: {vessel_data.get('dasgip_unit', '')}" if vessel_data.get('dasgip_unit') else ""
            )

        # Update step status if needed
        if step.status == 'Pending':
            step.status = 'In Progress'
            step.actual_start_date = date.today()
            step.save()

        return dbc.Alert(
            f"Successfully registered {len(vessels_data)} vessels for {step.step_name}!",
            color="success",
            dismissable=True,
            duration=5000
        )

    except Exception as e:
        print(f"Error saving process registration: {e}")
        return dbc.Alert(
            f"Error registering vessels: {str(e)}",
            color="danger",
            dismissable=True,
            duration=5000
        )

# TEMPORARILY DISABLED - will fix after HTML table test
# Callback for handling experiment selection in management interface
# @app.callback(
#     [Output("experiment-details-section", "style"),
#      Output("process-steps-section", "style"),
#      Output("vessels-section", "style"),
#      Output("selected-exp-details", "children"),
#      Output("process-steps-table", "data"),
#      Output("vessels-table", "data"),
#      Output("edit-selected-experiment-btn", "disabled"),
#      Output("add-vessels-btn", "disabled"),
#      Output("view-details-btn", "disabled")],
#     [Input("manage-experiments-table", "selected_rows")],
#     [State("manage-experiments-table", "data")]
# )
def handle_experiment_selection_in_modal_disabled(selected_rows, table_data):
    """Handle experiment selection in manage experiments modal"""
    if not selected_rows or not table_data:
        return (
            {'display': 'none'}, {'display': 'none'}, {'display': 'none'},
            [], [], [],
            True, True, True
        )

    try:
        selected_exp_data = table_data[selected_rows[0]]
        experiment = USPExperiment.objects.get(id=selected_exp_data['id'])

        # Experiment details
        exp_details = [
            html.P([html.Strong("Experiment ID: "), experiment.experiment_id]),
            html.P([html.Strong("Name: "), experiment.experiment_name]),
            html.P([html.Strong("Status: "), experiment.status]),
            html.P([html.Strong("Start Date: "), experiment.start_date.strftime('%Y-%m-%d') if experiment.start_date else 'N/A']),
            html.P([html.Strong("Description: "), experiment.description or 'No description'])
        ]

        # Process steps data
        steps = experiment.process_steps.all()
        steps_data = []
        for step in steps:
            vessel_count = step.vessels.count()
            steps_data.append({
                'id': step.id,
                'step_name': step.step_name,
                'step_type': step.step_type.replace('_', ' '),
                'status': step.status,
                'planned_start_date': step.planned_start_date.strftime('%Y-%m-%d') if step.planned_start_date else 'N/A',
                'planned_duration_days': step.planned_duration_days,
                'vessel_count': vessel_count,
                'step_actions': '⚗️ Add Vessels'
            })

        # Vessels data
        vessels = USPVessel.objects.filter(process_step__experiment=experiment)
        vessels_data = []
        for vessel in vessels:
            vessels_data.append({
                'id': vessel.id,
                'vessel_id': vessel.vessel_id,
                'vessel_type': vessel.vessel_type,
                'process_step': vessel.process_step.step_name,
                'inoculation_date': vessel.inoculation_date.strftime('%Y-%m-%d') if vessel.inoculation_date else 'N/A',
                'cell_line': vessel.cell_line or 'N/A',
                'vessel_status': 'Active' if vessel.inoculation_date else 'Planned',
                'vessel_actions': '📝 Edit'
            })

        return (
            {'display': 'block'}, {'display': 'block'}, {'display': 'block'},
            exp_details, steps_data, vessels_data,
            False, False, False
        )

    except Exception as e:
        print(f"Error handling experiment selection: {e}")
        return (
            {'display': 'none'}, {'display': 'none'}, {'display': 'none'},
            [], [], [],
            True, True, True
        )

# Link Add Vessels button to process registration modal
@app.callback(
    [Output("process-modal", "is_open", allow_duplicate=True),
     Output("selected-experiment-display", "children", allow_duplicate=True),
     Output("selected-experiment-info", "children", allow_duplicate=True),
     Output("process-step-select", "options", allow_duplicate=True),
     Output("seed-train-id-select", "options", allow_duplicate=True)],
    [Input("add-vessels-btn", "n_clicks")],
    [State("manage-experiments-table", "selected_rows"),
     State("manage-experiments-table", "data")],
    prevent_initial_call=True
)
def open_process_modal_from_manage(add_clicks, selected_rows, table_data):
    """Open process registration modal from manage experiments"""
    if not add_clicks or not selected_rows or not table_data:
        return False, "", "", [], []

    try:
        selected_exp_data = table_data[selected_rows[0]]
        experiment = USPExperiment.objects.get(id=selected_exp_data['id'])
        steps = experiment.process_steps.all()

        # Create step options
        step_options = [
            {
                'label': f"{step.step_name} ({step.step_type.replace('_', ' ')}) - {step.status}",
                'value': step.id
            }
            for step in steps
        ]

        # Get seed train options
        seed_train_steps = USPProcessStep.objects.filter(
            step_type='Seed_Train',
            status='Complete'
        ).select_related('experiment')

        seed_train_options = [
            {
                'label': f"{st.experiment.experiment_id} - {st.step_name}",
                'value': st.id
            }
            for st in seed_train_steps
        ]

        exp_display = f"{experiment.experiment_id} - {experiment.experiment_name}"
        exp_info = f"Status: {experiment.status} | Start: {experiment.start_date}"

        return True, exp_display, exp_info, step_options, seed_train_options

    except Exception as e:
        print(f"Error opening process modal from manage: {e}")
        return False, "", "", [], []

# REMOVED: Callback to load experiment when selected from dropdown - now handled by Edit button click
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, False, ""

    button_id = eval(ctx.triggered[0]['prop_id'].split('.')[0])
    step_id = button_id['index']

    try:
        step = USPProcessStep.objects.get(id=step_id)
        step_name = step.step_name
        step.delete()

        # Reload steps
        experiment = USPExperiment.objects.get(id=experiment_id)
        steps = experiment.process_steps.all().order_by('step_order')

        steps_table = html.Table(
            className="table table-sm",
            children=[
                html.Thead([
                    html.Tr([
                        html.Th("Step Name"),
                        html.Th("Type"),
                        html.Th("Order"),
                        html.Th("Start Date"),
                        html.Th("Duration (days)"),
                        html.Th("Status"),
                        html.Th("Vessels"),
                        html.Th("Actions")
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(step.step_name),
                        html.Td(step.step_type.replace('_', ' ')),
                        html.Td(str(step.step_order)),
                        html.Td(step.planned_start_date.strftime('%Y-%m-%d') if step.planned_start_date else 'Not set'),
                        html.Td(str(step.planned_duration_days)),
                        html.Td(dbc.Badge(step.status, color="primary" if step.status == "Complete" else "warning")),
                        html.Td(str(step.vessels.count())),
                        html.Td([
                            dbc.ButtonGroup([
                                dbc.Button("Edit", id={'type': 'edit-step-btn', 'index': step.id}, size="sm", color="info", className="me-1"),
                                dbc.Button("Delete", id={'type': 'delete-step-btn', 'index': step.id}, size="sm", color="danger")
                            ], size="sm")
                        ])
                    ]) for step in steps
                ])
            ]
        ) if steps.exists() else html.P("No process steps added yet", className="text-muted")

        return steps_table, True, f"Successfully deleted step: {step_name}"

    except Exception as e:
        print(f"Error deleting step: {e}")
        return dash.no_update, True, f"Error deleting step: {str(e)}"

# ============================================================================
# NEW CALLBACKS FOR REDESIGNED MANAGE EXPERIMENTS MODAL
# ============================================================================

# Callback to save inline edits to Experiments table
@app.callback(
    Output("experiments-datatable", "data", allow_duplicate=True),
    [Input("experiments-datatable", "data_timestamp")],
    [State("experiments-datatable", "data"),
     State("experiments-datatable", "data_previous")],
    prevent_initial_call=True
)
def save_experiments_edits(timestamp, current_data, previous_data):
    """Save inline edits made to experiments table"""
    if not timestamp or not current_data or not previous_data:
        raise PreventUpdate

    try:
        # Find which rows changed
        for i, (current_row, prev_row) in enumerate(zip(current_data, previous_data)):
            if current_row != prev_row:
                exp_id = current_row['experiment_id']
                experiment = USPExperiment.objects.get(experiment_id=exp_id)

                # Update fields that changed
                if current_row.get('project_id') != prev_row.get('project_id'):
                    experiment.project_id = current_row['project_id'] or None
                if current_row.get('experiment_name') != prev_row.get('experiment_name'):
                    experiment.experiment_name = current_row['experiment_name']
                if current_row.get('status') != prev_row.get('status'):
                    experiment.status = current_row['status']
                if current_row.get('start_date') != prev_row.get('start_date'):
                    experiment.start_date = pd.to_datetime(current_row['start_date']).date()
                if current_row.get('target_end_date') != prev_row.get('target_end_date'):
                    experiment.target_end_date = pd.to_datetime(current_row['target_end_date']).date() if current_row['target_end_date'] else None

                experiment.save()
                print(f"Updated experiment: {exp_id}")

        return current_data
    except Exception as e:
        print(f"Error saving experiments edits: {e}")
        import traceback
        traceback.print_exc()
        return previous_data or current_data

# Callback to save inline edits to Seed Trains table
@app.callback(
    Output("seedtrains-datatable", "data", allow_duplicate=True),
    [Input("seedtrains-datatable", "data_timestamp")],
    [State("seedtrains-datatable", "data"),
     State("seedtrains-datatable", "data_previous")],
    prevent_initial_call=True
)
def save_seedtrains_edits(timestamp, current_data, previous_data):
    """Save inline edits made to seed trains table"""
    if not timestamp or not current_data or not previous_data:
        raise PreventUpdate

    try:
        for i, (current_row, prev_row) in enumerate(zip(current_data, previous_data)):
            if current_row != prev_row:
                st_id = current_row['seed_train_id']
                seed_train = USPSeedTrain.objects.get(seed_train_id=st_id)

                # Update fields
                if current_row.get('cell_line') != prev_row.get('cell_line'):
                    seed_train.cell_line = current_row['cell_line']
                if current_row.get('thaw_date') != prev_row.get('thaw_date'):
                    seed_train.thaw_date = pd.to_datetime(current_row['thaw_date']).date()
                if current_row.get('bank_age') != prev_row.get('bank_age'):
                    seed_train.bank_age = current_row['bank_age']
                if current_row.get('pool_or_clone') != prev_row.get('pool_or_clone'):
                    seed_train.pool_or_clone = current_row['pool_or_clone']
                if current_row.get('program') != prev_row.get('program'):
                    seed_train.program = current_row['program']
                if current_row.get('clone') != prev_row.get('clone'):
                    seed_train.clone = current_row['clone']
                if current_row.get('media_type') != prev_row.get('media_type'):
                    seed_train.media_type = current_row['media_type']
                if current_row.get('media_lot') != prev_row.get('media_lot'):
                    seed_train.media_lot = current_row['media_lot']
                if current_row.get('is_discarded') != prev_row.get('is_discarded'):
                    is_discarded = current_row['is_discarded'] == 'True'
                    seed_train.is_discarded = is_discarded
                    if is_discarded and not seed_train.discard_date:
                        seed_train.discard_date = datetime.now()

                seed_train.save()
                print(f"Updated seed train: {st_id}")

        return current_data
    except Exception as e:
        print(f"Error saving seed trains edits: {e}")
        import traceback
        traceback.print_exc()
        return previous_data or current_data

# Callback to save inline edits to Vessels table
@app.callback(
    Output("vessels-datatable", "data", allow_duplicate=True),
    [Input("vessels-datatable", "data_timestamp")],
    [State("vessels-datatable", "data"),
     State("vessels-datatable", "data_previous")],
    prevent_initial_call=True
)
def save_vessels_edits(timestamp, current_data, previous_data):
    """Save inline edits made to vessels table"""
    if not timestamp or not current_data or not previous_data:
        raise PreventUpdate

    try:
        for i, (current_row, prev_row) in enumerate(zip(current_data, previous_data)):
            if current_row != prev_row:
                v_id = current_row['vessel_id']
                vessel = USPVessel.objects.get(vessel_id=v_id)

                # Update fields
                if current_row.get('cell_line') != prev_row.get('cell_line'):
                    vessel.cell_line = current_row['cell_line']
                if current_row.get('inoculation_date') != prev_row.get('inoculation_date'):
                    vessel.inoculation_date = pd.to_datetime(current_row['inoculation_date']).date() if current_row['inoculation_date'] else None
                if current_row.get('inoculation_density') != prev_row.get('inoculation_density'):
                    vessel.inoculation_density = float(current_row['inoculation_density']) if current_row['inoculation_density'] else None
                if current_row.get('pool_or_clone') != prev_row.get('pool_or_clone'):
                    vessel.pool_or_clone = current_row['pool_or_clone']
                if current_row.get('program') != prev_row.get('program'):
                    vessel.program = current_row['program']
                if current_row.get('clone') != prev_row.get('clone'):
                    vessel.clone = current_row['clone']
                if current_row.get('media_type') != prev_row.get('media_type'):
                    vessel.media_type = current_row['media_type']
                if current_row.get('feeding_strategy') != prev_row.get('feeding_strategy'):
                    vessel.feeding_strategy = current_row['feeding_strategy']
                if current_row.get('vessel_type') != prev_row.get('vessel_type'):
                    vessel.vessel_type = current_row['vessel_type']
                if current_row.get('start_volume') != prev_row.get('start_volume'):
                    vessel.start_volume = float(current_row['start_volume']) if current_row['start_volume'] else None
                if current_row.get('vessel_size') != prev_row.get('vessel_size'):
                    vessel.vessel_size = current_row['vessel_size']
                if current_row.get('status') != prev_row.get('status'):
                    vessel.status = current_row['status']
                    if vessel.status == 'Archived' and not vessel.is_archived:
                        vessel.is_archived = True
                        vessel.archive_date = datetime.now()

                vessel.save()
                print(f"Updated vessel: {v_id}")

        return current_data
    except Exception as e:
        print(f"Error saving vessels edits: {e}")
        import traceback
        traceback.print_exc()
        return previous_data or current_data

# Callback for Excel export - Experiments
@app.callback(
    Output("experiment-search", "value", allow_duplicate=True),  # Dummy output
    [Input("export-experiments-btn", "n_clicks")],
    [State("experiments-datatable", "data")],
    prevent_initial_call=True
)
def export_experiments_to_excel(n_clicks, data):
    """Export experiments table to Excel"""
    if not n_clicks or not data:
        raise PreventUpdate

    try:
        df = pd.DataFrame(data)
        filename = f"USP_Experiments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = f"C:\\Users\\cdallarosa\\DataAlchemy\\djangoProject\\{filename}"
        df.to_excel(filepath, index=False, sheet_name='Experiments')
        print(f"Exported experiments to {filepath}")
        return ""
    except Exception as e:
        print(f"Error exporting experiments: {e}")
        import traceback
        traceback.print_exc()
        raise PreventUpdate

# Callback for Excel export - Seed Trains
@app.callback(
    Output("experiment-search", "value", allow_duplicate=True),  # Dummy output
    [Input("export-seedtrains-btn", "n_clicks")],
    [State("seedtrains-datatable", "data")],
    prevent_initial_call=True
)
def export_seedtrains_to_excel(n_clicks, data):
    """Export seed trains table to Excel"""
    if not n_clicks or not data:
        raise PreventUpdate

    try:
        df = pd.DataFrame(data)
        filename = f"USP_SeedTrains_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = f"C:\\Users\\cdallarosa\\DataAlchemy\\djangoProject\\{filename}"
        df.to_excel(filepath, index=False, sheet_name='Seed Trains')
        print(f"Exported seed trains to {filepath}")
        return ""
    except Exception as e:
        print(f"Error exporting seed trains: {e}")
        import traceback
        traceback.print_exc()
        raise PreventUpdate

# Callback for Excel export - Vessels
@app.callback(
    Output("experiment-search", "value", allow_duplicate=True),  # Dummy output
    [Input("export-vessels-btn", "n_clicks")],
    [State("vessels-datatable", "data")],
    prevent_initial_call=True
)
def export_vessels_to_excel(n_clicks, data):
    """Export vessels table to Excel"""
    if not n_clicks or not data:
        raise PreventUpdate

    try:
        df = pd.DataFrame(data)
        filename = f"USP_Vessels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = f"C:\\Users\\cdallarosa\\DataAlchemy\\djangoProject\\{filename}"
        df.to_excel(filepath, index=False, sheet_name='Fed Batch')
        print(f"Exported vessels to {filepath}")
        return ""
    except Exception as e:
        print(f"Error exporting vessels: {e}")
        import traceback
        traceback.print_exc()
        raise PreventUpdate

# Callback for bulk discard seed trains
@app.callback(
    Output("seedtrains-datatable", "data", allow_duplicate=True),
    [Input("bulk-discard-seedtrains-btn", "n_clicks")],
    [State("seedtrains-datatable", "data"),
     State("seedtrains-datatable", "selected_rows")],
    prevent_initial_call=True
)
def bulk_discard_seedtrains(n_clicks, data, selected_rows):
    """Bulk discard selected seed trains"""
    if not n_clicks or not selected_rows:
        raise PreventUpdate

    try:
        for row_idx in selected_rows:
            st_id = data[row_idx]['seed_train_id']
            seed_train = USPSeedTrain.objects.get(seed_train_id=st_id)
            seed_train.is_discarded = True
            seed_train.discard_date = datetime.now()
            seed_train.discard_reason = "Bulk discard action"
            seed_train.save()

            # Update data
            data[row_idx]['is_discarded'] = 'True'

        print(f"Bulk discarded {len(selected_rows)} seed trains")
        return data
    except Exception as e:
        print(f"Error bulk discarding seed trains: {e}")
        import traceback
        traceback.print_exc()
        raise PreventUpdate

# Callback for bulk archive vessels
@app.callback(
    Output("vessels-datatable", "data", allow_duplicate=True),
    [Input("bulk-archive-vessels-btn", "n_clicks")],
    [State("vessels-datatable", "data"),
     State("vessels-datatable", "selected_rows")],
    prevent_initial_call=True
)
def bulk_archive_vessels(n_clicks, data, selected_rows):
    """Bulk archive selected vessels"""
    if not n_clicks or not selected_rows:
        raise PreventUpdate

    try:
        for row_idx in selected_rows:
            v_id = data[row_idx]['vessel_id']
            vessel = USPVessel.objects.get(vessel_id=v_id)
            vessel.is_archived = True
            vessel.archive_date = datetime.now()
            vessel.archive_reason = "Bulk archive action"
            vessel.status = "Archived"
            vessel.save()

            # Update data
            data[row_idx]['status'] = 'Archived'

        print(f"Bulk archived {len(selected_rows)} vessels")
        return data
    except Exception as e:
        print(f"Error bulk archiving vessels: {e}")
        import traceback
        traceback.print_exc()
        raise PreventUpdate

# ============================================================================
# REGISTRATION MODAL CALLBACKS
# ============================================================================

# Callback to open seed train registration modal
@app.callback(
    [Output("register-seedtrain-modal", "is_open"),
     Output("seedtrain-experiment-select", "options")],
    [Input("register-seedtrain-btn", "n_clicks"),
     Input("cancel-seedtrain-modal", "n_clicks")],
    [State("register-seedtrain-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_seedtrain_modal(register_clicks, cancel_clicks, is_open):
    """Open/close seed train registration modal and load dropdowns"""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "register-seedtrain-btn":
        # Load experiments
        experiments = USPExperiment.objects.all().order_by('-created_date')
        exp_options = [
            {'label': f"{exp.experiment_id} - {exp.experiment_name}", 'value': exp.id}
            for exp in experiments
        ]

        return True, exp_options

    return False, []

# Callback to load process steps when experiment is selected (seed train modal)
@app.callback(
    Output("seedtrain-step-select", "options"),
    [Input("seedtrain-experiment-select", "value")],
    prevent_initial_call=True
)
def load_seedtrain_steps(experiment_id):
    """Load seed train process steps for selected experiment"""
    if not experiment_id:
        return []

    try:
        steps = USPProcessStep.objects.filter(
            experiment_id=experiment_id,
            step_type='Seed_Train'
        ).order_by('step_order')

        return [
            {'label': f"{step.step_name} (Order {step.step_order})", 'value': step.id}
            for step in steps
        ]
    except Exception as e:
        print(f"Error loading seed train steps: {e}")
        return []

# Callback to populate store when experiment selected or add row button clicked
@app.callback(
    [Output("seedtrain-table-data", "data"),
     Output("seedtrain-row-counter", "data")],
    [Input("seedtrain-experiment-select", "value"),
     Input("add-seedtrain-row-btn", "n_clicks")],
    [State("seedtrain-table-data", "data"),
     State("seedtrain-row-counter", "data")],
    prevent_initial_call=True
)
def update_seedtrain_table_data(experiment_id, add_clicks, current_data, row_counter):
    """Populate store with existing seed trains or add blank row"""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if not experiment_id:
        return [], 0

    try:
        # When experiment is selected, load all existing seed trains into store
        if triggered_id == "seedtrain-experiment-select":
            experiment = USPExperiment.objects.get(id=experiment_id)
            seed_trains = USPSeedTrain.objects.filter(
                process_step__experiment=experiment
            ).select_related('process_step', 'media_prep').order_by('seed_train_id')

            table_data = []
            for st in seed_trains:
                table_data.append({
                    'db_id': st.id,  # Has DB ID = existing record
                    'seed_train_id': st.seed_train_id,
                    'cell_line': st.cell_line or '',
                    'clone': st.clone or '',
                    'pool_or_clone': st.pool_or_clone or '',
                    'bank_age': st.bank_age or '',
                    'passage_number': st.passage_number if st.passage_number is not None else '',
                    'vessel_type': st.vessel_type or '',
                    'start_volume': st.start_volume if st.start_volume is not None else '',
                    'thaw_date': st.thaw_date.isoformat() if st.thaw_date else '',
                    'media_prep_id': st.media_prep.id if st.media_prep else '',
                    'notes': st.notes or '',
                    'is_discarded': st.is_discarded
                })

            return table_data, len(table_data)

        # When "Add Seed Train" clicked, append blank row to store
        elif triggered_id == "add-seedtrain-row-btn":
            new_row = {
                'db_id': None,  # No DB ID = new record
                'seed_train_id': 'NEW',
                'cell_line': '',
                'clone': '',
                'pool_or_clone': '',
                'bank_age': '',
                'passage_number': '',
                'vessel_type': '',
                'start_volume': '',
                'thaw_date': '',
                'media_prep_id': '',
                'notes': '',
                'is_discarded': False
            }
            updated_data = current_data + [new_row] if current_data else [new_row]
            return updated_data, row_counter + 1

        return current_data, row_counter

    except Exception as e:
        print(f"Error updating seed train table data: {e}")
        import traceback
        traceback.print_exc()
        return current_data or [], row_counter

# Callback to render table from store
@app.callback(
    Output("unified-seedtrains-table", "children"),
    [Input("seedtrain-table-data", "data")],
    prevent_initial_call=True
)
def render_seedtrain_table_from_store(table_data):
    """Render HTML table from store data"""
    if not table_data:
        return html.P("Select an experiment above to load existing seed trains, or click 'Add Seed Train' to add new rows",
                     className="text-muted text-center")

    try:
        # Get all seed trains for this experiment
        experiment = USPExperiment.objects.get(id=experiment_id)
        seed_trains = USPSeedTrain.objects.filter(
            process_step__experiment=experiment
        ).select_related('process_step', 'media_prep').order_by('seed_train_id')

        if not seed_trains.exists():
            return html.P(f"No existing seed trains found for {experiment.experiment_id}",
                         className="text-muted text-center")

        # Get media prep options for dropdowns
        media_preps = USPMediaPrep.objects.all().order_by('-preparation_date')
        media_options = [
            {'label': f"{mp.media_id} - {mp.media_name}", 'value': mp.id}
            for mp in media_preps
        ]

        vessel_type_options = [
            {'label': 'T25 Flask', 'value': 'T25'},
            {'label': 'T75 Flask', 'value': 'T75'},
            {'label': 'T175 Flask', 'value': 'T175'},
            {'label': 'T225 Flask', 'value': 'T225'},
            {'label': '125mL SF', 'value': '125mL_SF'},
            {'label': '250mL SF', 'value': '250mL_SF'},
            {'label': '500mL SF', 'value': '500mL_SF'},
        ]

        pool_clone_options = [
            {'label': 'Pool', 'value': 'Pool'},
            {'label': 'Clone', 'value': 'Clone'},
        ]

        # Build table header (same as new seed trains)
        table_header = html.Thead(html.Tr([
            html.Th("Seed Train ID", style={'min-width': '120px'}),
            html.Th("Cell Line *", style={'min-width': '150px'}),
            html.Th("Clone", style={'min-width': '100px'}),
            html.Th("Pool/Clone", style={'min-width': '120px'}),
            html.Th("Bank Age", style={'min-width': '100px'}),
            html.Th("Passage #", style={'min-width': '100px'}),
            html.Th("Vessel Type *", style={'min-width': '150px'}),
            html.Th("Volume (mL)", style={'min-width': '120px'}),
            html.Th("Thaw Date *", style={'min-width': '150px'}),
            html.Th("Media Prep", style={'min-width': '200px'}),
            html.Th("Notes", style={'min-width': '200px'}),
        ]))

        # Create table rows with existing data
        table_rows = []
        for idx, st in enumerate(seed_trains):
            row = html.Tr([
                # Seed Train ID (display only, store actual ID in hidden div)
                html.Td([
                    st.seed_train_id,
                    html.Div(st.id, id={'type': 'existing-st-pk', 'index': idx}, style={'display': 'none'})
                ], id={'type': 'existing-st-id', 'index': idx}),

                # Cell Line
                html.Td(dbc.Input(
                    id={'type': 'existing-st-cell-line', 'index': idx},
                    type='text',
                    value=st.cell_line or '',
                    placeholder='CHO-K1, CHO-S, etc',
                    size='sm'
                )),

                # Clone
                html.Td(dbc.Input(
                    id={'type': 'existing-st-clone', 'index': idx},
                    type='text',
                    value=st.clone or '',
                    placeholder='1B2, 25H8, etc',
                    size='sm'
                )),

                # Pool/Clone
                html.Td(dcc.Dropdown(
                    id={'type': 'existing-st-pool-clone', 'index': idx},
                    options=pool_clone_options,
                    value=st.pool_or_clone or None,
                    placeholder='Select...',
                    style={'width': '100%'}
                )),

                # Bank Age
                html.Td(dbc.Input(
                    id={'type': 'existing-st-bank-age', 'index': idx},
                    type='text',
                    value=st.bank_age or '',
                    placeholder='P4, P5, etc',
                    size='sm'
                )),

                # Passage Number
                html.Td(dbc.Input(
                    id={'type': 'existing-st-passage', 'index': idx},
                    type='number',
                    value=st.passage_number or '',
                    placeholder='#',
                    size='sm'
                )),

                # Vessel Type
                html.Td(dcc.Dropdown(
                    id={'type': 'existing-st-vessel-type', 'index': idx},
                    options=vessel_type_options,
                    value=st.vessel_type or None,
                    placeholder='Select...',
                    style={'width': '100%'}
                )),

                # Volume
                html.Td(dbc.Input(
                    id={'type': 'existing-st-volume', 'index': idx},
                    type='number',
                    value=st.start_volume or '',
                    placeholder='mL',
                    size='sm'
                )),

                # Thaw Date
                html.Td(dcc.DatePickerSingle(
                    id={'type': 'existing-st-thaw-date', 'index': idx},
                    date=st.thaw_date if st.thaw_date else None,
                    display_format='YYYY-MM-DD',
                    style={'width': '100%'}
                )),

                # Media Prep
                html.Td(dcc.Dropdown(
                    id={'type': 'existing-st-media-prep', 'index': idx},
                    options=media_options,
                    value=st.media_prep.id if st.media_prep else None,
                    placeholder='Select media prep...',
                    style={'width': '100%'}
                )),

                # Notes
                html.Td(dbc.Input(
                    id={'type': 'existing-st-notes', 'index': idx},
                    type='text',
                    value=st.notes or '',
                    placeholder='Notes',
                    size='sm'
                )),
            ])
            table_rows.append(row)

        table_body = html.Tbody(table_rows)

        table = dbc.Table(
            [table_header, table_body],
            bordered=True,
            hover=True,
            responsive=True,
            striped=True,
            size='sm',
            style={'fontSize': '0.9rem'}
        )

        return html.Div([
            dbc.Alert(f"Found {len(seed_trains)} existing seed train(s). Edit fields below and click 'Save Edits to Existing'",
                     color="info", className="mb-3"),
            table
        ])

    except Exception as e:
        print(f"Error loading existing seed trains: {e}")
        import traceback
        traceback.print_exc()
        return html.Div([
            dbc.Alert(f"Error loading existing seed trains: {str(e)}", color="danger")
        ])

# Callback to generate preview table for seed trains
@app.callback(
    [Output("seedtrain-preview-table", "children"),
     Output("seedtrain-media-prep-options", "data")],
    [Input("generate-seedtrain-table-btn", "n_clicks")],
    [State("seedtrain-count", "value"),
     State("seedtrain-experiment-select", "value")],
    prevent_initial_call=True
)
def generate_seedtrain_preview_table(n_clicks, count, experiment_id):
    """Generate editable table with rows for each seed train"""
    if not n_clicks or not count or count < 1:
        raise PreventUpdate

    try:
        # Get media prep options (all media preps, not filtered)
        media_preps = USPMediaPrep.objects.all().order_by('-preparation_date')
        media_options = [
            {'label': f"{mp.media_id} - {mp.media_name}", 'value': mp.id}
            for mp in media_preps
        ]

        # Generate seed train IDs
        seed_train_ids = []
        for i in range(count):
            try:
                last_seed_train = USPSeedTrain.objects.filter(
                    seed_train_id__startswith='UPST'
                ).order_by('-seed_train_id').first()

                if last_seed_train:
                    last_number = int(last_seed_train.seed_train_id[4:])
                    next_number = last_number + 1 + i
                else:
                    next_number = 1 + i

                seed_train_ids.append(f"UPST{next_number:04d}")
            except:
                seed_train_ids.append(f"UPST{i+1:04d}")

        # Build table with editable inputs
        table_header = html.Thead(html.Tr([
            html.Th("Seed Train ID", style={'min-width': '120px'}),
            html.Th("Cell Line *", style={'min-width': '150px'}),
            html.Th("Clone", style={'min-width': '100px'}),
            html.Th("Pool/Clone", style={'min-width': '120px'}),
            html.Th("Bank Age", style={'min-width': '100px'}),
            html.Th("Passage #", style={'min-width': '100px'}),
            html.Th("Vessel Type *", style={'min-width': '150px'}),
            html.Th("Volume (mL)", style={'min-width': '120px'}),
            html.Th("Thaw Date *", style={'min-width': '150px'}),
            html.Th("Media Prep", style={'min-width': '200px'}),
            html.Th("Notes", style={'min-width': '200px'}),
        ]))

        vessel_type_options = [
            {'label': 'T25 Flask', 'value': 'T25'},
            {'label': 'T75 Flask', 'value': 'T75'},
            {'label': 'T175 Flask', 'value': 'T175'},
            {'label': 'T225 Flask', 'value': 'T225'},
            {'label': '125mL SF', 'value': '125mL_SF'},
            {'label': '250mL SF', 'value': '250mL_SF'},
            {'label': '500mL SF', 'value': '500mL_SF'},
        ]

        pool_clone_options = [
            {'label': 'Pool', 'value': 'Pool'},
            {'label': 'Clone', 'value': 'Clone'},
        ]

        # Create table rows
        table_rows = []
        for idx, seed_train_id in enumerate(seed_train_ids):
            row = html.Tr([
                # Seed Train ID (display only)
                html.Td(seed_train_id, id={'type': 'st-id', 'index': idx}),

                # Cell Line
                html.Td(dbc.Input(
                    id={'type': 'st-cell-line', 'index': idx},
                    type='text',
                    placeholder='CHO-K1, CHO-S, etc',
                    size='sm'
                )),

                # Clone
                html.Td(dbc.Input(
                    id={'type': 'st-clone', 'index': idx},
                    type='text',
                    placeholder='1B2, 25H8, etc',
                    size='sm'
                )),

                # Pool/Clone
                html.Td(dcc.Dropdown(
                    id={'type': 'st-pool-clone', 'index': idx},
                    options=pool_clone_options,
                    placeholder='Select...',
                    style={'width': '100%'}
                )),

                # Bank Age
                html.Td(dbc.Input(
                    id={'type': 'st-bank-age', 'index': idx},
                    type='text',
                    placeholder='P4, P5, etc',
                    size='sm'
                )),

                # Passage Number
                html.Td(dbc.Input(
                    id={'type': 'st-passage', 'index': idx},
                    type='number',
                    placeholder='#',
                    size='sm'
                )),

                # Vessel Type
                html.Td(dcc.Dropdown(
                    id={'type': 'st-vessel-type', 'index': idx},
                    options=vessel_type_options,
                    placeholder='Select...',
                    style={'width': '100%'}
                )),

                # Volume
                html.Td(dbc.Input(
                    id={'type': 'st-volume', 'index': idx},
                    type='number',
                    placeholder='mL',
                    size='sm'
                )),

                # Thaw Date
                html.Td(dcc.DatePickerSingle(
                    id={'type': 'st-thaw-date', 'index': idx},
                    date=date.today(),
                    display_format='YYYY-MM-DD',
                    style={'width': '100%'}
                )),

                # Media Prep
                html.Td(dcc.Dropdown(
                    id={'type': 'st-media-prep', 'index': idx},
                    options=media_options,
                    placeholder='Select media prep...',
                    style={'width': '100%'}
                )),

                # Notes
                html.Td(dbc.Input(
                    id={'type': 'st-notes', 'index': idx},
                    type='text',
                    placeholder='Notes',
                    size='sm'
                )),
            ])
            table_rows.append(row)

        table_body = html.Tbody(table_rows)

        table = dbc.Table(
            [table_header, table_body],
            bordered=True,
            hover=True,
            responsive=True,
            striped=True,
            size='sm',
            style={'fontSize': '0.9rem'}
        )

        return html.Div([
            dbc.Alert("Fill in the required fields (*) for each seed train below, then click 'Register All'",
                     color="info", className="mb-3"),
            table
        ]), media_options

    except Exception as e:
        print(f"Error generating seed train preview table: {e}")
        import traceback
        traceback.print_exc()
        return html.Div([
            dbc.Alert(f"Error generating table: {str(e)}", color="danger")
        ]), []

# Callback to save new seed trains from preview table
@app.callback(
    [Output("seedtrains-datatable", "data", allow_duplicate=True),
     Output("register-seedtrain-modal", "is_open", allow_duplicate=True),
     Output("alert-container", "children", allow_duplicate=True)],
    [Input("save-seedtrain", "n_clicks")],
    [State("seedtrain-experiment-select", "value"),
     State("seedtrain-step-select", "value"),
     State("seedtrain-project", "value"),
     State("seedtrain-count", "value"),
     State({'type': 'st-id', 'index': ALL}, 'children'),
     State({'type': 'st-cell-line', 'index': ALL}, 'value'),
     State({'type': 'st-clone', 'index': ALL}, 'value'),
     State({'type': 'st-pool-clone', 'index': ALL}, 'value'),
     State({'type': 'st-bank-age', 'index': ALL}, 'value'),
     State({'type': 'st-passage', 'index': ALL}, 'value'),
     State({'type': 'st-vessel-type', 'index': ALL}, 'value'),
     State({'type': 'st-volume', 'index': ALL}, 'value'),
     State({'type': 'st-thaw-date', 'index': ALL}, 'date'),
     State({'type': 'st-media-prep', 'index': ALL}, 'value'),
     State({'type': 'st-notes', 'index': ALL}, 'value'),
     State("seedtrains-datatable", "data")],
    prevent_initial_call=True
)
def save_seed_trains(n_clicks, exp_id, step_id, project, count, seed_train_ids, cell_lines, clones, pool_clones,
                     bank_ages, passages, vessel_types, volumes, thaw_dates, media_prep_ids,
                     notes_list, current_data):
    """Create new seed trains from preview table data"""
    if not n_clicks:
        raise PreventUpdate

    # Validation
    if not exp_id or not step_id:
        return no_update, no_update, dbc.Alert("Please select experiment and process step", color="danger", duration=3000)

    if not seed_train_ids or len(seed_train_ids) == 0:
        return no_update, no_update, dbc.Alert("Please generate the preview table first", color="danger", duration=3000)

    try:
        # Validate that all required fields are filled for each row
        for i in range(len(seed_train_ids)):
            if not thaw_dates[i] or not cell_lines[i] or not vessel_types[i]:
                return no_update, no_update, dbc.Alert(
                    f"Row {i+1}: Please fill in all required fields (Thaw Date, Cell Line, Vessel Type)",
                    color="danger",
                    duration=5000
                )

        # Create seed trains
        created_seed_trains = []
        for i in range(len(seed_train_ids)):
            # Get media prep if selected
            media_prep = None
            media_type = ""
            media_lot = ""
            if media_prep_ids[i]:
                try:
                    media_prep = USPMediaPrep.objects.get(id=media_prep_ids[i])
                    media_type = media_prep.media_name
                    media_lot = media_prep.lot_number if hasattr(media_prep, 'lot_number') else ""
                except:
                    pass

            seed_train = USPSeedTrain.objects.create(
                process_step_id=step_id,
                seed_train_id=seed_train_ids[i],
                vessel_type=vessel_types[i],
                thaw_date=pd.to_datetime(thaw_dates[i]).date(),
                start_volume=float(volumes[i]) if volumes[i] else None,
                cell_line=cell_lines[i],
                media_type=media_type,
                media_prep=media_prep,
                passage_number=int(passages[i]) if passages[i] else None,
                bank_age=bank_ages[i] or "",
                pool_or_clone=pool_clones[i] or "",
                program=project or "",  # Project field from top of modal
                clone=clones[i] or "",
                media_lot=media_lot,
                notes=notes_list[i] or ""
            )
            created_seed_trains.append(seed_train)

        # Refresh datatable
        experiment = USPExperiment.objects.get(id=exp_id)
        seed_trains = USPSeedTrain.objects.select_related('process_step__experiment').filter(
            process_step__experiment=experiment
        )

        new_data = []
        for st in seed_trains:
            new_data.append({
                'experiment_id': st.process_step.experiment.experiment_id,
                'seed_train_id': st.seed_train_id,
                'cell_line': st.cell_line or '',
                'thaw_date': st.thaw_date.strftime('%Y-%m-%d') if st.thaw_date else '',
                'bank_age': st.bank_age or '',
                'pool_or_clone': st.pool_or_clone or '',
                'program': st.program or '',
                'clone': st.clone or '',
                'media_type': st.media_type or '',
                'media_lot': st.media_lot or '',
                'is_discarded': 'True' if st.is_discarded else 'False',
            })

        # Merge with other experiments' data
        other_exps_data = [row for row in current_data if row['experiment_id'] != experiment.experiment_id]
        final_data = other_exps_data + new_data

        alert = dbc.Alert(
            f"Successfully created {len(created_seed_trains)} seed train(s)!",
            color="success",
            duration=3000
        )

        return final_data, False, alert

    except Exception as e:
        print(f"Error creating seed trains: {e}")
        import traceback
        traceback.print_exc()
        alert = dbc.Alert(f"Error: {str(e)}", color="danger", duration=5000)
        return no_update, no_update, alert

# Callback to save edits to existing seed trains
@app.callback(
    [Output("seedtrains-datatable", "data", allow_duplicate=True),
     Output("alert-container", "children", allow_duplicate=True),
     Output("existing-seedtrains-table", "children", allow_duplicate=True)],
    [Input("save-existing-seedtrains", "n_clicks")],
    [State("seedtrain-experiment-select", "value"),
     State({'type': 'existing-st-pk', 'index': ALL}, 'children'),
     State({'type': 'existing-st-cell-line', 'index': ALL}, 'value'),
     State({'type': 'existing-st-clone', 'index': ALL}, 'value'),
     State({'type': 'existing-st-pool-clone', 'index': ALL}, 'value'),
     State({'type': 'existing-st-bank-age', 'index': ALL}, 'value'),
     State({'type': 'existing-st-passage', 'index': ALL}, 'value'),
     State({'type': 'existing-st-vessel-type', 'index': ALL}, 'value'),
     State({'type': 'existing-st-volume', 'index': ALL}, 'value'),
     State({'type': 'existing-st-thaw-date', 'index': ALL}, 'date'),
     State({'type': 'existing-st-media-prep', 'index': ALL}, 'value'),
     State({'type': 'existing-st-notes', 'index': ALL}, 'value'),
     State("seedtrains-datatable", "data")],
    prevent_initial_call=True
)
def save_existing_seedtrains(n_clicks, exp_id, seed_train_pks, cell_lines, clones, pool_clones,
                              bank_ages, passages, vessel_types, volumes, thaw_dates, media_prep_ids,
                              notes_list, current_data):
    """Update existing seed trains with edited data"""
    if not n_clicks:
        raise PreventUpdate

    if not seed_train_pks or len(seed_train_pks) == 0:
        return no_update, dbc.Alert("No existing seed trains to update", color="warning", duration=3000), no_update

    try:
        # Validate that all required fields are filled for each row
        for i in range(len(seed_train_pks)):
            if not thaw_dates[i] or not cell_lines[i] or not vessel_types[i]:
                return no_update, dbc.Alert(
                    f"Row {i+1}: Please fill in all required fields (Thaw Date, Cell Line, Vessel Type)",
                    color="danger",
                    duration=5000
                ), no_update

        # Update seed trains
        updated_count = 0
        for i in range(len(seed_train_pks)):
            try:
                seed_train = USPSeedTrain.objects.get(id=seed_train_pks[i])

                # Get media prep if selected
                media_prep = None
                media_type = ""
                media_lot = ""
                if media_prep_ids[i]:
                    try:
                        media_prep = USPMediaPrep.objects.get(id=media_prep_ids[i])
                        media_type = media_prep.media_name
                        media_lot = media_prep.lot_number if hasattr(media_prep, 'lot_number') else ""
                    except:
                        pass

                # Update fields
                seed_train.cell_line = cell_lines[i]
                seed_train.clone = clones[i] or ""
                seed_train.pool_or_clone = pool_clones[i] or ""
                seed_train.bank_age = bank_ages[i] or ""
                seed_train.passage_number = int(passages[i]) if passages[i] else None
                seed_train.vessel_type = vessel_types[i]
                seed_train.start_volume = float(volumes[i]) if volumes[i] else None
                seed_train.thaw_date = pd.to_datetime(thaw_dates[i]).date()
                seed_train.media_prep = media_prep
                seed_train.media_type = media_type
                seed_train.media_lot = media_lot
                seed_train.notes = notes_list[i] or ""

                seed_train.save()
                updated_count += 1
            except Exception as e:
                print(f"Error updating seed train {seed_train_pks[i]}: {e}")
                continue

        # Refresh datatable
        experiment = USPExperiment.objects.get(id=exp_id)
        seed_trains = USPSeedTrain.objects.select_related('process_step__experiment').filter(
            process_step__experiment=experiment
        )

        new_data = []
        for st in seed_trains:
            new_data.append({
                'experiment_id': st.process_step.experiment.experiment_id,
                'seed_train_id': st.seed_train_id,
                'cell_line': st.cell_line or '',
                'thaw_date': st.thaw_date.strftime('%Y-%m-%d') if st.thaw_date else '',
                'bank_age': st.bank_age or '',
                'pool_or_clone': st.pool_or_clone or '',
                'program': st.program or '',
                'clone': st.clone or '',
                'media_type': st.media_type or '',
                'media_lot': st.media_lot or '',
                'is_discarded': 'True' if st.is_discarded else 'False',
            })

        # Merge with other experiments' data
        other_exps_data = [row for row in current_data if row['experiment_id'] != experiment.experiment_id]
        final_data = other_exps_data + new_data

        alert = dbc.Alert(
            f"Successfully updated {updated_count} seed train(s)!",
            color="success",
            duration=3000
        )

        # Reload existing seed trains table to show updated data
        return final_data, alert, no_update

    except Exception as e:
        print(f"Error updating seed trains: {e}")
        import traceback
        traceback.print_exc()
        alert = dbc.Alert(f"Error: {str(e)}", color="danger", duration=5000)
        return no_update, alert, no_update

# Callback to open vessel registration modal
@app.callback(
    [Output("register-vessel-modal", "is_open"),
     Output("vessel-experiment-select", "options"),
     Output("vessel-media-prep", "options")],
    [Input("register-vessel-btn", "n_clicks"),
     Input("cancel-vessel-modal", "n_clicks")],
    [State("register-vessel-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_vessel_modal(register_clicks, cancel_clicks, is_open):
    """Open/close vessel registration modal and load dropdowns"""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "register-vessel-btn":
        # Load experiments
        experiments = USPExperiment.objects.all().order_by('-created_date')
        exp_options = [
            {'label': f"{exp.experiment_id} - {exp.experiment_name}", 'value': exp.id}
            for exp in experiments
        ]

        # Load media preps (all media preps, not filtered)
        media_preps = USPMediaPrep.objects.all().order_by('-preparation_date')
        media_options = [
            {'label': f"{mp.media_id} - {mp.media_name} ({mp.preparation_date})", 'value': mp.id}
            for mp in media_preps
        ]

        return True, exp_options, media_options

    return False, [], []

# Callback to load process steps and seed trains when experiment is selected (vessel modal)
@app.callback(
    [Output("vessel-step-select", "options"),
     Output("vessel-source-seedtrain", "options")],
    [Input("vessel-experiment-select", "value")],
    prevent_initial_call=True
)
def load_vessel_options(experiment_id):
    """Load bioreactor/shake flask steps and available seed trains for selected experiment"""
    if not experiment_id:
        return [], []

    try:
        # Load bioreactor and shake flask steps
        steps = USPProcessStep.objects.filter(
            experiment_id=experiment_id,
            step_type__in=['Bioreactor', 'Shake_Flask']
        ).order_by('step_order')

        step_options = [
            {'label': f"{step.step_name} ({step.step_type}) - Order {step.step_order}", 'value': step.id}
            for step in steps
        ]

        # Load seed trains from same experiment
        seed_trains = USPSeedTrain.objects.filter(
            process_step__experiment_id=experiment_id
        ).order_by('-thaw_date')

        seedtrain_options = [
            {'label': f"{st.seed_train_id} ({st.cell_line}) - {st.thaw_date}", 'value': st.id}
            for st in seed_trains
        ]

        return step_options, seedtrain_options

    except Exception as e:
        print(f"Error loading vessel options: {e}")
        return [], []

# Callback to save new vessels
@app.callback(
    [Output("vessels-datatable", "data", allow_duplicate=True),
     Output("register-vessel-modal", "is_open", allow_duplicate=True),
     Output("alert-container", "children", allow_duplicate=True)],
    [Input("save-vessel", "n_clicks")],
    [State("vessel-experiment-select", "value"),
     State("vessel-step-select", "value"),
     State("vessel-count", "value"),
     State("vessel-source-seedtrain", "value"),
     State("vessel-vessel-type", "value"),
     State("vessel-size", "value"),
     State("vessel-inoc-date", "value"),
     State("vessel-inoc-density", "value"),
     State("vessel-cell-line", "value"),
     State("vessel-volume", "value"),
     State("vessel-feed-strategy", "value"),
     State("vessel-media-prep", "value"),
     State("vessel-pool-clone", "value"),
     State("vessel-program", "value"),
     State("vessel-clone", "value"),
     State("vessel-temperature", "value"),
     State("vessel-ph", "value"),
     State("vessel-do", "value"),
     State("vessel-notes", "value"),
     State("vessels-datatable", "data")],
    prevent_initial_call=True
)
def save_vessels(n_clicks, exp_id, step_id, count, seedtrain_id, vessel_type, vessel_size,
                 inoc_date, inoc_density, cell_line, volume, feed_strategy, media_prep_id,
                 pool_clone, program, clone, temperature, ph, do, notes, current_data):
    """Create new vessels with seed train linking"""
    if not n_clicks:
        raise PreventUpdate

    # Validation
    if not exp_id or not step_id or not vessel_type or not seedtrain_id:
        return no_update, no_update, dbc.Alert("Please fill in all required fields (including source seed train)", color="danger", duration=3000)

    try:
        # Get seed train and media prep
        seed_train = USPSeedTrain.objects.get(id=seedtrain_id)
        media_prep = USPMediaPrep.objects.get(id=media_prep_id) if media_prep_id else None

        # Create vessels
        created_vessels = []
        for i in range(int(count)):
            vessel_id = generate_fed_batch_id()

            vessel = USPVessel.objects.create(
                process_step_id=step_id,
                seed_train=seed_train,  # FK to seed train
                vessel_id=vessel_id,
                vessel_type=vessel_type,
                vessel_size=vessel_size or "",
                start_volume=float(volume) if volume else None,
                cell_line=cell_line or seed_train.cell_line,
                media_type=media_prep.media_name if media_prep else "",
                media_prep=media_prep,
                feeding_strategy=feed_strategy or "",
                inoculation_date=pd.to_datetime(inoc_date).date() if inoc_date else None,
                inoculation_density=float(inoc_density) if inoc_density else None,
                pool_or_clone=pool_clone or seed_train.pool_or_clone,
                program=program or seed_train.program,
                clone=clone or seed_train.clone,
                temperature_setpoint=float(temperature) if temperature else 37.0,
                ph_setpoint=float(ph) if ph else 7.0,
                do_setpoint=float(do) if do else 40.0,
                status='Active',
                notes=notes or ""
            )
            created_vessels.append(vessel)

        # Refresh datatable
        experiment = USPExperiment.objects.get(id=exp_id)
        vessels = USPVessel.objects.select_related('process_step__experiment', 'seed_train').filter(
            process_step__experiment=experiment
        )

        new_data = []
        for v in vessels:
            new_data.append({
                'experiment_id': v.process_step.experiment.experiment_id,
                'vessel_id': v.vessel_id,
                'cell_line': v.cell_line or '',
                'inoculation_date': v.inoculation_date.strftime('%Y-%m-%d') if v.inoculation_date else '',
                'inoculation_density': v.inoculation_density or '',
                'seed_train_id': v.seed_train.seed_train_id if v.seed_train else '',
                'pool_or_clone': v.pool_or_clone or '',
                'program': v.program or '',
                'clone': v.clone or '',
                'media_type': v.media_type or '',
                'feeding_strategy': v.feeding_strategy or '',
                'vessel_type': v.vessel_type or '',
                'start_volume': v.start_volume or '',
                'vessel_size': v.vessel_size or '',
                'status': v.status or 'Active',
            })

        # Merge with other experiments' data
        other_exps_data = [row for row in current_data if row['experiment_id'] != experiment.experiment_id]
        final_data = other_exps_data + new_data

        alert = dbc.Alert(
            f"Successfully created {len(created_vessels)} vessel(s) linked to {seed_train.seed_train_id}!",
            color="success",
            duration=3000
        )

        return final_data, False, alert

    except Exception as e:
        print(f"Error creating vessels: {e}")
        import traceback
        traceback.print_exc()
        alert = dbc.Alert(f"Error: {str(e)}", color="danger", duration=5000)
        return no_update, no_update, alert

if __name__ == '__main__':
    app.run_server(debug=True)