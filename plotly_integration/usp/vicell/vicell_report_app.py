import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State, MATCH, dash_table
from django_plotly_dash import DjangoDash
import pandas as pd
from plotly_integration.models import ViCellData, USPExperiment, USPProcessStep, USPSeedTrain, USPVessel
import json
from datetime import datetime, timedelta
import pytz
import re
import plotly.express as px
from plotly.subplots import make_subplots

# Initialize the Dash app with Bootstrap theme
app = DjangoDash("USPViCellApp", external_stylesheets=[dbc.themes.BOOTSTRAP])

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
    # {"name": "Date/Time", "id": "date_time", "editable": False},
    # {"name": "Experiment", "id": "experiment", "editable": True},
    # {"name": "Reactor Type", "id": "reactor_type", "editable": True},
    # {"name": "Reactor Number", "id": "reactor_number", "editable": True},
    # {"name": "Day", "id": "day", "editable": True},
    # {"name": "Special", "id": "special", "editable": False},
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
        dcc.Store(id="selected-process-step", data=None),
        dcc.Store(id="embedded-mode", data=False),
        dcc.Store(id="url-params", data={}),
        dcc.Store(id="edit-data-store", data=[]),
        dcc.Location(id="url", refresh=False),
        dcc.Interval(id="load-once", interval=1000, n_intervals=0, max_intervals=1),

        # Modal for Edit Data
        dbc.Modal([
            dbc.ModalHeader(
                dbc.ModalTitle([html.I(className="bi bi-pencil me-2"), "Edit ViCell Data"]),
                close_button=True
            ),
            dbc.ModalBody([
                html.Div(id="save-status-message", className="mb-3"),
                dbc.Spinner(
                    dash_table.DataTable(
                        id="edit-data-table",
                        columns=EDIT_DATA_COLUMNS,
                        data=[],
                        page_size=25,
                        editable=True,
                        row_deletable=False,
                        style_table={
                            "overflowX": "auto",
                            "maxHeight": "calc(100vh - 300px)",
                            "overflowY": "auto"
                        },
                        style_header={
                            "backgroundColor": "#f8f9fa",
                            "fontWeight": "bold",
                            "textAlign": "center",
                            "color": "#495057",
                            "fontSize": "13px",
                            "position": "sticky",
                            "top": 0,
                            "zIndex": 1
                        },
                        style_cell={
                            "textAlign": "center",
                            "padding": "10px",
                            "borderBottom": "1px solid #dee2e6",
                            "fontSize": "13px",
                            "minWidth": "80px",
                            "maxWidth": "180px",
                            "overflow": "hidden",
                            "textOverflow": "ellipsis"
                        },
                        style_data={"backgroundColor": "white", "color": "#212529"},
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
                    ),
                    color="primary"
                )
            ]),
            dbc.ModalFooter([
                dbc.Button(
                    [html.I(className="bi bi-arrow-clockwise me-2"), "Refresh"],
                    id="refresh-data-btn",
                    color="info",
                    className="me-2"
                ),
                dbc.Button(
                    [html.I(className="bi bi-check-lg me-2"), "Save Changes"],
                    id="save-changes-btn",
                    color="success"
                )
            ])
        ], id="edit-data-modal", fullscreen=True, is_open=False, scrollable=True),

        # Modal for Select Experiment
        dbc.Modal([
            dbc.ModalHeader(
                dbc.ModalTitle([html.I(className="bi bi-folder me-2"), "Select USP Experiment"]),
                close_button=True
            ),
            dbc.ModalBody([
                dbc.Spinner(
                    dash_table.DataTable(
                        id="experiment-selection-table",
                        columns=[
                            {"name": "Experiment ID", "id": "experiment_id"},
                            {"name": "Name", "id": "experiment_name"},
                            {"name": "Status", "id": "status"},
                            {"name": "Start Date", "id": "start_date"}
                        ],
                        data=[],
                        row_selectable="single",
                        selected_rows=[],
                        page_size=10,
                        sort_action="native",
                        filter_action="native",
                        style_table={
                            "overflowY": "auto",
                            "maxHeight": "500px"
                        },
                        style_cell={
                            "textAlign": "left",
                            "padding": "12px",
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
                                "backgroundColor": "#cfe2ff",
                                "border": "1px solid #0d6efd",
                            }
                        ]
                    ),
                    color="primary"
                )
            ], style={"minHeight": "400px"}),
            dbc.ModalFooter([
                dbc.Button(
                    [html.I(className="bi bi-check-lg me-2"), "Select Experiment"],
                    id="confirm-experiment-selection",
                    color="primary",
                    size="lg"
                )
            ])
        ], id="select-experiment-modal", size="xl", is_open=False),

        # Top toolbar with action buttons and filters
        dbc.Container(
            fluid=True,
            className="p-3 bg-light border-bottom",
            children=[
                # Top row - Action buttons and current experiment badge
                dbc.Row([
                    dbc.Col([
                        dbc.ButtonGroup([
                            dbc.Button(
                                [html.I(className="bi bi-folder me-2"), "Select Experiment"],
                                id="change-experiment-btn",
                                color="secondary",
                                className="me-2"
                            ),
                            dbc.Button(
                                [html.I(className="bi bi-pencil me-2"), "Edit Data"],
                                id="edit-data-btn",
                                color="danger"
                            )
                        ])
                    ], width="auto"),
                    dbc.Col([
                        html.Div(
                            id="current-experiment-text",
                            className="h5 mb-0 text-muted"
                        )
                    ], className="d-flex align-items-center justify-content-end")
                ], className="mb-3"),

                # Bottom row - Filter controls
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Process Step", html_for="process-step-dropdown", className="fw-bold"),
                        dcc.Dropdown(
                            id="process-step-dropdown",
                            placeholder="Select Process Step",
                            className="mb-2"
                        )
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Vessel Filter", html_for="vessel-filter-dropdown", className="fw-bold"),
                        dcc.Dropdown(
                            id="vessel-filter-dropdown",
                            placeholder="All Vessels",
                            multi=True,
                            className="mb-2"
                        )
                    ], md=6)
                ])
            ]
        ),

        # Main content area
        dbc.Container(
            fluid=True,
            className="p-3",
            children=[
                # Bootstrap Tabs for better styling
                dbc.Card([
                    dbc.CardHeader(
                        dbc.Tabs(
                            id="variable-tabs",
                            active_tab="viable_cells_per_ml",
                            children=[
                                dbc.Tab(label=label, tab_id=var, label_style={"cursor": "pointer"})
                                for var, label in VARIABLES.items()
                            ] + [
                                dbc.Tab(label="📊 Summary", tab_id="summary", label_style={"cursor": "pointer"})
                            ]
                        )
                    ),
                    dbc.CardBody([
                        # Summary container
                        html.Div(
                            id="summary-container",
                            style={"display": "block"},
                            children=[
                                dbc.Row([
                                    dbc.Col([
                                        html.H4([html.I(className="bi bi-table me-2"), "Vessel Data"], className="text-primary mb-3")
                                    ], width=8),
                                    dbc.Col([
                                        dcc.Dropdown(
                                            id="subset-dropdown",
                                            placeholder="Select Vessel to View",
                                            className="mb-3"
                                        )
                                    ], width=4)
                                ]),
                                dbc.Spinner(
                                    dash_table.DataTable(
                                        id="subset-table",
                                        columns=INITIAL_COLUMNS,
                                        data=[],
                                        style_table={
                                            "overflowX": "auto",
                                            "overflowY": "auto",
                                            "maxHeight": "600px"
                                        },
                                        style_header={
                                            "backgroundColor": "#f8f9fa",
                                            "fontWeight": "bold",
                                            "textAlign": "center",
                                            "color": "#495057",
                                            "fontSize": "14px"
                                        },
                                        style_cell={
                                            "textAlign": "center",
                                            "padding": "12px",
                                            "borderBottom": "1px solid #dee2e6",
                                            "fontSize": "13px"
                                        },
                                        style_data={"backgroundColor": "white", "color": "#212529"},
                                        style_data_conditional=[
                                            {
                                                "if": {"row_index": "odd"},
                                                "backgroundColor": "#f8f9fa",
                                            }
                                        ],
                                        filter_action="native",
                                        sort_action="native"
                                    ),
                                    color="primary"
                                )
                            ]
                        ),

                        # Graph container
                        html.Div(
                            id="variable-graph-container",
                            style={"display": "none"}
                        )
                    ])
                ], className="shadow-sm")
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
    Output("edit-data-modal", "is_open"),
    [Input("edit-data-btn", "n_clicks")],
    [State("edit-data-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_edit_data_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open


# Callback to show/hide Select Experiment modal and populate experiments
@app.callback(
    [Output("select-experiment-modal", "is_open"),
     Output("experiment-selection-table", "data"),
     Output("current-experiment-text", "children")],
    [Input("change-experiment-btn", "n_clicks"),
     Input("confirm-experiment-selection", "n_clicks"),
     Input("load-once", "n_intervals"),
     Input("url-params", "data")],
    [State("select-experiment-modal", "is_open"),
     State("experiment-selection-table", "selected_rows"),
     State("experiment-selection-table", "data"),
     State("embedded-mode", "data"),
     State("selected-experiment", "data")],
    prevent_initial_call=False
)
def toggle_select_modal(change_clicks, confirm_clicks, load_interval,
                        url_params, is_open, selected_rows, table_data,
                        embedded, current_experiment):
    ctx = dash.callback_context

    # Get trigger ID
    if not ctx.triggered:
        triggered_id = None
    else:
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Fetch experiments from USPExperiment model
    experiments_query = USPExperiment.objects.all().order_by("-created_date")

    experiments_data = [{
        "experiment_id": exp.experiment_id,
        "experiment_name": exp.experiment_name,
        "status": exp.status,
        "start_date": exp.start_date.strftime("%Y-%m-%d") if exp.start_date else ""
    } for exp in experiments_query]

    # Determine current experiment text
    if current_experiment:
        current_text = dbc.Badge(
            f"🔬 {current_experiment}",
            color="info",
            className="fs-6 px-3 py-2"
        )
    else:
        current_text = dbc.Badge(
            "No experiment selected",
            color="secondary",
            className="fs-6 px-3 py-2"
        )

    # Handle modal visibility
    if triggered_id == "change-experiment-btn":
        return not is_open, experiments_data, current_text
    elif triggered_id == "confirm-experiment-selection" and selected_rows and table_data:
        # Experiment will be selected by another callback, close modal
        return False, experiments_data, current_text

    return is_open, experiments_data, current_text


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

    if triggered_id == "url-params" and "experiment_id" in url_params:
        # Load from URL
        return url_params["experiment_id"]
    elif triggered_id == "confirm-experiment-selection" and selected_rows and table_data:
        # Load from selection
        selected_experiment = table_data[selected_rows[0]]
        return selected_experiment["experiment_id"]

    return None


# Populate process step dropdown based on selected experiment
@app.callback(
    [Output("process-step-dropdown", "options"),
     Output("process-step-dropdown", "value")],
    [Input("selected-experiment", "data")],
    prevent_initial_call=False
)
def update_process_step_dropdown(selected_experiment_id):
    """Populate dropdown with process steps from the selected experiment."""
    if not selected_experiment_id:
        return [], None

    # Query all process steps for this experiment
    try:
        experiment = USPExperiment.objects.get(experiment_id=selected_experiment_id)
        process_steps = USPProcessStep.objects.filter(experiment=experiment).order_by('step_order')

        if not process_steps.exists():
            print(f"⚠️ No process steps found for experiment {selected_experiment_id}")
            return [], None

        # Create dropdown options
        options = [{
            "label": f"{step.step_order}. {step.step_name} ({step.step_type})",
            "value": step.id
        } for step in process_steps]

        # Auto-select first step
        return options, process_steps.first().id if process_steps.exists() else None
    except USPExperiment.DoesNotExist:
        print(f"⚠️ Experiment {selected_experiment_id} not found")
        return [], None


# Update selected process step store and populate vessel filter
@app.callback(
    [Output("selected-process-step", "data"),
     Output("vessel-filter-dropdown", "options")],
    [Input("process-step-dropdown", "value")],
    prevent_initial_call=False
)
def update_vessel_filter(process_step_id):
    """Store selected process step and populate vessel filter with seed trains and vessels."""
    if not process_step_id:
        return None, []

    try:
        process_step = USPProcessStep.objects.get(id=process_step_id)

        # Get all seed trains for this process step
        seed_trains = USPSeedTrain.objects.filter(process_step=process_step)

        # Get all vessels for this process step
        vessels = USPVessel.objects.filter(process_step=process_step)

        # Build options list
        options = []

        # Add seed trains
        for st in seed_trains:
            vessel_type = st.vessel_type.replace('_', ' ')
            options.append({
                "label": f"🧪 {st.seed_train_id} ({vessel_type})",
                "value": st.seed_train_id
            })

        # Add vessels (fed batches)
        for vessel in vessels:
            vessel_type = vessel.vessel_type.replace('_', ' ')
            icon = "🔬" if "BRX" in vessel.vessel_type else "🧫"
            options.append({
                "label": f"{icon} {vessel.vessel_id} ({vessel_type})",
                "value": vessel.vessel_id
            })

        return process_step_id, options

    except USPProcessStep.DoesNotExist:
        print(f"⚠️ Process step {process_step_id} not found")
        return None, []


# Toggle between summary and graph views
@app.callback(
    [Output("summary-container", "style"),
     Output("variable-graph-container", "style")],
    Input("variable-tabs", "active_tab")
)
def toggle_view(active_tab):
    if active_tab == "summary":
        summary_style = {"display": "block"}
        graph_style = {"display": "none"}
    else:
        summary_style = {"display": "none"}
        graph_style = {"display": "block"}

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
        # Query ViCellData for the selected experiment with sample_type=3 (USP)
        if selected_experiment:
            vicell_data = ViCellData.objects.filter(
                experiment=selected_experiment,
                sample_type=3
            ).order_by("-date_time")
        else:
            # If no experiment selected, show all sample_type=3 data
            vicell_data = ViCellData.objects.filter(sample_type=3).order_by(
                "-date_time"
            )

        # Convert to list of dictionaries for DataTable
        # Get Pacific timezone for display
        pacific_tz = pytz.timezone('US/Pacific')

        data = []
        for record in vicell_data:
            # Convert UTC datetime to Pacific time for display
            if record.date_time:
                local_time = record.date_time.astimezone(pacific_tz)
                date_str = local_time.strftime("%m/%d/%Y %I:%M:%S %p")
            else:
                date_str = ""

            row = {
                "id": record.id,
                "sample_id": record.sample_id,
                "date_time": date_str,
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
    Output("save-status-message", "children"),
    [Input("save-changes-btn", "n_clicks")],
    [State("edit-data-table", "data"),
     State("edit-data-store", "data")],
    prevent_initial_call=True
)
def save_changes(save_clicks, current_data, original_data):
    if not save_clicks or not current_data:
        return ""

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

        # Prepare status message as Bootstrap alert
        if changes_made > 0 and not errors:
            return dbc.Alert(
                [html.I(className="bi bi-check-circle me-2"), f"Successfully saved {changes_made} changes!"],
                color="success",
                dismissable=True
            )
        elif changes_made > 0 and errors:
            return dbc.Alert(
                [html.I(className="bi bi-exclamation-triangle me-2"),
                 f"Saved {changes_made} changes with {len(errors)} errors. Errors: {'; '.join(errors[:3])}"],
                color="warning",
                dismissable=True
            )
        elif errors:
            return dbc.Alert(
                [html.I(className="bi bi-x-circle me-2"),
                 f"Failed to save changes. Errors: {'; '.join(errors[:3])}"],
                color="danger",
                dismissable=True
            )
        else:
            return dbc.Alert(
                [html.I(className="bi bi-info-circle me-2"), "No changes detected."],
                color="info",
                dismissable=True
            )

    except Exception as e:
        return dbc.Alert(
            [html.I(className="bi bi-x-circle me-2"), f"Error saving changes: {str(e)}"],
            color="danger",
            dismissable=True
        )


def calculate_process_days(df, process_step):
    """
    Calculate process day and process time (hours) for each sample based on vessel-specific start dates.

    Args:
        df: DataFrame with 'sample_id', 'date_time', and vessel_id information
        process_step: The USPProcessStep object to get vessel start dates from

    Returns:
        DataFrame with added 'process_day' and 'process_time_hours' columns
    """
    if df.empty or 'date_time' not in df.columns:
        return df

    # Convert date_time to datetime if it's not already
    df['date_time'] = pd.to_datetime(df['date_time'])

    # Extract vessel ID from sample_id (assumes format like UPST#### or UPFB#### )
    def extract_vessel_id(sample_id):
        """Extract vessel ID from sample_id string."""
        if not sample_id:
            return None
        # Look for patterns like UPST#### or UPFB#### (case insensitive)
        match = re.search(r'(UPST\d+|UPFB\d+)', str(sample_id), re.IGNORECASE)
        result = match.group(1).upper() if match else None
        return result

    df['vessel_id'] = df['sample_id'].apply(extract_vessel_id)

    # Debug: Show extracted vessel IDs
    extracted_vessels = df['vessel_id'].dropna().unique()
    print(f"✓ Extracted vessel IDs from sample_ids: {extracted_vessels}")

    # Convert to Pacific timezone before extracting date (important for correct process day calculation)
    pacific_tz = pytz.timezone('US/Pacific')
    df['date_time_local'] = df['date_time'].dt.tz_convert(pacific_tz)
    df['date_only'] = df['date_time_local'].dt.date

    # Get start dates for each vessel (thaw_date for seed trains, inoculation_date for vessels)
    seed_trains = {st.seed_train_id: st.thaw_date for st in USPSeedTrain.objects.filter(process_step=process_step)}
    vessels = {v.vessel_id: v.inoculation_date for v in USPVessel.objects.filter(process_step=process_step)}

    # Combine into one lookup
    vessel_start_dates = {**seed_trains, **vessels}

    print(f"✓ Vessel start dates: {vessel_start_dates}")

    # Calculate process day for each vessel based on its start date
    def calculate_day(row):
        vessel_id = row['vessel_id']
        date_only = row['date_only']
        if not vessel_id or not date_only:
            return 0
        start_date = vessel_start_dates.get(vessel_id)
        if not start_date:
            return 0
        days = (date_only - start_date).days
        return max(0, days)  # Set negative days to 0

    df['process_day'] = df.apply(calculate_day, axis=1)

    # Calculate process time in hours (from midnight of the process day) using local time
    df['process_time_hours'] = df['process_day'] * 24 + df['date_time_local'].dt.hour + df['date_time_local'].dt.minute / 60

    return df


def process_and_sort_samples_by_vessel(process_step_id, vessel_filter=None):
    """
    Fetches ViCell data for vessels associated with a process step.
    Groups by vessel ID for plotting.

    Args:
        process_step_id: ID of the USPProcessStep
        vessel_filter: Optional list of vessel IDs to filter (if None, shows all)

    Returns:
        Dictionary with vessel_id as keys and DataFrames as values
    """
    try:
        process_step = USPProcessStep.objects.get(id=process_step_id)
        experiment = process_step.experiment
        experiment_start_date = experiment.start_date
        print(f"✓ Found process step: {process_step.step_name} (ID: {process_step_id})")
        print(f"✓ Experiment start date: {experiment_start_date}")
    except USPProcessStep.DoesNotExist:
        print(f"⚠️ Process step {process_step_id} not found")
        return {}

    # Get all vessel IDs from this process step
    seed_train_ids = list(USPSeedTrain.objects.filter(
        process_step=process_step
    ).values_list('seed_train_id', flat=True))

    vessel_ids = list(USPVessel.objects.filter(
        process_step=process_step
    ).values_list('vessel_id', flat=True))

    all_vessel_ids = seed_train_ids + vessel_ids

    print(f"✓ Found {len(seed_train_ids)} seed trains: {seed_train_ids}")
    print(f"✓ Found {len(vessel_ids)} vessels: {vessel_ids}")

    # Apply vessel filter if provided
    if vessel_filter:
        all_vessel_ids = [vid for vid in all_vessel_ids if vid in vessel_filter]
        print(f"✓ After filter: {all_vessel_ids}")

    if not all_vessel_ids:
        print(f"⚠️ No vessels found for process step {process_step_id}")
        return {}

    # Query ViCellData where sample_id contains any of these vessel IDs
    # Using Q objects for OR queries
    from django.db.models import Q
    query = Q()
    for vessel_id in all_vessel_ids:
        query |= Q(sample_id__icontains=vessel_id)

    print(f"🔍 Querying ViCellData for vessels: {all_vessel_ids}")

    samples = ViCellData.objects.filter(
        query,
        sample_type=3  # USP samples (changed from 1 to 3)
    ).values(
        "sample_id", "experiment", "day", "reactor_type", "reactor_number", "special",
        "date_time", "cell_count", "viable_cells", "total_cells_per_ml", "viable_cells_per_ml",
        "viability", "average_diameter", "average_viable_diameter", "average_circularity",
        "average_viable_circularity"
    )

    df = pd.DataFrame(list(samples))

    print(f"✓ Found {len(df)} ViCell records")
    if not df.empty:
        print(f"   Sample IDs: {df['sample_id'].unique()[:5]}...")  # Show first 5

    if df.empty:
        print(f"⚠️ No ViCell data found for vessels: {all_vessel_ids}")
        return {}

    # Calculate process days based on vessel-specific start dates
    df = calculate_process_days(df, process_step)

    # Sort by vessel_id, then by process_day
    df_sorted = df.sort_values(by=["vessel_id", "process_day"], ascending=[True, True])

    # Group by vessel_id
    grouped_data = {}

    for vessel_id in df_sorted["vessel_id"].dropna().unique():
        vessel_df = df_sorted[df_sorted["vessel_id"] == vessel_id]
        if not vessel_df.empty:
            # Determine vessel type (BRX or SF)
            vessel_type = "Unknown"
            if vessel_id.startswith("UPST"):
                st = USPSeedTrain.objects.filter(seed_train_id=vessel_id).first()
                vessel_type = st.vessel_type if st else "Seed Train"
            elif vessel_id.startswith("UPFB"):
                vessel = USPVessel.objects.filter(vessel_id=vessel_id).first()
                vessel_type = vessel.vessel_type if vessel else "Fed Batch"

            # Store vessel type in the dataframe for reference
            vessel_df = vessel_df.copy()
            vessel_df['vessel_type'] = vessel_type

            grouped_data[vessel_id] = vessel_df
        else:
            print(f"⚠️ No data found for vessel {vessel_id}")

    return grouped_data


@app.callback(
    [Output("subset-dropdown", "options"),
     Output("subset-dropdown", "value")],
    [Input("selected-process-step", "data"),
     Input("vessel-filter-dropdown", "value")]
)
def update_vessel_dropdown(process_step_id, vessel_filter):
    """Populate dropdown with available vessels from the selected process step."""
    if not process_step_id:
        return [], None

    # Get grouped data for this process step
    grouped_data = process_and_sort_samples_by_vessel(process_step_id, vessel_filter)

    if not grouped_data:
        print("⚠️ No vessels with ViCell data found!")
        return [], None

    # Create dropdown options from vessels that have data
    vessel_ids = list(grouped_data.keys())
    options = []

    for vessel_id in sorted(vessel_ids):
        vessel_type = grouped_data[vessel_id]['vessel_type'].iloc[0] if 'vessel_type' in grouped_data[vessel_id].columns else "Unknown"
        vessel_type_short = vessel_type.replace('_', ' ')
        icon = "🔬" if "BRX" in vessel_type else "🧫" if "SF" in vessel_type else "🧪"
        options.append({
            "label": f"{icon} {vessel_id} ({vessel_type_short})",
            "value": vessel_id
        })

    return options, (vessel_ids[0] if vessel_ids else None)


@app.callback(
    Output("subset-table", "data"),
    [Input("subset-dropdown", "value"),
     Input("selected-process-step", "data"),
     Input("vessel-filter-dropdown", "value")]
)
def update_summary_table(selected_vessel_id, process_step_id, vessel_filter):
    """Populate table with data when a vessel is selected."""
    if not process_step_id or not selected_vessel_id:
        print("⚠️ No vessel or process step selected.")
        return []

    # Get grouped data for this process step
    grouped_data = process_and_sort_samples_by_vessel(process_step_id, vessel_filter)

    if selected_vessel_id not in grouped_data:
        print(f"⚠️ No data found for vessel {selected_vessel_id}")
        return []

    vessel_df = grouped_data[selected_vessel_id]

    # Convert to list of dictionaries for DataTable
    # Get Pacific timezone for display
    pacific_tz = pytz.timezone('US/Pacific')

    data = []
    for _, record in vessel_df.iterrows():
        # Convert UTC datetime to Pacific time for display
        if pd.notna(record.get("date_time")):
            dt = pd.to_datetime(record.get("date_time"))
            # If datetime is timezone-aware, convert to Pacific; if naive, assume UTC first
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
            local_time = dt.astimezone(pacific_tz)
            date_str = local_time.strftime("%m/%d/%Y %I:%M:%S %p")
        else:
            date_str = ""

        row = {
            "sample_id": record.get("sample_id", ""),
            "date_time": date_str,
            "day": int(record.get("process_day", 0)) if pd.notna(record.get("process_day")) else 0,
            "process_time_hours": round(record.get("process_time_hours", 0), 2) if pd.notna(record.get("process_time_hours")) else 0,
            "total_cells_per_ml": record.get("total_cells_per_ml"),
            "viable_cells_per_ml": record.get("viable_cells_per_ml"),
            "viability": record.get("viability"),
            "average_viable_diameter": record.get("average_viable_diameter"),
        }
        data.append(row)

    return data


@app.callback(
    Output("variable-graph-container", "children"),
    [Input("selected-process-step", "data"),
     Input("vessel-filter-dropdown", "value"),
     Input("variable-tabs", "active_tab")],
    prevent_initial_call=True
)
def update_graph(process_step_id, vessel_filter, selected_variable):
    """
    Updates the graph based on the selected variable tab.
    Each graph plots different vessel groups over time using process_day as the x-axis.
    """
    if selected_variable is None:
        return "⚠️ No variable selected."
    if selected_variable in ["summary"]:
        return None
    if not process_step_id:
        return "⚠️ No process step selected."

    # Use the new function to get vessel data
    grouped_data = process_and_sort_samples_by_vessel(process_step_id, vessel_filter)

    if not grouped_data:
        return "⚠️ No data available to plot for this process step."

    # Special handling for growth rate and doubling time analysis
    if selected_variable == "growth_rate":
        return create_growth_rate_analysis(grouped_data)
    elif selected_variable == "doubling_time":
        return create_doubling_time_analysis(grouped_data)

    # Create simple plot for standard variables
    fig = go.Figure()

    # Color palette for different vessels
    colors = px.colors.qualitative.Set1

    # Get process step info for title
    try:
        process_step = USPProcessStep.objects.get(id=process_step_id)
        experiment_info = f"{process_step.experiment.experiment_id} - {process_step.step_name}"
    except:
        experiment_info = "USP Experiment"

    for idx, (vessel_id, df) in enumerate(grouped_data.items()):
        if df.empty or selected_variable not in df.columns:
            continue

        # Sort by process_day for proper line plotting
        df_sorted = df.sort_values("process_day")

        # Get vessel type for legend
        vessel_type = df_sorted['vessel_type'].iloc[0] if 'vessel_type' in df_sorted.columns else "Unknown"
        vessel_type_short = vessel_type.replace('_', ' ')
        icon = "🔬" if "BRX" in vessel_type else "🧫" if "SF" in vessel_type else "🧪"

        # Add trace for this vessel
        fig.add_trace(go.Scatter(
            x=df_sorted["process_day"],
            y=df_sorted[selected_variable],
            mode="lines+markers",
            name=f"{icon} {vessel_id} ({vessel_type_short})",
            line=dict(color=colors[idx % len(colors)], width=3),
            marker=dict(size=10),
            hovertemplate=f"{vessel_id}<br>" +
                          "Day: %{x}<br>" +
                          f"{VARIABLES.get(selected_variable, selected_variable)}: %{{y:.2f}}<br>" +
                          "<extra></extra>"
        ))

    # Update layout
    fig.update_layout(
        title={
            'text': f"{VARIABLES.get(selected_variable, selected_variable)} Over Time - {experiment_info}",
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

    for idx, (vessel_id, df) in enumerate(grouped_data.items()):
        if df.empty or "viable_cells_per_ml" not in df.columns:
            continue

        df_sorted = df.sort_values("process_day")
        viable_cells = df_sorted["viable_cells_per_ml"].values
        days = df_sorted["process_day"].values

        # Skip if not enough data
        if len(viable_cells) < 3:
            continue

        # Calculate growth rates
        log_cells = np.log(viable_cells)
        growth_rates = np.diff(log_cells) / np.diff(days)

        # Get vessel type for legend
        vessel_type = df_sorted['vessel_type'].iloc[0] if 'vessel_type' in df_sorted.columns else "Unknown"
        icon = "🔬" if "BRX" in vessel_type else "🧫" if "SF" in vessel_type else "🧪"
        vessel_label = f"{icon} {vessel_id}"

        # 1. Growth curves (log scale)
        fig.add_trace(go.Scatter(
            x=days,
            y=viable_cells,
            mode="lines+markers",
            name=vessel_label,
            line=dict(color=colors[idx % len(colors)], width=2),
            marker=dict(size=8)
        ), row=1, col=1)

        # 2. Specific growth rate over time
        fig.add_trace(go.Scatter(
            x=days[1:],
            y=growth_rates,
            mode="lines+markers",
            name=f"μ {vessel_id}",
            line=dict(color=colors[idx % len(colors)], width=2),
            marker=dict(size=8)
        ), row=1, col=2)

        # 3. Growth rate distribution
        fig.add_trace(go.Histogram(
            x=growth_rates,
            name=vessel_id,
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
                name=f"MA {vessel_id}",
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

    for idx, (vessel_id, df) in enumerate(grouped_data.items()):
        if df.empty or "viable_cells_per_ml" not in df.columns:
            continue

        df_sorted = df.sort_values("process_day")
        viable_cells = df_sorted["viable_cells_per_ml"].values
        days = df_sorted["process_day"].values

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
            # Get vessel type for legend
            vessel_type = df_sorted['vessel_type'].iloc[0] if 'vessel_type' in df_sorted.columns else "Unknown"
            icon = "🔬" if "BRX" in vessel_type else "🧫" if "SF" in vessel_type else "🧪"
            vessel_label = f"{icon} {vessel_id}"

            fig.add_trace(go.Scatter(
                x=doubling_days,
                y=doubling_times,
                mode="lines+markers",
                name=vessel_label,
                line=dict(color=colors[idx % len(colors)], width=3),
                marker=dict(size=10),
                hovertemplate=f"{vessel_id}<br>" +
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
