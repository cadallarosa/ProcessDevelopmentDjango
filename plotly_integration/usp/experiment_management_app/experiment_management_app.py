"""
USP Experiment Management Dashboard App
Main dashboard for tracking USP experiments with bioreactors, shake flasks, and seed trains
"""

import json
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
from plotly_integration.models import (
    USPExperiment, USPProcessStep, USPVessel, USPSeedTrain, USPMediaPrep, USPCellBank,
    LimsSampleAnalysis, LimsSecResult, LimsTiterResult, LimsCeSdsResult, LimsCiefResult
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_usp_experiment_number():
    """Generate the next USP experiment number in format USP####"""
    try:
        last_experiment = USPExperiment.objects.filter(
            experiment_id__startswith='USP'
        ).order_by('-experiment_id').first()

        if last_experiment:
            last_number = int(last_experiment.experiment_id[3:])
            next_number = last_number + 1
        else:
            next_number = 1

        return f"USP{next_number:04d}"
    except:
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

def generate_cell_bank_id():
    """Generate the next Cell Bank ID in format UPCB####"""
    try:
        last_cell_bank = USPCellBank.objects.filter(
            cell_bank_id__startswith='UPCB'
        ).order_by('-cell_bank_id').first()

        if last_cell_bank:
            last_number = int(last_cell_bank.cell_bank_id[4:])
            next_number = last_number + 1
        else:
            next_number = 1

        return f"UPCB{next_number:04d}"
    except:
        return "UPCB0001"

def get_workflow_template(template_type='standard', start_date=None):
    """Get workflow steps based on template type with individual start dates"""
    if start_date is None:
        start_date = date.today()
    elif isinstance(start_date, str):
        start_date = pd.to_datetime(start_date).date()

    templates = {
        'standard': [
            {'step_name': 'Seed Train', 'step_type': 'Seed_Train', 'duration': 7, 'order': 1, 'start_date': start_date},
            {'step_name': 'Bioreactor Run', 'step_type': 'Bioreactor', 'duration': 14, 'order': 2, 'start_date': start_date + timedelta(days=7)},
            {'step_name': 'Shake Flask Run', 'step_type': 'Shake_Flask', 'duration': 14, 'order': 3, 'start_date': start_date + timedelta(days=21)},
        ],
        'seed_train_bioreactor': [
            {'step_name': 'Seed Train', 'step_type': 'Seed_Train', 'duration': 7, 'order': 1, 'start_date': start_date},
            {'step_name': 'Bioreactor Run', 'step_type': 'Bioreactor', 'duration': 14, 'order': 2, 'start_date': start_date + timedelta(days=7)},
        ],
        'seed_train_shake_flask': [
            {'step_name': 'Seed Train', 'step_type': 'Seed_Train', 'duration': 7, 'order': 1, 'start_date': start_date},
            {'step_name': 'Shake Flask Run', 'step_type': 'Shake_Flask', 'duration': 14, 'order': 2, 'start_date': start_date + timedelta(days=7)},
        ],
        'custom': []
    }
    return templates.get(template_type, templates['standard'])

def create_process_step_card(step_data, index):
    """Create a process step card similar to seed train rows"""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                # Delete button
                dbc.Col([
                    dbc.Button(
                        html.I(className="fas fa-trash"),
                        id={'type': 'delete-step', 'index': index},
                        color="danger",
                        size="sm",
                        outline=True
                    )
                ], width="auto"),

                # Step Name
                dbc.Col([
                    dbc.Label("Step Name *", size="sm"),
                    dbc.Input(
                        id={'type': 'step-name', 'index': index},
                        type='text',
                        value=step_data.get('step_name', ''),
                        placeholder='Enter step name',
                        size='sm'
                    )
                ], width=3),

                # Step Type
                dbc.Col([
                    dbc.Label("Step Type *", size="sm"),
                    dcc.Dropdown(
                        id={'type': 'step-type', 'index': index},
                        options=[
                            {'label': 'Seed Train', 'value': 'Seed_Train'},
                            {'label': 'Bioreactor', 'value': 'Bioreactor'},
                            {'label': 'Shake Flask', 'value': 'Shake_Flask'},
                        ],
                        value=step_data.get('step_type', 'Seed_Train'),
                        clearable=False,
                        style={'width': '100%'}
                    )
                ], width=2),

                # Start Date
                dbc.Col([
                    dbc.Label("Start Date *", size="sm"),
                    dcc.DatePickerSingle(
                        id={'type': 'step-start-date', 'index': index},
                        date=step_data.get('start_date'),
                        display_format='YYYY-MM-DD',
                        style={'width': '100%'}
                    )
                ], width=2),

                # Duration
                dbc.Col([
                    dbc.Label("Duration (days) *", size="sm"),
                    dbc.Input(
                        id={'type': 'step-duration', 'index': index},
                        type='number',
                        value=step_data.get('duration', 7),
                        min=1,
                        size='sm'
                    )
                ], width=2),

                # Status
                dbc.Col([
                    dbc.Label("Status", size="sm"),
                    dcc.Dropdown(
                        id={'type': 'step-status', 'index': index},
                        options=[
                            {'label': 'Pending', 'value': 'Pending'},
                            {'label': 'In Progress', 'value': 'In Progress'},
                            {'label': 'Complete', 'value': 'Complete'},
                            {'label': 'Skipped', 'value': 'Skipped'},
                        ],
                        value=step_data.get('status', 'Pending'),
                        clearable=False,
                        style={'width': '100%'}
                    )
                ], width=2),
            ])
        ])
    ], className="mb-2")

def create_edit_process_step_card(step_data, index):
    """Create a process step card for edit modal (with edit- prefix)"""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                # Delete button
                dbc.Col([
                    dbc.Button(
                        html.I(className="fas fa-trash"),
                        id={'type': 'edit-delete-step', 'index': index},
                        color="danger",
                        size="sm",
                        outline=True
                    )
                ], width="auto"),

                # Step Name
                dbc.Col([
                    dbc.Label("Step Name *", size="sm"),
                    dbc.Input(
                        id={'type': 'edit-step-name', 'index': index},
                        type='text',
                        value=step_data.get('step_name', ''),
                        placeholder='Enter step name',
                        size='sm'
                    )
                ], width=3),

                # Step Type
                dbc.Col([
                    dbc.Label("Step Type *", size="sm"),
                    dcc.Dropdown(
                        id={'type': 'edit-step-type', 'index': index},
                        options=[
                            {'label': 'Seed Train', 'value': 'Seed_Train'},
                            {'label': 'Bioreactor', 'value': 'Bioreactor'},
                            {'label': 'Shake Flask', 'value': 'Shake_Flask'},
                        ],
                        value=step_data.get('step_type', 'Seed_Train'),
                        clearable=False,
                        style={'width': '100%'}
                    )
                ], width=2),

                # Start Date
                dbc.Col([
                    dbc.Label("Start Date *", size="sm"),
                    dcc.DatePickerSingle(
                        id={'type': 'edit-step-start-date', 'index': index},
                        date=step_data.get('start_date'),
                        display_format='YYYY-MM-DD',
                        style={'width': '100%'}
                    )
                ], width=2),

                # Duration
                dbc.Col([
                    dbc.Label("Duration (days) *", size="sm"),
                    dbc.Input(
                        id={'type': 'edit-step-duration', 'index': index},
                        type='number',
                        value=step_data.get('duration', 7),
                        min=1,
                        size='sm'
                    )
                ], width=2),

                # Status
                dbc.Col([
                    dbc.Label("Status", size="sm"),
                    dcc.Dropdown(
                        id={'type': 'edit-step-status', 'index': index},
                        options=[
                            {'label': 'Pending', 'value': 'Pending'},
                            {'label': 'In Progress', 'value': 'In Progress'},
                            {'label': 'Complete', 'value': 'Complete'},
                            {'label': 'Skipped', 'value': 'Skipped'},
                        ],
                        value=step_data.get('status', 'Pending'),
                        clearable=False,
                        style={'width': '100%'}
                    )
                ], width=2),
            ])
        ])
    ], className="mb-2")

