import dash
import numpy as np
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State, MATCH, dash_table
from django_plotly_dash import DjangoDash
import pandas as pd
from plotly_integration.models import ViCellData
import json
from datetime import datetime
import re
import plotly.express as px
from plotly.subplots import make_subplots

# Initialize the Dash app
app = DjangoDash("ViCellReportApp")

# Define the variables and their corresponding labels
VARIABLES = {
    "viable_cells_per_ml": "Viable Cells/mL",
    "viability": "Viability (%)",
    "average_viable_diameter": "Average Viable Diameter (µm)",
    "total_cells_per_ml": "Total Cells/mL",
    "cell_count": "Total Cell Count",
    "average_diameter": "Average Diameter (µm)",
    "average_circularity": "Average Circularity",
    "growth_rate": "Growth Rate Analysis",
    "doubling_time": "Doubling Time Analysis",
}

# Define initial column structure
INITIAL_COLUMNS = [
    {"name": "Sample ID", "id": "sample_id"},
    {"name": "Date", "id": "date_time"},
    {"name": "Process Day", "id": "day"},
    {"name": "Process Time (hr)", "id": "process_time_hours"},
    {"name": "Total Cells/mL", "id": "total_cells_per_ml"},
    {"name": "Viable Cells/mL", "id": "viable_cells_per_ml"},
    {"name": "Viability (%)", "id": "viability"},
    {"name": "Avg Viable Diameter (µm)", "id": "average_viable_diameter"},
]

# Define columns for the edit data table
EDIT_DATA_COLUMNS = [
    {"name": "ID", "id": "id", "editable": False},
    {"name": "Sample ID", "id": "sample_id", "editable": True},
    {"name": "Date/Time", "id": "date_time", "editable": False},
    {"name": "Experiment", "id": "experiment", "editable": True},
    {"name": "Reactor Type", "id": "reactor_type", "editable": True},
    {"name": "Reactor Number", "id": "reactor_number", "editable": True},
    {"name": "Day", "id": "day", "editable": True},
    {"name": "Special", "id": "special", "editable": False},
    {"name": "Viable Cells/mL", "id": "viable_cells_per_ml", "editable": False,
     "format": {"specifier": ".2f"}},
    {"name": "Viability (%)", "id": "viability", "editable": False, "format": {"specifier": ".1f"}},
    {"name": "Cell Count", "id": "cell_count", "editable": False, "format": {"specifier": ".0f"}},
    {"name": "Viable Cells", "id": "viable_cells", "editable": False,
     "format": {"specifier": ".0f"}},
    {"name": "Total Cells/mL", "id": "total_cells_per_ml", "editable": False,
     "format": {"specifier": ".2f"}},
    {"name": "Sample Type", "id": "sample_type", "editable": False, 'hidden': True},
]

