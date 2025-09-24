import dash
import pandas as pd
import plotly.graph_objects as go
from django_plotly_dash import DjangoDash
from dash import dcc, html, Input, Output, State, dash_table
from plotly_integration.models import SartoflowTimeSeriesData, UFDFMetadata

# Create Dash App
app = DjangoDash("UFDFApp")

# Define selectable columns (except BatchId and ProcessTime)
selectable_columns = [
    {"label": "Agitator Speed (AG_2100)", "value": "ag2100_value"},
    {"label": "Differential Pressure (DPRESS)", "value": "dpress_value"},
    {"label": "Filtrate Flow Rate (F_PERM)", "value": "f_perm_value"},
    {"label": "Feed Pump Output (P2500)", "value": "p2500_output"},
    {"label": "Fill Pump Output (P3000 Output)", "value": "p3000_output"},
    {"label": "Fill Pump Totalizer (P3000_T)", "value": "p3000_t"},
    {"label": "Retentate Pressure (PIR2600)", "value": "pir2600"},
    {"label": "Permeate Pressure (PIR2700)", "value": "pir2700"},
    {"label": "Feed Pressure (PIRC2500)", "value": "pirc2500_value"},
    {"label": "Process Temperature (TIR2100)", "value": "tir2100"},
    {"label": "TMP (bar)", "value": "tmp"},
    {"label": "Permeate Weight (WIR2700)", "value": "wir2700"},
    {"label": "Retain Vessel Weight (WIRC2100)", "value": "wirc2100_setpoint"},
    {"label": "Feed Flow Rate (mL/min)", "value": "feed_flow_rate"},
    {"label": "Permeate Flow Rate (mL/min)", "value": "permeate_flow_rate"},
    {"label": "Retentate Flow Rate (mL/min)", "value": "retentate_flow_rate"},
    {"label": "Flux/Feed Rate", "value": "flux_decay"},
    {"label": "Flux (L/m²/hr)", "value": "flux"},
]

# Create a lookup for value → label
label_map = {item["value"].lower(): item["label"] for item in selectable_columns}

# Define input style similar to create_ufdf_experiment
input_style = {
    "width": "100%",
    "padding": "10px",
    "marginBottom": "15px",
    "borderRadius": "5px",
    "border": "1px solid #ccc"
}

readonly_input_style = input_style.copy()
readonly_input_style["backgroundColor"] = "#e9f1fb"
readonly_input_style["border"] = "1px solid #bbb"

