import numpy as np
import dash
import plotly.graph_objects as go
from django_plotly_dash import DjangoDash
from dash import dcc, html, Input, Output, dash_table, State
import pandas as pd
from django.db.models import F
import logging
from plotly_integration.models import AktaResult, AktaChromatogram, AktaFraction, AktaRunLog
import dash_bootstrap_components as dbc
from urllib.parse import urlencode, parse_qs, urlparse
from scipy.signal import find_peaks

AXIS_LABELS = {
    "uv_1_280": "UV 280 nm (mAU)",
    "uv_2_0": "UV 2.0 (mAU)",
    "uv_3_0": "UV 3.0 (mAU)",
    "cond": "Conductivity (mS/cm)",
    "conc_b": "Concentration B (%)",
    "pH": "pH",
    "system_flow": "System Flow (mL/min)",
    "system_linear_flow": "System Linear Flow (cm/h)",
    "system_pressure": "System Pressure (bar)",
    "cond_temp": "Conductivity Temp (°C)",
    "sample_flow": "Sample Flow (mL/min)",
    "sample_linear_flow": "Sample Linear Flow (cm/h)",
    "sample_pressure": "Sample Pressure (bar)",
    "preC_pressure": "Pre-column Pressure (bar)",
    "deltaC_pressure": "Delta Column Pressure (bar)",
    "postC_pressure": "Post-column Pressure (bar)"
}

TABLE_STYLE_CELL = {
    "textAlign": "left",
    "padding": "8px 12px",
    "fontSize": "13px",
    "border": "1px solid #dee2e6",
    "minWidth": "120px",
    "width": "120px",
    "maxWidth": "120px",
    "overflow": "hidden",
    "textOverflow": "ellipsis",
    "fontFamily": "Arial, sans-serif",
    "color": "#333"
}

TABLE_STYLE_HEADER = {
    "backgroundColor": "#0056b3",
    "fontWeight": "600",
    "color": "white",
    "textAlign": "center",
    "fontSize": "13px",
    "padding": "12px",
    "fontFamily": "Arial, sans-serif",
    "border": "1px solid #0056b3"
}

TABLE_STYLE_TABLE = {
    "overflowX": "auto",
    "overflowY": "auto",
    "maxHeight": "400px",
    "border": "1px solid #dee2e6",
    "borderRadius": "8px",
    "fontFamily": "Arial, sans-serif"
}