# Main layout with modals and stores
app.layout = html.Div(
    children=[
        # Stores for state management
        dcc.Store(id="selected-experiment", data=None),
        dcc.Store(id="embedded-mode", data=False),
        dcc.Store(id="url-params", data={}),
        dcc.Store(id="edit-data-store", data=[]),
        dcc.Location(id="url", refresh=False),
        dcc.Interval(id="load-once", interval=1000, n_intervals=0, max_intervals=1),

        # Modal for Edit Data
        html.Div(
            id="edit-data-modal",
            style={
                "display": "none",
                "position": "fixed",
                "top": "0",
                "left": "0",
                "width": "100%",
                "height": "100%",
                "backgroundColor": "rgba(0, 0, 0, 0.5)",
                "zIndex": "1000"
            },
            children=[
                html.Div(
                    style={
                        "position": "relative",
                        "margin": "2% auto",
                        "width": "95%",
                        "maxWidth": "1600px",
                        "height": "90%",
                        "backgroundColor": "white",
                        "borderRadius": "10px",
                        "padding": "20px",
                        "boxShadow": "0 5px 15px rgba(0,0,0,0.3)",
                        "display": "flex",
                        "flexDirection": "column"
                    },
                    children=[
                        html.Button(
                            "✕",
                            id="close-edit-data-modal-btn",
                            style={
                                "position": "absolute",
                                "top": "10px",
                                "right": "10px",
                                "fontSize": "24px",
                                "border": "none",
                                "backgroundColor": "transparent",
                                "cursor": "pointer",
                                "color": "#666"
                            }
                        ),
                        html.Div(
                            style={
                                "display": "flex",
                                "justifyContent": "space-between",
                                "alignItems": "center",
                                "marginBottom": "20px"
                            },
                            children=[
                                html.H3("Edit ViCell Data", style={"color": "#0056b3", "margin": "0"}),
                                html.Div(
                                    style={"display": "flex", "gap": "10px"},
                                    children=[
                                        html.Button(
                                            "Save Changes",
                                            id="save-changes-btn",
                                            style={
                                                "backgroundColor": "#28a745",
                                                "color": "white",
                                                "border": "none",
                                                "padding": "10px 20px",
                                                "fontSize": "14px",
                                                "cursor": "pointer",
                                                "borderRadius": "5px",
                                                "fontWeight": "500",
                                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                                            }
                                        ),
                                        html.Button(
                                            "Refresh Data",
                                            id="refresh-data-btn",
                                            style={
                                                "backgroundColor": "#17a2b8",
                                                "color": "white",
                                                "border": "none",
                                                "padding": "10px 20px",
                                                "fontSize": "14px",
                                                "cursor": "pointer",
                                                "borderRadius": "5px",
                                                "fontWeight": "500",
                                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                                            }
                                        )
                                    ]
                                )
                            ]
                        ),
                        html.Div(
                            id="save-status-message",
                            style={
                                "marginBottom": "10px",
                                "padding": "10px",
                                "borderRadius": "5px",
                                "display": "none"
                            }
                        ),
                        html.Div(
                            style={"flex": "1", "overflowY": "auto"},
                            children=[
                                dash_table.DataTable(
                                    id="edit-data-table",
                                    columns=EDIT_DATA_COLUMNS,
                                    data=[],
                                    page_size=25,
                                    editable=True,
                                    row_deletable=False,
                                    style_table={
                                        "overflowX": "auto",
                                        "borderRadius": "8px",
                                        "height": "100%"
                                    },
                                    style_header={
                                        "backgroundColor": "#e9f1fb",
                                        "fontWeight": "bold",
                                        "textAlign": "center",
                                        "color": "#0047b3",
                                        "fontSize": "12px"
                                    },
                                    style_cell={
                                        "textAlign": "center",
                                        "padding": "8px",
                                        "borderBottom": "1px solid #ccc",
                                        "fontFamily": "Arial, sans-serif",
                                        "fontSize": "12px",
                                        "minWidth": "80px",
                                        "maxWidth": "150px",
                                        "overflow": "hidden",
                                        "textOverflow": "ellipsis"
                                    },
                                    style_data={"backgroundColor": "white", "color": "#333"},
                                    style_data_conditional=[
                                        {
                                            "if": {"row_index": "odd"},
                                            "backgroundColor": "#f8f9fa",
                                        },
                                        {
                                            "if": {"column_editable": True},
                                            "backgroundColor": "#fff3cd",
                                        }
                                    ],
                                    filter_action="native",
                                    sort_action="native"
                                )
                            ]
                        )
                    ]
                )
            ]
        ),

        # Modal for Select Experiment
        html.Div(
            id="select-experiment-modal",
            style={
                "display": "none",
                "position": "fixed",
                "top": "0",
                "left": "0",
                "width": "100%",
                "height": "100%",
                "backgroundColor": "rgba(0, 0, 0, 0.5)",
                "zIndex": "1000"
            },
            children=[
                html.Div(
                    style={
                        "position": "relative",
                        "margin": "2% auto",
                        "width": "90%",
                        "maxWidth": "1400px",
                        "height": "85%",
                        "backgroundColor": "white",
                        "borderRadius": "10px",
                        "padding": "20px",
                        "boxShadow": "0 5px 15px rgba(0,0,0,0.3)",
                        "display": "flex",
                        "flexDirection": "column"
                    },
                    children=[
                        html.Button(
                            "✕",
                            id="close-select-experiment-btn",
                            style={
                                "position": "absolute",
                                "top": "10px",
                                "right": "10px",
                                "fontSize": "24px",
                                "border": "none",
                                "backgroundColor": "transparent",
                                "cursor": "pointer",
                                "color": "#666"
                            }
                        ),
                        html.H3("Select Experiment", style={"marginBottom": "20px", "color": "#0056b3"}),
                        html.Div(
                            style={"flex": "1", "overflowY": "auto", "marginBottom": "20px"},
                            children=[
                                dash_table.DataTable(
                                    id="experiment-selection-table",
                                    columns=[
                                        {"name": "Experiment", "id": "experiment"}
                                    ],
                                    data=[],
                                    row_selectable="single",
                                    selected_rows=[],
                                    page_size=10,
                                    sort_action="native",
                                    filter_action="native",
                                    style_table={
                                        "height": "100%",
                                        "overflowY": "auto"
                                    },
                                    style_cell={
                                        "textAlign": "left",
                                        "padding": "10px",
                                        "whiteSpace": "normal",
                                        "height": "auto",
                                        "fontSize": "14px"
                                    },
                                    style_header={
                                        "backgroundColor": "#f8f9fa",
                                        "fontWeight": "bold",
                                        "borderBottom": "2px solid #dee2e6",
                                        "color": "#495057"
                                    },
                                    style_data={
                                        "borderBottom": "1px solid #e9ecef",
                                        "color": "#212529"
                                    },
                                    style_data_conditional=[
                                        {
                                            "if": {"row_index": "odd"},
                                            "backgroundColor": "#f8f9fa",
                                        },
                                        {
                                            "if": {"state": "selected"},
                                            "backgroundColor": "#e3f2fd",
                                            "border": "1px solid #0056b3",
                                        }
                                    ]
                                )
                            ]
                        ),
                        html.Button(
                            "Select Experiment",
                            id="confirm-experiment-selection",
                            style={
                                "backgroundColor": "#0056b3",
                                "color": "white",
                                "border": "none",
                                "padding": "10px 30px",
                                "fontSize": "14px",
                                "cursor": "pointer",
                                "borderRadius": "5px",
                                "fontWeight": "500",
                                "position": "absolute",
                                "bottom": "20px",
                                "right": "20px",
                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                            }
                        )
                    ]
                )
            ]
        ),

        # Top toolbar with action buttons
        html.Div(
            id="toolbar-container",
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "padding": "15px 20px",
                "backgroundColor": "#f8f9fa",
                "borderBottom": "1px solid #dee2e6",
                "gap": "10px"
            },
            children=[
                # Left side - buttons
                html.Div(
                    style={"display": "flex", "gap": "10px"},
                    children=[
                        html.Button(
                            "Select Experiment",
                            id="change-experiment-btn",
                            style={
                                "backgroundColor": "#6c757d",
                                "color": "white",
                                "border": "none",
                                "padding": "10px 20px",
                                "fontSize": "14px",
                                "cursor": "pointer",
                                "borderRadius": "5px",
                                "fontWeight": "500",
                                "transition": "all 0.3s ease",
                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                            }
                        ),
                        html.Button(
                            "Edit Data",
                            id="edit-data-btn",
                            style={
                                "backgroundColor": "#dc3545",
                                "color": "white",
                                "border": "none",
                                "padding": "10px 20px",
                                "fontSize": "14px",
                                "cursor": "pointer",
                                "borderRadius": "5px",
                                "fontWeight": "500",
                                "transition": "all 0.3s ease",
                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                            }
                        )
                    ]
                ),
                # Right side - Current experiment display
                html.Div(
                    id="current-experiment-text",
                    style={
                        "fontSize": "16px",
                        "color": "#495057",
                        "fontWeight": "500"
                    }
                )
            ]
        ),

        # Main content area
        html.Div(
            children=[
                # Tab content with improved styling
                dcc.Tabs(
                    id="variable-tabs",
                    value="viable_cells_per_ml",
                    children=[
                        *[dcc.Tab(
                            label=label,
                            value=var,
                            style={
                                'borderTop': '1px solid #d6d6d6',
                                'borderBottom': '1px solid #d6d6d6',
                                'borderLeft': '1px solid #d6d6d6',
                                'borderRight': '1px solid #d6d6d6',
                                'backgroundColor': '#f9f9f9',
                                'color': '#666',
                                'padding': '16px 28px',
                                'fontWeight': '500',
                                'fontSize': '15px'
                            },
                            selected_style={
                                'borderTop': '1px solid #d6d6d6',
                                'borderBottom': '1px solid #d6d6d6',
                                'borderLeft': '1px solid #d6d6d6',
                                'borderRight': '1px solid #d6d6d6',
                                'backgroundColor': '#119DFF',
                                'color': 'white',
                                'padding': '16px 28px',
                                'fontWeight': '600',
                                'fontSize': '15px'
                            }
                        ) for var, label in VARIABLES.items()],
                        dcc.Tab(
                            label="Summary",
                            value="summary",
                            style={
                                'borderTop': '1px solid #d6d6d6',
                                'borderBottom': '1px solid #d6d6d6',
                                'borderLeft': '1px solid #d6d6d6',
                                'borderRight': '1px solid #d6d6d6',
                                'backgroundColor': '#f9f9f9',
                                'color': '#666',
                                'padding': '16px 28px',
                                'fontWeight': '500',
                                'fontSize': '15px'
                            },
                            selected_style={
                                'borderTop': '1px solid #d6d6d6',
                                'borderBottom': '1px solid #d6d6d6',
                                'borderLeft': '1px solid #d6d6d6',
                                'borderRight': '1px solid #d6d6d6',
                                'backgroundColor': '#119DFF',
                                'color': 'white',
                                'padding': '16px 28px',
                                'fontWeight': '600',
                                'fontSize': '15px'
                            }
                        ),
                    ],
                    style={
                        'height': '54px',
                        'marginTop': '20px',
                        'marginBottom': '20px'
                    }
                ),

                # Summary container
                html.Div(
                    id="summary-container",
                    style={"marginTop": "20px", "display": "block"},
                    children=[
                        html.H3("Experiment Summary", style={"marginBottom": "20px", "color": "#0047b3"}),
                        dcc.Dropdown(
                            id="subset-dropdown",
                            placeholder="Select Reactor Number to View",
                            style={"width": "400px", "marginBottom": "20px"}
                        ),
                        html.Div(
                            id="subset-table-container",
                            children=[
                                dash_table.DataTable(
                                    id="subset-table",
                                    columns=INITIAL_COLUMNS,
                                    data=[],
                                    page_size=15,
                                    style_table={
                                        "overflowX": "auto",
                                        "borderRadius": "8px",
                                        "table-layout": "fixed"
                                    },
                                    style_header={
                                        "backgroundColor": "#e9f1fb",
                                        "fontWeight": "bold",
                                        "textAlign": "center",
                                        "color": "#0047b3"
                                    },
                                    style_cell={
                                        "textAlign": "center",
                                        "padding": "10px",
                                        "borderBottom": "1px solid #ccc",
                                        "fontFamily": "Arial, sans-serif"
                                    },
                                    style_data={"backgroundColor": "white", "color": "#333"},
                                    filter_action="native",
                                    sort_action="native"
                                )
                            ]
                        )
                    ]
                ),

                # Graph container
                html.Div(
                    id="variable-graph-container",
                    style={
                        "display": "none",
                        "width": "100%",
                        "minHeight": "calc(100vh - 300px)",
                        "padding": "20px"
                    }
                )
            ]
        )
    ]
)