# Dash Layout
app.layout = html.Div(
    style={"fontFamily": "Arial, sans-serif", "padding": "20px"},
    children=[
        dcc.Store(id='selected-experiment', data=None),
        # Top bar with select button
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "marginBottom": "20px"},
            children=[
                html.Button(
                    "Select Experiment",
                    id="open-modal-btn",
                    style={
                        "backgroundColor": "#007bff",
                        "color": "white",
                        "border": "none",
                        "padding": "10px 20px",
                        "borderRadius": "5px",
                        "cursor": "pointer",
                        "fontSize": "14px"
                    }
                ),
                html.Div(id="selected-experiment-display", style={"fontSize": "16px", "fontWeight": "bold", "color": "#0047b3"})
            ]
        ),
        # Main Tabs
        dcc.Tabs(
            id="main-tabs",
            value="time-series-tab",
            children=[
                # Tab 1: Time Series Plot with Sidebar
                dcc.Tab(
                    label="Time Series Analysis",
                    value="time-series-tab",
                    children=[
                        html.Div(
                            style={
                                "display": "flex",
                                "flexDirection": "row",
                                "gap": "20px",
                                "marginTop": "20px",
                                "minHeight": "80vh"
                            },
                            children=[
                                # Graph Area (left side, larger)
                                html.Div(
                                    style={"width": "75%", "border": "1px solid #ccc", "padding": "10px", "borderRadius": "5px"},
                                    children=[
                                        html.H3("Time Series Data", style={"color": "#0047b3"}),
                                        dcc.Graph(id="time-series-graph"),
                                    ],
                                ),
                                # Right Sidebar for Plot Selection
                                html.Div(
                                    style={"width": "25%", "border": "1px solid #ccc", "padding": "10px", "borderRadius": "5px"},
                                    children=[
                                        html.H3("Select Data to Plot", style={"fontSize": "16px", "marginBottom": "10px", "color": "#0047b3"}),
                                        dcc.Checklist(
                                            id="data-selection",
                                            options=selectable_columns,
                                            value=["tmp"],  # Default selection
                                            style={"display": "flex", "flexDirection": "column"}
                                        ),
                                    ]
                                )
                            ]
                        )
                    ]
                ),
                # Tab 2: Experiment Details (form-like)
                dcc.Tab(
                    label="Experiment Details",
                    value="details-tab",
                    children=[
                        html.Div(
                            id="experiment-details-form",
                            style={"maxWidth": "800px", "margin": "20px auto", "padding": "20px"}
                        )
                    ]
                )
            ]
        ),
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
                        "margin": "2% auto",
                        "width": "95%",
                        "height": "90%",
                        "backgroundColor": "white",
                        "borderRadius": "10px",
                        "padding": "20px"
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
                        # Tabs for Create New vs Select Existing (Create New first)
                        dcc.Tabs(
                            id="modal-tabs",
                            value="create-tab",
                            children=[
                                dcc.Tab(
                                    label="Create New Experiment",
                                    value="create-tab",
                                    children=[
                                        html.Iframe(
                                            src="/plotly_integration/dash-app/app/UFDFAnalysis/",
                                            style={
                                                "width": "100%",
                                                "height": "75vh",
                                                "border": "none",
                                                "marginTop": "10px"
                                            }
                                        )
                                    ]
                                ),
                                dcc.Tab(
                                    label="Select Experiment",
                                    value="select-tab",
                                    children=[
                                        html.Div(
                                            style={
                                                "padding": "20px",
                                                "height": "70vh",
                                                "display": "flex",
                                                "flexDirection": "column",
                                                "boxSizing": "border-box"
                                            },
                                            children=[
                                                html.H4("Select an Existing Experiment",
                                                        style={'marginBottom': '20px', 'color': '#0056b3'}),
                                                # Table container that grows to fill available space
                                                html.Div(
                                                    style={
                                                        "flexGrow": 1,
                                                        "marginBottom": "20px",
                                                        "minHeight": 0
                                                    },
                                                    children=[
                                                        dash_table.DataTable(
                                                            id="experiments-table",
                                                            columns=[
                                                                {"name": "ID", "id": "result_id"},
                                                                {"name": "Experiment Name", "id": "experiment_name"},
                                                                {"name": "Molecule", "id": "molecule_name"},
                                                                {"name": "Created", "id": "created_at"}
                                                            ],
                                                            data=[],
                                                            row_selectable="single",
                                                            selected_rows=[],
                                                            filter_action="native",
                                                            sort_action="native",
                                                            page_action="native",
                                                            page_size=15,
                                                            fixed_rows={'headers': True},
                                                            style_table={
                                                                'height': '90%',
                                                                'overflowY': 'auto',
                                                                'overflowX': 'auto',
                                                                'borderRadius': '5px'
                                                            },
                                                            style_cell={
                                                                'textAlign': 'center',
                                                                'padding': '12px',
                                                                'fontSize': '14px',
                                                                'fontFamily': 'system-ui, -apple-system, sans-serif'
                                                            },
                                                            style_header={
                                                                'backgroundColor': '#f8f9fa',
                                                                'fontWeight': '600',
                                                                'borderBottom': '2px solid #dee2e6'
                                                            },
                                                            style_data={
                                                                'borderBottom': '1px solid #dee2e6'
                                                            },
                                                            style_data_conditional=[
                                                                {
                                                                    'if': {'row_index': 'odd'},
                                                                    'backgroundColor': '#f8f9fa'
                                                                }
                                                            ]
                                                        )
                                                    ]
                                                ),
                                                # Buttons at the bottom
                                                html.Div(
                                                    style={'display': 'flex', 'justifyContent': 'flex-end', 'gap': '10px'},
                                                    children=[
                                                        html.Button(
                                                            "Cancel",
                                                            id="cancel-select-btn",
                                                            style={
                                                                'backgroundColor': '#6c757d',
                                                                'color': 'white',
                                                                'padding': '8px 16px',
                                                                'border': 'none',
                                                                'borderRadius': '5px',
                                                                'cursor': 'pointer',
                                                                'fontSize': '14px',
                                                                'fontWeight': '500'
                                                            }
                                                        ),
                                                        html.Button(
                                                            "Select Experiment",
                                                            id="select-experiment-btn",
                                                            disabled=True,
                                                            style={
                                                                "backgroundColor": "#007bff",
                                                                "color": "white",
                                                                "border": "none",
                                                                "padding": "8px 16px",
                                                                "borderRadius": "5px",
                                                                "cursor": "pointer",
                                                                "fontSize": "14px",
                                                                "fontWeight": "500"
                                                            }
                                                        ),
                                                    ]
                                                ),
                                                html.Div(id="selection-status", style={"marginTop": "10px"})
                                            ]
                                        )
                                    ]
                                ),
                            ]
                        )
                    ]
                )
            ]
        ),
        dcc.Interval(
            id='refresh-interval',
            interval=10 * 1000,  # Every 10 seconds
            n_intervals=0
        ),
    ],
)


