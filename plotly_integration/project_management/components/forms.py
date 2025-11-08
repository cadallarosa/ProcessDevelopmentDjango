"""
Form components for Project Management Dashboard
"""
import dash_bootstrap_components as dbc
from dash import html, dcc
from typing import List, Dict


def create_project_form(project_data: Dict = None, user_options: List[Dict] = None) -> html.Div:
    """
    Create a form for creating/editing a project.

    Args:
        project_data: Existing project data (for editing)
        user_options: List of user options for dropdowns

    Returns:
        Div containing form fields
    """
    if project_data is None:
        project_data = {}

    if user_options is None:
        user_options = []

    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Label("Molecule ID *", className="fw-bold"),
                dbc.Input(
                    id="project-form-molecule-id",
                    type="text",
                    placeholder="Enter molecule ID (e.g., SI-212E18)",
                    value=project_data.get('molecule_id', ''),
                    disabled=bool(project_data),  # Disable if editing (can't change ID)
                )
            ], md=6),
            dbc.Col([
                dbc.Label("Priority Set *", className="fw-bold"),
                dcc.Dropdown(
                    id="project-form-priority",
                    options=[
                        {'label': 'Priority 1 (High)', 'value': 1},
                        {'label': 'Priority 2 (Medium)', 'value': 2},
                        {'label': 'Priority 3 (Low)', 'value': 3},
                    ],
                    value=project_data.get('priority_set', 2),
                    clearable=False
                )
            ], md=6),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col([
                dbc.Label("Status *", className="fw-bold"),
                dcc.Dropdown(
                    id="project-form-status",
                    options=[
                        {'label': 'Active', 'value': 'Active'},
                        {'label': 'On Hold', 'value': 'On Hold'},
                        {'label': 'Cancelled', 'value': 'Cancelled'},
                        {'label': 'Completed', 'value': 'Completed'},
                    ],
                    value=project_data.get('status', 'Active'),
                    clearable=False
                )
            ], md=6),
            dbc.Col([
                dbc.Label("Assigned To", className="fw-bold"),
                dcc.Dropdown(
                    id="project-form-assigned-to",
                    options=user_options,
                    value=project_data.get('assigned_to_id'),
                    placeholder="Select user...",
                    clearable=True
                )
            ], md=6),
        ], className="mb-3"),

        html.Hr(),

        html.H6("Timeline", className="mb-3 text-muted"),

        dbc.Row([
            dbc.Col([
                dbc.Label("Creation Date", className="fw-bold"),
                dbc.Input(
                    id="project-form-creation-date",
                    type="date",
                    value=project_data.get('creation_date', '')
                )
            ], md=4),
            dbc.Col([
                dbc.Label("Cloning Finish Date", className="fw-bold"),
                dbc.Input(
                    id="project-form-cloning-date",
                    type="date",
                    value=project_data.get('cloning_finish_date', '')
                )
            ], md=4),
            dbc.Col([
                dbc.Label("Purification Finish Date", className="fw-bold"),
                dbc.Input(
                    id="project-form-purification-date",
                    type="date",
                    value=project_data.get('purification_finish_date', '')
                )
            ], md=4),
        ], className="mb-3"),

        html.Hr(),

        dbc.Row([
            dbc.Col([
                dbc.Label("Notes", className="fw-bold"),
                dbc.Textarea(
                    id="project-form-notes",
                    placeholder="Enter project notes, comments, or additional information...",
                    value=project_data.get('notes', ''),
                    rows=4,
                    style={'resize': 'vertical'}
                )
            ], md=12),
        ], className="mb-3"),

        # Hidden fields for passing data
        dcc.Store(id='project-form-id', data=project_data.get('id')),
    ])


def create_bulk_status_update_form(user_options: List[Dict] = None) -> html.Div:
    """
    Create form for bulk status updates.

    Args:
        user_options: List of user options

    Returns:
        Div containing bulk update form
    """
    if user_options is None:
        user_options = []

    return html.Div([
        html.P("Update status for selected projects:", className="mb-3"),

        dbc.Row([
            dbc.Col([
                dbc.Label("New Status *", className="fw-bold"),
                dcc.Dropdown(
                    id="bulk-update-status",
                    options=[
                        {'label': 'Active', 'value': 'Active'},
                        {'label': 'On Hold', 'value': 'On Hold'},
                        {'label': 'Cancelled', 'value': 'Cancelled'},
                        {'label': 'Completed', 'value': 'Completed'},
                    ],
                    placeholder="Select new status...",
                    clearable=False
                )
            ], md=12),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col([
                dbc.Label("Rationale *", className="fw-bold"),
                dbc.Textarea(
                    id="bulk-update-rationale",
                    placeholder="Explain reason for this status change...",
                    rows=3,
                    style={'resize': 'vertical'}
                )
            ], md=12),
        ], className="mb-3"),

        dbc.Alert(
            id="bulk-update-selected-count",
            color="info",
            children="No projects selected",
            className="mb-0"
        ),
    ])


