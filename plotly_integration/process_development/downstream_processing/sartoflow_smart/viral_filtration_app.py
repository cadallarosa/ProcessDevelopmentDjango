import pandas as pd
import plotly.graph_objects as go
from django_plotly_dash import DjangoDash
from dash import dcc, html, Input, Output, dash_table
# from paramiko.agent import value

from plotly_integration.models import VFMetadata, VFTimeSeriesData
import numpy as np
from dash.dependencies import ALL, State
import dash

# Create Dash App
app = DjangoDash("ViralFiltrationApp")

# Define unit step options
unit_step_options = [
    {"label": "Water Flush", "value": 1},
    {"label": "Buffer Flush", "value": 2},
    {"label": "Product Filtration", "value": 3},
]

# Unit step name mapping
unit_step_names = {
    1: "Water Flush",
    2: "Buffer Flush",
    3: "Product Filtration"
}
# Query the database for unique experiment names and result IDs
experiments = VFMetadata.objects.values("result_id", "experiment_name").distinct().order_by("-result_id")

# Define selectable columns (including derived metrics)
selectable_columns = [
    {"label": "Pressure", "value": "pir2700"},
    {"label": "Filtrate Weight", "value": "wir2700"},
    {"label": "L/m²/hr", "value": "L/m²/hr"},
    {"label": "g/m²/hr", "value": "g/m²/hr"},
    # {"label": "mL/m²/hr", "value": "mL/m²/hr"},
    # {"label": "mL/min", "value": "mL_min"},
    {"label": "Flux Decay", "value": "flux_decay"}
]

# Define styles for the app
app_style = {
    "fontFamily": "Arial, sans-serif",
    "padding": "20px",
    "backgroundColor": "#f8f9fa",
}

card_style = {
    "padding": "15px",
    "borderRadius": "8px",
    "boxShadow": "0px 0px 10px rgba(0, 0, 0, 0.1)",
    "backgroundColor": "white",
}

# Define styling
input_style = {
    "width": "100%", 
    "padding": "12px", 
    "borderRadius": "8px", 
    "border": "1px solid #ddd",
    "fontSize": "14px",
    "fontFamily": "system-ui, -apple-system, sans-serif",
    "boxShadow": "0 1px 3px rgba(0,0,0,0.1)",
    "transition": "border-color 0.3s, box-shadow 0.3s"
}
readonly_style = input_style.copy()
readonly_style["backgroundColor"] = "#f8f9fa"
readonly_style["color"] = "#6c757d"

label_style = {
    "fontWeight": "600",
    "fontSize": "14px",
    "color": "#495057",
    "marginBottom": "8px",
    "display": "block"
}

field_container_style = {
    "marginBottom": "20px",
    "padding": "15px",
    "backgroundColor": "#ffffff",
    "borderRadius": "8px",
    "border": "1px solid #e9ecef",
    "boxShadow": "0 1px 3px rgba(0,0,0,0.05)"
}

