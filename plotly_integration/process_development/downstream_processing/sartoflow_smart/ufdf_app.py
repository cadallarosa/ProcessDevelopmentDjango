import dash
import pandas as pd
import plotly.graph_objects as go
from django_plotly_dash import DjangoDash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
from plotly_integration.models import SartoflowTimeSeriesData, UFDFMetadata

# Create Dash App with Bootstrap theme
app = DjangoDash("UFDFApp", external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
], suppress_callback_exceptions=True)

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

# Dash Layout with Bootstrap components
app.layout = dbc.Container([
    dcc.Store(id='selected-experiment', data=None),

    # Header
    # dbc.Row([
    #     dbc.Col([
    #         html.H1([
    #             html.I(className="fas fa-chart-line text-primary me-3"),
    #             "UFDF Process Analysis"
    #         ], className="mb-3"),
    #         html.P("Ultrafiltration/Diafiltration process monitoring and analysis system",
    #                className="lead text-muted")
    #     ], width=12),
    # ], className="mb-4"),

    # Top bar with experiment selection
    dbc.Row([
        dbc.Col([
            dbc.Button(
                [html.I(className="fas fa-search me-2"), "Select Experiment"],
                id="open-modal-btn",
                color="primary",
                size="md"
            )
        ], width="auto"),
        dbc.Col([
            html.Div(id="selected-experiment-display", className="fs-6 fw-bold text-info d-flex align-items-center")
        ], width=True),
    ], className="mb-4", justify="between"),
    # Main Tabs
    dbc.Tabs([
        dbc.Tab(label="Time Series Analysis", tab_id="time-series-tab"),
        dbc.Tab(label="Experiment Details", tab_id="details-tab"),
    ], id="main-tabs", active_tab="time-series-tab"),

    html.Div(id="tab-content", className="mt-4"),

    # Bootstrap Modal for experiment selection
    dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle([
                html.I(className="fas fa-search me-2"),
                "Select UFDF Experiment"
            ])
        ]),
        dbc.ModalBody([
            dbc.Tabs([
                dbc.Tab(label="Create New", tab_id="create-tab"),
                dbc.Tab(label="Select Existing", tab_id="select-tab"),
            ], id="modal-tabs", active_tab="select-tab"),
            html.Div(id="modal-tab-content", className="mt-3")
        ]),
    ], id="import-modal", size="xl", is_open=False),

    # Alerts
    html.Div(id="alerts-container")

], fluid=True, className="p-4")


# Tab Content Callback
@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs", "active_tab")
)
def render_tab_content(active_tab):
    if active_tab == "time-series-tab":
        return dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    # Graph Area (main content)
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5([
                                    html.I(className="fas fa-chart-area me-2"),
                                    "Time Series Data"
                                ], className="mb-0")
                            ]),
                            dbc.CardBody([
                                dcc.Graph(id="time-series-graph", style={"height": "70vh"})
                            ])
                        ])
                    ], width=8),
                    # Sidebar for Data Selection
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H6([
                                    html.I(className="fas fa-sliders-h me-2"),
                                    "Select Data to Plot"
                                ], className="mb-0")
                            ]),
                            dbc.CardBody([
                                dbc.Checklist(
                                    id="data-selection",
                                    options=selectable_columns,
                                    value=["tmp"],  # Default selection
                                    className="small"
                                ),
                            ])
                        ])
                    ], width=4)
                ])
            ])
        ])
    elif active_tab == "details-tab":
        return dbc.Card([
            dbc.CardBody([
                html.Div(id="experiment-details-form")
            ])
        ])


