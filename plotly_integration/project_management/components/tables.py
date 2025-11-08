"""
Table components for Project Management Dashboard
"""
from typing import List, Dict, Any
import dash_bootstrap_components as dbc
from dash import dash_table, html
from ..config import TABLE_PAGE_SIZE, STATUS_COLORS, PRIORITY_COLORS, RECOMMENDATION_COLORS


def create_projects_table(data: List[Dict[str, Any]] = None) -> dash_table.DataTable:
    """
    Create the main projects DataTable.

    Args:
        data: List of project dictionaries

    Returns:
        DataTable component
    """
    if data is None:
        data = []

    columns = [
        {'id': 'image', 'name': 'Image', 'editable': False, 'presentation': 'markdown'},
        {'id': 'molecule_id', 'name': 'Molecule ID', 'editable': False},
        {'id': 'priority_set', 'name': 'Priority', 'editable': True, 'presentation': 'dropdown'},
        {'id': 'status', 'name': 'Status', 'editable': True, 'presentation': 'dropdown'},
        {'id': 'current_concentration', 'name': 'Conc. (mg/mL)', 'editable': True, 'type': 'numeric'},
        {'id': 'current_volume', 'name': 'Volume (mL)', 'editable': True, 'type': 'numeric'},
        {'id': 'stock_status', 'name': 'Stock Status', 'editable': False},
        {'id': 'assigned_to', 'name': 'Assigned To', 'editable': False},
        {'id': 'creation_date', 'name': 'Creation Date', 'editable': False},
        {'id': 'cloning_finish_date', 'name': 'Cloning Finish', 'editable': False},
        {'id': 'purification_finish_date', 'name': 'Purification Finish', 'editable': False},
        {'id': 'lead_time', 'name': 'Lead Time (days)', 'editable': False, 'type': 'numeric'},
        {'id': 'last_volume_update', 'name': 'Last Updated', 'editable': False},
    ]

    return dash_table.DataTable(
        id='projects-table',
        columns=columns,
        data=data,
        editable=True,
        row_selectable='multi',
        selected_rows=[],
        filter_action='native',
        sort_action='native',
        sort_mode='multi',
        page_action='native',
        page_current=0,
        page_size=TABLE_PAGE_SIZE,
        markdown_options={'html': True},
        style_table={
            'overflowX': 'auto',
            'minWidth': '100%',
        },
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '13px',
            'minWidth': '80px',
        },
        style_cell_conditional=[
            {'if': {'column_id': 'image'}, 'width': '80px', 'textAlign': 'center'},
            {'if': {'column_id': 'molecule_id'}, 'width': '120px'},
            {'if': {'column_id': 'current_concentration'}, 'width': '100px'},
            {'if': {'column_id': 'current_volume'}, 'width': '100px'},
            {'if': {'column_id': 'stock_status'}, 'width': '110px'},
        ],
        style_header={
            'backgroundColor': '#2c3e50',
            'color': 'white',
            'fontWeight': 'bold',
            'fontSize': '14px',
            'border': '1px solid #34495e',
        },
        style_data={
            'whiteSpace': 'normal',
            'height': 'auto',
            'border': '1px solid #ddd',
        },
        style_data_conditional=get_table_conditional_styles(),
        dropdown={
            'priority_set': {
                'options': [
                    {'label': 'Priority 1 (High)', 'value': 1},
                    {'label': 'Priority 2 (Medium)', 'value': 2},
                    {'label': 'Priority 3 (Low)', 'value': 3},
                ]
            },
            'status': {
                'options': [
                    {'label': 'Active', 'value': 'Active'},
                    {'label': 'On Hold', 'value': 'On Hold'},
                    {'label': 'Cancelled', 'value': 'Cancelled'},
                    {'label': 'Completed', 'value': 'Completed'},
                ]
            },
        },
        css=[
            {
                'selector': '.dash-spreadsheet-inner',
                'rule': 'border-radius: 5px;'
            },
            {
                'selector': 'img',
                'rule': 'max-width: 60px; height: auto; border-radius: 4px; cursor: pointer;'
            }
        ],
    )


