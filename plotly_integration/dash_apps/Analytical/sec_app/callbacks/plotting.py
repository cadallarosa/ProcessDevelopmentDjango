import re

from plotly_integration.models import SampleMetadata, TimeSeriesData, Report
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
from dash import dcc, html, Input, Output, State, dash_table, Dash, MATCH, callback_context
from ..app import app

def generate_subplots_with_shading(selected_result_ids, sample_list, channels, enable_shading, enable_peak_labeling,
                                   main_peak_rt, slope,
                                   intercept, hmw_table_data, num_cols=3, vertical_spacing=0.05,
                                   horizontal_spacing=0.5):
    num_samples = len(sample_list)
    cols = num_cols
    rows = (num_samples // cols) + (num_samples % cols > 0)

    region_colors = {
        "HMW": "rgba(255, 87, 87, 0.85)",  # Coral Red
        "MP": "rgba(72, 149, 239, 0.85)",  # Sky Blue
        "LMW": "rgba(122, 230, 160, 0.85)"  # Mint Green
    }

    label_offsets = {
        "HMW": {"x_offset": -3, "y_offset": 0.02},
        "MP": {"x_offset": 0, "y_offset": 0.02},
        "LMW": {"x_offset": 2, "y_offset": 0.02}
    }

    fig = make_subplots(
        rows=rows,
        cols=cols,
        start_cell="top-left",
        subplot_titles=sample_list,  # NEED TO FIX THIS
        vertical_spacing=vertical_spacing,
        horizontal_spacing=horizontal_spacing
    )

    for i, result_id in enumerate(selected_result_ids):
        row = (i // cols) + 1
        col = (i % cols) + 1
        sample = SampleMetadata.objects.filter(result_id=result_id).first()
        if not sample:
            continue
        time_series = TimeSeriesData.objects.filter(result_id=sample.result_id)
        df = pd.DataFrame(list(time_series.values()))
        sample_name = sample.sample_name
        # Get HMW Table row for the current sample
        # ✅ Find HMW row safely
        hmw_row = next((r for r in hmw_table_data if isinstance(r, dict) and r.get('Sample Name') == sample_name), None)
        if not hmw_row:
            continue

        # Extract values from HMW Table
        main_peak_start = hmw_row.get("Main Peak Start", None)
        main_peak_end = hmw_row.get("Main Peak End", None)
        hmw_start = hmw_row.get("HMW Start", None)
        hmw_end = hmw_row.get("HMW End", None)
        lmw_start = hmw_row.get("LMW Start", None)
        lmw_end = hmw_row.get("LMW End", None)

        def safe_float(value):
            try:
                cleaned = re.sub(r"[^\d.]+", "", str(value))  # removes all but digits and dots
                return float(cleaned)
            except (ValueError, TypeError):
                return 0.0

        percentages = {
            "HMW": safe_float(hmw_row.get("HMW", 0)),
            "MP": safe_float(hmw_row.get("Main Peak", 0)),
            "LMW": safe_float(hmw_row.get("LMW", 0)),
        }

        for channel in channels:
            if channel in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['time'],
                        y=df[channel],
                        mode='lines',
                        line=dict(color="blue"),
                        name=f"{sample_name} - {channel}"
                    ),
                    row=row,
                    col=col
                )

                if enable_shading:
                    # Define shading regions using HMW Table data
                    shading_regions = {
                        "HMW": (hmw_start, hmw_end),
                        "MP": (main_peak_start, main_peak_end),
                        "LMW": (lmw_start, lmw_end)
                    }

                    for region, (start_time, end_time) in shading_regions.items():
                        try:
                            # Ensure numeric comparison
                            start_time = float(start_time) if pd.notna(start_time) else None
                            end_time = float(end_time) if pd.notna(end_time) else None
                        except ValueError:
                            start_time = end_time = None

                        if start_time is None or end_time is None:
                            continue  # Skip invalid regions

                        shading_region = df[(df['time'] >= start_time) & (df['time'] <= end_time)]
                        if not shading_region.empty:
                            fig.add_trace(
                                go.Scatter(
                                    x=shading_region['time'],
                                    y=shading_region[channel],
                                    fill='tozeroy',
                                    mode='none',
                                    fillcolor=region_colors[region],
                                    # opacity=0.01,
                                    name=f"{region} ({sample_name})"
                                ),
                                row=row,
                                col=col
                            )

                            if enable_peak_labeling:
                                # Annotate peaks using max value in the region
                                try:
                                    max_peak_row = shading_region.loc[shading_region[channel].idxmax()]
                                    max_retention_time = max_peak_row['time']
                                    max_peak_value = max_peak_row[channel]

                                    # Calculate MW using the max retention time
                                    log_mw = slope * max_retention_time + intercept
                                    mw = round(np.exp(log_mw) / 1000, 2)

                                    # Debug MW calculation
                                    # print(f"Sample: {sample_name}, Region: {region}, Max Retention Time: {max_retention_time}, MW: {mw}")

                                    # Apply offsets for labels
                                    x_offset = label_offsets[region]["x_offset"] + max_retention_time
                                    y_offset = label_offsets[region]["y_offset"] + max_peak_value

                                    if percentages[region] > 0:
                                        fig.add_annotation(
                                            x=x_offset,
                                            y=y_offset,
                                            text=f"{region}:{percentages[region]}%<br>RT:{round(max_retention_time, 2)} min<br>MW:{mw} kD",
                                            showarrow=False,
                                            font=dict(size=12, color="black"),
                                            align="center",
                                            # bgcolor="rgba(255, 255, 255, 0.8)",
                                            bgcolor=region_colors[region],
                                            bordercolor=region_colors[region],
                                            row=row,
                                            col=col
                                        )

                                except Exception as e:
                                    print(f"Error annotating MW for {sample_name}, {region}: {e}")

        fig.update_xaxes(
            title_text="Time (min)",
            title_standoff=3,
            row=row,
            col=col
        )
        fig.update_yaxes(
            title_text="UV280",
            title_standoff=3,
            row=row,
            col=col
        )
    fig.update_layout(
        height=350 * rows,
        margin=dict(l=10, r=10, t=50, b=10),
        title_x=0.5,
        showlegend=False,
        plot_bgcolor="white"
    )

    return fig