logging.basicConfig(filename='akta_logs.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

app = DjangoDash("AktaChromatogramApp", external_stylesheets=[
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
    dbc.themes.BOOTSTRAP
])

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="active-tab-store", data="tab-1"),
    dcc.Store(id="selected-result-ids", data=[]),  # Store multiple IDs
    dcc.Store(id="embed-mode", data=False),  # Store embed mode state
    html.Div([  # Main content container
        # Tab container - will be hidden in embed mode
        html.Div(id="tab-container", children=[
            dcc.Tabs(id="main-tabs", value="tab-1",
                     style={
                         'height': '44px',
                         'borderBottom': '1px solid #d6d6d6'
                     },
                     children=[
                         # 🔹 Tab 1: Sample Analysis
                         dcc.Tab(label="Select Result", value="tab-1",
                                 style={
                                     'borderLeft': '1px solid #d6d6d6',
                                     'borderRight': '1px solid #d6d6d6',
                                     'borderTop': '1px solid #d6d6d6',
                                     'backgroundColor': '#f9f9f9',
                                     'color': '#333',
                                     'padding': '12px 24px',
                                     'fontFamily': 'Arial, sans-serif',
                                     'fontWeight': '500'
                                 },
                                 selected_style={
                                     'borderTop': '3px solid #0056b3',
                                     'borderLeft': '1px solid #d6d6d6',
                                     'borderRight': '1px solid #d6d6d6',
                                     'borderBottom': '1px solid #fff',
                                     'backgroundColor': '#fff',
                                     'color': '#0056b3',
                                     'padding': '12px 24px',
                                     'fontFamily': 'Arial, sans-serif',
                                     'fontWeight': '600'
                                 },
                                 children=[
                                     html.Div([
                                         dcc.Store(id="reset-save-akta-trigger", data=False),
                                         dcc.Interval(id="reset-save-akta-timer", interval=3000, n_intervals=0,
                                                      disabled=True),
                                         dbc.Row([
                                             dbc.Col(dbc.Button("🔄 Refresh", id="refresh-akta-table", color="primary",
                                                                size="sm"),
                                                     width="auto"),
                                             dbc.Col(
                                                 dbc.Button("💾 Save", id="save-akta-names", color="primary", size="sm"),
                                                 width="auto"),
                                             dbc.Col(html.Div(id="save-akta-status",
                                                              style={"fontSize": "11px", "marginTop": "5px"}),
                                                     width="auto"),
                                             dbc.Col(html.Div(id="selection-status",
                                                              style={"fontSize": "12px", "marginTop": "5px",
                                                                     "fontWeight": "bold", "color": "#0056b3"}),
                                                     width="auto", className="ms-auto")
                                         ], className="mb-2 g-2"),

                                         dash_table.DataTable(
                                             id="result-table",
                                             columns=[
                                                 {"name": "Result ID", "id": "result_id", "editable": False},
                                                 {"name": "Result Name", "id": "report_name", "editable": True},
                                                 {"name": "Date Acquired", "id": "date", "editable": False},
                                                 {"name": "Method", "id": "method", "editable": False},
                                                 {"name": "User", "id": "user", "editable": False},
                                                 {"name": "System Name", "id": "system", "editable": False},
                                                 {"name": "Result Path", "id": "result_path", "editable": False},
                                             ],
                                             editable=True,
                                             row_selectable="multi",  # Changed to multi-select
                                             data=[],
                                             style_table={"overflowX": "auto", "overflowY": "auto", "height": "80vh",
                                                          "maxHeight": "80vh",
                                                          "border": "1px solid #dee2e6", "borderRadius": "8px",
                                                          "fontFamily": "Arial, sans-serif"},
                                             style_cell={"textAlign": "left", "padding": "8px 12px", "fontSize": "13px",
                                                         "height": "40px",
                                                         "fontFamily": "Arial, sans-serif", "color": "#333",
                                                         "border": "1px solid #dee2e6"},
                                             style_header={"backgroundColor": "#0056b3", "color": "white",
                                                           "fontWeight": "600",
                                                           "fontSize": "13px", "padding": "12px",
                                                           "fontFamily": "Arial, sans-serif"},
                                             filter_action="native",
                                             sort_action="native",
                                             page_size=20,
                                             page_current=0,
                                         )
                                     ], style={"padding": "10px"})
                                 ]),

                         dcc.Tab(label="Chromatogram Analysis", value="tab-2",
                                 style={
                                     'borderLeft': '1px solid #d6d6d6',
                                     'borderRight': '1px solid #d6d6d6',
                                     'borderTop': '1px solid #d6d6d6',
                                     'backgroundColor': '#f9f9f9',
                                     'color': '#333',
                                     'padding': '12px 24px',
                                     'fontFamily': 'Arial, sans-serif',
                                     'fontWeight': '500'
                                 },
                                 selected_style={
                                     'borderTop': '3px solid #0056b3',
                                     'borderLeft': '1px solid #d6d6d6',
                                     'borderRight': '1px solid #d6d6d6',
                                     'borderBottom': '1px solid #fff',
                                     'backgroundColor': '#fff',
                                     'color': '#0056b3',
                                     'padding': '12px 24px',
                                     'fontFamily': 'Arial, sans-serif',
                                     'fontWeight': '600'
                                 },
                                 children=[
                                     # Analysis content - will be shown in both normal and embed mode
                                     html.Div(id="analysis-content", children=[
                                         dcc.Store(id="chromatogram-data", data=None),
                                         dcc.Store(id="phases-data", data=None),
                                         dcc.Store(id="selected-result-id", data=None),  # Current viewing sample
                                         dcc.Store(id="load-volume-store", data=None),
                                         dcc.Store(id="titer-store", data={"titer": 0.0}),
                                         dcc.Store(id="x-axis-offset", data=None),
                                         dcc.Store(id="all-samples-data", data={}),
                                         # Store data for all selected samples

                                         dcc.Interval(id="load-once", interval=1000, n_intervals=0, max_intervals=1),

                                         # Top control row - adjusted for closer positioning
                                         dbc.Row([
                                             dbc.Col([
                                                 html.Label("Plot Mode:",
                                                            style={"font-weight": "bold", "margin-bottom": "8px",
                                                                   "color": "#0056b3"}),
                                                 dcc.RadioItems(
                                                     id="plot-mode-radio",
                                                     options=[
                                                         {"label": " Single Sample", "value": "single"},
                                                         {"label": " Overlay All", "value": "overlay"}
                                                     ],
                                                     value="single",
                                                     inline=True,
                                                     style={"margin-bottom": "10px"}
                                                 )
                                             ], width=3),
                                             dbc.Col([
                                                 html.Div(id="sample-selector-container", children=[
                                                     html.Label("View Result:",
                                                                style={"font-weight": "bold", "margin-bottom": "8px",
                                                                       "color": "#0056b3"}),
                                                     dcc.Dropdown(
                                                         id="sample-selector-dropdown",
                                                         options=[],
                                                         value=None,
                                                         placeholder="Select a result to analyze",
                                                         style={"margin-bottom": "10px"}
                                                     )
                                                 ])
                                             ], width=3),
                                         ], className="mb-3"),

                                         # Main content with original layout structure
                                         html.Div([
                                             # Left side: Plot + Info Tables
                                             html.Div([
                                                 dcc.Graph(id="chromatogram-graph", style={
                                                     "border": "1px solid #dee2e6",
                                                     "border-radius": "8px",
                                                     "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
                                                     "margin-bottom": "20px"
                                                 }),

                                                 # Load Volume Table
                                                 html.Div(id="load-volume-section", children=[
                                                     html.H4("Load Volume", style={
                                                         'color': '#0056b3',
                                                         'margin-top': '0px',
                                                         'margin-bottom': '10px',
                                                         'font-weight': '600'
                                                     }),
                                                     dash_table.DataTable(
                                                         id="load-volume-table",
                                                         columns=[],
                                                         data=[],
                                                         style_table={
                                                             **TABLE_STYLE_TABLE,
                                                             "border": "1px solid #dee2e6",
                                                             "border-radius": "8px",
                                                             "box-shadow": "0 2px 4px rgba(0,0,0,0.1)"
                                                         },
                                                         style_cell={
                                                             **TABLE_STYLE_CELL,
                                                             "fontFamily": "Arial, sans-serif"
                                                         },
                                                         style_header={
                                                             **TABLE_STYLE_HEADER,
                                                             "backgroundColor": "#0056b3",
                                                             "fontFamily": "Arial, sans-serif"
                                                         }
                                                     ),
                                                 ], style={"margin-bottom": "20px"}),

                                                 # Fraction Table
                                                 html.Div(id="fraction-section", children=[
                                                     html.H4("Fractions", style={
                                                         'color': '#0056b3',
                                                         'margin-top': '0px',
                                                         'margin-bottom': '10px',
                                                         'font-weight': '600'
                                                     }),
                                                     dash_table.DataTable(
                                                         id="fraction-table",
                                                         columns=[],
                                                         data=[],
                                                         fixed_rows={'headers': True},
                                                         style_table={
                                                             **TABLE_STYLE_TABLE,
                                                             "border": "1px solid #dee2e6",
                                                             "border-radius": "8px",
                                                             "box-shadow": "0 2px 4px rgba(0,0,0,0.1)"
                                                         },
                                                         style_cell={
                                                             **TABLE_STYLE_CELL,
                                                             "fontFamily": "Arial, sans-serif"
                                                         },
                                                         style_header={
                                                             **TABLE_STYLE_HEADER,
                                                             "backgroundColor": "#0056b3",
                                                             "fontFamily": "Arial, sans-serif"
                                                         }
                                                     ),
                                                 ]),
                                             ], style={
                                                 "width": "85%",
                                                 "padding-right": "20px"
                                             }),

                                             # Right side: Axis selection (15% width)
                                             html.Div([
                                                 html.H4("Plot Settings", style={
                                                     'color': '#0056b3',
                                                     'margin-bottom': '20px',
                                                     'font-weight': '600'
                                                 }),

                                                 # Left axis selection
                                                 html.Label("Left Axis Sensors:", style={
                                                     "font-weight": "600",
                                                     "margin-bottom": "8px",
                                                     "color": "#333",
                                                     "display": "block"
                                                 }),
                                                 dcc.Dropdown(
                                                     id="left-sensor-dropdown",
                                                     options=[],
                                                     value=[],
                                                     multi=True,
                                                     placeholder="Select sensors for left side",
                                                     style={"margin-bottom": "20px"}
                                                 ),

                                                 # Right axis selection
                                                 html.Label("Right Axis Sensors:", style={
                                                     "font-weight": "600",
                                                     "margin-bottom": "8px",
                                                     "color": "#333",
                                                     "display": "block"
                                                 }),
                                                 dcc.Dropdown(
                                                     id="right-sensor-dropdown",
                                                     options=[],
                                                     value=[],
                                                     multi=True,
                                                     placeholder="Select sensors for right side",
                                                     style={"margin-bottom": "20px"}
                                                 ),

                                                 html.Label("Options:", style={
                                                     "font-weight": "600",
                                                     "margin-bottom": "8px",
                                                     "color": "#333",
                                                     "display": "block"
                                                 }),
                                                 dcc.Checklist(
                                                     id="plot-options-checklist",
                                                     options=[
                                                         {"label": " Zero x-axis at Sample Application",
                                                          "value": "zero_ml"},
                                                         {"label": " Show Fraction Annotations",
                                                          "value": "show_fractions"}
                                                     ],
                                                     value=["zero_ml"],
                                                     style={"margin-bottom": "20px"}
                                                 ),

                                                 html.Label("E1%", style={
                                                     "font-weight": "600",
                                                     "margin-bottom": "8px",
                                                     "color": "#333",
                                                     "display": "block"
                                                 }),
                                                 dcc.Input(
                                                     id="extinction-coefficient",
                                                     type="number",
                                                     value=16.19,
                                                     step=0.01,
                                                     style={
                                                         "width": "100%",
                                                         "padding": "8px",
                                                         "border": "1px solid #dee2e6",
                                                         "border-radius": "4px",
                                                         "font-family": "Arial, sans-serif"
                                                     }
                                                 ),
                                             ], style={
                                                 "width": "15%",
                                                 "border": "1px solid #dee2e6",
                                                 "border-radius": "8px",
                                                 "padding": "20px",
                                                 "background-color": "#f8f9fa",
                                                 "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
                                                 "height": "fit-content"
                                             }),
                                         ], style={"display": "flex", "flex-direction": "row", "gap": "0px"}),
                                     ], style={"padding": "20px", "background-color": "#ffffff"})
                                 ])
                     ])
        ]),

        # Embed mode analysis content (shown when tabs are hidden)
        html.Div(id="embed-analysis", style={"display": "none"})
    ])
])


