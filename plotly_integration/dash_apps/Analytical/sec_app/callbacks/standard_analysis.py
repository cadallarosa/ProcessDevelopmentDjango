from collections import Counter
import dash
import numpy as np
import pandas as pd
from dash import Input, Output, State, html
import plotly.graph_objects as go
from scipy.stats import linregress

from plotly_integration.models import Report, SampleMetadata, TimeSeriesData
from ..app import app


def get_filtered_std_ids(report_id):
    """
    Retrieve all standard result IDs from the most relevant sample set for the given report ID,
    including the associated sample names.

    Args:
        report_id (str): The ID of the selected report.

    Returns:
        List[Tuple]: A list of tuples containing (std_result_id, sample_name, std_sample).
    """
    try:
        # Retrieve the report
        report = Report.objects.filter(report_id=report_id).first()
        if not report:
            return [("No STD Found", "Unknown Sample", None)]  # Ensure return format is consistent

        # Extract selected sample names **with exact match**
        selected_result_ids = [result_id.strip() for result_id in report.selected_result_ids.split(",") if
                               result_id.strip()]

        # Fetch all sample set names **linked to the exact selected samples**
        sample_set_entries = SampleMetadata.objects.filter(result_id__in=selected_result_ids) \
            .values_list("sample_name", "sample_set_name")

        # Count occurrences of each sample set
        sample_set_counts = Counter([entry[1] for entry in sample_set_entries])

        # If no sample sets are found, return an empty result
        if not sample_set_counts:
            return [("No STD Found", "Unknown Sample", None)]

        # Select the most common sample set (assumes correct set has most samples)
        most_common_sample_set = sample_set_counts.most_common(1)[0][0]

        # Debugging Output
        print(f"Extracted Sample Names: {selected_result_ids}")
        print(f"Detected Sample Set Names: {list(sample_set_counts.keys())}")
        print(f"✔ Using Most Common Sample Set: {most_common_sample_set}")

        # Retrieve standard IDs **only from this sample set**
        std_samples = SampleMetadata.objects.filter(
            sample_set_name=most_common_sample_set,  # Ensure correct filtering
            sample_prefix="STD"
        ).distinct()

        std_result_list = []
        for sample in std_samples:
            std_id = sample.result_id
            sample_name = getattr(sample, "sample_name", "Unknown Sample")  # Handle missing sample name safely
            std_result_list.append((std_id, sample_name, sample))

        return std_result_list if std_result_list else [("No STD Found", "Unknown Sample", None)]

    except Exception as e:
        print(f"Error retrieving standard result IDs: {e}")
        return [("No STD Found", "Unknown Sample", None)]


@app.callback(
    [
        Output('standard-id-dropdown', 'options'),  # Update dropdown options
        Output("std-result-id-store", "data"),  # Store first available standard ID
        Output('standard-id-dropdown', 'value')
    ],
    [Input("selected-report", "data")],
    prevent_initial_call=True
)
def update_standard_id_dropdown(selected_report):
    report_id = selected_report
    print(f'this is the stored report id {selected_report}')
    report = Report.objects.filter(report_id=report_id).first()

    if not report:
        return [], None

    # Retrieve standard IDs using the updated function
    std_results = get_filtered_std_ids(report.report_id)

    # Format dropdown options with sample name and standard ID
    dropdown_options = [
        {'label': f"{sample_name} - STD {std_id}", 'value': std_id}
        for std_id, sample_name, _ in std_results if std_id != "No STD Found"
    ]

    # Automatically select the first standard ID
    first_std_id = dropdown_options[0]['value'] if dropdown_options else "No STD Found"

    print(f"🔄 Auto-selecting first standard: {first_std_id}")  # Debugging

    return dropdown_options, first_std_id, first_std_id


