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
app = DjangoDash("CLDViCellApp", external_stylesheets=[dbc.themes.BOOTSTRAP])

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
        dcc.Store(id="sample-range", data={"start": None, "end": None}),
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

        # Modal for Select Sample Range
        dbc.Modal([
            dbc.ModalHeader(
                dbc.ModalTitle([html.I(className="bi bi-filter me-2"), "Select Sample ID Range"]),
                close_button=True
            ),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Start Sample ID (FB####)", className="fw-bold"),
                        dbc.Input(
                            id="start-sample-input",
                            type="number",
                            placeholder="e.g., 1001",
                            min=1,
                            className="mb-3"
                        )
                    ], md=6),
                    dbc.Col([
                        dbc.Label("End Sample ID (FB####)", className="fw-bold"),
                        dbc.Input(
                            id="end-sample-input",
                            type="number",
                            placeholder="e.g., 1050",
                            min=1,
                            className="mb-3"
                        )
                    ], md=6)
                ]),
                html.Div(id="sample-range-preview", className="mt-3")
            ], style={"minHeight": "200px"}),
            dbc.ModalFooter([
                dbc.Button(
                    [html.I(className="bi bi-check-lg me-2"), "Apply Range"],
                    id="confirm-sample-range",
                    color="primary",
                    size="lg"
                )
            ])
        ], id="select-experiment-modal", size="lg", is_open=False),

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
                                [html.I(className="bi bi-filter me-2"), "Select Sample Range"],
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
                        dbc.Label("Day Filter", html_for="day-filter-dropdown", className="fw-bold"),
                        dcc.Dropdown(
                            id="day-filter-dropdown",
                            placeholder="All Days",
                            multi=True,
                            className="mb-2"
                        )
                    ], md=12)
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


# Callback to show/hide Select Sample Range modal
@app.callback(
    [Output("select-experiment-modal", "is_open"),
     Output("current-experiment-text", "children")],
    [Input("change-experiment-btn", "n_clicks"),
     Input("confirm-sample-range", "n_clicks")],
    [State("select-experiment-modal", "is_open"),
     State("sample-range", "data")],
    prevent_initial_call=False
)
def toggle_select_modal(change_clicks, confirm_clicks, is_open, sample_range):
    ctx = dash.callback_context

    # Get trigger ID
    if not ctx.triggered:
        triggered_id = None
    else:
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Determine current sample range text
    if sample_range and sample_range.get("start") and sample_range.get("end"):
        current_text = dbc.Badge(
            f"📊 FB{sample_range['start']:04d} - FB{sample_range['end']:04d}",
            color="info",
            className="fs-6 px-3 py-2"
        )
    else:
        current_text = dbc.Badge(
            "No sample range selected",
            color="secondary",
            className="fs-6 px-3 py-2"
        )

    # Handle modal visibility
    if triggered_id == "change-experiment-btn":
        return not is_open, current_text
    elif triggered_id == "confirm-sample-range":
        return False, current_text

    return is_open, current_text


# Update sample range from modal
@app.callback(
    Output("sample-range", "data"),
    [Input("confirm-sample-range", "n_clicks")],
    [State("start-sample-input", "value"),
     State("end-sample-input", "value")],
    prevent_initial_call=True
)
def update_sample_range(confirm_clicks, start_sample, end_sample):
    if not confirm_clicks or start_sample is None or end_sample is None:
        return {"start": None, "end": None}

    return {"start": int(start_sample), "end": int(end_sample)}


# Populate day filter dropdown based on selected sample range
@app.callback(
    Output("day-filter-dropdown", "options"),
    [Input("sample-range", "data")],
    prevent_initial_call=False
)
def update_day_filter(sample_range):
    """Populate dropdown with available days from the sample range."""
    if not sample_range or not sample_range.get("start") or not sample_range.get("end"):
        return []

    try:
        # Query ViCellData for samples in the range
        from django.db.models import Q

        start_id = sample_range["start"]
        end_id = sample_range["end"]

        # Build query to match D##FB#### pattern where #### is in range
        query = Q()
        for sample_num in range(start_id, end_id + 1):
            pattern = f"FB{sample_num:04d}"
            query |= Q(sample_id__icontains=pattern)

        samples = ViCellData.objects.filter(query).values_list('sample_id', flat=True).distinct()

        # Extract unique days from sample IDs
        days = set()
        for sample_id in samples:
            # Extract day from D##FB#### pattern
            match = re.search(r'D(\d{1,2})FB\d{4}', str(sample_id), re.IGNORECASE)
            if match:
                day = int(match.group(1))
                days.add(day)

        # Create dropdown options
        options = [{"label": f"Day {day}", "value": day} for day in sorted(days)]
        return options

    except Exception as e:
        print(f"Error updating day filter: {e}")
        return []


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