def get_table_conditional_styles() -> List[Dict[str, Any]]:
    """
    Get conditional styling for the data table.

    Returns:
        List of conditional style dictionaries
    """
    styles = [
        # Header styling
        {
            'if': {'column_id': 'molecule_id'},
            'fontWeight': 'bold',
            'backgroundColor': '#ecf0f1',
        },
        # Priority-based row coloring
        {
            'if': {'filter_query': '{priority_set} = 1'},
            'borderLeft': f'4px solid {PRIORITY_COLORS[1]}',
        },
        {
            'if': {'filter_query': '{priority_set} = 2'},
            'borderLeft': f'4px solid {PRIORITY_COLORS[2]}',
        },
        {
            'if': {'filter_query': '{priority_set} = 3'},
            'borderLeft': f'4px solid {PRIORITY_COLORS[3]}',
        },
        # Status colors
        {
            'if': {'filter_query': '{status} = "Active"', 'column_id': 'status'},
            'backgroundColor': '#d4edda',
            'color': '#155724',
            'fontWeight': 'bold',
        },
        {
            'if': {'filter_query': '{status} = "On Hold"', 'column_id': 'status'},
            'backgroundColor': '#fff3cd',
            'color': '#856404',
            'fontWeight': 'bold',
        },
        {
            'if': {'filter_query': '{status} = "Cancelled"', 'column_id': 'status'},
            'backgroundColor': '#f8d7da',
            'color': '#721c24',
            'fontWeight': 'bold',
        },
        {
            'if': {'filter_query': '{status} = "Completed"', 'column_id': 'status'},
            'backgroundColor': '#d1ecf1',
            'color': '#0c5460',
            'fontWeight': 'bold',
        },
        # Recommendation colors
        {
            'if': {'filter_query': '{recommendation} = "PUSH FORWARD"', 'column_id': 'recommendation'},
            'backgroundColor': '#d4edda',
            'color': '#155724',
            'fontWeight': 'bold',
        },
        {
            'if': {'filter_query': '{recommendation} = "MONITOR"', 'column_id': 'recommendation'},
            'backgroundColor': '#d1ecf1',
            'color': '#0c5460',
        },
        {
            'if': {'filter_query': '{recommendation} = "REVIEW"', 'column_id': 'recommendation'},
            'backgroundColor': '#fff3cd',
            'color': '#856404',
            'fontWeight': 'bold',
        },
        {
            'if': {'filter_query': '{recommendation} = "CONSIDER CANCELLATION"', 'column_id': 'recommendation'},
            'backgroundColor': '#f8d7da',
            'color': '#721c24',
            'fontWeight': 'bold',
        },
        # Score coloring
        {
            'if': {'filter_query': '{weighted_score} >= 75', 'column_id': 'weighted_score'},
            'backgroundColor': '#d4edda',
            'fontWeight': 'bold',
        },
        {
            'if': {'filter_query': '{weighted_score} < 30', 'column_id': 'weighted_score'},
            'backgroundColor': '#f8d7da',
            'fontWeight': 'bold',
        },
        # Stock status colors
        {
            'if': {'filter_query': '{stock_status} = "Available"', 'column_id': 'stock_status'},
            'backgroundColor': '#d4edda',
            'color': '#155724',
            'fontWeight': 'bold',
        },
        {
            'if': {'filter_query': '{stock_status} = "Low Stock"', 'column_id': 'stock_status'},
            'backgroundColor': '#fff3cd',
            'color': '#856404',
            'fontWeight': 'bold',
        },
        {
            'if': {'filter_query': '{stock_status} = "Critical"', 'column_id': 'stock_status'},
            'backgroundColor': '#f8d7da',
            'color': '#721c24',
            'fontWeight': 'bold',
        },
        {
            'if': {'filter_query': '{stock_status} = "Depleted"', 'column_id': 'stock_status'},
            'backgroundColor': '#343a40',
            'color': 'white',
            'fontWeight': 'bold',
        },
        # Volume alert colors
        {
            'if': {'filter_query': '{current_volume} < 5 && {current_volume} > 0', 'column_id': 'current_volume'},
            'backgroundColor': '#f8d7da',
            'fontWeight': 'bold',
        },
        {
            'if': {'filter_query': '{current_volume} >= 5 && {current_volume} < 10', 'column_id': 'current_volume'},
            'backgroundColor': '#fff3cd',
            'fontWeight': 'bold',
        },
        # Hover effect
        {
            'if': {'state': 'active'},
            'backgroundColor': '#e8f4f8',
            'border': '2px solid #17a2b8',
        },
    ]

    return styles


