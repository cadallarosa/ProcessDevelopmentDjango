"""
Modal components for Project Management Dashboard
"""
import dash_bootstrap_components as dbc
from dash import html, dcc
from .forms import (
    create_project_form, create_bulk_status_update_form,
    create_decision_form, create_score_breakdown_display
)
from .tables import create_decision_history_table


def create_project_modal() -> dbc.Modal:
    """
    Create modal for creating/editing projects.

    Returns:
        Modal component
    """
    return dbc.Modal([
        dbc.ModalHeader([
            html.H5(id="project-modal-title", className="mb-0")
        ], close_button=True),
        dbc.ModalBody([
            # Alert for messages
            html.Div(id="project-modal-alert", className="mb-3"),

            # Tabs for different sections
            dbc.Tabs([
                dbc.Tab([
                    html.Div([
                        create_project_form(),
                    ], className="p-3")
                ], label="Project Details", tab_id="project-details-tab"),

                dbc.Tab([
                    html.Div([
                        html.Div(id="project-modal-score-breakdown"),
                    ], className="p-3")
                ], label="Score Breakdown", tab_id="score-breakdown-tab"),

                dbc.Tab([
                    html.Div([
                        html.Div(id="project-modal-decision-history"),
                    ], className="p-3")
                ], label="Decision History", tab_id="decision-history-tab"),
            ], id="project-modal-tabs", active_tab="project-details-tab"),
        ], style={"maxHeight": "70vh", "overflowY": "auto"}),
        dbc.ModalFooter([
            dbc.Button(
                [html.I(className="bi bi-x-circle me-2"), "Cancel"],
                id="project-modal-cancel",
                color="secondary",
                size="sm",
                outline=True,
                className="me-2"
            ),
            dbc.Button(
                [html.I(className="bi bi-save me-2"), "Save Project"],
                id="project-modal-save",
                color="primary",
                size="sm"
            )
        ])
    ], id="project-modal", is_open=False, size="xl", backdrop="static", scrollable=True)


def create_bulk_update_modal() -> dbc.Modal:
    """
    Create modal for bulk status updates.

    Returns:
        Modal component
    """
    return dbc.Modal([
        dbc.ModalHeader([
            html.H5("Bulk Status Update", className="mb-0")
        ], close_button=True),
        dbc.ModalBody([
            # Alert for messages
            html.Div(id="bulk-update-alert", className="mb-3"),

            # Bulk update form
            create_bulk_status_update_form(),
        ]),
        dbc.ModalFooter([
            dbc.Button(
                [html.I(className="bi bi-x-circle me-2"), "Cancel"],
                id="bulk-update-cancel",
                color="secondary",
                size="sm",
                outline=True,
                className="me-2"
            ),
            dbc.Button(
                [html.I(className="bi bi-check-circle me-2"), "Update Projects"],
                id="bulk-update-confirm",
                color="primary",
                size="sm"
            )
        ])
    ], id="bulk-update-modal", is_open=False, size="lg", backdrop="static")


def create_decision_modal() -> dbc.Modal:
    """
    Create modal for logging decisions.

    Returns:
        Modal component
    """
    return dbc.Modal([
        dbc.ModalHeader([
            html.H5("Log Decision", className="mb-0")
        ], close_button=True),
        dbc.ModalBody([
            # Alert for messages
            html.Div(id="decision-modal-alert", className="mb-3"),

            # Project info
            dbc.Card([
                dbc.CardBody([
                    html.Div(id="decision-modal-project-info")
                ])
            ], className="mb-3", color="light"),

            # Decision form
            create_decision_form(),

            # Hidden store for project ID
            dcc.Store(id='decision-modal-project-id'),
        ]),
        dbc.ModalFooter([
            dbc.Button(
                [html.I(className="bi bi-x-circle me-2"), "Cancel"],
                id="decision-modal-cancel",
                color="secondary",
                size="sm",
                outline=True,
                className="me-2"
            ),
            dbc.Button(
                [html.I(className="bi bi-save me-2"), "Log Decision"],
                id="decision-modal-save",
                color="primary",
                size="sm"
            )
        ])
    ], id="decision-modal", is_open=False, size="lg", backdrop="static")