def extract_day_and_sample_id(sample_id):
    """
    Extract day and FB sample ID from D##FB#### pattern.

    Args:
        sample_id: String with format D##FB#### (e.g., D03FB1234)

    Returns:
        Tuple of (day, fb_id) or (None, None) if pattern doesn't match
    """
    if not sample_id:
        return None, None

    # Match D##FB#### pattern (D can be 1-2 digits, FB is 4 digits)
    match = re.search(r'D(\d{1,2})FB(\d{4})', str(sample_id), re.IGNORECASE)
    if match:
        day = int(match.group(1))
        fb_id = int(match.group(2))
        return day, fb_id

    return None, None


def process_and_sort_samples_by_fb_id(sample_range, day_filter=None):
    """
    Fetches ViCell data for samples within the specified FB#### range.
    Groups by FB sample ID (each sample tracked across multiple days).

    Args:
        sample_range: Dict with 'start' and 'end' FB sample IDs
        day_filter: Optional list of days to filter (if None, shows all)

    Returns:
        Dictionary with fb_id as keys and DataFrames as values
    """
    if not sample_range or not sample_range.get("start") or not sample_range.get("end"):
        print("⚠️ No sample range specified")
        return {}

    try:
        start_id = sample_range["start"]
        end_id = sample_range["end"]

        # Build query to match D##FB#### pattern where #### is in range
        from django.db.models import Q
        query = Q()
        for sample_num in range(start_id, end_id + 1):
            pattern = f"FB{sample_num:04d}"
            query |= Q(sample_id__icontains=pattern)

        print(f"🔍 Querying ViCellData for sample range FB{start_id:04d} to FB{end_id:04d}")

        samples = ViCellData.objects.filter(query).values(
            "sample_id", "experiment", "day", "reactor_type", "reactor_number", "special",
            "date_time", "cell_count", "viable_cells", "total_cells_per_ml", "viable_cells_per_ml",
            "viability", "average_diameter", "average_viable_diameter", "average_circularity",
            "average_viable_circularity"
        )

        df = pd.DataFrame(list(samples))

        print(f"✓ Found {len(df)} ViCell records")

        if df.empty:
            print(f"⚠️ No ViCell data found for sample range")
            return {}

        # Extract day and FB ID from sample_id
        df[['extracted_day', 'fb_id']] = df['sample_id'].apply(
            lambda x: pd.Series(extract_day_and_sample_id(x))
        )

        # Filter out samples that don't match the pattern
        df = df[df['extracted_day'].notna()]

        if df.empty:
            print(f"⚠️ No samples matched D##FB#### pattern")
            return {}

        # Convert date_time to datetime
        df['date_time'] = pd.to_datetime(df['date_time'])

        # Apply day filter if provided
        if day_filter:
            df = df[df['extracted_day'].isin(day_filter)]
            print(f"✓ After day filter: {len(df)} records")

        # Sort by fb_id and day
        df_sorted = df.sort_values(by=["fb_id", "extracted_day"], ascending=[True, True])

        # Group by FB sample ID (so we can track each sample across days)
        grouped_data = {}

        for fb_id in sorted(df_sorted["fb_id"].dropna().unique()):
            fb_df = df_sorted[df_sorted["fb_id"] == fb_id].copy()
            if not fb_df.empty:
                grouped_data[int(fb_id)] = fb_df
                days = fb_df['extracted_day'].unique()
                print(f"✓ FB{int(fb_id):04d}: {len(fb_df)} records across days {sorted(days)}")

        return grouped_data

    except Exception as e:
        print(f"Error processing samples: {e}")
        return {}


