"""
Main callbacks for Project Management Dashboard

Simplified callback structure covering essential functionality.
"""
from dash import Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import html
import pandas as pd

from ..utils.data_helpers import get_all_projects, get_summary_stats, get_all_users, update_stock_levels
from ..components.tables import create_projects_table, create_summary_cards
from ..components.charts import (
    create_gantt_chart, create_priority_matrix,
    create_status_distribution_chart, create_recommendation_distribution_chart,
    create_score_histogram, create_lead_time_chart
)
from .modal_callbacks import register_modal_callbacks


def register_all_callbacks(app):
    """
    Register all callbacks for the application.

    Args:
        app: Dash app instance
    """

    # Register modal callbacks
    register_modal_callbacks(app)

    # ========================================
    # Data Loading Callbacks
    # ========================================

    @app.callback(
        [Output('projects-data-store', 'data'),
         Output('user-options-store', 'data'),
         Output('summary-cards-container', 'children')],
        [Input('refresh-data-btn', 'n_clicks'),
         Input('auto-refresh-interval', 'n_intervals')],
        prevent_initial_call=False
    )
    def load_initial_data(n_clicks, n_intervals):
        """Load projects data and user options."""
        try:
            # Get all projects
            projects = get_all_projects()

            # Get user options
            user_options = get_all_users()

            # Get summary stats
            stats = get_summary_stats()
            summary_cards = create_summary_cards(stats)

            return projects, user_options, summary_cards

        except Exception as e:
            print(f"Error loading data: {e}")
            return [], [], html.Div("Error loading data")

    # ========================================
    # Table Callbacks
    # ========================================

    @app.callback(
        Output('projects-table-container', 'children'),
        [Input('projects-data-store', 'data'),
         Input('filter-status', 'value'),
         Input('filter-priority', 'value'),
         Input('filter-recommendation', 'value'),
         Input('filter-search', 'value')]
    )
    def update_projects_table(projects_data, status_filter, priority_filter, rec_filter, search_term):
        """Update the projects table based on filters."""
        try:
            if not projects_data:
                return html.Div("No projects available", className="text-center text-muted p-5")

            # Apply filters
            filtered_data = projects_data.copy()

            if status_filter and status_filter != 'all':
                filtered_data = [p for p in filtered_data if p.get('status') == status_filter]

            if priority_filter and priority_filter != 'all':
                filtered_data = [p for p in filtered_data if p.get('priority_set') == priority_filter]

            if rec_filter and rec_filter != 'all':
                filtered_data = [p for p in filtered_data if p.get('recommendation') == rec_filter]

            if search_term:
                search_lower = search_term.lower()
                filtered_data = [
                    p for p in filtered_data
                    if search_lower in p.get('molecule_id', '').lower() or
                       search_lower in p.get('notes', '').lower()
                ]

            # Sort: Priority 1→2→3 (high to low priority), then by creation_date (newest first)
            filtered_data.sort(
                key=lambda x: (
                    x.get('priority_set', 2),  # 1, 2, 3 (high to low priority)
                    -(pd.to_datetime(x.get('creation_date')).timestamp() if x.get('creation_date') else 0)  # Newest first
                )
            )

            return create_projects_table(filtered_data)

        except Exception as e:
            print(f"Error updating table: {e}")
            return html.Div(f"Error: {str(e)}", className="text-danger")

    # ========================================
    # Chart Callbacks
    # ========================================

    @app.callback(
        Output('gantt-chart', 'figure'),
        [Input('projects-data-store', 'data')]
    )
    def update_gantt_chart(projects_data):
        """Update the Gantt chart."""
        try:
            return create_gantt_chart(projects_data)
        except Exception as e:
            print(f"Error creating Gantt chart: {e}")
            import traceback
            traceback.print_exc()
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_annotation(text=f"Error: {str(e)}", x=0.5, y=0.5, showarrow=False)
            return fig

    @app.callback(
        Output('priority-matrix-chart', 'figure'),
        [Input('projects-data-store', 'data')]
    )
    def update_priority_matrix(projects_data):
        """Update the priority matrix."""
        try:
            return create_priority_matrix(projects_data)
        except Exception as e:
            print(f"Error creating priority matrix: {e}")
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_annotation(text=f"Error: {str(e)}", x=0.5, y=0.5, showarrow=False)
            return fig

    @app.callback(
        Output('status-distribution-chart', 'figure'),
        [Input('projects-data-store', 'data')]
    )
    def update_status_distribution(projects_data):
        """Update status distribution chart."""
        try:
            return create_status_distribution_chart(projects_data)
        except Exception as e:
            print(f"Error creating status distribution: {e}")
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_annotation(text=f"Error: {str(e)}", x=0.5, y=0.5, showarrow=False)
            return fig

    @app.callback(
        Output('recommendation-distribution-chart', 'figure'),
        [Input('projects-data-store', 'data')]
    )
    def update_recommendation_distribution(projects_data):
        """Update recommendation distribution chart."""
        try:
            return create_recommendation_distribution_chart(projects_data)
        except Exception as e:
            print(f"Error creating recommendation distribution: {e}")
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_annotation(text=f"Error: {str(e)}", x=0.5, y=0.5, showarrow=False)
            return fig

    @app.callback(
        Output('score-histogram-chart', 'figure'),
        [Input('projects-data-store', 'data')]
    )
    def update_score_histogram(projects_data):
        """Update score histogram."""
        try:
            return create_score_histogram(projects_data)
        except Exception as e:
            print(f"Error creating score histogram: {e}")
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_annotation(text=f"Error: {str(e)}", x=0.5, y=0.5, showarrow=False)
            return fig

    @app.callback(
        Output('lead-time-chart', 'figure'),
        [Input('projects-data-store', 'data')]
    )
    def update_lead_time_chart(projects_data):
        """Update lead time chart."""
        try:
            return create_lead_time_chart(projects_data)
        except Exception as e:
            print(f"Error creating lead time chart: {e}")
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_annotation(text=f"Error: {str(e)}", x=0.5, y=0.5, showarrow=False)
            return fig

    # ========================================
    # Recommendation Lists Callbacks
    # ========================================

    @app.callback(
        [Output('recommendation-push-forward-list', 'children'),
         Output('recommendation-monitor-list', 'children'),
         Output('recommendation-review-list', 'children'),
         Output('recommendation-cancel-list', 'children')],
        [Input('projects-data-store', 'data')]
    )
    def update_recommendation_lists(projects_data):
        """Update the recommendation lists."""
        try:
            if not projects_data:
                empty_msg = html.Div("No projects", className="text-muted")
                return empty_msg, empty_msg, empty_msg, empty_msg

            # Group by recommendation
            push_forward = [p for p in projects_data if p.get('recommendation') == 'PUSH FORWARD']
            monitor = [p for p in projects_data if p.get('recommendation') == 'MONITOR']
            review = [p for p in projects_data if p.get('recommendation') == 'REVIEW']
            cancel = [p for p in projects_data if p.get('recommendation') == 'CONSIDER CANCELLATION']

            def create_list(projects):
                if not projects:
                    return html.Div("No projects in this category", className="text-muted")

                return html.Div([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6(p['molecule_id'], className="mb-1"),
                            html.Small([
                                f"Priority {p['priority_set']} | ",
                                f"Status: {p['status']} | ",
                                f"Score: {p['weighted_score']:.1f}"
                            ], className="text-muted"),
                            html.Hr(className="my-2"),
                            html.P(p.get('recommendation_reason', ''), className="mb-0 small"),
                        ])
                    ], className="mb-2")
                    for p in projects[:10]  # Limit to 10 per category
                ])

            return (
                create_list(push_forward),
                create_list(monitor),
                create_list(review),
                create_list(cancel)
            )

        except Exception as e:
            print(f"Error updating recommendation lists: {e}")
            error_msg = html.Div(f"Error: {str(e)}", className="text-danger")
            return error_msg, error_msg, error_msg, error_msg


    # ========================================
    # Table Edit Callbacks
    # ========================================

    @app.callback(
        [Output('table-status-message', 'children'),
         Output('projects-data-store', 'data', allow_duplicate=True)],
        [Input('projects-table', 'data'),
         Input('projects-table', 'data_timestamp')],
        [State('projects-data-store', 'data')],
        prevent_initial_call=True
    )
    def handle_table_edits(table_data, timestamp, original_data):
        """Handle edits made to the table (concentration, volume, status, priority)."""
        if not table_data or not original_data:
            return no_update, no_update

        try:
            # Find rows that were edited
            updated_count = 0
            messages = []

            for edited_row in table_data:
                molecule_id = edited_row.get('molecule_id')

                # Find original row
                original_row = next((r for r in original_data if r.get('molecule_id') == molecule_id), None)

                if original_row:
                    # Check if concentration or volume changed
                    conc_changed = edited_row.get('current_concentration') != original_row.get('current_concentration')
                    vol_changed = edited_row.get('current_volume') != original_row.get('current_volume')

                    if conc_changed or vol_changed:
                        # Update stock levels
                        project_id = edited_row.get('id')
                        success = update_stock_levels(
                            project_id=project_id,
                            concentration=edited_row.get('current_concentration'),
                            volume=edited_row.get('current_volume'),
                            updated_by_id=1  # TODO: Get actual user ID
                        )

                        if success:
                            updated_count += 1
                            messages.append(f"Updated {molecule_id}")

            if updated_count > 0:
                # Refresh data
                refreshed_data = get_all_projects()

                alert = dbc.Alert(
                    [
                        html.I(className="bi bi-check-circle me-2"),
                        f"Successfully updated {updated_count} project(s): {', '.join(messages)}"
                    ],
                    color="success",
                    dismissable=True,
                    duration=5000,
                    className="mt-2"
                )

                return alert, refreshed_data

            return no_update, no_update

        except Exception as e:
            print(f"Error handling table edits: {e}")
            alert = dbc.Alert(
                [
                    html.I(className="bi bi-exclamation-triangle me-2"),
                    f"Error updating projects: {str(e)}"
                ],
                color="danger",
                dismissable=True,
                duration=5000,
                className="mt-2"
            )
            return alert, no_update

    print("✓ All callbacks registered successfully")
