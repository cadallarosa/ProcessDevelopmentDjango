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
from plotly_integration.models import USPExperiment, USPProcessStep, USPVessel, USPSeedTrain

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

app = DjangoDash("USPExperimentManagementAppV1", external_stylesheets=[
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
            {'step_name': 'Seed Train Day 1', 'step_type': 'Seed_Train', 'duration': 3, 'order': 1, 'start_date': today},
            {'step_name': 'Seed Train Day 4', 'step_type': 'Seed_Train', 'duration': 3, 'order': 2, 'start_date': today + timedelta(days=3)},
            {'step_name': 'Bioreactor Run', 'step_type': 'Bioreactor', 'duration': 14, 'order': 3, 'start_date': today + timedelta(days=6)},
            {'step_name': 'Shake Flask Run', 'step_type': 'Shake_Flask', 'duration': 14, 'order': 4, 'start_date': today + timedelta(days=6)},  # Parallel with bioreactor
        ],
        'bioreactor_only': [
            {'step_name': 'Seed Train', 'step_type': 'Seed_Train', 'duration': 7, 'order': 1, 'start_date': today},
            {'step_name': 'Bioreactor Run', 'step_type': 'Bioreactor', 'duration': 14, 'order': 2, 'start_date': today + timedelta(days=7)},
        ],
        'shake_flask_only': [
            {'step_name': 'Seed Train', 'step_type': 'Seed_Train', 'duration': 3, 'order': 1, 'start_date': today},
            {'step_name': 'Shake Flask Run', 'step_type': 'Shake_Flask', 'duration': 14, 'order': 2, 'start_date': today + timedelta(days=3)},
        ],
        'parallel_production': [
            {'step_name': 'Seed Train', 'step_type': 'Seed_Train', 'duration': 5, 'order': 1, 'start_date': today},
            {'step_name': 'Bioreactor Run', 'step_type': 'Bioreactor', 'duration': 14, 'order': 2, 'start_date': today + timedelta(days=5)},
            {'step_name': 'Shake Flask Run', 'step_type': 'Shake_Flask', 'duration': 14, 'order': 3, 'start_date': today + timedelta(days=5)},  # Same start date as bioreactor
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
                ], md=6),
                dbc.Col([
                    dbc.Label("Experiment Name", html_for="experiment-name-input"),
                    dbc.Input(
                        id="experiment-name-input",
                        placeholder="Enter experiment name",
                        required=True
                    ),
                ], md=6),
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
                            {'label': 'Standard (Seed Train → Bioreactor & Shake Flask)', 'value': 'standard'},
                            {'label': 'Bioreactor Only', 'value': 'bioreactor_only'},
                            {'label': 'Shake Flask Only', 'value': 'shake_flask_only'},
                            {'label': 'Parallel Production (Bioreactor & Shake Flask)', 'value': 'parallel_production'},
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

    # Manage Experiments Modal
    dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle("Manage Experiments")
        ]),
        dbc.ModalBody([
            dcc.Store(id="selected-experiment-id", data=None),
            dbc.Tabs([
                dbc.Tab(label="Experiments List", tab_id="list-tab", children=[
                    dbc.Card([
                        dbc.CardHeader([
                            dbc.Row([
                                dbc.Col([
                                    html.H6("All Experiments", className="mb-0")
                                ], width=6),
                                dbc.Col([
                                    dbc.Input(
                                        id="experiment-search",
                                        placeholder="Search experiments...",
                                        type="text",
                                        size="sm"
                                    )
                                ], width=6)
                            ])
                        ]),
                        dbc.CardBody([
                            html.Div([
                                html.Table(
                                    id="manage-experiments-table",
                                    children=[
                                        html.Thead([
                                            html.Tr([
                                                html.Th("Experiment ID"),
                                                html.Th("Name"),
                                                html.Th("Status"),
                                                html.Th("Start Date"),
                                                html.Th("Steps"),
                                                html.Th("Vessels"),
                                                html.Th("Actions")
                                            ])
                                        ]),
                                        html.Tbody(id="manage-experiments-tbody")
                                    ],
                                    className="table table-striped table-hover"
                                )
                            ])
                        ])
                    ], className="mt-3")
                ]),
                dbc.Tab(label="Edit Experiment", tab_id="edit-tab", children=[
                    dbc.Card([
                        dbc.CardBody([
                            # Basic Information Section
                            html.H5("Basic Information", className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Experiment ID"),
                                    dbc.Input(id="edit-exp-id", disabled=True),
                                ], width=3),
                                dbc.Col([
                                    dbc.Label("Experiment Name"),
                                    dbc.Input(id="edit-exp-name", placeholder="Enter experiment name"),
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Status"),
                                    dbc.Select(
                                        id="edit-exp-status",
                                        options=[
                                            {"label": "Planning", "value": "Planning"},
                                            {"label": "In Progress", "value": "In Progress"},
                                            {"label": "Complete", "value": "Complete"},
                                            {"label": "On Hold", "value": "On Hold"},
                                            {"label": "Cancelled", "value": "Cancelled"}
                                        ]
                                    ),
                                ], width=3),
                            ], className="mb-3"),

                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Experiment Type"),
                                    dbc.Select(
                                        id="edit-exp-type",
                                        options=[
                                            {"label": "Conformance", "value": "Conformance"},
                                            {"label": "pH Test", "value": "pH_Test"},
                                            {"label": "Temperature Test", "value": "Temperature_Test"},
                                            {"label": "Media Optimization", "value": "Media_Optimization"},
                                            {"label": "Feed Optimization", "value": "Feed_Optimization"},
                                            {"label": "Scale Up", "value": "Scale_Up"},
                                            {"label": "Process Characterization", "value": "Process_Characterization"},
                                            {"label": "Other", "value": "Other"}
                                        ]
                                    ),
                                ], width=4),
                                dbc.Col([
                                    dbc.Label("Start Date"),
                                    dbc.Input(id="edit-exp-start-date", type="date"),
                                ], width=4),
                                dbc.Col([
                                    dbc.Label("Target End Date"),
                                    dbc.Input(id="edit-exp-target-date", type="date"),
                                ], width=4),
                            ], className="mb-3"),

                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Description"),
                                    dbc.Textarea(id="edit-exp-description", rows=3),
                                ], width=12),
                            ], className="mb-4"),

                            html.Hr(),

                            # Process Steps Section
                            dbc.Row([
                                dbc.Col([
                                    html.H5("Process Steps", className="mb-3"),
                                ], width=9),
                                dbc.Col([
                                    dbc.Button(
                                        [html.I(className="fas fa-plus me-2"), "Add Step"],
                                        id="add-step-btn",
                                        color="success",
                                        size="sm"
                                    )
                                ], width=3, className="text-end"),
                            ]),

                            html.Div(id="process-steps-edit-section", className="mb-4"),

                            html.Hr(),

                            # Vessels/Bioreactors Section - Per-Step View
                            dbc.Row([
                                dbc.Col([
                                    html.H5("Vessels & Seed Trains by Process Step", className="mb-3"),
                                ], width=9),
                                dbc.Col([
                                    dbc.Select(
                                        id="step-filter-dropdown",
                                        options=[{"label": "All Steps", "value": "all"}],
                                        value="all",
                                        size="sm"
                                    )
                                ], width=3),
                            ]),

                            # Per-step sections will be dynamically generated here
                            html.Div(id="per-step-vessels-section", className="mb-4"),

                            # Hidden stores and components for backward compatibility
                            dcc.Store(id="pending-vessels-data"),
                            dcc.Store(id="vessel-step-select", data=None),
                            html.Div(id="vessel-config-section", style={"display": "none"}),
                            html.Div(id="seed-train-config-section", style={"display": "none"}),
                            html.Div(id="seed-train-preview-table", style={"display": "none"}),
                            html.Div(id="vessel-preview-container", style={"display": "none"}),
                            html.Div(id="vessels-edit-section", style={"display": "none"}),
                            dbc.Input(id="edit-vessel-type-select", type="hidden"),
                            dbc.Input(id="vessel-start-volume", type="hidden"),
                            dbc.Input(id="vessel-inoc-date", type="hidden"),
                            dbc.Input(id="vessel-inoc-density", type="hidden"),
                            dbc.Select(id="vessel-feeding-strategy"),
                            dbc.Input(id="vessel-count", type="hidden"),
                            dbc.Select(id="seed-train-source"),
                            dbc.Button(id="generate-vessels-btn", style={"display": "none"}),
                            dbc.Button(id="clear-vessels-btn", style={"display": "none"}),
                            dbc.Input(id="seed-train-thaw-date", type="hidden"),
                            dbc.Input(id="seed-train-start-volume", type="hidden"),
                            dbc.Input(id="seed-train-sample-count", type="hidden"),
                            dbc.Input(id="seed-train-media", type="hidden"),
                            dbc.Button(id="generate-seed-trains-btn", style={"display": "none"}),
                            dbc.Button(id="clear-seed-trains-btn", style={"display": "none"}),

                            # Save/Cancel buttons
                            dbc.Row([
                                dbc.Col([
                                    dbc.ButtonGroup([
                                        dbc.Button("Cancel", id="cancel-edit-btn", color="secondary"),
                                        dbc.Button("Save Changes", id="save-edit-btn", color="primary")
                                    ])
                                ], className="text-end mt-3")
                            ])
                        ])
                    ], className="mt-3")
                ])
            ], id="manage-tabs", active_tab="list-tab")
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id="close-manage-modal", color="secondary")
        ])
    ], id="manage-experiments-modal", fullscreen=True, is_open=False, scrollable=True),

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
     State("experiment-type-select", "value"),
     State("description-input", "value"),
     State("start-date", "date"),
     State("status-select", "value"),
     State("notes-input", "value"),
     State("workflow-steps-data", "data")],
    prevent_initial_call=True
)
def save_experiment(save_clicks, experiment_id, experiment_name, experiment_type, description, start_date, status, notes, workflow_steps_data):
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