@app.callback(
    [Output("subset-dropdown", "options"),
     Output("subset-dropdown", "value")],
    [Input("sample-range", "data"),
     Input("day-filter-dropdown", "value")]
)
def update_fb_dropdown(sample_range, day_filter):
    """Populate dropdown with available FB samples from the sample range."""
    if not sample_range or not sample_range.get("start"):
        return [], None

    # Get grouped data for this sample range
    grouped_data = process_and_sort_samples_by_fb_id(sample_range, day_filter)

    if not grouped_data:
        print("⚠️ No FB samples with ViCell data found!")
        return [], None

    # Create dropdown options from FB samples that have data
    fb_ids = list(grouped_data.keys())
    options = []

    for fb_id in sorted(fb_ids):
        num_measurements = len(grouped_data[fb_id])
        days = sorted(grouped_data[fb_id]['extracted_day'].unique())
        day_range = f"D{min(days)}-D{max(days)}" if len(days) > 1 else f"D{days[0]}"
        options.append({
            "label": f"🧪 FB{fb_id:04d} ({day_range}, {num_measurements} points)",
            "value": fb_id
        })

    return options, (fb_ids[0] if fb_ids else None)


@app.callback(
    Output("subset-table", "data"),
    [Input("subset-dropdown", "value"),
     Input("sample-range", "data"),
     Input("day-filter-dropdown", "value")]
)
def update_summary_table(selected_fb_id, sample_range, day_filter):
    """Populate table with data when an FB sample is selected."""
    if not sample_range or selected_fb_id is None:
        print("⚠️ No FB sample or sample range selected.")
        return []

    # Get grouped data for this sample range
    grouped_data = process_and_sort_samples_by_fb_id(sample_range, day_filter)

    if selected_fb_id not in grouped_data:
        print(f"⚠️ No data found for FB{selected_fb_id:04d}")
        return []

    fb_df = grouped_data[selected_fb_id]

    # Convert to list of dictionaries for DataTable
    # Get Pacific timezone for display
    pacific_tz = pytz.timezone('US/Pacific')

    data = []
    for _, record in fb_df.iterrows():
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
            "day": int(record.get("extracted_day", 0)) if pd.notna(record.get("extracted_day")) else 0,
            "process_time_hours": 0,  # Not applicable for this grouping
            "total_cells_per_ml": record.get("total_cells_per_ml"),
            "viable_cells_per_ml": record.get("viable_cells_per_ml"),
            "viability": record.get("viability"),
            "average_viable_diameter": record.get("average_viable_diameter"),
        }
        data.append(row)

    return data