# Dash Layout
app.layout = html.Div(
    style=app_style,
    children=[
        # Top bar with select button
        html.Div(
            style={"display": "flex", "justifyContent": "flex-start", "marginBottom": "10px"},
            children=[
                html.Button(
                    "Select Experiment",
                    id="select-button",
                    style={
                        "backgroundColor": "#007bff",
                        "color": "white",
                        "border": "none",
                        "padding": "10px 20px",
                        "borderRadius": "5px",
                        "cursor": "pointer",
                        "fontSize": "14px"
                    }
                )
            ]
        ),

        # Selected experiment info
        html.Div(
            style=card_style,
            children=[
                html.Div(id="selected-experiment-info", 
                        children="No experiment selected. Click 'Select Experiment' to choose one.",
                        style={"marginBottom": "10px", "fontStyle": "italic", "color": "#666"}),
                
                html.Label("Select Unit Step:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="unit-step-dropdown",
                    options=unit_step_options,
                    placeholder="Select unit step...",
                    style={"marginBottom": "10px"},
                ),
                # Water Flush Flux Input
                html.Label("Water Flush Flux (L/m²/hr):", style={"fontWeight": "bold"}),
                dcc.Input(
                    id="water-flush-flux",
                    type="number",
                    placeholder="Enter Water Flush Flux",
                    style=input_style,
                ),
            ]
        ),
        html.Div([  # Main content container
            dcc.Tabs(id="main-tabs", value="tab-1", children=[
                # 🔹 Tab 1: Sample Analysis
                dcc.Tab(label="Viral Filtration Plot", value="tab-1", children=[
                    html.Div(
                        style={
                            **card_style, 
                            "display": "flex", 
                            "justifyContent": "space-between",
                            "alignItems": "flex-start",
                            "flexGrow": 1,
                            "gap": "20px",
                            "minHeight": "80vh"
                        },
                        children=[
                            # Left side: Graph
                            html.Div(
                                style={"flex": "2"},  # Allows the graph to take more space
                                children=[
                                    html.H3("Time Series Data", style={"color": "#0047b3"}),
                                    dcc.Graph(id="time-series-graph", config={"autosizable": "True","editable": True, "edits": {"titleText": True}}),

                                    # Display Overall LMH below the graph
                                    html.Div(
                                        children=[
                                            html.Label("Overall LMH:", style={"fontWeight": "bold"}),
                                            html.Span(id="overall-lmh-output",
                                                      style={"marginLeft": "10px", "color": "#d9534f",
                                                             "fontSize": "16px"})
                                        ],
                                        style={"marginTop": "15px", "textAlign": "left"}
                                    ),
                                ],
                            ),

                            # Right side: Controls
                            html.Div(
                                style={
                                    "flex": "1",  # Smaller width for the controls
                                    "display": "flex",
                                    "flexDirection": "column",
                                    "alignItems": "flex-start",
                                    "paddingLeft": "20px",  # Space between graph and controls
                                    "maxWidth": "300px",  # Prevents the control panel from becoming too wide
                                },
                                children=[
                                    html.Label("Select Data to Plot:", style={"fontWeight": "bold"}),
                                    dcc.Dropdown(
                                        id="data-selection",
                                        options=selectable_columns,
                                        value=["wir2700", "L/m²/hr"],
                                        multi=True,
                                        placeholder="Choose data to plot...",
                                        style={"marginBottom": "10px", "width": "100%"},
                                    ),

                                    html.Label("Select X Axis:", style={"fontWeight": "bold"}),
                                    dcc.Dropdown(
                                        id="xaxis-selection",
                                        options=[
                                            {"label": "Process Time", "value": "process_time"},
                                            {"label": "g/m²", "value": "g/m²"},
                                        ],
                                        value="process_time",
                                        multi=False,
                                        placeholder="Choose data to plot...",
                                        style={"marginBottom": "10px", "width": "100%"},
                                    ),

                                    html.Label("Smoothing (Seconds):", style={"fontWeight": "bold"}),
                                    dcc.Input(
                                        id="smoothing-input",
                                        type="number",
                                        min=10,
                                        step=1,
                                        placeholder="Min 10 sec",
                                        value=60,
                                        style={**input_style, "width": "100%", "marginBottom": "10px"},
                                    ),

                                    html.Label("Y-Min:", style={"fontWeight": "bold"}),
                                    dcc.Input(
                                        id="y-min-input",
                                        type="number",
                                        placeholder="Enter Y-min",
                                        value=0,
                                        style={"width": "100%", "marginBottom": "10px"},
                                    ),

                                    html.Label("Y-Max:", style={"fontWeight": "bold"}),
                                    dcc.Input(
                                        id="y-max-input",
                                        type="number",
                                        value=75,
                                        placeholder="Enter Y-max",
                                        style={"width": "100%"},
                                    ),
                                ],
                            ),
                        ],
                    ),
                ]),
                # 🔹 Tab 2: Experiment Information
                dcc.Tab(label="Experiment Information", value="tab-2", children=[
                    html.Div(
                        style={
                            **card_style,
                            "maxWidth": "1200px",
                            "margin": "0 auto",
                            "padding": "30px"
                        },
                        children=[
                            html.H3(
                                "Experiment Metadata", 
                                style={
                                    "color": "#0047b3",
                                    "textAlign": "center",
                                    "marginBottom": "30px",
                                    "fontSize": "28px",
                                    "fontWeight": "600"
                                }
                            ),
                            html.Div(
                                id="metadata-fields",
                                style={
                                    "display": "grid",
                                    "gridTemplateColumns": "repeat(auto-fit, minmax(300px, 1fr))",
                                    "gap": "20px",
                                    "marginBottom": "30px"
                                }
                            ),
                            html.Div(
                                style={"textAlign": "center"},
                                children=[
                                    html.Button(
                                        "Update Experiment", 
                                        id="update-button", 
                                        n_clicks=0,
                                        style={
                                            "backgroundColor": "#28a745",
                                            "color": "white",
                                            "border": "none",
                                            "padding": "12px 30px",
                                            "borderRadius": "8px",
                                            "fontSize": "16px",
                                            "fontWeight": "600",
                                            "cursor": "pointer",
                                            "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                                            "transition": "background-color 0.3s"
                                        }
                                    ),
                                    html.Div(
                                        id="update-status", 
                                        style={
                                            "marginTop": "15px", 
                                            "color": "green",
                                            "fontSize": "16px",
                                            "fontWeight": "500"
                                        }
                                    ),
                                ]
                            )
                        ],
                    ),
                ]),
            ])
        ]),
        
        # Modal for import experiment
        html.Div(
            id="import-modal",
            style={
                "display": "none",
                "position": "fixed",
                "zIndex": 1000,
                "left": 0,
                "top": 0,
                "width": "100%",
                "height": "100%",
                "backgroundColor": "rgba(0,0,0,0.5)"
            },
            children=[
                html.Div(
                    style={
                        "position": "relative",
                        "margin": "1% auto",
                        "width": "98%",
                        "height": "95%",
                        "backgroundColor": "white",
                        "borderRadius": "10px",
                        "padding": "10px"
                    },
                    children=[
                        html.Button(
                            "×",
                            id="close-modal",
                            style={
                                "position": "absolute",
                                "top": "10px",
                                "right": "15px",
                                "backgroundColor": "transparent",
                                "border": "none",
                                "fontSize": "24px",
                                "cursor": "pointer",
                                "color": "#999"
                            }
                        ),
                        html.H3("Select or Import Experiment", 
                               style={"marginBottom": "10px", "color": "#0047b3"}),
                        dcc.Tabs(
                            id="modal-tabs",
                            value="select-tab",
                            children=[
                                dcc.Tab(label="Select Existing", value="select-tab", 
                                       style={"fontSize": "16px"}, children=[
                                    html.Div(
                                        style={"padding": "10px"},
                                        children=[
                                            dash_table.DataTable(
                                                id="experiments-table",
                                                columns=[
                                                    {"name": "Molecule Name", "id": "molecule_name"},
                                                    {"name": "Experiment Name", "id": "experiment_name"},
                                                    {"name": "Yield %", "id": "yield_percentage", "type": "numeric", "format": {"specifier": ".1f"}},
                                                    {"name": "Created At", "id": "created_at", "type": "datetime"}
                                                ],
                                                data=[],
                                                style_table={
                                                    "overflowX": "auto", 
                                                    "height": "75vh", 
                                                    "overflowY": "auto",
                                                    "borderRadius": "5px"
                                                },
                                                style_cell={
                                                    "textAlign": "center", 
                                                    "padding": "12px", 
                                                    "fontSize": "14px",
                                                    "fontFamily": "system-ui, -apple-system, sans-serif"
                                                },
                                                style_header={
                                                    "backgroundColor": "#f8f9fa", 
                                                    "fontWeight": "600", 
                                                    "borderBottom": "2px solid #dee2e6"
                                                },
                                                style_data={
                                                    "borderBottom": "1px solid #dee2e6"
                                                },
                                                style_data_conditional=[
                                                    {
                                                        'if': {'row_index': 'odd'},
                                                        'backgroundColor': '#f8f9fa'
                                                    }
                                                ],
                                                row_selectable="single",
                                                selected_rows=[],
                                                filter_action="native",
                                                sort_action="native",
                                                page_action="native",
                                                page_size=15,
                                                fixed_rows={'headers': True}
                                            ),
                                            html.Div(
                                                style={"marginTop": "10px", "display": "flex", "justifyContent": "flex-end"},
                                                children=[
                                                    html.Button("Select", id="select-experiment-btn", 
                                                              style={"backgroundColor": "#28a745", "color": "white", 
                                                                     "border": "none", "padding": "8px 20px", 
                                                                     "borderRadius": "4px", "cursor": "pointer"})
                                                ]
                                            )
                                        ]
                                    )
                                ]),
                                dcc.Tab(label="Import New", value="import-tab", 
                                       style={"fontSize": "16px"}, children=[
                                    html.Div(
                                        style={"padding": "10px"},
                                        children=[
                                            html.Iframe(
                                                src="/plotly_integration/dash-app/app/ViralFiltrationExperimentImport/",
                                                style={
                                                    "width": "100%",
                                                    "height": "75vh",
                                                    "border": "none"
                                                }
                                            )
                                        ]
                                    )
                                ])
                            ],
                            colors={"border": "white", "primary": "darkblue", "background": "light-gray"}
                        )
                    ]
                )
            ]
        ),
        
        # Store for selected experiment
        dcc.Store(id='selected-experiment-store', data=None),
    ])