@app.callback(
    [
        Output('time-series-graph', 'figure'),
        Output('time-series-graph', 'style'),
        Output('time-series-graph', 'config')

    ],
    [
        Input('plot-type-dropdown', 'value'),  # Plot type change
        Input("selected-report", "data"),  # Report selection
        Input('shading-checklist', 'value'),
        Input('peak-label-checklist', 'value'),
        Input('main-peak-rt-input', 'value'),
        Input('low-mw-cutoff-input', 'value'),
        Input('regression-parameters', 'data'),
        Input('hmw-table-store', 'data'),
        Input('channel-checklist', 'value'),
        Input('num-cols-input', 'value'),
        Input('vertical-spacing-input', 'value'),
        Input('horizontal-spacing-input', 'value'),
    ],
    [State('selected-report', 'data')],  # Retrieve stored `report_id`
    prevent_initial_call=True
)
def update_graph(plot_type, report_name, shading_options, peak_label_options,
                 main_peak_rt, low_mw_cutoff, regression_params, hmw_table_data,
                 selected_channels, num_cols, vertical_spacing, horizontal_spacing,
                 stored_report_id):
    if report_name:
        report_id = report_name
        print(f'this is the stored report id {report_id}')

    elif stored_report_id:
        report_id = stored_report_id
        print(f'this is the stored report id {stored_report_id}')

    if not report_name:
        print("⚠️ No report found or selected. Returning empty graph.")
        return go.Figure().update_layout(title="No Report Selected"), {'display': 'block'}, {}

    # ✅ 2. Fetch the Report using `report_id`
    report = Report.objects.filter(report_id=report_id).first()

    if not report:
        print(f"⚠️ Report '{report_id}' not found in database.")
        return go.Figure().update_layout(title="Report Not Found"), {'display': 'block'}, {}

    # ✅ 3. Retrieve Sample List and Result IDs
    sample_list = [sample.strip() for sample in report.selected_samples.split(",") if sample.strip()]
    selected_result_ids = [result_id.strip() for result_id in report.selected_result_ids.split(",") if
                           result_id.strip()]
    # Order the result IDs numerically
    selected_result_ids = sorted(selected_result_ids, key=lambda x: int(x))

    # Build the sample list by querying SampleMetadata
    sample_list = []
    for result_id in selected_result_ids:
        sample = SampleMetadata.objects.filter(result_id=result_id).first()
        if sample:
            sample_list.append(sample.sample_name)
    print(f"✅ Report ID: {report_id}")
    print(f"✅ Selected Samples: {sample_list}")
    print(f"✅ Selected Result IDs: {selected_result_ids}")

    current_date = datetime.now().strftime("%Y%m%d")
    filename = f"{current_date}-{report.project_id}-{report.report_name}"

    # ✅ 4. Render Plot Based on Plot Type
    if plot_type == 'plotly':
        fig = go.Figure()
        for result_id in selected_result_ids:
            sample = SampleMetadata.objects.filter(result_id=result_id).first()
            if not sample:
                continue
            time_series = TimeSeriesData.objects.filter(result_id=result_id)
            df = pd.DataFrame(list(time_series.values()))
            for channel in selected_channels:
                if channel in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df['time'],
                        y=df[channel],
                        mode='lines',
                        name=f"{sample.sample_name} - {channel}"
                    ))

        fig.update_layout(
            title='Time Series Data (Plotly)',
            xaxis_title='Time (Minutes)',
            yaxis_title='UV280',
            template='plotly_white',
            height=800
        )
        n_traces = len(fig.data)

        # Toggle states
        visible_all = [True] * n_traces
        visible_legendonly = ['legendonly'] * n_traces

        # Update layout with buttons in the top-right
        fig.update_layout(
            updatemenus=[
                {
                    'buttons': [
                        {
                            'label': 'Show All',
                            'method': 'update',
                            'args': [{'visible': visible_all}]
                        },
                        {
                            'label': 'Hide All',
                            'method': 'update',
                            'args': [{'visible': visible_legendonly}]
                        }
                    ],
                    'type': 'buttons',
                    'direction': 'right',
                    'x': 0.9,  # Right side
                    'xanchor': 'right',
                    'y': 1.15,  # Slightly above the plot
                    'yanchor': 'top'
                }
            ]
        )

        return (fig, {'display': 'block'},
                {
                    'toImageButtonOptions': {
                        'filename': filename,
                        'format': 'png',
                        # 'height': 600,
                        'width': 800,
                        'scale': 2
                    }})

    elif plot_type == 'subplots':
        if not hmw_table_data:
            print("⚠️ No HMW table data provided.")
            return go.Figure().update_layout(title="No HMW Data"), {'display': 'block'}

        slope = regression_params.get('slope', 0)
        intercept = regression_params.get('intercept', 0)
        enable_shading = 'enable_shading' in shading_options
        enable_peak_labeling = 'enable_peak_labeling' in peak_label_options

        fig = generate_subplots_with_shading(
            selected_result_ids,
            sample_list,
            selected_channels,
            enable_shading=enable_shading,
            enable_peak_labeling=enable_peak_labeling,
            main_peak_rt=main_peak_rt,
            slope=slope,
            intercept=intercept,
            hmw_table_data=hmw_table_data,
            num_cols=num_cols,
            vertical_spacing=vertical_spacing,
            horizontal_spacing=horizontal_spacing
        )

        return (fig, {'display': 'block'},
                {
                    'toImageButtonOptions': {
                        'filename': filename,
                        'format': 'png',
                        # 'height': 600,
                        # 'width': 800,
                        'scale': 2
                    }})

    return go.Figure(), {'display': 'block'}, {}