# Callback for opening manage experiments modal
@app.callback(
    [Output("manage-experiments-modal", "is_open"),
     Output("manage-experiments-tbody", "children")],
    [Input("manage-experiments-btn", "n_clicks"),
     Input("close-manage-modal", "n_clicks")],
    [State("manage-experiments-modal", "is_open")]
)
def handle_manage_experiments_modal(manage_clicks, close_clicks, is_open):
    """Open/close manage experiments modal and load data"""
    ctx = dash.callback_context

    if not ctx.triggered:
        return is_open, []

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "manage-experiments-btn":
        # Load all experiments
        try:
            experiments = USPExperiment.objects.all().order_by('-created_date')
            table_rows = []

            for i, exp in enumerate(experiments):
                step_count = exp.process_steps.count()
                vessel_count = USPVessel.objects.filter(process_step__experiment=exp).count()

                # Create table row
                row = html.Tr([
                    html.Td(exp.experiment_id),
                    html.Td(exp.experiment_name),
                    html.Td(dbc.Badge(exp.status, color="primary")),
                    html.Td(exp.start_date.strftime('%Y-%m-%d') if exp.start_date else 'N/A'),
                    html.Td(str(step_count)),
                    html.Td(str(vessel_count)),
                    html.Td([
                        dbc.Button("Edit", size="sm", color="primary",
                                 id={'type': 'edit-experiment-btn', 'index': exp.id})
                    ])
                ], id={'type': 'experiment-row', 'index': exp.id})
                table_rows.append(row)

            return True, table_rows
        except Exception as e:
            print(f"Error loading experiments: {e}")
            return True, [html.Tr([html.Td(f"Error: {str(e)}", colSpan=7)])]

    elif button_id == "close-manage-modal":
        return False, []

    return is_open, []

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

if __name__ == '__main__':
    app.run_server(debug=True)