# Parse URL parameters callback
@app.callback(
    [Output("url-params", "data"),
     Output("embedded-mode", "data")],
    [Input("url", "search")],
    prevent_initial_call=False
)
def parse_url_params(search):
    if not search:
        return {}, False

    from urllib.parse import parse_qs
    params = parse_qs(search.lstrip("?"))

    url_params = {}
    embedded = False
    experiment = None

    if "embedded" in params:
        embedded = params["embedded"][0].lower() in ["true", "1", "yes"]
        url_params["embedded"] = embedded

    if "experiment" in params:
        experiment = params["experiment"][0]
        url_params["experiment"] = experiment

    return url_params, embedded


# Update toolbar visibility based on embedded mode
@app.callback(
    [Output("change-experiment-btn", "style"),
     Output("edit-data-btn", "style")],
    [Input("embedded-mode", "data")],
    prevent_initial_call=False
)
def update_toolbar_visibility(embedded):
    if embedded:
        # Hide buttons in embedded mode
        hidden_style = {"display": "none"}
        return hidden_style, hidden_style
    else:
        # Show buttons in normal mode
        select_btn_style = {
            "backgroundColor": "#6c757d",
            "color": "white",
            "border": "none",
            "padding": "10px 20px",
            "fontSize": "14px",
            "cursor": "pointer",
            "borderRadius": "5px",
            "fontWeight": "500",
            "transition": "all 0.3s ease",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
        }

        edit_btn_style = {
            "backgroundColor": "#dc3545",
            "color": "white",
            "border": "none",
            "padding": "10px 20px",
            "fontSize": "14px",
            "cursor": "pointer",
            "borderRadius": "5px",
            "fontWeight": "500",
            "transition": "all 0.3s ease",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
        }

        return select_btn_style, edit_btn_style