# Modal Tab Content Callback
@app.callback(
    Output("modal-tab-content", "children"),
    Input("modal-tabs", "active_tab")
)
def render_modal_tab_content(active_tab):
    print(f"DEBUG: render_modal_tab_content called with active_tab: {active_tab}")

    if active_tab == "create-tab":
        return html.Iframe(
            src="/plotly_integration/dash-app/app/UFDFAnalysis/",
            style={
                "width": "100%",
                "height": "75vh",
                "border": "none"
            }
        )
    elif active_tab == "select-tab":
        # Force an immediate data load by calling our function
        try:
            from plotly_integration.models import SartoflowTimeSeriesData
            available_result_ids = list(SartoflowTimeSeriesData.objects.values_list('result_id', flat=True).distinct())
            available_result_ids = [r for r in available_result_ids if r is not None]

            if not available_result_ids:
                experiments = UFDFMetadata.objects.all().order_by('-created_at').values(
                    'result_id', 'experiment_name', 'molecule_name', 'created_at'
                )
            else:
                experiments = UFDFMetadata.objects.filter(
                    result_id__in=available_result_ids
                ).order_by('-created_at').values('result_id', 'experiment_name', 'molecule_name', 'created_at')

            table_data = []
            for exp in experiments:
                table_data.append({
                    'result_id': exp['result_id'],
                    'experiment_name': exp['experiment_name'] or 'Unnamed',
                    'molecule_name': exp['molecule_name'] or 'Unknown',
                    'created_at': exp['created_at'].strftime('%Y-%m-%d %H:%M') if exp['created_at'] else 'N/A'
                })

            print(f"DEBUG: Loading {len(table_data)} experiments directly into table")

        except Exception as e:
            print(f"DEBUG: Error loading experiments: {e}")
            table_data = []

        return dbc.Card([
            dbc.CardBody([
                dash_table.DataTable(
                    id="experiments-table",
                    columns=[
                        {"name": "ID", "id": "result_id"},
                        {"name": "Experiment Name", "id": "experiment_name"},
                        {"name": "Molecule", "id": "molecule_name"},
                        {"name": "Created", "id": "created_at"}
                    ],
                    data=table_data,  # Pre-populate with data
                    row_selectable="single",
                    selected_rows=[],
                    filter_action="native",
                    sort_action="native",
                    page_action="native",
                    page_size=15,
                    style_cell={'textAlign': 'left', 'fontSize': '12px', 'padding': '8px'},
                    style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                    style_data_conditional=[
                        {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}
                    ]
                ),
                html.Div(className="mt-3 text-end", children=[
                    dbc.Button(
                        "Cancel",
                        id="cancel-select-btn",
                        color="secondary",
                        size="sm",
                        className="me-2"
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-check me-2"), "Select Experiment"],
                        id="select-experiment-btn",
                        color="primary",
                        size="sm",
                        disabled=True
                    )
                ])
            ])
        ])


    dcc.Interval(
        id='refresh-interval',
        interval=10 * 1000,  # Every 10 seconds
        n_intervals=0
    ),