def extract_phases(result_id):
    logs = AktaRunLog.objects.filter(result_id=result_id).order_by("date_time").values("date_time", "ml", "log_text")
    df = pd.DataFrame(logs).dropna(subset=["log_text"])

    phases = []
    phase_start = None

    for _, row in df.iterrows():
        log = row["log_text"]

        if log.startswith("Phase ") and "(Issued)" in log and "(Processing)" in log:
            phase_name = log.replace("Phase ", "").split(" (")[0]

            if phase_name == "Method Settings":
                phase_start = None
                continue

            phase_start = {
                "label": phase_name,
                "start_time": row["date_time"],
                "start_ml": row["ml"]
            }

        elif "End Phase (Issued) (Processing) (Completed)" in log and phase_start:
            phase_start.update({
                "end_time": row["date_time"],
                "end_ml": row["ml"]
            })
            phases.append(phase_start)
            phase_start = None

    if phase_start:
        end_blocks = df[df["log_text"].str.contains("End_Block \(Issued\) \(Processing\) \(Completed\)", na=False)]
        if not end_blocks.empty:
            last = end_blocks.iloc[-1]
            phase_start.update({
                "end_time": last["date_time"],
                "end_ml": last["ml"]
            })
            phases.append(phase_start)

    return pd.DataFrame(phases)


def fill_phase_mLs(phases_df, chrom_df):
    chrom_df = chrom_df.sort_values("date_time").copy()
    chrom_df["date_time"] = pd.to_datetime(chrom_df["date_time"])

    phases_df["start_time"] = pd.to_datetime(phases_df["start_time"])
    phases_df["end_time"] = pd.to_datetime(phases_df["end_time"])

    start_mls = []
    end_mls = []

    for _, row in phases_df.iterrows():
        start_ml = chrom_df.loc[
            (chrom_df["date_time"] - row["start_time"]).abs().idxmin(), "ml"
        ] if pd.notnull(row["start_time"]) else None

        end_ml = chrom_df.loc[
            (chrom_df["date_time"] - row["end_time"]).abs().idxmin(), "ml"
        ] if pd.notnull(row["end_time"]) else None

        start_mls.append(start_ml)
        end_mls.append(end_ml)

    phases_df["start_ml"] = start_mls
    phases_df["end_ml"] = end_mls

    return phases_df


def add_fraction_annotations(fig, result_id, offset_ml):
    """Add fraction annotations to the plot with goal posts and light shading"""

    # Get fraction data
    fraction_qs = AktaFraction.objects.filter(result_id=result_id).order_by("date_time")
    if not fraction_qs.exists():
        return

    # Get chromatogram data to find ml positions
    chrom_qs = AktaChromatogram.objects.filter(result_id=result_id).values()
    chrom_df = pd.DataFrame(chrom_qs).sort_values("date_time")
    chrom_df["date_time"] = pd.to_datetime(chrom_df["date_time"])

    frac_df = pd.DataFrame(list(fraction_qs.values("date_time", "fraction")))
    frac_df["date_time"] = pd.to_datetime(frac_df["date_time"])
    frac_df = frac_df.drop_duplicates(subset=["fraction"]).reset_index(drop=True)

    # Get ml positions for fractions
    start_mls = []
    for t in frac_df["date_time"]:
        idx = (chrom_df["date_time"] - t).abs().idxmin()
        start_mls.append(chrom_df.loc[idx, "ml"] if pd.notnull(idx) else None)

    frac_df["start_ml"] = start_mls
    # Calculate end_ml as the start of the next fraction
    frac_df["end_ml"] = frac_df["start_ml"].shift(-1)

    # Remove the last row if it doesn't have an end_ml
    frac_df = frac_df.dropna(subset=["start_ml", "end_ml"])

    # Apply offset
    frac_df["start_ml"] = frac_df["start_ml"] - offset_ml
    frac_df["end_ml"] = frac_df["end_ml"] - offset_ml

    # Filter out waste fractions
    frac_df = frac_df[~frac_df["fraction"].str.lower().str.contains("waste", na=False)]

    if frac_df.empty:
        return

    # Add fraction goal posts with light shading
    # Phases use y=0.0 to 0.05, so we'll use y=0.06 to 0.11 for fractions (above phases)
    fraction_y_bottom = 0.06  # Bottom of the vertical lines
    fraction_y_top = 0.11  # Top of the vertical lines

    for _, row in frac_df.iterrows():
        start_ml = row["start_ml"]
        end_ml = row["end_ml"]
        fraction_name = row["fraction"]

        # Calculate midpoint for label
        midpoint = (start_ml + end_ml) / 2

        # Add light shading between the goal posts
        fig.add_shape(
            type="rect",
            x0=start_ml,
            x1=end_ml,
            yref="paper",
            y0=fraction_y_bottom,
            y1=fraction_y_top,
            fillcolor="rgba(214, 39, 40, 0.1)",  # Light red shading (10% opacity)
            line=dict(width=0),  # No border
            layer="below"
        )

        # Add left vertical line (start of fraction)
        fig.add_shape(
            type="line",
            x0=start_ml,
            x1=start_ml,
            yref="paper",
            y0=fraction_y_bottom,
            y1=fraction_y_top,
            line=dict(width=2, color="#d62728"),  # Red color to distinguish from phases
            layer="above"
        )

        # Add right vertical line (end of fraction)
        fig.add_shape(
            type="line",
            x0=end_ml,
            x1=end_ml,
            yref="paper",
            y0=fraction_y_bottom,
            y1=fraction_y_top,
            line=dict(width=2, color="#d62728"),
            layer="above"
        )

        # Add fraction label in the middle between the goal posts
        # Clean up the fraction name for display (remove extra text if needed)
        display_name = fraction_name
        if "Fraction" in display_name:
            # Extract just the number/letter part if it's like "Fraction 01" or "Fraction A1"
            parts = display_name.split()
            if len(parts) > 1:
                display_name = parts[-1]  # Take the last part (usually the number/letter)

        fig.add_annotation(
            x=midpoint,
            y=(fraction_y_bottom + fraction_y_top) / 2,  # Center the label between bottom and top
            yref="paper",
            text=display_name,
            showarrow=False,
            yanchor="middle",
            xanchor="center",
            font=dict(size=10, color="#d62728", weight="bold")
        )