# Callback to show/hide Edit Data modal
@app.callback(
    Output("edit-data-modal", "style"),
    [Input("edit-data-btn", "n_clicks"),
     Input("close-edit-data-modal-btn", "n_clicks")],
    [State("edit-data-modal", "style")],
    prevent_initial_call=True
)
def toggle_edit_data_modal(open_clicks, close_clicks, current_style):
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_style

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "edit-data-btn":
        return {**current_style, "display": "block"}
    elif button_id == "close-edit-data-modal-btn":
        return {**current_style, "display": "none"}

    return current_style


# Callback to show/hide Select Experiment modal and populate experiments
@app.callback(
    [Output("select-experiment-modal", "style"),
     Output("experiment-selection-table", "data"),
     Output("current-experiment-text", "children")],
    [Input("change-experiment-btn", "n_clicks"),
     Input("close-select-experiment-btn", "n_clicks"),
     Input("confirm-experiment-selection", "n_clicks"),
     Input("load-once", "n_intervals"),
     Input("url-params", "data")],
    [State("select-experiment-modal", "style"),
     State("experiment-selection-table", "selected_rows"),
     State("experiment-selection-table", "data"),
     State("embedded-mode", "data"),
     State("selected-experiment", "data")],
    prevent_initial_call=False
)
def toggle_select_modal(change_clicks, close_clicks, confirm_clicks, load_interval,
                        url_params, current_style, selected_rows, table_data,
                        embedded, current_experiment):
    ctx = dash.callback_context

    # Get trigger ID
    if not ctx.triggered:
        triggered_id = None
    else:
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Fetch experiments for table - only sample_type=1 - SIMPLIFIED
    experiments_query = ViCellData.objects.filter(
        sample_type=1,
        experiment__isnull=False
    ).exclude(experiment="").values("experiment").distinct().order_by("-experiment")

    experiments_data = [{"experiment": exp_obj["experiment"]} for exp_obj in experiments_query]

    # Determine current experiment text
    current_text = "No experiment selected"
    if current_experiment:
        current_text = f"Current Experiment: {current_experiment}"

    # Handle modal visibility - simplified without auto-select
    if triggered_id == "change-experiment-btn":
        return {**current_style, "display": "block"}, experiments_data, current_text
    elif triggered_id == "close-select-experiment-btn":
        return {**current_style, "display": "none"}, experiments_data, current_text
    elif triggered_id == "confirm-experiment-selection" and selected_rows and table_data:
        # Experiment will be selected by another callback, close modal
        return {**current_style, "display": "none"}, experiments_data, current_text
    elif triggered_id == "load-once":
        # Initial load - don't auto-open modal, just return current state
        pass

    return current_style, experiments_data, current_text