def create_summary_cards(stats: Dict[str, Any]) -> dbc.Row:
    """
    Create summary metric cards.

    Args:
        stats: Dictionary with summary statistics

    Returns:
        Bootstrap Row with metric cards
    """
    # Top row - main metrics
    top_cards = [
        create_metric_card("Total Projects", stats.get('total_projects', 0), "bi-clipboard-data", "primary"),
        create_metric_card("Active", stats.get('active_count', 0), "bi-play-circle", "success"),
        create_metric_card("Completed", stats.get('completed_count', 0), "bi-check-circle", "info"),
        create_metric_card("Avg Score", f"{stats.get('avg_weighted_score', 0):.1f}", "bi-star", "secondary"),
        create_metric_card("Low Stock", stats.get('low_stock_count', 0), "bi-exclamation-triangle", "warning"),
        create_metric_card("Critical Stock", stats.get('critical_stock_count', 0), "bi-exclamation-octagon", "danger"),
    ]

    return dbc.Row([
        dbc.Col(card, width=2)
        for card in top_cards
    ], className="mb-4")


def create_metric_card(title: str, value: Any, icon: str, color: str) -> dbc.Card:
    """
    Create a single metric card.

    Args:
        title: Card title
        value: Metric value
        icon: Bootstrap icon class
        color: Bootstrap color

    Returns:
        Card component
    """
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"{icon} me-2", style={'fontSize': '24px'}),
                html.H6(title, className="mb-1", style={'fontSize': '12px', 'color': '#6c757d'}),
            ], className="d-flex align-items-center justify-content-between"),
            html.H3(value, className=f"text-{color} mb-0 mt-2", style={'fontSize': '28px', 'fontWeight': 'bold'}),
        ])
    ], className="shadow-sm", style={'borderRadius': '10px'})


def create_decision_history_table(history_data: List[Dict[str, Any]] = None) -> dash_table.DataTable:
    """
    Create the decision history table.

    Args:
        history_data: List of decision history records

    Returns:
        DataTable component
    """
    if history_data is None:
        history_data = []

    columns = [
        {'id': 'decision_date', 'name': 'Date', 'editable': False},
        {'id': 'decision_type', 'name': 'Decision Type', 'editable': False},
        {'id': 'decision_by', 'name': 'By', 'editable': False},
        {'id': 'previous_status', 'name': 'Previous Status', 'editable': False},
        {'id': 'new_status', 'name': 'New Status', 'editable': False},
        {'id': 'rationale', 'name': 'Rationale', 'editable': False},
        {'id': 'system_recommendation', 'name': 'System Recommendation', 'editable': False},
    ]

    return dash_table.DataTable(
        id='decision-history-table',
        columns=columns,
        data=history_data,
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '12px',
        },
        style_header={
            'backgroundColor': '#34495e',
            'color': 'white',
            'fontWeight': 'bold',
        },
        style_data={
            'whiteSpace': 'normal',
            'height': 'auto',
        },
        page_size=10,
    )


def create_project_comparison_table(project1_data: Dict, project2_data: Dict) -> dbc.Table:
    """
    Create a comparison table for two projects.

    Args:
        project1_data: First project data
        project2_data: Second project data

    Returns:
        Bootstrap Table component
    """
    headers = ['Metric', project1_data.get('molecule_id', 'Project 1'), project2_data.get('molecule_id', 'Project 2'), 'Difference']

    rows = [
        ['Status', project1_data.get('status'), project2_data.get('status'), '-'],
        ['Priority', project1_data.get('priority_set'), project2_data.get('priority_set'), '-'],
        ['Weighted Score', f"{project1_data.get('weighted_score', 0):.1f}",
         f"{project2_data.get('weighted_score', 0):.1f}",
         f"{project1_data.get('weighted_score', 0) - project2_data.get('weighted_score', 0):.1f}"],
        ['On-Time Score', f"{project1_data.get('on_time_score', 0):.1f}",
         f"{project2_data.get('on_time_score', 0):.1f}",
         f"{project1_data.get('on_time_score', 0) - project2_data.get('on_time_score', 0):.1f}"],
        ['Completion Score', f"{project1_data.get('completion_score', 0):.1f}",
         f"{project2_data.get('completion_score', 0):.1f}",
         f"{project1_data.get('completion_score', 0) - project2_data.get('completion_score', 0):.1f}"],
        ['Recommendation', project1_data.get('recommendation'), project2_data.get('recommendation'), '-'],
    ]

    table_header = [html.Thead(html.Tr([html.Th(h) for h in headers]))]
    table_body = [html.Tbody([html.Tr([html.Td(cell) for cell in row]) for row in rows])]

    return dbc.Table(table_header + table_body, bordered=True, hover=True, striped=True, className="mt-3")