def plot_single_sample(fig, df, left_sensors, right_sensors, phases_df, result_id, plot_options, offset_ml):
    """Plot a single sample with phases and optional fraction annotations"""

    phases = []
    for _, row in phases_df.iterrows():
        if pd.notnull(row["start_ml"]) and pd.notnull(row["end_ml"]):
            phases.append({
                "label": row["label"],
                "start": row["start_ml"],
                "end": row["end_ml"]
            })

    left_sensors = left_sensors or []
    right_sensors = right_sensors or []

    default_colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
        "#bcbd22", "#17becf"
    ]

    grid_color = "#eee"
    base_axis_style = dict(
        showline=True,
        linewidth=1,
        linecolor="black",
        mirror=True,
        ticks="inside",
        tickwidth=1,
        tickcolor="black",
        ticklen=6,
        showgrid=True,
        gridcolor=grid_color,
        minor=dict(
            ticks="inside",
            ticklen=3,
            tickcolor="black",
            showgrid=False
        )
    )

    axis_counter = 1

    # LEFT SENSORS
    for i, sensor in enumerate(left_sensors):
        if sensor not in df.columns:
            continue

        axis_id = "" if axis_counter == 1 else str(axis_counter)
        yaxis_name = f"yaxis{axis_id}"
        yaxis_id = f"y{axis_id}"

        y_data = df[sensor]
        y_data_max = y_data.max()
        y_max = y_data_max * 1.05
        y_min = y_data.min() - 1.5 * (y_max - y_data_max)

        color = default_colors[(axis_counter - 1) % len(default_colors)]

        fig.add_trace(go.Scatter(
            x=df["ml"],
            y=y_data,
            name=AXIS_LABELS.get(sensor, sensor),
            mode="lines",
            yaxis=yaxis_id,
            line=dict(color=color),
            connectgaps=True
        ))

        position_left = 0.0 + 0.05 * i
        if position_left > 0.4:
            position_left = 0.4

        layout_args = {
            **base_axis_style,
            "title": dict(text=AXIS_LABELS.get(sensor, sensor), font=dict(color=color)),
            "side": "left",
            "range": [y_min, y_max]
        }
        if axis_counter > 1:
            layout_args.update({
                "overlaying": "y",
                "anchor": "free",
                "position": position_left
            })

        fig.update_layout(**{yaxis_name: layout_args})
        axis_counter += 1

    # RIGHT SENSORS
    for j, sensor in enumerate(right_sensors):
        if sensor not in df.columns:
            continue

        axis_id = "" if axis_counter == 1 else str(axis_counter)
        yaxis_name = f"yaxis{axis_id}"
        yaxis_id = f"y{axis_id}"

        y_data = df[sensor]
        y_data_max = y_data.max()
        y_max = y_data_max * 1.05
        y_min = y_data.min() - 1.5 * (y_max - y_data_max)

        color = default_colors[(axis_counter - 1) % len(default_colors)]

        fig.add_trace(go.Scatter(
            x=df["ml"],
            y=y_data,
            name=AXIS_LABELS.get(sensor, sensor),
            mode="lines",
            yaxis=yaxis_id,
            line=dict(color=color),
            connectgaps=True
        ))

        position_right = 1.0 - 0.05 * j
        if position_right < 0.6:
            position_right = 0.6

        layout_args = {
            **base_axis_style,
            "title": dict(text=AXIS_LABELS.get(sensor, sensor), font=dict(color=color)),
            "side": "right",
            "range": [y_min, y_max]
        }
        if axis_counter > 1:
            layout_args.update({
                "overlaying": "y",
                "anchor": "free",
                "position": position_right
            })

        fig.update_layout(**{yaxis_name: layout_args})
        axis_counter += 1

    # Add phase annotations
    for phase in phases:
        phase["label"] = phase["label"].replace(" ", "<br>")
        midpoint = (phase["start"] + phase["end"]) / 2

        for x_pos in [phase["start"], phase["end"]]:
            fig.add_shape(
                type="line",
                x0=x_pos,
                x1=x_pos,
                yref="paper",
                y0=0.0,
                y1=0.05,
                line=dict(width=1),
                layer="above"
            )

        fig.add_annotation(
            x=midpoint,
            y=0.01,
            yref="paper",
            text=phase["label"],
            showarrow=False,
            yanchor="bottom",
            xanchor="center",
            font=dict(size=10)
        )

    # Add fraction annotations if enabled
    if "show_fractions" in (plot_options or []):
        add_fraction_annotations(fig, result_id, offset_ml)

    # Get result info for title
    result = AktaResult.objects.filter(result_id=result_id).first()
    if result:
        report_name = result.report_name
        cv = result.column_volume
        column_name = result.column_name
        method = result.method
        title_text = f"Result: {report_name} - Method: {method} - Column: {column_name} - CV: {cv} mL"
    else:
        title_text = f"Result ID: {result_id}"

    fig.update_layout(
        height=650,
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=16)
        ),
        xaxis={
            **base_axis_style,
            "title": "ml",
            "range": [df["ml"].min(), df["ml"].max()]
        },
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        showlegend=False,
        margin=dict(t=60, b=60, l=60, r=20)
    )

    return fig


def plot_overlay_samples(fig, all_data, selected_ids, left_sensors, right_sensors, plot_options):
    """Plot multiple samples overlaid"""

    default_colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
        "#bcbd22", "#17becf"
    ]

    # Use only the first sensor from left_sensors for overlay
    sensor = left_sensors[0] if left_sensors else "uv_1_280"

    all_x_min, all_x_max = float('inf'), float('-inf')

    for i, result_id in enumerate(selected_ids):
        if result_id not in all_data:
            continue

        sample_data = all_data[result_id]
        chrom_data = sample_data["chromatogram"]
        phases_data = sample_data["phases"]
        result_info = sample_data["result_info"]

        if not chrom_data:
            continue

        df = pd.DataFrame(chrom_data).sort_values("ml")

        # Apply offset if zero_ml option is selected
        offset_ml = 0.0
        if "zero_ml" in (plot_options or []):
            for phase in phases_data:
                if phase.get("label") == "Sample Application" and pd.notnull(phase.get("start_ml")):
                    offset_ml = phase["start_ml"]
                    break
            df["ml"] = df["ml"] - offset_ml

        if sensor in df.columns:
            color = default_colors[i % len(default_colors)]

            fig.add_trace(go.Scatter(
                x=df["ml"],
                y=df[sensor],
                name=f"{result_info['report_name']}",
                mode="lines",
                line=dict(color=color, width=2),
                connectgaps=True
            ))

            all_x_min = min(all_x_min, df["ml"].min())
            all_x_max = max(all_x_max, df["ml"].max())

    grid_color = "#eee"
    base_axis_style = dict(
        showline=True,
        linewidth=1,
        linecolor="black",
        mirror=True,
        ticks="inside",
        tickwidth=1,
        tickcolor="black",
        ticklen=6,
        showgrid=True,
        gridcolor=grid_color,
        minor=dict(
            ticks="inside",
            ticklen=3,
            tickcolor="black",
            showgrid=False
        )
    )

    fig.update_layout(
        height=650,
        title=dict(
            text=f"Overlay Plot - {AXIS_LABELS.get(sensor, sensor)}",
            x=0.5,
            xanchor='center',
            font=dict(size=16)
        ),
        xaxis={
            **base_axis_style,
            "title": "ml",
            "range": [all_x_min, all_x_max] if all_x_min != float('inf') else [0, 100]
        },
        yaxis={
            **base_axis_style,
            "title": AXIS_LABELS.get(sensor, sensor)
        },
        template="plotly_white",
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        showlegend=True,
        margin=dict(t=60, b=60, l=60, r=150)
    )

    return fig