@app.callback(
    Output("experiments-table", "data"),
    Input("refresh-interval", "n_intervals")
)
def update_experiment_table(n):
    # Get experiment IDs that have time series data
    from plotly_integration.models import SartoflowTimeSeriesData
    available_result_ids = list(SartoflowTimeSeriesData.objects.values_list('result_id', flat=True).distinct())
    available_result_ids = [r for r in available_result_ids if r is not None]
    
    # Only show experiments that have time series data
    experiments = UFDFMetadata.objects.filter(
        result_id__in=available_result_ids
    ).order_by('-created_at').values('result_id', 'experiment_name', 'molecule_name', 'created_at')

    # Format data for table
    table_data = []
    for exp in experiments:
        table_data.append({
            'result_id': exp['result_id'],
            'experiment_name': exp['experiment_name'],
            'molecule_name': exp['molecule_name'],
            'created_at': exp['created_at'].strftime('%Y-%m-%d %H:%M') if exp['created_at'] else 'N/A'
        })

    return table_data


@app.callback(
    Output("select-experiment-btn", "disabled"),
    Input("experiments-table", "selected_rows")
)
def enable_select_button(selected_rows):
    return len(selected_rows) == 0


@app.callback(
    Output("selected-experiment", "data"),
    Input("select-experiment-btn", "n_clicks"),
    [State("experiments-table", "selected_rows"), State("experiments-table", "data")],
    prevent_initial_call=True
)
def select_experiment_from_table(n_clicks, selected_rows, table_data):
    if not n_clicks:
        return dash.no_update
    
    if selected_rows and table_data and len(selected_rows) > 0:
        selected_experiment = table_data[selected_rows[0]]
        experiment_id = selected_experiment['result_id']
        return experiment_id
    else:
        # Button clicked but no selection
        return dash.no_update


