"""
Plotting Module for CE-SDS Analysis App
Unified chromatogram generation for both reduced and non-reduced samples.
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .peak_processing import (
    calculate_baseline, 
    combine_nearby_peaks, 
    add_annotation_with_positioning,
    classify_peak_by_retention_time
)
from .data_access import get_timeseries_data, get_peak_results


def shade_peak(fig, df, start_time, end_time, baseline_value, row, col, label, peak_time, peak_height, class_label,
               annotation_positioning='fixed', peak_index=0, all_peaks=None, y_scale=1, peak_data=None, 
               full_baseline=None, full_time=None):
    """Add shaded peak region with proper baseline"""
    
    PEAK_CLASS_COLORS = {
        "LMW": "rgba(76, 175, 80, 0.5)",  # green
        "Intact": "rgba(33, 150, 243, 0.5)",  # blue
        "Light Chain": "rgba(33, 150, 243, 0.5)",  # blue
        "Heavy Chain": "rgba(255, 193, 7, 0.5)",  # amber
        "HMW": "rgba(244, 67, 54, 0.5)",  # red
    }

    color = PEAK_CLASS_COLORS.get(class_label, "rgba(0,100,200,0.4)")
    
    region = df[(df["time_min"] >= start_time) & (df["time_min"] <= end_time)].copy()
    if region.empty:
        return

    # Use the full baseline data if provided, otherwise fallback to simple method
    if full_baseline is not None and full_time is not None:
        # Interpolate the full baseline for this peak region
        region_baseline = np.interp(region["time_min"], full_time, full_baseline)
    else:
        # Fallback: use a simple linear baseline between start and end
        start_baseline = region["channel_1"].iloc[0] * 0.95 if not region.empty else 0
        end_baseline = region["channel_1"].iloc[-1] * 0.95 if not region.empty else 0
        region_baseline = np.linspace(start_baseline, end_baseline, len(region))
    
    # Add shaded peak area
    fig.add_trace(
        go.Scatter(
            x=np.concatenate([region["time_min"], region["time_min"][::-1]]),
            y=np.concatenate([region["channel_1"], region_baseline[::-1]]),
            fill="toself",
            fillcolor=color,
            line=dict(color="rgba(255,255,255,0)"),
            showlegend=False,
            hoverinfo="skip"
        ),
        row=row,
        col=col
    )

    # Add annotation
    add_annotation_with_positioning(
        fig, peak_time, peak_height, label, row, col,
        positioning_method=annotation_positioning,
        peak_index=peak_index,
        all_peaks=all_peaks,
        y_scale=y_scale,
        peak_data=peak_data
    )


def generate_unified_chromatogram(
    result_df_by_id,
    title="Chromatograms",
    marker_rt=None,
    marker_label="10 kDa",
    light_chain_time=None,
    regression_slope=None,
    regression_intercept=None,
    y_scale=1,
    subplot_vertical_spacing=0.25,
    show_mw_in_annotations=True,
    annotation_positioning='fixed',
    sample_type='auto'  # 'reduced', 'nonreduced', or 'auto'
):
    """
    Unified chromatogram generation function for both reduced and non-reduced samples.
    
    Args:
        result_df_by_id: Dictionary of {metadata_id: {"sample_id": str, "data": DataFrame}}
        sample_type: 'reduced', 'nonreduced', or 'auto' (determines classification logic)
        ... (other parameters same as before)
    
    Returns:
        Tuple of (figure, table_data)
    """
    if not result_df_by_id:
        return go.Figure(), []

    num_rows = len(result_df_by_id)
    fig = make_subplots(
        rows=num_rows, cols=1,
        shared_xaxes=False,
        vertical_spacing=subplot_vertical_spacing,
        subplot_titles=[meta["sample_id"] for meta in result_df_by_id.values()]
    )

    table_data = []
    
    for i, (mid, meta) in enumerate(result_df_by_id.items(), start=1):
        df = meta["data"]
        if df.empty:
            continue

        # Add chromatogram trace
        fig.add_trace(
            go.Scatter(
                x=df["time_min"], 
                y=df["channel_1"], 
                mode="lines", 
                name=meta["sample_id"],
                line=dict(color="#2E86AB", width=1.5)
            ),
            row=i, col=1
        )

        # Calculate baseline for the entire chromatogram once
        full_signal = df["channel_1"].values
        full_time = df["time_min"].values
        full_baseline = calculate_baseline(full_signal, method='simple', window=350)

        # Add marker annotation if specified
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
                    ay=-30,
                    row=i,
                    col=1
                )

        # Get peaks from database
        peaks = get_peak_results(mid, integration_method='empower')
        
        if not peaks:
            print(f"[DEBUG] No peaks found for sample {meta['sample_id']}")
            continue

        # Determine if sample is reduced or non-reduced
        sample_name = meta["sample_id"]
        if sample_type == 'auto':
            is_reduced = not any(keyword in sample_name.upper() for keyword in ["NONREDUCED", "NR", "NON-REDUCED"])
        elif sample_type == 'reduced':
            is_reduced = True
        else:
            is_reduced = False

        # Process and classify peaks
        classified_peaks = []
        total_area = sum(p["area"] for p in peaks)
        
        for peak in peaks:
            rt = peak["retention_time"]
            class_label = classify_peak_by_retention_time(rt, is_reduced, light_chain_time)
            
            # Create standardized peak dict
            peak_dict = {
                "peak_time": rt,
                "area": peak["area"],
                "height": peak["height"],
                "percent_area": peak.get("percent_area", (peak["area"] / total_area * 100) if total_area else 0),
                "start_time": peak.get("peak_start_time", rt - 0.1),
                "end_time": peak.get("peak_end_time", rt + 0.1),
                "baseline": [0]  # Simple baseline placeholder
            }
            
            classified_peaks.append((peak_dict, class_label))

        # Calculate percentages by class
        class_labels = ["LMW", "Light Chain", "Heavy Chain", "Intact", "HMW", "Unknown"]
        percentages = {label: 0.0 for label in class_labels}
        
        # Apply combined peaks logic if needed
        if annotation_positioning == 'combined':
            peaks_with_area = []
            for p, class_label in classified_peaks:
                peak_copy = p.copy()
                peak_copy['class_label'] = class_label
                peaks_with_area.append(peak_copy)
            
            combined_peaks = combine_nearby_peaks(peaks_with_area)
            peaks_to_process = [(p, p.get('class_label', 'Unknown')) for p in combined_peaks]
        else:
            peaks_to_process = classified_peaks

        # Prepare peak data for annotations
        all_peaks_data = [{'peak_time': p["peak_time"], 'peak_height': p["peak_height"]} for p, _ in classified_peaks]

        # Plot peaks and annotations
        for peak_idx, (p, class_label) in enumerate(peaks_to_process):
            pct = p.get("percent_area", 0)
            percentages[class_label] += pct
            label = f"{class_label}<br>({pct:.1f}%)"

            # Add MW calculation if regression parameters provided
            if regression_slope is not None and regression_intercept is not None:
                log_mw = regression_slope * p["peak_time"] + regression_intercept
                mw_kda = np.exp(log_mw)
                
                if show_mw_in_annotations:
                    label += f"<br>{mw_kda:.1f} kDa"

            peak_height = p["peak_height"]
            if y_scale and y_scale != 1:
                y_max = df["channel_1"].max() * y_scale
                peak_height = min(peak_height, y_max)

            # Add shaded peak
            shade_peak(
                fig, df,
                start_time=p.get("start_time", p["peak_time"] - 0.1),
                end_time=p.get("end_time", p["peak_time"] + 0.1),
                baseline_value=0,
                row=i, col=1,
                label=label,
                peak_time=p["peak_time"],
                peak_height=peak_height,
                class_label=class_label,
                annotation_positioning=annotation_positioning,
                peak_index=peak_idx,
                all_peaks=all_peaks_data,
                y_scale=y_scale,
                peak_data=p,
                full_baseline=full_baseline,
                full_time=full_time
            )

        # Update axes
        if y_scale and y_scale != 1:
            y_max = df["channel_1"].max() * y_scale
            fig.update_yaxes(
                title_text="UV",
                autorange=True,
                autorangeoptions=dict(maxallowed=y_max),
                row=i, col=1
            )
        else:
            fig.update_yaxes(title_text="UV", row=i, col=1)
        
        fig.update_xaxes(title_text="Time (min)", row=i, col=1)

        # Add row to table data
        table_data.append({
            'Sample_ID': meta["sample_id"],
            'LMW_%': round(percentages.get("LMW", 0), 1),
            'Light_Chain_%': round(percentages.get("Light Chain", 0), 1),
            'Heavy_Chain_%': round(percentages.get("Heavy Chain", 0), 1),
            'Intact_%': round(percentages.get("Intact", 0), 1),
            'HMW_%': round(percentages.get("HMW", 0), 1)
        })

    fig.update_layout(
        title=title,
        showlegend=False,
        height=400 * num_rows
    )

    return fig, table_data


def plot_standard_chromatogram(metadata_id, num_peaks_to_keep=7):
    """Plot standard chromatogram for MW calibration"""
    df = get_timeseries_data(metadata_id)
    if df.empty:
        return go.Figure(), []

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["time_min"],
        y=df["channel_1"],
        mode="lines",
        name="STD Chromatogram",
        line=dict(color="#2E86AB", width=1.5)
    ))

    # Get peaks from database and select top N by height
    peaks = get_peak_results(metadata_id, integration_method='empower')
    if peaks:
        # Sort by height and take top N
        top_peaks = sorted(peaks, key=lambda p: p["height"], reverse=True)[:num_peaks_to_keep]
        # Sort selected peaks by retention time
        sorted_peaks = sorted(top_peaks, key=lambda p: p["retention_time"])
        
        # Assign default MWs
        default_mws = [10, 20, 35, 50, 100, 150, 250]
        table_data = []
        
        for i, peak in enumerate(sorted_peaks):
            table_data.append({
                "peak_rt": round(peak["retention_time"], 3),
                "peak_height": round(peak["height"], 3),
                "assigned_mw": default_mws[i] if i < len(default_mws) else ""
            })
            
            # Add peak markers
            fig.add_trace(go.Scatter(
                x=[peak["retention_time"]],
                y=[peak["height"]],
                mode="markers",
                marker=dict(size=8, color="red"),
                showlegend=False
            ))
        
        return fig, table_data
    
    return fig, []