# URL parsing and embed mode handling
@app.callback(
    Output("main-tabs", "value"),
    Output("embed-mode", "data"),
    Output("tab-container", "style"),
    Output("embed-analysis", "style"),
    Output("embed-analysis", "children"),
    Input("url", "search"),
    prevent_initial_call=True
)
def handle_url_and_embed_mode(search):
    if not search:
        return "tab-1", False, {"display": "block"}, {"display": "none"}, []

    query = parse_qs(urlparse(search).query)

    # Check for embed mode
    embed = query.get("embed", [None])[0]
    is_embed = embed == "true"

    # Check for DN, FB, or UP parameters
    dn_params = query.get("dn", [])
    fb_params = query.get("fb", [])
    up_params = query.get("up", [])

    if is_embed:
        # Hide tabs and show analysis content
        analysis_content = html.Div([
            dcc.Store(id="chromatogram-data", data=None),
            dcc.Store(id="phases-data", data=None),
            dcc.Store(id="selected-result-id", data=None),
            dcc.Store(id="load-volume-store", data=None),
            dcc.Store(id="titer-store", data={"titer": 0.0}),
            dcc.Store(id="x-axis-offset", data=None),
            dcc.Store(id="all-samples-data", data={}),

            # Top control row for embed mode
            dbc.Row([
                dbc.Col([
                    html.Label("Plot Mode:", style={"font-weight": "bold", "margin-bottom": "8px", "color": "#0056b3"}),
                    dcc.RadioItems(
                        id="plot-mode-radio",
                        options=[
                            {"label": " Single Sample", "value": "single"},
                            {"label": " Overlay All", "value": "overlay"}
                        ],
                        value="single",
                        inline=True,
                        style={"margin-bottom": "10px"}
                    )
                ], width=3),
                dbc.Col([
                    html.Div(id="sample-selector-container", children=[
                        html.Label("View Result:",
                                   style={"font-weight": "bold", "margin-bottom": "8px", "color": "#0056b3"}),
                        dcc.Dropdown(
                            id="sample-selector-dropdown",
                            options=[],
                            value=None,
                            placeholder="Select a result to analyze",
                            style={"margin-bottom": "10px"}
                        )
                    ])
                ], width=3),
            ], className="mb-3"),

            # Main content layout for embed
            html.Div([
                # Left side: Plot + Tables
                html.Div([
                    dcc.Graph(id="chromatogram-graph", style={
                        "border": "1px solid #dee2e6",
                        "border-radius": "8px",
                        "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
                        "margin-bottom": "20px"
                    }),

                    # Load Volume Table
                    html.Div(id="load-volume-section", children=[
                        html.H4("Load Volume", style={
                            'color': '#0056b3',
                            'margin-top': '0px',
                            'margin-bottom': '10px',
                            'font-weight': '600'
                        }),
                        dash_table.DataTable(
                            id="load-volume-table",
                            columns=[],
                            data=[],
                            style_table={
                                **TABLE_STYLE_TABLE,
                                "border": "1px solid #dee2e6",
                                "border-radius": "8px",
                                "box-shadow": "0 2px 4px rgba(0,0,0,0.1)"
                            },
                            style_cell={
                                **TABLE_STYLE_CELL,
                                "fontFamily": "Arial, sans-serif"
                            },
                            style_header={
                                **TABLE_STYLE_HEADER,
                                "backgroundColor": "#0056b3",
                                "fontFamily": "Arial, sans-serif"
                            }
                        ),
                    ], style={"margin-bottom": "20px"}),

                    # Fraction Table
                    html.Div(id="fraction-section", children=[
                        html.H4("Fractions", style={
                            'color': '#0056b3',
                            'margin-top': '0px',
                            'margin-bottom': '10px',
                            'font-weight': '600'
                        }),
                        dash_table.DataTable(
                            id="fraction-table",
                            columns=[],
                            data=[],
                            fixed_rows={'headers': True},
                            style_table={
                                **TABLE_STYLE_TABLE,
                                "border": "1px solid #dee2e6",
                                "border-radius": "8px",
                                "box-shadow": "0 2px 4px rgba(0,0,0,0.1)"
                            },
                            style_cell={
                                **TABLE_STYLE_CELL,
                                "fontFamily": "Arial, sans-serif"
                            },
                            style_header={
                                **TABLE_STYLE_HEADER,
                                "backgroundColor": "#0056b3",
                                "fontFamily": "Arial, sans-serif"
                            }
                        ),
                    ]),
                ], style={
                    "width": "85%",
                    "padding-right": "20px"
                }),

                # Right side: Plot Settings (15% width)
                html.Div([
                    html.H4("Plot Settings", style={
                        'color': '#0056b3',
                        'margin-bottom': '20px',
                        'font-weight': '600'
                    }),

                    html.Label("Left Axis Sensors:", style={
                        "font-weight": "600",
                        "margin-bottom": "8px",
                        "color": "#333",
                        "display": "block"
                    }),
                    dcc.Dropdown(
                        id="left-sensor-dropdown",
                        options=[],
                        value=[],
                        multi=True,
                        placeholder="Select sensors for left side",
                        style={"margin-bottom": "20px"}
                    ),

                    html.Label("Right Axis Sensors:", style={
                        "font-weight": "600",
                        "margin-bottom": "8px",
                        "color": "#333",
                        "display": "block"
                    }),
                    dcc.Dropdown(
                        id="right-sensor-dropdown",
                        options=[],
                        value=[],
                        multi=True,
                        placeholder="Select sensors for right side",
                        style={"margin-bottom": "20px"}
                    ),

                    html.Label("Options:", style={
                        "font-weight": "600",
                        "margin-bottom": "8px",
                        "color": "#333",
                        "display": "block"
                    }),
                    dcc.Checklist(
                        id="plot-options-checklist",
                        options=[
                            {"label": " Zero x-axis at Sample Application", "value": "zero_ml"},
                            {"label": " Show Fraction Annotations", "value": "show_fractions"}
                        ],
                        value=["zero_ml"],
                        style={"margin-bottom": "20px"}
                    ),

                    html.Label("E1%", style={
                        "font-weight": "600",
                        "margin-bottom": "8px",
                        "color": "#333",
                        "display": "block"
                    }),
                    dcc.Input(
                        id="extinction-coefficient",
                        type="number",
                        value=16.19,
                        step=0.01,
                        style={
                            "width": "100%",
                            "padding": "8px",
                            "border": "1px solid #dee2e6",
                            "border-radius": "4px",
                            "font-family": "Arial, sans-serif"
                        }
                    ),
                ], style={
                    "width": "15%",
                    "border": "1px solid #dee2e6",
                    "border-radius": "8px",
                    "padding": "20px",
                    "background-color": "#f8f9fa",
                    "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
                    "height": "fit-content"
                }),
            ], style={"display": "flex", "flex-direction": "row", "gap": "0px"}),
        ], style={"padding": "20px", "background-color": "#ffffff"})

        return dash.no_update, True, {"display": "none"}, {"display": "block"}, analysis_content

    # Normal mode - check if we should switch to tab-2
    if dn_params or fb_params or up_params:
        return "tab-2", False, {"display": "block"}, {"display": "none"}, []

    return "tab-1", False, {"display": "block"}, {"display": "none"}, []


# Combined callback for URL-based and table-based result selection
@app.callback(
    Output("selected-result-ids", "data"),
    Input("url", "search"),
    Input("result-table", "selected_rows"),
    State("result-table", "data"),
    State("embed-mode", "data"),
    prevent_initial_call=True
)
def handle_result_selection(search, selected_rows, table_data, is_embed):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    print(f"DEBUG: handle_result_selection triggered by: {triggered_id}")

    # Handle URL-based selection
    if triggered_id == "url":
        print(f"DEBUG: URL search parameter: {search}")

        if not search:
            return dash.no_update

        query = parse_qs(urlparse(search).query)
        print(f"DEBUG: Parsed query: {query}")

        # Get query parameters - can be multiple
        dn_params = query.get("dn", [])
        fb_params = query.get("fb", [])
        up_params = query.get("up", [])

        print(f"DEBUG: DN params: {dn_params}, FB params: {fb_params}, UP params: {up_params}")

        target_names = []

        # Handle DN parameters
        for dn_str in dn_params:
            if ',' in dn_str:
                for dn_part in dn_str.split(','):
                    try:
                        dn_number = int(dn_part.strip())
                        target_names.append(f"DN{dn_number}")
                    except ValueError:
                        continue
            else:
                try:
                    dn_number = int(dn_str)
                    target_names.append(f"DN{dn_number}")
                except ValueError:
                    continue

        # Handle FB parameters
        for fb_str in fb_params:
            if ',' in fb_str:
                for fb_part in fb_str.split(','):
                    try:
                        fb_number = int(fb_part.strip())
                        target_names.append(f"FB{fb_number}")
                    except ValueError:
                        continue
            else:
                try:
                    fb_number = int(fb_str)
                    target_names.append(f"FB{fb_number}")
                except ValueError:
                    continue

        # Handle UP parameters
        for up_str in up_params:
            if ',' in up_str:
                for up_part in up_str.split(','):
                    up_part = up_part.strip()
                    if up_part.isdigit():
                        target_names.append(f"UP{up_part}")
                    else:
                        target_names.append(up_part.upper())
            else:
                if up_str.isdigit():
                    target_names.append(f"UP{up_str}")
                else:
                    target_names.append(up_str.upper())

        if not target_names:
            return dash.no_update

        print(f"DEBUG: Looking for target names: {target_names}")

        # Find matching results directly from database
        from plotly_integration.models import AktaResult

        # First, let's see what report names actually exist in the database
        all_report_names = list(AktaResult.objects.values_list('report_name', flat=True)[:20])
        print(f"DEBUG: Sample report names in database: {all_report_names}")

        # Try exact match first
        matching_results = AktaResult.objects.filter(report_name__in=target_names)
        matching_list = list(matching_results.values_list('result_id', flat=True))

        print(f"DEBUG: URL-based selection found result IDs: {matching_list}")

        return matching_list if matching_list else dash.no_update

    # Handle table-based selection
    elif triggered_id == "result-table":
        print(f"DEBUG: Table selection - selected rows: {selected_rows}")

        if not selected_rows or not table_data:
            return []

        selected_ids = [table_data[row]["result_id"] for row in selected_rows]
        print(f"DEBUG: Table-based selection result IDs: {selected_ids}")

        return selected_ids

    return dash.no_update


