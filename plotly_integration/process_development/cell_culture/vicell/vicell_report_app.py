import dash
import numpy as np
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State, MATCH, dash_table
from django_plotly_dash import DjangoDash
import pandas as pd
from plotly_integration.models import ViCellData, ViCellReport
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

# Main layout with modals and stores
app.layout = html.Div(
    children=[
        # Stores for state management
        dcc.Store(id="selected-report", data=None),
        dcc.Store(id="embedded-mode", data=False),
        dcc.Store(id="url-params", data={}),
        dcc.Location(id="url", refresh=False),
        dcc.Interval(id="load-once", interval=1000, n_intervals=0, max_intervals=1),

        # Modal for Create Report iframe
        html.Div(
            id="create-report-modal",
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
                        "margin": "5% auto",
                        "width": "1300px",
                        "maxWidth": "90%",
                        "height": "80%",
                        "backgroundColor": "white",
                        "borderRadius": "10px",
                        "padding": "20px",
                        "boxShadow": "0 5px 15px rgba(0,0,0,0.3)"
                    },
                    children=[
                        html.Button(
                            "✕",
                            id="close-modal-btn",
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
                        html.H3("Create New ViCell Report", style={"marginBottom": "20px", "color": "#0056b3"}),
                        html.Iframe(
                            src="/plotly_integration/dash-app/app/ViCellCreateReportApp/",
                            style={
                                "width": "100%",
                                "height": "calc(100% - 60px)",
                                "border": "none"
                            }
                        )
                    ]
                )
            ]
        ),

        # Modal for Select Report
        html.Div(
            id="select-report-modal",
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
                            id="close-select-report-btn",
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
                        html.H3("Select ViCell Report", style={"marginBottom": "20px", "color": "#0056b3"}),
                        html.Div(
                            style={"flex": "1", "overflowY": "auto", "marginBottom": "20px"},
                            children=[
                                dash_table.DataTable(
                                    id="report-selection-table",
                                    columns=[
                                        {"name": "Report Name", "id": "report_name"},
                                        {"name": "Project ID", "id": "project_id"},
                                        {"name": "User ID", "id": "user_id"},
                                        {"name": "Date Created", "id": "date_created"},
                                        {"name": "Comments", "id": "comments"}
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
                            "Select Report",
                            id="confirm-report-selection",
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
                # Left side - Create Report button
                html.Div(
                    style={"display": "flex", "gap": "10px"},
                    children=[
                        html.Button(
                            "Create New Report",
                            id="create-report-btn",
                            style={
                                "backgroundColor": "#0056b3",
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
                            "Select Report",
                            id="change-report-btn",
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
                        )
                    ]
                ),
                # Right side - Current report display
                html.Div(
                    id="current-report-text",
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
                # Report dropdown (hidden when using modals)
                html.Div(
                    style={"display": "none"},
                    children=[
                        dcc.Dropdown(
                            id="report-dropdown",
                            placeholder="Select a report",
                            style={"width": "400px"}
                        )
                    ]
                ),

                # Tab content - Summary tab moved to the end
                dcc.Tabs(
                    id="variable-tabs",
                    value="viable_cells_per_ml",  # Default to first metric
                    children=[
                        *[dcc.Tab(label=label, value=var, style={"backgroundColor": "#f8f9fa"})
                          for var, label in VARIABLES.items()],
                        dcc.Tab(label="Summary", value="summary", style={"backgroundColor": "#f8f9fa"}),
                    ],
                    style={"marginTop": "20px", "marginBottom": "20px"}
                ),

                # Summary container
                html.Div(
                    id="summary-container",
                    style={"marginTop": "20px", "display": "block"},
                    children=[
                        html.H3("Report Summary", style={"marginBottom": "20px", "color": "#0047b3"}),
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
    report_id = None

    if "embedded" in params:
        embedded = params["embedded"][0].lower() in ["true", "1", "yes"]
        url_params["embedded"] = embedded

    if "report_id" in params:
        try:
            report_id = int(params["report_id"][0])
            url_params["report_id"] = report_id
        except:
            pass

    return url_params, embedded


# Update toolbar visibility based on embedded mode
@app.callback(
    [Output("create-report-btn", "style"),
     Output("change-report-btn", "style")],
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
        create_btn_style = {
            "backgroundColor": "#0056b3",
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

        return create_btn_style, select_btn_style


# Callback to show/hide Create Report modal
@app.callback(
    Output("create-report-modal", "style"),
    [Input("create-report-btn", "n_clicks"),
     Input("close-modal-btn", "n_clicks")],
    [State("create-report-modal", "style")],
    prevent_initial_call=True
)
def toggle_create_modal(open_clicks, close_clicks, current_style):
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_style

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "create-report-btn":
        return {**current_style, "display": "block"}
    elif button_id == "close-modal-btn":
        return {**current_style, "display": "none"}

    return current_style


# Callback to show/hide Select Report modal and populate reports
@app.callback(
    [Output("select-report-modal", "style"),
     Output("report-selection-table", "data"),
     Output("current-report-text", "children")],
    [Input("change-report-btn", "n_clicks"),
     Input("close-select-report-btn", "n_clicks"),
     Input("confirm-report-selection", "n_clicks"),
     Input("load-once", "n_intervals"),
     Input("url-params", "data")],
    [State("select-report-modal", "style"),
     State("report-selection-table", "selected_rows"),
     State("report-selection-table", "data"),
     State("embedded-mode", "data"),
     State("selected-report", "data")],
    prevent_initial_call=False
)
def toggle_select_modal(change_clicks, close_clicks, confirm_clicks, load_interval,
                        url_params, current_style, selected_rows, table_data,
                        embedded, current_report_id):
    ctx = dash.callback_context

    # Get trigger ID
    if not ctx.triggered:
        triggered_id = None
    else:
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Fetch reports for table
    reports = ViCellReport.objects.all().order_by("-date_created")
    reports_data = [
        {
            "id": r.id,
            "report_name": r.report_name,
            "project_id": r.project_id or "",
            "user_id": r.user_id or "",
            "date_created": r.date_created.strftime("%Y-%m-%d %H:%M:%S"),
            "comments": r.comments or ""
        }
        for r in reports
    ]

    # Determine current report text
    current_text = "No report selected"
    if current_report_id:
        report = next((r for r in reports_data if r["id"] == current_report_id), None)
        if report:
            current_text = f"Current Report: {report['report_name']}"

    # Handle modal visibility
    if triggered_id == "change-report-btn":
        return {**current_style, "display": "block"}, reports_data, current_text
    elif triggered_id == "close-select-report-btn":
        return {**current_style, "display": "none"}, reports_data, current_text
    elif triggered_id == "confirm-report-selection" and selected_rows:
        # Report will be selected by another callback
        return {**current_style, "display": "none"}, reports_data, current_text
    elif triggered_id == "load-once":
        # Initial load - check for URL params
        if not embedded and "report_id" not in url_params and not current_report_id:
            # Auto-open select modal if no report selected
            return {**current_style, "display": "block"}, reports_data, current_text

    return current_style, reports_data, current_text


# Update selected report from modal
@app.callback(
    [Output("selected-report", "data"),
     Output("report-dropdown", "value")],
    [Input("confirm-report-selection", "n_clicks"),
     Input("url-params", "data")],
    [State("report-selection-table", "selected_rows"),
     State("report-selection-table", "data")],
    prevent_initial_call=False
)
def update_selected_report(confirm_clicks, url_params, selected_rows, table_data):
    ctx = dash.callback_context

    if not ctx.triggered:
        return None, None

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "url-params" and "report_id" in url_params:
        # Load from URL
        return url_params["report_id"], url_params["report_id"]
    elif triggered_id == "confirm-report-selection" and selected_rows and table_data:
        # Load from selection
        selected_report = table_data[selected_rows[0]]
        return selected_report["id"], selected_report["id"]

    return None, None


# Populate Report Dropdown (keep existing functionality)
@app.callback(
    Output("report-dropdown", "options"),
    [Input("report-dropdown", "value")],
    [State("selected-report", "data")]
)
def populate_report_dropdown(dropdown_value, selected_report_id):
    reports = ViCellReport.objects.all().order_by("-date_created")

    if not reports:
        return []

    options = [
        {"label": f"{r.report_name} (Created: {r.date_created.strftime('%Y-%m-%d %H:%M:%S')})", "value": r.id}
        for r in reports
    ]

    return options


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


# Keep all existing callbacks from the original vicell_report_app.py below this line
# (process_and_sort_samples, update_reactor_number_dropdown, update_summary_table, update_graph, etc.)

def process_and_sort_samples(sample_names):
    """
    - Fetches parsed data from the ViCellData table instead of re-parsing.
    - Groups by `sample_id` and queries ViCellData to get data.
    - Returns a separate DataFrame for each unique `experiment`.
    """

    # Query `ViCellData` for multiple samples at once
    samples = ViCellData.objects.filter(sample_id__in=sample_names).values(
        "sample_id", "experiment", "day", "reactor_type", "reactor_number", "special",
        "date_time", "cell_count", "viable_cells", "total_cells_per_ml", "viable_cells_per_ml",
        "viability", "average_diameter", "average_viable_diameter", "average_circularity",
        "average_viable_circularity"
    )

    df = pd.DataFrame(list(samples))

    if df.empty:
        print("⚠️ No valid samples found.")
        return {}

    # Sort by reactor number, day, and special condition
    df_sorted = df.sort_values(by=["reactor_number", "day", "special"], ascending=[True, True, True])

    # Group by `reactor_number` to organize data properly
    sample_groups = df_sorted.groupby("reactor_number")["sample_id"].apply(list).to_dict()

    grouped_data = {}

    for reactor_number, result_names in sample_groups.items():
        print(f"🔍 Querying ViCellData for Reactor Number: {reactor_number}, Samples: {result_names}")

        # Fetch ViCellData for the grouped samples
        vicell_data = ViCellData.objects.filter(sample_id__in=result_names).values(
            "sample_id", "day", "date_time", "cell_count", "viable_cells", "total_cells_per_ml",
            "viable_cells_per_ml", "viability", "average_diameter", "average_viable_diameter",
            "average_circularity", "average_viable_circularity", "reactor_type"
        )

        vicell_df = pd.DataFrame(list(vicell_data))

        if not vicell_df.empty:
            grouped_data[reactor_number] = vicell_df
        else:
            print(f"⚠️ No matching data found for Reactor Number {reactor_number}")
            grouped_data[reactor_number] = pd.DataFrame(
                columns=["sample_id", "day", "date_time", "cell_count", "viable_cells",
                         "total_cells_per_ml", "viable_cells_per_ml", "viability", "average_diameter",
                         "average_viable_diameter", "average_circularity", "average_viable_circularity",
                         "reactor_type"]
            )

    return grouped_data


@app.callback(
    [Output("subset-dropdown", "options"),
     Output("subset-dropdown", "value")],
    [Input("selected-report", "data")]
)
def update_reactor_number_dropdown(selected_report_id):
    """Populate dropdown with available reactor numbers from the selected report."""
    if not selected_report_id:
        return [], None

    report = ViCellReport.objects.filter(id=selected_report_id).first()
    if not report or not report.selected_result_ids:
        return [], None

    sample_ids = [s.strip() for s in report.selected_result_ids.split(",") if s.strip()]

    # Query all distinct reactor numbers, ignoring NULL values
    reactors = list(
        ViCellData.objects.filter(id__in=sample_ids, reactor_number__isnull=False)
        .values_list("reactor_number", flat=True)
        .distinct()
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
     Input("selected-report", "data")]
)
def update_summary_table(selected_reactor, selected_report_id):
    """Populate table with data when a reactor number is selected from the selected report."""
    if not selected_report_id or not selected_reactor:
        print("⚠️ No reactor or report selected.")
        return []

    # Fetch the selected report
    report = ViCellReport.objects.filter(id=selected_report_id).first()
    if not report or not report.selected_result_ids:
        print("⚠️ Report not found or contains no selected results.")
        return []

    # Get sample IDs from report
    sample_ids = [s.strip() for s in report.selected_result_ids.split(",") if s.strip()]

    # Query ViCellData for the selected reactor
    vicell_data = ViCellData.objects.filter(
        id__in=sample_ids,
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
    [Input("selected-report", "data"),
     Input("variable-tabs", "value")],
    prevent_initial_call=True
)
def update_graph(selected_report_id, selected_variable):
    """
    Updates the graph based on the selected variable tab.
    Each graph plots different `reactor_number` groups over time using `day` as the x-axis.
    """
    if selected_variable is None:
        return "⚠️ No variable selected."
    if selected_variable == "summary":
        return None
    if not selected_report_id:
        return "⚠️ No report selected."

    report = ViCellReport.objects.filter(id=selected_report_id).first()
    if not report:
        return "⚠️ Report not found."

    if not report.selected_result_ids:
        return "⚠️ No selected result IDs found in this report."

    sample_ids = [s.strip() for s in report.selected_result_ids.split(",") if s.strip()]
    sample_names = list(ViCellData.objects.filter(id__in=sample_ids).values_list("sample_id", flat=True))

    if not sample_names:
        return "⚠️ No valid sample names found."

    # Use the existing process_and_sort_samples function
    grouped_data = process_and_sort_samples(sample_names)

    if not grouped_data:
        return "⚠️ No data available to plot."

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
            'text': f"{VARIABLES.get(selected_variable, selected_variable)} Over Time",
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
        margin=dict(l=80, r=150, t=100, b=80),
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
        margin=dict(l=80, r=80, t=100, b=80),
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
        margin=dict(l=80, r=150, t=100, b=80),
        autosize=True
    )

    return html.Div([
        dcc.Graph(
            figure=fig,
            style={"width": "100%", "height": "700px"},
            config={"displayModeBar": True, "responsive": True}
        )
    ], style={"width": "100%"})