# Update selected experiment from modal
@app.callback(
    Output("selected-experiment", "data"),
    [Input("confirm-experiment-selection", "n_clicks"),
     Input("url-params", "data")],
    [State("experiment-selection-table", "selected_rows"),
     State("experiment-selection-table", "data")],
    prevent_initial_call=False
)
def update_selected_experiment(confirm_clicks, url_params, selected_rows, table_data):
    ctx = dash.callback_context

    if not ctx.triggered:
        return None

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "url-params" and "experiment" in url_params:
        # Load from URL
        return url_params["experiment"]
    elif triggered_id == "confirm-experiment-selection" and selected_rows and table_data:
        # Load from selection
        selected_experiment = table_data[selected_rows[0]]
        return selected_experiment["experiment"]

    return None


# Toggle between summary and graph views
@app.callback(
    [Output("summary-container", "style"),
     Output("variable-graph-container", "style")],
    Input("variable-tabs", "value")
)
def toggle_view(selected_tab):
    if selected_tab == "summary":
        summary_style = {"marginTop": "20px", "display": "block"}
        graph_style = {"display": "none"}
    else:
        summary_style = {"marginTop": "20px", "display": "none"}
        graph_style = {
            "display": "block",
            "width": "100%",
            "minHeight": "calc(100vh - 300px)",
            "padding": "20px"
        }

    return summary_style, graph_style


@app.callback(
    [Output("edit-data-table", "data"),
     Output("edit-data-store", "data")],
    [Input("edit-data-btn", "n_clicks"),
     Input("refresh-data-btn", "n_clicks")],
    [State("selected-experiment", "data")],
    prevent_initial_call=True
)
def load_edit_data(edit_btn_clicks, refresh_clicks, selected_experiment):
    ctx = dash.callback_context
    if not ctx.triggered:
        return [], []

    try:
        # Query ViCellData for the selected experiment with sample_type=1
        if selected_experiment:
            vicell_data = ViCellData.objects.filter(
                experiment=selected_experiment,
                sample_type=1
            ).order_by("-date_time")
        else:
            # If no experiment selected, show all sample_type=1 data
            vicell_data = ViCellData.objects.filter(sample_type=1).order_by(
                "-date_time"
            )

        # Convert to list of dictionaries for DataTable
        data = []
        for record in vicell_data:
            row = {
                "id": record.id,
                "sample_id": record.sample_id,
                "date_time": record.date_time.strftime("%m/%d/%Y %H:%M:%S") if record.date_time else "",
                "experiment": record.experiment or "",
                "day": record.day,
                "reactor_type": record.reactor_type or "",
                "reactor_number": record.reactor_number,
                "special": record.special or "",
                "cell_count": record.cell_count,
                "viable_cells": record.viable_cells,
                "total_cells_per_ml": record.total_cells_per_ml,
                "viable_cells_per_ml": record.viable_cells_per_ml,
                "viability": record.viability,
                "sample_type": record.sample_type,
            }
            data.append(row)

        print(f"Loaded {len(data)} records for editing")
        return data, data
    except Exception as e:
        print(f"Error loading edit data: {e}")
        return [], []