def create_project_detail_modal() -> dbc.Modal:
    """
    Create modal for viewing detailed project information.
    Opens when clicking on molecule images in table or Gantt chart.

    Returns:
        Modal component
    """
    return dbc.Modal([
        dbc.ModalHeader([
            html.Div([
                html.H5(id="project-detail-modal-title", children="Project Details", className="mb-0"),
            ], style={'flex': '1'}),
            html.Div([
                dbc.Button(
                    [html.I(className="bi bi-pencil me-1"), "Edit"],
                    id="project-detail-edit-btn",
                    color="primary",
                    size="sm",
                    className="me-2"
                ),
            ], style={'display': 'flex', 'gap': '10px'}),
        ], close_button=True, style={'display': 'flex', 'justifyContent': 'space-between', 'width': '100%'}),
        dbc.ModalBody([
            # Store for selected project ID
            dcc.Store(id='project-detail-store', data=None),

            # Alert area for messages
            html.Div(id="project-detail-alert", className="mb-3"),

            # Tabs for different information sections
            dbc.Tabs([
                # Tab 1: Overview
                dbc.Tab([
                    html.Div([
                        dbc.Row([
                            # Left column - Image
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Img(
                                            id="project-detail-image",
                                            style={
                                                'width': '100%',
                                                'maxWidth': '300px',
                                                'height': 'auto',
                                                'borderRadius': '8px'
                                            }
                                        ),
                                    ], className="text-center")
                                ], className="shadow-sm")
                            ], md=4),

                            # Right column - Basic Info
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H6("Project Information", className="mb-3"),
                                        html.Div(id="project-detail-basic-info")
                                    ])
                                ], className="shadow-sm")
                            ], md=8),
                        ], className="mb-3"),

                        # Timeline Section
                        dbc.Card([
                            dbc.CardHeader(html.H6("Project Timeline", className="mb-0")),
                            dbc.CardBody([
                                html.Div(id="project-detail-timeline")
                            ])
                        ], className="shadow-sm")
                    ], className="p-3")
                ], label="Overview", tab_id="overview-tab"),

                # Tab 2: Stock Information
                dbc.Tab([
                    html.Div([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Stock Information", className="mb-3"),
                                html.Div(id="project-detail-stock-info"),
                                html.Hr(),
                                html.H6("Update Stock Levels", className="mb-3"),
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Concentration (mg/mL)"),
                                        dbc.Input(
                                            id="stock-concentration-input",
                                            type="number",
                                            placeholder="Enter concentration",
                                            step=0.1
                                        )
                                    ], md=4),
                                    dbc.Col([
                                        dbc.Label("Volume (mL)"),
                                        dbc.Input(
                                            id="stock-volume-input",
                                            type="number",
                                            placeholder="Enter volume",
                                            step=0.1
                                        )
                                    ], md=4),
                                    dbc.Col([
                                        dbc.Label("Location"),
                                        dbc.Input(
                                            id="stock-location-input",
                                            type="text",
                                            placeholder="e.g., Freezer A, Shelf 3"
                                        )
                                    ], md=4),
                                ], className="mb-3"),
                                dbc.Button(
                                    [html.I(className="bi bi-save me-2"), "Update Stock"],
                                    id="update-stock-btn",
                                    color="primary",
                                    size="sm"
                                )
                            ])
                        ], className="shadow-sm")
                    ], className="p-3")
                ], label="Stock", tab_id="stock-tab"),

                # Tab 3: Metrics & Scores
                dbc.Tab([
                    html.Div([
                        html.Div(id="project-detail-metrics")
                    ], className="p-3")
                ], label="Metrics", tab_id="metrics-tab"),

                # Tab 4: Analytics
                dbc.Tab([
                    html.Div([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Analytical Results", className="mb-3"),
                                html.Div(id="project-detail-analytics-info"),
                                html.P("Integration with LIMS analytical data (SEC, CE-SDS, etc.) can be added here.",
                                      className="text-muted mt-3")
                            ])
                        ], className="shadow-sm")
                    ], className="p-3")
                ], label="Analytics", tab_id="analytics-tab"),

            ], id="project-detail-tabs", active_tab="overview-tab"),

        ], style={"maxHeight": "75vh", "overflowY": "auto"}),
        dbc.ModalFooter([
            dbc.Button("Close", id="project-detail-close", color="secondary", size="sm")
        ])
    ], id="project-detail-modal", is_open=False, size="xl", scrollable=True)