def create_decision_form() -> html.Div:
    """
    Create form for logging a decision.

    Returns:
        Div containing decision form
    """
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Label("Decision Type *", className="fw-bold"),
                dcc.Dropdown(
                    id="decision-form-type",
                    options=[
                        {'label': 'Status Change', 'value': 'Status Change'},
                        {'label': 'Priority Change', 'value': 'Priority Change'},
                        {'label': 'Assignment Change', 'value': 'Assignment Change'},
                        {'label': 'Push Forward', 'value': 'Push Forward'},
                        {'label': 'Hold', 'value': 'Hold'},
                        {'label': 'Cancel', 'value': 'Cancel'},
                        {'label': 'Reactivate', 'value': 'Reactivate'},
                    ],
                    placeholder="Select decision type...",
                    clearable=False
                )
            ], md=12),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col([
                dbc.Label("Rationale *", className="fw-bold"),
                dbc.Textarea(
                    id="decision-form-rationale",
                    placeholder="Explain the rationale for this decision...",
                    rows=4,
                    style={'resize': 'vertical'}
                )
            ], md=12),
        ], className="mb-3"),

        dbc.Alert(
            id="decision-form-recommendation",
            color="info",
            children=[
                html.Strong("System Recommendation: "),
                html.Span(id="decision-form-recommendation-text")
            ],
            className="mb-0"
        ),
    ])


def create_filter_controls() -> dbc.Card:
    """
    Create filter controls for the projects table.

    Returns:
        Card containing filter controls
    """
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Status", className="fw-bold"),
                    dcc.Dropdown(
                        id="filter-status",
                        options=[
                            {'label': 'All Statuses', 'value': 'all'},
                            {'label': 'Active', 'value': 'Active'},
                            {'label': 'On Hold', 'value': 'On Hold'},
                            {'label': 'Cancelled', 'value': 'Cancelled'},
                            {'label': 'Completed', 'value': 'Completed'},
                        ],
                        value='all',
                        clearable=False
                    )
                ], md=3),
                dbc.Col([
                    dbc.Label("Priority", className="fw-bold"),
                    dcc.Dropdown(
                        id="filter-priority",
                        options=[
                            {'label': 'All Priorities', 'value': 'all'},
                            {'label': 'Priority 1 (High)', 'value': 1},
                            {'label': 'Priority 2 (Medium)', 'value': 2},
                            {'label': 'Priority 3 (Low)', 'value': 3},
                        ],
                        value='all',
                        clearable=False
                    )
                ], md=3),
                dbc.Col([
                    dbc.Label("Recommendation", className="fw-bold"),
                    dcc.Dropdown(
                        id="filter-recommendation",
                        options=[
                            {'label': 'All Recommendations', 'value': 'all'},
                            {'label': 'Push Forward', 'value': 'PUSH FORWARD'},
                            {'label': 'Monitor', 'value': 'MONITOR'},
                            {'label': 'Review', 'value': 'REVIEW'},
                            {'label': 'Consider Cancellation', 'value': 'CONSIDER CANCELLATION'},
                        ],
                        value='all',
                        clearable=False
                    )
                ], md=3),
                dbc.Col([
                    dbc.Label("Search", className="fw-bold"),
                    dbc.Input(
                        id="filter-search",
                        type="text",
                        placeholder="Search molecule ID, notes...",
                        debounce=True
                    )
                ], md=3),
            ], align="end")
        ])
    ], className="mb-3 shadow-sm")


def create_score_breakdown_display(score_data: Dict) -> html.Div:
    """
    Create a visual display of score breakdown.

    Args:
        score_data: Dictionary with score breakdown

    Returns:
        Div with score visualization
    """
    if not score_data:
        return html.Div("No score data available")

    scores = [
        {'label': 'Priority Score', 'value': score_data.get('priority_score', 0), 'weight': 40, 'color': '#3498db'},
        {'label': 'On-Time Score', 'value': score_data.get('on_time_score', 0), 'weight': 30, 'color': '#2ecc71'},
        {'label': 'Completion Score', 'value': score_data.get('completion_score', 0), 'weight': 20, 'color': '#9b59b6'},
        {'label': 'Resource Score', 'value': score_data.get('resource_score', 0), 'weight': 10, 'color': '#e74c3c'},
    ]

    return html.Div([
        html.H6("Score Breakdown", className="mb-3"),
        html.Div([
            create_score_bar(score['label'], score['value'], score['weight'], score['color'])
            for score in scores
        ]),
        html.Hr(),
        html.Div([
            html.Strong("Weighted Total: "),
            html.Span(
                f"{score_data.get('weighted_total', 0):.1f}",
                className="fs-4 fw-bold",
                style={'color': get_score_color(score_data.get('weighted_total', 0))}
            )
        ], className="text-center mt-3"),
    ])


def create_score_bar(label: str, value: float, weight: int, color: str) -> html.Div:
    """
    Create a single score progress bar.

    Args:
        label: Score label
        value: Score value (0-100)
        weight: Weight percentage
        color: Bar color

    Returns:
        Div with progress bar
    """
    return html.Div([
        html.Div([
            html.Span(label, className="fw-bold"),
            html.Span(f" (Weight: {weight}%)", className="text-muted small"),
            html.Span(f"{value:.1f}", className="float-end fw-bold", style={'color': color}),
        ], className="mb-1"),
        dbc.Progress(
            value=value,
            max=100,
            color="",
            style={'backgroundColor': '#e9ecef', 'height': '20px'},
            bar_style={'backgroundColor': color}
        ),
    ], className="mb-3")


def get_score_color(score: float) -> str:
    """
    Get color based on score value.

    Args:
        score: Score value

    Returns:
        Color hex code
    """
    if score >= 75:
        return '#28a745'  # Green
    elif score >= 50:
        return '#17a2b8'  # Blue
    elif score >= 30:
        return '#ffc107'  # Yellow
    else:
        return '#dc3545'  # Red