# Save changes to database
@app.callback(
    [Output("save-status-message", "children"),
     Output("save-status-message", "style")],
    [Input("save-changes-btn", "n_clicks")],
    [State("edit-data-table", "data"),
     State("edit-data-store", "data")],
    prevent_initial_call=True
)
def save_changes(save_clicks, current_data, original_data):
    if not save_clicks or not current_data:
        return "", {"display": "none"}

    try:
        changes_made = 0
        errors = []

        # Create dictionaries for easy comparison
        original_dict = {row["id"]: row for row in original_data}

        for row in current_data:
            record_id = row["id"]
            original_row = original_dict.get(record_id)

            if not original_row:
                continue

            # Check if any editable fields have changed
            editable_fields = ["sample_id", "experiment", "day", "reactor_type", "reactor_number"]
            has_changes = False

            for field in editable_fields:
                if str(row.get(field, "")) != str(original_row.get(field, "")):
                    has_changes = True
                    break

            if has_changes:
                try:
                    # Get the database record
                    vicell_record = ViCellData.objects.get(id=record_id)

                    # Update the editable fields
                    vicell_record.sample_id = row.get("sample_id", "")
                    vicell_record.experiment = row.get("experiment", "")
                    vicell_record.day = row.get("day") if row.get("day") not in [None, ""] else None
                    vicell_record.reactor_type = row.get("reactor_type", "")
                    vicell_record.reactor_number = row.get("reactor_number") if row.get("reactor_number") not in [None,
                                                                                                                  ""] else None

                    # Save the record
                    vicell_record.save()
                    changes_made += 1

                except Exception as e:
                    errors.append(f"Error updating record {record_id}: {str(e)}")

        # Prepare status message
        if changes_made > 0 and not errors:
            message = f"Successfully saved {changes_made} changes!"
            style = {
                "display": "block",
                "backgroundColor": "#d4edda",
                "color": "#155724",
                "border": "1px solid #c3e6cb"
            }
        elif changes_made > 0 and errors:
            message = f"Saved {changes_made} changes with {len(errors)} errors. Errors: {'; '.join(errors[:3])}"
            style = {
                "display": "block",
                "backgroundColor": "#fff3cd",
                "color": "#856404",
                "border": "1px solid #ffeaa7"
            }
        elif errors:
            message = f"Failed to save changes. Errors: {'; '.join(errors[:3])}"
            style = {
                "display": "block",
                "backgroundColor": "#f8d7da",
                "color": "#721c24",
                "border": "1px solid #f5c6cb"
            }
        else:
            message = "No changes detected."
            style = {
                "display": "block",
                "backgroundColor": "#d1ecf1",
                "color": "#0c5460",
                "border": "1px solid #bee5eb"
            }

        return message, style

    except Exception as e:
        return f"Error saving changes: {str(e)}", {
            "display": "block",
            "backgroundColor": "#f8d7da",
            "color": "#721c24",
            "border": "1px solid #f5c6cb"
        }


def process_and_sort_samples_by_experiment(experiment):
    """
    Fetches data for a specific experiment with sample_type=1.
    Groups by reactor_number for plotting.
    """
    # Query ViCellData for the experiment with sample_type=1
    samples = ViCellData.objects.filter(
        experiment=experiment,
        sample_type=1
    ).values(
        "sample_id", "experiment", "day", "reactor_type", "reactor_number", "special",
        "date_time", "cell_count", "viable_cells", "total_cells_per_ml", "viable_cells_per_ml",
        "viability", "average_diameter", "average_viable_diameter", "average_circularity",
        "average_viable_circularity"
    )

    df = pd.DataFrame(list(samples))

    if df.empty:
        print(f"⚠️ No valid samples found for experiment {experiment}.")
        return {}

    # Sort by reactor number, day, and special condition
    df_sorted = df.sort_values(by=["reactor_number", "day", "special"], ascending=[True, True, True])

    # Group by reactor_number to organize data properly
    grouped_data = {}

    for reactor_number in df_sorted["reactor_number"].dropna().unique():
        reactor_df = df_sorted[df_sorted["reactor_number"] == reactor_number]
        if not reactor_df.empty:
            grouped_data[reactor_number] = reactor_df
        else:
            print(f"⚠️ No matching data found for Reactor Number {reactor_number}")

    return grouped_data


@app.callback(
    [Output("subset-dropdown", "options"),
     Output("subset-dropdown", "value")],
    [Input("selected-experiment", "data")]
)
def update_reactor_number_dropdown(selected_experiment):
    """Populate dropdown with available reactor numbers from the selected experiment."""
    if not selected_experiment:
        return [], None

    # Query all distinct reactor numbers for this experiment with sample_type=1
    reactors = list(
        ViCellData.objects.filter(
            experiment=selected_experiment,
            sample_type=1,
            reactor_number__isnull=False
        ).values_list("reactor_number", flat=True).distinct()
    )

    # Ensure reactors are sorted numerically
    sorted_reactors = sorted(filter(lambda x: x is not None, reactors))

    if not sorted_reactors:
        print("⚠️ No reactor numbers found!")
        return [], None

    # Create dropdown options
    options = [{"label": f"Reactor {reactor}", "value": reactor} for reactor in sorted_reactors]

    return options, (sorted_reactors[0] if sorted_reactors else None)