def create_gantt_chart(status_filter='all', step_type_filter='all', start_date=None, end_date=None):
    """Create interactive Gantt chart for USP experiments (original version)"""
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
            # Include project ID in legend name
            project_label = f" ({experiment.project_id})" if experiment.project_id else ""
            experiment_name = f"{experiment.experiment_id}{project_label}"
            experiment_id_only = experiment.experiment_id  # For legend grouping

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
                show_legend = experiment_id_only not in added_experiments
                if show_legend:
                    added_experiments.add(experiment_id_only)

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
                    legendgroup=experiment_id_only,
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

        # Set date range: 5 days before current date to 1.5 months after
        x_start = datetime.now() - timedelta(days=5)
        x_end = datetime.now() + timedelta(days=45)  # 1.5 months = ~45 days

        # Update layout
        fig.update_layout(
            height=500,
            title="USP Experiment Process Timeline",
            xaxis_title="Timeline",
            yaxis_title="Process Steps",
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(
                type='date',
                showgrid=True,
                gridcolor='#e8e8e8',
                gridwidth=1,
                range=[x_start, x_end]
            ),
            yaxis=dict(
                tickmode='array',
                tickvals=[s['y_pos'] for s in workflow_steps],
                ticktext=[s['step'].replace('_', ' ') for s in workflow_steps],
                showgrid=True,
                gridcolor='#e8e8e8',
                gridwidth=1,
                range=[-1, len(workflow_steps)]
            ),
            showlegend=True,
            legend=dict(
                title="Experiments",
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='#e8e8e8',
                borderwidth=1
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

# ============================================================================
# APP INITIALIZATION
# ============================================================================

app = DjangoDash(
    'USPExperimentManagementApp',
    external_stylesheets=[dbc.themes.BOOTSTRAP, 'https://use.fontawesome.com/releases/v5.15.4/css/all.css']
)

# ============================================================================
# MAIN LAYOUT
# ============================================================================

app.layout = dbc.Container([
    # Stores
    dcc.Store(id='selected-experiment-id', data=None),
    dcc.Store(id='view-experiment-id', data=None),  # Separate store for View modal
    dcc.Store(id="seedtrain-table-data", data=[]),
    dcc.Store(id="seedtrain-row-counter", data=0),
    dcc.Store(id="process-steps-store", data=[]),
    dcc.Store(id="edit-mode", data=False),
    dcc.Store(id="loaded-experiment-steps", data=[]),  # Store for loading steps in edit mode
    dcc.Store(id="edit-process-steps-store", data=[]),  # Store for edit modal process steps

    # Alert container
    html.Div(id="alert-container"),

    # Header
    dbc.Row([
        dbc.Col([
            html.H1([
                html.I(className="fas fa-flask text-primary me-3"),
                "USP Experiment Management"
            ], className="mb-3"),
            html.P("Track experiments, seed trains, fed batch vessels, and cell banks",
                   className="lead text-muted")
        ], width=12),
    ], className="mb-4"),

    # Tabs Structure
    dbc.Tabs([
        # ========== OVERVIEW TAB ==========
        dbc.Tab(label="Overview", tab_id="overview-tab", children=[
            dbc.Card([
                dbc.CardHeader([
                    html.H5([html.I(className="fas fa-chart-gantt me-2"), "Experiment Timeline"],
                           className="mb-0")
                ]),
                dbc.CardBody([
                    dcc.Graph(id="gantt-chart", style={'height': '70vh'})
                ])
            ], className="mt-4")
        ]),

        # ========== EXPERIMENTS TAB ==========
        dbc.Tab(label="Experiments", tab_id="experiments-tab", children=[
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H5([html.I(className="fas fa-flask me-2"), "Experiment Management"],
                                   className="mb-0")
                        ], width="auto"),
                        dbc.Col([
                            dbc.Button(
                                [html.I(className="fas fa-plus me-2"), "New Experiment"],
                                id="new-experiment-btn",
                                color="primary",
                                size="sm"
                            )
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    # All Experiments Table
                    html.Div(id="experiments-table-container")
                ])
            ], className="mt-4"),

            # New/Edit Experiment Modal (Full Screen)
            dbc.Modal([
                dbc.ModalHeader([
                    dbc.ModalTitle(id="experiment-modal-title")
                ]),
                dbc.ModalBody([
                    # Alert container for modal
                    html.Div(id="modal-alert-container"),

                    # Experiment Form
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Experiment ID"),
                            dbc.Input(id="experiment-id-input", disabled=True),
                        ], md=3),
                        dbc.Col([
                            dbc.Label("Project ID"),
                            dbc.Input(id="project-id-input", placeholder="e.g., SI-49T5"),
                        ], md=3),
                        dbc.Col([
                            dbc.Label("Experiment Name *"),
                            dbc.Input(id="experiment-name-input", placeholder="Enter experiment name"),
                        ], md=4),
                        dbc.Col([
                            dbc.Label("Start Date *"),
                            dcc.DatePickerSingle(
                                id="experiment-start-date",
                                date=date.today(),
                                display_format='YYYY-MM-DD',
                                style={'width': '100%'}
                            ),
                        ], md=2),
                    ], className="mb-3"),

                    html.Hr(className="my-3"),

                    # Template Selection
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Workflow Template (Optional)"),
                            dcc.Dropdown(
                                id="workflow-template-select",
                                options=[
                                    {'label': 'Standard (Seed Train → Bioreactor → Shake Flask)', 'value': 'standard'},
                                    {'label': 'Seed Train + Bioreactor', 'value': 'seed_train_bioreactor'},
                                    {'label': 'Seed Train + Shake Flask', 'value': 'seed_train_shake_flask'},
                                    {'label': 'Custom (Add manually)', 'value': 'custom'},
                                ],
                                placeholder="Select template to auto-populate steps, or add manually..."
                            ),
                        ], md=12),
                    ], className="mb-3"),

                    # Process Steps Editor
                    dbc.Row([
                        dbc.Col([
                            html.H6("Process Steps", className="mb-3"),
                        ], width=9),
                        dbc.Col([
                            dbc.Button(
                                [html.I(className="fas fa-plus me-2"), "Add Step"],
                                id="add-process-step",
                                color="info",
                                size="sm",
                                outline=True
                            )
                        ], width=3),
                    ]),

                    # Process steps container (cards rendered from store)
                    html.Div(id="process-steps-container"),
                ]),
                dbc.ModalFooter([
                    dbc.Button("Cancel", id="close-experiment-modal", color="secondary", outline=True),
                    dbc.Button(
                        [html.I(className="fas fa-save me-2"), "Save"],
                        id="save-experiment-btn",
                        color="success"
                    ),
                ])
            ], id="experiment-modal", size="xl", is_open=False, fullscreen=True),

            # Edit Experiment Modal (Simpler - no template selector)
            dbc.Modal([
                dbc.ModalHeader([
                    dbc.ModalTitle(id="edit-experiment-modal-title")
                ]),
                dbc.ModalBody([
                    # Alert container for modal
                    html.Div(id="edit-modal-alert-container"),

                    # Experiment Form
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Experiment ID"),
                            dbc.Input(id="edit-experiment-id-input", disabled=True),
                        ], md=3),
                        dbc.Col([
                            dbc.Label("Project ID"),
                            dbc.Input(id="edit-project-id-input", placeholder="e.g., SI-49T5"),
                        ], md=3),
                        dbc.Col([
                            dbc.Label("Experiment Name *"),
                            dbc.Input(id="edit-experiment-name-input", placeholder="Enter experiment name"),
                        ], md=4),
                        dbc.Col([
                            dbc.Label("Start Date *"),
                            dcc.DatePickerSingle(
                                id="edit-experiment-start-date",
                                date=date.today(),
                                display_format='YYYY-MM-DD',
                                style={'width': '100%'}
                            ),
                        ], md=2),
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Description"),
                            dbc.Textarea(
                                id="edit-experiment-description-input",
                                placeholder="Enter detailed experiment description (optional)",
                                style={'height': '100px'}
                            ),
                        ], md=12),
                    ], className="mb-3"),

                    html.Hr(className="my-3"),

                    # Process Steps Editor
                    dbc.Row([
                        dbc.Col([
                            html.H6("Process Steps", className="mb-3"),
                        ], width=9),
                        dbc.Col([
                            dbc.Button(
                                [html.I(className="fas fa-plus me-2"), "Add Step"],
                                id="edit-add-process-step",
                                color="info",
                                size="sm",
                                outline=True
                            )
                        ], width=3),
                    ]),

                    # Process steps container (cards rendered from store)
                    html.Div(id="edit-process-steps-container"),
                ]),
                dbc.ModalFooter([
                    dbc.Button("Cancel", id="close-edit-experiment-modal", color="secondary", outline=True),
                    dbc.Button(
                        [html.I(className="fas fa-save me-2"), "Save Changes"],
                        id="save-edit-experiment-btn",
                        color="success"
                    ),
                ])
            ], id="edit-experiment-modal", size="xl", is_open=False, fullscreen=True),

            # View Experiment Details Modal (Full Screen)
            dbc.Modal([
                dbc.ModalHeader([
                    dbc.ModalTitle(id="view-experiment-modal-title")
                ]),
                dbc.ModalBody([
                    # Experiment Info Section
                    dbc.Card([
                        dbc.CardHeader(html.H5("Experiment Information")),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Strong("Experiment ID: "),
                                    html.Span(id="view-exp-id")
                                ], md=3),
                                dbc.Col([
                                    html.Strong("Project ID: "),
                                    html.Span(id="view-exp-project-id")
                                ], md=3),
                                dbc.Col([
                                    html.Strong("Status: "),
                                    html.Span(id="view-exp-status")
                                ], md=3),
                                dbc.Col([
                                    html.Strong("Start Date: "),
                                    html.Span(id="view-exp-start-date")
                                ], md=3),
                            ], className="mb-2"),
                            dbc.Row([
                                dbc.Col([
                                    html.Strong("Experiment Name: "),
                                    html.Span(id="view-exp-name")
                                ], md=12),
                            ], className="mb-2"),
                            dbc.Row([
                                dbc.Col([
                                    html.Strong("Description: "),
                                    html.Div(id="view-exp-description", style={'whiteSpace': 'pre-wrap'})
                                ], md=12),
                            ]),
                        ])
                    ], className="mb-3"),

                    # Seed Trains Section
                    dbc.Card([
                        dbc.CardHeader(html.H5("Seed Trains")),
                        dbc.CardBody([
                            html.Div(id="view-exp-seed-trains-table")
                        ])
                    ], className="mb-3"),

                    # Fed Batch Vessels Section
                    dbc.Card([
                        dbc.CardHeader(html.H5("Fed Batch Vessels")),
                        dbc.CardBody([
                            html.Div(id="view-exp-vessels-table")
                        ])
                    ], className="mb-3"),

                    # LIMS Analytical Results Section
                    dbc.Card([
                        dbc.CardHeader(html.H5("LIMS Analytical Results")),
                        dbc.CardBody([
                            html.Div(id="view-exp-lims-results-table")
                        ])
                    ], className="mb-3"),
                ]),
                dbc.ModalFooter([
                    dbc.Button("Close", id="close-view-experiment-modal", color="secondary"),
                ])
            ], id="view-experiment-modal", size="xl", is_open=False, fullscreen=True),
        ]),

        # ========== SEED TRAINS TAB ==========
        dbc.Tab(label="Seed Trains", tab_id="seed-trains-tab", children=[
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H5([html.I(className="fas fa-seedling me-2"), "Seed Train Registration"],
                                   className="mb-0")
                        ], width="auto"),
                        dbc.Col([
                            dbc.Button(
                                [html.I(className="fas fa-table me-2"), "View All Seed Trains"],
                                id="view-all-seedtrains-btn",
                                color="info",
                                size="sm",
                                outline=True
                            )
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    # Experiment selector and seed train manager
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Select Experiment"),
                            dcc.Dropdown(
                                id="main-experiment-select",
                                options=[{'label': 'View All', 'value': 'VIEW_ALL'}],
                                placeholder="Select experiment to manage seed trains"
                            ),
                        ], md=6),
                        dbc.Col([
                            dbc.Label("Process Step"),
                            dcc.Dropdown(
                                id="main-step-select",
                                placeholder="Select process step"
                            ),
                        ], md=4),
                        dbc.Col([
                            dbc.Label("Project"),
                            dbc.Input(
                                id="main-project-input",
                                type="text",
                                placeholder="e.g., SI-49T5"
                            ),
                        ], md=2),
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
                    html.Div(id="unified-seedtrains-table", children=[
                        html.P("Select an experiment above to view seed trains, or click 'Add Seed Train' to create new entries",
                               className="text-muted text-center py-5")
                    ]),

                    html.Hr(),

                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Save All Changes", id="save-all-seedtrains", color="success", size="lg"),
                        ], width=12, className="text-center"),
                    ]),
                ])
            ], className="mt-4"),

            # View All Modal with DataTable
            dbc.Modal([
                dbc.ModalHeader([dbc.ModalTitle("All Seed Trains")]),
                dbc.ModalBody([
                    html.Div(id="all-seedtrains-datatable")
                ]),
                dbc.ModalFooter([
                    dbc.Button("Close", id="close-viewall-modal", color="secondary")
                ])
            ], id="viewall-seedtrains-modal", size="xl", is_open=False, fullscreen=True),
        ]),

        # ========== FED BATCH TAB ==========
        dbc.Tab(label="Fed Batch", tab_id="fed-batch-tab", children=[
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H5([html.I(className="fas fa-flask me-2"), "Fed Batch Vessel Registration"],
                                   className="mb-0")
                        ], width="auto"),
                        dbc.Col([
                            dbc.Button(
                                [html.I(className="fas fa-table me-2"), "View All Fed Batch"],
                                id="view-all-fedbatch-btn",
                                color="info",
                                size="sm",
                                outline=True
                            )
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    # Experiment selector
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Select Experiment"),
                            dcc.Dropdown(
                                id="fb-experiment-select",
                                placeholder="Select experiment to manage fed batch"
                            ),
                        ], md=6),
                        dbc.Col([
                            dbc.Label("Process Step"),
                            dcc.Dropdown(
                                id="fb-step-select",
                                placeholder="Select process step"
                            ),
                        ], md=6),
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                [html.I(className="fas fa-plus me-2"), "Add Fed Batch Vessel"],
                                id="add-fedbatch-row-btn",
                                color="primary",
                                size="sm"
                            ),
                        ], width="auto"),
                    ], className="mb-3"),

                    html.Hr(),

                    # Fed Batch Table
                    dcc.Store(id="fedbatch-table-data", data=[]),
                    dcc.Store(id="fedbatch-row-counter", data=0),
                    html.Div(id="unified-fedbatch-table", children=[
                        html.P("Select an experiment above to view fed batch vessels, or click 'Add Fed Batch Vessel' to create new entries",
                               className="text-muted text-center py-5")
                    ]),

                    html.Hr(),

                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Save All Changes", id="save-all-fedbatch", color="success", size="lg"),
                        ], width=12, className="text-center"),
                    ]),
                ])
            ], className="mt-4"),

            # View All Modal with DataTable
            dbc.Modal([
                dbc.ModalHeader([dbc.ModalTitle("All Fed Batch Vessels")]),
                dbc.ModalBody([
                    html.Div(id="all-fedbatch-datatable")
                ]),
                dbc.ModalFooter([
                    dbc.Button("Close", id="close-viewall-fb-modal", color="secondary")
                ])
            ], id="viewall-fedbatch-modal", size="xl", is_open=False, fullscreen=True),
        ]),

        # ========== CELL BANKS TAB ==========
        dbc.Tab(label="Cell Banks", tab_id="cell-banks-tab", children=[
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H5([html.I(className="fas fa-database me-2"), "Cell Bank Registration"],
                                   className="mb-0")
                        ], width="auto"),
                        dbc.Col([
                            dbc.Button(
                                [html.I(className="fas fa-table me-2"), "View All Cell Banks"],
                                id="view-all-cellbanks-btn",
                                color="info",
                                size="sm",
                                outline=True
                            )
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    # Experiment selector
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Select Experiment"),
                            dcc.Dropdown(
                                id="cb-experiment-select",
                                placeholder="Select experiment to manage cell banks"
                            ),
                        ], md=6),
                        dbc.Col([
                            dbc.Label("Process Step"),
                            dcc.Dropdown(
                                id="cb-step-select",
                                placeholder="Select process step"
                            ),
                        ], md=6),
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                [html.I(className="fas fa-plus me-2"), "Add Cell Bank"],
                                id="add-cellbank-row-btn",
                                color="primary",
                                size="sm"
                            ),
                        ], width="auto"),
                    ], className="mb-3"),

                    html.Hr(),

                    # Cell Bank Table
                    dcc.Store(id="cellbank-table-data", data=[]),
                    dcc.Store(id="cellbank-row-counter", data=0),
                    html.Div(id="unified-cellbank-table", children=[
                        html.P("Select an experiment above to view cell banks, or click 'Add Cell Bank' to create new entries",
                               className="text-muted text-center py-5")
                    ]),

                    html.Hr(),

                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Save All Changes", id="save-all-cellbanks", color="success", size="lg"),
                        ], width=12, className="text-center"),
                    ]),
                ])
            ], className="mt-4"),

            # View All Modal with DataTable
            dbc.Modal([
                dbc.ModalHeader([dbc.ModalTitle("All Cell Banks")]),
                dbc.ModalBody([
                    html.Div(id="all-cellbanks-datatable")
                ]),
                dbc.ModalFooter([
                    dbc.Button("Close", id="close-viewall-cb-modal", color="secondary")
                ])
            ], id="viewall-cellbanks-modal", size="xl", is_open=False),
        ]),

    ], id="main-tabs", active_tab="overview-tab"),

], fluid=True, style={'padding': '20px'})

# ============================================================================
# CALLBACKS
# ============================================================================

