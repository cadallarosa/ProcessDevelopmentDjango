"""
Main layout for Project Management Dashboard
"""
import dash_bootstrap_components as dbc
from dash import html, dcc
from .components.tables import create_projects_table, create_summary_cards
from .components.forms import create_filter_controls
from .components.modals import (
    create_project_modal, create_bulk_update_modal,
    create_decision_modal, create_project_detail_modal,
    create_comparison_modal, create_excel_import_modal,
    create_recalculate_scores_modal
)
from .config import APP_TITLE


def create_layout() -> html.Div:
    """
    Create the main application layout.

    Returns:
        Complete app layout
    """
    return html.Div([
        # Data stores for state management
        create_stores(),

        # All modals
        create_project_modal(),
        create_bulk_update_modal(),
        create_decision_modal(),
        create_project_detail_modal(),
        create_comparison_modal(),
        create_excel_import_modal(),
        create_recalculate_scores_modal(),

        # Main content container
        dbc.Container([
            # Header
            create_header(),

            # Summary cards
            html.Div(id="summary-cards-container", className="mb-4"),

            # Action buttons row
            create_action_buttons(),

            # Filter controls
            create_filter_controls(),

            # Main tabs
            create_main_tabs(),

        ], fluid=True, style={"padding": "20px", "backgroundColor": "#f8f9fa", "minHeight": "100vh"}),

    ])


def create_header() -> dbc.Row:
    """
    Create the application header.

    Returns:
        Header row
    """
    return dbc.Row([
        dbc.Col([
            html.H2([
                html.I(className="bi bi-clipboard-data me-3", style={'color': '#3498db'}),
                APP_TITLE
            ], className="mb-1"),
            html.P(
                "Track, analyze, and make data-driven decisions on protein engineering projects",
                className="text-muted mb-0"
            )
        ], width="auto"),
    ], className="mb-4")


def create_action_buttons() -> dbc.Row:
    """
    Create the action buttons row.

    Returns:
        Row with action buttons
    """
    return dbc.Row([
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button(
                    [html.I(className="bi bi-plus-circle me-2"), "New Project"],
                    id="open-create-project-modal",
                    color="success",
                    size="sm",
                ),
                dbc.Button(
                    [html.I(className="bi bi-pencil-square me-2"), "Bulk Update"],
                    id="open-bulk-update-modal",
                    color="primary",
                    size="sm",
                ),
                dbc.Button(
                    [html.I(className="bi bi-upload me-2"), "Import Excel"],
                    id="open-import-modal",
                    color="info",
                    size="sm",
                ),
            ], className="me-2"),

            dbc.ButtonGroup([
                dbc.Button(
                    [html.I(className="bi bi-arrow-clockwise me-2"), "Refresh"],
                    id="refresh-data-btn",
                    color="secondary",
                    size="sm",
                    outline=True,
                ),
                dbc.Button(
                    [html.I(className="bi bi-calculator me-2"), "Recalculate Scores"],
                    id="open-recalc-modal",
                    color="secondary",
                    size="sm",
                    outline=True,
                ),
                dbc.Button(
                    [html.I(className="bi bi-download me-2"), "Export"],
                    id="export-data-btn",
                    color="secondary",
                    size="sm",
                    outline=True,
                ),
            ]),
        ], width="auto"),
    ], className="mb-3")


def create_main_tabs() -> dbc.Tabs:
    """
    Create the main content tabs.

    Returns:
        Tabs component
    """
    return dbc.Tabs([
        # Tab 1: Projects Table
        dbc.Tab([
            html.Div([
                # Status message area
                html.Div(id="table-status-message", className="mb-2"),

                # Projects table
                dbc.Card([
                    dbc.CardBody([
                        html.Div(id="projects-table-container"),
                    ])
                ], className="shadow-sm"),
            ], className="p-3")
        ], label="Projects Table", tab_id="projects-tab", className="pt-3"),

        # Tab 2: Timeline (Gantt)
        dbc.Tab([
            html.Div([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.H6("Project Timeline", className="mb-0"),
                            dbc.ButtonGroup([
                                dbc.Button("Sort by Date", id="gantt-sort-date", size="sm", color="primary", active=True),
                                dbc.Button("Sort by Priority", id="gantt-sort-priority", size="sm", color="secondary"),
                            ], size="sm"),
                        ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}),
                    ]),
                    dbc.CardBody([
                        dcc.Loading(
                            id="loading-gantt",
                            type="default",
                            children=html.Div(
                                id="gantt-container",
                                style={"overflowY": "auto", "maxHeight": "800px"},
                                children=dcc.Graph(id="gantt-chart", config={'displayModeBar': True})
                            )
                        )
                    ])
                ], className="shadow-sm"),
            ], className="p-3")
        ], label="Timeline", tab_id="timeline-tab", className="pt-3"),

    ], id="main-tabs", active_tab="projects-tab")


def create_stores() -> html.Div:
    """
    Create dcc.Store components for state management.

    Returns:
        Div containing all store components
    """
    return html.Div([
        dcc.Store(id='projects-data-store', data=[]),
        dcc.Store(id='selected-project-store', data=None),
        dcc.Store(id='user-options-store', data=[]),
        dcc.Store(id='filter-state-store', data={
            'status': 'all',
            'priority': 'all',
            'recommendation': 'all',
            'search': ''
        }),
        dcc.Interval(
            id='auto-refresh-interval',
            interval=60*1000,  # Refresh every minute
            n_intervals=0,
            disabled=True  # Disabled by default, can be enabled
        ),
        # Download component for exports
        dcc.Download(id="download-dataframe-xlsx"),
    ])


def create_recommendation_project_card(project: dict) -> dbc.Card:
    """
    Create a card for a project in the recommendations list.

    Args:
        project: Project dictionary

    Returns:
        Card component
    """
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H6(project['molecule_id'], className="mb-1"),
                    html.Small([
                        html.Span(f"Priority {project['priority_set']}", className="me-3"),
                        html.Span(f"Status: {project['status']}", className="me-3"),
                        html.Span(f"Score: {project['weighted_score']:.1f}"),
                    ], className="text-muted"),
                ], width=8),
                dbc.Col([
                    dbc.Button(
                        "View Details",
                        id={'type': 'view-project-btn', 'index': project['id']},
                        size="sm",
                        color="primary",
                        outline=True,
                        className="float-end"
                    ),
                ], width=4),
            ]),
            html.Hr(className="my-2"),
            html.P(project.get('recommendation_reason', ''), className="mb-0 small text-muted"),
        ])
    ], className="mb-2")