@app.callback(
    Output("variable-graph-container", "children"),
    [Input("sample-range", "data"),
     Input("day-filter-dropdown", "value"),
     Input("variable-tabs", "active_tab")],
    prevent_initial_call=True
)
def update_graph(sample_range, day_filter, selected_variable):
    """
    Updates the graph based on the selected variable tab.
    X-axis: Day (D##)
    Y-axis: Selected variable
    Different lines: One per FB sample ID
    """
    if selected_variable is None:
        return "⚠️ No variable selected."
    if selected_variable in ["summary"]:
        return None
    if not sample_range or not sample_range.get("start"):
        return "⚠️ No sample range selected."

    # Get data grouped by FB sample ID
    grouped_data = process_and_sort_samples_by_fb_id(sample_range, day_filter)

    if not grouped_data:
        return "⚠️ No data available to plot for this sample range."

    # Special handling for growth rate and doubling time analysis
    if selected_variable == "growth_rate":
        return create_growth_rate_analysis(grouped_data)
    elif selected_variable == "doubling_time":
        return create_doubling_time_analysis(grouped_data)

    # Create simple plot for standard variables
    fig = go.Figure()

    # Color palette for different FB samples
    colors = px.colors.qualitative.Plotly  # Use larger color palette

    # Get sample range info for title
    range_info = f"FB{sample_range['start']:04d} - FB{sample_range['end']:04d}"

    for idx, (fb_id, df) in enumerate(sorted(grouped_data.items())):
        if df.empty or selected_variable not in df.columns:
            continue

        # Sort by day for proper line plotting
        df_sorted = df.sort_values("extracted_day")

        # Drop NaN values for the selected variable
        df_sorted = df_sorted.dropna(subset=[selected_variable])

        if df_sorted.empty:
            continue

        # Add trace for this FB sample
        fig.add_trace(go.Scatter(
            x=df_sorted["extracted_day"],  # Day on X-axis
            y=df_sorted[selected_variable],
            mode="lines+markers",
            name=f"FB{fb_id:04d}",
            line=dict(color=colors[idx % len(colors)], width=2),
            marker=dict(size=8),
            hovertemplate=f"FB{fb_id:04d}<br>" +
                          "Day: %{x}<br>" +
                          f"{VARIABLES.get(selected_variable, selected_variable)}: %{{y:.2f}}<br>" +
                          "<extra></extra>"
        ))

    # Update layout
    fig.update_layout(
        title={
            'text': f"{VARIABLES.get(selected_variable, selected_variable)} Over Time - Samples {range_info}",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title="Day",
        yaxis_title=VARIABLES.get(selected_variable, selected_variable),
        height=700,
        width=None,
        hovermode="closest",
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
            borderwidth=1,
            title="Sample ID"
        ),
        font=dict(family="Arial, sans-serif", size=14),
        margin=dict(l=120, r=220, t=140, b=120),
        autosize=True
    )

    # Update axes styling
    fig.update_xaxes(
        gridcolor='rgba(128, 128, 128, 0.2)',
        showgrid=True,
        zeroline=False,
        dtick=1  # Show every day on x-axis
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
    """Create specialized growth rate analysis plots - grouped by FB sample ID"""
    from plotly.subplots import make_subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Growth Curves (Log Scale)", "Specific Growth Rate",
                        "Growth Rate Distribution", "Exponential Phase Detection"),
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )

    colors = px.colors.qualitative.Plotly

    for idx, (fb_id, df) in enumerate(grouped_data.items()):
        if df.empty or "viable_cells_per_ml" not in df.columns:
            continue

        df_sorted = df.sort_values("extracted_day")
        viable_cells = df_sorted["viable_cells_per_ml"].values
        days = df_sorted["extracted_day"].values

        # Skip if not enough data
        if len(viable_cells) < 3:
            continue

        # Calculate growth rates
        log_cells = np.log(viable_cells)
        growth_rates = np.diff(log_cells) / np.diff(days)

        fb_label = f"FB{fb_id:04d}"

        # 1. Growth curves (log scale)
        fig.add_trace(go.Scatter(
            x=days,
            y=viable_cells,
            mode="lines+markers",
            name=fb_label,
            line=dict(color=colors[idx % len(colors)], width=2),
            marker=dict(size=8)
        ), row=1, col=1)

        # 2. Specific growth rate over time
        fig.add_trace(go.Scatter(
            x=days[1:],
            y=growth_rates,
            mode="lines+markers",
            name=f"μ {fb_label}",
            line=dict(color=colors[idx % len(colors)], width=2),
            marker=dict(size=8)
        ), row=1, col=2)

        # 3. Growth rate distribution
        fig.add_trace(go.Histogram(
            x=growth_rates,
            name=fb_label,
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
                name=f"MA {fb_label}",
                line=dict(color=colors[idx % len(colors)], width=3)
            ), row=2, col=2)

    # Update layouts
    fig.update_xaxes(title_text="Day", row=1, col=1)
    fig.update_xaxes(title_text="Day", row=1, col=2)
    fig.update_xaxes(title_text="Growth Rate (1/day)", row=2, col=1)
    fig.update_xaxes(title_text="Day", row=2, col=2)

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
    """Create doubling time analysis - grouped by FB sample ID"""
    fig = go.Figure()

    colors = px.colors.qualitative.Plotly

    for idx, (fb_id, df) in enumerate(grouped_data.items()):
        if df.empty or "viable_cells_per_ml" not in df.columns:
            continue

        df_sorted = df.sort_values("extracted_day")
        viable_cells = df_sorted["viable_cells_per_ml"].values
        days = df_sorted["extracted_day"].values

        if len(viable_cells) < 2:
            continue

        # Calculate doubling times
        doubling_times = []
        doubling_days = []

        for i in range(1, len(viable_cells)):
            if viable_cells[i] > viable_cells[i - 1] and viable_cells[i - 1] > 0:
                # Calculate doubling time using: DT = ((t2-t1)*ln(2))/(ln(N2)-ln(N1))
                t1 = days[i - 1]
                t2 = days[i]
                N1 = viable_cells[i - 1]
                N2 = viable_cells[i]

                # DT in days
                dt_days = ((t2 - t1) * np.log(2)) / (np.log(N2) - np.log(N1))
                # Convert to hours
                dt_hours = dt_days * 24

                if dt_hours > 0:
                    doubling_times.append(dt_hours)
                    doubling_days.append((days[i] + days[i - 1]) / 2)

        if doubling_times:
            fb_label = f"FB{fb_id:04d}"

            fig.add_trace(go.Scatter(
                x=doubling_days,
                y=doubling_times,
                mode="lines+markers",
                name=fb_label,
                line=dict(color=colors[idx % len(colors)], width=3),
                marker=dict(size=10),
                hovertemplate=f"{fb_label}<br>" +
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
        xaxis_title="Day",
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
