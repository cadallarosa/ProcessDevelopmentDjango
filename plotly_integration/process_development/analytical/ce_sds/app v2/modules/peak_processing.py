"""
Peak Processing Module for CE-SDS Analysis App
Handles peak detection, baseline calculation, and annotation positioning.
"""

import numpy as np
from scipy.signal import find_peaks, savgol_filter, argrelextrema
from scipy.ndimage import gaussian_filter1d


def calculate_baseline(signal, method='simple', window=350, percentile=10, time=None):
    """Calculate baseline using CIEF app's optimized method"""
    from scipy.signal import savgol_filter
    from scipy.ndimage import gaussian_filter1d
    import numpy as np
    
    if method == 'simple':
        # Fast simple baseline - use larger windows to avoid peaks
        window_size = int(window) if window > 50 else len(signal) // 10
        if window_size < 100:
            window_size = 100

        min_points = []
        min_indices = []

        for i in range(0, len(signal), window_size):
            end = min(i + window_size, len(signal))
            window_data = signal[i:end]
            if len(window_data) > 0:
                # Take the 5th percentile instead of minimum to be more robust
                min_val = np.percentile(window_data, 5)
                min_idx = i + np.argmin(np.abs(window_data - min_val))
                min_points.append(signal[min_idx])
                min_indices.append(min_idx)

        # Interpolate between minimum points
        baseline = np.interp(range(len(signal)), min_indices, min_points)

        # Smoothing to remove artifacts
        if len(baseline) > 51:
            baseline = savgol_filter(baseline, 51, 3)
        elif len(baseline) > 21:
            baseline = savgol_filter(baseline, 21, 3)

        return baseline
    
    elif method == 'rolling_ball':
        # Rolling ball baseline
        baseline = np.zeros_like(signal)
        half_window = window // 2
        
        for i in range(len(signal)):
            start = max(0, i - half_window)
            end = min(len(signal), i + half_window)
            baseline[i] = np.min(signal[start:end])
        
        baseline = gaussian_filter1d(baseline, sigma=5)
        return baseline
    
    else:
        return np.zeros_like(signal)


def classify_peak_by_retention_time(retention_time, is_reduced=True, light_chain_time=None):
    """
    Classify peak based on retention time and sample type.
    
    Args:
        retention_time: Peak retention time
        is_reduced: Whether sample is reduced or non-reduced
        light_chain_time: Optional specific light chain time
    
    Returns:
        String classification: LMW, Light Chain, Heavy Chain/Intact, HMW
    """
    if is_reduced:
        # Reduced sample classification
        if retention_time < 8.0:
            return "LMW"
        elif retention_time < 12.0:
            if light_chain_time and abs(retention_time - light_chain_time) < 0.5:
                return "Light Chain"
            else:
                return "Light Chain"
        elif retention_time < 18.0:
            return "Heavy Chain"
        else:
            return "HMW"
    else:
        # Non-reduced sample classification
        if retention_time < 8.0:
            return "LMW"
        elif retention_time < 15.0:
            return "Intact"  # Non-reduced intact protein
        else:
            return "HMW"