@app.callback(
    Output("experiments-table", "data"),
    [Input("refresh-interval", "n_intervals"), Input("import-modal", "is_open")]
)
def update_experiment_table(n, modal_is_open):
    print(f"DEBUG: update_experiment_table called with n_intervals={n}, modal_is_open={modal_is_open}")

    try:
        # Get experiment IDs that have time series data
        from plotly_integration.models import SartoflowTimeSeriesData

        # First, let's see what data we have
        total_ufdf_metadata = UFDFMetadata.objects.count()
        total_time_series = SartoflowTimeSeriesData.objects.count()
        print(f"DEBUG: Total UFDFMetadata records: {total_ufdf_metadata}")
        print(f"DEBUG: Total SartoflowTimeSeriesData records: {total_time_series}")

        # Check what result_ids exist in time series data
        time_series_result_ids = list(SartoflowTimeSeriesData.objects.values_list('result_id', flat=True).distinct())
        print(f"DEBUG: Time series result_ids (raw): {time_series_result_ids[:10]}...")  # Show first 10

        # Filter out None values
        available_result_ids = [r for r in time_series_result_ids if r is not None]
        print(f"DEBUG: Available result_ids (filtered): {len(available_result_ids)} total")
        if available_result_ids:
            print(f"DEBUG: Sample result_ids: {available_result_ids[:5]}")

        # Check what result_ids exist in UFDFMetadata
        ufdf_result_ids = list(UFDFMetadata.objects.values_list('result_id', flat=True).distinct())
        print(f"DEBUG: UFDFMetadata result_ids: {len(ufdf_result_ids)} total")
        if ufdf_result_ids:
            print(f"DEBUG: Sample UFDFMetadata result_ids: {ufdf_result_ids[:5]}")

        # Find intersection
        common_ids = set(available_result_ids) & set(ufdf_result_ids)
        print(f"DEBUG: Common result_ids between tables: {len(common_ids)}")

        if not available_result_ids:
            print("DEBUG: No time series data found, showing all UFDFMetadata records")
            # If no time series data, show all UFDF experiments
            experiments = UFDFMetadata.objects.all().order_by('-created_at').values(
                'result_id', 'experiment_name', 'molecule_name', 'created_at'
            )
        else:
            # Only show experiments that have time series data
            experiments = UFDFMetadata.objects.filter(
                result_id__in=available_result_ids
            ).order_by('-created_at').values('result_id', 'experiment_name', 'molecule_name', 'created_at')

        print(f"DEBUG: Found {len(experiments)} experiments for table")

        # Format data for table
        table_data = []
        for exp in experiments:
            table_data.append({
                'result_id': exp['result_id'],
                'experiment_name': exp['experiment_name'] or 'Unnamed',
                'molecule_name': exp['molecule_name'] or 'Unknown',
                'created_at': exp['created_at'].strftime('%Y-%m-%d %H:%M') if exp['created_at'] else 'N/A'
            })

        print(f"DEBUG: Returning {len(table_data)} records to table")
        return table_data

    except Exception as e:
        print(f"ERROR: Exception in update_experiment_table: {e}")
        import traceback
        traceback.print_exc()
        return []


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
        return dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "No experiment selected. Click 'Select Experiment' to choose one."
        ], color="info", className="text-center"), ""

    try:
        exp = UFDFMetadata.objects.get(result_id=experiment_id)

        # Create form with Bootstrap styling
        form_layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H3([
                        html.I(className="fas fa-flask me-2"),
                        f"UFDF Experiment: {exp.experiment_name}"
                    ], className="text-primary mb-4 text-center")
                ])
            ]),

            # Basic Information Section
            dbc.Card([
                dbc.CardHeader([
                    html.H5([
                        html.I(className="fas fa-info me-2"),
                        "Basic Information"
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Molecule:", className="fw-bold"),
                            dbc.Input(
                                id="detail-molecule",
                                type="text",
                                value=exp.molecule_name or "",
                                className="mb-3"
                            ),
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Experiment Name:", className="fw-bold"),
                            dbc.Input(
                                id="detail-experiment-name",
                                type="text",
                                value=exp.experiment_name or "",
                                className="mb-3"
                            ),
                        ], width=6),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Experimental Notes:", className="fw-bold"),
                            dbc.Textarea(
                                id="detail-notes",
                                value=exp.experimental_notes or "",
                                rows=3,
                                className="mb-3"
                            ),
                        ])
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Cassette Type (m²):", className="fw-bold"),
                            dbc.Input(
                                id="detail-cassette",
                                type="number",
                                value=exp.cassette_type or 0.02,
                                className="mb-3"
                            ),
                        ], width=6),
                    ]),
                ])
            ], className="mb-4"),
            
            # Load Information Section
            dbc.Card([
                dbc.CardHeader([
                    html.H5([
                        html.I(className="fas fa-vial me-2"),
                        "Load Information"
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Load Concentration (mg/mL):", className="fw-bold"),
                            dbc.Input(
                                id="detail-load-concentration",
                                type="number",
                                value=exp.load_concentration or "",
                                className="mb-3"
                            ),
                        ], width=4),
                        dbc.Col([
                            dbc.Label("Load Volume (mL):", className="fw-bold"),
                            dbc.Input(
                                id="detail-load-volume",
                                type="number",
                                value=exp.load_volume or "",
                                className="mb-3"
                            ),
                        ], width=4),
                        dbc.Col([
                            dbc.Label("Load Mass (mg):", className="fw-bold"),
                            dbc.Input(
                                id="detail-load-mass",
                                type="number",
                                value=exp.load_mass or "",
                                readonly=True,
                                className="mb-3 bg-light"
                            ),
                        ], width=4),
                    ]),
                ])
            ], className="mb-4"),

            # Process Settings Section
            dbc.Card([
                dbc.CardHeader([
                    html.H5([
                        html.I(className="fas fa-cogs me-2"),
                        "Process Settings"
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Target Diafiltration Concentration:", className="fw-bold"),
                            dbc.Input(
                                id="detail-uf1-target",
                                type="number",
                                value=exp.target_diafiltration_concentration or "",
                                className="mb-3"
                            ),
                        ], width=6),
                        dbc.Col([
                            dbc.Label("UF1 Target Reservoir Mass (g):", className="fw-bold"),
                            dbc.Input(
                                id="detail-uf1-mass",
                                type="number",
                                value=exp.uf1_target_reservoir_mass or "",
                                readonly=True,
                                className="mb-3 bg-light"
                            ),
                        ], width=6),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("# Diavolumes:", className="fw-bold"),
                            dbc.Input(
                                id="detail-diavolumes",
                                type="number",
                                value=exp.diavolumes or "",
                                className="mb-3"
                            ),
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Permeate Target Mass (g):", className="fw-bold"),
                            dbc.Input(
                                id="detail-permeate-mass",
                                type="number",
                                value=exp.permeate_target_mass or "",
                                readonly=True,
                                className="mb-3 bg-light"
                            ),
                        ], width=6),
                    ]),
                ])
            ], className="mb-4"),

            # Filtration Settings Section
            dbc.Card([
                dbc.CardHeader([
                    html.H5([
                        html.I(className="fas fa-filter me-2"),
                        "Filtration Settings"
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("LMH Target:", className="fw-bold"),
                            dbc.Input(
                                id="detail-lmh-target",
                                type="number",
                                value=exp.lmh_target or "",
                                className="mb-3"
                            ),
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Target Flow Rate (mL/min):", className="fw-bold"),
                            dbc.Input(
                                id="detail-target-flow-rate",
                                type="number",
                                value=exp.target_flow_rate or "",
                                readonly=True,
                                className="mb-3 bg-light"
                            ),
                        ], width=6),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Target P2500 Setpoint (%):", className="fw-bold"),
                            dbc.Input(
                                id="detail-p2500-setpoint",
                                type="number",
                                value=exp.target_p2500_setpoint or "",
                                readonly=True,
                                className="mb-3 bg-light"
                            ),
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Target P3000 Setpoint:", className="fw-bold"),
                            dbc.Input(
                                id="detail-p3000-setpoint",
                                type="number",
                                value=exp.target_p3000_setpoint or "",
                                readonly=True,
                                className="mb-3 bg-light"
                            ),
                        ], width=6),
                    ]),
                ])
            ], className="mb-4"),

            # Final Results Section
            dbc.Card([
                dbc.CardHeader([
                    html.H5([
                        html.I(className="fas fa-chart-bar me-2"),
                        "Final Results"
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Final Volume (mL):", className="fw-bold"),
                            dbc.Input(
                                id="detail-final-volume",
                                type="number",
                                value=exp.final_volume or "",
                                className="mb-3"
                            ),
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Final Concentration (mg/mL):", className="fw-bold"),
                            dbc.Input(
                                id="detail-final-concentration",
                                type="number",
                                value=exp.final_concentration or "",
                                className="mb-3"
                            ),
                        ], width=6),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Product Mass (mg):", className="fw-bold"),
                            dbc.Input(
                                id="detail-product-mass",
                                type="number",
                                value=exp.product_mass or "",
                                readonly=True,
                                className="mb-3 bg-light"
                            ),
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Yield (%):", className="fw-bold"),
                            dbc.Input(
                                id="detail-yield",
                                type="number",
                                value=exp.yield_percentage or "",
                                readonly=True,
                                className="mb-3 bg-light"
                            ),
                        ], width=6),
                    ]),
                ])
            ], className="mb-4"),

            # Update Button
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-save me-2"), "Update Experiment"],
                        id="update-experiment-btn",
                        color="success",
                        size="lg",
                        className="w-100"
                    ),
                    html.Div(id="update-status", className="mt-3")
                ])
            ])
        ])
        
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
        print(f"DEBUG: Fetching experiment with ID: {selected_experiment_id}")
        experiment = UFDFMetadata.objects.get(result_id=selected_experiment_id)
        print(f"DEBUG: Found experiment: {experiment.experiment_name}")

        # First, let's check what fields are actually available in the model
        print("DEBUG: Checking SartoflowTimeSeriesData fields...")
        sample_record = SartoflowTimeSeriesData.objects.filter(
            result_id=selected_experiment_id
        ).first()

        if sample_record:
            print(f"DEBUG: Sample record fields: {[f.name for f in sample_record._meta.fields]}")
            print(f"DEBUG: Sample record process_time value: {getattr(sample_record, 'process_time', 'FIELD NOT FOUND')}")
        else:
            print(f"DEBUG: No records found for experiment ID {selected_experiment_id}")

        # Query all time series data for this experiment, ordered by unit_step and process_time
        # Handle NULL process_time values by filtering them out or ordering nulls last
        print("DEBUG: Querying time series data...")
        query_set = SartoflowTimeSeriesData.objects.filter(
            result_id=selected_experiment_id
        )

        print(f"DEBUG: Found {query_set.count()} records")

        # Check for process_time field existence and NULL values
        null_count = query_set.filter(process_time__isnull=True).count()
        print(f"DEBUG: Records with NULL process_time: {null_count}")

        # Filter out NULL process_time values
        query_set = query_set.filter(process_time__isnull=False).values().order_by('unit_step', 'process_time')

        print(f"DEBUG: After filtering NULLs: {len(query_set)} records")

        df = pd.DataFrame.from_records(query_set)

        if not df.empty:
            print(f"DEBUG: DataFrame columns: {df.columns.tolist()}")
            print(f"DEBUG: DataFrame shape: {df.shape}")

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
            print(f"ERROR: 'process_time' not in DataFrame columns")
            print(f"DEBUG: Available columns: {df.columns.tolist()}")
            return go.Figure().add_annotation(
                text="process_time column not found in data",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font={"size": 16, "color": "#dc3545"}
            ).update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False}
            )

        print(f"DEBUG: process_time column found. Data type: {df['process_time'].dtype}")
        print(f"DEBUG: process_time first 5 values: {df['process_time'].head().tolist()}")
        print(f"DEBUG: process_time NaN count: {df['process_time'].isna().sum()}")

        # Create consecutive time series by adjusting process times for each step
        combined_df = pd.DataFrame()
        cumulative_time_offset = 0

        # Step type mapping for display
        step_names = {1: "UF1", 2: "UF2", 3: "DF1", 4: "DF2", 5: "Rinse"}

        unit_steps = sorted([x for x in df['unit_step'].unique() if pd.notna(x)])
        print(f"DEBUG: Starting to process {len(unit_steps)} unit steps")
        print(f"DEBUG: Unit steps available: {unit_steps}")

        if not unit_steps:
            print("DEBUG: No valid unit steps found, using original dataframe")
            df['step_name'] = "Unknown Step"
            combined_df = df.copy()
        else:
            for unit_step in unit_steps:
                step_data = df[df['unit_step'] == unit_step].copy()
                print(f"DEBUG: Processing unit_step {unit_step}: {len(step_data)} records")

                # Reset process time to start from the cumulative offset
                if not step_data.empty:
                    step_min_time = step_data['process_time'].min()
                    step_data['process_time'] = step_data['process_time'] - step_min_time + cumulative_time_offset
                    step_data['step_name'] = step_names.get(unit_step, f"Step {unit_step}")

                    print(f"DEBUG: Step {unit_step} - process_time range: {step_data['process_time'].min():.4f} to {step_data['process_time'].max():.4f}")

                    # Update cumulative offset for next step
                    cumulative_time_offset = step_data['process_time'].max() + 0.1  # Small gap between steps

                    if combined_df.empty:
                        combined_df = step_data.copy()
                        print(f"DEBUG: Initialized combined_df with {len(combined_df)} records")
                    else:
                        combined_df = pd.concat([combined_df, step_data], ignore_index=True)
                        print(f"DEBUG: After concat, combined_df has {len(combined_df)} records")

        print(f"DEBUG: Final combined_df shape: {combined_df.shape}")
        print(f"DEBUG: Final combined_df columns: {combined_df.columns.tolist()}")

        if 'process_time' not in combined_df.columns:
            print(f"ERROR: process_time column missing from combined_df!")
            print(f"DEBUG: Available columns: {combined_df.columns.tolist()}")
            return go.Figure().add_annotation(
                text="Error: process_time column missing after data processing",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font={"size": 16, "color": "#dc3545"}
            )

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

        # Convert selected columns to lowercase for comparison (but preserve case in data access)
        selected_columns_lower = [col.lower() if isinstance(col, str) else col for col in selected_columns]

        print(f"DEBUG: Selected columns for plotting: {selected_columns_lower}")
        print(f"DEBUG: Available DataFrame columns: {df.columns.tolist()}")

        fig = go.Figure()
        axis_map = {}
        y_axis_count = 1

        for column in selected_columns_lower:
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

        for i, column in enumerate(selected_columns_lower, start=1):
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
        for i, column in enumerate(selected_columns_lower[1:], start=2):
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
        print(f"DEBUG: UFDFMetadata.DoesNotExist for ID: {selected_experiment_id}")
        return go.Figure().add_annotation(
            text="Experiment not found",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    except KeyError as e:
        print(f"ERROR: KeyError in update_graph: {e}")
        print(f"DEBUG: Missing key: {str(e)}")
        import traceback
        traceback.print_exc()
        return go.Figure().add_annotation(
            text=f"Data format error: Missing field '{str(e)}'",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font={"size": 14, "color": "#dc3545"}
        )
    except Exception as e:
        print(f"ERROR: General exception in update_graph: {e}")
        print(f"DEBUG: Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return go.Figure().add_annotation(
            text=f"Error loading data: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font={"size": 14, "color": "#dc3545"}
        )


@app.callback(
    Output("import-modal", "is_open"),
    [Input("open-modal-btn", "n_clicks"), Input("cancel-select-btn", "n_clicks"), Input("select-experiment-btn", "n_clicks")],
    [State("import-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_modal(open_clicks, cancel_clicks, select_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "open-modal-btn":
        return True
    else:
        return False

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
        return dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            "Experiment updated successfully!"
        ], color="success", dismissable=True, duration=4000)

    except UFDFMetadata.DoesNotExist:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Error: Experiment not found"
        ], color="danger", dismissable=True)
    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error updating experiment: {str(e)}"
        ], color="danger", dismissable=True)