def create_comparison_modal() -> dbc.Modal:
    """
    Create modal for comparing multiple projects.

    Returns:
        Modal component
    """
    return dbc.Modal([
        dbc.ModalHeader([
            html.H5("Project Comparison", className="mb-0")
        ], close_button=True),
        dbc.ModalBody([
            html.Div(id="comparison-modal-content"),
        ], style={"maxHeight": "75vh", "overflowY": "auto"}),
        dbc.ModalFooter([
            dbc.Button("Close", id="comparison-modal-close", color="secondary", size="sm")
        ])
    ], id="comparison-modal", is_open=False, size="xl", scrollable=True)


def create_excel_import_modal() -> dbc.Modal:
    """
    Create modal for importing data from Excel.

    Returns:
        Modal component
    """
    return dbc.Modal([
        dbc.ModalHeader([
            html.H5("Import Projects from Excel", className="mb-0")
        ], close_button=True),
        dbc.ModalBody([
            # Alert for messages
            html.Div(id="import-modal-alert", className="mb-3"),

            # Import instructions
            dbc.Card([
                dbc.CardBody([
                    html.H6("Import Instructions", className="mb-3"),
                    html.Ol([
                        html.Li("The system will import projects from the configured Excel file"),
                        html.Li("Existing projects (by Molecule ID) will be skipped"),
                        html.Li("Scores and metrics will be automatically calculated"),
                        html.Li("Review the import summary after completion"),
                    ]),
                    html.Hr(),
                    html.Div([
                        html.Strong("File Path: "),
                        html.Code(id="import-file-path", children=""),
                    ]),
                ])
            ], className="mb-3", color="info", outline=True),

            # Import results
            html.Div(id="import-results", style={'display': 'none'}),

            # Loading spinner
            dcc.Loading(
                id="import-loading",
                type="default",
                children=html.Div(id="import-loading-content")
            ),
        ]),
        dbc.ModalFooter([
            dbc.Button(
                [html.I(className="bi bi-x-circle me-2"), "Cancel"],
                id="import-modal-cancel",
                color="secondary",
                size="sm",
                outline=True,
                className="me-2"
            ),
            dbc.Button(
                [html.I(className="bi bi-upload me-2"), "Start Import"],
                id="import-modal-start",
                color="primary",
                size="sm"
            )
        ])
    ], id="import-modal", is_open=False, size="lg", backdrop="static")


def create_recalculate_scores_modal() -> dbc.Modal:
    """
    Create modal for recalculating all project scores.

    Returns:
        Modal component
    """
    return dbc.Modal([
        dbc.ModalHeader([
            html.H5("Recalculate All Scores", className="mb-0")
        ], close_button=True),
        dbc.ModalBody([
            # Alert for messages
            html.Div(id="recalc-modal-alert", className="mb-3"),

            # Warning message
            dbc.Alert([
                html.I(className="bi bi-exclamation-triangle-fill me-2"),
                html.Strong("Warning: "),
                "This will recalculate scores and recommendations for all projects in the database. "
                "This operation may take a few moments depending on the number of projects."
            ], color="warning"),

            # Results area
            html.Div(id="recalc-results", style={'display': 'none'}),

            # Loading spinner
            dcc.Loading(
                id="recalc-loading",
                type="default",
                children=html.Div(id="recalc-loading-content")
            ),
        ]),
        dbc.ModalFooter([
            dbc.Button(
                [html.I(className="bi bi-x-circle me-2"), "Cancel"],
                id="recalc-modal-cancel",
                color="secondary",
                size="sm",
                outline=True,
                className="me-2"
            ),
            dbc.Button(
                [html.I(className="bi bi-arrow-clockwise me-2"), "Recalculate"],
                id="recalc-modal-start",
                color="primary",
                size="sm"
            )
        ])
    ], id="recalc-modal", is_open=False, size="md", backdrop="static")


