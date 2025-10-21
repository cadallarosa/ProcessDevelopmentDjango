import re

from plotly_integration.models import SampleMetadata, TimeSeriesData, Report
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.colors
import pandas as pd
import numpy as np
from datetime import datetime
from dash import dcc, html, Input, Output, State, dash_table, Dash, MATCH, callback_context
from ..app import app


def natural_sort_key(sample_name):
    """
    Extract prefix and numeric components from sample name for natural sorting.

    Examples:
        'UP001' -> ('UP', 1)
        'UPFB0012' -> ('UPFB', 12)
        'FB10' -> ('FB', 10)
        'PD002' -> ('PD', 2)

    This ensures samples are sorted by prefix first, then numerically within each prefix.
    """
    # Match pattern: prefix (letters) + number
    match = re.match(r'([A-Za-z]+)(\d+)', sample_name)
    if match:
        prefix = match.group(1)
        number = int(match.group(2))
        return (prefix, number)
    # Fallback for non-standard names
    return (sample_name, 0)

def generate_subplots_with_shading(selected_result_ids, sample_list, channels, enable_shading, enable_peak_labeling,
                                   main_peak_rt, slope,
                                   intercept, hmw_table_data, num_cols=3, vertical_spacing=0.05,
                                   horizontal_spacing=0.5, show_mw_annotations=True,
                                   manual_scaling=False, x_min=None, x_max=None, y_min=None, y_max=None):
    num_samples = len(sample_list)
    
    # Variables to track data ranges for auto-scaling fallback
    all_x_values = []
    all_y_values = []
    
    # No sample limit - let users handle all their data
    
    cols = num_cols
    rows = (num_samples // cols) + (num_samples % cols > 0)

    # More robust vertical spacing calculation
    if rows == 1:
        vertical_spacing = 0.05  # Single row needs minimal spacing
    elif rows == 2:
        vertical_spacing = 0.15  # Two rows need moderate spacing
    elif rows <= 4:
        vertical_spacing = max(0.08, (1 / (rows - 1)) * 0.2)  # 3-4 rows
    elif rows <= 6:
        vertical_spacing = 0.08  # 5-6 rows need more space
    elif rows <= 8:
        vertical_spacing = 0.06  # 7-8 rows need decent spacing
    else:
        vertical_spacing = 0.02  # 9+ rows need tight but readable spacing
    
    print(f"Rows: {rows}, Vertical spacing set to: {vertical_spacing:.3f}")

    region_colors = {
        "HMW": "rgba(255, 87, 87, 0.85)",  # Coral Red
        "MP": "rgba(72, 149, 239, 0.85)",  # Sky Blue
        "LMW": "rgba(122, 230, 160, 0.85)"  # Mint Green
    }

    label_offsets = {
        "HMW": {"x_offset": -3, "y_offset_percentage": 0.05},  # 5% of peak height
        "MP": {"x_offset": 0, "y_offset_percentage": 0.05},   # 5% of peak height
        "LMW": {"x_offset": 2, "y_offset_percentage": 0.05}   # 5% of peak height
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
        time_series = TimeSeriesData.objects.filter(result_id=sample.injection_id)
        df = pd.DataFrame(list(time_series.values()))
        sample_name = sample.sample_name
        # Get HMW Table row for the current sample
        # ✅ Find HMW row by result_id (not sample_name, as multiple results can have the same sample name)
        # Convert both to int for comparison since result_id might be string or int
        hmw_row = next((r for r in hmw_table_data if isinstance(r, dict) and int(r.get('Result ID', 0)) == int(result_id)), None)
        if not hmw_row:
            print(f"⚠️ No HMW row found for result_id={result_id}")
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
                # Collect data ranges
                all_x_values.extend(df['time'].tolist())
                all_y_values.extend(df[channel].tolist())
                
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
                                # Annotate peaks using max value in the region - SIMPLE ORIGINAL METHOD
                                try:
                                    max_peak_row = shading_region.loc[shading_region[channel].idxmax()]
                                    max_retention_time = max_peak_row['time']
                                    max_peak_value = max_peak_row[channel]

                                    # Calculate MW using the max retention time
                                    log_mw = slope * max_retention_time + intercept
                                    mw = round(np.exp(log_mw) / 1000, 2)

                                    # Apply offsets for labels - use percentage of peak height
                                    x_offset = label_offsets[region]["x_offset"] + max_retention_time
                                    y_offset = max_peak_value + (max_peak_value * label_offsets[region]["y_offset_percentage"])

                                    if percentages[region] > 0:
                                        # Modern annotation colors
                                        modern_colors = {
                                            "HMW": "rgba(239, 68, 68, 0.9)",   # Modern red
                                            "MP": "rgba(37, 99, 235, 0.9)",    # Modern blue  
                                            "LMW": "rgba(5, 150, 105, 0.9)"    # Modern green
                                        }
                                        
                                        # Create annotation text based on MW toggle setting
                                        if show_mw_annotations:
                                            annotation_text = f"<b>{region}</b><br>{percentages[region]}%<br>RT: {round(max_retention_time, 2)} min<br>MW: {mw} kDa"
                                        else:
                                            annotation_text = f"<b>{region}</b><br>{percentages[region]}%<br>RT: {round(max_retention_time, 2)} min"
                                        
                                        # Create rounded effect by using HTML/CSS-like styling
                                        fig.add_annotation(
                                            x=x_offset,
                                            y=y_offset,
                                            text=annotation_text,
                                            showarrow=False,
                                            font=dict(
                                                size=10,
                                                color="white",
                                                family="system-ui, -apple-system, sans-serif"
                                            ),
                                            align="center",
                                            bgcolor=modern_colors[region],
                                            bordercolor="rgba(255, 255, 255, 0.3)",
                                            borderwidth=0,
                                            borderpad=8,  # Increased padding for more rounded appearance
                                            xanchor="center",
                                            yanchor="bottom",
                                            row=row,
                                            col=col,
                                            opacity=0.95,
                                            # These properties help create a more rounded visual effect
                                            hoverlabel=dict(
                                                bgcolor=modern_colors[region],
                                                bordercolor="rgba(255, 255, 255, 0.3)"
                                            )
                                        )

                                except Exception as e:
                                    print(f"Error annotating MW for {sample_name}, {region}: {e}")

        # Update axes - with or without manual scaling
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
    height = 350 * rows
    print('Height of the figure:', height)
    fig.update_layout(
        height=350 * rows,
        margin=dict(l=10, r=10, t=50, b=10),
        title_x=0.5,
        showlegend=False,
        plot_bgcolor="white"
    )
    
    # Apply manual scaling after figure is built
    if manual_scaling and (x_min is not None or x_max is not None or y_min is not None or y_max is not None):
        # Calculate auto-scale ranges from the data if needed
        if all_x_values:
            auto_x_min = min(all_x_values)
            auto_x_max = max(all_x_values)
        else:
            auto_x_min = 0
            auto_x_max = 1
            
        if all_y_values:
            auto_y_min = min(all_y_values)
            auto_y_max = max(all_y_values)
            # Add some padding for y-axis
            y_padding = (auto_y_max - auto_y_min) * 0.05
            auto_y_min = auto_y_min - y_padding
            auto_y_max = auto_y_max + y_padding
        else:
            auto_y_min = 0
            auto_y_max = 1
        
        # Determine final ranges
        final_x_min = x_min if x_min is not None else auto_x_min
        final_x_max = x_max if x_max is not None else auto_x_max
        final_y_min = y_min if y_min is not None else auto_y_min
        final_y_max = y_max if y_max is not None else auto_y_max
        
        # Apply to all subplots
        fig.update_xaxes(range=[final_x_min, final_x_max])
        fig.update_yaxes(range=[final_y_min, final_y_max])

    return fig


# Pagination management callback
@app.callback(
    [
        Output('pagination-data', 'data'),
        Output('pagination-controls-top', 'style'),
        Output('pagination-controls-bottom', 'style'),
        Output('page-info-top', 'children'),
        Output('page-info-bottom', 'children'),
        Output('samples-info-top', 'children'),
        Output('samples-info-bottom', 'children'),
        Output('prev-page-btn-top', 'disabled'),
        Output('prev-page-btn-bottom', 'disabled'),
        Output('next-page-btn-top', 'disabled'),
        Output('next-page-btn-bottom', 'disabled')
    ],
    [
        Input("selected-report", "data"),
        Input('prev-page-btn-top', 'n_clicks'),
        Input('next-page-btn-top', 'n_clicks'),
        Input('prev-page-btn-bottom', 'n_clicks'),
        Input('next-page-btn-bottom', 'n_clicks')
    ],
    [
        State('pagination-data', 'data'),
        State('selected-report', 'data')
    ],
    prevent_initial_call=True
)
def manage_pagination(report_name, prev_clicks_top, next_clicks_top, prev_clicks_bottom, next_clicks_bottom, pagination_data, stored_report_id):
    from dash import callback_context
    
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else ''
    
    # Get report ID
    report_id = report_name or stored_report_id
    if not report_id:
        return pagination_data, {'display': 'none'}, {'display': 'none'}, "Page 1 of 1", "Page 1 of 1", "", "", True, True, True, True
    
    # Fetch report data
    report = Report.objects.filter(report_id=report_id).first()
    if not report:
        return pagination_data, {'display': 'none'}, {'display': 'none'}, "Page 1 of 1", "Page 1 of 1", "", "", True, True, True, True
    
    # Get all samples
    sample_list = [sample.strip() for sample in report.selected_samples.split(",") if sample.strip()]
    selected_result_ids = [result_id.strip() for result_id in report.selected_result_ids.split(",") if result_id.strip()]

    # Build list of (sample_name, result_id) tuples by querying SampleMetadata
    sample_result_pairs = []
    for result_id in selected_result_ids:
        sample = SampleMetadata.objects.filter(result_id=result_id).first()
        if sample:
            sample_result_pairs.append((sample.sample_name, result_id))

    # Sort by sample name using natural sorting (prefix + numeric)
    sample_result_pairs.sort(key=lambda x: natural_sort_key(x[0]))

    # Extract sorted lists
    final_sample_list = [pair[0] for pair in sample_result_pairs]
    selected_result_ids = [pair[1] for pair in sample_result_pairs]
    
    total_samples = len(final_sample_list)
    samples_per_page = 30
    total_pages = max(1, (total_samples + samples_per_page - 1) // samples_per_page)
    
    # Determine current page
    if trigger_id == 'selected-report' or not pagination_data.get('current_page'):
        current_page = 1
    elif trigger_id in ['prev-page-btn-top', 'prev-page-btn-bottom']:
        current_page = max(1, pagination_data.get('current_page', 1) - 1)
    elif trigger_id in ['next-page-btn-top', 'next-page-btn-bottom']:
        current_page = min(total_pages, pagination_data.get('current_page', 1) + 1)
    else:
        current_page = pagination_data.get('current_page', 1)
    
    # Show pagination only if more than 30 samples
    show_pagination = total_samples >= 30
    
    pagination_style = {'display': 'block'} if show_pagination else {'display': 'none'}
    
    page_info = f"Page {current_page} of {total_pages}"
    samples_info = f"Showing samples {(current_page-1)*samples_per_page + 1}-{min(current_page*samples_per_page, total_samples)} of {total_samples}"
    
    prev_disabled = current_page <= 1
    next_disabled = current_page >= total_pages
    
    # Update pagination data
    new_pagination_data = {
        'current_page': current_page,
        'total_pages': total_pages,
        'samples_per_page': samples_per_page,
        'all_samples': final_sample_list,
        'all_result_ids': selected_result_ids,
        'total_samples': total_samples
    }
    
    return (new_pagination_data, pagination_style, pagination_style, 
            page_info, page_info, samples_info, samples_info, 
            prev_disabled, prev_disabled, next_disabled, next_disabled)


@app.callback(
    [
        Output('time-series-graph', 'figure'),
        Output('time-series-graph', 'style'),
        Output('time-series-graph', 'config')
    ],
    [
        # Immediate updates (affect data/shading)
        Input('plot-type-dropdown', 'value'),  # Plot type change
        Input("selected-report", "data"),  # Report selection
        Input('shading-checklist', 'value'),  # Toggle shading
        Input('peak-label-checklist', 'value'),  # Toggle labels
        Input('channel-checklist', 'value'),  # Change channels
        Input('regression-parameters', 'data'),  # MW calculations
        Input('hmw-table-store', 'data'),  # Peak boundaries
        Input('pagination-data', 'data'),  # Page changes
        
        # Layout-only updates (manual trigger)
        Input('apply-layout-btn', 'n_clicks'),  # Apply layout settings
    ],
    [
        # States (don't trigger updates)
        State('main-peak-rt-input', 'value'),  # Used by HMW table, not directly here
        State('low-mw-cutoff-input', 'value'),  # Used by HMW table, not directly here
        State('num-cols-input', 'value'),  # Layout only
        State('vertical-spacing-input', 'value'),  # Layout only
        State('horizontal-spacing-input', 'value'),  # Layout only
        State('selected-report', 'data'),  # Retrieve stored `report_id`
        State('manual-scaling-checkbox', 'value'),  # Manual scaling toggle
        State('x-min-input', 'value'),  # X-axis min
        State('x-max-input', 'value'),  # X-axis max
        State('y-min-input', 'value'),  # Y-axis min
        State('y-max-input', 'value')  # Y-axis max
    ],
    prevent_initial_call=True
)
def update_graph(plot_type, report_name, shading_options, peak_label_options,
                 selected_channels, regression_params, hmw_table_data, pagination_data, apply_layout_clicks,
                 main_peak_rt, low_mw_cutoff, num_cols, vertical_spacing, horizontal_spacing,
                 stored_report_id, manual_scaling_checkbox, x_min, x_max, y_min, y_max):
    if report_name:
        report_id = report_name
        print(f'this is the stored report id {report_id}')

    elif stored_report_id:
        report_id = stored_report_id
        print(f'this is the stored report id {stored_report_id}')

    if not report_name:
        print("⚠️ No report found or selected. Returning empty graph.")
        return go.Figure().update_layout(title="No Report Selected"), {'display': 'block'}, {}

    # ✅ Use pagination data to get current page samples
    if not pagination_data or not pagination_data.get('all_samples'):
        print("⚠️ No pagination data available.")
        return go.Figure().update_layout(title="Loading..."), {'display': 'block'}, {}

    # Get current page data
    current_page = pagination_data.get('current_page', 1)
    samples_per_page = pagination_data.get('samples_per_page', 30)
    all_samples = pagination_data.get('all_samples', [])
    all_result_ids = pagination_data.get('all_result_ids', [])
    total_samples = pagination_data.get('total_samples', len(all_samples))
    
    # Calculate page slice
    start_idx = (current_page - 1) * samples_per_page
    end_idx = min(start_idx + samples_per_page, len(all_samples))
    
    # Get samples for current page
    sample_list = all_samples[start_idx:end_idx]
    selected_result_ids = all_result_ids[start_idx:end_idx]
    
    print(f"✅ Report ID: {report_id}")
    print(f"✅ Page {current_page}: Showing {len(sample_list)} samples ({start_idx+1}-{end_idx} of {total_samples})")
    print(f"✅ Current Page Samples: {sample_list}")
    print(f"✅ Current Page Result IDs: {selected_result_ids}")

    # Get report for filename
    report = Report.objects.filter(report_id=report_id).first()
    current_date = datetime.now().strftime("%Y%m%d")
    filename = f"{current_date}-{report.project_id if report else 'unknown'}-page{current_page}"

    # ✅ 4. Render Plot Based on Plot Type
    if plot_type == 'plotly':
        # Use Dark24 color palette (cycles after 24 colors)
        colors = plotly.colors.qualitative.Dark24

        fig = go.Figure()
        color_idx = 0
        for result_id in selected_result_ids:
            sample = SampleMetadata.objects.filter(result_id=result_id).first()
            if not sample:
                continue
            time_series = TimeSeriesData.objects.filter(result_id=sample.injection_id)
            df = pd.DataFrame(list(time_series.values()))
            for channel in selected_channels:
                if channel in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df['time'],
                        y=df[channel],
                        mode='lines',
                        name=f"{sample.sample_name} - {channel}",
                        line=dict(color=colors[color_idx % len(colors)])
                    ))
                    color_idx += 1

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
            return go.Figure().update_layout(title="No HMW Data"), {'display': 'block'}, {}

        slope = regression_params.get('slope', 0)
        intercept = regression_params.get('intercept', 0)
        enable_shading = 'enable_shading' in shading_options
        enable_peak_labeling = 'enable_peak_labeling' in peak_label_options
        show_mw_annotations = 'show_mw_annotations' in peak_label_options
        
        # Check if manual scaling is enabled
        manual_scaling_enabled = manual_scaling_checkbox and 'enable_manual_scaling' in manual_scaling_checkbox

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
            horizontal_spacing=horizontal_spacing,
            show_mw_annotations=show_mw_annotations,
            manual_scaling=manual_scaling_enabled,
            x_min=x_min,
            x_max=x_max,
            y_min=y_min,
            y_max=y_max
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
