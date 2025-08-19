import dash
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State, MATCH, dash_table
from django_plotly_dash import DjangoDash
import pandas as pd
from plotly_integration.models import NovaFlex2
import json
from datetime import datetime
import re
import plotly.express as px

# Initialize the Dash app
app = DjangoDash("NovaDataReportApp")

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

# Main layout with modals and stores
app.layout = html.Div(
    children=[
        # Stores for state management
        dcc.Store(id="selected-experiment", data=None),
        dcc.Store(id="embedded-mode", data=False),
        dcc.Store(id="url-params", data={}),
        dcc.Location(id="url", refresh=False),
        dcc.Interval(id="load-once", interval=1000, n_intervals=0, max_intervals=1),

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
                        )
                    ]
                ),
                # Right side - Current report display
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
                    value="summary",
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

    # Fetch experiments for table - get unique experiments from NovaFlex2
    experiments_query = NovaFlex2.objects.filter(
        experiment__isnull=False
    ).exclude(experiment="").values("experiment").distinct().order_by("-experiment")
    
    experiments_data = [{"experiment": exp_obj["experiment"]} for exp_obj in experiments_query]

    # Determine current experiment text
    current_text = "No experiment selected"
    if current_experiment:
        current_text = f"Current Experiment: {current_experiment}"

    # Handle modal visibility
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


def process_and_sort_samples_by_experiment(experiment):
    """
    Fetches data for a specific experiment.
    Groups by reactor_number for plotting.
    """
    # Query NovaFlex2 for the experiment
    samples = NovaFlex2.objects.filter(
        experiment=experiment
    ).values(
        "sample_id", "experiment", "day", "reactor_type", "reactor_number", "special",
        "date_time", "gln", "glu", "gluc", "lac", "nh4", "pH", "po2", "pco2", "osm"
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
            # Add the new column `do` (Dissolved Oxygen) as `po2 / 1.6`
            reactor_df["do"] = reactor_df["po2"] / 1.6
            grouped_data[reactor_number] = reactor_df
        else:
            print(f"⚠️ No matching data found for Reactor Number {reactor_number}")

    return grouped_data


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
    Output("variable-graph-container", "children"),
    [Input("selected-experiment", "data"),
     Input("variable-tabs", "value")],
    prevent_initial_call=True
)
def update_graph(selected_experiment, selected_variable):
    """
    Updates the graph based on the selected variable tab.
    Each graph plots different `reactor_number` groups over time using `day` as the x-axis.
    """
    if selected_variable is None:
        return "⚠️ No variable selected."
    if selected_variable == 'summary':
        return None
    if not selected_experiment:
        return "⚠️ No experiment selected."

    # Use the new function to get experiment data
    sorted_groups = process_and_sort_samples_by_experiment(selected_experiment)

    if not sorted_groups:
        return "⚠️ No data available to plot for this experiment."

    # Create simple plot for standard variables
    fig = go.Figure()

    # Color palette for different reactor numbers
    colors = px.colors.qualitative.Set1

    for idx, (reactor_number, df) in enumerate(sorted_groups.items()):
        if df.empty or selected_variable not in df.columns:
            continue

        # Sort by day for proper line plotting
        df_sorted = df.sort_values("day")
        
        # Drop NaN/None values for the selected variable
        df_sorted = df_sorted.dropna(subset=[selected_variable])

        if df_sorted.empty:
            print(f"⚠️ All values were NaN for {selected_variable} in Reactor {reactor_number}, skipping...")
            continue

        # Get the unique reactor type for this group
        reactor_type = df_sorted["reactor_type"].iloc[0] if "reactor_type" in df_sorted.columns else "Unknown"

        # Add trace for this reactor
        fig.add_trace(go.Scatter(
            x=df_sorted["day"],
            y=df_sorted[selected_variable],
            mode="lines+markers",
            name=f"{reactor_type} {reactor_number}",
            line=dict(color=colors[idx % len(colors)], width=3),
            marker=dict(size=10),
            hovertemplate=f"{reactor_type} {reactor_number}<br>" +
                          "Day: %{x}<br>" +
                          f"{VARIABLES.get(selected_variable, selected_variable)}: %{{y:.2f}}<br>" +
                          "<extra></extra>"
        ))

    # Update layout to match vicell styling
    fig.update_layout(
        title={
            'text': f"{VARIABLES.get(selected_variable, selected_variable)} Over Time - {selected_experiment}",
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




@app.callback(
    [Output("subset-dropdown", "options"),
     Output("subset-dropdown", "value")],
    [Input("selected-experiment", "data")]
)
def update_reactor_number_dropdown(selected_experiment):
    """Populate dropdown with available reactor numbers from the selected experiment."""
    if not selected_experiment:
        return [], None

    # Query all distinct reactor numbers for this experiment
    reactors = list(
        NovaFlex2.objects.filter(
            experiment=selected_experiment,
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

    # Query NovaFlex2 for the selected reactor and experiment
    nova_data = NovaFlex2.objects.filter(
        experiment=selected_experiment,
        reactor_number=selected_reactor
    ).order_by("day", "special")

    # Convert to list of dictionaries for DataTable
    data = []
    for record in nova_data:
        row = {
            "date_time": record.date_time.strftime("%m/%d/%Y %I:%M:%S %p") if record.date_time else "",
            "sample_id": record.sample_id,
            "day": record.day,
            "gln": record.gln,
            "glu": record.glu,
            "gluc": record.gluc,
            "lac": record.lac,
            "nh4": record.nh4,
            "pH": record.pH,
            "po2": record.po2,
            "do": round(record.po2 / 1.6, 1) if record.po2 else None,
            "pco2": record.pco2,
            "osm": record.osm,
        }
        data.append(row)

    return data