@app.callback(
    Output("subset-table", "data"),
    [Input("subset-dropdown", "value"),
     Input("selected-experiment", "data")]
)
def update_summary_table(selected_reactor, selected_experiment):
    """Populate table with data when a reactor number is selected from the selected experiment."""
    if not selected_experiment or not selected_reactor:
        print("⚠️ No reactor or experiment selected.")
        return []

    # Query ViCellData for the selected reactor and experiment with sample_type=1
    vicell_data = ViCellData.objects.filter(
        experiment=selected_experiment,
        sample_type=1,
        reactor_number=selected_reactor
    ).order_by("day", "special")

    # Convert to list of dictionaries for DataTable
    data = []
    for record in vicell_data:
        row = {
            "sample_id": record.sample_id,
            "date_time": record.date_time.strftime("%m/%d/%Y %I:%M:%S %p") if record.date_time else "",
            "day": record.day,
            "process_time_hours": record.process_time_hours if hasattr(record, "process_time_hours") else None,
            "total_cells_per_ml": record.total_cells_per_ml,
            "viable_cells_per_ml": record.viable_cells_per_ml,
            "viability": record.viability,
            "average_viable_diameter": record.average_viable_diameter,
        }
        data.append(row)

    return data


@app.callback(
    Output("variable-graph-container", "children"),
    [Input("selected-experiment", "data"),
     Input("variable-tabs", "value")],
    prevent_initial_call=True
)
def update_graph(selected_experiment, selected_variable):
    """
    Updates the graph based on the selected variable tab.
    Each graph plots different reactor_number groups over time using day as the x-axis.
    """
    if selected_variable is None:
        return "⚠️ No variable selected."
    if selected_variable in ["summary"]:
        return None
    if not selected_experiment:
        return "⚠️ No experiment selected."

    # Use the new function to get experiment data
    grouped_data = process_and_sort_samples_by_experiment(selected_experiment)

    if not grouped_data:
        return "⚠️ No data available to plot for this experiment."

    # Special handling for growth rate and doubling time analysis
    if selected_variable == "growth_rate":
        return create_growth_rate_analysis(grouped_data)
    elif selected_variable == "doubling_time":
        return create_doubling_time_analysis(grouped_data)

    # Create simple plot for standard variables
    fig = go.Figure()

    # Color palette for different reactor numbers
    colors = px.colors.qualitative.Set1

    for idx, (reactor_number, df) in enumerate(grouped_data.items()):
        if df.empty or selected_variable not in df.columns:
            continue

        # Sort by day for proper line plotting
        df_sorted = df.sort_values("day")

        # Add trace for this reactor
        fig.add_trace(go.Scatter(
            x=df_sorted["day"],
            y=df_sorted[selected_variable],
            mode="lines+markers",
            name=f"Reactor {reactor_number}",
            line=dict(color=colors[idx % len(colors)], width=3),
            marker=dict(size=10),
            hovertemplate=f"Reactor {reactor_number}<br>" +
                          "Day: %{x}<br>" +
                          f"{VARIABLES.get(selected_variable, selected_variable)}: %{{y:.2f}}<br>" +
                          "<extra></extra>"
        ))

    # Update layout
    fig.update_layout(
        title={
            'text': f"{VARIABLES.get(selected_variable, selected_variable)} Over Time - {selected_experiment}",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title="Process Day",
        yaxis_title=VARIABLES.get(selected_variable, selected_variable),
        height=700,
        width=None,
        hovermode="x unified",
        template="plotly_white",
        plot_bgcolor='rgba(245, 245, 250, 0.5)',
        paper_bgcolor='white',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="rgba(0, 0, 0, 0.2)",
            borderwidth=1
        ),
        font=dict(family="Arial, sans-serif", size=14),
        margin=dict(l=120, r=220, t=140, b=120),
        autosize=True
    )

    # Update axes styling
    fig.update_xaxes(
        gridcolor='rgba(128, 128, 128, 0.2)',
        showgrid=True,
        zeroline=False
    )
    fig.update_yaxes(
        gridcolor='rgba(128, 128, 128, 0.2)',
        showgrid=True,
        zeroline=False
    )

    return html.Div([
        dcc.Graph(
            figure=fig,
            style={"width": "100%", "height": "700px"},
            config={"displayModeBar": True, "responsive": True}
        )
    ], style={"width": "100%"})