def get_top_peaks(result_id):
    """
    Try to match known standard peaks by retention time. If match quality is poor,
    fall back to selecting top peaks by area.
    """
    import pandas as pd
    from plotly_integration.models import PeakResults  # adjust if needed

    # Fetch peak results
    peaks = PeakResults.objects.filter(result_id=result_id).values(
        "peak_name", "peak_retention_time", "height", "area", "asym_at_10", "plate_count", "res_hh"
    )
    df = pd.DataFrame(list(peaks))

    if df.empty:
        return df

    # Optional cutoff to ignore noise peaks
    df = df[df["peak_retention_time"] <= 18]

    # Define expected retention times
    target_peaks = {
        "Peak1-Thyroglobulin": 7.11,
        "Peak2-IgG": 8.95,
        "Peak3-BSA": 10.1,
        "Peak4-Myoglobin": 12.23,
        "Peak5-Uracil": 16.0
    }

    max_allowed_diff = 0.75  # fallback threshold in minutes
    matched_peaks = []
    used_indices = set()

    for name, target_rt in target_peaks.items():
        df["rt_diff"] = (df["peak_retention_time"] - target_rt).abs()
        candidates = df[~df.index.isin(used_indices)]

        if candidates.empty:
            continue

        closest_idx = candidates["rt_diff"].idxmin()
        closest_peak = candidates.loc[closest_idx]

        # Only accept match if within threshold
        if closest_peak["rt_diff"] <= max_allowed_diff:
            peak_copy = closest_peak.copy()
            peak_copy["peak_name"] = name
            matched_peaks.append(peak_copy)
            used_indices.add(closest_idx)

    if len(matched_peaks) >= 3:  # Only use matched peaks if enough are found
        df_result = pd.DataFrame(matched_peaks).drop(columns="rt_diff", errors="ignore")
        return df_result.reset_index(drop=True)

    # 🔁 Fallback: top 5 peaks by area, sorted by retention time
    df = df.sort_values(by="area", ascending=False).iloc[:5]
    df = df.sort_values(by="peak_retention_time").reset_index(drop=True)

    ordered_peak_names = list(target_peaks.keys())[:len(df)]
    df["peak_name"] = ordered_peak_names
    return df


@app.callback(
    Output('standard-peak-plot', 'figure'),
    Input('standard-id-dropdown', 'value'),
    prevent_initial_call=True
)
def update_standard_plot(standard_id):
    if not standard_id or standard_id == "No STD Found":
        return go.Figure()

    # Fetch time series data
    time_series = TimeSeriesData.objects.filter(result_id=standard_id).values("time", "channel_1")
    df_time = pd.DataFrame(time_series)

    if df_time.empty:
        return go.Figure()

    # Fetch and process the top 6 peaks
    df_peaks = get_top_peaks(standard_id)

    if df_peaks.empty:
        return go.Figure()

    # Function to find the closest y-value in time series for a given retention time
    def get_closest_time_series_value(retention_time):
        closest_idx = (df_time["time"] - retention_time).abs().idxmin()
        return df_time.loc[closest_idx, "channel_1"] if closest_idx in df_time.index else None

    # Create Plotly figure
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=df_time["time"], y=df_time["channel_1"], mode='lines', name=f"STD {standard_id} - Channel 1"))

    # Ensure annotation is placed at the correct peak height from time series
    for _, row in df_peaks.iterrows():
        y_value = get_closest_time_series_value(row["peak_retention_time"])
        if y_value is not None:
            fig.add_annotation(x=row["peak_retention_time"], y=y_value, text=row["peak_name"], showarrow=True,
                               arrowhead=2)

    fig.update_layout(title=f"Time Series for Standard ID {standard_id}", xaxis_title="Time (min)",
                      yaxis_title="UV280", template="plotly_white")
    return fig


