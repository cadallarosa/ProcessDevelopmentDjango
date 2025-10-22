"""
CLD Project Management Dashboard App
Main dashboard for tracking CLD projects with Gantt chart visualization
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table, no_update
from dash.exceptions import PreventUpdate
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, date
from django.db.models import Count, Q, F, Avg
from plotly_integration.models import CLDProject, CLDAnalytics, CLDProcessStep

app = DjangoDash("CLDProjectManagementApp", external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
], suppress_callback_exceptions=True)

def get_dashboard_statistics():
    """Get overall project statistics"""
    today = date.today()

    try:
        stats = {
            'total_projects': CLDProject.objects.count(),
            'active_projects': CLDProject.objects.filter(status='In Progress').count(),
            'planning_projects': CLDProject.objects.filter(status='Planning').count(),
            'completed_projects': CLDProject.objects.filter(status='Complete').count(),
            'upcoming_harvests': CLDProject.objects.filter(
                target_harvest_date__gte=today,
                target_harvest_date__lte=today + timedelta(days=7)
            ).count(),
            'analytics_pending': CLDAnalytics.objects.filter(status='Pending').count(),
            'analytics_in_progress': CLDAnalytics.objects.filter(status='In Progress').count(),
            'analytics_reported': CLDAnalytics.objects.filter(status='Reported').count(),
            'purification_in_progress': CLDProject.objects.filter(
                purification_type__isnull=False,
                status='In Progress'
            ).count(),
        }

        # Calculate completion rate
        total_analytics = CLDAnalytics.objects.filter(required=True).count()
        completed_analytics = CLDAnalytics.objects.filter(
            Q(status='Complete') | Q(status='Reported'),
            required=True
        ).count()

        if total_analytics > 0:
            stats['analytics_completion_rate'] = round((completed_analytics / total_analytics) * 100, 1)
        else:
            stats['analytics_completion_rate'] = 0

        return stats
    except Exception as e:
        print(f"Error getting dashboard statistics: {e}")
        # Return default stats if there's an error
        return {
            'total_projects': 0,
            'active_projects': 0,
            'planning_projects': 0,
            'completed_projects': 0,
            'upcoming_harvests': 0,
            'analytics_pending': 0,
            'analytics_in_progress': 0,
            'analytics_reported': 0,
            'analytics_completion_rate': 0
        }

def get_project_gantt_data():
    """Prepare project data for Gantt chart visualization"""
    try:
        projects = CLDProject.objects.all().order_by('-start_date')

        gantt_data = []
        for project in projects:
            # Main project bar
            gantt_data.append({
                'Task': f"{project.project_number} ({project.number_of_samples} samples)",
                'Start': project.start_date,
                'Finish': project.target_harvest_date,
                'Resource': 'Harvest',
                'project_id': project.id,
                'status': project.status,
                'harvest_type': project.get_harvest_type_display(),
                'purification': project.get_purification_type_display(),
            })

            # Add analytics timeline
            try:
                analytics = project.analytics.all()
                for analytic in analytics:
                    if analytic.scheduled_date:
                        # Analytics typically take 2-3 days
                        end_date = analytic.scheduled_date + timedelta(days=3)
                        if analytic.completed_date:
                            end_date = analytic.completed_date

                        gantt_data.append({
                            'Task': f"{project.project_number} ({project.number_of_samples} samples)",
                            'Start': analytic.scheduled_date,
                            'Finish': end_date,
                            'Resource': analytic.analysis_type,
                            'project_id': project.id,
                            'status': analytic.status,
                            'harvest_type': project.get_harvest_type_display(),
                            'purification': project.get_purification_type_display(),
                        })
            except Exception as e:
                print(f"Error loading analytics for project {project.project_number}: {e}")
                continue

        return pd.DataFrame(gantt_data)
    except Exception as e:
        print(f"Error creating Gantt data: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

def create_gantt_chart(df, status_filter='all', harvest_filter='all', start_date=None, end_date=None):
    """Create interactive Gantt chart using CLDProcessStep model"""
    print(f"Creating Gantt chart with filters: status={status_filter}, harvest={harvest_filter}")

    try:
        fig = go.Figure()

        # Define the CLD workflow steps in display order (reversed from execution)
        workflow_steps = [
            {'step': 'Analytics', 'y_pos': 0},
            {'step': 'Purification', 'y_pos': 1},
            {'step': 'Harvest', 'y_pos': 2},
            {'step': 'Cydem', 'y_pos': 3},
            {'step': 'Grow Up', 'y_pos': 4},
            {'step': 'Beacon', 'y_pos': 5},
            {'step': 'Recovery', 'y_pos': 6},
            {'step': 'mP/BP', 'y_pos': 7},
            {'step': 'Transfection', 'y_pos': 8}
        ]

        # Get projects from database with filtering
        projects_query = CLDProject.objects.all()

        # Apply filters (simplified for now since we're using new model structure)
        if status_filter != 'all':
            projects_query = projects_query.filter(status=status_filter)

        projects = list(projects_query.order_by('-created_date')[:15])

        # For demo purposes, create dummy projects with process steps if no real projects exist
        if len(projects) < 2:
            projects = get_projects_with_steps()

        # Filter projects by date range if specified
        if start_date and end_date:
            # Convert string dates to date objects for comparison
            from datetime import datetime as dt
            if isinstance(start_date, str):
                start_date = dt.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = dt.strptime(end_date, '%Y-%m-%d').date()

            filtered_projects = []
            for project in projects:
                # Check if project has any steps in the date range
                if hasattr(project, 'process_steps'):
                    # Get actual steps (handle both list and RelatedManager)
                    if hasattr(project.process_steps, 'all'):
                        project_steps = project.process_steps.all()
                    else:
                        project_steps = project.process_steps

                    steps_in_range = [step for step in project_steps if
                                    getattr(step, 'planned_start_date', None) and
                                    getattr(step, 'planned_end_date', None) and
                                    step.planned_start_date <= end_date and
                                    step.planned_end_date >= start_date]
                    if steps_in_range:
                        filtered_projects.append(project)
            projects = filtered_projects

        # Generate colors for projects
        colors = px.colors.qualitative.Plotly

        # Track all project names for legend
        added_projects = set()

        # Calculate offset for each project to avoid overlaps
        bar_height = 0.6
        project_height = bar_height / max(len(projects), 1)

        for idx, project in enumerate(projects):
            color = colors[idx % len(colors)]
            project_name = getattr(project, 'project_id', f"Project-{idx+1}")

            # Calculate y-offset for this project to prevent overlaps
            y_offset = (idx * project_height) - (bar_height / 2)

            # Get process steps for this project
            if hasattr(project, 'process_steps'):
                if hasattr(project.process_steps, 'all'):
                    steps = project.process_steps.all()
                else:
                    steps = project.process_steps
            else:
                steps = []

            for step_info in workflow_steps:
                step_name = step_info['step']
                y_pos = step_info['y_pos']

                # Find the corresponding step data
                step_data = None
                for s in steps:
                    if hasattr(s, 'step_name') and s.step_name == step_name:
                        step_data = s
                        break
                    elif isinstance(s, dict) and s.get('step_name') == step_name:
                        step_data = s
                        break

                if not step_data:
                    continue

                # Use actual dates if available, otherwise planned dates
                if hasattr(step_data, 'actual_start_date'):
                    # Django model object
                    bar_start = step_data.actual_start_date or step_data.planned_start_date
                    if step_data.actual_end_date:
                        bar_end = step_data.actual_end_date
                    elif step_data.actual_duration_days:
                        bar_end = bar_start + timedelta(days=step_data.actual_duration_days)
                    else:
                        bar_end = step_data.planned_end_date or bar_start + timedelta(days=1)
                    step_status = step_data.status
                    planned_duration = step_data.planned_duration_days
                    actual_duration = step_data.actual_duration_days
                else:
                    # Dictionary object (dummy data)
                    bar_start = step_data.get('actual_start_date') or step_data.get('planned_start_date')
                    if step_data.get('actual_end_date'):
                        bar_end = step_data['actual_end_date']
                    elif step_data.get('actual_duration_days'):
                        bar_end = bar_start + timedelta(days=step_data['actual_duration_days'])
                    else:
                        bar_end = step_data.get('planned_end_date', bar_start + timedelta(days=1))
                    step_status = step_data.get('status', 'Pending')
                    planned_duration = step_data.get('planned_duration_days', 1)
                    actual_duration = step_data.get('actual_duration_days')

                # Convert to datetime if needed
                if bar_start and not isinstance(bar_start, datetime):
                    bar_start = datetime.combine(bar_start, datetime.min.time())
                if bar_end and not isinstance(bar_end, datetime):
                    bar_end = datetime.combine(bar_end, datetime.min.time())

                # Skip if we don't have valid dates
                if not bar_start or not bar_end:
                    continue

                # Determine status and styling based on step status
                if step_status == 'Complete':
                    status = 'complete'
                    opacity = 1.0
                    dash = None
                elif step_status == 'In Progress':
                    status = 'in_progress'
                    opacity = 0.7
                    dash = 'dash'
                elif step_status == 'Skipped':
                    status = 'skipped'
                    opacity = 0.2
                    dash = 'dashdot'
                else:
                    status = 'pending'
                    opacity = 0.3
                    dash = 'dot'

                # Create step label

                if actual_duration:
                    step_label = f"{step_name} (Actual: {actual_duration}d, Planned: {planned_duration}d)"
                else:
                    step_label = f"{step_name} (Planned: {planned_duration}d)"

                # Only add to legend once per project
                show_legend = project_name not in added_projects
                if show_legend:
                    added_projects.add(project_name)

                # Create bar for this step with y-offset to avoid overlaps
                bar_bottom = y_pos + y_offset - (project_height / 2)
                bar_top = y_pos + y_offset + (project_height / 2)

                fig.add_trace(go.Scatter(
                    x=[bar_start, bar_end, bar_end, bar_start, bar_start],
                    y=[bar_bottom, bar_bottom, bar_top, bar_top, bar_bottom],
                    fill='toself',
                    fillcolor=color,
                    opacity=opacity,
                    line=dict(color=color, dash=dash, width=2 if status == 'in_progress' else 1),
                    mode='lines',
                    name=project_name,
                    legendgroup=project_name,
                    showlegend=show_legend,
                    hovertemplate=f'<b>{project_name}</b><br>{step_label}<br>Start: %{{x[0]|%Y-%m-%d}}<br>End: %{{x[1]|%Y-%m-%d}}<br>Status: {step_status}<extra></extra>'
                ))

                # Add text annotation for harvest steps
                if step_name == 'Harvest':
                    mid_date = bar_start + (bar_end - bar_start) / 2
                    samples = getattr(project, 'number_of_samples', 0)
                    fig.add_annotation(
                        x=mid_date,
                        y=y_pos + y_offset,
                        text=f"{samples}",
                        showarrow=False,
                        font=dict(size=9, color='white' if opacity > 0.5 else 'black'),
                        bgcolor=color,
                        opacity=0.8
                    )

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
            x_start = datetime.now()
            x_end = datetime.now() + timedelta(days=60)

        # Update layout
        fig.update_layout(
            height=500,
            title="CLD Project Workflow Timeline",
            xaxis_title="Timeline",
            yaxis_title="Workflow Steps",
            xaxis=dict(
                type='date',
                showgrid=True,
                gridcolor='lightgray',
                range=[x_start, x_end]
            ),
            yaxis=dict(
                tickmode='array',
                tickvals=[s['y_pos'] for s in workflow_steps],
                ticktext=[s['step'] for s in workflow_steps],
                showgrid=True,
                gridcolor='lightgray',
                range=[-1, len(workflow_steps)]  # Expanded range to accommodate offsets
            ),
            showlegend=True,
            legend=dict(
                title="Projects",
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            ),
            margin=dict(l=100, r=150, t=80, b=50),
            hovermode='closest'
        )

        print(f"Created Gantt chart with {len(fig.data)} traces")
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

def get_projects_with_steps():
    """Get projects with their process steps from database, create demo data if none exist"""
    try:
        # Try to get projects with process steps from database
        projects = CLDProject.objects.prefetch_related('process_steps').order_by('-created_date')[:15]

        # Convert to list - keep Django objects but ensure we can access steps
        project_list = []
        for project in projects:
            # Check if this project has process steps
            step_count = project.process_steps.count()
            if step_count > 0:
                project_list.append(project)

        # If we have projects with steps, return them
        if project_list:
            return project_list

    except Exception as e:
        print(f"Error fetching projects from database: {e}")

    # If no projects exist or error occurred, create dummy projects
    return create_dummy_projects_with_steps()

def create_dummy_projects_with_steps():
    """Create dummy projects with process steps for demonstration"""
    from datetime import date, timedelta

    dummy_projects = []

    for i in range(2):
        class DummyProject:
            def __init__(self, num):
                self.project_id = f"CLD-2025-{num:03d}"
                self.project_number = self.project_id
                self.number_of_samples = [24, 96][num % 2]
                self.transfection_start_date = date.today() + timedelta(days=num*5)
                self.status = ['In Progress', 'Planning'][num % 2]

                # Create process steps with realistic timelines
                base_date = self.transfection_start_date
                self.process_steps = []

                steps_config = [
                    {'step_name': 'Transfection', 'duration': 1, 'status': 'Complete' if num == 0 else 'In Progress'},
                    {'step_name': 'mP/BP', 'duration': 1, 'status': 'Complete' if num == 0 else 'Pending'},
                    {'step_name': 'Recovery', 'duration': 14, 'status': 'In Progress' if num == 0 else 'Pending'},
                    {'step_name': 'Beacon', 'duration': 14, 'status': 'Pending'},
                    {'step_name': 'Grow Up', 'duration': 21, 'status': 'Pending'},
                    {'step_name': 'Cydem', 'duration': 14, 'status': 'Pending'},
                    {'step_name': 'Harvest', 'duration': 1, 'status': 'Pending'},
                    {'step_name': 'Purification', 'duration': 2, 'status': 'Pending'},
                    {'step_name': 'Analytics', 'duration': 4, 'status': 'Pending'},
                ]

                current_date = base_date
                for step_config in steps_config:
                    step = {
                        'step_name': step_config['step_name'],
                        'planned_duration_days': step_config['duration'],
                        'actual_duration_days': step_config['duration'] if step_config['status'] == 'Complete' else None,
                        'planned_start_date': current_date,
                        'planned_end_date': current_date + timedelta(days=step_config['duration']),
                        'actual_start_date': current_date if step_config['status'] in ['Complete', 'In Progress'] else None,
                        'actual_end_date': current_date + timedelta(days=step_config['duration']) if step_config['status'] == 'Complete' else None,
                        'status': step_config['status']
                    }
                    self.process_steps.append(step)
                    current_date += timedelta(days=step_config['duration'])

        dummy_projects.append(DummyProject(i))

    return dummy_projects

# Callback to initialize workflow steps when creating new project
@app.callback(
    Output("workflow-steps-container", "children"),
    [Input("new-project-btn", "n_clicks")],
    prevent_initial_call=True
)
def initialize_workflow_steps(n_clicks):
    if n_clicks:
        default_steps = get_default_workflow_steps()
        return [
            create_step_card(i, step['step_name'], step['duration'])
            for i, step in enumerate(default_steps)
        ]
    return []

# Callback for loading templates
@app.callback(
    Output("workflow-steps-container", "children", allow_duplicate=True),
    [Input("load-template-btn", "n_clicks"),
     Input("process-template-select", "value")],
    prevent_initial_call=True
)
def load_template(n_clicks, template_type):
    print(f"\n[DEBUG TEMPLATE] load_template called: n_clicks={n_clicks}, template_type={template_type}")

    ctx = dash.callback_context
    if not ctx.triggered:
        print("[DEBUG TEMPLATE] No trigger context, returning empty")
        return []

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print(f"[DEBUG TEMPLATE] Trigger ID: {trigger_id}")

    if trigger_id == "load-template-btn" or trigger_id == "process-template-select":
        if not template_type:
            print("[DEBUG TEMPLATE] No template type selected")
            return []

        print(f"[DEBUG TEMPLATE] Loading template: {template_type}")
        template_steps = get_workflow_template(template_type)
        print(f"[DEBUG TEMPLATE] Template steps: {[s['step_name'] for s in template_steps]}")

        step_cards = [
            create_step_card(i, step['step_name'], step['duration'])
            for i, step in enumerate(template_steps)
        ]
        print(f"[DEBUG TEMPLATE] Created {len(step_cards)} step cards for workflow-steps-container")
        return step_cards

    print("[DEBUG TEMPLATE] No valid trigger, returning empty")
    return []

# Callback for adding new steps
@app.callback(
    Output("workflow-steps-container", "children", allow_duplicate=True),
    [Input("add-step-btn", "n_clicks")],
    [State("workflow-steps-container", "children")],
    prevent_initial_call=True
)
def add_workflow_step(n_clicks, current_steps):
    if n_clicks and current_steps is not None:
        new_index = len(current_steps)
        new_step = create_step_card(new_index, "", 1)
        return current_steps + [new_step]
    return current_steps or []

# Callback for adding steps in edit modal
@app.callback(
    Output("edit-steps-container", "children", allow_duplicate=True),
    [Input("add-edit-step-btn", "n_clicks")],
    [State("edit-steps-container", "children")],
    prevent_initial_call=True
)
def add_edit_step(n_clicks, current_steps):
    if n_clicks and current_steps is not None:
        new_index = len(current_steps)
        new_step_data = {
            'step_name': '',
            'planned_duration': 1,
            'status': 'Pending',
            'actual_duration': None,
            'order': new_index + 1
        }
        new_step = create_edit_step_card(new_index, new_step_data)
        return current_steps + [new_step]
    return current_steps or []

# Callback to handle status and completion date changes
@app.callback(
    Output("edit-steps-store", "data", allow_duplicate=True),
    [Input({"type": "step-status", "index": dash.dependencies.ALL}, "value"),
     Input({"type": "step-completion-date", "index": dash.dependencies.ALL}, "date")],
    [State("edit-steps-store", "data"),
     State("edit-steps-project-id", "data")],
    prevent_initial_call=True
)
def handle_step_status_changes(statuses, completion_dates, store_data, project_id):
    """Handle status and completion date changes with timeline recalculation"""

    if not store_data or not store_data.get('steps'):
        return store_data

    ctx = dash.callback_context
    if not ctx.triggered:
        return store_data

    # Deep copy for modification
    import copy
    from datetime import datetime, timedelta
    steps_data = store_data['steps']
    new_steps = copy.deepcopy(steps_data)

    # Update statuses and completion dates
    for i, step in enumerate(new_steps):
        if i < len(statuses) and statuses[i]:
            step['status'] = statuses[i]

        if i < len(completion_dates) and completion_dates[i]:
            step['actual_end_date'] = completion_dates[i]

            # Auto-calculate actual duration when marked complete
            if step['status'] == 'Complete' and step['actual_end_date']:
                # Calculate from previous step end or project start
                if i > 0:
                    prev_step = new_steps[i-1]
                    if prev_step.get('actual_end_date'):
                        start_date = datetime.strptime(prev_step['actual_end_date'], '%Y-%m-%d')
                    else:
                        # Use planned timeline if previous step not complete
                        start_date = datetime.now() - timedelta(days=sum(s['planned_duration'] for s in new_steps[:i]))
                else:
                    # First step starts from project transfection date
                    start_date = datetime.now() - timedelta(days=7)  # Default 7 days ago

                end_date = datetime.strptime(step['actual_end_date'], '%Y-%m-%d')
                actual_duration = (end_date - start_date).days
                step['actual_duration'] = max(1, actual_duration)

    # Recalculate timeline for subsequent steps
    recalculate_timeline(new_steps)

    # Save to database
    if project_id:
        save_steps_with_timeline(project_id, new_steps)

    print(f"[DEBUG] Updated step statuses and recalculated timeline")
    # Return with incremented version to force update
    return {'version': store_data.get('version', 0) + 1, 'steps': new_steps}

# FIXED: Improved callback for step reordering with proper re-rendering
@app.callback(
    Output("edit-steps-store", "data", allow_duplicate=True),
    [Input({"type": "move-up", "index": dash.dependencies.ALL}, "n_clicks"),
     Input({"type": "move-down", "index": dash.dependencies.ALL}, "n_clicks"),
     Input({"type": "remove-step", "index": dash.dependencies.ALL}, "n_clicks")],
    [State("edit-steps-store", "data"),
     State("edit-steps-project-id", "data")],
    prevent_initial_call=True
)
def handle_step_actions(up_clicks, down_clicks, remove_clicks, store_data, project_id):
    """Handle step reordering and removal by manipulating store data"""

    if not store_data or not store_data.get('steps'):
        return store_data

    ctx = dash.callback_context
    if not ctx.triggered:
        return store_data

    # Check if any button was actually clicked (look for non-zero values)
    has_up_clicks = up_clicks and any(click and click > 0 for click in up_clicks)
    has_down_clicks = down_clicks and any(click and click > 0 for click in down_clicks)
    has_remove_clicks = remove_clicks and any(click and click > 0 for click in remove_clicks)

    if not (has_up_clicks or has_down_clicks or has_remove_clicks):
        return store_data

    trigger = ctx.triggered[0]
    trigger_id = trigger['prop_id'].split('.')[0]

    try:
        import json
        trigger_data = json.loads(trigger_id)  # Use json.loads instead of eval
        action = trigger_data['type']
        index = trigger_data['index']

        print(f"[DEBUG] Action: {action}, Index: {index}")

        # Make a deep copy of the data to manipulate
        import copy
        import time
        new_steps = copy.deepcopy(store_data['steps'])

        if action == "move-up" and index > 0:
            # Swap with previous step
            new_steps[index], new_steps[index - 1] = new_steps[index - 1], new_steps[index]
            print(f"[DEBUG] Moved step {index} up")

        elif action == "move-down" and index < len(new_steps) - 1:
            # Swap with next step
            new_steps[index], new_steps[index + 1] = new_steps[index + 1], new_steps[index]
            print(f"[DEBUG] Moved step {index} down")

        elif action == "remove-step":
            # Remove the step
            new_steps.pop(index)
            print(f"[DEBUG] Removed step {index}")

        # Update the order values to match new positions
        for i, step in enumerate(new_steps):
            step['order'] = i + 1
            # Add a timestamp to force re-render
            step['_timestamp'] = time.time()
            step['_ui_key'] = f"step-{i}-{step['step_name']}-{time.time()}"  # Unique UI key

        # Save to database if project_id is available
        if project_id:
            save_steps_to_database(project_id, new_steps)

        print(f"[DEBUG] New step order: {[s['step_name'] for s in new_steps]}")

        # Force a complete re-render by incrementing version significantly
        new_version = store_data.get('version', 0) + 100

        return {'version': new_version, 'steps': new_steps, 'force_refresh': time.time()}

    except Exception as e:
        print(f"[DEBUG ERROR] {e}")
        import traceback
        print(traceback.format_exc())
        return store_data

# New callback to refresh step values when refresh trigger changes
@app.callback(
    [Output({"type": "edit-step-type", "index": dash.dependencies.ALL}, "value"),
     Output({"type": "edit-step-duration", "index": dash.dependencies.ALL}, "value"),
     Output({"type": "edit-step-status", "index": dash.dependencies.ALL}, "value")],
    [Input("steps-refresh-trigger", "data")],
    [State("edit-steps-project-id", "data")],
    prevent_initial_call=True
)
def refresh_step_values(trigger, project_id):
    """Refresh all step field values from database when trigger changes"""
    print(f"\n[DEBUG REFRESH] refresh_step_values called with trigger={trigger}, project_id={project_id}")

    if not project_id:
        print("[DEBUG REFRESH] No project_id, returning empty")
        return [], [], []

    try:
        project = CLDProject.objects.get(id=project_id)
        steps = list(project.process_steps.all().order_by('step_order'))

        step_types = []
        durations = []
        statuses = []

        for step in steps:
            step_types.append(step.step_name)
            durations.append(step.planned_duration_days)
            statuses.append(step.status)
            print(f"[DEBUG REFRESH] Step: {step.step_name}, duration: {step.planned_duration_days}, status: {step.status}")

        print(f"[DEBUG REFRESH] Returning values for {len(steps)} steps")
        return step_types, durations, statuses

    except Exception as e:
        print(f"[DEBUG REFRESH ERROR] Error: {e}")
        return [], [], []

# Simple callback to handle step status updates and save to database immediately
@app.callback(
    Output("edit-steps-data", "data"),
    [Input({"type": "edit-step-status", "index": dash.dependencies.ALL}, "value"),
     Input({"type": "edit-step-completion", "index": dash.dependencies.ALL}, "date"),
     Input({"type": "edit-step-type", "index": dash.dependencies.ALL}, "value"),
     Input({"type": "edit-step-duration", "index": dash.dependencies.ALL}, "value")],
    [State("edit-steps-project-id", "data"),
     State("edit-steps-data", "data")],
    prevent_initial_call=True
)
def update_step_data(statuses, completion_dates, step_types, durations, project_id, current_data):
    """Update step data and immediately save to database when form changes"""
    if not project_id:
        return current_data

    try:
        project = CLDProject.objects.get(id=project_id)
        steps = list(project.process_steps.all().order_by('step_order'))

        updated_count = 0
        for i, step in enumerate(steps):
            step_changed = False

            # Update status if changed
            if i < len(statuses) and statuses[i] and statuses[i] != step.status:
                step.status = statuses[i]
                step_changed = True

            # Update completion date and calculate duration if step is complete
            if i < len(completion_dates) and completion_dates[i] and step.status == 'Complete':
                from datetime import datetime
                completion_dt = datetime.strptime(completion_dates[i], '%Y-%m-%d').date()

                # Set actual end date
                step.actual_end_date = completion_dt

                # Calculate start date and duration
                if i > 0:
                    prev_step = steps[i-1]
                    start_date = prev_step.actual_end_date or prev_step.planned_end_date or project.transfection_start_date
                else:
                    start_date = project.transfection_start_date

                step.actual_start_date = start_date
                duration = (completion_dt - start_date).days
                step.actual_duration_days = max(1, duration)
                step_changed = True

            # Update planned duration if changed
            if i < len(durations) and durations[i] and durations[i] != step.planned_duration_days:
                step.planned_duration_days = int(durations[i])
                step_changed = True

            # Save if changed
            if step_changed:
                step.save()
                updated_count += 1

        print(f"Updated {updated_count} steps in database")
        return {"updated_count": updated_count, "timestamp": datetime.now().isoformat()}

    except Exception as e:
        print(f"Error updating step data: {e}")
        return current_data

def get_recent_projects():
    """Get recent projects with summary information"""
    projects = CLDProject.objects.all().order_by('-created_date')[:15]

    project_data = []
    for project in projects:
        analytics_count = project.analytics.count()
        completed_analytics = project.analytics.filter(
            status__in=['Complete', 'Reported']
        ).count()

        completion_rate = 0
        if analytics_count > 0:
            completion_rate = round((completed_analytics / analytics_count) * 100, 1)

        days_to_harvest = project.days_to_harvest()
        harvest_status = "Completed"
        if days_to_harvest is not None:
            if days_to_harvest < 0:
                harvest_status = "Overdue"
            elif days_to_harvest <= 3:
                harvest_status = "Urgent"
            elif days_to_harvest <= 7:
                harvest_status = "Soon"
            else:
                harvest_status = "Scheduled"

        project_data.append({
            'id': project.id,
            'project_number': project.project_number,
            'sip_number': getattr(project, 'sip_number', 'N/A'),
            'samples': project.number_of_samples,
            'start_date': project.start_date.strftime('%Y-%m-%d') if project.start_date else 'N/A',
            'harvest_date': project.target_harvest_date.strftime('%Y-%m-%d') if project.target_harvest_date else 'N/A',
            'harvest_type': project.get_harvest_type_display() if hasattr(project, 'get_harvest_type_display') else 'N/A',
            'purification': project.get_purification_type_display(),
            'status': project.status,
            'analytics_progress': f"{completed_analytics}/{analytics_count}",
            'completion': f"{completion_rate}%",
            'harvest_status': harvest_status,
            'days_to_harvest': days_to_harvest if days_to_harvest is not None else 'N/A'
        })

    return project_data

def get_upcoming_deadlines():
    """Get projects with upcoming deadlines"""
    today = date.today()
    upcoming_threshold = today + timedelta(days=14)

    # Get projects with upcoming harvests
    upcoming_projects = CLDProject.objects.filter(
        target_harvest_date__gte=today,
        target_harvest_date__lte=upcoming_threshold,
        status__in=['Planning', 'In Progress']
    ).order_by('target_harvest_date')

    deadlines = []
    for project in upcoming_projects:
        days_remaining = (project.target_harvest_date - today).days
        deadlines.append({
            'project_number': project.project_number,
            'harvest_date': project.target_harvest_date.strftime('%Y-%m-%d'),
            'days_remaining': days_remaining,
            'harvest_type': project.get_harvest_type_display(),
            'samples': project.number_of_samples,
            'status': project.status,
            'urgency': 'High' if days_remaining <= 3 else 'Medium' if days_remaining <= 7 else 'Low'
        })

    # Get analytics with upcoming scheduled dates
    try:
        upcoming_analytics = CLDAnalytics.objects.filter(
            scheduled_date__gte=today,
            scheduled_date__lte=upcoming_threshold,
            status__in=['Pending', 'In Progress']
        ).select_related('project').order_by('scheduled_date')

        for analytic in upcoming_analytics:
            days_remaining = (analytic.scheduled_date - today).days
            deadlines.append({
                'project_number': f"{analytic.project.project_number} - {analytic.analysis_type}",
                'harvest_date': analytic.scheduled_date.strftime('%Y-%m-%d'),
                'days_remaining': days_remaining,
                'harvest_type': 'Analytics',
                'samples': analytic.project.number_of_samples,
                'status': analytic.status,
                'urgency': 'High' if days_remaining <= 2 else 'Medium' if days_remaining <= 5 else 'Low'
            })
    except Exception as e:
        print(f"Error fetching analytics deadlines: {e}")
        # Continue without analytics deadlines if there's an error

    return sorted(deadlines, key=lambda x: x['days_remaining'])

def create_summary_cards():
    """Create summary statistics cards"""
    stats = get_dashboard_statistics()

    return html.Div([
        dbc.Badge([
            html.I(className="fas fa-project-diagram me-2"),
            f"Total: {stats['total_projects']}"
        ], color="primary", className="me-2 p-2"),
        dbc.Badge([
            html.I(className="fas fa-play-circle me-2"),
            f"Active: {stats['active_projects']}"
        ], color="success", className="me-2 p-2"),
        dbc.Badge([
            html.I(className="fas fa-calendar-check me-2"),
            f"Upcoming: {stats['upcoming_harvests']}"
        ], color="warning", className="me-2 p-2"),
        dbc.Badge([
            html.I(className="fas fa-flask me-2"),
            f"Analytics Pending: {stats['analytics_pending']}"
        ], color="info", className="me-2 p-2"),
        dbc.Badge([
            html.I(className="fas fa-filter me-2"),
            f"Purification: {stats['purification_in_progress']}"
        ], color="secondary", className="me-2 p-2"),
        dbc.Badge([
            html.I(className="fas fa-check-double me-2"),
            f"Complete: {stats['completed_projects']}"
        ], color="dark", className="p-2")
    ])

# Layout
app.layout = dbc.Container([
    dcc.Store(id="selected-project-store"),
    dcc.Interval(id="refresh-interval", interval=300000, n_intervals=0),  # Refresh every 5 minutes

    # Header
    dbc.Row([
        dbc.Col([
            html.H1([
                html.I(className="fas fa-tasks text-primary me-3"),
                "CLD Project Management"
            ], className="mb-3"),
            html.P("Track projects, harvests, analytics, and purification with interactive Gantt charts",
                   className="lead text-muted")
        ], width=8),
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button(
                    [html.I(className="fas fa-plus me-2"), "New Project"],
                    id="new-project-btn",
                    color="primary",
                    className="me-2"
                ),
                dbc.Button(
                    [html.I(className="fas fa-sync me-2"), "Refresh"],
                    id="refresh-btn",
                    color="secondary",
                    outline=True
                ),
            ], className="mt-3")
        ], width=4, className="text-end")
    ], className="mb-4"),

    # Combined Filter Controls and Summary Cards
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Status Filter:", className="fw-bold"),
                    dcc.Dropdown(
                        id="status-filter",
                        options=[
                            {'label': 'All Projects', 'value': 'all'},
                            {'label': 'Planning', 'value': 'Planning'},
                            {'label': 'In Progress', 'value': 'In Progress'},
                            {'label': 'Complete', 'value': 'Complete'},
                        ],
                        value='all',
                        clearable=False
                    )
                ], md=2),
                dbc.Col([
                    dbc.Label("Harvest Type:", className="fw-bold"),
                    dcc.Dropdown(
                        id="harvest-type-filter",
                        options=[
                            {'label': 'All Types', 'value': 'all'},
                            {'label': '24 Deepwell', 'value': '24_deepwell'},
                            {'label': '48 Deepwell', 'value': '48_deepwell'},
                            {'label': 'Shake Flask', 'value': 'shake_flask'},
                            {'label': 'Beacon', 'value': 'beacon'},
                        ],
                        value='all',
                        clearable=False
                    )
                ], md=2),
                dbc.Col([
                    dbc.Label("Date Range:", className="fw-bold"),
                    dcc.DatePickerRange(
                        id="date-range-filter",
                        start_date=datetime.now().date(),
                        end_date=(datetime.now() + timedelta(days=60)).date(),
                        display_format='YYYY-MM-DD',
                        style={'width': '100%'}
                    )
                ], md=4),
                # Summary Cards moved here
                dbc.Col([
                    html.Div(id="summary-cards-container", className="d-flex gap-2 justify-content-end")
                ], md=4)
            ])
        ])
    ], className="mb-4"),

    # Main Gantt Chart
    dbc.Card([
        dbc.CardHeader([
            html.H5([html.I(className="fas fa-chart-gantt me-2"), "Project Timeline"], className="mb-0")
        ]),
        dbc.CardBody([
            dcc.Loading(
                id="loading-gantt",
                type="default",
                children=html.Div(id="gantt-chart-container")
            )
        ])
    ], className="mb-4"),

    # Bottom Section: Projects Table and Analytics Overview
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5([html.I(className="fas fa-table me-2"), "Recent Projects"], className="mb-0")
                ]),
                dbc.CardBody([
                    html.Div(id="projects-table")
                ])
            ])
        ], md=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5([html.I(className="fas fa-chart-pie me-2"), "Analytics Overview"], className="mb-0")
                ]),
                dbc.CardBody([
                    dcc.Graph(id="analytics-overview-chart")
                ])
            ])
        ], md=4),
    ], className="mb-4"),

    # Upcoming Deadlines Section
    dbc.Card([
        dbc.CardHeader([
            html.H5([html.I(className="fas fa-exclamation-triangle me-2"), "Upcoming Deadlines"], className="mb-0")
        ]),
        dbc.CardBody([
            html.Div(id="upcoming-deadlines-table")
        ])
    ]),

    # Modal for project creation/editing
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
        dbc.ModalBody([
            dcc.Store(id="edit-project-store"),  # Store for editing project data
            dbc.Form([
                # Project Details Section
                html.H5("Project Details", className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Project ID", html_for="project-id-input"),
                        dbc.Input(
                            id="project-id-input",
                            placeholder="Enter project ID",
                            type="text",
                            required=True
                        ),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("SIP Number", html_for="sip-number-input"),
                        dbc.Input(
                            id="sip-number-input",
                            placeholder="Enter SIP number",
                            type="text",
                            required=True
                        ),
                    ], md=6),
                ], className="mb-3"),

                # Transfection Details Section
                html.Hr(),
                html.H5("Transfection Details", className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Transfection Start Date", html_for="transfection-start-date"),
                        dcc.DatePickerSingle(
                            id="transfection-start-date",
                            date=date.today(),
                            display_format="YYYY-MM-DD",
                            style={'width': '100%'}
                        ),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Transfection Type", html_for="transfection-type-select"),
                        dcc.Dropdown(
                            id="transfection-type-select",
                            options=[
                                {'label': 'Lonza', 'value': 'Lonza'},
                                {'label': 'BTX', 'value': 'BTX'},
                            ],
                            value='Lonza',
                            clearable=False
                        ),
                    ], md=6),
                ], className="mb-3"),

                dbc.Row([
                    dbc.Col([
                        dbc.Label("Transfection Amount (mg)", html_for="transfection-amount-input"),
                        dbc.Input(
                            id="transfection-amount-input",
                            placeholder="Enter amount in mg",
                            type="number",
                            step=0.01,
                            min=0,
                            required=True
                        ),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Options", html_for="options-select"),
                        dcc.Dropdown(
                            id="options-select",
                            options=[
                                {'label': 'Minipool', 'value': 'Minipool'},
                                {'label': 'Bulkpool', 'value': 'Bulkpool'},
                                {'label': 'Minipool+Bulkpool', 'value': 'Minipool+Bulkpool'},
                            ],
                            value='Minipool',
                            clearable=False
                        ),
                    ], md=6),
                ], className="mb-3"),

                # Legacy fields for backward compatibility
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Number of Samples", html_for="num-samples-input"),
                        dbc.Input(
                            id="num-samples-input",
                            placeholder="Enter number of samples",
                            type="number",
                            min=1,
                            required=True
                        ),
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Purification Type", html_for="purification-type-select"),
                        dcc.Dropdown(
                            id="purification-type-select",
                            options=[
                                {'label': 'Protein A', 'value': 'PROA'},
                                {'label': 'Kappa', 'value': 'Kappa'},
                                {'label': 'Lambda', 'value': 'Lambda'},
                                {'label': 'G Protein', 'value': 'G_protein'},
                                {'label': 'L Protein', 'value': 'L_protein'},
                                {'label': 'Other', 'value': 'Other'},
                            ],
                            value='PROA',
                            clearable=False
                        ),
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Project Status", html_for="status-select"),
                        dcc.Dropdown(
                            id="status-select",
                            options=[
                                {'label': 'Planning', 'value': 'Planning'},
                                {'label': 'In Progress', 'value': 'In Progress'},
                                {'label': 'Complete', 'value': 'Complete'},
                            ],
                            value='Planning',
                            clearable=False
                        ),
                    ], md=4),
                ], className="mb-3"),

                # Workflow Template Section
                html.Hr(),
                html.H5("Workflow Configuration", className="mb-3"),

                dbc.Row([
                    dbc.Col([
                        dbc.Label("Process Template", html_for="process-template-select", className="fw-bold"),
                        dcc.Dropdown(
                            id="process-template-select",
                            options=[
                                {'label': 'Standard CLD Workflow (9 steps)', 'value': 'standard'},
                                {'label': 'Fast Track CLD (6 steps)', 'value': 'fast_track'},
                                {'label': 'Minimal CLD (4 steps)', 'value': 'minimal'},
                                {'label': 'Custom Workflow', 'value': 'custom'},
                            ],
                            value='standard',
                            clearable=False
                        ),
                        html.P("Choose a template or create a custom workflow", className="text-muted small mt-1"),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Actions", className="fw-bold"),
                        html.Div([
                            dbc.Button(
                                [html.I(className="fas fa-sync me-2"), "Load Template"],
                                id="load-template-btn",
                                color="primary",
                                size="sm",
                                outline=True,
                                className="me-2"
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-plus me-2"), "Add Step"],
                                id="add-step-btn",
                                color="success",
                                size="sm",
                                outline=True
                            ),
                        ])
                    ], md=6, className="text-end"),
                ], className="mb-3"),

                # Container for dynamic steps
                html.Div(id="workflow-steps-container", children=[
                    # Will be populated based on template selection
                ]),

                # Analytics Section
                html.Hr(),
                html.H5("Required Analytics", className="mb-3"),
                html.P("Select which analytics are required for this project:", className="text-muted"),

                dbc.Row([
                    dbc.Col([
                        dbc.Checklist(
                            id="analytics-checklist",
                            options=[
                                {'label': 'SEC (Size Exclusion Chromatography)', 'value': 'SEC'},
                                {'label': 'Titer', 'value': 'Titer'},
                                {'label': 'Octet', 'value': 'Octet'},
                                {'label': 'CE-SDS', 'value': 'CE-SDS'},
                                {'label': 'cIEF', 'value': 'cIEF'},
                                {'label': 'LC-MS', 'value': 'LCMS'},
                            ],
                            value=['SEC', 'Titer'],  # Default selections
                            inline=False
                        ),
                    ], md=12),
                ], className="mb-3"),

                # Notes Section
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Notes", html_for="notes-input"),
                        dbc.Textarea(
                            id="notes-input",
                            placeholder="Enter any additional notes or comments...",
                            rows=3
                        ),
                    ], md=12),
                ], className="mb-3"),
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-modal", color="secondary", className="me-2", n_clicks=0),
            dbc.Button("Save Project", id="save-project", color="primary", n_clicks=0),
        ]),
    ], id="project-modal", is_open=False, size="lg"),

    # Project Step Editing Modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Edit Project Steps")),
        dbc.ModalBody([
            dcc.Store(id="edit-steps-project-id"),
            dcc.Store(id="edit-steps-store", data={'version': 0, 'steps': []}),  # Store with version tracking
            dcc.Store(id="edit-steps-data", data={}),  # Store for step data updates
            html.Div(id="project-steps-wrapper", children=[
                html.Div(id="project-steps-container")
            ]),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-steps-modal", color="secondary", className="me-2"),
            dbc.Button("Save Changes", id="save-steps", color="primary"),
        ]),
    ], id="steps-modal", is_open=False, size="xl"),

    # Alert for success/error messages
    dcc.Store(id="alert-store"),
    html.Div(id="alert-container"),

], fluid=True)

# Callbacks
@app.callback(
    [Output("summary-cards-container", "children"),
     Output("gantt-chart-container", "children"),
     Output("projects-table", "children"),
     Output("upcoming-deadlines-table", "children"),
     Output("analytics-overview-chart", "figure")],
    [Input("refresh-interval", "n_intervals"),
     Input("refresh-btn", "n_clicks"),
     Input("status-filter", "value"),
     Input("harvest-type-filter", "value"),
     Input("date-range-filter", "start_date"),
     Input("date-range-filter", "end_date")]
)
def update_dashboard(n_intervals, refresh_clicks, status_filter, harvest_filter, start_date, end_date):
    # Summary cards
    summary_cards = create_summary_cards()

    # Filter projects for Gantt chart
    gantt_df = get_project_gantt_data()

    if not gantt_df.empty and status_filter != 'all':
        gantt_df = gantt_df[gantt_df['status'] == status_filter]

    if not gantt_df.empty and harvest_filter != 'all':
        # Filter based on harvest type in the Task column
        if harvest_filter == '24_deepwell':
            gantt_df = gantt_df[gantt_df['harvest_type'] == '24 Deepwell']
        elif harvest_filter == 'shake_flask':
            gantt_df = gantt_df[gantt_df['harvest_type'] == 'Shake Flask']

    if not gantt_df.empty and start_date and end_date:
        gantt_df = gantt_df[
            (gantt_df['Start'] >= pd.to_datetime(start_date).date()) |
            (gantt_df['Finish'] <= pd.to_datetime(end_date).date())
        ]

    gantt_chart = create_gantt_chart(gantt_df, status_filter, harvest_filter, start_date, end_date)

    # Projects table with Edit Steps buttons
    projects_data = get_recent_projects()
    if projects_data:
        # Add project ID to each row for the edit functionality
        for project in projects_data:
            project['project_id'] = project['id']  # Use the actual database ID
            project['edit_action'] = "Edit Steps"

        projects_table = html.Div([
            dash_table.DataTable(
                id="projects-datatable",
                data=projects_data,
                columns=[
                    {'name': 'Project', 'id': 'project_number'},
                    {'name': 'Edit', 'id': 'edit_action'},
                    {'name': 'SIP Number', 'id': 'sip_number'},
                    {'name': 'Samples', 'id': 'samples', 'type': 'numeric'},
                    {'name': 'Start', 'id': 'start_date'},
                    {'name': 'Harvest', 'id': 'harvest_date'},
                    {'name': 'Type', 'id': 'harvest_type'},
                    {'name': 'Status', 'id': 'status'},
                ],
                style_cell={'textAlign': 'left', 'fontSize': '12px'},
                style_data_conditional=[
                    {
                        'if': {'column_id': 'edit_action'},
                        'backgroundColor': '#007bff',
                        'color': 'white',
                        'textAlign': 'center',
                    },
                    {
                        'if': {'filter_query': '{status} = Complete', 'column_id': 'status'},
                        'backgroundColor': '#d4edda',
                        'color': 'black',
                    }
                ],
                page_size=10,
                sort_action="native",
                filter_action="native"
            ),
            # Store for tracking clicked project
            dcc.Store(id="selected-project-id")
        ])
    else:
        projects_table = html.P("No projects found", className="text-muted")

    # Upcoming deadlines table
    deadlines = get_upcoming_deadlines()
    if deadlines:
        deadline_table = dash_table.DataTable(
            data=deadlines,
            columns=[
                {'name': 'Project', 'id': 'project_number'},
                {'name': 'Date', 'id': 'harvest_date'},
                {'name': 'Days', 'id': 'days_remaining', 'type': 'numeric'},
                {'name': 'Type', 'id': 'harvest_type'},
                {'name': 'Samples', 'id': 'samples', 'type': 'numeric'},
                {'name': 'Status', 'id': 'status'},
                {'name': 'Urgency', 'id': 'urgency'},
            ],
            style_cell={'textAlign': 'left'},
            style_data_conditional=[
                {
                    'if': {'filter_query': '{urgency} = High'},
                    'backgroundColor': '#f8d7da',
                    'color': 'black',
                },
                {
                    'if': {'filter_query': '{urgency} = Medium'},
                    'backgroundColor': '#fff3cd',
                    'color': 'black',
                },
                {
                    'if': {'filter_query': '{urgency} = Low'},
                    'backgroundColor': '#d4edda',
                    'color': 'black',
                }
            ],
            page_size=10,
            sort_action="native"
        )
    else:
        deadline_table = html.P("No upcoming deadlines in the next 14 days", className="text-muted")

    # Analytics overview chart
    analytics_data = CLDAnalytics.objects.values('status').annotate(count=Count('id'))
    if analytics_data:
        status_counts = {item['status']: item['count'] for item in analytics_data}

        analytics_fig = go.Figure(data=[go.Pie(
            labels=list(status_counts.keys()),
            values=list(status_counts.values()),
            hole=0.4,
            marker=dict(colors=['#ffc107', '#17a2b8', '#28a745', '#6c757d'])
        )])

        analytics_fig.update_layout(
            title="Analytics Status Distribution",
            height=300,
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.1)
        )
    else:
        analytics_fig = go.Figure()
        analytics_fig.add_annotation(
            text="No analytics data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        analytics_fig.update_layout(height=300, showlegend=False)

    # Wrap gantt_chart in dcc.Graph component
    gantt_component = dcc.Graph(figure=gantt_chart, id="gantt-chart-graph")

    return summary_cards, gantt_component, projects_table, deadline_table, analytics_fig

# Callback for handling project table clicks and loading step data into store
@app.callback(
    [Output("steps-modal", "is_open"),
     Output("edit-steps-project-id", "data"),
     Output("edit-steps-store", "data")],
    [Input("projects-datatable", "active_cell")],
    [State("projects-datatable", "data"),
     State("steps-modal", "is_open")]
)
def handle_table_click(active_cell, table_data, modal_open):
    if not active_cell or not table_data:
        return modal_open, None, {'version': 0, 'steps': []}

    # Check if user clicked on the Edit column
    if active_cell['column_id'] == 'edit_action':
        row_index = active_cell['row']
        project_data = table_data[row_index]
        project_id = project_data.get('project_id')

        # Load step data from database into store
        steps_data = load_project_steps(project_id)
        print(f"[DEBUG] Loading {len(steps_data)} steps into store for project {project_id}")
        return True, project_id, {'version': 1, 'steps': steps_data}

    return modal_open, None, {'version': 0, 'steps': []}

def load_project_steps(project_id):
    """Load project steps from database into a simple data structure"""
    try:
        project = CLDProject.objects.get(id=project_id)
        steps = project.process_steps.all().order_by('step_order')

        steps_data = []
        for step in steps:
            steps_data.append({
                'id': step.id,
                'step_name': step.step_name,
                'planned_duration': step.planned_duration_days,
                'status': step.status,
                'actual_duration': step.actual_duration_days,
                'actual_end_date': str(step.actual_end_date) if step.actual_end_date else None,
                'order': step.step_order
            })
        return steps_data
    except:
        return []

def save_steps_to_database(project_id, steps_data):
    """Save the reordered steps back to database"""
    try:
        project = CLDProject.objects.get(id=project_id)

        # Update each step's order in database
        for step_data in steps_data:
            step = CLDProcessStep.objects.get(id=step_data['id'])
            step.step_order = step_data['order']
            step.save()

        print(f"[DEBUG] Saved {len(steps_data)} steps to database")
        return True
    except Exception as e:
        print(f"[DEBUG ERROR] Failed to save to database: {e}")
        return False

def save_steps_with_timeline(project_id, steps_data):
    """Save steps with updated timeline information to database"""
    try:
        project = CLDProject.objects.get(id=project_id)

        for step_data in steps_data:
            step = CLDProcessStep.objects.get(id=step_data['id'])
            step.step_order = step_data['order']
            step.status = step_data.get('status', 'Pending')

            # Save actual dates and durations if available
            if step_data.get('actual_end_date'):
                from datetime import datetime
                step.actual_end_date = datetime.strptime(step_data['actual_end_date'], '%Y-%m-%d').date()

            if step_data.get('actual_duration'):
                step.actual_duration_days = step_data['actual_duration']

            step.save()

        print(f"[DEBUG] Saved {len(steps_data)} steps with timeline to database")
        return True
    except Exception as e:
        print(f"[DEBUG ERROR] Failed to save timeline: {e}")
        return False

def recalculate_timeline(steps_data):
    """Recalculate the project timeline based on actual vs planned durations"""
    from datetime import datetime, timedelta

    cumulative_shift = 0  # Track how many days ahead/behind schedule

    for i, step in enumerate(steps_data):
        if step['status'] == 'Complete' and step.get('actual_duration'):
            # Calculate the difference from planned
            planned = step['planned_duration']
            actual = step['actual_duration']
            shift = actual - planned
            cumulative_shift += shift

            # Update expected dates for subsequent steps
            if i < len(steps_data) - 1:
                next_step = steps_data[i + 1]
                # Adjust the expected start/end dates (stored as metadata)
                if not next_step.get('timeline_shift'):
                    next_step['timeline_shift'] = 0
                next_step['timeline_shift'] = cumulative_shift

                print(f"[DEBUG] Step '{step['step_name']}' took {actual} days (planned {planned})")
                print(f"[DEBUG] Timeline shifted by {shift} days, cumulative shift: {cumulative_shift} days")

    return cumulative_shift

# FIXED: Updated callback to render the UI from the store data with proper keying
@app.callback(
    Output("project-steps-wrapper", "children"),
    [Input("edit-steps-store", "data")],
    [State("edit-steps-project-id", "data")]
)
def render_steps_from_store(store_data, project_id):
    """Render the step editing UI from the store data with proper keying"""

    if not store_data or not store_data.get('steps'):
        print(f"[DEBUG RENDER] No steps data in store")
        return html.Div("No steps found", className="text-center text-muted")

    steps_data = store_data['steps']
    version = store_data.get('version', 0)
    print(f"[DEBUG RENDER] Rendering {len(steps_data)} steps from store version {version}")
    print(f"[DEBUG RENDER] Step order: {[s['step_name'] for s in steps_data]}")

    # Calculate cumulative timeline shift
    cumulative_shift = 0
    for step in steps_data:
        if step.get('timeline_shift'):
            cumulative_shift = step['timeline_shift']

    step_components = []
    for i, step in enumerate(steps_data):
        # Use a unique key that changes when order changes
        unique_key = step.get('_ui_key', f"step-{i}-{step['step_name']}-{version}")
        step_card = create_simple_step_card(i, step, key=unique_key)
        step_components.append(step_card)

    # Timeline status alert
    timeline_alert = None
    if cumulative_shift != 0:
        if cumulative_shift > 0:
            timeline_alert = dbc.Alert(
                [html.I(className="fas fa-exclamation-triangle me-2"),
                 f"Project is {cumulative_shift} days behind schedule"],
                color="warning",
                className="mb-3"
            )
        else:
            timeline_alert = dbc.Alert(
                [html.I(className="fas fa-check-circle me-2"),
                 f"Project is {abs(cumulative_shift)} days ahead of schedule"],
                color="success",
                className="mb-3"
            )

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H6(f"Edit Steps for Project {project_id}", className="mb-3"),
            ], md=8),
            dbc.Col([
                dbc.Button(
                    [html.I(className="fas fa-plus me-2"), "Add Step"],
                    id="add-edit-step-btn",
                    color="success",
                    size="sm",
                    outline=True
                ),
            ], md=4, className="text-end"),
        ], className="mb-3"),
        timeline_alert if timeline_alert else html.Div(),
        html.Div(id="edit-steps-container", children=step_components),
        html.Hr(),
        dbc.Alert(
            "Update step status and completion dates to track progress. Timeline automatically adjusts based on actual durations.",
            color="info",
            className="mt-3"
        )
    ])  # Key the entire wrapper

# FIXED: Updated create_simple_step_card function to accept and use a key parameter
def create_simple_step_card(index, step_data, key=None):
    """Create an editable step card with drag handle and status/completion date"""

    # Calculate actual duration if step is complete
    actual_duration_display = ""
    if step_data.get('actual_duration'):
        actual_duration_display = f"{step_data['actual_duration']} days (actual)"
    elif step_data.get('status') == 'Complete' and step_data.get('actual_end_date'):
        actual_duration_display = "Calculating..."

    # Use provided key or generate one
    if not key:
        import time
        key = f"step-{step_data.get('id', index)}-{step_data.get('_timestamp', time.time())}"

    return html.Div([
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    # Drag handle column
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-grip-vertical text-muted",
                                  style={'fontSize': '20px', 'cursor': 'move'}),
                        ], className="d-flex align-items-center justify-content-center h-100")
                    ], md=1),

                    dbc.Col([
                        dbc.Label(f"Step {index + 1}: {step_data['step_name']}",
                                 className="fw-bold text-primary mb-1"),
                        html.Small(f"Planned: {step_data['planned_duration']} days",
                                  className="text-muted")
                    ], md=2),

                    dbc.Col([
                        dbc.Label("Status", className="small"),
                        dcc.Dropdown(
                            id={'type': 'step-status', 'index': index},
                            options=[
                                {'label': 'Pending', 'value': 'Pending'},
                                {'label': 'In Progress', 'value': 'In Progress'},
                                {'label': 'Complete', 'value': 'Complete'},
                                {'label': 'Skipped', 'value': 'Skipped'}
                            ],
                            value=step_data.get('status', 'Pending'),
                            clearable=False,
                            style={'fontSize': '12px'}
                        )
                    ], md=2),

                    dbc.Col([
                        dbc.Label("Completion Date", className="small"),
                        dcc.DatePickerSingle(
                            id={'type': 'step-completion-date', 'index': index},
                            date=step_data.get('actual_end_date'),
                            display_format="YYYY-MM-DD",
                            disabled=step_data.get('status') != 'Complete',
                            style={'width': '100%'}
                        )
                    ], md=2),

                    dbc.Col([
                        dbc.Label("Actual Duration", className="small"),
                        html.Div(
                            actual_duration_display or "-",
                            className="text-info fw-bold" if actual_duration_display else "text-muted"
                        )
                    ], md=2),

                    dbc.Col([
                        dbc.ButtonGroup([
                            dbc.Button(
                                html.I(className="fas fa-arrow-up"),
                                id={'type': 'move-up', 'index': index},
                                color="info",
                                size="sm",
                                outline=True,
                                disabled=index == 0,
                                title="Move up"
                            ),
                            dbc.Button(
                                html.I(className="fas fa-arrow-down"),
                                id={'type': 'move-down', 'index': index},
                                color="info",
                                size="sm",
                                outline=True,
                                title="Move down"
                            ),
                            dbc.Button(
                                html.I(className="fas fa-trash"),
                                id={'type': 'remove-step', 'index': index},
                                color="danger",
                                size="sm",
                                outline=True,
                                title="Remove step"
                            )
                        ])
                    ], md=3, className="text-end")
                ])
            ])
        ], className="mb-2 shadow-sm")
    ], id={'type': 'step-card', 'index': index})

def create_project_steps_editor(project_id):
    """Create the step editing interface for a project"""
    print(f"\n[DEBUG EDITOR] create_project_steps_editor called for project_id={project_id}")
    try:
        # Fetch actual steps from database
        project = CLDProject.objects.get(id=project_id)
        steps = project.process_steps.all().order_by('step_order')
        print(f"[DEBUG EDITOR] Found {steps.count()} steps in database")

        if not steps:
            # Fallback to default steps if none exist
            steps_data = get_default_workflow_steps()
        else:
            steps_data = []
            for step in steps:
                steps_data.append({
                    'step_name': step.step_name,
                    'planned_duration': step.planned_duration_days,
                    'status': step.status,
                    'actual_duration': step.actual_duration_days,
                    'actual_end_date': step.actual_end_date,
                    'order': step.step_order
                })
    except:
        # Fallback if project not found
        steps_data = get_default_workflow_steps()

    step_components = []
    for i, step in enumerate(steps_data):
        step_card = create_edit_step_card(i, step)
        step_components.append(step_card)
        print(f"[DEBUG EDITOR] Created card {i} for step: {step.get('step_name', 'Unknown')}")

    print(f"[DEBUG EDITOR] Total components created: {len(step_components)}")
    print(f"[DEBUG EDITOR] Returning structure with edit-steps-container")

    return [
        dbc.Row([
            dbc.Col([
                html.H6(f"Edit Steps for Project {project_id}", className="mb-3"),
            ], md=8),
            dbc.Col([
                dbc.Button(
                    [html.I(className="fas fa-plus me-2"), "Add Step"],
                    id="add-edit-step-btn",
                    color="success",
                    size="sm",
                    outline=True
                ),
            ], md=4, className="text-end"),
        ], className="mb-3"),
        html.Div(id="edit-steps-container", children=step_components),
        html.Hr(),
        dbc.Alert(
            "You can add, remove, and reorder steps. Changes to durations will automatically shift subsequent step timelines.",
            color="info",
            className="mt-3"
        )
    ]

def create_edit_step_card(step_index, step_data, key=None):
    """Create an editable step card for the edit modal"""
    print(f"[DEBUG CARD] Creating edit step card: index={step_index}, step={step_data.get('step_name', 'Unknown')}, key={key}")

    available_steps = [
        'Transfection', 'mP/BP', 'Recovery', 'Beacon',
        'Grow Up', 'Cydem', 'Harvest', 'Purification', 'Analytics'
    ]

    card_props = {"key": key} if key else {}

    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Step Type", className="small fw-bold"),
                    dcc.Dropdown(
                        id={"type": "edit-step-type", "index": step_index},
                        options=[{'label': step, 'value': step} for step in available_steps],
                        value=step_data['step_name'],
                        clearable=False,
                        style={'fontSize': '12px'}
                    ),
                ], md=2),
                dbc.Col([
                    dbc.Label("Planned Duration", className="small fw-bold"),
                    dbc.Input(
                        id={"type": "edit-step-duration", "index": step_index},
                        type="number",
                        value=step_data['planned_duration'],
                        min=1,
                        max=60,
                        size="sm"
                    ),
                ], md=2),
                dbc.Col([
                    dbc.Label("Status", className="small fw-bold"),
                    dcc.Dropdown(
                        id={"type": "edit-step-status", "index": step_index},
                        options=[
                            {'label': 'Pending', 'value': 'Pending'},
                            {'label': 'In Progress', 'value': 'In Progress'},
                            {'label': 'Complete', 'value': 'Complete'},
                            {'label': 'Skipped', 'value': 'Skipped'},
                        ],
                        value=step_data['status'],
                        clearable=False,
                        style={'fontSize': '12px'}
                    ),
                ], md=2),
                dbc.Col([
                    dbc.Label("Completion Date", className="small fw-bold"),
                    dcc.DatePickerSingle(
                        id={"type": "edit-step-completion", "index": step_index},
                        date=step_data.get('actual_end_date') if step_data['status'] == 'Complete' else None,
                        display_format="YYYY-MM-DD",
                        style={'fontSize': '12px', 'width': '100%'}
                    ),
                ], md=2),
                dbc.Col([
                    dbc.Label("Actual Duration (calculated)", className="small fw-bold"),
                    dbc.Input(
                        id=f"edit-step-actual-{step_index}",
                        type="number",
                        value=step_data['actual_duration'] or "",
                        size="sm",
                        disabled=True,  # Read-only - calculated automatically
                        style={'backgroundColor': '#f8f9fa'}
                    ),
                ], md=2),
                dbc.Col([
                    dbc.Label("Actions", className="small fw-bold"),
                    html.Div([
                        dbc.ButtonGroup([
                            dbc.Button(
                                html.I(className="fas fa-arrow-up"),
                                id={"type": "edit-step-up", "index": step_index},
                                color="info",
                                size="sm",
                                outline=True,
                                title="Move up"
                            ),
                            dbc.Button(
                                html.I(className="fas fa-arrow-down"),
                                id={"type": "edit-step-down", "index": step_index},
                                color="info",
                                size="sm",
                                outline=True,
                                title="Move down"
                            ),
                        ], className="me-2"),
                        dbc.Button(
                            html.I(className="fas fa-trash"),
                            id={"type": "edit-step-remove", "index": step_index},
                            color="danger",
                            size="sm",
                            outline=True,
                            title="Remove step"
                        ),
                    ])
                ], md=2),
            ])
        ])
    ], className="mb-2", **card_props)

def calculate_timeline_impact(step):
    """Calculate and display timeline impact of duration changes"""
    if step['actual_duration'] and step['planned_duration']:
        difference = step['actual_duration'] - step['planned_duration']
        if difference > 0:
            return f"+{difference} days (delayed)"
        elif difference < 0:
            return f"{difference} days (ahead)"
        else:
            return "On schedule"
    return "Not set"

def create_step_card(step_index, step_name="", duration=1, is_edit_mode=False):
    """Create a step configuration card"""
    available_steps = [
        'Transfection', 'mP/BP', 'Recovery', 'Beacon',
        'Grow Up', 'Cydem', 'Harvest', 'Purification', 'Analytics'
    ]

    step_id_prefix = "edit-step" if is_edit_mode else "step"

    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Step Type", className="small fw-bold"),
                    dcc.Dropdown(
                        id=f"{step_id_prefix}-type-{step_index}",
                        options=[{'label': step, 'value': step} for step in available_steps],
                        value=step_name,
                        clearable=False,
                        style={'fontSize': '12px'}
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Label("Duration (days)", className="small fw-bold"),
                    dbc.Input(
                        id=f"{step_id_prefix}-duration-{step_index}",
                        type="number",
                        value=duration,
                        min=1,
                        max=60,
                        size="sm"
                    ),
                ], md=3),
                dbc.Col([
                    dbc.Label("Actions", className="small fw-bold"),
                    html.Div([
                        dbc.ButtonGroup([
                            dbc.Button(
                                html.I(className="fas fa-arrow-up"),
                                id=f"{step_id_prefix}-up-{step_index}",
                                color="info",
                                size="sm",
                                outline=True,
                                title="Move up"
                            ),
                            dbc.Button(
                                html.I(className="fas fa-arrow-down"),
                                id=f"{step_id_prefix}-down-{step_index}",
                                color="info",
                                size="sm",
                                outline=True,
                                title="Move down"
                            ),
                        ], className="me-2"),
                        dbc.Button(
                            html.I(className="fas fa-trash"),
                            id=f"{step_id_prefix}-remove-{step_index}",
                            color="danger",
                            size="sm",
                            outline=True,
                            title="Remove step"
                        ),
                    ])
                ], md=3),
            ])
        ])
    ], className="mb-2")

def get_workflow_template(template_type='standard'):
    """Get workflow steps based on template type"""
    templates = {
        'standard': [
            {'step_name': 'Transfection', 'duration': 1, 'order': 1},
            {'step_name': 'mP/BP', 'duration': 1, 'order': 2},
            {'step_name': 'Recovery', 'duration': 14, 'order': 3},
            {'step_name': 'Beacon', 'duration': 14, 'order': 4},
            {'step_name': 'Grow Up', 'duration': 21, 'order': 5},
            {'step_name': 'Cydem', 'duration': 14, 'order': 6},
            {'step_name': 'Harvest', 'duration': 1, 'order': 7},
            {'step_name': 'Purification', 'duration': 2, 'order': 8},
            {'step_name': 'Analytics', 'duration': 4, 'order': 9},
        ],
        'fast_track': [
            {'step_name': 'Transfection', 'duration': 1, 'order': 1},
            {'step_name': 'Recovery', 'duration': 10, 'order': 2},
            {'step_name': 'Beacon', 'duration': 10, 'order': 3},
            {'step_name': 'Grow Up', 'duration': 14, 'order': 4},
            {'step_name': 'Harvest', 'duration': 1, 'order': 5},
            {'step_name': 'Analytics', 'duration': 3, 'order': 6},
        ],
        'minimal': [
            {'step_name': 'Transfection', 'duration': 1, 'order': 1},
            {'step_name': 'Recovery', 'duration': 12, 'order': 2},
            {'step_name': 'Harvest', 'duration': 1, 'order': 3},
            {'step_name': 'Analytics', 'duration': 2, 'order': 4},
        ],
        'custom': []  # Empty for custom workflows
    }
    return templates.get(template_type, templates['standard'])

def get_default_workflow_steps():
    """Get default workflow steps for new projects"""
    return get_workflow_template('standard')

# Callback for closing step editing modal and saving changes
@app.callback(
    [Output("steps-modal", "is_open", allow_duplicate=True),
     Output("alert-container", "children", allow_duplicate=True)],
    [Input("cancel-steps-modal", "n_clicks"),
     Input("save-steps", "n_clicks")],
    [State("steps-modal", "is_open"),
     State("edit-steps-project-id", "data"),
     State("edit-steps-container", "children")],
    prevent_initial_call=True
)
def close_steps_modal(cancel_clicks, save_clicks, is_open, project_id, steps_container):
    if cancel_clicks:
        return False, []

    if save_clicks:
        # Since real-time saving is already happening through the update_step_data callback,
        # we just need to close the modal and show a success message
        success_alert = dbc.Alert(
            "Changes saved successfully! Project timeline has been updated.",
            color="success",
            dismissable=True,
            duration=4000
        )
        return False, success_alert

    return is_open, []

@app.callback(
    [Output("project-modal", "is_open"),
     Output("modal-title", "children"),
     Output("edit-project-store", "data"),
     Output("project-id-input", "value"),
     Output("sip-number-input", "value"),
     Output("transfection-start-date", "date"),
     Output("transfection-type-select", "value"),
     Output("transfection-amount-input", "value"),
     Output("options-select", "value"),
     Output("num-samples-input", "value"),
     Output("purification-type-select", "value"),
     Output("status-select", "value"),
     Output("analytics-checklist", "value"),
     Output("notes-input", "value")],
    [Input("new-project-btn", "n_clicks"),
     Input("cancel-modal", "n_clicks"),
     Input("save-project", "n_clicks")],
    [State("project-modal", "is_open"),
     State("edit-project-store", "data"),
     State("project-id-input", "value"),
     State("sip-number-input", "value"),
     State("transfection-start-date", "date"),
     State("transfection-type-select", "value"),
     State("transfection-amount-input", "value"),
     State("options-select", "value"),
     State("num-samples-input", "value"),
     State("purification-type-select", "value"),
     State("status-select", "value"),
     State("analytics-checklist", "value"),
     State("notes-input", "value")]
)
def handle_project_modal(new_clicks, cancel_clicks, save_clicks, is_open, edit_data,
                        project_id, sip_number, transfection_start_date, transfection_type,
                        transfection_amount, options, num_samples, purification_type,
                        status, analytics, notes):

    # Default values (modal closed, default form values)
    default_values = (False, "Create New Project", None, "", "", date.today(),
                     "Lonza", 0.0, "Minipool", None, "PROA", "Planning", ["SEC", "Titer"], "")

    # If no clicks yet, return defaults
    if not any([new_clicks, cancel_clicks, save_clicks]):
        return default_values

    # If new project button clicked
    if new_clicks and (not cancel_clicks and not save_clicks):
        return (True, "Create New Project", None, "", "", date.today(),
                "Lonza", 0.0, "Minipool", None, "PROA", "Planning", ["SEC", "Titer"], "")

    # If cancel button clicked
    if cancel_clicks:
        return default_values

    # If save button clicked
    if save_clicks:
        # Validate required fields
        if not project_id or not sip_number or not num_samples or not transfection_start_date:
            # Keep modal open if required fields are missing
            return (is_open, "Create New Project", edit_data, project_id, sip_number,
                    transfection_start_date, transfection_type, transfection_amount,
                    options, num_samples, purification_type, status, analytics, notes)

        try:
            # Create new project with new fields
            project = CLDProject.objects.create(
                project_id=project_id,
                sip_number=sip_number,
                project_number=project_id,  # Use project_id as project_number for compatibility
                number_of_samples=int(num_samples),
                transfection_start_date=pd.to_datetime(transfection_start_date).date(),
                transfection_type=transfection_type,
                transfection_amount_mg=float(transfection_amount) if transfection_amount else 0.0,
                options=options,
                start_date=pd.to_datetime(transfection_start_date).date(),  # Use transfection date as start
                purification_type=purification_type,
                status=status,
                notes=notes or ""
            )

            # Create analytics entries
            if analytics:
                for analysis_type in analytics:
                    CLDAnalytics.objects.create(
                        project=project,
                        analysis_type=analysis_type,
                        required=True,
                        status='Pending'
                    )

            # Create process steps for the project
            # Note: We'll collect these from the dynamic form in a future update
            # For now, use default steps as fallback
            default_steps = get_default_workflow_steps()

            for step_config in default_steps:
                CLDProcessStep.objects.create(
                    project=project,
                    step_name=step_config['step_name'],
                    step_order=step_config['order'],
                    planned_duration_days=step_config['duration'],
                    status='Pending'
                )

            # Close modal and reset form
            return default_values

        except Exception as e:
            # Keep modal open if there's an error
            print(f"Error creating project: {e}")
            return (is_open, "Create New Project", edit_data, project_id, sip_number,
                    transfection_start_date, transfection_type, transfection_amount,
                    options, num_samples, purification_type, status, analytics, notes)

    # Default fallback
    return (is_open, "Create New Project", edit_data, project_id, sip_number,
            transfection_start_date, transfection_type, transfection_amount,
            options, num_samples, purification_type, status, analytics, notes)

@app.callback(
    Output("alert-container", "children", allow_duplicate=True),
    [Input("save-project", "n_clicks")],
    [State("project-id-input", "value"),
     State("sip-number-input", "value"),
     State("num-samples-input", "value"),
     State("transfection-start-date", "date")],
    prevent_initial_call=True
)
def show_alerts(save_clicks, project_id, sip_number, num_samples, transfection_start_date):
    if not save_clicks:
        return []

    # Validation
    if not project_id or not sip_number or not num_samples or not transfection_start_date:
        return dbc.Alert(
            "Please fill in all required fields (Project ID, SIP Number, Number of Samples, Transfection Start Date).",
            color="danger",
            dismissable=True,
            duration=5000
        )

    try:
        if int(num_samples) <= 0:
            return dbc.Alert(
                "Number of samples must be greater than 0.",
                color="danger",
                dismissable=True,
                duration=5000
            )
    except (ValueError, TypeError):
        return dbc.Alert(
            "Please enter a valid number for samples.",
            color="danger",
            dismissable=True,
            duration=5000
        )

    # If we get here, the project was likely created successfully
    return dbc.Alert(
        f"Project {project_id} created successfully!",
        color="success",
        dismissable=True,
        duration=3000
    )

# Add callback to refresh dashboard after project creation
@app.callback(
    Output("refresh-interval", "n_intervals"),
    [Input("save-project", "n_clicks")],
    [State("refresh-interval", "n_intervals")]
)
def refresh_after_save(save_clicks, current_intervals):
    if save_clicks and save_clicks > 0:
        return current_intervals + 1
    return current_intervals