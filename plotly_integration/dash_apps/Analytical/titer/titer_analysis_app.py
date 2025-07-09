import plotly.graph_objects as go
from plotly.subplots import make_subplots
from django_plotly_dash import DjangoDash
import dash
from dash import dcc, html, Input, Output, State, dash_table, Dash, MATCH, callback_context
import pandas as pd
from scipy.stats import linregress, t
from plotly_integration.models import Report, SampleMetadata, PeakResults, TimeSeriesData
import json
import logging
from openpyxl.workbook import Workbook
from collections import Counter
from django.db.models import F, ExpressionWrapper, fields
from datetime import datetime, timedelta
import re
import numpy as np
from collections import Counter
from collections import defaultdict
from datetime import timedelta

# Logging Configuration
logging.basicConfig(filename='app_logs.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the Dash app
app = DjangoDash('TiterAnalysisApp')


# Layout for the Dash app
app.layout = html.Div([

    dcc.Store(id='selected-report', data=None),
    dcc.Store(id='selected-report-2', data=None),
    dcc.Store(id="std-result-id-store"),
    dcc.Store(id='regression-parameters', data={"slope": 0,
                                                "intercept": 0,
                                                "std_err": 0,
                                                "t_score": 0,
                                                "n": 0,
                                                "mean_x": 0,
                                                "sum_x_sq": 0
                                                }),
    dcc.Store(id='result-table-store', data=[]),
    dcc.Store(id='report-list-store', data=[]),
    dcc.Interval(id="load-once", interval=1000, n_intervals=0, max_intervals=1),

    # # 🔹 Top-left Home Button
    # html.Div(
    #     html.Button("Home", id="home-btn", style={
    #         'background-color': '#0056b3',
    #         'color': 'white',
    #         'border': 'none',
    #         'padding': '10px 20px',
    #         'font-size': '16px',
    #         'cursor': 'pointer',
    #         'border-radius': '5px'
    #     }),
    #     style={'margin': '10px'}
    # ),

    html.Div([  # Main layout with sidebar and content areas


        html.Div([  # Main content container
            dcc.Tabs(id="main-tabs", value="tab-1", children=[

                dcc.Tab(label="Select Report", value="tab-1", children=[
                    html.Div([
                        html.H4("Select a Report", style={'textAlign': 'center', 'color': '#0056b3'}),
                        dash_table.DataTable(
                            id='report-selection-table',
                            columns=[
                                {"name": "Report ID", "id": "report_id"},
                                {"name": "Report Name", "id": "report_name"},
                                {"name": "Project ID", "id": "project_id"},
                                {"name": "Created By", "id": "user_id"},
                                {"name": "Date Created", "id": "date_created"},
                            ],
                            row_selectable="single",
                            filter_action="native",
                            sort_action="native",
                            page_action="native",
                            page_size=25,
                            fixed_rows={'headers': True},
                            style_table={'overflowX': 'auto'},
                            style_cell={
                                'textAlign': 'center',
                                'padding': '5px',
                                'minWidth': '100px',
                                'maxWidth': '180px',
                                'whiteSpace': 'normal'
                            },

                        )
                    ], style={
                        'width': '98%',
                        'margin': 'auto',
                        'padding': '10px',
                        'border': '2px solid #0056b3',
                        'border-radius': '5px',
                        'background-color': '#f7f9fc',
                        'margin-bottom': '10px'
                    })
                ]),

                # 🔹 Tab 1: Sample Analysis
                dcc.Tab(label="Sample Analysis", value="tab-2", children=[
                    html.Div([
                        html.Div(  # Plot area (90% width)
                            id='plot-area',
                            children=[
                                html.H4("Titer Results", id="results-header",
                                        style={'text-align': 'center', 'color': '#0056b3'}),
                                dcc.Graph(id='time-series-graph')
                            ],
                            style={
                                'width': '98%',  # ✅ Increased width to 90%
                                'margin': 'auto',
                                'padding': '10px',
                                'border': '2px solid #0056b3',
                                'border-radius': '5px',
                                'background-color': '#f7f9fc',
                                'margin-bottom': '10px'
                            }
                        ),

                        html.Div(  # ✅ Plot settings moved below plot
                            id='plot-settings',
                            children=[
                                html.H4("Plot Settings", style={'color': '#0056b3', 'text-align': 'center'}),
                                dcc.RadioItems(  # ✅ Horizontal layout for radio buttons
                                    id='channel-radio',
                                    options=[
                                        {'label': 'UV280', 'value': 'channel_1'},
                                        {'label': 'UV260', 'value': 'channel_2'},
                                        {'label': 'Pressure', 'value': 'channel_3'}
                                    ],
                                    value='channel_1',  # Default selection
                                    labelStyle={'display': 'inline-block', 'margin-right': '15px'}
                                    # ✅ Horizontal layout
                                ),
                                dcc.Dropdown(
                                    id='plot-type-dropdown',
                                    options=[
                                        {'label': 'Plotly Graph', 'value': 'plotly'},
                                        {'label': 'Subplots', 'value': 'subplots'}
                                    ],
                                    value='plotly',
                                    style={'width': '100%', 'margin-top': '10px'}
                                ),
                            ],
                            style={
                                'width': '98%',  # ✅ Increased width to 90%
                                'margin': 'auto',
                                'padding': '10px',
                                'background-color': '#f7f9fc',
                                'border': '2px solid #0056b3',
                                'border-radius': '5px',
                                'margin-bottom': '10px'
                            }
                        ),

                        html.Div(  # Titer Data Table
                            id='titer-data',
                            children=[
                                html.H4("Titer Results", style={'text-align': 'center', 'color': '#0056b3'}),
                                dash_table.DataTable(
                                    id='result-table',
                                    columns=[
                                        {"name": "Sample Name", "id": "Sample Name"},
                                        {"name": "Dilution Factor", "id": "Dilution Factor"},
                                        {"name": "Peak Start", "id": "Peak Start"},
                                        {"name": "Peak End", "id": "Peak End"},
                                        {"name": "Main Peak Area", "id": "Main Peak Area"},
                                        {"name": "Concentration (mg/mL)", "id": "Concentration"},
                                        {"name": "Uncertainty", "id": "Uncertainty"},
                                        {"name": "Injection Volume (uL)", "id": "Injection Volume"}
                                    ],
                                    data=[],
                                    # row_selectable="single",  # ✅ Changed to single row selection
                                    # selected_rows=[],
                                    sort_action="native",
                                    style_table={'overflowX': 'auto'},
                                    style_cell={'textAlign': 'center', 'padding': '5px'},
                                    style_header={'fontWeight': 'bold', 'backgroundColor': '#e9f1fb'}
                                ),
                                html.Button("Export to XLSX", id="export-button", style={  # ✅ Added back export button
                                    'margin-top': '10px',
                                    'background-color': '#0047b3',
                                    'color': 'white',
                                    'padding': '10px',
                                    'border': 'none',
                                    'border-radius': '5px',
                                    'cursor': 'pointer'
                                }),
                                dcc.Download(id="download-result-data")
                            ],
                            style={
                                'width': '98%',  # ✅ Increased width to 90%
                                'margin': 'auto',
                                'padding': '10px',
                                'border': '2px solid #0056b3',
                                'border-radius': '5px',
                                'background-color': '#f7f9fc'
                            }
                        ),
                    ])
                ]),
                # 🔹 Tab 2: Standard Analysis
                dcc.Tab(label="Standard Analysis", value="tab-3", children=[
                    html.Div(
                        id='standard-analysis',
                        children=[
                            html.H4("Standard Analysis", style={'text-align': 'center', 'color': '#0056b3'}),
                            dcc.Graph(id='standard-plot', style={'margin-top': '10px'}),

                            html.Div(
                                id='standard-analysis-content',
                                children=[
                                    dcc.Graph(id='regression-plot', style={'margin-top': '20px'}),
                                    dash_table.DataTable(
                                        id="standard-table",
                                        columns=[
                                            {"name": "Sample Name", "id": "Sample Name"},
                                            {"name": "Injection Date", "id": "Injection Date"},
                                            {"name": "Peak Start", "id": "Peak Start"},
                                            {"name": "Peak End", "id": "Peak End"},
                                            {"name": "Peak Area", "id": "Main Peak Area"},
                                            {"name": "Concentration (mg/mL)", "id": "Concentration (mg/mL)"},
                                            {"name": "Injection Volume (uL)", "id": "Injection Volume (uL)"}
                                        ],
                                        data=[],
                                        row_selectable='multi',
                                        selected_rows=[],
                                        style_table={'overflowX': 'auto'},
                                        style_cell={'textAlign': 'center', 'padding': '5px'},
                                        style_header={'fontWeight': 'bold', 'backgroundColor': '#e9f1fb'}
                                    )
                                ],
                                style={
                                    'padding': '10px',
                                    'border': '2px solid #0056b3',
                                    'border-radius': '5px',
                                    'background-color': '#f7f9fc',
                                }
                            ),

                            html.P("Regression Equation: ", id="regression-equation"),
                            html.P("R² Value: ", id="r-squared-value"),
                        ],
                        style={
                            'width': '95%',
                            'margin-top': '20px',
                            'padding': '10px',
                            'border': '2px solid #0056b3',
                            'border-radius': '5px',
                            'background-color': '#f7f9fc'
                        }
                    )
                ])
            ])
        ], style={'width': '95%', 'padding': '10px', 'overflow-y': 'auto'})
    ], style={'display': 'flex', 'flex-direction': 'row', 'gap': '10px'})
])


@app.callback(
    Output("report-selection-table", "data"),
    Input("load-once", "n_intervals")
)
def populate_report_table(active_tab):
    reports = Report.objects.filter(analysis_type=2).order_by('-date_created').values(
        "report_id", "report_name", "project_id", "user_id", "date_created"
    )
    data = []
    for report in reports:
        date = report["date_created"]
        date_str = date.strftime("%Y-%m-%d %H:%M:%S") if date else "N/A"
        data.append({
            "report_id": report["report_id"],
            "report_name": report["report_name"],
            "project_id": report["project_id"],
            "user_id": report["user_id"] or "N/A",
            "date_created": date_str
        })
    return data


@app.callback(
    Output("selected-report", "data"),
    Input("report-selection-table", "selected_rows"),
    State("report-selection-table", "data"),
    prevent_initial_call=True
)
def store_selected_report(selected_rows, table_data):
    if not selected_rows:
        return dash.no_update
    selected_row = table_data[selected_rows[0]]
    return selected_row["report_id"]

# @app.callback(
#     Output("report-selection-table", "selected_rows"),
#     Input("report-selection-table", "data"),
#     prevent_initial_call=True
# )
# def auto_select_first_row(data):
#     # Only trigger on first table load
#     if data and len(data) > 0:
#         return [0]
#     return []


@app.callback(
    Output("results-header", "children"),  # Update the SEC Results header
    [Input("selected-report", "data")],
    prevent_initial_call=True
)
def update_results_header(selected_report):
    report_name = selected_report

    if not report_name:
        print("🚨 No report selected.")
        return go.Figure()

    # ✅ Retrieve selected report
    report = Report.objects.filter(report_id=report_name).first()

    if not report:
        return "Report Not Found"

    # Format the SEC Results text
    return f"{report.project_id} - {report.report_name}"


@app.callback(
    Output("sample-details-table", "data"),
    Input("selected-report", "data"),
    prevent_initial_call=True
)
def update_sample_and_std_details(selected_report):
    # Default table data
    default_data = [
        {"field": "Sample Set Name", "value": ""},
        {"field": "Column Name", "value": ""},
        {"field": "Column Serial Number", "value": ""},
        {"field": "System Name", "value": ""},
        {"field": "Instrument Method Name", "value": ""},
    ]

    report_name = selected_report

    if not report_name:
        print("🚨 No report selected.")
        return go.Figure()

    # ✅ Retrieve selected report
    report = Report.objects.filter(report_id=report_name).first()

    if not report:
        return default_data

    # Fetch the first sample name from the report's selected samples
    selected_result_ids = [sample.strip() for sample in report.selected_result_ids.split(",") if sample.strip()]
    if not selected_result_ids:
        return default_data

    first_sample_name = selected_result_ids[0]
    sample_metadata = SampleMetadata.objects.filter(result_id=first_sample_name).first()

    if not sample_metadata:
        return default_data

    # Extract details from the `SampleMetadata` model
    sample_set_name = sample_metadata.sample_set_name or "N/A"
    column_name = sample_metadata.column_name or "N/A"
    column_serial_number = sample_metadata.column_serial_number or "N/A"
    system_name = sample_metadata.system_name or "N/A"
    instrument_method_name = sample_metadata.instrument_method_name or "N/A"

    # Return table data
    return [
        {"field": "Sample Set Name", "value": sample_set_name},
        {"field": "Column Name", "value": column_name},
        {"field": "Column Serial Number", "value": column_serial_number},
        {"field": "System Name", "value": system_name},
        {"field": "Instrument Method Name", "value": instrument_method_name},
    ]


def extract_concentration(sample_name):
    """Extracts concentration from sample names formatted as '130E7 Std_x'."""
    match = re.search(r"Std_([\d\.]+)", sample_name)
    return float(match.group(1)) if match else None


@app.callback(
    Output("standard-plot", "figure"),  # ✅ Time series data for standards
    [
        Input("selected-report", "data")  # ✅ Trigger on report click
    ],
    [State("selected-report", "data")],  # ✅ Use the stored selected report
    prevent_initial_call=True
)
def plot_standard_time_series(report_clicks, selected_report):
    """Fetch time series data for standard samples in the selected report and plot it."""
    report_name = selected_report

    if not report_name:
        print("🚨 No report selected.")
        return go.Figure()

    # ✅ Retrieve selected report
    report = Report.objects.filter(report_id=report_name).first()

    if not report:
        print(f"🚨 Report not found: {report_name}")
        return go.Figure()

    # ✅ Extract samples from the selected report
    selected_samples = [s.strip() for s in report.selected_samples.split(",") if s.strip()]

    if not selected_samples:
        print(f"🚨 No samples found in report: {report_name}")
        return go.Figure()

    print(f"✅ Selected Report: {report_name}")
    print(f"📢 Found Samples: {selected_samples}")

    # ✅ Extract standard samples from the selected report
    result_ids = [r.strip() for r in report.selected_result_ids.split(",") if r.strip()]

    # Step 1: Retrieve sample_set_ids associated with these result_ids
    sample_set_ids = SampleMetadata.objects.filter(result_id__in=result_ids).values_list("sample_set_id",
                                                                                         flat=True).distinct()

    # Step 2: Filter standard samples within the identified sample_set_ids
    std_samples = SampleMetadata.objects.filter(
        sample_set_id__in=sample_set_ids,
        sample_name__contains="Std_"
    ).values("sample_name", "injection_volume", "result_id")

    # ✅ If enough found, skip fallback
    if len(std_samples) < 3:
        # ✅ Step 1: Use project_id from report (drop "SI-" prefix)
        project_prefix = report.project_id.replace("SI-", "")

        # ✅ Step 2: Get median acquisition time for report samples
        sample_times = SampleMetadata.objects.filter(
            result_id__in=result_ids
        ).values_list("date_acquired", flat=True)

        if sample_times:
            median_time = sorted(sample_times)[len(sample_times) // 2]

            # ✅ Step 3: Query fallback standard samples by project
            candidate_stds = SampleMetadata.objects.filter(
                sample_name__startswith=project_prefix,
                sample_name__contains="Std_"
            ).exclude(date_acquired__isnull=True).values(
                "sample_name", "injection_volume", "result_id", "sample_set_id", "date_acquired"
            )

            # ✅ Step 4: Group by sample_set_id and find closest in time
            grouped_by_set = defaultdict(list)
            for std in candidate_stds:
                grouped_by_set[std["sample_set_id"]].append(std)

            best_group = None
            best_time_diff = timedelta.max

            for sample_set_id, group in grouped_by_set.items():
                if len(group) < 3:
                    continue
                group_times = [std["date_acquired"] for std in group]
                group_median = sorted(group_times)[len(group_times) // 2]
                time_diff = abs(group_median - median_time)
                if time_diff < best_time_diff:
                    best_time_diff = time_diff
                    best_group = group

            std_samples = best_group if best_group else []

    if not std_samples:
        print(f"🚨 No standard samples found in report: {report_name}")
        return go.Figure()

    print(f"✅ Found Standard Samples: {[s['sample_name'] for s in std_samples]}")

    # ✅ Initialize Plotly Figure
    fig = go.Figure()

    # ✅ Retrieve Time Series Data for Each Standard Sample
    for std in std_samples:
        result_id = std["result_id"]
        sample_name = std["sample_name"]

        # ✅ Fetch Time Series Data from `TimeSeriesData`
        time_series = TimeSeriesData.objects.filter(result_id=result_id).values("time", "channel_1")

        df = pd.DataFrame(list(time_series))  # Convert to DataFrame

        if df.empty:
            print(f"⚠️ No Time Series Data for: {sample_name}")
            continue

        # ✅ Add Trace to the Plot
        fig.add_trace(go.Scatter(
            x=df["time"],
            y=df["channel_1"],
            mode="lines",
            name=sample_name
        ))

    # ✅ Update Plot Layout
    fig.update_layout(
        title="Time Series Data for Standards",
        xaxis_title="Time",
        yaxis_title="Signal Intensity",
        template="plotly_white"
    )

    return fig


@app.callback(
    [
        Output("standard-table", "data"),  # ✅ Populate the table
        Output("standard-table", "selected_rows")  # ✅ Default: Select first 5 rows
    ],
    [
        Input("selected-report", "data")  # ✅ Trigger on report selection
    ],
    [State("selected-report", "data")],  # ✅ Use stored selected report
    prevent_initial_call=True
)
def update_standard_table(report_clicks, selected_report):
    """Populate standard-table when a report is selected, and set default selected rows."""
    report_name = selected_report

    if not report_name:
        return [], []

    # ✅ Retrieve selected report
    report = Report.objects.filter(report_id=report_name).first()
    if not report:
        return [], []

    # ✅ Extract standard samples from the selected report
    result_ids = [r.strip() for r in report.selected_result_ids.split(",") if r.strip()]

    # Step 1: Retrieve sample_set_ids associated with these result_ids
    sample_set_ids = SampleMetadata.objects.filter(result_id__in=result_ids).values_list("sample_set_id",
                                                                                         flat=True).distinct()

    # Step 2: Filter standard samples within the identified sample_set_ids
    std_samples = SampleMetadata.objects.filter(
        sample_set_id__in=sample_set_ids,
        sample_name__contains="Std_"
    ).values("sample_name", "injection_volume", "result_id", "date_acquired")

    # ✅ If enough found, skip fallback
    if len(std_samples) < 3:
        # ✅ Step 1: Use project_id from report (drop "SI-" prefix)
        project_prefix = report.project_id.replace("SI-", "")

        # ✅ Step 2: Get median acquisition time for report samples
        sample_times = SampleMetadata.objects.filter(
            result_id__in=result_ids
        ).values_list("date_acquired", flat=True)

        if sample_times:
            median_time = sorted(sample_times)[len(sample_times) // 2]

            # ✅ Step 3: Query fallback standard samples by project
            candidate_stds = SampleMetadata.objects.filter(
                sample_name__startswith=project_prefix,
                sample_name__contains="Std_"
            ).exclude(date_acquired__isnull=True).values(
                "sample_name", "injection_volume", "result_id", "sample_set_id", "date_acquired"
            )

            # ✅ Step 4: Group by sample_set_id and find closest in time
            grouped_by_set = defaultdict(list)
            for std in candidate_stds:
                grouped_by_set[std["sample_set_id"]].append(std)

            best_group = None
            best_time_diff = timedelta.max

            for sample_set_id, group in grouped_by_set.items():
                if len(group) < 3:
                    continue
                group_times = [std["date_acquired"] for std in group]
                group_median = sorted(group_times)[len(group_times) // 2]
                time_diff = abs(group_median - median_time)
                if time_diff < best_time_diff:
                    best_time_diff = time_diff
                    best_group = group

            std_samples = best_group if best_group else []

    if not std_samples:
        return [], []

    table_data = []
    for std in std_samples:
        concentration = extract_concentration(std["sample_name"])
        injection_volume = std["injection_volume"]
        result_id = std["result_id"]

        dt = std["date_acquired"]
        # Convert to datetime object and remove timezone
        dt = dt.replace(tzinfo=None)
        # Format to readable string
        injection_date = dt.strftime("%b %d, %Y %I:%M %p")  # e.g., "Apr 10, 2025 09:41 PM"

        # ✅ Fetch Peak Area, Peak Start, and Peak End from PeakResults Table
        peak_result = (PeakResults.objects.filter(result_id=result_id).order_by("-height")
                       .values("area", "peak_start_time", "peak_end_time").first())

        peak_area = peak_result["area"] if peak_result else None
        peak_start = peak_result["peak_start_time"] if peak_result else None
        peak_end = peak_result["peak_end_time"] if peak_result else None

        if concentration and peak_area:
            table_data.append({
                "Sample Name": std["sample_name"],
                "Injection Date": injection_date,
                "Peak Start": peak_start,
                "Peak End": peak_end,
                "Main Peak Area": peak_area,
                "Concentration (mg/mL)": concentration,
                "Injection Volume (uL)": injection_volume
            })

    # ✅ Sort table by concentration (lowest to highest)
    table_data = sorted(table_data, key=lambda x: x["Concentration (mg/mL)"])

    # ✅ Select all rows by default
    selected_rows = list(range(len(table_data)))  # ✅ Select all rows

    return table_data, selected_rows


@app.callback(
    [
        Output("regression-equation", "children"),
        Output("r-squared-value", "children"),
        Output("regression-plot", "figure"),  # ✅ Regression Plot
        Output("regression-parameters", "data")  # Store slope & intercept for calculations
    ],
    [
        Input("standard-table", "selected_rows")  # ✅ Trigger on row selection
    ],
    [
        State("standard-table", "data")  # ✅ Use existing table data
    ],
    prevent_initial_call=True
)
def update_regression_plot(selected_rows, table_data):
    """Update regression plot based on selected rows from the standard-table."""

    if not table_data or not selected_rows:
        return "No Standard Data Selected", "N/A", go.Figure(), {"slope": None, "intercept": None}

    # ✅ Filter selected rows
    selected_data = [table_data[i] for i in selected_rows if i < len(table_data)]
    selected_df = pd.DataFrame(selected_data)

    if selected_df.empty:
        return "No Standard Data Selected", "N/A", go.Figure(), {"slope": None, "intercept": None}

    # ✅ Extract x (concentration) and y (peak area)
    concentrations = selected_df["Concentration (mg/mL)"].astype(float)
    peak_areas = selected_df["Main Peak Area"].astype(float)

    # ✅ Perform Linear Regression
    try:
        slope, intercept, r_value, _, std_err = linregress(concentrations, peak_areas)  # ✅ std_err = standard deviation
    except Exception as e:
        print(f"Regression error: {e}")
        return "Regression Failed", "N/A", go.Figure(), {"slope": None, "intercept": None, "std_dev": None}

    # ✅ Generate Regression Line
    x_vals = np.linspace(concentrations.min(), concentrations.max(), 100)
    y_vals = slope * x_vals + intercept

    # ✅ Compute Prediction Interval

    n = len(concentrations)  # Number of data points
    mean_x = np.mean(concentrations)
    sum_x_sq = np.sum((concentrations - mean_x) ** 2)

    # ✅ t-score for 95% confidence
    t_score = t.ppf(0.975, df=n - 2)  # Two-tailed 95% confidence

    print(std_err)
    print(n)
    print(mean_x)
    print(sum_x_sq)

    # ✅ Create Plotly Figure for Regression
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=concentrations,
        y=peak_areas,
        mode="markers",
        name="Standard Data",
        marker=dict(size=8, color="blue")
    ))
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="lines",
        name="Regression Line",
        line=dict(color="red", dash="dash")
    ))

    # ✅ Add annotations for each data point
    for i, (x, y) in enumerate(zip(concentrations, peak_areas)):
        fig.add_annotation(
            x=x, y=y,
            text=f"{x:.3f} mg/mL",
            showarrow=True,
            arrowhead=2,
            ax=0, ay=-20
        )

    fig.update_layout(
        title="Regression Analysis: Concentration vs Peak Area",
        xaxis_title="Concentration (mg/mL)",
        yaxis_title="Peak Area",
        template="plotly_white"
    )

    return (
        f"y = {slope:.4f}x + {intercept:.4f}",
        f"R² = {r_value ** 2:.4f}",
        fig,  # ✅ Regression plot updates dynamically
        {"slope": slope,
         "intercept": intercept,
         "std_err": std_err,
         "t_score": t_score,
         "n": n,
         "mean_x": mean_x,
         "sum_x_sq": sum_x_sq
         }
    )


@app.callback(
    [
        Output("result-table", "columns"),  # ✅ Table column structure
        Output("result-table", "data")  # ✅ Populate the result table
    ],
    [
        Input("selected-report", "data"),  # ✅ Trigger on report selection
        Input("regression-parameters", "data")  # ✅ Trigger when regression parameters change
    ],
    [State("selected-report", "data")],  # ✅ Use stored selected report
    prevent_initial_call=True
)
def update_result_table(report_clicks, regression_params, selected_report):
    """Populate result-table with all report samples and update calculated concentrations using regression parameters."""
    report_name = selected_report

    if not report_name:
        print("⚠️ No report found or selected. Returning empty table.")
        return [], [], None

    # ✅ Retrieve selected report
    report = Report.objects.filter(report_id=report_name).first()
    if not report:
        print(f"⚠️ Report '{report_name}' not found in database.")
        return [], [], report_name

    # ✅ Extract all samples from the report
    all_samples = [s.strip() for s in report.selected_result_ids.split(",") if s.strip()]
    report_samples = SampleMetadata.objects.filter(result_id__in=all_samples).values(
        "sample_name", "injection_volume", "result_id", "system_name", "date_acquired"
    )

    if not report_samples:
        print(f"⚠️ No samples found in report '{report_name}'.")
        return [], [], report_name

    # ✅ Extract regression parameters
    slope = regression_params.get("slope")
    intercept = regression_params.get("intercept")
    std_err = regression_params.get("std_err")
    t_score = regression_params.get("t_score")
    n = regression_params.get("n")
    mean_x = regression_params.get("mean_x")
    sum_x_sq = regression_params.get("sum_x_sq")

    # ✅ Initialize result data list
    result_data = []

    for i, sample in enumerate(report_samples):
        sample_name = sample["sample_name"]
        injection_volume = sample["injection_volume"]
        result_id = sample["result_id"]
        system_name = sample["system_name"]
        date_acquired = sample["date_acquired"]
        dt = sample["date_acquired"]
        # Convert to datetime object and remove timezone
        dt = dt.replace(tzinfo=None)
        # Format to readable string
        injection_date = dt.strftime("%b %d, %Y %I:%M %p")  # e.g., "Apr 10, 2025 09:41 PM"

        # Retrieve the SampleMetadata instance for the given result_id
        sample_metadata = SampleMetadata.objects.filter(result_id=result_id).first()

        # Check if the instance exists and retrieve dilution, default to 1 if None
        dilution_factor = sample_metadata.dilution if sample_metadata and sample_metadata.dilution is not None else 1

        print(dilution_factor)  # ✅ Check the output

        # ✅ Fetch Peak Area, Peak Start, and Peak End from PeakResults Table, choosing the row with the largest peak height
        peak_result = PeakResults.objects.filter(result_id=result_id, channel_name='DAD.0.0').order_by(
            "-height").values(
            "area", "peak_start_time", "peak_end_time", "height").first()

        peak_area = peak_result["area"] if peak_result else None
        peak_start = peak_result["peak_start_time"] if peak_result else None
        peak_end = peak_result["peak_end_time"] if peak_result else None

        # ✅ Calculate concentration using regression parameters (if available)
        calculated_concentration = None
        uncertainty = None  # Prediction interval uncertainty

        if peak_area and slope is not None and intercept is not None:
            calculated_concentration = round(((peak_area - intercept) / slope) * dilution_factor, 3) if slope else None

            # ✅ Compute uncertainty using the prediction interval
            if calculated_concentration is not None and slope is not None and intercept is not None:
                # Use the correct prediction interval equation
                uncertainty = t_score * std_err * np.sqrt(
                    1 + (1 / n) + ((calculated_concentration - mean_x) ** 2 / sum_x_sq))

                # Convert peak area uncertainty into concentration uncertainty
                uncertainty /= abs(slope)  # ✅ Divide by the absolute slope

                # ✅ Round values for better display
                calculated_concentration = round(calculated_concentration, 3)
                uncertainty = round(uncertainty, 3)

        # ✅ Append sample to results table
        result_data.append({
            "Sample Name": sample_name,
            "System Name": system_name,
            "Injection Date": injection_date,
            "Dilution Factor": dilution_factor,
            "Peak Start": peak_start,
            "Peak End": peak_end,
            "Main Peak Area": peak_area,
            "Concentration (mg/mL)": calculated_concentration,
            "Uncertainty": f"{calculated_concentration:.3f} ± {uncertainty:.3f}" if calculated_concentration and uncertainty else None,
            "Injection Volume (uL)": injection_volume,
            "Result ID": result_id  # ✅ Store `Result ID` for sorting later
        })

    # ✅ Sort non-Std_ samples by `Result ID`, keeping `Std_` samples at the end
    result_data_sorted = sorted(
        result_data,
        key=lambda x: ("Std_" in x["Sample Name"], x["Result ID"])
    )

    # ✅ Define table columns dynamically
    table_columns = [
        {"name": "Sample Name", "id": "Sample Name"},
        {"name": "Injection Date", "id": "Injection Date"},
        {"name": "System Name", "id": "System Name"},
        {"name": "Dilution Factor", "id": "Dilution Factor"},
        {"name": "Peak Start", "id": "Peak Start"},
        {"name": "Peak End", "id": "Peak End"},
        {"name": "Main Peak Area", "id": "Main Peak Area"},
        {"name": "Concentration (mg/mL)", "id": "Concentration (mg/mL)"},
        {"name": "Uncertainty", "id": "Uncertainty"},
        {"name": "Injection Volume (uL)", "id": "Injection Volume (uL)"},
    ]

    return table_columns, result_data_sorted


@app.callback(
    [Output("download-result-data", "data")],
    [
        Input("export-button", "n_clicks"),
    ],
    [
        State("result-table", "data"),
        State('selected-report', 'data')
    ],  # Use the stored selected report
    prevent_initial_call=True
)
def export_to_xlsx(n_clicks, table_data, selected_report):
    if not table_data:
        return dash.no_update  # Do nothing if the table is empty

    report = Report.objects.filter(report_id=int(selected_report)).first()
    # print(report)
    # print(report.project_id)
    # print(report.report_name)

    if not report:
        return dash.no_update

    # Get current date
    current_date = datetime.now().strftime("%Y%m%d")

    # Build the file name
    file_name = f"{current_date}-{report.project_id}-{report.report_name}.xlsx"
    # print(file_name)

    # Convert table data to a pandas DataFrame
    df = pd.DataFrame(table_data)

    # Use Dash's `send_data_frame` to export the DataFrame as an XLSX file
    return [dcc.send_data_frame(df.to_excel, file_name, index=False)]


@app.callback(
    Output("time-series-graph", "figure"),  # ✅ Time series data for standards
    [
        Input("selected-report", "data")  # ✅ Trigger on report click
    ],
    [State("selected-report", "data")],  # ✅ Use the stored selected report
    prevent_initial_call=True
)
def plot_standard_time_series(report_clicks, selected_report):
    """Fetch time series data for standard samples in the selected report and plot it."""
    report_name = selected_report

    if not report_name:
        print("🚨 No report selected.")
        return go.Figure()

    # ✅ Retrieve selected report
    report = Report.objects.filter(report_id=report_name).first()

    if not report:
        print(f"🚨 Report not found: {report_name}")
        return go.Figure()

    # ✅ Extract standard samples from the selected report
    selected_samples = [s.strip() for s in report.selected_samples.split(",") if s.strip()]

    if not selected_samples:
        print(f"🚨 No samples found in report: {report_name}")
        return go.Figure()

    print(f"✅ Selected Report: {report_name}")
    print(f"📢 Found Samples: {selected_samples}")

    # ✅ Retrieve non-standard samples (Exclude "Std_") and sort by result_id
    non_std_samples = SampleMetadata.objects.filter(
        sample_name__in=selected_samples
    ).exclude(sample_name__contains="Std_").order_by("result_id")  # ✅ Sort by result_id

    if not non_std_samples:
        print(f"🚨 No samples found in report: {report_name}")
        return go.Figure()

    print(f"✅ Found Samples: {[s.sample_name for s in non_std_samples]}")

    # ✅ Initialize Plotly Figure
    fig = go.Figure()

    # ✅ Retrieve Time Series Data for Each Standard Sample
    for sample in non_std_samples:
        result_id = sample.result_id  # ✅ Correct way to access model attributes
        sample_name = sample.sample_name

        # ✅ Fetch Time Series Data from `TimeSeriesData`
        time_series = TimeSeriesData.objects.filter(result_id=result_id).values("time", "channel_1")

        df = pd.DataFrame(list(time_series))  # Convert to DataFrame

        if df.empty:
            print(f"⚠️ No Time Series Data for: {sample_name}")
            continue

        # ✅ Add Trace to the Plot
        fig.add_trace(go.Scatter(
            x=df["time"],
            y=df["channel_1"],
            mode="lines",
            name=sample_name
        ))

    # ✅ Update Plot Layout
    fig.update_layout(
        title="Time Series Data for Standards",
        xaxis_title="Time (min)",
        yaxis_title="UV280",
        template="plotly_white"
    )

    return fig