def format_project_detail_content(project_data: dict) -> html.Div:
    """
    Format project data for detail modal display.

    Args:
        project_data: Project dictionary

    Returns:
        Formatted HTML Div
    """
    return html.Div([
        # Summary cards row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Status", className="text-muted mb-2"),
                        html.H4(project_data.get('status', 'N/A'), className="mb-0"),
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Priority", className="text-muted mb-2"),
                        html.H4(f"Set {project_data.get('priority_set', 'N/A')}", className="mb-0"),
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Weighted Score", className="text-muted mb-2"),
                        html.H4(f"{project_data.get('weighted_score', 0):.1f}", className="mb-0"),
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Recommendation", className="text-muted mb-2"),
                        html.H4(project_data.get('recommendation', 'N/A'), className="mb-0",
                               style={'fontSize': '14px'}),
                    ])
                ], className="text-center shadow-sm")
            ], md=3),
        ], className="mb-4"),

        # Timeline section
        dbc.Card([
            dbc.CardHeader(html.H6("Timeline", className="mb-0")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Strong("Creation Date: "),
                        html.Span(project_data.get('creation_date', 'Not set')),
                    ], md=4),
                    dbc.Col([
                        html.Strong("Cloning Finish: "),
                        html.Span(project_data.get('cloning_finish_date', 'Not set')),
                    ], md=4),
                    dbc.Col([
                        html.Strong("Purification Finish: "),
                        html.Span(project_data.get('purification_finish_date', 'Not set')),
                    ], md=4),
                ]),
                html.Hr(className="my-2"),
                html.Div([
                    html.Strong("Lead Time: "),
                    html.Span(f"{project_data.get('lead_time', 'N/A')} days" if project_data.get('lead_time') else 'Not calculated'),
                ])
            ])
        ], className="mb-3 shadow-sm"),

        # Team section
        dbc.Card([
            dbc.CardHeader(html.H6("Team", className="mb-0")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Strong("Created By: "),
                        html.Span(project_data.get('created_by', 'Unknown')),
                    ], md=6),
                    dbc.Col([
                        html.Strong("Assigned To: "),
                        html.Span(project_data.get('assigned_to', 'Unassigned')),
                    ], md=6),
                ])
            ])
        ], className="mb-3 shadow-sm"),

        # Notes section
        dbc.Card([
            dbc.CardHeader(html.H6("Notes", className="mb-0")),
            dbc.CardBody([
                html.P(project_data.get('notes', 'No notes available'), className="mb-0"),
            ])
        ], className="mb-3 shadow-sm"),

        # Recommendation section
        dbc.Card([
            dbc.CardHeader(html.H6("System Recommendation", className="mb-0")),
            dbc.CardBody([
                dbc.Alert([
                    html.H5(project_data.get('recommendation', 'N/A'), className="mb-2"),
                    html.P(project_data.get('recommendation_reason', ''), className="mb-0"),
                ], color=get_recommendation_color(project_data.get('recommendation')))
            ])
        ], className="shadow-sm"),
    ])


def get_recommendation_color(recommendation: str) -> str:
    """
    Get Bootstrap color for recommendation.

    Args:
        recommendation: Recommendation string

    Returns:
        Bootstrap color name
    """
    color_map = {
        'PUSH FORWARD': 'success',
        'MONITOR': 'info',
        'REVIEW': 'warning',
        'CONSIDER CANCELLATION': 'danger',
    }
    return color_map.get(recommendation, 'secondary')