@app.callback(
    [Output("experiment-details-form", "children"),
     Output("selected-experiment-display", "children")],
    Input("selected-experiment", "data")
)
def show_experiment_details(experiment_id):
    if not experiment_id:
        return html.Div("No experiment selected. Click 'Select Experiment' to choose one.", 
                        style={"textAlign": "center", "color": "#666", "marginTop": "50px"}), ""

    try:
        exp = UFDFMetadata.objects.get(result_id=experiment_id)
        
        # Create form similar to create_ufdf_experiment
        form_layout = [
            html.H2(f"UFDF Experiment: {exp.experiment_name}", 
                   style={"textAlign": "center", "color": "#0047b3", "marginBottom": "20px"}),
            
            # Basic Information Section
            html.H3("Basic Information", style={"marginTop": "20px", "color": "#0047b3"}),
            
            html.Label("Molecule:", style={"fontWeight": "bold", "marginTop": "15px"}),
            dcc.Input(id="detail-molecule", type="text", value=exp.molecule_name or "",
                     style=input_style),
            
            html.Label("Experiment Name:", style={"fontWeight": "bold", "marginTop": "15px"}),
            dcc.Input(id="detail-experiment-name", type="text", value=exp.experiment_name or "",
                     style=input_style),
            
            html.Label("Experimental Notes:", style={"fontWeight": "bold", "marginTop": "15px"}),
            dcc.Textarea(id="detail-notes", value=exp.experimental_notes or "",
                        style={"width": "100%", "height": "100px", "padding": "10px", "marginBottom": "20px"}),
            
            html.Label("Cassette Type (m²):", style={"fontWeight": "bold", "marginTop": "15px"}),
            dcc.Input(id="detail-cassette", type="number", value=exp.cassette_type or 0.02,
                     style=input_style),
            
            # Load Information Section
            html.H3("Load Information", style={"marginTop": "20px", "color": "#0047b3"}),
            
            html.Label("Load Concentration (mg/mL):", style={"fontWeight": "bold", "marginTop": "15px"}),
            dcc.Input(id="detail-load-concentration", type="number", value=exp.load_concentration or "",
                     style=input_style),
            
            html.Label("Load Volume (mL):", style={"fontWeight": "bold"}),
            dcc.Input(id="detail-load-volume", type="number", value=exp.load_volume or "",
                     style=input_style),
            
            html.Label("Load Mass (mg):", style={"fontWeight": "bold"}),
            dcc.Input(id="detail-load-mass", type="number", value=exp.load_mass or "", readOnly=True,
                     style=readonly_input_style),
            
            # Process Settings Section
            html.H3("Process Settings", style={"marginTop": "20px", "color": "#0047b3"}),
            
            html.Label("Target Diafiltration Concentration:", style={"fontWeight": "bold"}),
            dcc.Input(id="detail-uf1-target", type="number", value=exp.target_diafiltration_concentration or "",
                     style=input_style),
            
            html.Label("UF1 Target Reservoir Mass (g):", style={"fontWeight": "bold"}),
            dcc.Input(id="detail-uf1-mass", type="number", value=exp.uf1_target_reservoir_mass or "", readOnly=True,
                     style=readonly_input_style),
            
            html.Label("# Diavolumes:", style={"fontWeight": "bold"}),
            dcc.Input(id="detail-diavolumes", type="number", value=exp.diavolumes or "",
                     style=input_style),
            
            html.Label("Permeate Target Mass (g):", style={"fontWeight": "bold"}),
            dcc.Input(id="detail-permeate-mass", type="number", value=exp.permeate_target_mass or "", readOnly=True,
                     style=readonly_input_style),
            
            # Filtration Settings Section
            html.H3("Filtration Settings", style={"marginTop": "20px", "color": "#0047b3"}),
            
            html.Label("LMH Target:", style={"fontWeight": "bold"}),
            dcc.Input(id="detail-lmh-target", type="number", value=exp.lmh_target or "",
                     style=input_style),
            
            html.Label("Target Flow Rate (mL/min):", style={"fontWeight": "bold"}),
            dcc.Input(id="detail-target-flow-rate", type="number", value=exp.target_flow_rate or "", readOnly=True,
                     style=readonly_input_style),
            
            html.Label("Target P2500 Setpoint (%):", style={"fontWeight": "bold"}),
            dcc.Input(id="detail-p2500-setpoint", type="number", value=exp.target_p2500_setpoint or "", readOnly=True,
                     style=readonly_input_style),
            
            html.Label("Target P3000 Setpoint:", style={"fontWeight": "bold"}),
            dcc.Input(id="detail-p3000-setpoint", type="number", value=exp.target_p3000_setpoint or "", readOnly=True,
                     style=readonly_input_style),
            
            # Final Results Section
            html.H3("Final Results", style={"marginTop": "20px", "color": "#0047b3"}),
            
            html.Label("Final Volume (mL):", style={"fontWeight": "bold"}),
            dcc.Input(id="detail-final-volume", type="number", value=exp.final_volume or "",
                     style=input_style),
            
            html.Label("Final Concentration (mg/mL):", style={"fontWeight": "bold"}),
            dcc.Input(id="detail-final-concentration", type="number", value=exp.final_concentration or "",
                     style=input_style),
            
            html.Label("Product Mass (mg):", style={"fontWeight": "bold"}),
            dcc.Input(id="detail-product-mass", type="number", value=exp.product_mass or "", readOnly=True,
                     style=readonly_input_style),
            
            html.Label("Yield (%):", style={"fontWeight": "bold"}),
            dcc.Input(id="detail-yield", type="number", value=exp.yield_percentage or "", readOnly=True,
                     style=readonly_input_style),
            
            # Update Button
            html.Button("Update Experiment", id="update-experiment-btn", n_clicks=0,
                       style={"backgroundColor": "#28a745", "color": "white", "padding": "10px 20px",
                              "marginTop": "30px", "borderRadius": "5px", "border": "none", "cursor": "pointer"}),
            
            html.Div(id="update-status", style={"marginTop": "10px", "color": "green"})
        ]
        
        display_text = f"Selected: {exp.experiment_name} ({exp.molecule_name})"
        return form_layout, display_text
        
    except UFDFMetadata.DoesNotExist:
        return html.Div("Experiment not found", 
                       style={"textAlign": "center", "color": "#dc3545", "marginTop": "50px"}), ""


