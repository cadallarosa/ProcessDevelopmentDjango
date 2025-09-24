import numpy as np
import plotly.graph_objects as go

def calculate_baseline(signal, window=350, percentile=10, time=None):
    """Calculate baseline using CIEF app's optimized method"""
    from scipy.signal import savgol_filter
    from scipy.ndimage import gaussian_filter1d
    import numpy as np

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

def process_peaks(peaks, sample_name, sample_type='reduced', light_chain_time=None, marker_peak_time=None, df=None, regression_params=None, reduced_reference_times=None):
    """
    Process Empower peaks to categorize them into LMW, Light Chain/Heavy Chain (reduced) or Intact (non-reduced), and HMW
    Returns both summary statistics and classified peaks for visualization

    Args:
        peaks: List of peak dictionaries from PeakResults table
        sample_name: Name of the sample for debugging
        sample_type: 'reduced' or 'non-reduced' to determine peak labeling
        light_chain_time: Expected light chain retention time (for reduced samples)
        marker_peak_time: Marker peak time to exclude from analysis
        df: DataFrame with time series data for calculating missing peak heights
        regression_params: Dictionary with 'slope' and 'intercept' for MW calculation

    Returns:
        Dictionary with:
            - summary: Dictionary with categorized peak percentages and MW values
            - classified_peaks: List of tuples (peak_dict, class_label) for visualization
            - percentages: Dictionary with percentage values for each class
            - mw_values: Dictionary with MW values for each class
            - peak_times: Dictionary with peak times for each class
    """
    if not peaks:
        print(f"[DEBUG] {sample_name}: No peaks found for Empower integration")
        if sample_type == 'reduced':
            empty_percentages = {"LMW": 0.0, "Light Chain": 0.0, "Heavy Chain": 0.0, "HMW": 0.0}
            empty_mw_values = {"LMW": None, "Light Chain": None, "Heavy Chain": None, "HMW": None}
            empty_peak_times = {"LMW": None, "Light Chain": None, "Heavy Chain": None, "HMW": None}
        else:
            empty_percentages = {"LMW": 0.0, "Light Chain": 0.0, "Intact": 0.0, "HMW": 0.0}
            empty_mw_values = {"LMW": None, "Light Chain": None, "Intact": None, "HMW": None}
            empty_peak_times = {"LMW": None, "Light Chain": None, "Intact": None, "HMW": None}

        # Build summary for backward compatibility
        empty_summary = {}
        for key in empty_percentages:
            empty_summary[f'{key} (%)'] = empty_percentages[key]
            empty_summary[f'{key} MW (kDa)'] = empty_mw_values[key]
            empty_summary[f'{key} Time'] = empty_peak_times[key]

        return {
            'summary': empty_summary,
            'classified_peaks': [],
            'percentages': empty_percentages,
            'mw_values': empty_mw_values,
            'peak_times': empty_peak_times
        }

    # Filter out marker peaks if marker_peak_time is provided
    filtered_peaks = []
    for peak in peaks:
        rt = peak['peak_retention_time']
        if marker_peak_time and abs(rt - marker_peak_time) < 1.0:
            print(f"[DEBUG] Excluding marker peak at RT={rt:.3f} min (marker at {marker_peak_time:.3f})")
            continue
        filtered_peaks.append(peak)

    if not filtered_peaks:
        print(f"[DEBUG] {sample_name}: All peaks were filtered out")
        if sample_type == 'reduced':
            empty_percentages = {"LMW": 0.0, "Light Chain": 0.0, "Heavy Chain": 0.0, "HMW": 0.0}
            empty_mw_values = {"LMW": None, "Light Chain": None, "Heavy Chain": None, "HMW": None}
            empty_peak_times = {"LMW": None, "Light Chain": None, "Heavy Chain": None, "HMW": None}
        else:
            empty_percentages = {"LMW": 0.0, "Light Chain": 0.0, "Intact": 0.0, "HMW": 0.0}
            empty_mw_values = {"LMW": None, "Light Chain": None, "Intact": None, "HMW": None}
            empty_peak_times = {"LMW": None, "Light Chain": None, "Intact": None, "HMW": None}

        return {
            'summary': {},
            'classified_peaks': [],
            'percentages': empty_percentages,
            'mw_values': empty_mw_values,
            'peak_times': empty_peak_times
        }

    # Sort peaks by retention time
    sorted_peaks = sorted(filtered_peaks, key=lambda x: x['peak_retention_time'])
    print(f"[DEBUG] {sample_name}: Processing {len(sorted_peaks)} peaks with Empower integration")

    # Find the main peak (highest area)
    main_peak = max(sorted_peaks, key=lambda x: x.get('area', 0) or 0)
    main_peak_rt = main_peak['peak_retention_time']
    main_peak_area = main_peak.get('percent_area', 0) or 0

    print(f"[DEBUG] {sample_name}: Main peak at RT={main_peak_rt:.3f} min with {main_peak_area:.2f}% area")

    # Initialize results
    classified_peaks = []

    # Initialize percentages and MW values based on sample type
    if sample_type == 'reduced':
        percentages = {"LMW": 0.0, "Light Chain": 0.0, "Heavy Chain": 0.0, "HMW": 0.0}
        mw_values = {"LMW": None, "Light Chain": None, "Heavy Chain": None, "HMW": None}
        peak_times = {"LMW": None, "Light Chain": None, "Heavy Chain": None, "HMW": None}
    else:  # non-reduced
        percentages = {"LMW": 0.0, "Light Chain": 0.0, "Intact": 0.0, "HMW": 0.0}
        mw_values = {"LMW": None, "Light Chain": None, "Intact": None, "HMW": None}
        peak_times = {"LMW": None, "Light Chain": None, "Intact": None, "HMW": None}

    # Parse regression parameters for MW calculation
    regression_slope = regression_params.get('slope') if regression_params else None
    regression_intercept = regression_params.get('intercept') if regression_params else None

    # Simplified peak classification logic
    if sample_type == 'reduced':
        # For reduced samples: find top 2 peaks with >1 min RT difference
        top_peaks = sorted(sorted_peaks, key=lambda x: x.get('area', 0) or 0, reverse=True)[:2]

        light_chain_rt = None
        heavy_chain_rt = None

        if len(top_peaks) >= 2:
            # Sort by retention time
            peak1, peak2 = sorted(top_peaks, key=lambda x: x['peak_retention_time'])
            rt_diff = peak2['peak_retention_time'] - peak1['peak_retention_time']

            if rt_diff > 1.0:  # >1 minute difference
                light_chain_rt = peak1['peak_retention_time']  # Earlier peak
                heavy_chain_rt = peak2['peak_retention_time']  # Later peak
                print(f"[DEBUG] {sample_name}: LC at {light_chain_rt:.2f}, HC at {heavy_chain_rt:.2f}")
            else:
                # If no valid pair, use the main peak as heavy chain
                heavy_chain_rt = main_peak_rt
                print(f"[DEBUG] {sample_name}: Only one major peak identified at {heavy_chain_rt:.2f}")
        else:
            # Single peak case
            heavy_chain_rt = main_peak_rt

    else:  # non-reduced
        # For non-reduced: main peak is intact
        intact_rt = main_peak_rt
        light_chain_rt = None
        heavy_chain_rt = None

        # Use reference times from corresponding reduced sample if available
        if reduced_reference_times:
            ref_lc_time = reduced_reference_times.get('light_chain')
            ref_hc_time = reduced_reference_times.get('heavy_chain')

            # Check if any peaks are within 1 minute of reference times
            for peak in sorted_peaks:
                rt = peak['peak_retention_time']
                if ref_lc_time and abs(rt - ref_lc_time) <= 1.0:  # 1 minute
                    light_chain_rt = rt
                    print(f"[DEBUG] {sample_name}: Found LC at {rt:.2f} (ref: {ref_lc_time:.2f})")
                elif ref_hc_time and abs(rt - ref_hc_time) <= 1.0:  # 1 minute
                    heavy_chain_rt = rt
                    print(f"[DEBUG] {sample_name}: Found HC at {rt:.2f} (ref: {ref_hc_time:.2f})")

    # Process each peak and classify it
    for peak in sorted_peaks:
        rt = peak['peak_retention_time']
        area_percent = peak.get('percent_area', 0) or 0

        # Classify based on sample type and reference times
        if sample_type == 'reduced':
            if light_chain_rt and abs(rt - light_chain_rt) < 0.1:
                class_label = "Light Chain"
            elif heavy_chain_rt and abs(rt - heavy_chain_rt) < 0.1:
                class_label = "Heavy Chain"
            elif heavy_chain_rt and rt > heavy_chain_rt:
                class_label = "HMW"
            else:
                class_label = "LMW"
        else:  # non-reduced
            if abs(rt - intact_rt) < 0.1:
                class_label = "Intact"
            elif light_chain_rt and abs(rt - light_chain_rt) < 0.1:
                class_label = "Light Chain"
            elif heavy_chain_rt and abs(rt - heavy_chain_rt) < 0.1:
                class_label = "Heavy Chain"
            elif rt > intact_rt:
                class_label = "HMW"
            else:
                class_label = "LMW"

        # Get peak height and boundaries
        peak_height = peak.get('height', 0)
        start_time = peak.get('peak_start_time')
        end_time = peak.get('peak_end_time')

        # Calculate missing values from chromatogram if needed
        if df is not None and (peak_height == 0 or peak_height is None or start_time is None or end_time is None):
            peak_data = df[(df["time_min"] >= rt - 0.2) & (df["time_min"] <= rt + 0.2)]
            if not peak_data.empty:
                if peak_height == 0 or peak_height is None:
                    peak_height = peak_data["channel_1"].max()
                    print(f"[DEBUG] Calculated height {peak_height:.1f} for peak at RT={rt:.3f}")
                if start_time is None:
                    start_time = rt - 0.15
                if end_time is None:
                    end_time = rt + 0.15

        # Create peak dict for visualization
        peak_dict = {
            "peak_time": rt,
            "peak_height": peak_height,
            "area": peak.get("area", 0),
            "percent_area": area_percent,
            "start_time": start_time,
            "end_time": end_time,
            "baseline": [0]
        }

        # Calculate MW if regression parameters are provided
        mw_kda = None
        if regression_slope is not None and regression_intercept is not None:
            import numpy as np
            log_mw = regression_slope * rt + regression_intercept
            mw_kda = np.exp(log_mw)
            peak_dict['mw_kda'] = mw_kda

        # Add to classified peaks list
        classified_peaks.append((peak_dict, class_label))

        # Update percentages and track MW/times
        percentages[class_label] += area_percent
        if peak_times[class_label] is None:
            peak_times[class_label] = rt
            if mw_kda:
                mw_values[class_label] = round(mw_kda, 1)

    # Handle light chain time adjustment for reduced samples
    if sample_type == 'reduced' and light_chain_time is not None:
        # Find peak closest to specified light chain time
        closest_idx = None
        closest_diff = float('inf')

        for idx, (peak_dict, _) in enumerate(classified_peaks):
            diff = abs(peak_dict['peak_time'] - light_chain_time)
            if diff < closest_diff:
                closest_diff = diff
                closest_idx = idx

        if closest_idx is not None and closest_diff < 1.0:  # Within 1 minute tolerance
            # Update the classification of the closest peak to Light Chain
            peak_dict, old_class = classified_peaks[closest_idx]
            lc_rt = peak_dict['peak_time']
            lc_area = peak_dict['percent_area']

            # Update classifications
            classified_peaks[closest_idx] = (peak_dict, "Light Chain")

            # Update percentages - move area from old class to Light Chain
            percentages[old_class] -= lc_area
            percentages['Light Chain'] = lc_area
            peak_times['Light Chain'] = lc_rt

            # Update MW if available
            if 'mw_kda' in peak_dict:
                mw_values['Light Chain'] = round(peak_dict['mw_kda'], 1)

            # If the main peak was not the light chain, classify it as Heavy Chain
            if main_peak_rt != lc_rt:
                # Find the main peak in classified_peaks and update to Heavy Chain
                for idx, (peak_dict, class_label) in enumerate(classified_peaks):
                    if peak_dict['peak_time'] == main_peak_rt:
                        classified_peaks[idx] = (peak_dict, "Heavy Chain")
                        # Move area from old classification to Heavy Chain
                        if class_label == "Light Chain":
                            percentages['Light Chain'] -= peak_dict['percent_area']
                        percentages['Heavy Chain'] = peak_dict['percent_area']
                        peak_times['Heavy Chain'] = main_peak_rt

                        # Update MW if available
                        if 'mw_kda' in peak_dict:
                            mw_values['Heavy Chain'] = round(peak_dict['mw_kda'], 1)
                        break

    # Recalculate percentages based on the total area of remaining peaks
    total_area = sum([p[0]['area'] for p in classified_peaks])
    if total_area > 0:
        # Reset percentages
        for key in percentages:
            percentages[key] = 0.0

        # Recalculate percentages based on actual areas
        for peak_dict, class_label in classified_peaks:
            area = peak_dict['area']
            new_percent = (area / total_area) * 100
            percentages[class_label] += new_percent
            # Update the peak dict with the new percentage
            peak_dict['percent_area'] = new_percent

        print(f"[DEBUG] {sample_name}: Recalculated percentages based on total area {total_area:.0f}")

    # Build summary dictionary for backward compatibility
    summary = {}
    for key in percentages:
        summary[f'{key} (%)'] = percentages[key]
        summary[f'{key} MW (kDa)'] = mw_values[key]
        summary[f'{key} Time'] = peak_times[key]

    # Print debug summary
    if sample_type == 'reduced':
        print(f"[DEBUG] {sample_name}: Final percentages - LMW: {percentages['LMW']:.2f}%, "
              f"LC: {percentages['Light Chain']:.2f}%, HC: {percentages['Heavy Chain']:.2f}%, "
              f"HMW: {percentages['HMW']:.2f}%")
    else:
        print(f"[DEBUG] {sample_name}: Final percentages - LMW: {percentages['LMW']:.2f}%, "
              f"LC: {percentages['Light Chain']:.2f}%, Intact: {percentages['Intact']:.2f}%, "
              f"HMW: {percentages['HMW']:.2f}%")

    return {
        'summary': summary,
        'classified_peaks': classified_peaks,
        'percentages': percentages,
        'mw_values': mw_values,
        'peak_times': peak_times
    }