@app.callback(
    Output("experiments-table", "data"),
    Input("import-modal", "style")
)
def populate_experiments_table(modal_style):
    if modal_style and modal_style.get("display") == "block":
        experiments = VFMetadata.objects.all().order_by("-created_at")
        data = []
        for exp in experiments:
            data.append({
                "result_id": exp.result_id,
                "molecule_name": exp.molecule_name or "",
                "experiment_name": exp.experiment_name or "",
                "yield_percentage": exp.yield_percentage or 0,
                "created_at": exp.created_at.strftime("%Y-%m-%d %H:%M") if exp.created_at else ""
            })
        return data
    return []


@app.callback(
    [Output("selected-experiment-store", "data"),
     Output("selected-experiment-info", "children"),
     Output("import-modal", "style"),
     Output("unit-step-dropdown", "value")],
    [Input("select-button", "n_clicks"), 
     Input("close-modal", "n_clicks"),
     Input("select-experiment-btn", "n_clicks")],
    [State("experiments-table", "selected_rows"),
     State("experiments-table", "data")],
    prevent_initial_call=True
)
def handle_modal_actions(select_btn_clicks, close_btn_clicks, select_exp_clicks, selected_rows, table_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, {"display": "none"}, dash.no_update
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Open modal when "Select Experiment" button is clicked
    if button_id == "select-button":
        return dash.no_update, dash.no_update, {
            "display": "block",
            "position": "fixed",
            "zIndex": 1000,
            "left": 0,
            "top": 0,
            "width": "100%",
            "height": "100%",
            "backgroundColor": "rgba(0,0,0,0.5)"
        }, dash.no_update
    
    # Close modal when close button (×) is clicked
    elif button_id == "close-modal":
        return dash.no_update, dash.no_update, {"display": "none"}, dash.no_update
    
    # Handle experiment selection
    elif button_id == "select-experiment-btn":
        if not select_exp_clicks:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        # Close modal regardless of selection
        modal_style = {"display": "none"}
        
        if selected_rows and table_data and len(selected_rows) > 0:
            selected_exp = table_data[selected_rows[0]]
            experiment_info = f"Selected: {selected_exp['experiment_name']} ({selected_exp['molecule_name']}) - Yield: {selected_exp['yield_percentage']:.1f}%"
            
            # Default to Product Filtration (unit step 3)
            default_unit_step = 3
            
            return selected_exp['result_id'], experiment_info, modal_style, default_unit_step
        else:
            # Button was clicked but no row selected - still close modal
            return dash.no_update, "Please select an experiment from the table first.", modal_style, dash.no_update
    
    return dash.no_update, dash.no_update, {"display": "none"}, dash.no_update


@app.callback(
    Output("time-series-graph", "figure"),
    Output("overall-lmh-output", "children"),
    Input("selected-experiment-store", "data"),
    Input("unit-step-dropdown", "value"),
    Input("data-selection", "value"),
    Input("xaxis-selection", "value"),
    Input("y-min-input", "value"),
    Input("y-max-input", "value"),
    Input("smoothing-input", "value"),
    Input("water-flush-flux", "value"),
    State({"type": "metadata-field", "field": "load_concentration"}, "value"),
)
def update_graph(selected_experiment, selected_unit_step, selected_columns, x_axis, y_min, y_max, smoothing_seconds,
                 water_flux, load_concentration):
    if not selected_experiment or not selected_unit_step:
        return go.Figure(), "No experiment selected"

    # Query metadata for selected filter area (m²)
    try:
        metadata = VFMetadata.objects.get(result_id=selected_experiment)
        filter_area = float(metadata.filter_type)  # Assuming filter_type stores the m² value
        experiment_name = metadata.experiment_name or f"Experiment {selected_experiment}"
        # Use metadata load_concentration if the field value is not available
        if load_concentration is None:
            load_concentration = metadata.load_concentration or 0
    except VFMetadata.DoesNotExist:
        return go.Figure(), "Experiment not found"

    # Query database for selected experiment and unit step
    query_set = VFTimeSeriesData.objects.filter(
        result_id=selected_experiment,
        unit_step=selected_unit_step
    ).values()

    df = pd.DataFrame.from_records(query_set)
    # df.to_csv("viral_filtration_data_raw.csv", index=False)
    print(df)
    print(selected_experiment)
    print(selected_unit_step)

    if df.empty:
        return go.Figure(),0

    df = df.sort_values(by="process_time")

    # Data Preprocessing
    df = df.round({"wir2700": 1, "process_time": 6})
    df = df.drop_duplicates(subset=['wir2700'], keep='first').reset_index(drop=True)

    df['g/m²'] = ((df['wir2700'] * load_concentration) / 1000) / filter_area

    # Create a new DataFrame for flow rate calculation
    df_flux = df[["process_time", "wir2700"]].copy()

    df_flux['process_time_seconds'] = df_flux['process_time'] * 3600

    # Round numerical columns to a fixed number of decimal places
    df_flux = df_flux.round({"wir2700": 1, "process_time": 6})

    df_flux = df_flux.drop_duplicates(subset=['wir2700'], keep='first')

    df_flux['diff_wir2700'] = df_flux['wir2700'].diff() / 1000

    # Calculate x axis g/m^2
    df_flux['g/m²'] = ((df_flux['wir2700'] * load_concentration) / 1000) / filter_area

    df_flux['diff_time'] = df_flux['process_time'].diff()

    df_flux['L/hr'] = df_flux['diff_wir2700'] / df_flux['diff_time']

    df_flux['mL/min'] = df_flux['L/hr'] * 16.666

    df_flux = df_flux[df_flux['L/hr'] > 0]
    # df_flux["L/hr_moving_average"] = df_flux['L/hr'].rolling(window=15).mean()

    # Dynamic Smoothing
    if smoothing_seconds and smoothing_seconds >= 10:
        rolling_window = max(1, int(smoothing_seconds / df_flux["diff_time"].median()))
        df_flux["L/hr_moving_average"] = df_flux['L/hr'].rolling(window=smoothing_seconds).mean()
    else:
        df_flux["L/hr_moving_average"] = df_flux['L/hr']

    # Compute L/m²/hr
    if filter_area > 0:
        df_flux["L/m²/hr"] = df_flux["L/hr_moving_average"] / filter_area
        df_flux["g/m²/hr"] = df_flux["L/m²/hr"] * load_concentration
        df_flux = df_flux[df_flux['L/m²/hr'] > 0]

    # Compute Flux Decay based on Water Flush Flux
    if water_flux:
        df_flux["flux_decay"] = ((water_flux - df_flux["L/m²/hr"]) / (water_flux)) * 100

    # Overall LMH Calculation
    final_time = df["process_time"].iloc[-1]  # Last process time
    final_weight = (df["wir2700"].iloc[-1]) / 1000
    overall_lmh = (final_weight / final_time) / filter_area

    # df_flux.to_csv("viral_filtration_data.csv", index=False)
    # print("CSV saved: viral_filtration_data.csv")

    print(df_flux)

    # Define a dictionary for more descriptive axis labels
    axis_labels = {
        "process_time": "Time (hours)",
        "g/m²": "Load Density (g/m²)",
        "wir2700": "Volume (mL)",
        "L/hr": "Flow Rate (L/hr)",
        "mL/min": "Flow Rate (mL/min)",
        "L/m²/hr": "Flux (L/m²/hr)",
        "g/m²/hr": "Mass Flux (g/m²/hr)",
        "flux_decay": "Flux Decay (%)"
    }

    fig = go.Figure()

    # Define colors for each sensor
    colors = ["blue", "red", "green", "orange", "purple", "brown", "pink", "gray"]

    # Dictionary to store y-axis configurations
    y_axes = {}

    # Iterate over all selected columns and assign traces dynamically
    for i, column in enumerate(selected_columns):
        # Determine which DataFrame to use
        data_source = df_flux if column in df_flux.columns else df  # Choose the appropriate DataFrame

        if column in data_source.columns:
            yaxis_name = f"y{i + 1}" if i > 0 else "y"  # First axis is 'y', others are 'y2', 'y3', etc.

            fig.add_trace(go.Scatter(
                x=data_source[x_axis],  # Shared x-axis
                y=data_source[column],
                mode="lines",
                name=axis_labels.get(column, column),  # Use the descriptive label if available
                yaxis=yaxis_name,  # Assign a unique y-axis
                line=dict(color=colors[i % len(colors)]),
            ))

            # Store y-axis configuration (Correctly formatted for Plotly Layout)
            layout_axis_name = "yaxis" if i == 0 else f"yaxis{i + 1}"  # First axis is 'yaxis', others 'yaxis2', 'yaxis3'
            y_axes[layout_axis_name] = {
                "title": axis_labels.get(column, column),  # Use descriptive labels
                "overlaying": "y" if i > 0 else None,  # First y-axis is standalone, others overlay it
                "side": "right" if i % 2 == 0 else "left",
                "showgrid": True if i == 0 else False,  # Only show grid for primary y-axis
                "gridcolor": 'lightgray' if i == 0 else None
            }

    # Update layout with dynamically created y-axes and new x-axis label
    unit_step_name = unit_step_names.get(selected_unit_step, f"Unit Step {selected_unit_step}")
    fig.update_layout(
        title={
            "text": f"{experiment_name} - {unit_step_name}",
            "x": 0.5,  # Centers the title
            "xanchor": "center",  # Ensures proper centering
            "yanchor": "top"  # Aligns title at the top
        },
        xaxis=dict(title=axis_labels.get(x_axis, x_axis), showgrid=True, gridcolor='lightgray'),  # Set descriptive x-axis title with grid
        hovermode="x unified",
        height=800,
        plot_bgcolor='white',  # White background
        paper_bgcolor='white',  # White paper background
        **y_axes  # Add all y-axes configurations dynamically
    )
    # ✅ Ensure `fig` is returned at the end

    return fig, f"{overall_lmh:.2f} L/m²/hr"


@app.callback(
    Output("metadata-fields", "children"),
    Input("selected-experiment-store", "data")
)
def populate_metadata_fields(selected_experiment):
    if not selected_experiment:
        return html.Div("Select an experiment to view details.")

    try:
        metadata = VFMetadata.objects.get(result_id=selected_experiment)
    except VFMetadata.DoesNotExist:
        return html.Div("Experiment not found.")

    # Fields that should be read-only (auto-calculated)
    calculated_fields = ["load_mass", "product_mass", "yield_percentage"]

    fields = []
    for field in VFMetadata._meta.fields:
        if field.name in ["result_id", "created_at"]:  # Skip ID and timestamp
            continue

        field_container = html.Div(
            style=field_container_style,
            children=[
                html.Label(
                    field.verbose_name or field.name.replace('_', ' ').title(), 
                    style=label_style
                ),
                # Use textarea for experimental_notes field
                dcc.Textarea(
                    id={"type": "metadata-field", "field": field.name},
                    value=getattr(metadata, field.name, ""),
                    style={
                        **input_style,
                        "height": "120px",
                        "resize": "vertical",
                        "fontFamily": "system-ui, -apple-system, sans-serif"
                    }
                ) if field.name == "experimental_notes" else dcc.Input(
                    id={"type": "metadata-field", "field": field.name},
                    type="text",
                    value=getattr(metadata, field.name, ""),
                    style=readonly_style if field.name in calculated_fields else input_style,
                    readOnly=field.name in calculated_fields
                )
            ]
        )
        fields.append(field_container)

    return fields


@app.callback(
    Output("update-status", "children"),
    Input("update-button", "n_clicks"),
    State("selected-experiment-store", "data"),
    State({"type": "metadata-field", "field": ALL}, "value"),
    State({"type": "metadata-field", "field": ALL}, "id"),
    prevent_initial_call=True
)
def update_metadata(n_clicks, selected_experiment, values, ids):
    if not selected_experiment:
        return "Please select an experiment first."

    try:
        metadata = VFMetadata.objects.get(result_id=selected_experiment)

        for value, field_id in zip(values, ids):
            field_name = field_id["field"]
            if field_name in ["result_id", "created_at", "load_mass", "product_mass", "yield_percentage"]:
                continue  # Skip non-editable fields

            setattr(metadata, field_name, value)

        metadata.save()
        return "Experiment information updated successfully!"
    except Exception as e:
        return f"Error updating experiment: {str(e)}"


@app.callback(
    Output({"type": "metadata-field", "field": "load_mass"}, "value"),
    Input({"type": "metadata-field", "field": "load_concentration"}, "value"),
    Input({"type": "metadata-field", "field": "load_volume"}, "value"),
)
def calculate_load_mass(load_concentration, load_volume):
    try:
        load_mass = (float(load_concentration or 0) * float(load_volume or 0))
        return round(load_mass, 2)
    except:
        return ""


@app.callback(
    [Output({"type": "metadata-field", "field": "product_mass"}, "value"),
     Output({"type": "metadata-field", "field": "yield_percentage"}, "value")],
    Input({"type": "metadata-field", "field": "final_volume"}, "value"),
    Input({"type": "metadata-field", "field": "final_concentration"}, "value"),
    Input({"type": "metadata-field", "field": "load_mass"}, "value"),
)
def calculate_product_mass_and_yield(final_volume, final_concentration, load_mass):
    try:
        product_mass = float(final_volume or 0) * float(final_concentration or 0)
        recovery = (product_mass / float(load_mass or 1)) * 100
        return round(product_mass, 2), round(recovery, 2)
    except:
        return "", ""
