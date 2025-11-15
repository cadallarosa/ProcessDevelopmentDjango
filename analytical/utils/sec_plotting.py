"""
SEC Plotting Utilities
Functions for generating SEC chromatography plots and analysis
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json


def fetch_time_series_data(result_ids):
    """
    Fetch time series data for multiple result IDs
    OPTIMIZED: Uses bulk queries instead of N+1 queries

    Args:
        result_ids: List of result IDs

    Returns:
        dict: {result_id: DataFrame with columns [time, channel_1, channel_2, channel_3]}
    """
    from plotly_integration.models import TimeSeriesData, SampleMetadata

    # IMPORTANT: Convert result_ids to integers (they come as strings from CSV parsing)
    result_ids_int = [int(rid) if isinstance(rid, str) else rid for rid in result_ids]
    print(f"    🔍 fetch_time_series_data: Looking for result_ids={result_ids_int}")

    # OPTIMIZED: Fetch all samples in ONE query instead of N queries
    # Include system_name to properly query TimeSeriesData
    samples = list(SampleMetadata.objects.filter(result_id__in=result_ids_int).values('result_id', 'injection_id', 'system_name'))
    print(f"    🔍 Found {len(samples)} samples with injection IDs")

    # Create mapping of result_id -> {injection_id, system_name}
    # Filter out samples with NULL injection_id
    injection_map = {
        s['result_id']: {'injection_id': s['injection_id'], 'system_name': s['system_name']}
        for s in samples if s['injection_id'] is not None
    }
    print(f"    🔍 injection_map: {injection_map}")
    print(f"    🔍 Fetching timeseries for {len(injection_map)} samples with valid injection_ids")

    # OPTIMIZED: Fetch ALL time series data in ONE query instead of N queries
    # Query using BOTH injection_id AND system_name for accurate matching
    from django.db.models import Q
    q_objects = Q()
    for result_id, info in injection_map.items():
        q_objects |= Q(result_id=info['injection_id'], system_name=info['system_name'])

    timeseries_qs = TimeSeriesData.objects.filter(q_objects).values(
        'result_id', 'system_name', 'time', 'channel_1', 'channel_2', 'channel_3'
    ).order_by('result_id', 'system_name', 'time')

    timeseries_count = timeseries_qs.count()
    print(f"    🔍 Found {timeseries_count} timeseries rows")

    # Group by (injection_id, system_name) composite key
    timeseries_by_injection = {}
    for row in timeseries_qs:
        key = (row['result_id'], row['system_name'])
        if key not in timeseries_by_injection:
            timeseries_by_injection[key] = []
        timeseries_by_injection[key].append({
            'time': row['time'],
            'channel_1': row['channel_1'],
            'channel_2': row['channel_2'],
            'channel_3': row['channel_3']
        })

    print(f"    🔍 Grouped into {len(timeseries_by_injection)} injection ID + system pairs")
    for (inj_id, system), rows in timeseries_by_injection.items():
        print(f"        - {inj_id} ({system}): {len(rows)} data points")

    # Map back to original result_ids (use integers for lookup, but keep original for keys)
    data_dict = {}
    for orig_id, int_id in zip(result_ids, result_ids_int):
        info = injection_map.get(int_id)
        if info:
            key = (info['injection_id'], info['system_name'])
            if key in timeseries_by_injection:
                df = pd.DataFrame(timeseries_by_injection[key])
                data_dict[orig_id] = df  # Use original ID (string or int) as key
                print(f"    ✅ result_id {orig_id} ({int_id}) -> {len(df)} rows [injection={info['injection_id']}, system={info['system_name']}]")
            else:
                data_dict[orig_id] = pd.DataFrame(columns=['time', 'channel_1', 'channel_2', 'channel_3'])
                print(f"    ❌ result_id {orig_id} ({int_id}) -> NO DATA (injection_id={info['injection_id']}, system={info['system_name']} not found in timeseries)")
        else:
            data_dict[orig_id] = pd.DataFrame(columns=['time', 'channel_1', 'channel_2', 'channel_3'])
            print(f"    ❌ result_id {orig_id} ({int_id}) -> NO DATA (NULL injection_id or not in metadata)")

    return data_dict


def fetch_sample_metadata(result_ids):
    """
    Fetch sample metadata for result IDs
    OPTIMIZED: Uses bulk query instead of N+1 queries

    Args:
        result_ids: List of result IDs

    Returns:
        dict: {result_id: metadata_dict}
    """
    from plotly_integration.models import SampleMetadata

    # IMPORTANT: Convert result_ids to integers
    result_ids_int = [int(rid) if isinstance(rid, str) else rid for rid in result_ids]

    # OPTIMIZED: Fetch all samples in ONE query instead of N queries
    samples = SampleMetadata.objects.filter(result_id__in=result_ids_int).values(
        'result_id', 'sample_name', 'sample_set_name', 'injection_id',
        'column_name', 'system_name', 'date_acquired'
    )

    # Build dict with integer keys, then map back to original IDs
    metadata_by_int = {}
    for sample in samples:
        metadata_by_int[sample['result_id']] = {
            'sample_name': sample['sample_name'],
            'sample_set_name': sample['sample_set_name'],
            'injection_id': sample['injection_id'],
            'column_name': sample['column_name'],
            'system_name': sample['system_name'],
            'date_acquired': str(sample['date_acquired']) if sample['date_acquired'] else None,
        }

    # Map back to original result_ids
    metadata_dict = {}
    for orig_id, int_id in zip(result_ids, result_ids_int):
        if int_id in metadata_by_int:
            metadata_dict[orig_id] = metadata_by_int[int_id]

    return metadata_dict


def fetch_peak_results(result_ids, channel_name=None):
    """
    Fetch peak results for samples
    OPTIMIZED: Uses bulk query instead of N+1 queries

    Args:
        result_ids: List of result IDs
        channel_name: Optional channel filter

    Returns:
        dict: {result_id: DataFrame with peak data}
    """
    from plotly_integration.models import PeakResults

    # IMPORTANT: Convert result_ids to integers
    result_ids_int = [int(rid) if isinstance(rid, str) else rid for rid in result_ids]

    # OPTIMIZED: Fetch all peaks in ONE query instead of N queries
    filters = {'result_id__in': result_ids_int}
    if channel_name:
        filters['channel_name'] = channel_name

    peaks_qs = PeakResults.objects.filter(**filters).values(
        'result_id', 'peak_retention_time', 'peak_start_time', 'peak_end_time',
        'area', 'height', 'percent_area'
    )

    # Group peaks by result_id (integers from DB)
    peaks_by_int = {}
    for peak in peaks_qs:
        result_id = peak['result_id']
        if result_id not in peaks_by_int:
            peaks_by_int[result_id] = []
        peaks_by_int[result_id].append({
            'peak_retention_time': peak['peak_retention_time'],
            'peak_start_time': peak['peak_start_time'],
            'peak_end_time': peak['peak_end_time'],
            'area': peak['area'],
            'height': peak['height'],
            'percent_area': peak['percent_area']
        })

    # Create DataFrames for each result_id, mapping back to original IDs
    peak_dict = {}
    for orig_id, int_id in zip(result_ids, result_ids_int):
        if int_id in peaks_by_int:
            peak_dict[orig_id] = pd.DataFrame(peaks_by_int[int_id])
        else:
            peak_dict[orig_id] = pd.DataFrame()

    return peak_dict


def identify_main_peak(peak_df, mode='rt', target_rt=10.5):
    """
    Identify the main peak in peak results

    Args:
        peak_df: DataFrame with peak data
        mode: 'rt' (retention time) or 'height'
        target_rt: Target retention time for RT mode

    Returns:
        dict: Main peak data or None
    """
    if peak_df.empty:
        return None

    if mode == 'height':
        # Find peak with maximum height
        idx = peak_df['height'].idxmax()
        return peak_df.loc[idx].to_dict()
    else:
        # Find peak closest to target RT
        peak_df = peak_df.copy()
        peak_df['rt_diff'] = abs(peak_df['peak_retention_time'] - target_rt)
        idx = peak_df['rt_diff'].idxmin()
        return peak_df.loc[idx].to_dict()


def calculate_region_percentages(peak_df, main_peak, low_mw_cutoff=12):
    """
    Calculate HMW, Main Peak, and LMW percentages

    Args:
        peak_df: DataFrame with all peaks
        main_peak: Main peak dict
        low_mw_cutoff: Low MW cutoff retention time (minutes) - peaks after this RT are ignored

    Returns:
        dict: {hmw_percent, main_percent, lmw_percent, main_peak_rt, main_peak_start, main_peak_end}
    """
    if peak_df.empty or not main_peak:
        return {
            'hmw_percent': 0.0,
            'main_percent': 0.0,
            'lmw_percent': 0.0,
            'main_peak_rt': None,
            'main_peak_start': None,
            'main_peak_end': None
        }

    # Filter out peaks after low MW cutoff (ignore peaks with RT > low_mw_cutoff)
    peak_df_filtered = peak_df[peak_df['peak_retention_time'] <= low_mw_cutoff].copy()

    if peak_df_filtered.empty:
        return {
            'hmw_percent': 0.0,
            'main_percent': 0.0,
            'lmw_percent': 0.0,
            'main_peak_rt': main_peak['peak_retention_time'],
            'main_peak_start': None,
            'main_peak_end': None
        }

    main_start = main_peak['peak_start_time']
    main_end = main_peak['peak_end_time']

    # Calculate region percentages from filtered peaks only
    total_area = peak_df_filtered['area'].sum()

    if total_area == 0:
        return {
            'hmw_percent': 0.0,
            'main_percent': 0.0,
            'lmw_percent': 0.0,
            'main_peak_rt': main_peak['peak_retention_time'],
            'main_peak_start': main_start,
            'main_peak_end': main_end
        }

    # HMW: peaks before main peak
    hmw_area = peak_df_filtered[peak_df_filtered['peak_end_time'] < main_start]['area'].sum()

    # Main peak area
    main_area = main_peak['area']

    # LMW: peaks after main peak (but still before cutoff)
    lmw_area = peak_df_filtered[peak_df_filtered['peak_start_time'] > main_end]['area'].sum()

    return {
        'hmw_percent': round((hmw_area / total_area) * 100, 2),
        'main_percent': round((main_area / total_area) * 100, 2),
        'lmw_percent': round((lmw_area / total_area) * 100, 2),
        'main_peak_rt': main_peak['peak_retention_time'],
        'main_peak_start': main_start,
        'main_peak_end': main_end
    }


def create_sec_plot(time_series_dict, metadata_dict, analysis_results,
                    show_uv280=True, show_uv260=False, show_pressure=False):
    """
    Create Plotly SEC chromatography plot

    Args:
        time_series_dict: {result_id: DataFrame}
        metadata_dict: {result_id: metadata}
        analysis_results: {result_id: {hmw_percent, main_percent, lmw_percent, ...}}
        show_uv280: Show UV280 channel
        show_uv260: Show UV260 channel
        show_pressure: Show pressure channel

    Returns:
        str: JSON string for Plotly.js
    """
    fig = go.Figure()

    # Define colors for different samples
    colors = ['#0056b3', '#dc3545', '#28a745', '#ffc107', '#17a2b8',
              '#6f42c1', '#e83e8c', '#fd7e14', '#20c997', '#6c757d']

    for idx, (result_id, df) in enumerate(time_series_dict.items()):
        if df.empty:
            continue

        color = colors[idx % len(colors)]
        sample_name = metadata_dict.get(result_id, {}).get('sample_name', f'Sample {result_id}')

        # Add traces based on channel selection
        if show_uv280:
            fig.add_trace(go.Scatter(
                x=df['time'].tolist(),  # Convert pandas Series to list
                y=df['channel_1'].tolist(),  # Convert pandas Series to list
                mode='lines',
                name=f'{sample_name} - UV280',
                line=dict(color=color, width=2),
                legendgroup=f'group{idx}',
                hovertemplate='<b>%{fullData.name}</b><br>RT: %{x:.2f} min<br>UV: %{y:.2f}<extra></extra>'
            ))

        if show_uv260 and 'channel_2' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['time'].tolist(),  # Convert pandas Series to list
                y=df['channel_2'].tolist(),  # Convert pandas Series to list
                mode='lines',
                name=f'{sample_name} - UV260',
                line=dict(color=color, width=1, dash='dash'),
                legendgroup=f'group{idx}',
                visible='legendonly',
                hovertemplate='<b>%{fullData.name}</b><br>RT: %{x:.2f} min<br>UV: %{y:.2f}<extra></extra>'
            ))

        if show_pressure and 'channel_3' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['time'].tolist(),  # Convert pandas Series to list
                y=df['channel_3'].tolist(),  # Convert pandas Series to list
                mode='lines',
                name=f'{sample_name} - Pressure',
                line=dict(color=color, width=1, dash='dot'),
                legendgroup=f'group{idx}',
                visible='legendonly',
                yaxis='y2',
                hovertemplate='<b>%{fullData.name}</b><br>RT: %{x:.2f} min<br>Pressure: %{y:.2f}<extra></extra>'
            ))

        # Add shaded regions for HMW/Main/LMW if available (only for first sample to avoid clutter)
        if result_id in analysis_results and idx == 0:
            result = analysis_results[result_id]
            main_start = result.get('main_peak_start')
            main_end = result.get('main_peak_end')

            if main_start and main_end:
                # HMW region (before main peak) - light red
                fig.add_vrect(
                    x0=df['time'].min(),
                    x1=main_start,
                    fillcolor="rgba(220, 53, 69, 0.1)",
                    layer="below",
                    line_width=0,
                )

                # Main peak region - light green
                fig.add_vrect(
                    x0=main_start,
                    x1=main_end,
                    fillcolor="rgba(40, 167, 69, 0.1)",
                    layer="below",
                    line_width=0,
                )

                # LMW region (after main peak) - light blue
                fig.add_vrect(
                    x0=main_end,
                    x1=df['time'].max(),
                    fillcolor="rgba(23, 162, 184, 0.1)",
                    layer="below",
                    line_width=0,
                )

    # Update layout
    fig.update_layout(
        title=dict(
            text='SEC Chromatography Results',
            font=dict(size=20, color='#0056b3')
        ),
        xaxis=dict(
            title='Retention Time (min)',
            gridcolor='#e3e6ea',
            showline=True,
            linewidth=2,
            linecolor='#343a40'
        ),
        yaxis=dict(
            title='UV Absorbance (mAU)',
            gridcolor='#e3e6ea',
            showline=True,
            linewidth=2,
            linecolor='#343a40'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='closest',
        height=700,
        margin=dict(l=80, r=80, t=80, b=80),
        legend=dict(
            orientation='v',
            yanchor='top',
            y=1,
            xanchor='left',
            x=1.02,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#e3e6ea',
            borderwidth=1
        ),
        dragmode='zoom'
    )

    # Add secondary y-axis for pressure if shown
    if show_pressure:
        fig.update_layout(
            yaxis2=dict(
                title='Pressure (MPa)',
                overlaying='y',
                side='right',
                gridcolor='#f1f3f5'
            )
        )

    # Return as JSON for Plotly.js
    return json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder)


class PlotlyJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for Plotly figures"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return super().default(obj)


def analyze_samples(result_ids, peak_mode='rt', main_peak_rt=10.5,
                    low_mw_cutoff=12, use_std_curve=False):
    """
    Perform complete analysis on samples

    Args:
        result_ids: List of result IDs
        peak_mode: 'rt' or 'height'
        main_peak_rt: Target RT for main peak
        low_mw_cutoff: Low MW cutoff
        use_std_curve: Whether to use standard curve

    Returns:
        dict: {
            'analysis_results': {result_id: analysis_dict},
            'time_series': {result_id: DataFrame},
            'metadata': {result_id: metadata_dict}
        }
    """
    import time

    start_time = time.time()
    print(f"    ⏱️ analyze_samples() started for {len(result_ids)} samples")

    # Fetch data
    ts_start = time.time()
    time_series_dict = fetch_time_series_data(result_ids)
    ts_end = time.time()
    print(f"    ⏱️ [{int((ts_end - start_time) * 1000)}ms] fetch_time_series_data() took {int((ts_end - ts_start) * 1000)}ms")

    meta_start = time.time()
    metadata_dict = fetch_sample_metadata(result_ids)
    meta_end = time.time()
    print(f"    ⏱️ [{int((meta_end - start_time) * 1000)}ms] fetch_sample_metadata() took {int((meta_end - meta_start) * 1000)}ms")

    peak_start = time.time()
    peak_dict = fetch_peak_results(result_ids)
    peak_end = time.time()
    print(f"    ⏱️ [{int((peak_end - start_time) * 1000)}ms] fetch_peak_results() took {int((peak_end - peak_start) * 1000)}ms")

    # Analyze each sample
    analysis_start = time.time()
    analysis_results = {}

    for result_id in result_ids:
        peak_df = peak_dict.get(result_id, pd.DataFrame())
        ts_df = time_series_dict.get(result_id, pd.DataFrame())

        # Identify main peak
        main_peak = identify_main_peak(peak_df, mode=peak_mode, target_rt=main_peak_rt)

        # Calculate region percentages
        region_data = calculate_region_percentages(peak_df, main_peak, low_mw_cutoff)

        analysis_results[result_id] = {
            **region_data,
            'sample_name': metadata_dict.get(result_id, {}).get('sample_name', f'Sample {result_id}')
        }

    analysis_end = time.time()
    print(f"    ⏱️ [{int((analysis_end - start_time) * 1000)}ms] Analysis loop took {int((analysis_end - analysis_start) * 1000)}ms")

    total_time = (analysis_end - start_time) * 1000
    print(f"    ✅ analyze_samples() TOTAL: {int(total_time)}ms (timeseries: {int((ts_end - ts_start) * 1000)}ms, metadata: {int((meta_end - meta_start) * 1000)}ms, peaks: {int((peak_end - peak_start) * 1000)}ms, analysis: {int((analysis_end - analysis_start) * 1000)}ms)")

    return {
        'analysis_results': analysis_results,
        'time_series': time_series_dict,
        'metadata': metadata_dict
    }


def create_channel_traces(time_series_dict, metadata_dict, channel, analysis_results=None, line_width=1.5):
    """
    Create Plotly traces for a specific channel (OVERLAY MODE - multi-colored)

    Args:
        time_series_dict: {result_id: DataFrame}
        metadata_dict: {result_id: metadata}
        channel: 'uv280', 'uv260', or 'pressure'
        analysis_results: Optional analysis results for shading
        line_width: Line width for traces

    Returns:
        list: List of Plotly trace dicts
    """
    traces = []

    # Multi-colored for overlay mode
    colors = ['#0056b3', '#dc3545', '#28a745', '#ffc107', '#17a2b8',
              '#6f42c1', '#e83e8c', '#fd7e14', '#20c997', '#6c757d']

    channel_map = {
        'uv280': ('channel_1', 'UV280', 'solid', line_width),
        'uv260': ('channel_2', 'UV260', 'dash', line_width),
        'pressure': ('channel_3', 'Pressure', 'dot', line_width)
    }

    if channel not in channel_map:
        return traces

    col_name, label, dash_style, width = channel_map[channel]

    for idx, (result_id, df) in enumerate(time_series_dict.items()):
        if df.empty or col_name not in df.columns:
            continue

        # Filter out NaN values to prevent plotting errors
        df_clean = df[['time', col_name]].dropna()
        if df_clean.empty:
            continue

        color = colors[idx % len(colors)]
        sample_name = metadata_dict.get(result_id, {}).get('sample_name', f'Sample {result_id}')

        trace = {
            'x': df_clean['time'].tolist(),
            'y': df_clean[col_name].tolist(),
            'mode': 'lines',
            'name': f'{sample_name} - {label}',
            'line': {'color': color, 'width': width, 'dash': dash_style},
            'legendgroup': f'group{idx}',
            'customdata': [{'result_id': result_id}] * len(df_clean),
            'hovertemplate': f'<b>%{{fullData.name}}</b><br>RT: %{{x:.2f}} min<br>{label}: %{{y:.2f}}<extra></extra>'
        }

        # UV260 and pressure start as hidden
        if channel in ['uv260', 'pressure']:
            trace['visible'] = 'legendonly'

        # Pressure uses secondary y-axis
        if channel == 'pressure':
            trace['yaxis'] = 'y2'

        traces.append(trace)

    return traces


def create_plot_layout(show_shading=False, analysis_results=None, time_series_dict=None):
    """
    Create Plotly layout configuration

    Args:
        show_shading: Whether to show HMW/Main/LMW regions (disabled by default)
        analysis_results: Analysis results for shading
        time_series_dict: Time series data for determining time range

    Returns:
        dict: Plotly layout dict
    """
    layout = {
        'title': {
            'text': 'SEC Chromatography Results',
            'font': {'size': 20, 'color': '#0056b3'}
        },
        'xaxis': {
            'title': 'Retention Time (min)',
            'gridcolor': '#e3e6ea',
            'showline': True,
            'linewidth': 2,
            'linecolor': '#343a40'
        },
        'yaxis': {
            'title': 'UV Absorbance (mAU)',
            'gridcolor': '#e3e6ea',
            'showline': True,
            'linewidth': 2,
            'linecolor': '#343a40'
        },
        'yaxis2': {
            'title': 'Pressure (MPa)',
            'overlaying': 'y',
            'side': 'right',
            'gridcolor': '#f1f3f5'
        },
        'plot_bgcolor': 'white',
        'paper_bgcolor': 'white',
        'hovermode': 'closest',
        'height': 700,
        'margin': {'l': 80, 'r': 80, 't': 80, 'b': 80},
        'legend': {
            'orientation': 'v',
            'yanchor': 'top',
            'y': 1,
            'xanchor': 'left',
            'x': 1.02,
            'bgcolor': 'rgba(255,255,255,0.8)',
            'bordercolor': '#e3e6ea',
            'borderwidth': 1
        },
        'dragmode': 'zoom'
    }

    # Shading disabled - can be re-enabled later when logic is fixed
    # if show_shading and analysis_results and time_series_dict:
    #     ... shading code ...

    return layout


def format_results_for_table(analysis_results, metadata_dict):
    """
    Format analysis results for display in results table

    Args:
        analysis_results: {result_id: analysis_dict}
        metadata_dict: {result_id: metadata_dict}

    Returns:
        dict: Formatted results data
    """
    results = []

    for result_id, analysis in analysis_results.items():
        metadata = metadata_dict.get(result_id, {})

        results.append({
            'result_id': result_id,
            'sample_name': analysis.get('sample_name') or metadata.get('sample_name', f'Sample {result_id}'),
            'sample_set_name': metadata.get('sample_set_name', 'N/A'),
            'hmw_percent': analysis.get('hmw_percent'),
            'main_percent': analysis.get('main_percent'),
            'lmw_percent': analysis.get('lmw_percent'),
            'main_peak_rt': analysis.get('main_peak_rt'),
            'main_peak_start': analysis.get('main_peak_start'),
            'main_peak_end': analysis.get('main_peak_end'),
            'date_acquired': metadata.get('date_acquired')
        })

    return {'results': results}


def create_subplot_layout(num_subplots, cols=2):
    """
    Create subplot layout configuration for multiple samples

    Args:
        num_subplots: Number of subplots needed
        cols: Number of columns (default 2)

    Returns:
        dict: Layout configuration with subplot settings
    """
    import math

    rows = math.ceil(num_subplots / cols)

    # Calculate subplot positions
    subplot_specs = []
    for i in range(rows):
        row_specs = []
        for j in range(cols):
            row_specs.append({"secondary_y": True})  # Support secondary y-axis for pressure
        subplot_specs.append(row_specs)

    layout = {
        'title': {
            'text': 'SEC Chromatography Results (Subplots)',
            'font': {'size': 20, 'color': '#0056b3'}
        },
        'plot_bgcolor': 'white',
        'paper_bgcolor': 'white',
        'hovermode': 'closest',
        'height': max(700, rows * 300),  # Dynamic height based on rows
        'margin': {'l': 60, 'r': 60, 't': 80, 'b': 60},
        'showlegend': True,
        'legend': {
            'orientation': 'v',
            'yanchor': 'top',
            'y': 1,
            'xanchor': 'left',
            'x': 1.02,
            'bgcolor': 'rgba(255,255,255,0.8)',
            'bordercolor': '#e3e6ea',
            'borderwidth': 1
        }
    }

    # Add axis configurations for each subplot
    for i in range(1, num_subplots + 1):
        xaxis_key = 'xaxis' if i == 1 else f'xaxis{i}'
        yaxis_key = 'yaxis' if i == 1 else f'yaxis{i}'

        layout[xaxis_key] = {
            'title': 'Retention Time (min)',
            'gridcolor': '#e3e6ea',
            'showline': True,
            'linewidth': 1,
            'linecolor': '#343a40'
        }

        layout[yaxis_key] = {
            'title': 'UV (mAU)',
            'gridcolor': '#e3e6ea',
            'showline': True,
            'linewidth': 1,
            'linecolor': '#343a40'
        }

    return layout


def create_channel_traces_subplot(time_series_dict, metadata_dict, channel, subplot_index_map, subplot_color='#000000', line_width=1.5):
    """
    Create Plotly traces for subplots mode

    Args:
        time_series_dict: {result_id: DataFrame}
        metadata_dict: {result_id: metadata}
        channel: 'uv280', 'uv260', or 'pressure'
        subplot_index_map: {result_id: subplot_number} mapping
        subplot_color: Color to use for all traces in subplot mode
        line_width: Line width for traces

    Returns:
        list: List of Plotly trace dicts with subplot assignments
    """
    traces = []

    # Use user-selected color for all traces in subplot mode
    color = subplot_color

    channel_map = {
        'uv280': ('channel_1', 'UV280', 'solid', line_width),
        'uv260': ('channel_2', 'UV260', 'dash', line_width),
        'pressure': ('channel_3', 'Pressure', 'dot', line_width)
    }

    if channel not in channel_map:
        return traces

    col_name, label, dash_style, width = channel_map[channel]

    for idx, (result_id, df) in enumerate(time_series_dict.items()):
        if df.empty or col_name not in df.columns:
            continue

        # Filter out NaN values to prevent plotting errors
        df_clean = df[['time', col_name]].dropna()
        if df_clean.empty:
            continue

        sample_name = metadata_dict.get(result_id, {}).get('sample_name', f'Sample {result_id}')
        subplot_num = subplot_index_map.get(result_id, 1)

        # Determine which axes to use
        xaxis = 'x' if subplot_num == 1 else f'x{subplot_num}'
        yaxis = 'y' if subplot_num == 1 else f'y{subplot_num}'

        trace = {
            'x': df_clean['time'].tolist(),
            'y': df_clean[col_name].tolist(),
            'mode': 'lines',
            'name': f'{sample_name} - {label}',
            'line': {'color': color, 'width': width, 'dash': dash_style},
            'xaxis': xaxis,
            'yaxis': yaxis,
            'hovertemplate': f'<b>%{{fullData.name}}</b><br>RT: %{{x:.2f}} min<br>{label}: %{{y:.2f}}<extra></extra>'
        }

        # UV260 starts hidden
        if channel == 'uv260':
            trace['visible'] = 'legendonly'

        # Pressure uses secondary y-axis
        if channel == 'pressure':
            yaxis2 = 'y2' if subplot_num == 1 else f'y{subplot_num*2}'
            trace['yaxis'] = yaxis2

        traces.append(trace)

    return traces
