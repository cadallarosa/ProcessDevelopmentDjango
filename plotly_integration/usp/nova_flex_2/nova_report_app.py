import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State, MATCH, dash_table
from django_plotly_dash import DjangoDash
import pandas as pd
from plotly_integration.models import NovaFlex2, USPExperiment, USPProcessStep, USPSeedTrain, USPVessel
import json
from datetime import datetime
import re
import plotly.express as px

# Initialize the Dash app with Bootstrap theme
app = DjangoDash("USPNovaFlexIIApp", external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the variables and their corresponding labels
VARIABLES = {
    "gln": "Glutamine",
    "glu": "Glutamate",
    "gluc": "Glucose",
    "lac": "Lactate",
    "nh4": "Ammonium (NH4+)",
    "pH": "pH",
    "po2": "Partial Oxygen (PO2)",
    "do": "Dissolved Oxygen (DO)",
    "pco2": "Partial Carbon Dioxide (PCO2)",
    "osm": "Osmolality (Osm)"
}

UNITS = {
    "gln": "mmol/L",
    "glu": "mmol/L",
    "gluc": "g/L",
    "lac": "g/L",
    "nh4": "mmol/L",
    "pH": "-",  # No unit for pH
    "po2": "mmHg",
    "do": "mg/L",  # Assuming DO is in mg/L
    "pco2": "mmHg",
    "osm": "mOsm/kg"
}

# ✅ Define initial column structure
INITIAL_COLUMNS = [
    {"name": "Date", "id": "date_time"},
    {"name": "Sample Name", "id": "sample_id"},
    {"name": "Process Day", "id": "day"},
    {"name": "Glutamine (mmol/L)", "id": "gln"},
    {"name": "Glutamate (mmol/L)", "id": "glu"},
    {"name": "Glucose (g/L)", "id": "gluc"},
    {"name": "Lactate (g/L)", "id": "lac"},
    {"name": "Ammonium (mmol/L)", "id": "nh4"},
    {"name": "pH Level", "id": "pH"},
    {"name": "PO₂ (mmHg)", "id": "po2"},
    {"name": "DO", "id": "do"},
    {"name": "PCO₂ (mmHg)", "id": "pco2"},
    {"name": "Osmolality (mOsm/kg)", "id": "osm"}
]

# Define columns for the edit data table
EDIT_DATA_COLUMNS = [
    {"name": "ID", "id": "id", "editable": False},
    {"name": "Sample ID", "id": "sample_id", "editable": True},
    {"name": "Date/Time", "id": "date_time", "editable": False},
    {"name": "Glutamine (mmol/L)", "id": "gln", "editable": False, "format": {"specifier": ".2f"}},
    {"name": "Glutamate (mmol/L)", "id": "glu", "editable": False, "format": {"specifier": ".2f"}},
    {"name": "Glucose (g/L)", "id": "gluc", "editable": False, "format": {"specifier": ".2f"}},
    {"name": "Lactate (g/L)", "id": "lac", "editable": False, "format": {"specifier": ".2f"}},
    {"name": "Ammonium (mmol/L)", "id": "nh4", "editable": False, "format": {"specifier": ".2f"}},
    {"name": "pH", "id": "pH", "editable": False, "format": {"specifier": ".3f"}},
    {"name": "PO₂ (mmHg)", "id": "po2", "editable": False, "format": {"specifier": ".1f"}},
    {"name": "PCO₂ (mmHg)", "id": "pco2", "editable": False, "format": {"specifier": ".1f"}},
    {"name": "Osmolality", "id": "osm", "editable": False, "format": {"specifier": ".1f"}},
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

        # Modal for Edit Data (Full Screen)
        dbc.Modal([
            dbc.ModalHeader(
                dbc.ModalTitle([html.I(className="bi bi-pencil me-2"), "Edit NovaFlex2 Data"]),
                close_button=True
            ),
            dbc.ModalBody([
                html.Div(id="save-status-message", className="mb-3"),
                dbc.Spinner(
                    dash_table.DataTable(
                        id="edit-data-table",
                        columns=EDIT_DATA_COLUMNS,
                        data=[],
                        page_size=50,
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
                            active_tab="summary",
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


# Load NovaFlex2 data into edit table
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
        # Query NovaFlex2 for the selected experiment
        if selected_experiment:
            nova_data = NovaFlex2.objects.filter(
                experiment=selected_experiment
            ).order_by("-date_time")
        else:
            # If no experiment selected, show recent data
            nova_data = NovaFlex2.objects.all().order_by("-date_time")[:100]

        # Convert to list of dictionaries for DataTable
        data = []
        for record in nova_data:
            row = {
                "id": record.id,
                "sample_id": record.sample_id,
                "date_time": record.date_time.strftime("%m/%d/%Y %H:%M:%S") if record.date_time else "",
                "experiment": record.experiment or "",
                "day": record.day,
                "gln": record.gln,
                "glu": record.glu,
                "gluc": record.gluc,
                "lac": record.lac,
                "nh4": record.nh4,
                "pH": record.pH,
                "po2": record.po2,
                "pco2": record.pco2,
                "osm": record.osm,
            }
            data.append(row)

        print(f"Loaded {len(data)} NovaFlex2 records for editing")
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

            # Check if sample_id has changed
            if str(row.get("sample_id", "")) != str(original_row.get("sample_id", "")):
                try:
                    # Get the database record
                    nova_record = NovaFlex2.objects.get(id=record_id)

                    # Update the sample_id field
                    nova_record.sample_id = row.get("sample_id", "")

                    # Save the record
                    nova_record.save()
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

    if "experiment_id" in params:
        experiment = params["experiment_id"][0]
        url_params["experiment_id"] = experiment

    return url_params, embedded


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


def process_and_sort_samples_by_vessel(process_step_id, vessel_filter=None):
    """
    Fetches NovaFlex2 data for vessels associated with a process step.
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

    # Query NovaFlex2 data where sample_id contains any of these vessel IDs
    # Using Q objects for OR queries
    from django.db.models import Q
    query = Q()
    for vessel_id in all_vessel_ids:
        query |= Q(sample_id__icontains=vessel_id)

    print(f"🔍 Querying NovaFlex2 for vessels: {all_vessel_ids}")

    samples = NovaFlex2.objects.filter(query).values(
        "sample_id", "experiment", "day", "reactor_type", "reactor_number", "special",
        "date_time", "gln", "glu", "gluc", "lac", "nh4", "pH", "po2", "pco2", "osm", "dilution_factor"
    )

    df = pd.DataFrame(list(samples))

    print(f"✓ Found {len(df)} NovaFlex2 records")
    if not df.empty:
        print(f"   Sample IDs: {df['sample_id'].unique()[:5]}...")  # Show first 5

    if df.empty:
        print(f"⚠️ No NovaFlex2 data found for vessels: {all_vessel_ids}")
        return {}

    # Extract vessel ID from sample_id
    def extract_vessel_id(sample_id):
        """Extract vessel ID from sample_id string."""
        if not sample_id:
            return None
        # Look for patterns like UPST#### or UPFB#### (case insensitive)
        match = re.search(r'(UPST\d+|UPFB\d+)', str(sample_id), re.IGNORECASE)
        result = match.group(1).upper() if match else None
        return result

    df['vessel_id'] = df['sample_id'].apply(extract_vessel_id)

    # Calculate process day based on vessel-specific start dates (thaw_date or inoculation_date)
    if 'date_time' in df.columns:
        df['date_time'] = pd.to_datetime(df['date_time'])

        # Extract just the date portion (ignoring time)
        df['date_only'] = df['date_time'].dt.date

        # Get start dates for each vessel
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

        df['day'] = df.apply(calculate_day, axis=1)

        print(f"✓ Calculated process days from vessel start dates")

    # Sort by vessel_id and day
    df_sorted = df.sort_values(by=["vessel_id", "day"], ascending=[True, True])

    # Group by vessel_id
    grouped_data = {}

    for vessel_id in df_sorted["vessel_id"].dropna().unique():
        vessel_df = df_sorted[df_sorted["vessel_id"] == vessel_id]
        if not vessel_df.empty:
            # Add the new column `do` (Dissolved Oxygen) as `po2 / 1.6`
            vessel_df = vessel_df.copy()

            # Apply dilution factor to chemistry values (all except pH)
            # Fill NaN dilution_factor values with 1.0 (no dilution)
            vessel_df['dilution_factor'] = vessel_df['dilution_factor'].fillna(1.0)

            chemistry_columns = ['gln', 'glu', 'gluc', 'lac', 'nh4', 'po2', 'pco2', 'osm']
            for col in chemistry_columns:
                if col in vessel_df.columns:
                    vessel_df[col] = vessel_df[col] * vessel_df['dilution_factor']

            # Calculate DO after applying dilution factor to po2
            vessel_df["do"] = vessel_df["po2"] / 1.6

            # Determine vessel type (BRX or SF)
            vessel_type = "Unknown"
            if vessel_id.startswith("UPST"):
                st = USPSeedTrain.objects.filter(seed_train_id=vessel_id).first()
                vessel_type = st.vessel_type if st else "Seed Train"
            elif vessel_id.startswith("UPFB"):
                vessel = USPVessel.objects.filter(vessel_id=vessel_id).first()
                vessel_type = vessel.vessel_type if vessel else "Fed Batch"

            # Store vessel type in the dataframe for reference
            vessel_df['vessel_type'] = vessel_type

            grouped_data[vessel_id] = vessel_df
            print(f"✓ Vessel {vessel_id}: {len(vessel_df)} records, days {vessel_df['day'].min()}-{vessel_df['day'].max()}")
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
        print("⚠️ No vessels with NovaFlex2 data found!")
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
    data = []
    for _, record in vessel_df.iterrows():
        row = {
            "date_time": pd.to_datetime(record.get("date_time")).strftime("%m/%d/%Y %I:%M:%S %p") if pd.notna(record.get("date_time")) else "",
            "sample_id": record.get("sample_id", ""),
            "day": record.get("day"),
            "gln": record.get("gln"),
            "glu": record.get("glu"),
            "gluc": record.get("gluc"),
            "lac": record.get("lac"),
            "nh4": record.get("nh4"),
            "pH": record.get("pH"),
            "po2": record.get("po2"),
            "do": round(record.get("do"), 1) if pd.notna(record.get("do")) else None,
            "pco2": record.get("pco2"),
            "osm": record.get("osm"),
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
    Each graph plots different vessel groups over time using `day` as the x-axis.
    """
    if selected_variable is None:
        return "⚠️ No variable selected."
    if selected_variable == 'summary':
        return None
    if not process_step_id:
        return "⚠️ No process step selected."

    # Use the new function to get vessel data
    grouped_data = process_and_sort_samples_by_vessel(process_step_id, vessel_filter)

    if not grouped_data:
        return "⚠️ No data available to plot for this process step."

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

        # Sort by day for proper line plotting
        df_sorted = df.sort_values("day")

        # Drop NaN/None values for the selected variable
        df_sorted = df_sorted.dropna(subset=[selected_variable])

        if df_sorted.empty:
            print(f"⚠️ All values were NaN for {selected_variable} in Vessel {vessel_id}, skipping...")
            continue

        # Get vessel type for legend
        vessel_type = df_sorted['vessel_type'].iloc[0] if 'vessel_type' in df_sorted.columns else "Unknown"
        vessel_type_short = vessel_type.replace('_', ' ')
        icon = "🔬" if "BRX" in vessel_type else "🧫" if "SF" in vessel_type else "🧪"

        # Add trace for this vessel
        fig.add_trace(go.Scatter(
            x=df_sorted["day"],
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

    # Update layout to match vicell styling
    fig.update_layout(
        title={
            'text': f"{VARIABLES.get(selected_variable, selected_variable)} Over Time - {experiment_info}",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title="Process Day",
        yaxis_title=f"{VARIABLES[selected_variable]} ({UNITS.get(selected_variable, '')})",
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