def create_growth_rate_analysis(grouped_data):
    """Create specialized growth rate analysis plots"""
    from plotly.subplots import make_subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Growth Curves (Log Scale)", "Specific Growth Rate",
                        "Growth Rate Distribution", "Exponential Phase Detection"),
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )

    colors = px.colors.qualitative.Set1

    for idx, (reactor_number, df) in enumerate(grouped_data.items()):
        if df.empty or "viable_cells_per_ml" not in df.columns:
            continue

        df_sorted = df.sort_values("day")
        viable_cells = df_sorted["viable_cells_per_ml"].values
        days = df_sorted["day"].values

        # Skip if not enough data
        if len(viable_cells) < 3:
            continue

        # Calculate growth rates
        log_cells = np.log(viable_cells)
        growth_rates = np.diff(log_cells) / np.diff(days)

        # 1. Growth curves (log scale)
        fig.add_trace(go.Scatter(
            x=days,
            y=viable_cells,
            mode="lines+markers",
            name=f"Reactor {reactor_number}",
            line=dict(color=colors[idx % len(colors)], width=2),
            marker=dict(size=8)
        ), row=1, col=1)

        # 2. Specific growth rate over time
        fig.add_trace(go.Scatter(
            x=days[1:],
            y=growth_rates,
            mode="lines+markers",
            name=f"μ R{reactor_number}",
            line=dict(color=colors[idx % len(colors)], width=2),
            marker=dict(size=8)
        ), row=1, col=2)

        # 3. Growth rate distribution
        fig.add_trace(go.Histogram(
            x=growth_rates,
            name=f"R{reactor_number}",
            marker_color=colors[idx % len(colors)],
            opacity=0.7,
            nbinsx=20
        ), row=2, col=1)

        # 4. Exponential phase detection
        # Find the period of maximum sustained growth
        if len(growth_rates) >= 3:
            window_size = min(3, len(growth_rates))
            moving_avg = np.convolve(growth_rates, np.ones(window_size) / window_size, mode='valid')

            fig.add_trace(go.Scatter(
                x=days[window_size:],
                y=moving_avg,
                mode="lines",
                name=f"MA R{reactor_number}",
                line=dict(color=colors[idx % len(colors)], width=3)
            ), row=2, col=2)

    # Update layouts
    fig.update_xaxes(title_text="Process Day", row=1, col=1)
    fig.update_xaxes(title_text="Process Day", row=1, col=2)
    fig.update_xaxes(title_text="Growth Rate (1/day)", row=2, col=1)
    fig.update_xaxes(title_text="Process Day", row=2, col=2)

    fig.update_yaxes(title_text="Viable Cells/mL", type="log", row=1, col=1)
    fig.update_yaxes(title_text="Specific Growth Rate (1/day)", row=1, col=2)
    fig.update_yaxes(title_text="Frequency", row=2, col=1)
    fig.update_yaxes(title_text="Moving Avg Growth Rate", row=2, col=2)

    fig.update_layout(
        height=1000,
        width=None,
        showlegend=True,
        template="plotly_white",
        plot_bgcolor='rgba(245, 245, 250, 0.5)',
        paper_bgcolor='white',
        margin=dict(l=120, r=120, t=140, b=120),
        autosize=True
    )

    return html.Div([
        dcc.Graph(
            figure=fig,
            style={"width": "100%", "height": "1000px"},
            config={"displayModeBar": True, "responsive": True}
        )
    ], style={"width": "100%"})


def create_doubling_time_analysis(grouped_data):
    """Create doubling time analysis"""
    fig = go.Figure()

    colors = px.colors.qualitative.Set1

    for idx, (reactor_number, df) in enumerate(grouped_data.items()):
        if df.empty or "viable_cells_per_ml" not in df.columns:
            continue

        df_sorted = df.sort_values("day")
        viable_cells = df_sorted["viable_cells_per_ml"].values
        days = df_sorted["day"].values

        if len(viable_cells) < 2:
            continue

        # Calculate doubling times
        doubling_times = []
        doubling_days = []

        for i in range(1, len(viable_cells)):
            if viable_cells[i] > viable_cells[i - 1]:
                # Calculate growth rate
                growth_rate = (np.log(viable_cells[i]) - np.log(viable_cells[i - 1])) / (days[i] - days[i - 1])
                # Calculate doubling time
                if growth_rate > 0:
                    dt = np.log(2) / growth_rate * 24  # Convert to hours
                    doubling_times.append(dt)
                    doubling_days.append((days[i] + days[i - 1]) / 2)

        if doubling_times:
            fig.add_trace(go.Scatter(
                x=doubling_days,
                y=doubling_times,
                mode="lines+markers",
                name=f"Reactor {reactor_number}",
                line=dict(color=colors[idx % len(colors)], width=3),
                marker=dict(size=10),
                hovertemplate=f"Reactor {reactor_number}<br>" +
                              "Day: %{x:.1f}<br>" +
                              "Doubling Time: %{y:.1f} hours<br>" +
                              "<extra></extra>"
            ))

    # Add reference line for typical doubling time
    fig.add_hline(y=24, line_dash="dash", line_color="gray",
                  annotation_text="24h Reference",
                  annotation_position="right")

    fig.update_layout(
        title="Population Doubling Time Analysis",
        xaxis_title="Process Day",
        yaxis_title="Doubling Time (hours)",
        height=700,
        width=None,
        hovermode="x unified",
        template="plotly_white",
        plot_bgcolor='rgba(245, 245, 250, 0.5)',
        paper_bgcolor='white',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.95,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="rgba(0, 0, 0, 0.2)",
            borderwidth=1
        ),
        margin=dict(l=120, r=220, t=140, b=120),
        autosize=True
    )

    return html.Div([
        dcc.Graph(
            figure=fig,
            style={"width": "100%", "height": "700px"},
            config={"displayModeBar": True, "responsive": True}
        )
    ], style={"width": "100%"})