@app.callback(
    Output("result-table", "data"),
    Input("load-once", "n_intervals"),
    Input("refresh-akta-table", "n_clicks"),
    prevent_initial_call=False
)
def load_or_refresh_result_table(_, refresh_clicks):
    from plotly_integration.models import AktaResult

    results = AktaResult.objects.all().order_by("-date")[:500]
    table_data = []

    for r in results:
        table_data.append({
            "result_id": r.result_id,
            "report_name": r.report_name,
            "user": r.user,
            "method": getattr(r, "method", ""),
            "date": r.date.strftime("%Y-%m-%d") if r.date else "",
            "result_path": getattr(r, "result_path", ""),
            "system": getattr(r, "system", "")
        })

    return table_data


@app.callback(
    Output("save-akta-status", "children"),
    Output("reset-save-akta-timer", "disabled"),
    Input("save-akta-names", "n_clicks_timestamp"),
    Input("reset-save-akta-timer", "n_intervals"),
    State("reset-save-akta-timer", "disabled"),
    State("result-table", "derived_virtual_data"),
    State("result-table", "page_current"),
    State("result-table", "page_size"),
    prevent_initial_call=True
)
def save_edited_akta_names(save_ts, interval_n, interval_disabled,
                           visible_data, page_current, page_size):
    from plotly_integration.models import AktaResult

    if not interval_disabled:
        return "💾 Save", True

    if not visible_data or page_current is None or page_size is None:
        return "💾 Save", True

    start = page_current * page_size
    end = start + page_size
    page_rows = visible_data[start:end]

    updated, skipped, errors = 0, 0, 0

    for row in page_rows:
        try:
            result_id = row.get("result_id")
            new_name = row.get("report_name", "")

            existing = AktaResult.objects.filter(result_id=result_id).first()
            if not existing:
                skipped += 1
                continue

            if existing.report_name != new_name:
                existing.report_name = new_name
                existing.save()
                updated += 1
            else:
                skipped += 1

        except Exception as e:
            print(f"❌ Error saving Akta result {result_id}: {e}")
            errors += 1

    return f"✅ Saved! ({updated} updated, {skipped} skipped, {errors} errors)", False


# Show/hide sample selector based on plot mode
@app.callback(
    Output("sample-selector-container", "style"),
    Input("plot-mode-radio", "value"),
    prevent_initial_call=True
)
def toggle_sample_selector(plot_mode):
    if plot_mode == "overlay":
        return {"display": "none"}
    return {"display": "block"}


# Show/hide tables based on plot mode
@app.callback(
    Output("fraction-section", "style"),
    Input("plot-mode-radio", "value"),
    prevent_initial_call=True
)
def toggle_fraction_table(plot_mode):
    if plot_mode == "overlay":
        return {"display": "none"}
    return {"display": "block"}


# Show selection status on result table page
@app.callback(
    Output("selection-status", "children"),
    Input("selected-result-ids", "data"),
    prevent_initial_call=True
)
def update_selection_status(selected_ids):
    if not selected_ids:
        return ""

    count = len(selected_ids)
    if count == 1:
        return f"📊 {count} sample selected"
    else:
        return f"📊 {count} samples selected"


# Populate sample selector dropdown
@app.callback(
    Output("sample-selector-dropdown", "options"),
    Output("sample-selector-dropdown", "value"),
    Input("selected-result-ids", "data"),
    State("result-table", "data"),
    State("embed-mode", "data"),
    prevent_initial_call=True
)
def update_sample_selector(selected_ids, table_data, is_embed):
    print(f"DEBUG: update_sample_selector called with IDs: {selected_ids}, embed_mode: {is_embed}")

    if not selected_ids:
        print("DEBUG: No selected IDs for sample selector")
        return [], None

    options = []

    if is_embed:
        print("DEBUG: Embed mode - getting data from database")
        # In embed mode, get data directly from database
        for result_id in selected_ids:
            result = AktaResult.objects.filter(result_id=result_id).first()
            if result:
                options.append({
                    "label": result.report_name,  # Only show report name
                    "value": result_id
                })
                print(f"DEBUG: Added option: {result.report_name} -> {result_id}")
    else:
        print("DEBUG: Normal mode - using table data")
        # In URL mode when not embedded, still get from database since table_data might not be loaded
        if not table_data:
            print("DEBUG: No table data available, getting from database instead")
            # Fallback to database when table data not available (like in URL mode)
            for result_id in selected_ids:
                result = AktaResult.objects.filter(result_id=result_id).first()
                if result:
                    options.append({
                        "label": result.report_name,  # Only show report name
                        "value": result_id
                    })
                    print(f"DEBUG: Added option from DB: {result.report_name} -> {result_id}")
        else:
            # Normal table-based mode
            for row in table_data:
                if row["result_id"] in selected_ids:
                    options.append({
                        "label": row["report_name"],  # Only show report name, no ID
                        "value": row["result_id"]
                    })
                    print(f"DEBUG: Added option from table: {row['report_name']} -> {row['result_id']}")

    # Set first selected as default
    default_value = selected_ids[0] if selected_ids else None
    print(f"DEBUG: Sample selector options: {len(options)} items, default: {default_value}")

    return options, default_value


# Load data for all selected samples
@app.callback(
    Output("all-samples-data", "data"),
    Input("selected-result-ids", "data"),
    prevent_initial_call=True
)
def load_all_samples_data(selected_ids):
    print(f"DEBUG: load_all_samples_data called with IDs: {selected_ids}")

    if not selected_ids:
        print("DEBUG: No selected IDs, returning empty dict")
        return {}

    all_data = {}

    for result_id in selected_ids:
        print(f"DEBUG: Processing result_id: {result_id}")

        # Load chromatogram data
        chrom_qs = AktaChromatogram.objects.filter(result_id=result_id).values()
        print(f"DEBUG: Chromatogram query count for {result_id}: {chrom_qs.count()}")

        if not chrom_qs.exists():
            print(f"DEBUG: No chromatogram data found for {result_id}")
            continue

        chrom_df = pd.DataFrame(chrom_qs)
        if chrom_df.empty or "date_time" not in chrom_df.columns:
            print(f"DEBUG: Chromatogram DataFrame empty or missing date_time for {result_id}")
            continue

        chrom_df = chrom_df.sort_values("date_time")
        chrom_df["date_time"] = pd.to_datetime(chrom_df["date_time"])
        print(f"DEBUG: Chromatogram data loaded for {result_id}, shape: {chrom_df.shape}")

        # Load phases data
        phases_df = extract_phases(result_id)
        print(f"DEBUG: Phases extracted for {result_id}, shape: {phases_df.shape if not phases_df.empty else 'empty'}")

        if not phases_df.empty:
            phases_df = fill_phase_mLs(phases_df, chrom_df)
            print(f"DEBUG: Phases filled with mL data for {result_id}")

        # Get result info
        result = AktaResult.objects.filter(result_id=result_id).first()
        print(f"DEBUG: Result info found for {result_id}: {result.report_name if result else 'None'}")

        all_data[result_id] = {
            "chromatogram": chrom_df.to_dict("records"),
            "phases": phases_df.to_dict("records") if not phases_df.empty else [],
            "result_info": {
                "report_name": result.report_name if result else "",
                "method": getattr(result, "method", "") if result else "",
                "column_name": getattr(result, "column_name", "") if result else "",
                "column_volume": getattr(result, "column_volume", "") if result else "",
                "date": result.date if result else None
            }
        }
        print(f"DEBUG: Successfully loaded data for {result_id}")

    print(f"DEBUG: Final all_data keys: {list(all_data.keys())}")
    return all_data