@app.callback(
    [
        Output("regression-equation", "children"),
        Output("r-squared-value", "children"),
        Output("regression-plot", "figure"),
        Output("estimated-mw", "children"),
        Output("standard-table", "data"),
        Output("regression-parameters", "data"),  # Store slope and intercept
    ],
    [
        Input('standard-id-dropdown', 'value'),
        Input("standard-table", "selected_rows"),  # Ensure selection is passed
        State("standard-table", "data"),
        State("rt-input", "value"),
    ],
    prevent_initial_call=True
)
def standard_analysis(std_result_id, selected_rows, table_data, rt_input):
    if not std_result_id or std_result_id == "No STD Found":
        return "No STD Selected", "N/A", {}, "N/A", [], {'slope': 0, 'intercept': 0}

    # Fetch and process the top 6 peaks
    df = get_top_peaks(std_result_id)

    if df.empty:
        return "No Peak Results Found", "N/A", {}, "N/A", [], [], {'slope': 0, 'intercept': 0}

    # Assign Molecular Weight (MW)
    MW_MAPPING = {
        'Peak1-Thyroglobulin': 660000,
        'Peak2-IgG': 150000,
        'Peak3-BSA': 66400,
        'Peak4-Myoglobin': 17000,
        'Peak5-Uracil': 112
    }
    # Molecular weight mapping
    PERFORMANCE_MAPPING = {
        'Peak1-Thyroglobulin': 1000,
        'Peak2-IgG': 14000,
        'Peak3-BSA': 1000,
        'Peak4-Myoglobin': 1000,
        'Peak5-Uracil': 1000
    }
    df["MW"] = df["peak_name"].map(MW_MAPPING).fillna("N/A")

    # Add Performance column
    df["performance_cutoff"] = df["peak_name"].map(PERFORMANCE_MAPPING)

    # Add Pass/Fail column based on plate count
    def determine_pass_fail(row):
        # Ensure column_performance_cutoff is an integer
        column_performance_cutoff = PERFORMANCE_MAPPING.get(row["peak_name"], None)
        try:
            column_performance_cutoff = int(column_performance_cutoff)
        except (TypeError, ValueError):
            return "Fail"  # Default to "Fail" if the cutoff is invalid

        # Ensure plate_count is an integer
        try:
            plate_count = int(row["plate_count"])
        except (TypeError, ValueError):
            return "Fail"  # Default to "Fail" if plate_count is invalid

        # Compare plate_count to the cutoff
        if plate_count >= column_performance_cutoff:
            return "Pass"
        return "Fail"

    df["pass/fail"] = df.apply(determine_pass_fail, axis=1)
    # print(df)
    # Prepare table data
    table_data = df.to_dict("records")
    # print("Table Data for Display:", table_data)

    # Prepare table data
    table_data = df.to_dict("records")

    # **Ensure user selection persists**
    if not selected_rows or not table_data:
        return "No Points Selected for Regression", "N/A", {}, "N/A", table_data, selected_rows, {'slope': 0,
                                                                                                  'intercept': 0}

    # Retrieve selected peaks
    selected_data = [table_data[i] for i in selected_rows if i < len(table_data)]
    regression_df = pd.DataFrame(selected_data).dropna(subset=["MW", "peak_retention_time"])

    if regression_df.empty:
        return "Regression Data is Empty", "N/A", {}, "N/A", table_data, selected_rows, {'slope': 0, 'intercept': 0}

    # Perform regression
    regression_df = pd.DataFrame(selected_data).dropna(subset=["MW", "peak_retention_time"])
    if regression_df.empty:
        return "Regression Data is Empty", "N/A", {}, "N/A", table_data, {'slope': 0, 'intercept': 0}

    try:
        slope, intercept, r_value, _, _ = linregress(
            regression_df["peak_retention_time"], np.log(regression_df["MW"])
        )
    except Exception as e:
        print(f"Regression error: {e}")
        return "Regression Failed", "N/A", {}, "N/A", table_data, {'slope': 0, 'intercept': 0}

    # **Generate regression plot**
    x_vals = np.linspace(regression_df["peak_retention_time"].min(), regression_df["peak_retention_time"].max(), 100)
    y_vals = slope * x_vals + intercept
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=regression_df["peak_retention_time"],
        y=np.log(regression_df["MW"]),
        mode="markers+text",
        text=regression_df["peak_name"],
        textposition="top center",
        name="Data Points"
    ))
    fig.add_trace(go.Scatter
                  (x=x_vals,
                   y=y_vals,
                   mode="lines",
                   name="Regression Line",
                   line=dict(dash='dash')  # ✅ Makes the regression line dashed
                   ))
    fig.update_layout(
        title="Retention Time vs Log(MW)",
        xaxis_title="Retention Time (min)",
        yaxis_title="Log(MW)",
        template="plotly_white"
    )

    # **Estimate MW**
    estimated_mw = "N/A"
    if rt_input is not None:
        log_mw = slope * rt_input + intercept
        estimated_mw = f"{np.exp(log_mw) / 1000:.2f} kD"

    return (
        f"y = {slope:.4f}x + {intercept:.4f}",
        f"R² = {r_value ** 2:.4f}",
        fig,
        estimated_mw,
        table_data,
        {'slope': slope, 'intercept': intercept}
    )