# Open/Close experiment modal and load data (CREATE only, EDIT uses separate modal)
@app.callback(
    [Output("experiment-modal", "is_open"),
     Output("experiment-modal-title", "children"),
     Output("experiment-id-input", "value"),
     Output("project-id-input", "value"),
     Output("experiment-name-input", "value"),
     Output("experiment-start-date", "date"),
     Output("edit-mode", "data"),
     Output("workflow-template-select", "value"),
     Output("loaded-experiment-steps", "data")],
    [Input("new-experiment-btn", "n_clicks"),
     Input("close-experiment-modal", "n_clicks")],
    [State("experiment-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_experiment_modal(new_clicks, close_clicks, is_open):
    """
    Modal handling for experiment CREATION only. EDIT uses separate modal.
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # CASE 1: Close modal via Cancel button
    if triggered_id == "close-experiment-modal":
        if not close_clicks:
            raise PreventUpdate
        return (
            False,  # Close modal
            "",
            generate_usp_experiment_number(),
            "",
            "",
            date.today(),
            False,
            None,  # Clear template
            []  # Empty list
        )

    # CASE 2: Open modal for NEW experiment
    if triggered_id == "new-experiment-btn":
        if not new_clicks:
            raise PreventUpdate

        print("DEBUG: Opening NEW experiment modal")
        return (
            True,  # Open modal
            "Create New Experiment",
            generate_usp_experiment_number(),
            "",
            "",
            date.today(),
            False,  # Not edit mode
            None,  # No template selected
            []  # Empty process steps
        )

    raise PreventUpdate

# ============================================================================
# EDIT EXPERIMENT MODAL CALLBACKS
# ============================================================================

# Open/Close edit experiment modal and load data
@app.callback(
    [Output("edit-experiment-modal", "is_open"),
     Output("edit-experiment-modal-title", "children"),
     Output("edit-experiment-id-input", "value"),
     Output("edit-project-id-input", "value"),
     Output("edit-experiment-name-input", "value"),
     Output("edit-experiment-start-date", "date"),
     Output("edit-experiment-description-input", "value"),
     Output("selected-experiment-id", "data")],  # Store experiment ID instead of steps
    [Input({'type': 'edit-experiment-btn', 'index': ALL}, 'n_clicks'),
     Input("close-edit-experiment-modal", "n_clicks")],
    prevent_initial_call=True
)
def toggle_edit_experiment_modal(edit_clicks, close_clicks):
    """Open/close edit experiment modal and load experiment data"""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Close modal
    if triggered_id == "close-edit-experiment-modal":
        return False, "", "", "", "", date.today(), "", None

    # Open modal for editing
    if triggered_id.startswith('{'):
        import json
        button_id = json.loads(triggered_id)

        if button_id.get('type') == 'edit-experiment-btn':
            if not edit_clicks or all(click is None for click in edit_clicks):
                raise PreventUpdate

            experiment_id = button_id['index']
            print(f"🔧 EDIT MODAL: Loading experiment ID: {experiment_id}")

            try:
                experiment = USPExperiment.objects.get(id=experiment_id)
                print(f"🔧 EDIT MODAL: Found experiment {experiment.experiment_id}")
                print(f"🔧 EDIT MODAL: Project ID from DB: [{experiment.project_id}]")

                return (
                    True,  # Open modal
                    f"Edit Experiment: {experiment.experiment_id}",
                    experiment.experiment_id,
                    experiment.project_id or "",
                    experiment.experiment_name,
                    experiment.start_date or date.today(),
                    experiment.description or "",
                    experiment_id  # Just store the ID
                )

            except USPExperiment.DoesNotExist:
                print(f"ERROR: Experiment with ID {experiment_id} not found")
                raise PreventUpdate
            except Exception as e:
                print(f"ERROR: Failed to load experiment: {e}")
                import traceback
                traceback.print_exc()
                raise PreventUpdate

    raise PreventUpdate

# Manage edit modal process steps store
@app.callback(
    Output('edit-process-steps-store', 'data'),
    [Input('edit-add-process-step', 'n_clicks'),
     Input({'type': 'edit-delete-step', 'index': ALL}, 'n_clicks')],
    [State('edit-process-steps-store', 'data'),
     State('edit-experiment-start-date', 'date')],
    prevent_initial_call=True
)
def manage_edit_process_steps_store(add_clicks, delete_clicks, store_data, start_date):
    """Manage process steps in edit modal"""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print(f"🔧 EDIT manage_process_steps_store triggered by: {triggered_id}")

    # Add step
    if triggered_id == "edit-add-process-step":
        if not add_clicks:
            raise PreventUpdate

        current_steps = store_data if store_data and isinstance(store_data, list) else []
        new_index = len(current_steps)

        new_step = {
            'index': new_index,
            'step_name': '',
            'step_type': 'Seed_Train',
            'start_date': start_date if start_date else date.today().isoformat(),
            'duration': 7,
            'status': 'Pending'
        }

        result = current_steps + [new_step]
        print(f"🔧 EDIT: Added step, now {len(result)} steps")
        return result

    # Delete step
    if triggered_id.startswith('{') and 'edit-delete-step' in triggered_id:
        import json
        triggered_dict = json.loads(triggered_id)
        clicked_index = triggered_dict['index']

        current_steps = store_data if store_data and isinstance(store_data, list) else []

        if clicked_index < len(current_steps):
            new_steps = current_steps[:clicked_index] + current_steps[clicked_index + 1:]

            # Re-index
            for i, step in enumerate(new_steps):
                step['index'] = i

            print(f"🔧 EDIT: Deleted step at index {clicked_index}, now {len(new_steps)} steps")
            return new_steps

    raise PreventUpdate

# Render process steps in edit modal - query database directly
@app.callback(
    Output('edit-process-steps-container', 'children'),
    [Input('edit-experiment-modal', 'is_open'),
     Input('edit-add-process-step', 'n_clicks')],
    [State('selected-experiment-id', 'data'),
     State('edit-process-steps-container', 'children')],
    prevent_initial_call=False
)
def render_edit_process_steps(is_open, add_clicks, experiment_id, current_children):
    """Render process step cards by querying database directly"""
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    print(f"🎨 EDIT RENDER called by: {triggered_id}, is_open={is_open}, experiment_id={experiment_id}")

    # Only render when modal is open
    if not is_open or not experiment_id:
        print("🎨 EDIT RENDER: Modal closed or no experiment, returning placeholder")
        return html.P("Click 'Add Step' to add process steps",
                     className="text-muted text-center py-4")

    try:
        # Query database directly for process steps
        experiment = USPExperiment.objects.get(id=experiment_id)
        steps = experiment.process_steps.all().order_by('step_order')

        print(f"🎨 EDIT RENDER: Found {steps.count()} process steps from database")

        if steps.count() == 0:
            print("🎨 EDIT RENDER: No steps, returning placeholder")
            return html.P("Click 'Add Step' to add process steps",
                         className="text-muted text-center py-4")

        # Create cards from database steps
        cards = []
        for idx, step in enumerate(steps):
            step_data = {
                'index': idx,
                'step_name': step.step_name,
                'step_type': step.step_type,
                'start_date': step.planned_start_date.isoformat() if step.planned_start_date else date.today().isoformat(),
                'duration': step.planned_duration_days,
                'status': step.status or 'Pending'
            }
            print(f"🎨 EDIT: Creating card {idx}: {step.step_name}")
            card = create_edit_process_step_card(step_data, idx)
            cards.append(card)

        print(f"🎨 EDIT RENDER: Returning {len(cards)} cards")
        return cards

    except USPExperiment.DoesNotExist:
        print(f"🎨 EDIT RENDER: Experiment {experiment_id} not found")
        return html.P("Experiment not found",
                     className="text-muted text-center py-4")
    except Exception as e:
        print(f"🎨 EDIT RENDER: Error: {e}")
        import traceback
        traceback.print_exc()
        return html.P("Error loading process steps",
                     className="text-muted text-center py-4")

# Save edited experiment
@app.callback(
    [Output("edit-modal-alert-container", "children"),
     Output("alert-container", "children", allow_duplicate=True),
     Output("edit-experiment-modal", "is_open", allow_duplicate=True)],
    [Input("save-edit-experiment-btn", "n_clicks")],
    [State("edit-experiment-id-input", "value"),
     State("edit-project-id-input", "value"),
     State("edit-experiment-name-input", "value"),
     State("edit-experiment-start-date", "date"),
     State("edit-experiment-description-input", "value"),
     State({'type': 'edit-step-name', 'index': ALL}, 'value'),
     State({'type': 'edit-step-type', 'index': ALL}, 'value'),
     State({'type': 'edit-step-start-date', 'index': ALL}, 'date'),
     State({'type': 'edit-step-duration', 'index': ALL}, 'value'),
     State({'type': 'edit-step-status', 'index': ALL}, 'value')],
    prevent_initial_call=True
)
def save_edit_experiment(n_clicks, exp_id, project_id, exp_name, start_date, description,
                        step_names, step_types, step_start_dates, step_durations, step_statuses):
    """Update existing experiment with process steps"""
    if not n_clicks:
        raise PreventUpdate

    if not exp_name:
        return (dbc.Alert("Please enter an experiment name", color="danger", duration=3000), no_update, no_update)

    if not step_names or len(step_names) == 0:
        return (dbc.Alert("Please define at least one process step", color="danger", duration=3000), no_update, no_update)

    # Validate that at least one step has a name
    if not any(name.strip() for name in step_names if name):
        return (dbc.Alert("Please enter a name for at least one process step", color="danger", duration=3000), no_update, no_update)

    try:
        # Convert start_date to date object if needed
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date).date()

        # UPDATE existing experiment
        try:
            experiment = USPExperiment.objects.get(experiment_id=exp_id)
            experiment.project_id = project_id or ""
            experiment.experiment_name = exp_name
            experiment.start_date = start_date
            experiment.description = description or ""
            experiment.save()

            # Delete existing process steps and recreate
            experiment.process_steps.all().delete()

            # Create new process steps from pattern-matching inputs
            for i in range(len(step_names)):
                if step_names[i] and step_names[i].strip():  # Only create if step has a name
                    step_start = pd.to_datetime(step_start_dates[i]).date() if step_start_dates[i] else start_date
                    step_duration = int(step_durations[i]) if step_durations[i] else 7
                    step_status = step_statuses[i] if i < len(step_statuses) and step_statuses[i] else 'Pending'

                    USPProcessStep.objects.create(
                        experiment=experiment,
                        step_name=step_names[i],
                        step_type=step_types[i] if i < len(step_types) else 'Seed_Train',
                        step_order=i + 1,
                        planned_duration_days=step_duration,
                        planned_start_date=step_start,
                        planned_end_date=step_start + timedelta(days=step_duration),
                        status=step_status
                    )

            # Show success message and close modal
            success_alert = dbc.Alert(
                f"Successfully updated experiment {experiment.experiment_id}!",
                color="success",
                duration=4000
            )
            print(f"✅ Successfully updated experiment {experiment.experiment_id}")
            return (no_update, success_alert, False)  # Close modal

        except USPExperiment.DoesNotExist:
            return (dbc.Alert(f"Experiment {exp_id} not found", color="danger", duration=4000), no_update, no_update)

    except Exception as e:
        print(f"Error saving experiment: {e}")
        import traceback
        traceback.print_exc()
        error_alert = dbc.Alert(f"Error: {str(e)}", color="danger", duration=5000)
        return (error_alert, no_update, no_update)

# UNIFIED callback to manage process steps store
@app.callback(
    Output('process-steps-store', 'data'),
    [Input('workflow-template-select', 'value'),
     Input('add-process-step', 'n_clicks'),
     Input({'type': 'delete-step', 'index': ALL}, 'n_clicks'),
     Input('loaded-experiment-steps', 'data')],
    [State('process-steps-store', 'data'),
     State('experiment-start-date', 'date'),
     State('edit-mode', 'data')],
    prevent_initial_call=True
)
def manage_process_steps_store(template_value, add_clicks, delete_clicks, loaded_steps, store_data, start_date, edit_mode):
    """Unified callback to handle all process steps store updates"""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print(f"🔧 manage_process_steps_store triggered by: {triggered_id}, edit_mode={edit_mode}")

    # CASE 0: Loaded experiment steps (from edit mode)
    if triggered_id == "loaded-experiment-steps":
        if loaded_steps and isinstance(loaded_steps, list) and len(loaded_steps) > 0:
            print(f"🔧 Loading {len(loaded_steps)} steps from loaded experiment")
            return loaded_steps
        else:
            print(f"🔧 No loaded steps, maintaining current store")
            raise PreventUpdate

    # CASE 1: Template selected
    if triggered_id == "workflow-template-select":
        if not template_value or template_value == 'custom':
            print(f"🔧 Template value is None or custom, not updating store")
            raise PreventUpdate

        print(f"🔧 Loading template: {template_value}")
        workflow_steps = get_workflow_template(template_value, start_date)

        steps_data = []
        for idx, step in enumerate(workflow_steps):
            steps_data.append({
                'index': idx,
                'step_name': step['step_name'],
                'step_type': step['step_type'],
                'start_date': step['start_date'].isoformat() if hasattr(step['start_date'], 'isoformat') else str(step['start_date']),
                'duration': step['duration'],
                'status': 'Pending'
            })

        print(f"🔧 Template loaded: {len(steps_data)} steps")
        return steps_data

    # CASE 2: Add step button clicked
    if triggered_id == "add-process-step":
        if not add_clicks:
            raise PreventUpdate

        current_steps = store_data if store_data and isinstance(store_data, list) else []
        new_index = len(current_steps)

        print(f"🔧 Adding step at index {new_index}, current count: {len(current_steps)}")

        new_step = {
            'index': new_index,
            'step_name': '',
            'step_type': 'Seed_Train',
            'start_date': start_date if start_date else date.today().isoformat(),
            'duration': 7,
            'status': 'Pending'
        }

        result = current_steps + [new_step]
        print(f"🔧 Returning {len(result)} steps")
        return result

    # CASE 3: Delete step button clicked
    if triggered_id.startswith('{') and 'delete-step' in triggered_id:
        import json
        triggered_dict = json.loads(triggered_id)
        clicked_index = triggered_dict['index']

        current_steps = store_data if store_data and isinstance(store_data, list) else []

        if clicked_index < len(current_steps):
            new_steps = current_steps[:clicked_index] + current_steps[clicked_index + 1:]

            # Re-index
            for i, step in enumerate(new_steps):
                step['index'] = i

            print(f"🔧 Deleted step at index {clicked_index}, now {len(new_steps)} steps")
            return new_steps

    raise PreventUpdate

# Render process step cards in the modal
@app.callback(
    Output('process-steps-container', 'children'),
    Input('process-steps-store', 'data')
)
def render_process_steps(store_data):
    """Render process step cards from store data"""
    print(f"🎨 RENDER called: type={type(store_data)}, len={len(store_data) if store_data else 0}")
    print(f"🎨 RENDER data: {store_data}")

    # Handle empty or invalid data
    if not store_data or not isinstance(store_data, list) or len(store_data) == 0:
        print("🎨 RENDER: Returning placeholder")
        return html.P("Click 'Add Step' to begin adding process steps",
                     className="text-muted text-center py-4")

    print(f"🎨 RENDER: Creating {len(store_data)} cards")
    # Create a card for each process step
    cards = []
    for step in store_data:
        if isinstance(step, dict) and 'index' in step:
            print(f"🎨 Creating card {step['index']}: {step.get('step_name', 'unnamed')}")
            card = create_process_step_card(step, step['index'])
            cards.append(card)

    print(f"🎨 RENDER: Returning {len(cards)} cards")
    return cards if cards else html.P("Click 'Add Step' to begin adding process steps",
                                     className="text-muted text-center py-4")

# Load experiment options on page load and after creating new experiment
@app.callback(
    Output("main-experiment-select", "options"),
    [Input("alert-container", "children")],  # Refresh after any operation
)
def load_experiment_options(alert):
    """Load all experiments into dropdown"""
    experiments = USPExperiment.objects.all().order_by('-created_date')
    return [
        {'label': f"{exp.experiment_id} - {exp.experiment_name}", 'value': exp.id}
        for exp in experiments
    ]

# Load process steps when experiment selected
@app.callback(
    Output("main-step-select", "options"),
    [Input("main-experiment-select", "value")],
    prevent_initial_call=True
)
def load_process_steps(experiment_id):
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
        print(f"Error loading steps: {e}")
        return []

# ============================================================================
# UNIFIED SEED TRAIN TABLE CALLBACKS
# ============================================================================

# Populate store when experiment selected or "Add Seed Train" clicked
@app.callback(
    [Output("seedtrain-table-data", "data"),
     Output("seedtrain-row-counter", "data")],
    [Input("main-experiment-select", "value"),
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

    if not experiment_id and triggered_id != "add-seedtrain-row-btn":
        return [], 0

    try:
        # When experiment is selected, load all existing seed trains into store
        if triggered_id == "main-experiment-select":
            experiment = USPExperiment.objects.get(id=experiment_id)
            seed_trains = USPSeedTrain.objects.filter(
                process_step__experiment=experiment
            ).select_related('process_step', 'media_prep').order_by('seed_train_id')

            table_data = []
            for st in seed_trains:
                table_data.append({
                    'db_id': st.id,  # Has DB ID = existing record
                    'seed_train_id': st.seed_train_id,
                    'project_id': st.project_id or '',
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
                'project_id': '',
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

        return current_data or [], row_counter

    except Exception as e:
        print(f"Error updating seed train table data: {e}")
        import traceback
        traceback.print_exc()
        return current_data or [], row_counter

# Render table from store data
@app.callback(
    Output("unified-seedtrains-table", "children"),
    [Input("seedtrain-table-data", "data")],
    prevent_initial_call=True
)
def render_seedtrain_table(table_data):
    """Render HTML table from store data"""
    if not table_data:
        return html.P("Select an experiment above to view seed trains, or click 'Add Seed Train' to create new entries",
                     className="text-muted text-center py-5")

    try:
        # Get dropdown options
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

        # Build table header
        table_header = html.Thead(html.Tr([
            html.Th("Action", style={'min-width': '80px'}),
            html.Th("Seed Train ID", style={'min-width': '120px'}),
            html.Th("Project ID", style={'min-width': '120px'}),
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
            html.Th("Discard", style={'min-width': '80px'}),
        ]))

        # Build table rows from store data
        table_rows = []
        for idx, row_data in enumerate(table_data):
            is_existing = row_data.get('db_id') is not None

            row = html.Tr([
                # Action column - delete button only for new rows
                html.Td(
                    dbc.Button(
                        html.I(className="fas fa-trash"),
                        id={'type': 'delete-st-row', 'index': idx},
                        color="danger",
                        size="sm",
                        outline=True
                    ) if not is_existing else ""
                ),

                # Seed Train ID (display only, hidden DB ID)
                html.Td([
                    row_data.get('seed_train_id', 'NEW'),
                    html.Div(row_data.get('db_id', ''), id={'type': 'st-db-id', 'index': idx}, style={'display': 'none'})
                ]),

                # Project ID
                html.Td(dbc.Input(
                    id={'type': 'st-project-id', 'index': idx},
                    type='text',
                    value=row_data.get('project_id', ''),
                    placeholder='e.g., SI-49T5',
                    size='sm'
                )),

                # Cell Line
                html.Td(dbc.Input(
                    id={'type': 'st-cell-line', 'index': idx},
                    type='text',
                    value=row_data.get('cell_line', ''),
                    placeholder='CHO-K1, CHO-S, etc',
                    size='sm'
                )),

                # Clone
                html.Td(dbc.Input(
                    id={'type': 'st-clone', 'index': idx},
                    type='text',
                    value=row_data.get('clone', ''),
                    placeholder='1B2, 25H8, etc',
                    size='sm'
                )),

                # Pool/Clone
                html.Td(dcc.Dropdown(
                    id={'type': 'st-pool-clone', 'index': idx},
                    options=pool_clone_options,
                    value=row_data.get('pool_or_clone') or None,
                    placeholder='Select...',
                    clearable=True,
                    style={'width': '100%'}
                )),

                # Bank Age
                html.Td(dbc.Input(
                    id={'type': 'st-bank-age', 'index': idx},
                    type='text',
                    value=row_data.get('bank_age', ''),
                    placeholder='P4, P5, etc',
                    size='sm'
                )),

                # Passage Number
                html.Td(dbc.Input(
                    id={'type': 'st-passage', 'index': idx},
                    type='number',
                    value=row_data.get('passage_number', ''),
                    placeholder='#',
                    size='sm'
                )),

                # Vessel Type
                html.Td(dcc.Dropdown(
                    id={'type': 'st-vessel-type', 'index': idx},
                    options=vessel_type_options,
                    value=row_data.get('vessel_type') or None,
                    placeholder='Select...',
                    clearable=True,
                    style={'width': '100%'}
                )),

                # Volume
                html.Td(dbc.Input(
                    id={'type': 'st-volume', 'index': idx},
                    type='number',
                    value=row_data.get('start_volume', ''),
                    placeholder='mL',
                    size='sm'
                )),

                # Thaw Date
                html.Td(dcc.DatePickerSingle(
                    id={'type': 'st-thaw-date', 'index': idx},
                    date=row_data.get('thaw_date') or None,
                    display_format='YYYY-MM-DD',
                    style={'width': '100%', 'height': '38px'}
                )),

                # Media Prep
                html.Td(dcc.Dropdown(
                    id={'type': 'st-media-prep', 'index': idx},
                    options=media_options,
                    value=row_data.get('media_prep_id') or None,
                    placeholder='Select media prep...',
                    clearable=True,
                    style={'width': '100%'}
                )),

                # Notes
                html.Td(dbc.Input(
                    id={'type': 'st-notes', 'index': idx},
                    type='text',
                    value=row_data.get('notes', ''),
                    placeholder='Notes',
                    size='sm'
                )),

                # Discard checkbox (only for existing records)
                html.Td(
                    dbc.Checkbox(
                        id={'type': 'st-is-discarded', 'index': idx},
                        value=row_data.get('is_discarded', False)
                    ) if is_existing else ""
                ),
            ], id={'type': 'st-row', 'index': idx})
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

        return table

    except Exception as e:
        print(f"Error rendering seed train table: {e}")
        import traceback
        traceback.print_exc()
        return html.Div([
            dbc.Alert(f"Error rendering table: {str(e)}", color="danger")
        ])

# Delete row callback - removes new rows from store
@app.callback(
    Output("seedtrain-table-data", "data", allow_duplicate=True),
    [Input({'type': 'delete-st-row', 'index': ALL}, 'n_clicks')],
    [State("seedtrain-table-data", "data")],
    prevent_initial_call=True
)
def delete_seedtrain_row(delete_clicks, table_data):
    """Remove new seed train row from store"""
    ctx = dash.callback_context
    if not ctx.triggered or not table_data:
        raise PreventUpdate

    # Find which delete button was clicked
    triggered_id = ctx.triggered[0]['prop_id']
    if '.n_clicks' not in triggered_id:
        raise PreventUpdate

    # Extract index from triggered ID
    import json
    button_id = json.loads(triggered_id.split('.')[0])
    delete_index = button_id['index']

    # Remove row at that index
    updated_data = [row for i, row in enumerate(table_data) if i != delete_index]

    return updated_data

# Save all changes callback - creates new and updates existing seed trains
@app.callback(
    [Output("alert-container", "children"),
     Output("seedtrain-table-data", "data", allow_duplicate=True)],
    [Input("save-all-seedtrains", "n_clicks")],
    [State("main-experiment-select", "value"),
     State("main-step-select", "value"),
     State("main-project-input", "value"),
     State({'type': 'st-db-id', 'index': ALL}, 'children'),
     State({'type': 'st-project-id', 'index': ALL}, 'value'),
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
     State({'type': 'st-is-discarded', 'index': ALL}, 'value')],
    prevent_initial_call=True
)
def save_all_seedtrains(n_clicks, experiment_id, step_id, project, db_ids, project_ids, cell_lines, clones,
                        pool_clones, bank_ages, passages, vessel_types, volumes, thaw_dates,
                        media_prep_ids, notes_list, is_discarded_list):
    """Save all changes - create new seed trains and update existing ones"""
    if not n_clicks:
        raise PreventUpdate

    if not experiment_id or not step_id:
        return dbc.Alert("Please select an experiment and process step", color="danger", duration=4000), no_update

    if not db_ids:
        return dbc.Alert("No seed trains to save", color="warning", duration=3000), no_update

    try:
        created_count = 0
        updated_count = 0
        errors = []

        for i in range(len(db_ids)):
            # Validate required fields
            if not cell_lines[i] or not vessel_types[i] or not thaw_dates[i]:
                errors.append(f"Row {i+1}: Missing required fields (Cell Line, Vessel Type, Thaw Date)")
                continue

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

            # Check if this is an existing record (has DB ID) or new (no DB ID)
            if db_ids[i]:  # Existing record - UPDATE
                try:
                    seed_train = USPSeedTrain.objects.get(id=db_ids[i])

                    # Update all fields
                    seed_train.project_id = project_ids[i] or ""
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
                    seed_train.program = project or ""
                    seed_train.notes = notes_list[i] or ""

                    # Update discard status if provided
                    if i < len(is_discarded_list) and is_discarded_list[i] is not None:
                        seed_train.is_discarded = is_discarded_list[i]
                        if is_discarded_list[i]:
                            seed_train.discard_date = datetime.now()

                    seed_train.save()
                    updated_count += 1

                except Exception as e:
                    errors.append(f"Row {i+1}: Error updating - {str(e)}")
                    print(f"Error updating seed train {db_ids[i]}: {e}")
                    continue

            else:  # New record - CREATE
                try:
                    seed_train_id = generate_seed_train_id()

                    seed_train = USPSeedTrain.objects.create(
                        process_step_id=step_id,
                        seed_train_id=seed_train_id,
                        project_id=project_ids[i] or "",
                        cell_line=cell_lines[i],
                        clone=clones[i] or "",
                        pool_or_clone=pool_clones[i] or "",
                        bank_age=bank_ages[i] or "",
                        passage_number=int(passages[i]) if passages[i] else None,
                        vessel_type=vessel_types[i],
                        start_volume=float(volumes[i]) if volumes[i] else None,
                        thaw_date=pd.to_datetime(thaw_dates[i]).date(),
                        media_prep=media_prep,
                        media_type=media_type,
                        media_lot=media_lot,
                        program=project or "",
                        notes=notes_list[i] or ""
                    )
                    created_count += 1

                except Exception as e:
                    errors.append(f"Row {i+1}: Error creating - {str(e)}")
                    print(f"Error creating seed train: {e}")
                    continue

        # Reload table data from database to reflect changes
        experiment = USPExperiment.objects.get(id=experiment_id)
        seed_trains = USPSeedTrain.objects.filter(
            process_step__experiment=experiment
        ).select_related('process_step', 'media_prep').order_by('seed_train_id')

        table_data = []
        for st in seed_trains:
            table_data.append({
                'db_id': st.id,
                'seed_train_id': st.seed_train_id,
                'project_id': st.project_id or '',
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

        # Build success/error message
        messages = []
        if created_count > 0:
            messages.append(f"Created {created_count} new seed train(s)")
        if updated_count > 0:
            messages.append(f"Updated {updated_count} existing seed train(s)")
        if errors:
            messages.append(f"{len(errors)} error(s) occurred")

        alert_color = "success" if not errors else ("warning" if created_count + updated_count > 0 else "danger")
        alert_message = " | ".join(messages)
        if errors:
            alert_message += "\n" + "\n".join(errors[:3])  # Show first 3 errors

        return dbc.Alert(alert_message, color=alert_color, duration=5000), table_data

    except Exception as e:
        print(f"Error saving seed trains: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Error: {str(e)}", color="danger", duration=5000), no_update

# Create/Update experiment callback
@app.callback(
    [Output("modal-alert-container", "children"),
     Output("alert-container", "children", allow_duplicate=True),
     Output("experiment-modal", "is_open", allow_duplicate=True)],
    [Input("save-experiment-btn", "n_clicks")],
    [State("experiment-id-input", "value"),
     State("project-id-input", "value"),
     State("experiment-name-input", "value"),
     State("experiment-start-date", "date"),
     State("edit-mode", "data"),
     State({'type': 'step-name', 'index': ALL}, 'value'),
     State({'type': 'step-type', 'index': ALL}, 'value'),
     State({'type': 'step-start-date', 'index': ALL}, 'date'),
     State({'type': 'step-duration', 'index': ALL}, 'value'),
     State({'type': 'step-status', 'index': ALL}, 'value')],
    prevent_initial_call=True
)
def save_experiment(n_clicks, exp_id, project_id, exp_name, start_date, edit_mode,
                   step_names, step_types, step_start_dates, step_durations, step_statuses):
    """Create new or update existing experiment with process steps"""
    if not n_clicks:
        raise PreventUpdate

    if not exp_name:
        return (dbc.Alert("Please enter an experiment name", color="danger", duration=3000), no_update, no_update)

    if not step_names or len(step_names) == 0:
        return (dbc.Alert("Please define at least one process step", color="danger", duration=3000), no_update, no_update)

    # Validate that at least one step has a name
    if not any(name.strip() for name in step_names if name):
        return (dbc.Alert("Please enter a name for at least one process step", color="danger", duration=3000), no_update, no_update)

    try:
        # Convert start_date to date object if needed
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date).date()

        if edit_mode:
            # UPDATE existing experiment
            try:
                experiment = USPExperiment.objects.get(experiment_id=exp_id)
                experiment.project_id = project_id or ""
                experiment.experiment_name = exp_name
                experiment.start_date = start_date
                experiment.save()

                # Delete existing process steps and recreate
                experiment.process_steps.all().delete()

                # Create new process steps from pattern-matching inputs
                for i in range(len(step_names)):
                    if step_names[i] and step_names[i].strip():  # Only create if step has a name
                        step_start = pd.to_datetime(step_start_dates[i]).date() if step_start_dates[i] else start_date
                        step_duration = int(step_durations[i]) if step_durations[i] else 7
                        step_status = step_statuses[i] if i < len(step_statuses) and step_statuses[i] else 'Pending'

                        USPProcessStep.objects.create(
                            experiment=experiment,
                            step_name=step_names[i],
                            step_type=step_types[i] if i < len(step_types) else 'Seed_Train',
                            step_order=i + 1,
                            planned_duration_days=step_duration,
                            planned_start_date=step_start,
                            planned_end_date=step_start + timedelta(days=step_duration),
                            status=step_status
                        )

                # Show success message and close modal
                success_alert = dbc.Alert(
                    f"Successfully updated experiment {experiment.experiment_id}!",
                    color="success",
                    duration=4000
                )
                return (no_update, success_alert, False)  # Close modal

            except USPExperiment.DoesNotExist:
                return (dbc.Alert(f"Experiment {exp_id} not found", color="danger", duration=4000), no_update, no_update)

        else:
            # CREATE new experiment
            experiment = USPExperiment.objects.create(
                experiment_id=exp_id or generate_usp_experiment_number(),
                project_id=project_id or "",
                experiment_name=exp_name,
                start_date=start_date,
                status='Active'
            )

            # Create process steps from pattern-matching inputs
            for i in range(len(step_names)):
                if step_names[i] and step_names[i].strip():  # Only create if step has a name
                    step_start = pd.to_datetime(step_start_dates[i]).date() if step_start_dates[i] else start_date
                    step_duration = int(step_durations[i]) if step_durations[i] else 7
                    step_status = step_statuses[i] if i < len(step_statuses) and step_statuses[i] else 'Pending'

                    USPProcessStep.objects.create(
                        experiment=experiment,
                        step_name=step_names[i],
                        step_type=step_types[i] if i < len(step_types) else 'Seed_Train',
                        step_order=i + 1,
                        planned_duration_days=step_duration,
                        planned_start_date=step_start,
                        planned_end_date=step_start + timedelta(days=step_duration),
                        status=step_status
                    )

            # Show success message and close modal
            success_alert = dbc.Alert(
                f"Successfully created experiment {experiment.experiment_id}!",
                color="success",
                duration=4000
            )
            return (no_update, success_alert, False)  # Close modal

    except Exception as e:
        print(f"Error saving experiment: {e}")
        import traceback
        traceback.print_exc()
        error_alert = dbc.Alert(f"Error: {str(e)}", color="danger", duration=5000)
        return (error_alert, no_update, no_update)

# Populate experiments table with Edit buttons
@app.callback(
    Output("experiments-table-container", "children"),
    [Input("alert-container", "children")],  # Update when new experiment created
)
def populate_experiments_table(alert):
    """Show all experiments in a table with Edit buttons"""
    try:
        experiments = USPExperiment.objects.all().order_by('-created_date')

        if not experiments:
            return html.Div([
                html.P("No experiments found. Click 'New Experiment' to create one!",
                       className="text-muted text-center py-5")
            ])

        # Create table rows with View and Edit buttons
        table_rows = []
        for exp in experiments:
            # Count process steps
            steps = USPProcessStep.objects.filter(experiment=exp)
            step_count = steps.count()

            row = html.Tr([
                html.Td([
                    dbc.Button(
                        [html.I(className="fas fa-eye")],
                        id={'type': 'view-experiment-btn', 'index': exp.id},
                        color="info",
                        size="sm",
                        outline=True,
                        title="View Experiment Details"
                    )
                ], style={'textAlign': 'center', 'width': '60px'}),
                html.Td(exp.experiment_id),
                html.Td(exp.project_id or '-'),
                html.Td(exp.experiment_name),
                html.Td(exp.start_date.strftime('%Y-%m-%d') if exp.start_date else '-'),
                html.Td(
                    dbc.Badge(exp.status, color="success" if exp.status == "Active" else "secondary"),
                ),
                html.Td(step_count, style={'textAlign': 'center'}),
                html.Td(exp.created_date.strftime('%Y-%m-%d') if exp.created_date else '-'),
                html.Td([
                    dbc.Button(
                        [html.I(className="fas fa-edit me-1"), "Edit"],
                        id={'type': 'edit-experiment-btn', 'index': exp.id},
                        color="primary",
                        size="sm",
                        outline=True
                    )
                ], style={'textAlign': 'center'}),
            ])
            table_rows.append(row)

        # Create table
        table = dbc.Table([
            html.Thead(html.Tr([
                html.Th("View", style={'textAlign': 'center', 'width': '60px'}),
                html.Th("Experiment ID"),
                html.Th("Project ID"),
                html.Th("Experiment Name"),
                html.Th("Start Date"),
                html.Th("Status"),
                html.Th("Steps", style={'textAlign': 'center'}),
                html.Th("Created"),
                html.Th("Actions", style={'textAlign': 'center'}),
            ])),
            html.Tbody(table_rows)
        ], bordered=True, hover=True, responsive=True, striped=True)

        return table

    except Exception as e:
        print(f"Error loading experiments: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Error loading experiments: {str(e)}", color="danger")

# Render Gantt chart (using original function)
@app.callback(
    Output("gantt-chart", "figure"),
    [Input("main-tabs", "active_tab")],  # Update when switching to overview tab
)
def render_gantt_chart_callback(active_tab):
    """Render Gantt chart using original function"""
    return create_gantt_chart()

# Toggle View All Seed Trains modal
@app.callback(
    Output("viewall-seedtrains-modal", "is_open"),
    [Input("view-all-seedtrains-btn", "n_clicks"),
     Input("close-viewall-modal", "n_clicks")],
    [State("viewall-seedtrains-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_viewall_modal(open_clicks, close_clicks, is_open):
    """Toggle View All Seed Trains modal"""
    return not is_open

# Populate View All Seed Trains DataTable
@app.callback(
    Output("all-seedtrains-datatable", "children"),
    [Input("viewall-seedtrains-modal", "is_open")],
    prevent_initial_call=True
)
def populate_viewall_datatable(is_open):
    """Show all seed trains in a DataTable when modal opens"""
    if not is_open:
        raise PreventUpdate

    try:
        seed_trains = USPSeedTrain.objects.all().select_related('process_step__experiment', 'media_prep').order_by('-created_date')

        if not seed_trains:
            return html.P("No seed trains found in the database.", className="text-muted text-center py-4")

        table_data = []
        for st in seed_trains:
            table_data.append({
                'Seed Train ID': st.seed_train_id,
                'Project ID': st.project_id or '-',
                'Experiment': st.process_step.experiment.experiment_id if st.process_step and st.process_step.experiment else '-',
                'Cell Line': st.cell_line or '-',
                'Clone': st.clone or '-',
                'Pool/Clone': st.pool_or_clone or '-',
                'Vessel Type': st.vessel_type or '-',
                'Volume (mL)': st.start_volume if st.start_volume else '-',
                'Thaw Date': st.thaw_date.strftime('%Y-%m-%d') if st.thaw_date else '-',
                'Media Prep': st.media_prep.media_id if st.media_prep else '-',
                'Status': 'Discarded' if st.is_discarded else 'Active',
                'Created': st.created_date.strftime('%Y-%m-%d') if st.created_date else '-',
            })

        df = pd.DataFrame(table_data)

        return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in df.columns],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '8px',
                'fontSize': '13px',
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'border': '1px solid #dee2e6'
            },
            style_data={
                'border': '1px solid #dee2e6'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                },
                {
                    'if': {
                        'filter_query': '{Status} = "Discarded"',
                    },
                    'backgroundColor': '#ffebee',
                    'color': '#c62828'
                }
            ],
            filter_action="native",
            sort_action="native",
        )

    except Exception as e:
        print(f"Error loading all seed trains: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Error loading seed trains: {str(e)}", color="danger")

# ============================================================================
# FED BATCH CALLBACKS
# ============================================================================

# Load fed batch experiment options
@app.callback(
    Output("fb-experiment-select", "options"),
    [Input("alert-container", "children")],
)
def load_fb_experiment_options(alert):
    """Load all experiments into fed batch dropdown"""
    experiments = USPExperiment.objects.all().order_by('-created_date')
    return [
        {'label': f"{exp.experiment_id} - {exp.experiment_name}", 'value': exp.id}
        for exp in experiments
    ]

# Load fed batch process steps
@app.callback(
    Output("fb-step-select", "options"),
    [Input("fb-experiment-select", "value")],
    prevent_initial_call=True
)
def load_fb_process_steps(experiment_id):
    """Load bioreactor/shake flask process steps for selected experiment"""
    if not experiment_id:
        return []

    try:
        steps = USPProcessStep.objects.filter(
            experiment_id=experiment_id,
            step_type__in=['Bioreactor', 'Shake_Flask']
        ).order_by('step_order')

        return [
            {'label': f"{step.step_name} (Order {step.step_order})", 'value': step.id}
            for step in steps
        ]
    except Exception as e:
        print(f"Error loading fed batch steps: {e}")
        return []

# Populate fed batch store
@app.callback(
    [Output("fedbatch-table-data", "data"),
     Output("fedbatch-row-counter", "data")],
    [Input("fb-experiment-select", "value"),
     Input("add-fedbatch-row-btn", "n_clicks")],
    [State("fedbatch-table-data", "data"),
     State("fedbatch-row-counter", "data")],
    prevent_initial_call=True
)
def update_fedbatch_table_data(experiment_id, add_clicks, current_data, row_counter):
    """Populate store with existing fed batch vessels or add blank row"""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if not experiment_id and triggered_id != "add-fedbatch-row-btn":
        return [], 0

    try:
        # When experiment is selected, load all existing fed batch vessels
        if triggered_id == "fb-experiment-select":
            experiment = USPExperiment.objects.get(id=experiment_id)
            vessels = USPVessel.objects.filter(
                process_step__experiment=experiment
            ).select_related('process_step', 'seed_train', 'media_prep').order_by('vessel_id')

            table_data = []
            for vessel in vessels:
                # Extract probe serial numbers from JSON field
                do_probe_sn = ''
                ph_probe_sn = ''
                if vessel.serial_numbers:
                    do_probe_sn = vessel.serial_numbers.get('do_probe', '')
                    ph_probe_sn = vessel.serial_numbers.get('ph_probe', '')

                table_data.append({
                    'db_id': vessel.id,
                    'vessel_id': vessel.vessel_id,
                    'project_id': vessel.project_id or '',
                    'cell_line': vessel.cell_line or '',
                    'seed_train_id': vessel.seed_train.id if vessel.seed_train else '',
                    'vessel_type': vessel.vessel_type or '',
                    'start_volume': vessel.start_volume if vessel.start_volume is not None else '',
                    'feeding_strategy': vessel.feeding_strategy or '',
                    'inoculation_date': vessel.inoculation_date.isoformat() if vessel.inoculation_date else '',
                    'inoculation_density': vessel.inoculation_density if vessel.inoculation_density is not None else '',
                    'harvest_date': vessel.harvest_date.isoformat() if vessel.harvest_date else '',
                    'temperature': vessel.temperature_setpoint if vessel.temperature_setpoint is not None else '',
                    'ph': vessel.ph_setpoint if vessel.ph_setpoint is not None else '',
                    'do_probe_sn': do_probe_sn,
                    'ph_probe_sn': ph_probe_sn,
                    'notes': vessel.notes or '',
                })

            return table_data, len(table_data)

        # When "Add Fed Batch" clicked, append blank row
        elif triggered_id == "add-fedbatch-row-btn":
            new_row = {
                'db_id': None,
                'vessel_id': 'NEW',
                'project_id': '',
                'cell_line': '',
                'seed_train_id': '',
                'vessel_type': '',
                'start_volume': '',
                'feeding_strategy': '',
                'inoculation_date': '',
                'inoculation_density': '',
                'harvest_date': '',
                'temperature': 37.0,
                'ph': 7.0,
                'do_probe_sn': '',
                'ph_probe_sn': '',
                'notes': '',
            }
            updated_data = current_data + [new_row] if current_data else [new_row]
            return updated_data, row_counter + 1

        return current_data or [], row_counter

    except Exception as e:
        print(f"Error updating fed batch table data: {e}")
        import traceback
        traceback.print_exc()
        return current_data or [], row_counter

# Render fed batch table
@app.callback(
    Output("unified-fedbatch-table", "children"),
    [Input("fedbatch-table-data", "data"),
     Input("fb-experiment-select", "value")],
    prevent_initial_call=True)
def render_fedbatch_table(table_data, experiment_id):
    """Render HTML table for fed batch vessels from store data"""
    if not table_data:
        return html.P("Select an experiment above to view fed batch vessels, or click 'Add Fed Batch Vessel' to create new entries",
                     className="text-muted text-center py-5")

    try:
        # Get seed train options for the selected experiment
        seed_train_options = []
        if experiment_id:
            seed_trains = USPSeedTrain.objects.filter(
                process_step__experiment_id=experiment_id
            ).order_by('seed_train_id')
            seed_train_options = [
                {'label': f"{st.seed_train_id} - {st.cell_line}", 'value': st.id}
                for st in seed_trains
            ]

        vessel_type_options = [
            {'label': '2L Bioreactor', 'value': '2L_BRX'},
            {'label': '5L Bioreactor', 'value': '5L_BRX'},
            {'label': '10L Bioreactor', 'value': '10L_BRX'},
            {'label': '15L Bioreactor', 'value': '15L_BRX'},
            {'label': '250mL Shake Flask', 'value': '250mL_SF'},
            {'label': '500mL Shake Flask', 'value': '500mL_SF'},
            {'label': '1L Shake Flask', 'value': '1L_SF'},
            {'label': '2L Shake Flask', 'value': '2L_SF'},
        ]

        feeding_strategy_options = [
            {'label': 'Platform', 'value': 'Platform'},
            {'label': 'Standard', 'value': 'Standard'},
            {'label': 'Other', 'value': 'Other'},
        ]

        # Build table header
        table_header = html.Thead(html.Tr([
            html.Th("Action", style={'min-width': '80px'}),
            html.Th("Vessel ID", style={'min-width': '120px'}),
            html.Th("Project ID", style={'min-width': '120px'}),
            html.Th("Cell Line *", style={'min-width': '150px'}),
            html.Th("Seed Train *", style={'min-width': '250px'}),
            html.Th("Vessel Type *", style={'min-width': '200px'}),
            html.Th("Volume (mL)", style={'min-width': '110px'}),
            html.Th("Feeding Strategy", style={'min-width': '180px'}),
            html.Th("Inoc. Date *", style={'min-width': '150px'}),
            html.Th("Inoc. Density", style={'min-width': '130px'}),
            html.Th("Harvest Date", style={'min-width': '150px'}),
            html.Th("Temp (°C)", style={'min-width': '100px'}),
            html.Th("pH", style={'min-width': '80px'}),
            html.Th("DO Probe SN", style={'min-width': '130px'}),
            html.Th("pH Probe SN", style={'min-width': '130px'}),
            html.Th("Notes", style={'min-width': '200px'}),
        ]))

        # Build table rows
        table_rows = []
        for idx, row_data in enumerate(table_data):
            is_existing = row_data.get('db_id') is not None

            row = html.Tr([
                # Action column
                html.Td(
                    dbc.Button(
                        html.I(className="fas fa-trash"),
                        id={'type': 'delete-fb-row', 'index': idx},
                        color="danger",
                        size="sm",
                        outline=True
                    ) if not is_existing else ""
                ),

                # Vessel ID
                html.Td([
                    row_data.get('vessel_id', 'NEW'),
                    html.Div(row_data.get('db_id', ''), id={'type': 'fb-db-id', 'index': idx}, style={'display': 'none'})
                ]),

                # Project ID
                html.Td(dbc.Input(
                    id={'type': 'fb-project-id', 'index': idx},
                    type='text',
                    value=row_data.get('project_id', ''),
                    placeholder='e.g., SI-49T5',
                    size='sm'
                )),

                # Cell Line
                html.Td(dbc.Input(
                    id={'type': 'fb-cell-line', 'index': idx},
                    type='text',
                    value=row_data.get('cell_line', ''),
                    placeholder='CHO-K1, CHO-S, etc',
                    size='sm'
                )),

                # Seed Train dropdown
                html.Td(dcc.Dropdown(
                    id={'type': 'fb-seed-train', 'index': idx},
                    options=seed_train_options,
                    value=row_data.get('seed_train_id') or None,
                    placeholder='Select seed train...',
                    clearable=True,
                    style={'width': '100%', 'minWidth': '250px'}
                )),

                # Vessel Type
                html.Td(dcc.Dropdown(
                    id={'type': 'fb-vessel-type', 'index': idx},
                    options=vessel_type_options,
                    value=row_data.get('vessel_type') or None,
                    placeholder='Select...',
                    clearable=True,
                    style={'width': '100%', 'minWidth': '200px'}
                )),

                # Volume
                html.Td(dbc.Input(
                    id={'type': 'fb-volume', 'index': idx},
                    type='number',
                    value=row_data.get('start_volume', ''),
                    placeholder='mL',
                    size='sm'
                )),

                # Feeding Strategy
                html.Td(dcc.Dropdown(
                    id={'type': 'fb-feeding', 'index': idx},
                    options=feeding_strategy_options,
                    value=row_data.get('feeding_strategy') or None,
                    placeholder='Select...',
                    clearable=True,
                    style={'width': '100%', 'minWidth': '180px'}
                )),

                # Inoculation Date
                html.Td(dcc.DatePickerSingle(
                    id={'type': 'fb-inoc-date', 'index': idx},
                    date=row_data.get('inoculation_date') or None,
                    display_format='YYYY-MM-DD',
                    style={'width': '100%', 'height': '38px'}
                )),

                # Inoculation Density
                html.Td(dbc.Input(
                    id={'type': 'fb-inoc-density', 'index': idx},
                    type='number',
                    value=row_data.get('inoculation_density', ''),
                    placeholder='cells/mL',
                    size='sm'
                )),

                # Harvest Date
                html.Td(dcc.DatePickerSingle(
                    id={'type': 'fb-harvest-date', 'index': idx},
                    date=row_data.get('harvest_date') or None,
                    display_format='YYYY-MM-DD',
                    style={'width': '100%', 'height': '38px'}
                )),

                # Temperature
                html.Td(dbc.Input(
                    id={'type': 'fb-temp', 'index': idx},
                    type='number',
                    step=0.1,
                    value=row_data.get('temperature', 37.0),
                    size='sm'
                )),

                # pH
                html.Td(dbc.Input(
                    id={'type': 'fb-ph', 'index': idx},
                    type='number',
                    step=0.1,
                    value=row_data.get('ph', 7.0),
                    size='sm'
                )),

                # DO Probe Serial Number
                html.Td(dbc.Input(
                    id={'type': 'fb-do-probe', 'index': idx},
                    type='text',
                    value=row_data.get('do_probe_sn', ''),
                    placeholder='DO Probe SN',
                    size='sm'
                )),

                # pH Probe Serial Number
                html.Td(dbc.Input(
                    id={'type': 'fb-ph-probe', 'index': idx},
                    type='text',
                    value=row_data.get('ph_probe_sn', ''),
                    placeholder='pH Probe SN',
                    size='sm'
                )),

                # Notes
                html.Td(dbc.Input(
                    id={'type': 'fb-notes', 'index': idx},
                    type='text',
                    value=row_data.get('notes', ''),
                    placeholder='Notes',
                    size='sm'
                )),
            ], id={'type': 'fb-row', 'index': idx})
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

        return table

    except Exception as e:
        print(f"Error rendering fed batch table: {e}")
        import traceback
        traceback.print_exc()
        return html.Div([
            dbc.Alert(f"Error rendering table: {str(e)}", color="danger")
        ])

# Delete fed batch row
@app.callback(
    Output("fedbatch-table-data", "data", allow_duplicate=True),
    [Input({'type': 'delete-fb-row', 'index': ALL}, 'n_clicks')],
    [State("fedbatch-table-data", "data")],
    prevent_initial_call=True
)
def delete_fedbatch_row(delete_clicks, table_data):
    """Remove new fed batch row from store"""
    ctx = dash.callback_context
    if not ctx.triggered or not table_data:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id']
    if '.n_clicks' not in triggered_id:
        raise PreventUpdate

    import json
    button_id = json.loads(triggered_id.split('.')[0])
    delete_index = button_id['index']

    updated_data = [row for i, row in enumerate(table_data) if i != delete_index]

    return updated_data

# Save all fed batch changes
@app.callback(
    [Output("alert-container", "children", allow_duplicate=True),
     Output("fedbatch-table-data", "data", allow_duplicate=True)],
    [Input("save-all-fedbatch", "n_clicks")],
    [State("fb-experiment-select", "value"),
     State("fb-step-select", "value"),
     State({'type': 'fb-db-id', 'index': ALL}, 'children'),
     State({'type': 'fb-project-id', 'index': ALL}, 'value'),
     State({'type': 'fb-cell-line', 'index': ALL}, 'value'),
     State({'type': 'fb-seed-train', 'index': ALL}, 'value'),
     State({'type': 'fb-vessel-type', 'index': ALL}, 'value'),
     State({'type': 'fb-volume', 'index': ALL}, 'value'),
     State({'type': 'fb-feeding', 'index': ALL}, 'value'),
     State({'type': 'fb-inoc-date', 'index': ALL}, 'date'),
     State({'type': 'fb-inoc-density', 'index': ALL}, 'value'),
     State({'type': 'fb-harvest-date', 'index': ALL}, 'date'),
     State({'type': 'fb-temp', 'index': ALL}, 'value'),
     State({'type': 'fb-ph', 'index': ALL}, 'value'),
     State({'type': 'fb-do-probe', 'index': ALL}, 'value'),
     State({'type': 'fb-ph-probe', 'index': ALL}, 'value'),
     State({'type': 'fb-notes', 'index': ALL}, 'value')],
    prevent_initial_call=True
)
def save_all_fedbatch(n_clicks, experiment_id, step_id, db_ids, project_ids, cell_lines, seed_trains, vessel_types,
                      volumes, feedings, inoc_dates, inoc_densities, harvest_dates, temps, phs, do_probes, ph_probes, notes_list):
    """Save all fed batch changes - create new and update existing"""
    if not n_clicks:
        raise PreventUpdate

    if not experiment_id or not step_id:
        return dbc.Alert("Please select an experiment and process step", color="danger", duration=4000), no_update

    if not db_ids:
        return dbc.Alert("No fed batch vessels to save", color="warning", duration=3000), no_update

    try:
        created_count = 0
        updated_count = 0
        errors = []

        for i in range(len(db_ids)):
            # Validate required fields
            if not vessel_types[i] or not inoc_dates[i]:
                errors.append(f"Row {i+1}: Missing required fields (Vessel Type, Inoculation Date)")
                continue

            # Get seed train if selected
            seed_train = None
            cell_line = ""
            if seed_trains[i]:
                try:
                    seed_train = USPSeedTrain.objects.get(id=seed_trains[i])
                    cell_line = seed_train.cell_line
                except:
                    pass

            # Check if this is an existing record or new
            if db_ids[i]:  # Existing record - UPDATE
                try:
                    vessel = USPVessel.objects.get(id=db_ids[i])

                    vessel.project_id = project_ids[i] or ""
                    vessel.seed_train = seed_train
                    vessel.cell_line = cell_lines[i] or cell_line
                    vessel.vessel_type = vessel_types[i]
                    vessel.start_volume = float(volumes[i]) if volumes[i] else None
                    vessel.feeding_strategy = feedings[i] or ""
                    vessel.inoculation_date = pd.to_datetime(inoc_dates[i]).date()
                    vessel.inoculation_density = float(inoc_densities[i]) if inoc_densities[i] else None
                    vessel.harvest_date = pd.to_datetime(harvest_dates[i]).date() if harvest_dates[i] else None
                    vessel.temperature_setpoint = float(temps[i]) if temps[i] else 37.0
                    vessel.ph_setpoint = float(phs[i]) if phs[i] else 7.0
                    vessel.notes = notes_list[i] or ""

                    # Update serial numbers JSON field
                    serial_numbers = {}
                    if do_probes[i]:
                        serial_numbers['do_probe'] = do_probes[i]
                    if ph_probes[i]:
                        serial_numbers['ph_probe'] = ph_probes[i]
                    vessel.serial_numbers = serial_numbers if serial_numbers else None

                    vessel.save()
                    updated_count += 1

                except Exception as e:
                    errors.append(f"Row {i+1}: Error updating - {str(e)}")
                    print(f"Error updating vessel {db_ids[i]}: {e}")
                    continue

            else:  # New record - CREATE
                try:
                    vessel_id = generate_fed_batch_id()

                    # Build serial numbers JSON
                    serial_numbers = {}
                    if do_probes[i]:
                        serial_numbers['do_probe'] = do_probes[i]
                    if ph_probes[i]:
                        serial_numbers['ph_probe'] = ph_probes[i]

                    vessel = USPVessel.objects.create(
                        process_step_id=step_id,
                        seed_train=seed_train,
                        vessel_id=vessel_id,
                        project_id=project_ids[i] or "",
                        cell_line=cell_lines[i] or cell_line,
                        vessel_type=vessel_types[i],
                        start_volume=float(volumes[i]) if volumes[i] else None,
                        feeding_strategy=feedings[i] or "",
                        inoculation_date=pd.to_datetime(inoc_dates[i]).date(),
                        inoculation_density=float(inoc_densities[i]) if inoc_densities[i] else None,
                        harvest_date=pd.to_datetime(harvest_dates[i]).date() if harvest_dates[i] else None,
                        temperature_setpoint=float(temps[i]) if temps[i] else 37.0,
                        ph_setpoint=float(phs[i]) if phs[i] else 7.0,
                        serial_numbers=serial_numbers if serial_numbers else None,
                        notes=notes_list[i] or ""
                    )
                    created_count += 1

                except Exception as e:
                    errors.append(f"Row {i+1}: Error creating - {str(e)}")
                    print(f"Error creating vessel: {e}")
                    continue

        # Reload table data from database
        experiment = USPExperiment.objects.get(id=experiment_id)
        vessels = USPVessel.objects.filter(
            process_step__experiment=experiment
        ).select_related('process_step', 'seed_train', 'media_prep').order_by('vessel_id')

        table_data = []
        for vessel in vessels:
            # Extract probe serial numbers from JSON field
            do_probe_sn = ''
            ph_probe_sn = ''
            if vessel.serial_numbers:
                do_probe_sn = vessel.serial_numbers.get('do_probe', '')
                ph_probe_sn = vessel.serial_numbers.get('ph_probe', '')

            table_data.append({
                'db_id': vessel.id,
                'vessel_id': vessel.vessel_id,
                'project_id': vessel.project_id or '',
                'cell_line': vessel.cell_line or '',
                'seed_train_id': vessel.seed_train.id if vessel.seed_train else '',
                'vessel_type': vessel.vessel_type or '',
                'start_volume': vessel.start_volume if vessel.start_volume is not None else '',
                'feeding_strategy': vessel.feeding_strategy or '',
                'inoculation_date': vessel.inoculation_date.isoformat() if vessel.inoculation_date else '',
                'inoculation_density': vessel.inoculation_density if vessel.inoculation_density is not None else '',
                'harvest_date': vessel.harvest_date.isoformat() if vessel.harvest_date else '',
                'temperature': vessel.temperature_setpoint if vessel.temperature_setpoint is not None else '',
                'ph': vessel.ph_setpoint if vessel.ph_setpoint is not None else '',
                'do_probe_sn': do_probe_sn,
                'ph_probe_sn': ph_probe_sn,
                'notes': vessel.notes or '',
            })

        # Build success/error message
        messages = []
        if created_count > 0:
            messages.append(f"Created {created_count} new vessel(s)")
        if updated_count > 0:
            messages.append(f"Updated {updated_count} existing vessel(s)")
        if errors:
            messages.append(f"{len(errors)} error(s) occurred")

        alert_color = "success" if not errors else ("warning" if created_count + updated_count > 0 else "danger")
        alert_message = " | ".join(messages)
        if errors:
            alert_message += "\n" + "\n".join(errors[:3])

        return dbc.Alert(alert_message, color=alert_color, duration=5000), table_data

    except Exception as e:
        print(f"Error saving fed batch vessels: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Error: {str(e)}", color="danger", duration=5000), no_update

# Toggle View All Fed Batch modal
@app.callback(
    Output("viewall-fedbatch-modal", "is_open"),
    [Input("view-all-fedbatch-btn", "n_clicks"),
     Input("close-viewall-fb-modal", "n_clicks")],
    [State("viewall-fedbatch-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_viewall_fb_modal(open_clicks, close_clicks, is_open):
    """Toggle View All Fed Batch modal"""
    return not is_open

# Populate View All Fed Batch DataTable
@app.callback(
    Output("all-fedbatch-datatable", "children"),
    [Input("viewall-fedbatch-modal", "is_open")],
    prevent_initial_call=True
)
def populate_viewall_fb_datatable(is_open):
    """Show all fed batch vessels in a DataTable when modal opens"""
    if not is_open:
        raise PreventUpdate

    try:
        vessels = USPVessel.objects.all().select_related('process_step__experiment', 'seed_train').order_by('-id')

        if not vessels:
            return html.P("No fed batch vessels found in the database.", className="text-muted text-center py-4")

        table_data = []
        for v in vessels:
            # Get project_id and cell_line from vessel first, fallback to seed train
            project_id = v.project_id if v.project_id else (v.seed_train.project_id if v.seed_train and v.seed_train.project_id else '-')
            cell_line = v.cell_line if v.cell_line else (v.seed_train.cell_line if v.seed_train and v.seed_train.cell_line else '-')

            table_data.append({
                'Vessel ID': v.vessel_id,
                'Project ID': project_id,
                'Cell Line': cell_line,
                'Experiment': v.process_step.experiment.experiment_id if v.process_step and v.process_step.experiment else '-',
                'Seed Train': v.seed_train.seed_train_id if v.seed_train else '-',
                'Vessel Type': v.vessel_type or '-',
                'Volume (mL)': v.start_volume if v.start_volume else '-',
                'Feeding': v.feeding_strategy or '-',
                'Inoc. Date': v.inoculation_date.strftime('%Y-%m-%d') if v.inoculation_date else '-',
                'Harvest Date': v.harvest_date.strftime('%Y-%m-%d') if v.harvest_date else '-',
                'Temp (°C)': v.temperature_setpoint if v.temperature_setpoint else '-',
                'pH': v.ph_setpoint if v.ph_setpoint else '-',
            })

        df = pd.DataFrame(table_data)

        return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in df.columns],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '8px',
                'fontSize': '13px',
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'border': '1px solid #dee2e6'
            },
            style_data={
                'border': '1px solid #dee2e6'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ],
            filter_action="native",
            sort_action="native",
        )

    except Exception as e:
        print(f"Error loading all fed batch vessels: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Error loading vessels: {str(e)}", color="danger")

# ============================================================================
# CELL BANK CALLBACKS
# ============================================================================

# Load cell bank experiment options
@app.callback(
    Output("cb-experiment-select", "options"),
    [Input("alert-container", "children")],
)
def load_cb_experiment_options(alert):
    """Load all experiments into cell bank dropdown"""
    experiments = USPExperiment.objects.all().order_by('-created_date')
    return [
        {'label': f"{exp.experiment_id} - {exp.experiment_name}", 'value': exp.id}
        for exp in experiments
    ]

# Load cell bank process steps
@app.callback(
    Output("cb-step-select", "options"),
    [Input("cb-experiment-select", "value")],
    prevent_initial_call=True
)
def load_cb_process_steps(experiment_id):
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
        print(f"Error loading cell bank steps: {e}")
        return []

# Populate cell bank store
@app.callback(
    [Output("cellbank-table-data", "data"),
     Output("cellbank-row-counter", "data")],
    [Input("cb-experiment-select", "value"),
     Input("add-cellbank-row-btn", "n_clicks")],
    [State("cellbank-table-data", "data"),
     State("cellbank-row-counter", "data")],
    prevent_initial_call=True
)
def update_cellbank_table_data(experiment_id, add_clicks, current_data, row_counter):
    """Populate store with existing cell banks or add blank row"""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if not experiment_id and triggered_id != "add-cellbank-row-btn":
        return [], 0

    try:
        # When experiment is selected, load all existing cell banks
        if triggered_id == "cb-experiment-select":
            experiment = USPExperiment.objects.get(id=experiment_id)
            cell_banks = USPCellBank.objects.filter(
                seed_train_source__process_step__experiment=experiment
            ).select_related('seed_train_source').order_by('cell_bank_id')

            table_data = []
            for cb in cell_banks:
                # Calculate bank age in days from banking_date to today
                bank_age_days = ''
                if cb.banking_date:
                    days_diff = (date.today() - cb.banking_date).days
                    bank_age_days = days_diff

                table_data.append({
                    'db_id': cb.id,
                    'cell_bank_id': cb.cell_bank_id,
                    'seed_train_id': cb.seed_train_source.id if cb.seed_train_source else '',
                    'density': cb.density if cb.density is not None else '',
                    'number_of_vials': cb.number_of_vials if cb.number_of_vials is not None else '',
                    'media': cb.media or '',
                    'banking_date': cb.banking_date.isoformat() if cb.banking_date else '',
                    'bank_age_days': bank_age_days,
                    'bank_age_notes': cb.bank_age_notes or '',
                    'ln2_location': cb.ln2_location or '',
                    'notes': cb.notes or '',
                })

            return table_data, len(table_data)

        # When "Add Cell Bank" clicked, append blank row
        elif triggered_id == "add-cellbank-row-btn":
            new_row = {
                'db_id': None,
                'cell_bank_id': 'NEW',
                'seed_train_id': '',
                'density': '',
                'number_of_vials': '',
                'media': '',
                'banking_date': '',
                'bank_age_days': '',
                'bank_age_notes': '',
                'ln2_location': '',
                'notes': '',
            }
            updated_data = current_data + [new_row] if current_data else [new_row]
            return updated_data, row_counter + 1

        return current_data or [], row_counter

    except Exception as e:
        print(f"Error updating cell bank table data: {e}")
        import traceback
        traceback.print_exc()
        return current_data or [], row_counter

# Render cell bank table
@app.callback(
    Output("unified-cellbank-table", "children"),
    [Input("cellbank-table-data", "data"),
     Input("cb-experiment-select", "value")],
    prevent_initial_call=True
)
def render_cellbank_table(table_data, experiment_id):
    """Render HTML table for cell banks from store data"""
    if not table_data:
        return html.P("Select an experiment above to view cell banks, or click 'Add Cell Bank' to create new entries",
                     className="text-muted text-center py-5")

    try:
        # Get seed train options for the selected experiment
        seed_train_options = []
        if experiment_id:
            seed_trains = USPSeedTrain.objects.filter(
                process_step__experiment_id=experiment_id
            ).order_by('seed_train_id')
            seed_train_options = [
                {'label': f"{st.seed_train_id} - {st.cell_line}", 'value': st.id}
                for st in seed_trains
            ]

        # Build table header
        table_header = html.Thead(html.Tr([
            html.Th("Action", style={'min-width': '80px'}),
            html.Th("Cell Bank ID", style={'min-width': '120px'}),
            html.Th("Seed Train Source *", style={'min-width': '200px'}),
            html.Th("Density (cells/mL) *", style={'min-width': '150px'}),
            html.Th("Number of Vials *", style={'min-width': '120px'}),
            html.Th("Media *", style={'min-width': '200px'}),
            html.Th("Banking Date *", style={'min-width': '150px'}),
            html.Th("Bank Age (Days)", style={'min-width': '120px'}),
            html.Th("Bank Age Notes", style={'min-width': '200px'}),
            html.Th("LN2 Location", style={'min-width': '150px'}),
            html.Th("Notes", style={'min-width': '200px'}),
        ]))

        # Build table rows
        table_rows = []
        for idx, row in enumerate(table_data):
            table_rows.append(html.Tr([
                # Delete button
                html.Td([
                    dbc.Button(
                        html.I(className="fas fa-trash"),
                        id={'type': 'delete-cb-row', 'index': idx},
                        color="danger",
                        size="sm",
                        outline=True
                    )
                ]),
                # Cell Bank ID (hidden db_id)
                html.Td([
                    html.Span(row['cell_bank_id'], className="badge bg-primary"),
                    html.Div(row['db_id'], id={'type': 'cb-db-id', 'index': idx}, style={'display': 'none'})
                ]),
                # Seed Train Source dropdown
                html.Td([
                    dcc.Dropdown(
                        id={'type': 'cb-seed-train', 'index': idx},
                        options=seed_train_options,
                        value=row['seed_train_id'],
                        placeholder="Select seed train",
                        clearable=False
                    )
                ]),
                # Density
                html.Td([
                    dbc.Input(
                        id={'type': 'cb-density', 'index': idx},
                        type="number",
                        value=row['density'],
                        placeholder="e.g., 1.0E+07",
                        step="any"
                    )
                ]),
                # Number of Vials
                html.Td([
                    dbc.Input(
                        id={'type': 'cb-vials', 'index': idx},
                        type="number",
                        value=row['number_of_vials'],
                        placeholder="e.g., 4"
                    )
                ]),
                # Media
                html.Td([
                    dbc.Input(
                        id={'type': 'cb-media', 'index': idx},
                        type="text",
                        value=row['media'],
                        placeholder="e.g., CHO MaxX + 10% DMSO"
                    )
                ]),
                # Banking Date
                html.Td([
                    dcc.DatePickerSingle(
                        id={'type': 'cb-banking-date', 'index': idx},
                        date=row['banking_date'] if row['banking_date'] else None,
                        display_format='YYYY-MM-DD',
                        placeholder='Select date',
                        style={'width': '100%', 'height': '38px'}
                    )
                ]),
                # Bank Age (Days) - Calculated field, read-only
                html.Td([
                    dbc.Input(
                        id={'type': 'cb-age-days', 'index': idx},
                        type="text",
                        value=row['bank_age_days'] if row['bank_age_days'] else '',
                        disabled=True,
                        className="bg-light"
                    )
                ]),
                # Bank Age Notes
                html.Td([
                    dbc.Textarea(
                        id={'type': 'cb-age-notes', 'index': idx},
                        value=row['bank_age_notes'],
                        placeholder="Age notes",
                        style={'minHeight': '60px'}
                    )
                ]),
                # LN2 Location
                html.Td([
                    dbc.Input(
                        id={'type': 'cb-ln2-location', 'index': idx},
                        type="text",
                        value=row['ln2_location'],
                        placeholder="Storage location"
                    )
                ]),
                # Notes
                html.Td([
                    dbc.Textarea(
                        id={'type': 'cb-notes', 'index': idx},
                        value=row['notes'],
                        placeholder="Additional notes",
                        style={'minHeight': '60px'}
                    )
                ]),
            ]))

        table_body = html.Tbody(table_rows)

        return dbc.Table(
            [table_header, table_body],
            bordered=True,
            hover=True,
            responsive=True,
            striped=True,
            className="table-sm"
        )

    except Exception as e:
        print(f"Error rendering cell bank table: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Error rendering table: {str(e)}", color="danger")

# Delete cell bank row
@app.callback(
    Output("cellbank-table-data", "data", allow_duplicate=True),
    [Input({'type': 'delete-cb-row', 'index': ALL}, 'n_clicks')],
    [State("cellbank-table-data", "data")],
    prevent_initial_call=True
)
def delete_cellbank_row(n_clicks_list, table_data):
    """Remove a row from the cell bank table"""
    if not any(n_clicks_list) or not table_data:
        raise PreventUpdate

    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id']

    if 'delete-cb-row' not in triggered_id:
        raise PreventUpdate

    button_id = json.loads(triggered_id.split('.')[0])
    delete_index = button_id['index']

    updated_data = [row for i, row in enumerate(table_data) if i != delete_index]

    return updated_data

# Save all cell bank changes
@app.callback(
    [Output("alert-container", "children", allow_duplicate=True),
     Output("cellbank-table-data", "data", allow_duplicate=True)],
    [Input("save-all-cellbanks", "n_clicks")],
    [State("cb-experiment-select", "value"),
     State("cb-step-select", "value"),
     State({'type': 'cb-db-id', 'index': ALL}, 'children'),
     State({'type': 'cb-seed-train', 'index': ALL}, 'value'),
     State({'type': 'cb-density', 'index': ALL}, 'value'),
     State({'type': 'cb-vials', 'index': ALL}, 'value'),
     State({'type': 'cb-media', 'index': ALL}, 'value'),
     State({'type': 'cb-banking-date', 'index': ALL}, 'date'),
     State({'type': 'cb-age-days', 'index': ALL}, 'value'),
     State({'type': 'cb-age-notes', 'index': ALL}, 'value'),
     State({'type': 'cb-ln2-location', 'index': ALL}, 'value'),
     State({'type': 'cb-notes', 'index': ALL}, 'value')],
    prevent_initial_call=True
)
def save_all_cellbank(n_clicks, experiment_id, step_id, db_ids, seed_trains, densities,
                      vials, medias, banking_dates, age_days, age_notes, ln2_locations, notes_list):
    """Save all cell bank changes - create new and update existing"""
    if not n_clicks:
        raise PreventUpdate

    if not experiment_id or not step_id:
        return dbc.Alert("Please select an experiment and process step", color="danger", duration=4000), no_update

    if not db_ids:
        return dbc.Alert("No cell banks to save", color="warning", duration=3000), no_update

    try:
        created_count = 0
        updated_count = 0
        errors = []

        for i in range(len(db_ids)):
            # Validate required fields
            if not seed_trains[i] or not densities[i] or not vials[i] or not medias[i] or not banking_dates[i]:
                errors.append(f"Row {i+1}: Missing required fields")
                continue

            # Get seed train
            try:
                seed_train = USPSeedTrain.objects.get(id=seed_trains[i])
            except USPSeedTrain.DoesNotExist:
                errors.append(f"Row {i+1}: Invalid seed train selected")
                continue

            # Check if this is an existing record or new
            if db_ids[i]:  # Existing record - UPDATE
                try:
                    cell_bank = USPCellBank.objects.get(id=db_ids[i])

                    cell_bank.seed_train_source = seed_train
                    cell_bank.density = float(densities[i])
                    cell_bank.number_of_vials = int(vials[i])
                    cell_bank.media = medias[i]
                    cell_bank.banking_date = pd.to_datetime(banking_dates[i]).date()
                    cell_bank.bank_age_days = int(age_days[i]) if age_days[i] else None
                    cell_bank.bank_age_notes = age_notes[i] or ""
                    cell_bank.ln2_location = ln2_locations[i] or ""
                    cell_bank.notes = notes_list[i] or ""

                    cell_bank.save()
                    updated_count += 1

                except Exception as e:
                    errors.append(f"Row {i+1}: Error updating - {str(e)}")
                    print(f"Error updating cell bank {db_ids[i]}: {e}")
                    continue

            else:  # New record - CREATE
                try:
                    cell_bank_id = generate_cell_bank_id()

                    cell_bank = USPCellBank.objects.create(
                        cell_bank_id=cell_bank_id,
                        seed_train_source=seed_train,
                        density=float(densities[i]),
                        number_of_vials=int(vials[i]),
                        media=medias[i],
                        banking_date=pd.to_datetime(banking_dates[i]).date(),
                        bank_age_days=int(age_days[i]) if age_days[i] else None,
                        bank_age_notes=age_notes[i] or "",
                        ln2_location=ln2_locations[i] or "",
                        notes=notes_list[i] or ""
                    )
                    created_count += 1

                except Exception as e:
                    errors.append(f"Row {i+1}: Error creating - {str(e)}")
                    print(f"Error creating cell bank: {e}")
                    continue

        # Reload table data from database
        experiment = USPExperiment.objects.get(id=experiment_id)
        cell_banks = USPCellBank.objects.filter(
            seed_train_source__process_step__experiment=experiment
        ).select_related('seed_train_source').order_by('cell_bank_id')

        table_data = []
        for cb in cell_banks:
            table_data.append({
                'db_id': cb.id,
                'cell_bank_id': cb.cell_bank_id,
                'seed_train_id': cb.seed_train_source.id if cb.seed_train_source else '',
                'density': cb.density if cb.density is not None else '',
                'number_of_vials': cb.number_of_vials if cb.number_of_vials is not None else '',
                'media': cb.media or '',
                'banking_date': cb.banking_date.isoformat() if cb.banking_date else '',
                'bank_age_days': cb.bank_age_days if cb.bank_age_days is not None else '',
                'bank_age_notes': cb.bank_age_notes or '',
                'ln2_location': cb.ln2_location or '',
                'notes': cb.notes or '',
            })

        # Build success/error message
        messages = []
        if created_count > 0:
            messages.append(f"✓ Created {created_count} cell bank(s)")
        if updated_count > 0:
            messages.append(f"✓ Updated {updated_count} cell bank(s)")

        alert_color = "success" if not errors else ("warning" if created_count + updated_count > 0 else "danger")
        alert_message = " | ".join(messages)
        if errors:
            alert_message += "\n" + "\n".join(errors[:3])

        return dbc.Alert(alert_message, color=alert_color, duration=5000), table_data

    except Exception as e:
        print(f"Error saving cell banks: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Error: {str(e)}", color="danger", duration=5000), no_update

# Toggle View All Cell Banks modal
@app.callback(
    Output("viewall-cellbanks-modal", "is_open"),
    [Input("view-all-cellbanks-btn", "n_clicks"),
     Input("close-viewall-cb-modal", "n_clicks")],
    [State("viewall-cellbanks-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_viewall_cb_modal(open_clicks, close_clicks, is_open):
    """Toggle View All Cell Banks modal"""
    return not is_open

# Populate View All Cell Banks DataTable
@app.callback(
    Output("all-cellbanks-datatable", "children"),
    [Input("viewall-cellbanks-modal", "is_open")],
    prevent_initial_call=True
)
def populate_viewall_cb_datatable(is_open):
    """Show all cell banks in a DataTable when modal opens"""
    if not is_open:
        raise PreventUpdate

    try:
        cell_banks = USPCellBank.objects.all().select_related('seed_train_source__process_step__experiment').order_by('-id')

        if not cell_banks:
            return html.P("No cell banks found in the database.", className="text-muted text-center py-4")

        table_data = []
        for cb in cell_banks:
            table_data.append({
                'Cell Bank ID': cb.cell_bank_id,
                'Seed Train': cb.seed_train_source.seed_train_id if cb.seed_train_source else '-',
                'Experiment': cb.seed_train_source.process_step.experiment.experiment_id if cb.seed_train_source and cb.seed_train_source.process_step and cb.seed_train_source.process_step.experiment else '-',
                'Density (cells/mL)': cb.density if cb.density else '-',
                'Vials': cb.number_of_vials if cb.number_of_vials else '-',
                'Media': cb.media or '-',
                'Banking Date': cb.banking_date.strftime('%Y-%m-%d') if cb.banking_date else '-',
                'Bank Age (Days)': cb.bank_age_days if cb.bank_age_days else '-',
                'LN2 Location': cb.ln2_location or '-',
            })

        df = pd.DataFrame(table_data)

        return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in df.columns],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '8px',
                'fontSize': '13px',
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'border': '1px solid #dee2e6'
            },
            style_data={
                'border': '1px solid #dee2e6'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ],
            filter_action="native",
            sort_action="native",
        )

    except Exception as e:
        print(f"Error loading all cell banks: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Error loading cell banks: {str(e)}", color="danger")

# ============================================================================
# VIEW EXPERIMENT CALLBACKS
# ============================================================================

# Toggle View Experiment Modal
@app.callback(
    [Output("view-experiment-modal", "is_open"),
     Output("view-experiment-id", "data")],
    [Input({'type': 'view-experiment-btn', 'index': ALL}, "n_clicks"),
     Input("close-view-experiment-modal", "n_clicks")],
    [State("view-experiment-modal", "is_open"),
     State({'type': 'view-experiment-btn', 'index': ALL}, "id")],
    prevent_initial_call=True
)
def toggle_view_experiment_modal(view_clicks, close_click, is_open, button_ids):
    """Toggle View Experiment modal and store experiment ID"""
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id']

    # Close button clicked
    if 'close-view-experiment-modal' in trigger_id:
        return False, None

    # View button clicked
    if view_clicks and any(view_clicks):
        # Find which button was clicked
        clicked_index = next((i for i, clicks in enumerate(view_clicks) if clicks), None)
        if clicked_index is not None:
            experiment_id = button_ids[clicked_index]['index']
            return True, experiment_id

    return is_open, no_update

# Populate View Experiment Modal Content
@app.callback(
    [Output("view-experiment-modal-title", "children"),
     Output("view-exp-id", "children"),
     Output("view-exp-project-id", "children"),
     Output("view-exp-status", "children"),
     Output("view-exp-start-date", "children"),
     Output("view-exp-name", "children"),
     Output("view-exp-description", "children"),
     Output("view-exp-seed-trains-table", "children"),
     Output("view-exp-vessels-table", "children"),
     Output("view-exp-lims-results-table", "children")],
    [Input("view-experiment-id", "data")],
    prevent_initial_call=True
)
def populate_view_experiment_modal(experiment_id):
    """Populate the View Experiment modal with experiment details"""
    if not experiment_id:
        raise PreventUpdate

    try:
        # Get experiment
        experiment = USPExperiment.objects.get(id=experiment_id)

        # Basic experiment info
        title = f"Experiment Details: {experiment.experiment_id}"
        exp_id = experiment.experiment_id
        project_id = experiment.project_id or "-"
        status = dbc.Badge(experiment.status, color="success" if experiment.status == "Complete" else "info")
        start_date = experiment.start_date.strftime('%Y-%m-%d') if experiment.start_date else "-"
        name = experiment.experiment_name
        description = experiment.description or "No description provided"

        # Get all seed trains for this experiment
        seed_trains = USPSeedTrain.objects.filter(
            process_step__experiment=experiment
        ).select_related('process_step', 'media_prep').order_by('seed_train_id')

        if seed_trains.exists():
            seed_train_rows = []
            for st in seed_trains:
                seed_train_rows.append(html.Tr([
                    html.Td(st.seed_train_id),
                    html.Td(st.project_id or '-'),
                    html.Td(st.cell_line or '-'),
                    html.Td(st.vessel_type or '-'),
                    html.Td(f"{st.start_volume:.1f}" if st.start_volume else '-'),
                    html.Td(st.thaw_date.strftime('%Y-%m-%d') if st.thaw_date else '-'),
                    html.Td(st.media_type or '-'),
                    html.Td(f"{st.viability_at_thaw:.1f}%" if st.viability_at_thaw else '-'),
                ]))

            seed_trains_table = dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Seed Train ID"),
                    html.Th("Project ID"),
                    html.Th("Cell Line"),
                    html.Th("Vessel Type"),
                    html.Th("Volume (mL)"),
                    html.Th("Thaw Date"),
                    html.Th("Media Type"),
                    html.Th("Viability"),
                ])),
                html.Tbody(seed_train_rows)
            ], bordered=True, hover=True, responsive=True, striped=True, size='sm')
        else:
            seed_trains_table = html.P("No seed trains found for this experiment.", className="text-muted")

        # Get all vessels (fed batches) for this experiment
        vessels = USPVessel.objects.filter(
            process_step__experiment=experiment
        ).select_related('process_step', 'seed_train', 'media_prep').order_by('vessel_id')

        if vessels.exists():
            vessel_rows = []
            for v in vessels:
                vessel_rows.append(html.Tr([
                    html.Td(v.vessel_id),
                    html.Td(v.project_id or '-'),
                    html.Td(v.cell_line or '-'),
                    html.Td(v.vessel_type or '-'),
                    html.Td(f"{v.start_volume:.1f}" if v.start_volume else '-'),
                    html.Td(v.inoculation_date.strftime('%Y-%m-%d') if v.inoculation_date else '-'),
                    html.Td(v.harvest_date.strftime('%Y-%m-%d') if v.harvest_date else '-'),
                    html.Td(f"{v.harvest_viability:.1f}%" if v.harvest_viability else '-'),
                    html.Td(f"{v.harvest_vcd:.2e}" if v.harvest_vcd else '-'),
                ]))

            vessels_table = dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Vessel ID"),
                    html.Th("Project ID"),
                    html.Th("Cell Line"),
                    html.Th("Vessel Type"),
                    html.Th("Volume (mL)"),
                    html.Th("Inoculation Date"),
                    html.Th("Harvest Date"),
                    html.Th("Harvest Viability"),
                    html.Th("Harvest VCD"),
                ])),
                html.Tbody(vessel_rows)
            ], bordered=True, hover=True, responsive=True, striped=True, size='sm')
        else:
            vessels_table = html.P("No fed batch vessels found for this experiment.", className="text-muted")

        # Get LIMS analytical results linked to this experiment
        # Link by project_id or by searching for seed train IDs and vessel IDs
        lims_samples = LimsSampleAnalysis.objects.filter(
            Q(project_id=experiment.project_id) if experiment.project_id else Q(sample_id__in=[])
        ).select_related(
            'sec_result', 'titer_result', 'ce_sds_result', 'cief_result'
        ).order_by('-sample_date')[:50]  # Limit to 50 most recent

        if lims_samples.exists():
            lims_rows = []
            for sample in lims_samples:
                # Collect available results
                results = []
                if sample.sec_result:
                    results.append(f"SEC: {sample.sec_result.monomer_percent:.1f}%" if hasattr(sample.sec_result, 'monomer_percent') and sample.sec_result.monomer_percent else "SEC")
                if sample.titer_result:
                    results.append(f"Titer: {sample.titer_result.titer_mg_ml:.2f} mg/mL" if hasattr(sample.titer_result, 'titer_mg_ml') and sample.titer_result.titer_mg_ml else "Titer")
                if sample.ce_sds_result:
                    results.append("CE-SDS")
                if sample.cief_result:
                    results.append("cIEF")
                if sample.a280_result:
                    results.append(f"A280: {sample.a280_result:.2f}")

                results_str = ", ".join(results) if results else "-"

                lims_rows.append(html.Tr([
                    html.Td(sample.sample_id),
                    html.Td(sample.project_id or '-'),
                    html.Td(sample.sample_date.strftime('%Y-%m-%d') if sample.sample_date else '-'),
                    html.Td(sample.description or '-'),
                    html.Td(results_str),
                    html.Td(dbc.Badge(sample.status, color="success" if sample.status == "complete" else "warning", className="text-capitalize")),
                ]))

            lims_table = dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Sample ID"),
                    html.Th("Project ID"),
                    html.Th("Sample Date"),
                    html.Th("Description"),
                    html.Th("Available Results"),
                    html.Th("Status"),
                ])),
                html.Tbody(lims_rows)
            ], bordered=True, hover=True, responsive=True, striped=True, size='sm')
        else:
            lims_table = html.P("No LIMS analytical results found for this project.", className="text-muted")

        return (title, exp_id, project_id, status, start_date, name, description,
                seed_trains_table, vessels_table, lims_table)

    except USPExperiment.DoesNotExist:
        return ("Error", "Not found", "-", "-", "-", "-", "Experiment not found",
                html.P("Error", className="text-danger"),
                html.P("Error", className="text-danger"),
                html.P("Error", className="text-danger"))
    except Exception as e:
        print(f"Error loading experiment details: {e}")
        import traceback
        traceback.print_exc()
        return ("Error", "-", "-", "-", "-", "-", f"Error: {str(e)}",
                html.P("Error loading data", className="text-danger"),
                html.P("Error loading data", className="text-danger"),
                html.P("Error loading data", className="text-danger"))

print("USP Experiment Management App initialized successfully")