# Set current viewing sample
@app.callback(
    Output("selected-result-id", "data"),
    Input("sample-selector-dropdown", "value"),
    Input("selected-result-ids", "data"),  # Add this as trigger
    prevent_initial_call=True
)
def set_current_sample(selected_sample, selected_ids):
    print(f"DEBUG: set_current_sample called with sample: {selected_sample}, all_ids: {selected_ids}")

    # If no sample selected but we have IDs, select the first one
    if not selected_sample and selected_ids:
        default_sample = selected_ids[0]
        print(f"DEBUG: No sample selected, defaulting to first: {default_sample}")
        return default_sample

    print(f"DEBUG: Returning selected sample: {selected_sample}")
    return selected_sample


# Update chromatogram data based on current sample
@app.callback(
    Output("chromatogram-data", "data"),
    Output("phases-data", "data"),
    Input("selected-result-id", "data"),
    Input("all-samples-data", "data"),  # Add this as Input to wait for data loading
    prevent_initial_call=True
)
def update_current_sample_data(current_sample, all_data):
    print(f"DEBUG: update_current_sample_data called with sample: {current_sample}")
    print(f"DEBUG: Available data keys: {list(all_data.keys()) if all_data else 'None'}")

    if not current_sample:
        print("DEBUG: No current sample, returning empty data")
        return [], []

    if not all_data or current_sample not in all_data:
        print(f"DEBUG: Current sample {current_sample} not found in all_data")
        return [], []

    sample_data = all_data[current_sample]
    chrom_data = sample_data["chromatogram"]
    phases_data = sample_data["phases"]

    print(f"DEBUG: Returning chromatogram data with {len(chrom_data)} records and {len(phases_data)} phases")
    return chrom_data, phases_data


# Update load volume table for overlay mode
@app.callback(
    Output("load-volume-table", "columns"),
    Output("load-volume-table", "data"),
    Input("plot-mode-radio", "value"),
    Input("load-volume-store", "data"),
    Input("titer-store", "data"),
    Input("x-axis-offset", "data"),
    State("all-samples-data", "data"),
    State("selected-result-ids", "data"),
    prevent_initial_call=True
)
def update_load_volume_table(plot_mode, load_data, titer_data, x_offset_ml, all_data, selected_ids):
    if plot_mode == "single":
        # Original single sample logic
        if not load_data:
            return [], []

        titer = titer_data.get("titer", 1.0)
        load_volume = load_data["load_volume"]
        load_mass = round(titer * load_volume, 2)

        result_df = pd.DataFrame([{
            "start_ml": round(load_data["start_ml"] - (x_offset_ml or 0), 2),
            "end_ml": round(load_data["end_ml"] - (x_offset_ml or 0), 2),
            "load_volume": round(load_volume, 2),
            "titer": titer,
            "load_mass": load_mass
        }])

        table_columns = [
            {"name": "Sample Application Start", "id": "start_ml", "type": "numeric"},
            {"name": "Sample Application End", "id": "end_ml", "type": "numeric"},
            {"name": "Load Volume", "id": "load_volume", "type": "numeric"},
            {"name": "Titer (mg/mL)", "id": "titer", "type": "numeric", "editable": True},
            {"name": "Load Mass (mg)", "id": "load_mass", "type": "numeric"},
        ]

        return table_columns, result_df.to_dict("records")

    else:  # overlay mode
        if not all_data or not selected_ids:
            return [], []

        overlay_data = []

        for result_id in selected_ids:
            if result_id not in all_data:
                continue

            sample_data = all_data[result_id]
            phases_data = sample_data["phases"]
            result_info = sample_data["result_info"]

            # Find Sample Application phase
            sample_app_phase = None
            for phase in phases_data:
                if phase.get("label") == "Sample Application":
                    sample_app_phase = phase
                    break

            if sample_app_phase:
                start_ml = sample_app_phase.get("start_ml", 0)
                end_ml = sample_app_phase.get("end_ml", 0)
                load_volume = end_ml - start_ml

                # Use default titer for overlay mode
                titer = 1.0
                load_mass = round(titer * load_volume, 2)

                overlay_data.append({
                    "sample": result_info["report_name"],
                    "start_ml": round(start_ml, 2),
                    "end_ml": round(end_ml, 2),
                    "load_volume": round(load_volume, 2),
                    "titer": titer,
                    "load_mass": load_mass
                })

        table_columns = [
            {"name": "Sample", "id": "sample"},
            {"name": "Sample Application Start", "id": "start_ml", "type": "numeric"},
            {"name": "Sample Application End", "id": "end_ml", "type": "numeric"},
            {"name": "Load Volume", "id": "load_volume", "type": "numeric"},
            {"name": "Titer (mg/mL)", "id": "titer", "type": "numeric", "editable": True},
            {"name": "Load Mass (mg)", "id": "load_mass", "type": "numeric"},
        ]

        return table_columns, overlay_data


# STEP 1: Build sensor options & keep them disjoint
@app.callback(
    Output("left-sensor-dropdown", "options"),
    Output("left-sensor-dropdown", "value"),
    Output("right-sensor-dropdown", "options"),
    Output("right-sensor-dropdown", "value"),
    Input("selected-result-id", "data"),
    Input("left-sensor-dropdown", "value"),
    Input("right-sensor-dropdown", "value"),
    prevent_initial_call=True
)
def manage_sensor_choices(result_id, left_vals, right_vals):
    all_fields = [f.name for f in AktaChromatogram._meta.get_fields()]
    all_sensors = [f for f in all_fields if f not in ["id", "result_id", "ml", "date_time"]]

    left_vals = set(left_vals or [])
    right_vals = set(right_vals or [])

    default_sensor = "uv_1_280"
    if default_sensor in all_sensors:
        if not left_vals:
            left_vals.add(default_sensor)
        elif default_sensor in right_vals:
            right_vals.remove(default_sensor)

    overlap = left_vals & right_vals
    if overlap:
        right_vals = right_vals - overlap

    left_vals = left_vals.intersection(all_sensors)
    right_vals = right_vals.intersection(all_sensors)

    left_options = [{"label": AXIS_LABELS.get(s, s), "value": s} for s in all_sensors if s not in right_vals]
    right_options = [{"label": AXIS_LABELS.get(s, s), "value": s} for s in all_sensors if s not in left_vals]

    return left_options, sorted(left_vals), right_options, sorted(right_vals)


@app.callback(
    Output("titer-store", "data"),
    Input("load-volume-table", "data"),
    prevent_initial_call=True
)
def update_titer_from_table(table_data):
    if table_data and isinstance(table_data, list) and len(table_data) > 0:
        titer_val = table_data[0].get("titer", 0.0)
        return {"titer": titer_val}
    return {"titer": 0.0}


