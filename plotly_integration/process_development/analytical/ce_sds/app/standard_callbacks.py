import numpy as np
import pandas as pd
import plotly.graph_objects as go
from .app import app
from dash import Input, Output, State
from scipy.signal import find_peaks
from scipy.stats import linregress
from .database_funcs import get_metadata_from_source, get_timeseries_data

# Standard Analysis Logic
@app.callback(
    Output("standard-id-dropdown", "options"),
    Input("selected-result-ids", "data")
)
def get_std_dropdown_options(result_ids):
    if not result_ids:
        return []

    # Always use unified tables
    metas = get_metadata_from_source(result_ids)
    # Filter for standards (STD in sample name)
    stds = [m for m in metas if m.sample_id_full and "std" in m.sample_id_full.lower()]

    return [{"label": s.sample_id_full, "value": s.id} for s in stds]


@app.callback(
    Output("standard-id-dropdown", "value"),
    Input("standard-id-dropdown", "options")
)
def auto_select_first_std(options):
    if options:
        return options[0]["value"]
    return None


@app.callback(
    [
        Output("standard-peak-plot", "figure"),
        Output("std-detected-peak-table", "data")
    ],
    [
        Input("standard-id-dropdown", "value"),
        State("num-std-peaks", "value")
    ]
)
def plot_std_chromatogram_and_generate_table(metadata_id, num_to_keep):
    if not metadata_id:
        return go.Figure(), []

    # Use helper function to get time series data from unified tables
    df = get_timeseries_data(metadata_id)
    if df.empty:
        return go.Figure(), []

    # Plot full chromatogram
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["time_min"],
        y=df["channel_1"],
        mode="lines",
        name="STD Chromatogram",
        line=dict(color="#2E86AB", width=1.5)  # Consistent blue color, thinner line
    ))

    # Filter to >5 min for peak detection
    df_filtered = df[df["time_min"] > 5.0]
    if df_filtered.empty:
        return fig, []

    x = df_filtered["time_min"].values
    y = df_filtered["channel_1"].values
    peak_indices, _ = find_peaks(y, distance=5)
    all_peaks = [{"peak_rt": x[i], "peak_height": y[i]} for i in peak_indices]

    # Step 1: Take top N peaks by height
    top_peaks = sorted(all_peaks, key=lambda p: p["peak_height"], reverse=True)[:num_to_keep or 7]

    # Step 2: Sort selected peaks by RT (ascending)
    sorted_peaks = sorted(top_peaks, key=lambda p: p["peak_rt"])

    # Step 3: Assign MWs linearly (left = 10 kDa, right = 250 kDa)
    default_mws = [10, 20, 35, 50, 100, 150, 250]
    assigned_mws = default_mws[:len(sorted_peaks)]

    table_data = []
    for i, peak in enumerate(sorted_peaks):
        table_data.append({
            "peak_rt": round(peak["peak_rt"], 3),
            "peak_height": round(peak["peak_height"], 3),
            "assigned_mw": assigned_mws[i] if i < len(assigned_mws) else ""
        })

    # Add peak markers to plot
    fig.add_trace(go.Scatter(
        x=[p["peak_rt"] for p in sorted_peaks],
        y=[p["peak_height"] for p in sorted_peaks],
        mode="markers+text",
        text=[f"{i + 1}" for i in range(len(sorted_peaks))],
        textposition="top center",
        marker=dict(color="red", size=8),
        name="Top Peaks"
    ))

    fig.update_layout(
        title="Standard Chromatogram with Assigned Peaks",
        xaxis_title="Time (min)",
        yaxis_title="UV (Channel 1)",
        template="plotly_white"
    )

    return fig, table_data


@app.callback(
    [
        Output("regression-equation", "children"),
        Output("r-squared-value", "children"),
        Output("regression-plot", "figure"),
        Output("estimated-mw", "children"),
        Output("standard-regression-params", "data")
    ],
    [
        Input("std-detected-peak-table", "data"),
        Input("std-detected-peak-table", "selected_rows"),
        Input("rt-input", "value")
    ]
)
def run_linear_mw_regression(table_data, selected_rows, rt_input):
    if not table_data or not selected_rows:
        return "No selected points", "N/A", go.Figure(), "N/A", {}

    df = pd.DataFrame(table_data)
    df = df.iloc[selected_rows]  # Only keep selected rows
    df = df.dropna(subset=["peak_rt", "assigned_mw"])
    df = df[df["assigned_mw"] > 0]

    if df.shape[0] < 2:
        return "Select ≥2 points", "N/A", go.Figure(), "N/A", {}

    try:
        x = df["peak_rt"]
        y = np.log(df["assigned_mw"])
        slope, intercept, r_value, _, _ = linregress(x, y)

        # Generate regression line
        x_vals = np.linspace(x.min(), x.max(), 100)
        y_vals = slope * x_vals + intercept

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x,
            y=np.log(df["assigned_mw"]),  # y = log(MW)
            mode="markers+text",
            text=[f"{mw:.0f} kDa" for mw in df["assigned_mw"]],  # ✅ correct label from original MWs
            textposition="top center",
            name="Selected Points"
        ))
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines",
            name="Regression Line",
            line=dict(color="#E74C3C", width=2, dash="dash")  # Red dashed line for regression
        ))
        fig.update_layout(
            title="Log MW vs Retention Time",
            xaxis_title="Retention Time (min)",
            yaxis_title="Log MW (kDa)",
            template="plotly_white"
        )

        estimated_mw = "N/A"
        if rt_input is not None:
            log_mw = slope * rt_input + intercept
            estimated_mw = f"{np.exp(log_mw) / 1000:.2f} kD"

        return (
            f"MW = {slope:.3f} × RT + {intercept:.3f}",
            f"R² = {r_value ** 2:.4f}",
            fig,
            estimated_mw,
            {"slope": slope, "intercept": intercept}
        )

    except Exception as e:
        return f"Error: {e}", "N/A", go.Figure(), "N/A", {}


@app.callback(
    Output("std-detected-peak-table", "selected_rows"),
    Input("std-detected-peak-table", "data")
)
def auto_select_all_std_peaks(data):
    return list(range(len(data))) if data else []