def combine_nearby_peaks(peaks, time_threshold=45.0, area_threshold=5.0):
    """Combine peaks that are within the time threshold (default 45 seconds), have <5% total area, and same classification"""
    if not peaks:
        return []

    # Sort peaks by retention time
    sorted_peaks = sorted(peaks, key=lambda x: x['peak_time'])
    combined_peaks = []
    current_group = [sorted_peaks[0]]

    for i in range(1, len(sorted_peaks)):
        peak = sorted_peaks[i]
        last_peak = current_group[-1]

        # Check if within time window, area threshold, and same classification
        time_diff = abs(peak['peak_time'] - last_peak['peak_time']) * 60  # Convert to seconds
        total_area = sum([p.get('percent_area', 0) for p in current_group]) + peak.get('percent_area', 0)
        same_class = peak.get('class_label') == last_peak.get('class_label')

        if time_diff <= time_threshold and total_area < area_threshold and same_class:
            current_group.append(peak)
        else:
            # Finalize current group
            if len(current_group) > 1:
                # Create combined peak entry
                min_time = min([p['peak_time'] for p in current_group])
                max_time = max([p['peak_time'] for p in current_group])
                max_height = max([p['peak_height'] for p in current_group])
                total_area = sum([p.get('percent_area', 0) for p in current_group])

                # Get shared classification from the group
                shared_class = current_group[0].get('class_label', 'Unknown')

                combined_peaks.append({
                    'peak_time': (min_time + max_time) / 2,  # Center time
                    'peak_height': max_height,
                    'time_range': (min_time, max_time),
                    'percent_area': total_area,
                    'peak_count': len(current_group),
                    'individual_peaks': current_group,
                    'class_label': shared_class
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

        # Get shared classification from the group
        shared_class = current_group[0].get('class_label', 'Unknown')

        combined_peaks.append({
            'peak_time': (min_time + max_time) / 2,
            'peak_height': max_height,
            'time_range': (min_time, max_time),
            'percent_area': total_area,
            'peak_count': len(current_group),
            'individual_peaks': current_group,
            'class_label': shared_class
        })
    else:
        combined_peaks.append(current_group[0])

    return combined_peaks

def add_annotations_for_peaks(fig, classified_peaks, row, col, positioning_method='fixed',
                             show_mw_in_annotations=True, y_scale=1, y_max=None, sample_type='reduced',
                             combine_time_seconds=45.0):
    """
    Add annotations for all peaks using the specified positioning method.
    Handles peak combination for 'combined' positioning mode.

    Args:
        fig: Plotly figure object
        classified_peaks: List of tuples (peak_dict, class_label)
        row, col: Subplot position
        positioning_method: Method for positioning annotations
        show_mw_in_annotations: Whether to show MW values in labels
        y_scale: Y-axis scaling factor
        y_max: Maximum Y value (for scaling)
    """
    if not classified_peaks:
        return

    # Handle multiple Intact peaks for non-reduced samples
    if sample_type == 'non-reduced':
        # Find all Intact peaks and combine them
        intact_peaks = []
        other_peaks = []

        for p, class_label in classified_peaks:
            if class_label == 'Intact':
                intact_peaks.append(p)
            else:
                other_peaks.append((p, class_label))

        # Combine multiple Intact peaks if found
        if len(intact_peaks) > 1:
            print(f"[DEBUG] Combining {len(intact_peaks)} Intact peaks")
            # Calculate combined values
            total_area = sum(p.get('percent_area', 0) for p in intact_peaks)
            peak_times = [p.get('peak_time') for p in intact_peaks]
            peak_heights = [p.get('peak_height') for p in intact_peaks]

            # Use the peak with highest area as representative
            main_intact = max(intact_peaks, key=lambda x: x.get('percent_area', 0))

            # Create combined peak
            combined_intact = main_intact.copy()
            combined_intact['percent_area'] = total_area
            combined_intact['peak_count'] = len(intact_peaks)
            combined_intact['individual_peaks'] = intact_peaks

            # Add combined peak back to the list
            classified_peaks = other_peaks + [(combined_intact, 'Intact')]

    # Prepare peaks for annotation (handle combined mode if needed)
    if positioning_method == 'combined':
        # Add class_label to peaks for combining logic
        peaks_with_area = []
        for p, class_label in classified_peaks:
            peak_copy = p.copy()
            peak_copy['class_label'] = class_label
            peaks_with_area.append(peak_copy)

        # Combine nearby peaks
        combined_peaks = combine_nearby_peaks(peaks_with_area)
        peaks_for_annotation = [(p, p.get('class_label', 'Unknown')) for p in combined_peaks]
    else:
        peaks_for_annotation = classified_peaks

    # Prepare peak data for annotation positioning
    all_peaks_data = [{'peak_time': p["peak_time"], 'peak_height': p["peak_height"]}
                     for p, _ in peaks_for_annotation]

    # Find reference peak times for smart positioning
    lc_time = None
    hc_time = None
    intact_time = None

    for p, class_label in peaks_for_annotation:
        if class_label == 'Light Chain':
            lc_time = p.get('peak_time')
        elif class_label == 'Heavy Chain':
            hc_time = p.get('peak_time')
        elif class_label == 'Intact':
            intact_time = p.get('peak_time')

    print(f"[DEBUG] Reference times - LC: {lc_time}, HC: {hc_time}, Intact: {intact_time}")

    # Track annotation offsets as we process each peak
    annotation_offsets = {}  # Dictionary to store peak_time -> ax_offset mapping

    # Add annotations for all peaks
    for peak_idx, (p, class_label) in enumerate(peaks_for_annotation):
        # Get percent_area from the peak dict
        pct = p.get("percent_area", 0)
        label = f"{class_label}<br>({pct:.1f}%)"

        # Add MW to label if available and show_mw_in_annotations is True
        if show_mw_in_annotations and 'mw_kda' in p:
            label += f"<br>{p['mw_kda']:.1f} kDa"

        peak_height = p["peak_height"]
        if y_scale and y_scale != 1 and y_max:
            peak_height = min(peak_height, y_max)

        peak_time = p["peak_time"]
        peak_data = p

        # Annotation positioning logic (consolidated from add_single_annotation)
        # Calculate dynamic offset based on peak height for better visibility
        if all_peaks_data and len(all_peaks_data) > 0:
            max_peak_height = max([p['peak_height'] for p in all_peaks_data])
        else:
            max_peak_height = peak_height

        # Use 15% of the maximum peak height for more consistent positioning
        relative_offset = max_peak_height * 0.15
        print('Relative offset for annotation:', relative_offset)

        # Determine positioning parameters based on peak class and sample type
        x_offset = 0  # Horizontal positioning offset
        y_offset = relative_offset  # Default vertical offset
        arrow_ax = 0  # Arrow tail x position (relative to annotation)
        arrow_ay = -40  # Arrow tail y position (relative to annotation)

        # Smart positioning logic based on peak class and sample type
        if positioning_method == 'fixed':
            if sample_type == 'reduced':
                # For reduced samples: LC and HC directly above with offset
                if class_label in ['Light Chain', 'Heavy Chain']:
                    # Direct positioning above peak
                    y_offset = relative_offset
                    arrow_ax = 0
                    arrow_ay = -40
                else:
                    # For LMW and HMW, check proximity to LC/HC for side positioning
                    if lc_time and abs(peak_time - lc_time) <= 1.0:
                        # Near light chain - position slightly to the right
                        x_offset = 0.1  # 0.1 minute offset
                        print(f"[DEBUG] {class_label} near LC, positioning right")
                    elif hc_time and abs(peak_time - hc_time) <= 1.0:
                        # Near heavy chain - position slightly to the left
                        x_offset = -0.1  # 0.1 minute offset
                        print(f"[DEBUG] {class_label} near HC, positioning left")

            elif sample_type == 'non-reduced':
                # Check if peak is within 30 seconds of another peak and get their actual offsets
                nearby_peaks_offsets = []
                for other_peak, other_label in peaks_for_annotation:
                    if other_peak != peak_data:  # Don't compare with itself
                        time_diff_seconds = abs(peak_time - other_peak['peak_time']) * 60  # Convert to seconds
                        if time_diff_seconds <= 30:
                            # Check if this nearby peak already has an assigned offset
                            other_peak_time = other_peak['peak_time']
                            if other_peak_time in annotation_offsets:
                                # Use the actual offset that was applied to this peak
                                nearby_offset = annotation_offsets[other_peak_time]
                            else:
                                # Use the default offset that would be applied
                                if other_label == 'Intact':
                                    nearby_offset = 0
                                elif other_label == 'LMW':
                                    nearby_offset = -40
                                elif other_label == 'HMW':
                                    nearby_offset = 40
                                else:
                                    nearby_offset = 0
                            nearby_peaks_offsets.append(nearby_offset)

                if class_label == 'Intact':
                    # Intact always has no ax offset
                    arrow_ax = 0
                    arrow_ay = -40
                elif len(nearby_peaks_offsets) > 0:
                    # Peak is within 30 seconds of another peak - apply base offset then multiply by 2
                    if class_label == 'LMW':
                        base_offset = -40  # Base offset to the left
                        arrow_ax = base_offset * 2  # Multiply by 2 for nearby peaks
                        arrow_ay = -40
                        print(f"[DEBUG] LMW peak at {peak_time:.3f}: nearby offsets {nearby_peaks_offsets}, using ax={arrow_ax}")
                    elif class_label == 'HMW':
                        base_offset = 40   # Base offset to the right
                        arrow_ax = base_offset * 2  # Multiply by 2 for nearby peaks
                        arrow_ay = -40
                        print(f"[DEBUG] HMW peak at {peak_time:.3f}: nearby offsets {nearby_peaks_offsets}, using ax={arrow_ax}")
                    else:
                        arrow_ax = 0
                        arrow_ay = -40
                else:
                    # Peak is not within 30 seconds - no ax offset
                    arrow_ax = 0
                    arrow_ay = -40

            # Standard fixed positioning with smart offsets
            fig.add_annotation(
                x=peak_time + x_offset,
                y=peak_height + y_offset,
                text=label,
                showarrow=True,
                arrowhead=1,
                ax=arrow_ax,
                ay=arrow_ay,
                xanchor="center",
                yanchor="bottom",
                row=row,
                col=col
            )

            # Store the offset for this peak for future reference
            annotation_offsets[peak_time] = arrow_ax

        elif positioning_method == 'combined':
            # Enhanced label for combined peaks
            if peak_data and 'peak_count' in peak_data:
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

            # Apply same smart positioning as fixed mode
            if sample_type == 'reduced':
                if class_label in ['Light Chain', 'Heavy Chain']:
                    y_offset = relative_offset
                    arrow_ax = 0
                    arrow_ay = -40
                else:
                    arrow_ax = 0
                    arrow_ay = -40


            elif sample_type == 'non-reduced':
                # Check if peak is within 30 seconds of another peak and get their actual offsets
                nearby_peaks_offsets = []
                for other_peak, other_label in peaks_for_annotation:
                    if other_peak != peak_data:  # Don't compare with itself
                        time_diff_seconds = abs(peak_time - other_peak['peak_time']) * 60  # Convert to seconds
                        if time_diff_seconds <= 30:
                            # Check if this nearby peak already has an assigned offset
                            other_peak_time = other_peak['peak_time']
                            if other_peak_time in annotation_offsets:
                                # Use the actual offset that was applied to this peak
                                nearby_offset = annotation_offsets[other_peak_time]
                            else:
                                # Use the default offset that would be applied
                                if other_label == 'Intact':
                                    nearby_offset = 0
                                elif other_label == 'LMW':
                                    nearby_offset = -40
                                elif other_label == 'HMW':
                                    nearby_offset = 40
                                else:
                                    nearby_offset = 0
                            nearby_peaks_offsets.append(nearby_offset)

                if class_label == 'Intact':
                    # Intact always has no ax offset
                    arrow_ax = 0
                    arrow_ay = -40
                elif len(nearby_peaks_offsets) > 0:
                    # Peak is within 30 seconds of another peak - apply base offset then multiply by 2
                    if class_label == 'LMW':
                        base_offset = -40  # Base offset to the left
                        arrow_ax = base_offset * 2  # Multiply by 2 for nearby peaks
                        arrow_ay = -40
                        print(f"[DEBUG] Combined LMW peak at {peak_time:.3f}: nearby offsets {nearby_peaks_offsets}, using ax={arrow_ax}")
                    elif class_label == 'HMW':
                        base_offset = 40   # Base offset to the right
                        arrow_ax = base_offset * 2  # Multiply by 2 for nearby peaks
                        arrow_ay = -40
                        print(f"[DEBUG] Combined HMW peak at {peak_time:.3f}: nearby offsets {nearby_peaks_offsets}, using ax={arrow_ax}")
                    else:
                        arrow_ax = 0
                        arrow_ay = -40
                else:
                    # Peak is not within 30 seconds - no ax offset
                    arrow_ax = 0
                    arrow_ay = -40

            fig.add_annotation(
                x=peak_time,
                y=peak_height,
                text=combined_label,
                showarrow=True,
                arrowhead=1,
                ax=arrow_ax,
                ay=arrow_ay,
                row=row,
                col=col
            )

            # Store the offset for this peak for future reference
            annotation_offsets[peak_time] = arrow_ax

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


def shade_peak(fig, df, start_time, end_time, class_label, row, col,
               full_baseline=None, full_time=None):
    """
    Shade the area under a peak in the chromatogram.

    Args:
        fig: Plotly figure object
        df: DataFrame with chromatogram data
        start_time: Start time of the peak
        end_time: End time of the peak
        class_label: Classification label for color selection
        row, col: Subplot position
        full_baseline: Full baseline array for the chromatogram
        full_time: Time array corresponding to full_baseline
    """
    PEAK_CLASS_COLORS = {
        "LMW": "rgba(76, 175, 80, 0.5)",  # green - increased opacity
        "Intact": "rgba(33, 150, 243, 0.5)",  # blue - increased opacity
        "Light Chain": "rgba(33, 150, 243, 0.5)",  # blue - increased opacity
        "Heavy Chain": "rgba(255, 193, 7, 0.5)",  # amber - increased opacity
        "HMW": "rgba(244, 67, 54, 0.5)",  # red - increased opacity
    }

    color = PEAK_CLASS_COLORS.get(class_label, "rgba(0,100,200,0.4)")  # fallback gray - increased opacity

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

    # Use the interpolated full baseline for accurate shading
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