def combine_nearby_peaks(peaks, time_threshold=30.0, area_threshold=5.0):
    """Combine peaks that are within 30 seconds and have <5% total area"""
    if not peaks:
        return []
    
    # Sort peaks by retention time
    sorted_peaks = sorted(peaks, key=lambda x: x['peak_time'])
    combined_peaks = []
    current_group = [sorted_peaks[0]]
    
    for i in range(1, len(sorted_peaks)):
        peak = sorted_peaks[i]
        last_peak = current_group[-1]
        
        # Check if within time window and area threshold
        time_diff = abs(peak['peak_time'] - last_peak['peak_time']) * 60  # Convert to seconds
        total_area = sum([p.get('percent_area', 0) for p in current_group]) + peak.get('percent_area', 0)
        
        if time_diff <= time_threshold and total_area < area_threshold:
            current_group.append(peak)
        else:
            # Finalize current group
            if len(current_group) > 1:
                # Create combined peak entry
                min_time = min([p['peak_time'] for p in current_group])
                max_time = max([p['peak_time'] for p in current_group])
                max_height = max([p['peak_height'] for p in current_group])
                total_area = sum([p.get('percent_area', 0) for p in current_group])
                
                combined_peaks.append({
                    'peak_time': (min_time + max_time) / 2,  # Center time
                    'peak_height': max_height,
                    'time_range': (min_time, max_time),
                    'percent_area': total_area,
                    'peak_count': len(current_group),
                    'individual_peaks': current_group
                })
            else:
                combined_peaks.append(current_group[0])
            
            current_group = [peak]
    
    # Handle last group
    if len(current_group) > 1:
        min_time = min([p['peak_time'] for p in current_group])
        max_time = max([p['peak_time'] for p in current_group])
        max_height = max([p['peak_height'] for p in current_group])
        total_area = sum([p.get('percent_area', 0) for p in current_group])
        
        combined_peaks.append({
            'peak_time': (min_time + max_time) / 2,
            'peak_height': max_height,
            'time_range': (min_time, max_time),
            'percent_area': total_area,
            'peak_count': len(current_group),
            'individual_peaks': current_group
        })
    else:
        combined_peaks.append(current_group[0])
    
    return combined_peaks


def add_annotation_with_positioning(fig, peak_time, peak_height, label, row, col, positioning_method='fixed',
                                    peak_index=0, all_peaks=None, y_scale=1, peak_data=None):
    """Add annotation with specified positioning method"""

    # Calculate dynamic offset based on peak height for better visibility
    if all_peaks and len(all_peaks) > 0:
        max_peak_height = max([p['peak_height'] for p in all_peaks])
    else:
        max_peak_height = peak_height
    
    # Use 15% of the maximum peak height for more consistent positioning
    relative_offset = max_peak_height * 0.15

    if positioning_method == 'fixed':
        # Standard fixed positioning
        fig.add_annotation(
            x=peak_time,
            y=peak_height + relative_offset,
            text=label,
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=0,
            row=row,
            col=col
        )

    elif positioning_method == 'combined':
        # Simplified combined mode - uses same positioning as fixed offset
        # but shows combined peak information in the label
        if peak_data and 'time_range' in peak_data:
            # This is a combined peak group - create enhanced label
            combined_label = f"{label}<br>({peak_data['peak_count']} peaks)"
            if 'individual_peaks' in peak_data:
                # Extract MW range from individual peaks if available
                mws = []
                for p in peak_data['individual_peaks']:
                    if 'mw_kda' in p:
                        mws.append(p['mw_kda'])
                if mws and len(mws) > 1:
                    combined_label += f"<br>{min(mws):.1f}-{max(mws):.1f} kDa"
        else:
            combined_label = label
        
        # Use fixed offset positioning with enhanced label
        fig.add_annotation(
            x=peak_time,
            y=peak_height + relative_offset,
            text=combined_label,
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=0,
            row=row,
            col=col
        )

    elif positioning_method == 'vertical':
        # Vertical text mode with boxed annotations
        fig.add_annotation(
            x=peak_time,
            y=peak_height + relative_offset,
            text=label,
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=0,
            textangle=90,  # Vertical text
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="black",
            borderwidth=1,
            borderpad=4,
            row=row,
            col=col
        )

    elif positioning_method == 'height_offset':
        # Height offset mode - positions annotations based on peak height
        # Taller peaks get higher offsets to reduce overlapping
        height_ratio = peak_height / max_peak_height if max_peak_height > 0 else 1
        height_offset = relative_offset * (0.5 + height_ratio)  # Scale from 50% to 150% of base offset
        
        fig.add_annotation(
            x=peak_time,
            y=peak_height + height_offset,
            text=label,
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=0,
            row=row,
            col=col
        )

    else:
        # Default to fixed positioning
        fig.add_annotation(
            x=peak_time,
            y=peak_height + relative_offset,
            text=label,
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=0,
            row=row,
            col=col
        )