@app.callback(
    Output("time-series-graph", "figure"),
    Input("selected-experiment", "data"),
    Input("data-selection", "value")
)
def update_graph(selected_experiment_id, selected_columns):
    if not selected_experiment_id:
        return go.Figure().add_annotation(
            text="Select an experiment to view time series data",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font={"size": 16, "color": "#666"}
        ).update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False}
        )

    try:
        # Get experiment metadata
        experiment = UFDFMetadata.objects.get(result_id=selected_experiment_id)

        # Query all time series data for this experiment, ordered by unit_step and process_time
        query_set = SartoflowTimeSeriesData.objects.filter(
            result_id=selected_experiment_id
        ).values().order_by('unit_step', 'process_time')

        df = pd.DataFrame.from_records(query_set)

        if df.empty:
            return go.Figure().add_annotation(
                text=f"No time series data found for experiment ID {selected_experiment_id}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font={"size": 16, "color": "#dc3545"}
            ).update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False}
            )

        # Verify 'process_time' column exists
        if 'process_time' not in df.columns:
            return go.Figure().add_annotation(
                text="process_time column not found in data",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font={"size": 16, "color": "#dc3545"}
            ).update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False}
            )

        # Create consecutive time series by adjusting process times for each step
        combined_df = pd.DataFrame()
        cumulative_time_offset = 0

        # Step type mapping for display
        step_names = {1: "UF1", 2: "UF2", 3: "DF1", 4: "DF2", 5: "Rinse"}

        for unit_step in sorted(df['unit_step'].unique()):
            step_data = df[df['unit_step'] == unit_step].copy()

            # Reset process time to start from the cumulative offset
            if not step_data.empty:
                step_min_time = step_data['process_time'].min()
                step_data['process_time'] = step_data['process_time'] - step_min_time + cumulative_time_offset
                step_data['step_name'] = step_names.get(unit_step, f"Step {unit_step}")

                # Update cumulative offset for next step
                cumulative_time_offset = step_data['process_time'].max() + 0.1  # Small gap between steps

                combined_df = pd.concat([combined_df, step_data], ignore_index=True)

        df = combined_df.sort_values(by="process_time")

        # Calculated columns
        df['feed_flow_rate'] = df['p2500_output'] * 16.67
        df['diff_wir2700'] = df['wir2700'].diff() / 1000
        df['diff_time'] = df['process_time'].diff()
        df['permeate_flow_rate'] = (df['diff_wir2700'] / df['diff_time']) * 16.667
        df['permeate_flow_rate'] = df['permeate_flow_rate'].rolling(window=10).mean()
        df['retentate_flow_rate'] = df['feed_flow_rate'] - df['permeate_flow_rate']
        df['flux_decay'] = df['permeate_flow_rate'] / df['feed_flow_rate']
        df['flux'] = (df['permeate_flow_rate'] * 0.06) / 0.02

        # Convert selected columns to lowercase
        selected_columns = [col.lower() for col in selected_columns]

        fig = go.Figure()
        axis_map = {}
        y_axis_count = 1

        for column in selected_columns:
            if column in df.columns:
                y_axis_name = "y" if y_axis_count == 1 else f"y{y_axis_count}"
                axis_map[column] = y_axis_name

                fig.add_trace(go.Scatter(
                    x=df["process_time"],
                    y=df[column],
                    mode="lines",
                    name=label_map.get(column, column),
                    yaxis=y_axis_name,
                    text=df['step_name'],
                    hovertemplate=f"<b>{label_map.get(column, column)}</b><br>" +
                                  "Time: %{x}<br>" +
                                  "Value: %{y}<br>" +
                                  "Step: %{text}<br>" +
                                  "<extra></extra>"
                ))

                y_axis_count += 1
            else:
                print(f"⚠️ Warning: Column '{column}' not found in DataFrame.")

        # Add vertical lines to separate process steps
        step_boundaries = []
        current_time = 0
        for unit_step in sorted(df['unit_step'].unique()):
            step_data = df[df['unit_step'] == unit_step]
            if not step_data.empty:
                step_start = step_data['process_time'].min()
                if step_start > current_time:
                    step_boundaries.append(step_start)
                current_time = step_data['process_time'].max()

        for boundary_time in step_boundaries:
            fig.add_vline(x=boundary_time, line_dash="dash", line_color="gray", opacity=0.5)

        # Layout with multiple Y-axes and 0 min range
        layout = {
            "title": {
                "text": f"{experiment.experiment_name} - UFDF Process",
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
                "font": {"size": 18, "color": "#0056b3"}
            },
            "xaxis": {"title": "Cumulative Process Time (hrs)"},
        }

        for i, column in enumerate(selected_columns, start=1):
            axis_key = "yaxis" if i == 1 else f"yaxis{i}"
            axis_name = "y" if i == 1 else f"y{i}"

            axis_config = {
                "title": label_map.get(column, column),
                "overlaying": "y" if i > 1 else None,
                "side": "right" if i % 2 == 0 else "left",
                "showgrid": i == 1,
            }

            if column == "flux_decay":
                axis_config["range"] = [0, 1]  # Force fixed scale for flux/feed
            else:
                axis_config["rangemode"] = "tozero"

            layout[axis_key] = axis_config

        # Dynamically add extra y-axes
        for i, column in enumerate(selected_columns[1:], start=2):
            layout[f"yaxis{i}"] = {
                "title": label_map.get(column, column),
                "overlaying": "y",
                "side": "right" if i % 2 == 0 else "left",
                "showgrid": False,
                "rangemode": "tozero"
            }

        fig.update_layout(layout, template="plotly_white")

        return fig

    except UFDFMetadata.DoesNotExist:
        return go.Figure().add_annotation(
            text="Experiment not found",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    except Exception as e:
        print(f"Error updating graph: {e}")
        return go.Figure().add_annotation(
            text=f"Error loading data: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )


@app.callback(
    Output("import-modal", "style"),
    [Input("open-modal-btn", "n_clicks"), Input("close-modal", "n_clicks"), Input("cancel-select-btn", "n_clicks"), Input("select-experiment-btn", "n_clicks")],
    prevent_initial_call=True
)
def toggle_modal(open_clicks, close_clicks, cancel_clicks, select_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {"display": "none"}
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "open-modal-btn":
        return {
            "display": "block",
            "position": "fixed",
            "zIndex": 1000,
            "left": 0,
            "top": 0,
            "width": "100%",
            "height": "100%",
            "backgroundColor": "rgba(0,0,0,0.5)"
        }
    else:
        return {"display": "none"}

# Add callback to update experiment
@app.callback(
    Output("update-status", "children"),
    Input("update-experiment-btn", "n_clicks"),
    [State("selected-experiment", "data"),
     State("detail-molecule", "value"),
     State("detail-experiment-name", "value"),
     State("detail-notes", "value"),
     State("detail-cassette", "value"),
     State("detail-load-concentration", "value"),
     State("detail-load-volume", "value"),
     State("detail-uf1-target", "value"),
     State("detail-diavolumes", "value"),
     State("detail-lmh-target", "value"),
     State("detail-final-volume", "value"),
     State("detail-final-concentration", "value")],
    prevent_initial_call=True
)
def update_experiment(n_clicks, experiment_id, molecule, exp_name, notes, cassette, 
                     load_conc, load_vol, uf1_target, diavolumes, lmh_target,
                     final_vol, final_conc):
    if not n_clicks or not experiment_id:
        return ""
    
    try:
        exp = UFDFMetadata.objects.get(result_id=experiment_id)
        
        # Update fields
        exp.molecule_name = molecule
        exp.experiment_name = exp_name
        exp.experimental_notes = notes
        exp.cassette_type = cassette
        exp.load_concentration = load_conc
        exp.load_volume = load_vol
        exp.target_diafiltration_concentration = uf1_target
        exp.diavolumes = diavolumes
        exp.lmh_target = lmh_target
        exp.final_volume = final_vol
        exp.final_concentration = final_conc
        
        # Calculate derived fields
        if load_conc and load_vol:
            exp.load_mass = load_conc * load_vol
        
        if uf1_target and exp.load_mass:
            exp.uf1_target_reservoir_mass = exp.load_mass / uf1_target if uf1_target else None
            
        if diavolumes and exp.uf1_target_reservoir_mass:
            exp.permeate_target_mass = diavolumes * exp.uf1_target_reservoir_mass
            
        if lmh_target and cassette:
            exp.target_flow_rate = (lmh_target * cassette) / 0.06
            exp.target_p2500_setpoint = exp.target_flow_rate / 2 if exp.target_flow_rate else None
            exp.target_p3000_setpoint = exp.target_flow_rate / 10 if exp.target_flow_rate else None
        
        if final_vol and final_conc:
            exp.product_mass = final_vol * final_conc
            
        if exp.product_mass and exp.load_mass:
            exp.yield_percentage = (exp.product_mass / exp.load_mass) * 100
        
        exp.save()
        return "✓ Experiment updated successfully!"
        
    except UFDFMetadata.DoesNotExist:
        return "Error: Experiment not found"
    except Exception as e:
        return f"Error updating experiment: {str(e)}"