# Fraction Table (only for single mode)
@app.callback(
    [Output("fraction-table", "columns"),
     Output("fraction-table", "data")],
    [Input("selected-result-id", "data"),
     Input("x-axis-offset", "data"),
     Input("plot-mode-radio", "value")],
    [State("extinction-coefficient", "value"),
     State("chromatogram-data", "data"),
     State("phases-data", "data")],
    prevent_initial_call=True
)
def update_fraction_table(result_id, x_offset, plot_mode, extinction_coeff, chrom_data, phases_data):
    if plot_mode == "overlay" or not result_id:
        return [], []

    if not chrom_data or not phases_data:
        return [], []

    # Convert chromatogram data from dict records back to DataFrame
    chrom_df = pd.DataFrame(chrom_data)

    # Check if DataFrame is empty or missing required columns
    if chrom_df.empty:
        print("DEBUG: Chromatogram DataFrame is empty")
        return [], []

    if "date_time" not in chrom_df.columns:
        print(f"DEBUG: date_time column missing. Available columns: {list(chrom_df.columns)}")
        return [], []

    chrom_df["date_time"] = pd.to_datetime(chrom_df["date_time"])
    chrom_df = chrom_df.sort_values("date_time")

    fraction_qs = AktaFraction.objects.filter(result_id=result_id).order_by("date_time")
    if not fraction_qs.exists():
        print(f"DEBUG: No fractions found for result_id: {result_id}")
        return [], []

    frac_df = pd.DataFrame(list(fraction_qs.values("date_time", "fraction")))
    frac_df["date_time"] = pd.to_datetime(frac_df["date_time"])
    frac_df = frac_df.drop_duplicates(subset=["fraction"]).reset_index(drop=True)

    start_mls = []
    for t in frac_df["date_time"]:
        idx = (chrom_df["date_time"] - t).abs().idxmin()
        start_mls.append(chrom_df.loc[idx, "ml"] if pd.notnull(idx) else None)

    frac_df["start_ml"] = start_mls
    frac_df["end_ml"] = frac_df["start_ml"].shift(-1)
    frac_df["volume_ml"] = frac_df["end_ml"] - frac_df["start_ml"]

    frac_df = frac_df[~frac_df["fraction"].str.lower().str.contains("waste", na=False)].copy()

    auc_list = []
    mass_list = []
    conc_list = []

    e1_percent = extinction_coeff
    path_length = 0.2
    ext_coeff = e1_percent * path_length * 100

    chrom_df = chrom_df.sort_values("ml")

    for _, row in frac_df.iterrows():
        start = row["start_ml"]
        end = row["end_ml"]
        vol = row["volume_ml"]

        subset = chrom_df[(chrom_df["ml"] >= start) & (chrom_df["ml"] <= end)]

        if not subset.empty and "uv_1_280" in chrom_df.columns:
            auc = np.trapz(subset["uv_1_280"].fillna(0), subset["ml"])
            mass = auc / ext_coeff if ext_coeff else 0
            conc = mass / vol if vol > 0 else 0
        else:
            auc = mass = conc = 0

        auc_list.append(round(auc, 2))
        mass_list.append(round(mass, 2))
        conc_list.append(round(conc, 2))

    frac_df["auc"] = auc_list
    frac_df["mass"] = mass_list
    frac_df["concentration"] = conc_list

    phases_df = pd.DataFrame(phases_data)
    phases_df["start_ml"] = pd.to_numeric(phases_df["start_ml"], errors="coerce")
    phases_df["end_ml"] = pd.to_numeric(phases_df["end_ml"], errors="coerce")

    phase_labels = []
    for _, row in frac_df.iterrows():
        f_start = row["start_ml"]
        f_end = row["end_ml"]
        matched_phases = []

        if pd.notnull(f_start) and pd.notnull(f_end) and (f_end > f_start):
            for _, p in pd.DataFrame(phases_data).iterrows():
                p_start = p.get("start_ml")
                p_end = p.get("end_ml")

                if pd.notnull(p_start) and pd.notnull(p_end):
                    overlap_start = max(f_start, p_start)
                    overlap_end = min(f_end, p_end)

                    overlap_length = max(0.0, overlap_end - overlap_start)
                    fraction_length = f_end - f_start
                    overlap_fraction = overlap_length / fraction_length

                    if overlap_fraction >= 0.1:
                        matched_phases.append(p["label"])

        phase_labels.append(" / ".join(matched_phases) if matched_phases else "")

    frac_df["phase"] = phase_labels

    display_df = frac_df[[
        "fraction", "phase", "start_ml", "end_ml", "volume_ml", "auc", "mass", "concentration"
    ]].dropna()

    if x_offset:
        display_df['start_ml'] = display_df['start_ml'] - x_offset
        display_df['end_ml'] = display_df['end_ml'] - x_offset

    display_df = display_df.round(2)
    display_df = display_df.rename(columns={
        "fraction": "Fraction",
        "phase": "Phase(s)",
        "start_ml": "Start (mL)",
        "end_ml": "End (mL)",
        "volume_ml": "Volume (mL)",
        "auc": "AUC (mAU·mL)",
        "mass": "Mass (mg)",
        "concentration": "Conc. (mg/mL)"
    })

    columns = [{"name": col, "id": col} for col in display_df.columns]
    data = display_df.to_dict("records")

    return columns, data


@app.callback(
    Output("chromatogram-graph", "figure"),
    Output("load-volume-store", "data"),
    Output("x-axis-offset", "data"),
    Input("chromatogram-data", "data"),
    Input("phases-data", "data"),
    Input("left-sensor-dropdown", "value"),
    Input("right-sensor-dropdown", "value"),
    Input("plot-options-checklist", "value"),
    Input("plot-mode-radio", "value"),
    State("selected-result-id", "data"),
    State("all-samples-data", "data"),
    State("selected-result-ids", "data"),
    prevent_initial_call=True
)
def update_chromatogram_plot(chrom_data, phase_data, left_sensors, right_sensors, plot_options,
                             plot_mode, result_id, all_data, selected_ids):
    print(f"DEBUG: update_chromatogram_plot called with:")
    print(f"  - result_id: {result_id}")
    print(f"  - plot_mode: {plot_mode}")
    print(f"  - chrom_data length: {len(chrom_data) if chrom_data else 0}")
    print(f"  - phase_data length: {len(phase_data) if phase_data else 0}")

    fig = go.Figure()

    if plot_mode == "single":
        # Single sample plotting logic
        if not result_id:
            print("DEBUG: No result_id for single mode")
            return go.Figure(), {}, 0.0

        if not chrom_data or not phase_data:
            print("DEBUG: Missing chromatogram or phase data for single mode")
            return go.Figure(), {}, 0.0

        df = pd.DataFrame(chrom_data).sort_values("ml")
        phases_df = pd.DataFrame(phase_data)

        print(f"DEBUG: Single mode - DataFrame shape: {df.shape}, Phases shape: {phases_df.shape}")

        offset_ml = 0.0
        load_store_data = {}
        sample_app_phase = phases_df[phases_df["label"] == "Sample Application"]
        if not sample_app_phase.empty and pd.notnull(sample_app_phase.iloc[0]["start_ml"]):
            start_ml = sample_app_phase.iloc[0]["start_ml"]
            end_ml = sample_app_phase.iloc[0]["end_ml"]
            load_store_data = {
                "start_ml": round(start_ml, 2),
                "end_ml": round(end_ml, 2),
                "load_volume": round(end_ml - start_ml, 2)
            }
            if "zero_ml" in (plot_options or []):
                offset_ml = start_ml
                df["ml"] = df["ml"] - offset_ml
                phases_df["start_ml"] = phases_df["start_ml"] - offset_ml
                phases_df["end_ml"] = phases_df["end_ml"] - offset_ml

        if df.empty:
            print("DEBUG: DataFrame is empty after processing")
            return fig, load_store_data, offset_ml

        # Add single sample traces
        fig = plot_single_sample(fig, df, left_sensors, right_sensors, phases_df, result_id, plot_options, offset_ml)
        print("DEBUG: Single sample plot created successfully")

    else:  # overlay mode
        if not all_data or not selected_ids:
            print("DEBUG: Missing all_data or selected_ids for overlay mode")
            return go.Figure(), {}, 0.0

        # Plot multiple samples
        fig = plot_overlay_samples(fig, all_data, selected_ids, left_sensors, right_sensors, plot_options)
        offset_ml = 0.0
        load_store_data = {}
        print("DEBUG: Overlay plot created successfully")

    return fig, load_store_data, offset_ml