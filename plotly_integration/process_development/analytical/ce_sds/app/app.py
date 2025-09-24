from datetime import datetime
from .layout import layout
import dash
import pandas as pd
import numpy as np
from dash import dcc, html, Input, Output, State, dash_table
from dash.exceptions import PreventUpdate
from django_plotly_dash import DjangoDash
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from plotly_integration.models import (
    CESDSReport,SampleMetadata, TimeSeriesData, PeakResults)
from plotly_integration.process_development.analytical.ce_sds.app.database_funcs import get_timeseries_data, \
    get_peak_results, get_metadata_from_source
from plotly_integration.process_development.analytical.ce_sds.app.plotting_funcs import shade_peak, calculate_baseline, \
    process_peaks, add_annotations_for_peaks

app = DjangoDash("CESDSReportViewerApp")

app.layout = layout



def generate_electropherogram(
        result_ids=None,
        sample_type = 'reduced',
        title="Electropherograms",
        marker_rt=None,
        marker_label="10 kDa",
        light_chain_time=None,
        regression_params=None,
        y_scale=1,
        subplot_vertical_spacing=0.25,
        show_mw_in_annotations=True,
        annotation_positioning='fixed',
        reduced_table_data=None,
        autoscale_x=False,
):
    """Generate electropherogram figure and table data"""
    if result_ids:
        results = get_metadata_from_source(result_ids)
        result_df = {}
    else:
        return go.Figure(), []

    for result in results:
        #Function to get time series data
        df = get_timeseries_data(result.result_id)

        if df.empty or "time_min" not in df.columns or "channel_1" not in df.columns:
            continue

        result_df[str(result.id)] = {
            "sample_id": result.sample_id_full,
            "data": df.sort_values("time_min")
        }

        #Get peak results from Peak Results Table
        peaks = get_peak_results(result.result_id)
        if peaks:
            result_df[str(result.id)]["peaks"] = peaks

    # Initialize table_output as empty list
    table_output = []

    #Parse regression parameters
    regression_slope = regression_params.get("slope") if regression_params else None
    regression_intercept = regression_params.get("intercept") if regression_params else None
    # show_mw_in_annotations is now passed as a boolean from the callbacks

    #Initialize subplots
    num_rows = len(result_df)
    fig = make_subplots(
        rows=num_rows, cols=1,
        shared_xaxes=False,
        vertical_spacing=subplot_vertical_spacing,
        subplot_titles=[meta["sample_id"] for meta in result_df.values()]
    )

    # Iterate through each sample and plot
    for i, (mid, meta) in enumerate(result_df.items(), start=1):
        df = meta["data"]
        if df.empty:
            continue

        # Plot the chromatogram line
        fig.add_trace(
            go.Scatter(
                x=df["time_min"],
                y=df["channel_1"],
                mode="lines",
                name=meta["sample_id"],
                line=dict(color="#2E86AB", width=1.5)  # Consistent blue color, thinner line
            ),
            row=i, col=1
        )

        # Calculate baseline for the entire chromatogram once
        df_length = len(df)
        window = min(350, max(50, df_length // 20))  # Dynamic window size based on data length
        full_signal = df["channel_1"].values
        full_time = df["time_min"].values
        full_baseline = calculate_baseline(full_signal, window=window)


        # Annotate marker peak if specified
        marker_peak_time = None
        if marker_rt is not None:
            df_marker = df[(df["time_min"] >= marker_rt - 0.5) & (df["time_min"] <= marker_rt + 0.5)]
            if not df_marker.empty:
                idx = df_marker["channel_1"].idxmax()
                marker_peak_time = df_marker.loc[idx, "time_min"]
                peak_height = df_marker.loc[idx, "channel_1"]
                fig.add_annotation(
                    x=marker_peak_time,
                    y=peak_height,
                    text=f"{marker_label} ({marker_peak_time:.2f} min)",
                    showarrow=True,
                    arrowhead=1,
                    ax=0,
                    ay=-40,
                    row=i, col=1
                )

        # Use Empower integration for peak detection
        if "peaks" in meta and meta["peaks"]:
            print(f"Using Empower peaks for sample {meta['sample_id']}")

            # For non-reduced samples, try to find corresponding reduced sample reference times from table data
            reduced_reference_times = None
            if sample_type == 'non-reduced' and reduced_table_data:
                # Look for corresponding reduced sample by removing 'NR' prefix and adding 'R'
                current_sample_id = meta["sample_id"]
                reduced_sample_id = current_sample_id
                if current_sample_id.startswith('NR '):
                    reduced_sample_id = 'R ' + current_sample_id[3:]
                elif current_sample_id.startswith('NR'):
                    reduced_sample_id = 'R' + current_sample_id[2:]

                # Find the corresponding reduced sample in the table data
                for row in reduced_table_data:
                    if row.get('Sample Name') == reduced_sample_id:
                        lc_time = row.get('Light Chain Time')
                        hc_time = row.get('Heavy Chain Time')
                        if lc_time is not None or hc_time is not None:
                            reduced_reference_times = {
                                'light_chain': lc_time,
                                'heavy_chain': hc_time
                            }
                            print(f"[DEBUG] Found reduced reference for {current_sample_id}: LC={lc_time}, HC={hc_time}")
                            break

            # Process all peaks using the refactored function
            peak_results = process_peaks(
                peaks=meta["peaks"],
                sample_name=meta["sample_id"],
                sample_type=sample_type,
                light_chain_time=light_chain_time,
                marker_peak_time=marker_peak_time,
                df=df,
                regression_params=regression_params,
                reduced_reference_times=reduced_reference_times
            )

            # Extract results
            classified_peaks = peak_results['classified_peaks']
            percentages = peak_results['percentages']
            mw_values = peak_results['mw_values']
            peak_times = peak_results['peak_times']
        else:
            # No peaks available - empty result
            print(f"[DEBUG] No Empower peaks available for sample {meta['sample_id']}")
            classified_peaks = []
            if sample_type == 'reduced':
                percentages = {"LMW": 0.0, "Light Chain": 0.0, "Heavy Chain": 0.0, "HMW": 0.0}
                mw_values = {"LMW": None, "Light Chain": None, "Heavy Chain": None, "HMW": None}
                peak_times = {"LMW": None, "Light Chain": None, "Heavy Chain": None, "HMW": None}
            else:
                percentages = {"LMW": 0.0, "Light Chain": 0.0, "Intact": 0.0, "HMW": 0.0}
                mw_values = {"LMW": None, "Light Chain": None, "Intact": None, "HMW": None}
                peak_times = {"LMW": None, "Light Chain": None, "Intact": None, "HMW": None}

        # percentages, mw_values, and peak_times are already set from process_peaks

        max_signal = df["channel_1"].max()
        if not y_scale or y_scale == 1:
            fig.update_yaxes(title_text="UV", row=i, col=1)
        else:
            y_max = max_signal * y_scale
            fig.update_yaxes(
                title_text="UV",
                autorange=True,
                autorangeoptions=dict(maxallowed=y_max),
                row=i, col=1
            )

        fig.update_xaxes(title_text="Time (min)", row=i, col=1)


        # First, shade all the original peaks (not combined)
        for p, class_label in classified_peaks:
            shade_peak(
                fig, df,
                start_time=p.get("start_time"),
                end_time=p.get("end_time"),
                class_label=class_label,
                row=i, col=1,
                full_baseline=full_baseline,
                full_time=full_time
            )

        # Add annotations for all peaks using the unified function
        add_annotations_for_peaks(
            fig=fig,
            classified_peaks=classified_peaks,
            row=i,
            col=1,
            positioning_method=annotation_positioning,
            show_mw_in_annotations=show_mw_in_annotations,
            y_scale=y_scale,
            y_max=y_max if y_scale and y_scale != 1 else None,
            sample_type=sample_type
        )

        # Check total percentage
        total_pct = sum(percentages.values())
        if total_pct > 0 and abs(total_pct - 100) > 1e-2:
            print(f"[DEBUG] {meta['sample_id']} percentages do not sum to 100%: {total_pct:.2f}%")

        if table_output is not None:
            row_data = {
                "Sample Name": meta["sample_id"],
                "LMW (%)": round(percentages.get("LMW", 0), 1),
                "Light Chain (%)": round(percentages.get("Light Chain", 0), 1),
                "HMW (%)": round(percentages.get("HMW", 0), 1),
            }

            # Add sample type specific columns
            if sample_type == 'reduced':
                row_data["Heavy Chain (%)"] = round(percentages.get("Heavy Chain", 0), 1)
                row_data["Heavy Chain MW (kDa)"] = mw_values.get("Heavy Chain")
                row_data["Heavy Chain Time"] = peak_times.get("Heavy Chain")
            else:  # non-reduced
                row_data["Intact (%)"] = round(percentages.get("Intact", 0), 1)
                row_data["Intact MW (kDa)"] = mw_values.get("Intact")
                row_data["Intact Time"] = peak_times.get("Intact")

            # Add common MW and time columns
            row_data.update({
                "LMW MW (kDa)": mw_values.get("LMW"),
                "Light Chain MW (kDa)": mw_values.get("Light Chain"),
                "HMW MW (kDa)": mw_values.get("HMW"),
                "LMW Time": peak_times.get("LMW"),
                "Light Chain Time": peak_times.get("Light Chain"),
                "HMW Time": peak_times.get("HMW"),
            })

            table_output.append(row_data)

    # Apply autoscaling if enabled
    if autoscale_x and marker_rt is not None:
        # Find the start time: 45 seconds (0.75 minutes) before marker
        x_start = marker_rt - 0.75

        # Find the end time: 30 seconds after the last peak's end time
        x_end = marker_rt + 2.0  # Default fallback

        # Look through all classified peaks to find the latest end time
        latest_end_time = 0
        for p, _ in classified_peaks:
            peak_end = p.get('end_time')
            if peak_end and peak_end > latest_end_time:
                latest_end_time = peak_end

        if latest_end_time > 0:
            x_end = latest_end_time + 0.5  # 30 seconds after last peak

        print(f"[DEBUG] Autoscaling X-axis from {x_start:.2f} to {x_end:.2f} minutes")

        # Apply the x-axis range to all subplots
        for i in range(1, num_rows + 1):
            fig.update_xaxes(range=[x_start, x_end], row=i, col=1)

    fig.update_layout(
        height=300 * num_rows,
        title=title,
        showlegend=False,
        template="plotly_white",
        margin=dict(t=40, b=40, l=40, r=30)
    )
    return fig, table_output


@app.callback(
    [Output("reduced-chromatogram", "figure"),
     Output("reduced-chromatogram", "config"),
     Output("reduced-table", "data"),
     Output("reduced-table", "columns")],

    [
        Input("reduced-result-ids", "data"),
        Input("marker-rt", "value"),
        Input("marker-label", "value"),
        Input("light-chain-time", "value"),
        Input("standard-regression-params", "data"),
        Input("reduced-y-axis-scaling", "value"),
        Input("reduced-subplot-vertical-spacing", "value"),
        Input("reduced-show-mw-checklist", "value"),
        Input("reduced-autoscale-checklist", "value"),
        Input("reduced-annotation-positioning", "value"),
        Input("main-tabs", "value"),
        Input("selected-report", "data"),
    ]
)
def reduced_callback(result_ids, marker_rt, marker_label, light_chain_time,
                     regression_params, y_scale, subplot_vertical_spacing, show_mw_in_annotations, autoscale_checklist, annotation_positioning,
                     active_tab, selected_report):
    # Parse display options
    show_mw = 'show_mw' in show_mw_in_annotations if show_mw_in_annotations else False
    autoscale_x = 'autoscale_x' in autoscale_checklist if autoscale_checklist else False

    # Use the unified generate_electropherogram function with sample_type='reduced'
    fig, table_data = generate_electropherogram(
        result_ids=result_ids,
        sample_type='reduced',
        title="Reduced Chromatograms with Peak Classification",
        marker_rt=marker_rt,
        marker_label=marker_label,
        light_chain_time=light_chain_time,
        regression_params=regression_params,
        y_scale=y_scale,
        subplot_vertical_spacing=subplot_vertical_spacing,
        show_mw_in_annotations=show_mw,
        annotation_positioning=annotation_positioning,
        autoscale_x=autoscale_x
    )

    columns = [{"name": k, "id": k} for k in table_data[0].keys()] if table_data else []

    report_name = CESDSReport.objects.filter(
        id=selected_report).first().report_name if selected_report else "CESDS_Report"

    plot_config = {
        'toImageButtonOptions': {
            'filename': f"{datetime.now().strftime('%Y%m%d')}-R-{report_name}",
            'format': 'png',
        }}

    return fig, plot_config, table_data, columns

@app.callback(
    [
        Output("nonreduced-chromatogram", "figure"),
        Output("nonreduced-chromatogram", "config"),
        Output("nonreduced-table", "data"),
        Output("nonreduced-table", "columns")
    ],
    [
        Input("nonreduced-result-ids", "data"),
        Input("nr-marker-rt", "value"),
        Input("nr-marker-label", "value"),
        Input("standard-regression-params", "data"),
        Input("non-reduced-y-axis-scaling", "value"),
        Input("non-reduced-subplot-vertical-spacing", "value"),
        Input("nonreduced-show-mw-checklist", "value"),
        Input("nonreduced-autoscale-checklist", "value"),
        Input("nonreduced-annotation-positioning", "value"),
        Input("main-tabs", "value"),
        Input("selected-report", "data"),
        State("reduced-table", "data"),
    ]
)
def nonreduced_callback(result_ids, marker_rt, marker_label, regression_params, y_scale,
                        subplot_vertical_spacing, show_mw_checklist, autoscale_checklist, annotation_positioning, active_tab,
                        selected_report, reduced_table_data):
    # Parse display options
    show_mw = 'show_mw' in show_mw_checklist if show_mw_checklist else False
    autoscale_x = 'autoscale_x' in autoscale_checklist if autoscale_checklist else False

    # Use the unified generate_electropherogram function with sample_type='non-reduced'
    fig, table_data = generate_electropherogram(
        result_ids=result_ids,
        sample_type='non-reduced',
        title="Non-Reduced Chromatograms with Peak Classification",
        marker_rt=marker_rt,
        marker_label=marker_label,
        light_chain_time=None,  # Light chain time not typically used for non-reduced
        regression_params=regression_params,
        y_scale=y_scale,
        subplot_vertical_spacing=subplot_vertical_spacing,
        show_mw_in_annotations=show_mw,
        annotation_positioning=annotation_positioning,
        reduced_table_data=reduced_table_data,
        autoscale_x=autoscale_x
    )

    columns = [{"name": k, "id": k} for k in table_data[0].keys()] if table_data else []

    report_name = CESDSReport.objects.filter(
        id=selected_report).first().report_name if selected_report else "CESDS_Report"

    plot_config = {
        'toImageButtonOptions': {
            'filename': f"{datetime.now().strftime('%Y%m%d')}-NR-{report_name}",
            'format': 'png',
        }}

    return fig, plot_config, table_data, columns



