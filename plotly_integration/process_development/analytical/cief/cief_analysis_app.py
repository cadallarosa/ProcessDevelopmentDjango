import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.io as pio
from django_plotly_dash import DjangoDash
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scipy.signal import find_peaks, savgol_filter
from scipy.integrate import simpson
from scipy.ndimage import gaussian_filter1d
from scipy.stats import linregress
import base64
import io
import json
import colorsys
from datetime import datetime, timezone
import os
import sys
import time  # For timing debug

from plotly_integration.models import CIEFReport, CIEFMetadata, CIEFTimeSeries
from plotly_integration.models import LimsSampleAnalysis, LimsCiefResult

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# Initialize the Dash app with Bootstrap theme
app = DjangoDash("cIEFReportViewerApp", external_stylesheets=[dbc.themes.BOOTSTRAP])


# Helper functions for peak detection
def savitzky_golay_smooth(data, window_size):
    """Apply Savitzky-Golay smoothing filter"""
    if window_size % 2 == 0:
        window_size += 1
    half_window = window_size // 2
    smoothed = data.copy()

    for i in range(half_window, len(data) - half_window):
        smoothed[i] = np.mean(data[i - half_window:i + half_window + 1])

    return smoothed


def calculate_derivatives(time, signal, smoothing=5):
    """Calculate first and second derivatives of the signal"""
    n = len(signal)
    first_deriv = np.zeros(n)
    second_deriv = np.zeros(n)

    # Smooth the signal first
    smoothed = savitzky_golay_smooth(signal, smoothing)

    # Calculate first derivative
    dt = np.mean(np.diff(time))
    first_deriv[1:-1] = (smoothed[2:] - smoothed[:-2]) / (2 * dt)
    first_deriv[0] = first_deriv[1]
    first_deriv[-1] = first_deriv[-2]

    # Calculate second derivative
    second_deriv[1:-1] = (first_deriv[2:] - first_deriv[:-2]) / (2 * dt)
    second_deriv[0] = second_deriv[1]
    second_deriv[-1] = second_deriv[-2]

    return first_deriv, second_deriv


def detect_peaks_threshold(signal, height_threshold, prominence, distance):
    """Threshold-based peak detection"""
    peaks, properties = find_peaks(
        signal,
        height=height_threshold,
        prominence=prominence,
        distance=distance
    )
    return peaks, properties


def detect_peaks_gaussian(time, signal, smooth_window, min_width):
    """Gaussian fitting peak detection with proper min width filtering"""
    if smooth_window is None:
        smooth_window = 3
    if min_width is None:
        min_width = 0.2

    if smooth_window < 3:
        smoothed = signal
    else:
        smoothed = savitzky_golay_smooth(signal, smooth_window)

    # Find local maxima
    peaks = []
    for i in range(1, len(smoothed) - 1):
        if smoothed[i] > smoothed[i - 1] and smoothed[i] > smoothed[i + 1]:
            peaks.append(i)

    # Filter by minimum width at half height
    valid_peaks = []
    for peak in peaks:
        half_height = smoothed[peak] / 2

        # Find left width
        left_idx = peak
        while left_idx > 0 and smoothed[left_idx] > half_height:
            left_idx -= 1

        # Find right width
        right_idx = peak
        while right_idx < len(smoothed) - 1 and smoothed[right_idx] > half_height:
            right_idx += 1

        # Calculate width in time units
        width = time[right_idx] - time[left_idx]

        # Only keep peaks that meet minimum width requirement
        if width >= min_width:
            valid_peaks.append(peak)
        else:
            print(f"Peak at time {time[peak]:.2f} rejected: width {width:.3f} < min_width {min_width}")

    return np.array(valid_peaks)


def detect_peaks_derivative(time, signal, smooth_factor, zero_threshold):
    """Second derivative peak detection"""
    _, second_deriv = calculate_derivatives(time, signal, smooth_factor)

    peaks = []
    threshold = zero_threshold * np.max(signal) / 100

    for i in range(1, len(second_deriv) - 1):
        if second_deriv[i - 1] < 0 and second_deriv[i] > 0 and signal[i] > threshold:
            peaks.append(i)

    return np.array(peaks)


def find_peak_boundaries(peaks, signal, baseline, method='valley', std_peak_indices=None):
    """Find integration boundaries for peaks"""
    corrected_signal = signal - baseline
    boundaries = []

    std_peaks_set = set(std_peak_indices) if std_peak_indices is not None else set()

    # Find actual sample peak indices (not positions in the peaks array)
    sample_peak_indices = []
    for i, peak in enumerate(peaks):
        if peak not in std_peaks_set:
            sample_peak_indices.append(peak)

    for idx, peak in enumerate(peaks):
        left_bound = peak
        right_bound = peak

        is_sample_peak = peak not in std_peaks_set
        is_first_sample = False
        is_last_sample = False

        # Check if this is the first or last SAMPLE peak by actual peak index
        if is_sample_peak and len(sample_peak_indices) > 0:
            is_first_sample = (peak == sample_peak_indices[0])
            is_last_sample = (peak == sample_peak_indices[-1])

        # Special handling for first sample peak
        if is_first_sample:
            # LEFT: Use threshold method first, fall back to valley if needed
            # Calculate peak prominence (height above baseline)
            peak_prominence = corrected_signal[peak]
            # Use 5% of prominence as threshold
            threshold = peak_prominence * 0.05

            # Try threshold method first
            left_bound = peak
            while left_bound > 0 and corrected_signal[left_bound] > threshold:
                left_bound -= 1

            # Check if we have a previous peak (should be the 2nd standard)
            if idx > 0:
                prev_peak = peaks[idx - 1]
                # If threshold method went past the previous peak, use valley method instead
                if left_bound <= prev_peak:
                    # Find the valley between peaks
                    if peak > prev_peak:
                        valley_region = corrected_signal[prev_peak:peak]
                        if len(valley_region) > 0:
                            min_idx = np.argmin(valley_region) + prev_peak
                            left_bound = min_idx

            # RIGHT: Use the user-selected method
            if method == 'valley' and idx < len(peaks) - 1:
                next_peak = peaks[idx + 1]
                if next_peak > peak:
                    valley_region = corrected_signal[peak:next_peak]
                    if len(valley_region) > 0:
                        min_idx = np.argmin(valley_region) + peak
                        right_bound = min_idx
            elif method == 'baseline':
                threshold = corrected_signal[peak] * 0.01
                while right_bound < len(signal) - 1 and corrected_signal[right_bound] > threshold:
                    right_bound += 1
            elif method == 'threshold':
                threshold = corrected_signal[peak] * 0.05
                while right_bound < len(signal) - 1 and corrected_signal[right_bound] > threshold:
                    right_bound += 1

        # Special handling for last sample peak
        elif is_last_sample:
            # LEFT: Use the user-selected method
            if method == 'valley' and idx > 0:
                prev_peak = peaks[idx - 1]
                if peak > prev_peak:
                    valley_region = corrected_signal[prev_peak:peak]
                    if len(valley_region) > 0:
                        min_idx = np.argmin(valley_region) + prev_peak
                        left_bound = min_idx
            elif method == 'baseline':
                threshold = corrected_signal[peak] * 0.01
                while left_bound > 0 and corrected_signal[left_bound] > threshold:
                    left_bound -= 1
            elif method == 'threshold':
                threshold = corrected_signal[peak] * 0.05
                while left_bound > 0 and corrected_signal[left_bound] > threshold:
                    left_bound -= 1

            # RIGHT: Use threshold method to extend to baseline
            peak_height = corrected_signal[peak]
            threshold = max(1000, peak_height * 0.05)  # 5% of peak height or 1000
            if peak_height < 20000:
                threshold = peak_height * 0.02  # 2% for small peaks

            while right_bound < len(signal) - 1 and corrected_signal[right_bound] > threshold:
                right_bound += 1

        # All other peaks use the user-selected method for both boundaries
        else:
            if method == 'valley':
                # Valley method - find lowest point between peaks
                if idx > 0:
                    prev_peak = peaks[idx - 1]
                    if peak > prev_peak:
                        valley_region = corrected_signal[prev_peak:peak]
                        if len(valley_region) > 0:
                            min_idx = np.argmin(valley_region) + prev_peak
                            left_bound = min_idx

                if idx < len(peaks) - 1:
                    next_peak = peaks[idx + 1]
                    if next_peak > peak:
                        valley_region = corrected_signal[peak:next_peak]
                        if len(valley_region) > 0:
                            min_idx = np.argmin(valley_region) + peak
                            right_bound = min_idx

            elif method == 'baseline':
                threshold = corrected_signal[peak] * 0.01
                while left_bound > 0 and corrected_signal[left_bound] > threshold:
                    left_bound -= 1
                while right_bound < len(signal) - 1 and corrected_signal[right_bound] > threshold:
                    right_bound += 1

            elif method == 'threshold':
                threshold = corrected_signal[peak] * 0.05
                while left_bound > 0 and corrected_signal[left_bound] > threshold:
                    left_bound -= 1
                while right_bound < len(signal) - 1 and corrected_signal[right_bound] > threshold:
                    right_bound += 1

        boundaries.append({'left': left_bound, 'right': right_bound})

    return boundaries


def calculate_baseline(signal, method='rolling_ball', window=50, percentile=10, time=None):
    """Calculate baseline using various methods - OPTIMIZED VERSION"""
    if method == 'simple':
        # Very fast simple baseline - use larger windows to avoid peaks
        # Use the window parameter if provided, otherwise calculate based on signal length
        window_size = int(window) if window > 50 else len(signal) // 10  # Increased from // 20
        if window_size < 100:  # Increased minimum from 50
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

        # Heavier smoothing to remove artifacts
        if len(baseline) > 51:
            baseline = savgol_filter(baseline, 51, 3)
        elif len(baseline) > 21:
            baseline = savgol_filter(baseline, 21, 3)

        return baseline

    elif method == 'rolling_ball':
        # Optimized rolling ball - use stride for large windows
        baseline = np.zeros_like(signal)
        half_window = window // 2

        # Use strided approach for better performance
        if window > 100:
            stride = 5  # Process every 5th point for speed
            for i in range(0, len(signal), stride):
                start = max(0, i - half_window)
                end = min(len(signal), i + half_window)
                baseline[i] = np.min(signal[start:end])

            # Interpolate missing points
            indices = np.arange(0, len(signal), stride)
            baseline = np.interp(np.arange(len(signal)), indices, baseline[indices])
        else:
            for i in range(len(signal)):
                start = max(0, i - half_window)
                end = min(len(signal), i + half_window)
                baseline[i] = np.min(signal[start:end])

        # Reduce gaussian filter sigma for speed
        baseline = gaussian_filter1d(baseline, sigma=5)
        return baseline

    elif method == 'percentile':
        return np.full_like(signal, np.percentile(signal, percentile))

    elif method == 'moving':
        # Optimized moving average baseline
        actual_window = int(window)
        half_window = actual_window // 2

        # Use numpy's more efficient sliding window
        baseline = np.zeros_like(signal)

        # Vectorized approach for percentile calculation
        if actual_window > 100:
            stride = 10
            for i in range(0, len(signal), stride):
                start = max(0, i - half_window)
                end = min(len(signal), i + half_window)
                baseline[i] = np.percentile(signal[start:end], 10)

            # Interpolate
            indices = np.arange(0, len(signal), stride)
            baseline = np.interp(np.arange(len(signal)), indices, baseline[indices])
        else:
            for i in range(len(signal)):
                start = max(0, i - half_window)
                end = min(len(signal), i + half_window)
                baseline[i] = np.percentile(signal[start:end], 10)

        # Light smoothing
        if len(baseline) > 5:
            baseline = savitzky_golay_smooth(baseline, 5)
        return baseline

    elif method == 'polynomial':
        # Optimized polynomial - use fewer valleys
        valleys = []
        window_size = max(len(signal) // 20, 10)  # Fewer valleys for speed
        for i in range(0, len(signal), window_size):
            end = min(i + window_size, len(signal))
            min_idx = np.argmin(signal[i:end]) + i
            valleys.append(min_idx)

        baseline = np.interp(range(len(signal)), valleys, signal[valleys])
        return baseline
    else:
        return np.zeros_like(signal)


def integrate_peak(signal, baseline, left_bound, right_bound, time):
    """Integrate peak area using trapezoidal rule"""
    corrected_signal = np.maximum(0, signal[left_bound:right_bound + 1] - baseline[left_bound:right_bound + 1])
    if len(corrected_signal) > 1:
        return np.trapz(corrected_signal, time[left_bound:right_bound + 1])
    return 0


def generate_peak_colors(n_peaks):
    """Generate distinct colors for peaks using golden ratio"""
    colors = []
    golden_ratio = 0.618033988749895
    hue = 0

    for i in range(n_peaks):
        hue = (hue + golden_ratio) % 1
        rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
        color = f'rgb({int(rgb[0] * 255)}, {int(rgb[1] * 255)}, {int(rgb[2] * 255)})'
        colors.append(color)

    return colors


def detect_valley_to_valley_peaks(df, signal_col="channel_1", time_col="time_min",
                                  max_peaks=3, prominence_threshold=25.0,
                                  valley_search_window=3.0, valley_drop_ratio=0.2,
                                  smoothing_window=11, smoothing_polyorder=3):
    """Detects peaks using valley-to-valley integration"""
    from scipy.signal import savgol_filter, find_peaks

    time = df[time_col].values
    signal = df[signal_col].values

    n_points = len(signal)
    safe_window = min(smoothing_window, n_points - 1 if n_points % 2 == 0 else n_points)
    if safe_window < 3:
        return [], []
    if safe_window % 2 == 0:
        safe_window -= 1

    smoothed = signal  # Using raw signal instead of smoothing

    interval = time[1] - time[0]
    min_distance = max(1, int(0.3 / interval))
    peak_indices, _ = find_peaks(smoothed, prominence=prominence_threshold, distance=min_distance)

    peak_indices = sorted(peak_indices, key=lambda i: smoothed[i], reverse=True)[:max_peaks]
    peak_indices.sort()

    peak_infos = []

    for idx in peak_indices:
        peak_time = time[idx]
        peak_height = smoothed[idx]
        min_valley_height = peak_height * (1 - valley_drop_ratio)

        left_limit = max(0, idx - int(valley_search_window / interval))
        left_slice = smoothed[left_limit:idx]
        if left_slice.size == 0:
            continue
        left_valley_idx = left_limit + np.argmin(left_slice)
        left_valley_val = smoothed[left_valley_idx]

        right_limit = min(len(smoothed) - 1, idx + int(valley_search_window / interval))
        right_slice = smoothed[idx:right_limit + 1]
        if right_slice.size == 0:
            continue
        right_valley_idx = idx + np.argmin(right_slice)
        right_valley_val = smoothed[right_valley_idx]

        if left_valley_val > min_valley_height or right_valley_val > min_valley_height:
            continue

        baseline = np.linspace(left_valley_val, right_valley_val, right_valley_idx - left_valley_idx + 1)
        signal_segment = smoothed[left_valley_idx:right_valley_idx + 1]
        time_segment = time[left_valley_idx:right_valley_idx + 1]
        area = np.trapz(signal_segment - baseline, time_segment)

        if area > 0:
            peak_infos.append({
                "peak_time": time[idx],
                "peak_height": peak_height,
                "area": area,
                "start_time": time[left_valley_idx],
                "end_time": time[right_valley_idx],
                "baseline": baseline,
                "baseline_time": time_segment,
                "signal_segment": signal_segment,
                "peak_index": idx
            })

    return sorted(peak_infos, key=lambda x: x["area"], reverse=True), smoothed


def identify_standard_peaks(df, time, signal, std_start_cutoff, std_end_cutoff):
    """Identify standard peaks and sample peaks based on time windows - OPTIMIZED"""
    pi_values = [10.0, 9.5, 5.5, 4.0]

    # Cache the dataframe filtering
    if not hasattr(identify_standard_peaks, '_cache'):
        identify_standard_peaks._cache = {}

    cache_key = f"{id(df)}_{std_start_cutoff}_{std_end_cutoff}"

    if cache_key in identify_standard_peaks._cache:
        return identify_standard_peaks._cache[cache_key]

    # Use faster peak detection for standards
    front_mask = df['time_min'] >= std_start_cutoff
    front_df = df[front_mask]

    if len(front_df) > 0:
        front_signal = front_df['channel_1'].values
        front_time = front_df['time_min'].values

        # Simple peak detection for standards
        front_peaks_local, _ = find_peaks(front_signal, height=10000, distance=20)
        front_peak_times = front_time[front_peaks_local]

        # Convert to global indices
        front_peak_indices = []
        for pt in front_peak_times[:2]:  # Only first 2
            idx = np.argmin(np.abs(time - pt))
            front_peak_indices.append(idx)
    else:
        front_peak_indices = []

    # Back standards
    back_mask = df['time_min'] >= std_end_cutoff
    back_df = df[back_mask]

    if len(back_df) > 0:
        back_signal = back_df['channel_1'].values
        back_time = back_df['time_min'].values

        # Simple peak detection for standards
        back_peaks_local, _ = find_peaks(back_signal, height=10000, distance=20)

        # Sort by height and take top 2
        if len(back_peaks_local) > 0:
            peak_heights = back_signal[back_peaks_local]
            sorted_indices = np.argsort(peak_heights)[::-1][:2]
            back_peaks_local = back_peaks_local[sorted_indices]
            back_peaks_local.sort()  # Sort by time

        back_peak_times = back_time[back_peaks_local]

        # Convert to global indices
        back_peak_indices = []
        for pt in back_peak_times:
            idx = np.argmin(np.abs(time - pt))
            back_peak_indices.append(idx)
    else:
        back_peak_indices = []

    # Standard labels
    std_labels = {}
    if len(front_peak_indices) >= 1:
        std_labels[front_peak_indices[0]] = f"pI {pi_values[0]}"
    if len(front_peak_indices) >= 2:
        std_labels[front_peak_indices[1]] = f"pI {pi_values[1]}"
    if len(back_peak_indices) >= 1:
        std_labels[back_peak_indices[0]] = f"pI {pi_values[2]}"
    if len(back_peak_indices) >= 2:
        std_labels[back_peak_indices[1]] = f"pI {pi_values[3]}"

    result = (np.array(front_peak_indices), np.array(back_peak_indices), std_labels)

    # Cache the result
    identify_standard_peaks._cache[cache_key] = result

    return result


def filter_top_n_sample_peaks(sample_peaks, signal, n_peaks, show_peaks, main_peak_idx=None, time=None):
    """Filter sample peaks to show only top N by height, ensuring representation from both basic and acidic regions"""
    if show_peaks == 'none':
        return np.array([])
    elif show_peaks == 'all':
        return sample_peaks
    elif show_peaks == 'top_n' and len(sample_peaks) > 0:
        # If we have a main peak, ensure we get peaks from both sides
        if main_peak_idx is not None and time is not None:
            main_peak_time = time[main_peak_idx]

            # Separate peaks into basic (before main) and acidic (after main)
            basic_peaks = []
            acidic_peaks = []

            for peak in sample_peaks:
                if peak == main_peak_idx:
                    continue  # Main peak will be included separately
                elif time[peak] < main_peak_time:
                    basic_peaks.append(peak)
                else:
                    acidic_peaks.append(peak)

            # Always include the main peak
            selected_peaks = [main_peak_idx]

            # Distribute remaining slots between basic and acidic
            remaining_slots = n_peaks - 1

            if len(basic_peaks) > 0 and len(acidic_peaks) > 0:
                # Allocate slots proportionally, but ensure at least 1-2 from each side if available
                basic_slots = max(1, min(len(basic_peaks), remaining_slots // 3))  # At least 1/3 for basic
                acidic_slots = remaining_slots - basic_slots

                # If we have very few basic peaks, adjust
                if len(basic_peaks) < basic_slots:
                    basic_slots = len(basic_peaks)
                    acidic_slots = remaining_slots - basic_slots

                # Sort by height and select top N from each category
                basic_heights = [(p, signal[p]) for p in basic_peaks]
                basic_heights.sort(key=lambda x: x[1], reverse=True)
                selected_basic = [p[0] for p in basic_heights[:basic_slots]]

                acidic_heights = [(p, signal[p]) for p in acidic_peaks]
                acidic_heights.sort(key=lambda x: x[1], reverse=True)
                selected_acidic = [p[0] for p in acidic_heights[:acidic_slots]]

                selected_peaks.extend(selected_basic)
                selected_peaks.extend(selected_acidic)

            elif len(basic_peaks) > 0:
                # Only basic peaks available
                basic_heights = [(p, signal[p]) for p in basic_peaks]
                basic_heights.sort(key=lambda x: x[1], reverse=True)
                selected_basic = [p[0] for p in basic_heights[:remaining_slots]]
                selected_peaks.extend(selected_basic)

            elif len(acidic_peaks) > 0:
                # Only acidic peaks available
                acidic_heights = [(p, signal[p]) for p in acidic_peaks]
                acidic_heights.sort(key=lambda x: x[1], reverse=True)
                selected_acidic = [p[0] for p in acidic_heights[:remaining_slots]]
                selected_peaks.extend(selected_acidic)

            return np.sort(np.array(selected_peaks))
        else:
            # Fallback to original behavior if no main peak
            peak_heights = signal[sample_peaks]
            sorted_indices = np.argsort(peak_heights)[::-1]
            top_indices = sorted_indices[:min(n_peaks, len(sample_peaks))]
            top_peaks = sample_peaks[top_indices]
            return np.sort(top_peaks)
    return sample_peaks


def calculate_pi_calibration(std_peaks, std_times, std_pis):
    """Calculate linear regression for pI vs time calibration"""
    if len(std_times) < 2:
        return None, None, None, None

    slope, intercept, r_value, p_value, std_err = linregress(std_times, std_pis)

    return slope, intercept, r_value ** 2, lambda t: slope * t + intercept


def classify_peaks(peak_indices, main_peak_idx, time):
    """Classify peaks as Basic, Main Peak, or Acidic"""
    classifications = {}

    if main_peak_idx is None:
        return classifications

    main_peak_time = time[main_peak_idx]

    for idx in peak_indices:
        peak_time = time[idx]
        if idx == main_peak_idx:
            classifications[idx] = "Main Peak"
        elif peak_time < main_peak_time:
            classifications[idx] = "Basic"
        else:
            classifications[idx] = "Acidic"

    return classifications


def get_classification_color(classification, pi_value=None, main_peak_pi=None):
    """
    Generate colors based on peak classification
    Basic: Blue gradient (darker = more basic/higher pI)
    Main Peak: Green
    Acidic: Red gradient (darker = more acidic/lower pI)
    """
    if classification == "Main Peak":
        return 'rgb(0, 180, 0)'  # Bright green for main peak

    elif classification == "Basic":
        # Blue gradient - darker for higher pI (more basic)
        if pi_value is not None and main_peak_pi is not None:
            # Calculate how far from main peak (higher difference = more basic)
            pi_diff = pi_value - main_peak_pi
            # Normalize to 0-1 range (assume max 2.5 pI units difference)
            intensity = min(1.0, max(0.0, pi_diff / 2.5))

            # Light blue to dark blue
            # Start at rgb(100, 150, 255) and go to rgb(0, 0, 200)
            r = int(100 * (1 - intensity))
            g = int(150 * (1 - intensity))
            b = int(200 + 55 * (1 - intensity))
        else:
            # Default medium blue if no pI info
            r, g, b = 50, 100, 230

        return f'rgb({r}, {g}, {b})'

    elif classification == "Acidic":
        # Red gradient - darker for lower pI (more acidic)
        if pi_value is not None and main_peak_pi is not None:
            # Calculate how far from main peak (larger negative difference = more acidic)
            pi_diff = main_peak_pi - pi_value
            # Normalize to 0-1 range (assume max 2.5 pI units difference)
            intensity = min(1.0, max(0.0, pi_diff / 2.5))

            # Light red to dark red
            # Start at rgb(255, 150, 150) and go to rgb(200, 0, 0)
            r = int(200 + 55 * (1 - intensity))
            g = int(150 * (1 - intensity))
            b = int(150 * (1 - intensity))
        else:
            # Default medium red if no pI info
            r, g, b = 230, 50, 50

        return f'rgb({r}, {g}, {b})'

    else:
        # Unknown classification - gray
        return 'rgb(128, 128, 128)'


# App layout
app.layout = dbc.Container([
    # Store components
    dcc.Store(id='stored-data'),
    dcc.Store(id='analysis-results'),
    dcc.Store(id='url-params'),
    dcc.Store(id='embedded-mode'),
    dcc.Store(id='selected-report'),
    dcc.Store(id='selected-result-ids'),
    dcc.Store(id='settings-loaded', data=False),
    dcc.Store(id='main-peak-trigger', data=0),
    dcc.Store(id='main-peak-settings',
              data={'mode': 'auto', 'time': None, 'applied_time': None}),

    dcc.Store(id='applied-main-peak-mode', data='auto'),
    dcc.Store(id='applied-main-peak-time', data=None),


    # URL and interval components
    dcc.Location(id='url', refresh=False),
    dcc.Interval(id='load-once', interval=1000, n_intervals=0, max_intervals=1),

    dcc.Store(id='button-reset-trigger'),
    dcc.Interval(id='button-reset-interval', interval=10000, n_intervals=0, disabled=True),

    # Report modal
    html.Div(
        id="report-modal",
        style={
            "display": "none",
            "position": "fixed",
            "top": "0",
            "left": "0",
            "width": "100%",
            "height": "100%",
            "backgroundColor": "rgba(0, 0, 0, 0.5)",
            "zIndex": "1000"
        },
        children=[
            html.Div(
                style={
                    "position": "relative",
                    "margin": "2% auto",
                    "width": "90%",
                    "maxWidth": "1400px",
                    "height": "85%",
                    "backgroundColor": "white",
                    "borderRadius": "10px",
                    "padding": "20px",
                    "boxShadow": "0 5px 15px rgba(0,0,0,0.3)",
                    "display": "flex",
                    "flexDirection": "column"
                },
                children=[
                    html.Button(
                        "✕",
                        id="close-report-modal-btn",
                        style={
                            "position": "absolute",
                            "top": "10px",
                            "right": "10px",
                            "fontSize": "24px",
                            "border": "none",
                            "backgroundColor": "transparent",
                            "cursor": "pointer",
                            "color": "#666"
                        }
                    ),
                    html.H3("Report Management",
                            style={"marginBottom": "20px", "color": "#0056b3", "textAlign": "center"}),

                    dcc.Tabs(
                        id="report-tabs",
                        value="select-tab",
                        children=[
                            dcc.Tab(
                                label="Select Report",
                                value="select-tab",
                                style={"height": "100%"},
                                children=[
                                    html.Div(
                                        style={
                                            "padding": "20px",
                                            "height": "100%",
                                            "display": "flex",
                                            "flexDirection": "column",
                                            "boxSizing": "border-box"
                                        },
                                        children=[
                                            html.H4("Select an Existing Report",
                                                    style={'marginBottom': '20px', 'color': '#0056b3'}),
                                            html.Div(
                                                style={
                                                    "flexGrow": 1,
                                                    "marginBottom": "20px",
                                                    "minHeight": 0
                                                },
                                                children=[
                                                    dash_table.DataTable(
                                                        id='report-selection-table',
                                                        columns=[
                                                            {"name": "Report ID", "id": "report_id"},
                                                            {"name": "Report Name", "id": "report_name"},
                                                            {"name": "Project ID", "id": "project_id"},
                                                            {"name": "Created By", "id": "user_id"},
                                                            {"name": "Date Created", "id": "date_created"},
                                                        ],
                                                        data=[],
                                                        row_selectable="single",
                                                        selected_rows=[],
                                                        filter_action="native",
                                                        sort_action="native",
                                                        page_action="native",
                                                        page_size=15,
                                                        fixed_rows={'headers': True},
                                                        style_table={
                                                            'height': '90%',
                                                            'overflowY': 'auto',
                                                            'overflowX': 'auto',
                                                            'borderRadius': '5px'
                                                        },
                                                        style_cell={
                                                            'textAlign': 'center',
                                                            'padding': '12px',
                                                            'fontSize': '14px',
                                                            'fontFamily': 'system-ui, -apple-system, sans-serif'
                                                        },
                                                        style_header={
                                                            'backgroundColor': '#f8f9fa',
                                                            'fontWeight': '600',
                                                            'borderBottom': '2px solid #dee2e6'
                                                        },
                                                        style_data={
                                                            'borderBottom': '1px solid #dee2e6'
                                                        },
                                                        style_data_conditional=[
                                                            {
                                                                'if': {'row_index': 'odd'},
                                                                'backgroundColor': '#f8f9fa'
                                                            }
                                                        ]
                                                    )
                                                ]
                                            ),
                                            html.Div(
                                                style={'display': 'flex', 'justifyContent': 'flex-end',
                                                       'gap': '10px'},
                                                children=[
                                                    html.Button(
                                                        "Cancel",
                                                        id="cancel-select-btn",
                                                        style={
                                                            'backgroundColor': '#6c757d',
                                                            'color': 'white',
                                                            'padding': '8px 16px',
                                                            'border': 'none',
                                                            'borderRadius': '5px',
                                                            'cursor': 'pointer',
                                                            'fontSize': '14px',
                                                            'fontWeight': '500'
                                                        }
                                                    ),
                                                    html.Button(
                                                        "Confirm Selection",
                                                        id="confirm-report-selection",
                                                        style={
                                                            'backgroundColor': '#0056b3',
                                                            'color': 'white',
                                                            'padding': '8px 16px',
                                                            'border': 'none',
                                                            'borderRadius': '5px',
                                                            'cursor': 'pointer',
                                                            'fontSize': '14px',
                                                            'fontWeight': '500'
                                                        }
                                                    ),
                                                ]
                                            )
                                        ]
                                    )
                                ]
                            ),
                            dcc.Tab(
                                label="Create Report",
                                value="create-tab",
                                children=[
                                    html.Div(
                                        style={
                                            "height": "calc(100vh - 300px)",
                                            "overflow": "hidden"
                                        },
                                        children=[
                                            html.Iframe(
                                                src="/plotly_integration/dash-app/app/cIEFReportApp/",
                                                style={
                                                    "width": "100%",
                                                    "height": "100%",
                                                    "border": "none",
                                                    "display": "block"
                                                }
                                            )
                                        ]
                                    )
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    ),

    # Toolbar
    html.Div(
        id='toolbar-container',
        style={
            'display': 'flex',
            'justifyContent': 'space-between',
            'alignItems': 'center',
            'padding': '20px 30px',
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'margin': '0 30px 30px 30px',
            'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.08)',
            'gap': '10px'
        },
        children=[
            html.Div(
                id='left-toolbar',
                style={'display': 'flex', 'gap': '20px', 'alignItems': 'center'},
                children=[
                    html.Button([
                        html.Span("📊 ", style={'marginRight': '5px'}),
                        "Select/Create Report"
                    ], id="select-create-report-btn", style={
                        'backgroundColor': '#0056b3',
                        'color': 'white',
                        'border': 'none',
                        'padding': '12px 24px',
                        'fontSize': '14px',
                        'cursor': 'pointer',
                        'borderRadius': '8px',
                        'fontWeight': '500',
                        'transition': 'background-color 0.3s ease'
                    }),
                    html.Div([
                        html.Span("Current Report: ", style={'fontWeight': '600', 'color': '#495057'}),
                        html.Span("No report selected", id="current-report-text", style={'color': '#6c757d'})
                    ], style={'marginLeft': '10px', 'fontSize': '15px'})
                ]
            ),
            html.Div(
                style={'display': 'flex', 'gap': '15px'},
                children=[
                    html.Button([
                        html.Span("💾 ", style={'marginRight': '5px'}),
                        "Save Report Settings"
                    ], id="save-settings-btn", style={
                        'backgroundColor': '#28a745',
                        'color': 'white',
                        'border': 'none',
                        'padding': '12px 24px',
                        'fontSize': '14px',
                        'cursor': 'pointer',
                        'borderRadius': '8px',
                        'fontWeight': '500',
                        'transition': 'background-color 0.3s ease'
                    }),
                    html.Button([
                        html.Span("🔗 ", style={'marginRight': '5px'}),
                        "Report Results"
                    ], id="report-results-btn", style={
                        'backgroundColor': '#17a2b8',
                        'color': 'white',
                        'border': 'none',
                        'padding': '12px 24px',
                        'fontSize': '14px',
                        'cursor': 'pointer',
                        'borderRadius': '8px',
                        'fontWeight': '500',
                        'transition': 'background-color 0.3s ease'
                    }),
                ]
            )
        ]
    ),

    # Status messages
    html.Div(id="status-message", style={
        'padding': '16px 24px',
        'margin': '0 30px 20px 30px',
        'borderRadius': '8px',
        'display': 'none',
        'fontSize': '15px',
        'fontWeight': '500',
        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
        'transition': 'all 0.3s ease'
    }),

    # Main content area
    html.Div(
        style={
            'padding': '0 30px 30px 30px',
        },
        children=[
            dbc.Tabs([
                dbc.Tab(
                    label="Electropherogram",
                    tab_id="plot-tab",
                    children=[
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Plot Settings"),
                                    dbc.CardBody([
                                        dbc.Row([
                                            dbc.Col([
                                                dbc.Label("Plot Height (px):"),
                                                dbc.Input(id='plot-height', type='number', value=400, min=200,
                                                          max=800, step=50),
                                            ], width=3),
                                            dbc.Col([
                                                dbc.Label("Plots per Row:"),
                                                dbc.Input(id='plots-per-row', type='number', value=1, min=1, max=4),
                                            ], width=3),
                                            dbc.Col([
                                                dbc.Label("Show Peaks:"),
                                                dcc.Dropdown(
                                                    id='show-peaks',
                                                    options=[
                                                        {'label': 'All', 'value': 'all'},
                                                        {'label': 'Top N (Balanced)', 'value': 'top_n'},
                                                        {'label': 'None', 'value': 'none'}
                                                    ],
                                                    value='top_n',
                                                    clearable=False
                                                ),
                                            ], width=3),
                                            dbc.Col([
                                                dbc.Label("Top N Peaks:"),
                                                dbc.Input(id='n-peaks', type='number', value=8, min=1, max=50),
                                            ], width=3),
                                        ]),
                                        dbc.Row([
                                            dbc.Col([
                                                dbc.Label("View:"),
                                                dcc.Dropdown(
                                                    id='zoom-view-dropdown',
                                                    options=[
                                                        {'label': 'View All', 'value': 'all'},
                                                        {'label': 'Sample Region', 'value': 'sample'},
                                                        {'label': 'Peak Region', 'value': 'peaks'}
                                                    ],
                                                    value='all',
                                                    clearable=False
                                                ),
                                            ], width=6),

                                        ], className="mt-3"),
                                    ])
                                ], className="mb-3"),

                                # Loading indicator with plot
                                dcc.Loading(
                                    id="loading-plot",
                                    type="default",
                                    children=html.Div(id='electropherogram-container')
                                ),

                            ], width=10),

                            dbc.Col([
                                # html.H5("Peak Detection", className="mb-3 text-center"),

                                dbc.Card([
                                    dbc.CardHeader("Method", className="py-2"),
                                    dbc.CardBody([
                                        dcc.Dropdown(
                                            id='detection-method',
                                            options=[
                                                {'label': 'Threshold', 'value': 'threshold'},
                                                {'label': 'Gaussian', 'value': 'gaussian'},
                                                {'label': 'Derivative', 'value': 'derivative'}
                                            ],
                                            value='gaussian',
                                            clearable=False
                                        ),

                                        html.Div(id='threshold-params', children=[
                                            html.Hr(),
                                            dbc.Label("Height (%):"),
                                            dcc.Slider(
                                                id='height-threshold',
                                                min=0, max=50, value=10, step=1,
                                                marks={0: '0', 25: '25', 50: '50'},
                                                tooltip={"placement": "left", "always_visible": True}
                                            ),
                                            dbc.Label("Prominence (%):"),
                                            dcc.Slider(
                                                id='prominence',
                                                min=0, max=50, value=5, step=1,
                                                marks={0: '0', 25: '25', 50: '50'},
                                                tooltip={"placement": "left", "always_visible": True}
                                            ),
                                            dbc.Label("Min Distance:"),
                                            dbc.Input(id='min-distance', type='number', value=10, min=1, size="sm"),
                                        ], style={'display': 'none'}),

                                        html.Div(id='gaussian-params', children=[
                                            html.Hr(),
                                            dbc.Label("Smooth Window:"),
                                            dbc.Input(id='smooth-window', type='number', value=3, min=3, step=2,
                                                      size="sm"),
                                            dbc.Label("Min Width:"),
                                            dbc.Input(id='min-width', type='number', value=0.1, min=0.01, step=0.1,
                                                      size="sm"),
                                        ]),

                                        html.Div(id='derivative-params', children=[
                                            html.Hr(),
                                            dbc.Label("Smooth Factor:"),
                                            dcc.Slider(
                                                id='smooth-factor',
                                                min=1, max=20, value=5, step=1,
                                                marks={1: '1', 10: '10', 20: '20'},
                                                tooltip={"placement": "left", "always_visible": True}
                                            ),
                                            dbc.Label("Zero Threshold (%):"),
                                            dcc.Slider(
                                                id='zero-threshold',
                                                min=0, max=10, value=1, step=0.1,
                                                marks={0: '0', 5: '5', 10: '10'},
                                                tooltip={"placement": "left", "always_visible": True}
                                            ),
                                        ], style={'display': 'none'}),
                                    ], className="p-2")
                                ], className="mb-2"),

                                dbc.Card([
                                    dbc.CardHeader("Integration", className="py-2"),
                                    dbc.CardBody([
                                        dbc.Label("Method:"),
                                        dcc.Dropdown(
                                            id='boundary-method',
                                            options=[
                                                {'label': 'Valley', 'value': 'valley'},
                                                {'label': 'Baseline', 'value': 'baseline'},
                                                {'label': '5% Threshold', 'value': 'threshold'}
                                            ],
                                            value='valley',
                                            clearable=False
                                        ),
                                        html.Hr(),
                                        dbc.Label("Baseline:"),
                                        dcc.Dropdown(
                                            id='baseline-method',
                                            options=[
                                                {'label': 'Simple (Fast)', 'value': 'simple'},
                                                {'label': 'Rolling Ball', 'value': 'rolling_ball'},
                                                {'label': 'Percentile', 'value': 'percentile'},
                                                {'label': 'Moving Avg', 'value': 'moving'},
                                                {'label': 'Polynomial', 'value': 'polynomial'}
                                            ],
                                            value='simple',
                                            clearable=False
                                        ),
                                        dbc.Label("Window:"),
                                        dbc.Input(id='baseline-window', type='number', value=350, min=50, size="sm"),
                                    ], className="p-2")
                                ], className="mb-2"),

                                dbc.Card([
                                    dbc.CardHeader("Standards", className="py-2"),
                                    dbc.CardBody([
                                        dbc.Label("Front Start (min):"),
                                        dbc.Input(id='std-start-cutoff', type='number', value=15, step=0.1,
                                                  size="sm"),
                                        dbc.Label("Back Start (min):"),
                                        dbc.Input(id='std-end-cutoff', type='number', value=25, step=0.1,
                                                  size="sm"),
                                    ], className="p-2")
                                ], className="mb-2"),

                                dbc.Card([
                                    dbc.CardHeader("Main Peak Selection", className="py-2"),
                                    dbc.CardBody([
                                        # Selection mode radio buttons
                                        dbc.Label("Selection Mode:", className="fw-bold"),
                                        dbc.RadioItems(
                                            id='main-peak-mode',
                                            options=[
                                                {'label': 'Auto (Highest)', 'value': 'auto'},
                                                {'label': 'Manual Time', 'value': 'manual'}
                                            ],
                                            value='auto',
                                            inline=True,
                                            className="mb-2"
                                        ),

                                        # Manual time input (conditional visibility)
                                        html.Div([
                                            dbc.Label("Time (min):"),
                                            dbc.Input(
                                                id='main-peak-time',
                                                type='number',
                                                step=0.01,
                                                size="sm",
                                                placeholder="Enter time"
                                            ),
                                        ], id='main-peak-time-container'),

                                        # Single Apply button
                                        dbc.Button('Apply', id='apply-main-peak', color="info",
                                                   size="sm", className="mt-2 w-100"),

                                        # Status/info display
                                        html.Div(id='main-peak-info', className="mt-2 small"),

                                        # Store for main peak settings
                                    ], className="p-2")
                                ]),

                            ], width=2),
                        ])
                    ]
                ),

                dbc.Tab(
                    label="Data Tables",
                    tab_id="table-tab",
                    children=[
                        dbc.Container([
                            # Add export button at the top
                            dbc.Row([
                                dbc.Col([
                                    html.H4("Peak Analysis Results", className="mt-3"),
                                ], width=8),
                                dbc.Col([
                                    html.Button([
                                        html.Span("📊 ", style={'marginRight': '5px'}),
                                        "Export to Excel"
                                    ], id="export-results-btn", style={
                                        'backgroundColor': '#6c757d',
                                        'color': 'white',
                                        'border': 'none',
                                        'padding': '10px 20px',
                                        'fontSize': '14px',
                                        'cursor': 'pointer',
                                        'borderRadius': '6px',
                                        'fontWeight': '500',
                                        'float': 'right',
                                        'marginTop': '20px'
                                    }),
                                ], width=4),
                            ]),

                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Select Sample:"),
                                    dcc.Dropdown(
                                        id='sample-selector',
                                        options=[],  # Will be populated by callback
                                        value=None,
                                        clearable=False,
                                        style={'marginBottom': '20px'}
                                    ),
                                ], width=4),
                            ]),
                            html.Div(id='peak-table-container'),

                            html.Hr(),

                            html.H4("Species Distribution"),
                            html.Div(id='category-summary-container'),

                            html.Hr(),

                            html.H4("pI Linear Regression"),
                            html.Div(id='pi-calibration-container'),
                        ], fluid=True)
                    ]
                ),
            ], id="tabs", active_tab="plot-tab"),
        ]),

    # Download component
    dcc.Download(id="download-data"),

], fluid=True)


# Callbacks

@app.callback(
    Output('url-params', 'data'),
    [Input('url', 'search')],
    prevent_initial_call=False
)
def parse_url_params(search):
    if not search:
        return {}

    # Parse query parameters
    from urllib.parse import parse_qs
    params = parse_qs(search.lstrip('?'))

    url_params = {}
    if 'report_id' in params:
        try:
            report_id = int(params['report_id'][0])
            url_params['report_id'] = report_id
        except (ValueError, TypeError):
            pass

    return url_params


# SINGLE callback that writes to selected-report (handles both URL and manual selection)
@app.callback(
    Output("selected-report", "data"),
    [Input('url-params', 'data'),
     Input("confirm-report-selection", "n_clicks")],
    [State("report-selection-table", "selected_rows"),
     State("report-selection-table", "data")],
    prevent_initial_call=False
)
def update_selected_report(url_params, confirm_clicks, selected_rows, table_data):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Handle URL parameter changes
    if triggered_id == "url-params" and url_params and url_params.get("report_id"):
        report_id = url_params.get("report_id")
        try:
            # Verify report exists in database - use CIEFReport and id field
            report = CIEFReport.objects.filter(id=report_id).first()
            if report:
                print(f"✅ Found CIEFReport {report_id}: {report.report_name}")
                return report_id
            else:
                print(f"❌ CIEFReport {report_id} not found")
        except Exception as e:
            print(f"Error validating CIEFReport {report_id}: {e}")

    # Handle manual report selection
    elif triggered_id == "confirm-report-selection" and confirm_clicks:
        if selected_rows and table_data:
            selected_row = table_data[selected_rows[0]]
            return selected_row["report_id"]

    return dash.no_update


# Update results header
@app.callback(
    Output("results-header", "children"),
    [Input("selected-report", "data")],
    prevent_initial_call=True
)
def update_results_header(selected_report):
    if not selected_report:
        return "cIEF Results"

    try:
        report_id = int(selected_report)
        report = CIEFReport.objects.filter(id=report_id).first()

        if not report:
            return f"Report {report_id} Not Found"

        return f"{report.project_id} - {report.report_name}"

    except (ValueError, TypeError):
        return "Invalid Report ID"


# Update report modal display
@app.callback(
    [Output("report-modal", "style"),
     Output("current-report-text", "children")],
    [Input("select-create-report-btn", "n_clicks"),
     Input("close-report-modal-btn", "n_clicks"),
     Input("cancel-select-btn", "n_clicks"),
     Input("confirm-report-selection", "n_clicks"),
     Input("selected-report", "data")],  # Listen for selected report changes
    [State("report-modal", "style"),
     State("report-selection-table", "selected_rows"),
     State("report-selection-table", "data")],
    prevent_initial_call=False
)
def toggle_report_modal(open_clicks, close_clicks, cancel_clicks, confirm_clicks,
                        selected_report, current_style, selected_rows, table_data):
    ctx = dash.callback_context

    if not ctx.triggered:
        triggered_id = None
    else:
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Handle selected report changes (from store)
    if triggered_id == "selected-report":
        if selected_report:
            try:
                report = CIEFReport.objects.filter(id=int(selected_report)).first()
                if report:
                    return dash.no_update, f"Report: {report.report_name} (ID: {selected_report})"
                else:
                    return dash.no_update, f"Report ID {selected_report} not found"
            except (ValueError, TypeError):
                return dash.no_update, f"Invalid report ID: {selected_report}"

    # Handle button clicks
    if triggered_id == "select-create-report-btn":
        return {**current_style, "display": "block"}, dash.no_update

    elif triggered_id in ["close-report-modal-btn", "cancel-select-btn"]:
        return {**current_style, "display": "none"}, dash.no_update

    elif triggered_id == "confirm-report-selection" and selected_rows and table_data:
        selected_report_data = table_data[selected_rows[0]]
        report_name = selected_report_data.get("report_name", "Unknown Report")
        report_id = selected_report_data.get("report_id", "Unknown ID")
        return {**current_style, "display": "none"}, f"Report: {report_name} (ID: {report_id})"

    # Default display based on current selected report
    if selected_report:
        try:
            report = CIEFReport.objects.filter(id=int(selected_report)).first()
            if report:
                return current_style, f"Report: {report.report_name} (ID: {selected_report})"
            else:
                return current_style, f"Report ID {selected_report} not found"
        except (ValueError, TypeError):
            return current_style, f"Invalid report ID: {selected_report}"

    return current_style, "No report selected"


@app.callback(
    Output("report-selection-table", "data"),
    [Input("report-modal", "style"),
     Input("report-tabs", "value")],  # Trigger when modal opens or tab changes
    prevent_initial_call=True
)
def populate_report_table(modal_style, active_tab):
    """Populate the report selection table when the modal is opened and select tab is active"""

    # Only populate if modal is visible and we're on the select tab
    if modal_style.get("display") == "block" and active_tab == "select-tab":
        try:
            # Fetch all CIEFReports
            reports = CIEFReport.objects.all().order_by('-date_created')

            report_data = []
            for report in reports:
                report_data.append({
                    "report_id": report.id,  # Use id field for CIEFReport
                    "report_name": report.report_name,
                    "project_id": report.project_id,
                    "user_id": report.user_id,
                    "date_created": report.date_created.strftime("%Y-%m-%d %H:%M") if report.date_created else ""
                })

            return report_data
        except Exception as e:
            print(f"Error fetching reports: {e}")
            return []

    return dash.no_update


# Load settings and result IDs when report is selected
@app.callback(
    [Output("selected-result-ids", "data"),
     Output('plot-height', 'value'),
     Output('plots-per-row', 'value'),
     Output('detection-method', 'value'),
     Output('boundary-method', 'value'),
     Output('baseline-method', 'value'),
     Output('baseline-window', 'value'),
     Output('height-threshold', 'value'),
     Output('prominence', 'value'),
     Output('min-distance', 'value'),
     Output('smooth-window', 'value'),
     Output('min-width', 'value'),
     Output('smooth-factor', 'value'),
     Output('zero-threshold', 'value'),
     Output('std-start-cutoff', 'value'),
     Output('std-end-cutoff', 'value'),
     Output('n-peaks', 'value'),
     Output('show-peaks', 'value'),
     Output('zoom-view-dropdown', 'value'),
     # ADD THESE NEW OUTPUTS FOR MAIN PEAK SELECTION
     Output('main-peak-mode', 'value'),
     Output('main-peak-time', 'value'),
     Output('main-peak-settings', 'data'),
     Output('settings-loaded', 'data')],
    [Input("selected-report", "data")],
    prevent_initial_call=True
)
def load_report_settings_and_result_ids(selected_report_id):
    """Load settings and result IDs when a report is selected"""
    if not selected_report_id:
        return (dash.no_update,) * 23  # UPDATE COUNT TO 22

    try:
        report = CIEFReport.objects.filter(id=int(selected_report_id)).first()

        if not report:
            return (dash.no_update,) * 23  # UPDATE COUNT TO 22

        # Get result IDs
        result_ids = [r.strip() for r in report.selected_result_ids.split(",") if r.strip()]

        # Load settings from JSON if available
        settings = report.settings if hasattr(report, 'settings') and report.settings else {}

        # CREATE MAIN PEAK SETTINGS DATA
        main_peak_settings = {
            'mode': settings.get('main_peak_mode', 'auto'),
            'time': settings.get('main_peak_time'),
            'applied_time': settings.get('main_peak_applied_time')
        }
        settings_loaded = True
        return (
            result_ids,
            settings.get('plot_height', 400),
            settings.get('plots_per_row', 1),
            settings.get('detection_method', 'gaussian'),
            settings.get('boundary_method', 'valley'),
            settings.get('baseline_method', 'simple'),
            settings.get('baseline_window', 350),
            settings.get('height_threshold', 10),
            settings.get('prominence', 5),
            settings.get('min_distance', 10),
            settings.get('smooth_window', 3),
            settings.get('min_width', 0.1),
            settings.get('smooth_factor', 5),
            settings.get('zero_threshold', 1),
            settings.get('std_start_cutoff', 15),
            settings.get('std_end_cutoff', 25),
            settings.get('n_peaks', 8),
            settings.get('show_peaks', 'top_n'),
            settings.get('zoom_view', 'all'),
            # ADD MAIN PEAK SETTINGS
            settings.get('main_peak_mode', 'auto'),
            settings.get('main_peak_time'),
            main_peak_settings,
            settings_loaded
        )


    except Exception as e:
        print(f"Error loading settings for report {selected_report_id}: {e}")
        return (dash.no_update,) * 23  # UPDATE COUNT TO 22


@app.callback(
    Output('status-message', 'children'),
    Output('status-message', 'style'),
    [Input('save-settings-btn', 'n_clicks')],
    [State('selected-report', 'data'),
     State('plot-height', 'value'),
     State('plots-per-row', 'value'),
     State('detection-method', 'value'),
     State('boundary-method', 'value'),
     State('baseline-method', 'value'),
     State('baseline-window', 'value'),
     State('height-threshold', 'value'),
     State('prominence', 'value'),
     State('min-distance', 'value'),
     State('smooth-window', 'value'),
     State('min-width', 'value'),
     State('smooth-factor', 'value'),
     State('zero-threshold', 'value'),
     State('std-start-cutoff', 'value'),
     State('std-end-cutoff', 'value'),
     State('n-peaks', 'value'),
     State('show-peaks', 'value'),
     State('zoom-view-dropdown', 'value'),
     # ADD THESE NEW STATES FOR MAIN PEAK SELECTION
     State('main-peak-mode', 'value'),
     State('main-peak-time', 'value'),
     State('main-peak-settings', 'data')],
    prevent_initial_call=True
)
def save_settings(n_clicks, selected_report, plot_height, plots_per_row, detection_method,
                  boundary_method, baseline_method, baseline_window, height_threshold,
                  prominence, min_distance, smooth_window, min_width, smooth_factor,
                  zero_threshold, std_start_cutoff, std_end_cutoff,
                  n_peaks, show_peaks, zoom_view,
                  # ADD THESE NEW PARAMETERS
                  main_peak_mode, main_peak_time, main_peak_settings):
    if not n_clicks or not selected_report:
        return dash.no_update, dash.no_update

    try:
        report = CIEFReport.objects.get(id=int(selected_report))

        # Create settings dictionary - ADD MAIN PEAK SETTINGS
        settings = {
            'plot_height': plot_height,
            'plots_per_row': plots_per_row,
            'detection_method': detection_method,
            'boundary_method': boundary_method,
            'baseline_method': baseline_method,
            'baseline_window': baseline_window,
            'height_threshold': height_threshold,
            'prominence': prominence,
            'min_distance': min_distance,
            'smooth_window': smooth_window,
            'min_width': min_width,
            'smooth_factor': smooth_factor,
            'zero_threshold': zero_threshold,
            'std_start_cutoff': std_start_cutoff,
            'std_end_cutoff': std_end_cutoff,
            'n_peaks': n_peaks,
            'show_peaks': show_peaks,
            'zoom_view': zoom_view,
            # ADD MAIN PEAK SETTINGS
            'main_peak_mode': main_peak_mode,
            'main_peak_time': main_peak_time,
            'main_peak_applied_time': main_peak_settings.get('applied_time') if main_peak_settings else None
        }

        # Save to JSON field
        report.settings = settings
        report.save()

        return ("Settings saved successfully!",
                {
                    'padding': '16px 24px',
                    'margin': '0 30px 20px 30px',
                    'borderRadius': '8px',
                    'display': 'block',
                    'fontSize': '15px',
                    'fontWeight': '500',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'transition': 'all 0.3s ease',
                    'backgroundColor': '#d4edda',
                    'color': '#155724',
                    'border': '1px solid #c3e6cb'
                })
    except Exception as e:
        return (f"Error saving settings: {str(e)}",
                {
                    'padding': '16px 24px',
                    'margin': '0 30px 20px 30px',
                    'borderRadius': '8px',
                    'display': 'block',
                    'fontSize': '15px',
                    'fontWeight': '500',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'transition': 'all 0.3s ease',
                    'backgroundColor': '#f8d7da',
                    'color': '#721c24',
                    'border': '1px solid #f5c6cb'
                })


# Simple callback to show/hide manual time input
@app.callback(
    Output('main-peak-time-container', 'style'),
    [Input('main-peak-mode', 'value')]
)
def update_main_peak_controls(mode):
    if mode == 'manual':
        return {'display': 'block'}  # Show time input
    else:
        return {'display': 'none'}  # Hide time input


# Fix the apply_main_peak_settings callback to use consistent field names:


@app.callback(
    [Output('applied-main-peak-mode', 'data'),
     Output('applied-main-peak-time', 'data'),
     Output('main-peak-info', 'children')],
    [Input('apply-main-peak', 'n_clicks'),
     Input("settings-loaded", "data")],
    [State('main-peak-mode', 'value'),
     State('main-peak-time', 'value')],
    prevent_initial_call=True
)
def apply_main_peak_settings(n_clicks, settings_loaded, mode, time_value):
    print(f"=== APPLY CALLBACK ===")
    print(f"n_clicks: {n_clicks}")
    print(f"settings_loaded: {settings_loaded}")
    print(f"mode: {mode}")
    print(f"time_value: {time_value}")

    # If no triggers, do nothing
    if not n_clicks and not settings_loaded:
        return dash.no_update, dash.no_update, dash.no_update

    # Apply the current UI values regardless of trigger
    if mode == 'auto':
        message = "✅ Applied: Auto (highest peak)"
        return 'auto', None, html.Div(message, style={'color': 'green', 'fontWeight': 'bold'})
    else:
        if time_value is not None:
            message = f"✅ Applied: Manual peak at {time_value:.2f} min"
            return 'manual', time_value, html.Div(message, style={'color': 'green', 'fontWeight': 'bold'})
        else:
            message = "⚠️ Please enter a time value"
            return dash.no_update, dash.no_update, html.Div(message, style={'color': 'orange'})

@app.callback(
    [Output('electropherogram-container', 'children'),
     Output('sample-selector', 'options'),
     Output('sample-selector', 'value'),
     Output('analysis-results', 'data')],
    [Input('selected-result-ids', 'data'),
     Input('plot-height', 'value'),
     Input('plots-per-row', 'value'),
     Input('detection-method', 'value'),
     Input('boundary-method', 'value'),
     Input('baseline-method', 'value'),
     Input('baseline-window', 'value'),
     Input('height-threshold', 'value'),
     Input('prominence', 'value'),
     Input('min-distance', 'value'),
     Input('smooth-window', 'value'),
     Input('min-width', 'value'),
     Input('smooth-factor', 'value'),
     Input('zero-threshold', 'value'),
     Input('std-start-cutoff', 'value'),
     Input('std-end-cutoff', 'value'),
     Input('n-peaks', 'value'),
     Input('show-peaks', 'value'),
     Input('zoom-view-dropdown', 'value'),
     Input('applied-main-peak-mode', 'data'),
     Input('applied-main-peak-time', 'data')]
)
def update_electropherogram_from_report(result_ids, plot_height, plots_per_row,
                                        detection_method, boundary_method, baseline_method,
                                        baseline_window, height_threshold, prominence,
                                        min_distance, smooth_window, min_width,
                                        smooth_factor, zero_threshold,
                                        std_start_cutoff, std_end_cutoff,
                                        n_peaks, show_peaks, zoom_view, applied_mode, applied_time):
    """Load data from database and create electropherogram plots with debugging"""
    print(f"=== MAIN FUNCTION CALLED ===")
    print(f"applied_mode: {applied_mode}")
    print(f"applied_time: {applied_time}")
    start_time = time.time()
    debug_times = {}

    if not result_ids:
        return (html.Div("No data to display. Please select a report.",
                         className="text-center p-5 text-muted"),
                [], None, {})

    # Database loading
    db_start = time.time()
    metas = CIEFMetadata.objects.filter(id__in=result_ids)

    result_df_by_id = {}
    for m in metas:
        timeseries_data = CIEFTimeSeries.objects.filter(metadata_id=m.id).values("time_min", "channel_1").order_by(
            "time_min")
        df = pd.DataFrame(list(timeseries_data))
        if not df.empty:
            result_df_by_id[str(m.id)] = {
                "sample_id": m.sample_id_full,
                "data": df
            }

    debug_times['database_loading'] = time.time() - db_start
    print(f"DEBUG: Database loading took {debug_times['database_loading']:.3f} seconds")

    num_results = len(result_df_by_id)
    if num_results == 0:
        return (html.Div("No data found for selected results.",
                         className="text-center p-5 text-muted"),
                [], None, {})

    # Figure setup
    num_rows = (num_results + plots_per_row - 1) // plots_per_row
    num_cols = min(plots_per_row, num_results)
    subplot_titles = [meta["sample_id"] for mid, meta in result_df_by_id.items()]

    fig = make_subplots(
        rows=num_rows,
        cols=num_cols,
        subplot_titles=subplot_titles,
        vertical_spacing=0.1 / num_rows,
        horizontal_spacing=0.1 / num_cols
    )

    # Store data for tables
    all_peaks_data = []
    all_summary_data = []
    all_calibration_data = []

    # Initialize analysis results
    analysis_results = {
        'peaks': [],
        'summary': [],
        'calibration': [],
        'peak_regions': {}
    }

    # Process each result
    for idx, (mid, meta) in enumerate(result_df_by_id.items()):
        sample_start = time.time()

        df = meta["data"]
        if df.empty:
            continue

        row = (idx // plots_per_row) + 1
        col = (idx % plots_per_row) + 1

        time_array = df["time_min"].values
        signal = df["channel_1"].values

        # Baseline calculation
        baseline_start = time.time()
        baseline = calculate_baseline(signal, baseline_method, window=baseline_window, time=time_array)
        corrected_signal = signal - baseline
        debug_times[f'baseline_{idx}'] = time.time() - baseline_start

        # Add traces
        fig.add_trace(
            go.Scatter(x=time_array, y=signal,
                       name='Signal' if idx == 0 else None,  # Only show legend for first sample
                       line=dict(color='blue', width=1),
                       showlegend=(idx == 0),  # Only first sample shows in legend
                       legendgroup="signal"),
            row=row, col=col
        )

        fig.add_trace(
            go.Scatter(x=time_array, y=baseline,
                       name='Baseline' if idx == 0 else None,  # Only show legend for first sample
                       line=dict(color='red', width=2, dash='dash'),
                       showlegend=(idx == 0),  # Only first sample shows in legend
                       legendgroup="baseline"),
            row=row, col=col
        )

        # Peak detection
        peak_detect_start = time.time()

        if detection_method == 'threshold':
            height = height_threshold * np.max(corrected_signal) / 100
            prom = prominence * np.max(corrected_signal) / 100
            peaks, _ = detect_peaks_threshold(corrected_signal, height, prom, min_distance)
        elif detection_method == 'gaussian':
            peaks = detect_peaks_gaussian(time_array, corrected_signal, smooth_window, min_width)
        else:
            peaks = detect_peaks_derivative(time_array, corrected_signal, smooth_factor, zero_threshold)

        debug_times[f'peak_detection_{idx}'] = time.time() - peak_detect_start

        if len(peaks) > 0:
            # Standard peak identification
            front_peaks, back_peaks, std_labels = identify_standard_peaks(
                df, time_array, signal, std_start_cutoff, std_end_cutoff
            )

            # Calculate sample start time based on second pI standard returning to baseline
            sample_start_time = std_start_cutoff  # Default
            sample_end_time = std_end_cutoff

            # Find where the second pI standard (pI 9.5) returns to baseline
            if len(front_peaks) >= 2:
                second_std_peak = front_peaks[1]
                peak_height = corrected_signal[second_std_peak]
                threshold = peak_height * 0.05  # 5% of peak height

                # Find right boundary where signal returns close to baseline
                right_bound = second_std_peak
                while right_bound < len(corrected_signal) - 1 and corrected_signal[right_bound] > threshold:
                    right_bound += 1

                # Start sample region after this point with a small buffer
                # Add 0.1 min buffer to ensure we're past the standard peak tail
                if right_bound < len(time_array) - 1:
                    sample_start_time = time_array[right_bound] + 0.1
                else:
                    sample_start_time = time_array[right_bound]

            # End sample region before back standards
            if len(back_peaks) > 0:
                # End before the first back standard
                sample_end_time = time_array[back_peaks[0]] - 0.5

            # Sample peaks - ONLY peaks within the sample region
            sample_mask = (time_array[peaks] > sample_start_time) & (time_array[peaks] < sample_end_time)
            sample_peaks = peaks[sample_mask]

            # Find main peak first (needed for balanced filtering)
            main_peak_idx = None
            if len(sample_peaks) > 0:
                if applied_mode == 'manual' and applied_time is not None:
                    # Manual mode - find peak closest to specified time
                    try:
                        peak_times = time_array[sample_peaks]
                        closest_peak_idx = np.argmin(np.abs(peak_times - applied_time))
                        main_peak_idx = sample_peaks[closest_peak_idx]
                        print(
                            f"Manual main peak: target={applied_time:.2f} min, found peak at {time_array[main_peak_idx]:.2f} min")
                    except Exception as e:
                        print(f"Error in manual peak selection: {e}, falling back to auto")
                        sample_heights = [(sp, signal[sp]) for sp in sample_peaks]
                        if sample_heights:
                            main_peak_idx = max(sample_heights, key=lambda x: x[1])[0]
                            print(
                                f"Auto main peak (error fallback): highest peak at {time_array[main_peak_idx]:.2f} min")
                else:
                    # Auto mode - find highest peak (default behavior)
                    sample_heights = [(sp, signal[sp]) for sp in sample_peaks]
                    if sample_heights:
                        main_peak_idx = max(sample_heights, key=lambda x: x[1])[0]
                        print(f"Auto main peak: highest peak at {time_array[main_peak_idx]:.2f} min")

            # Filter peaks with balanced representation
            filtered_sample_peaks = filter_top_n_sample_peaks(
                sample_peaks, signal, n_peaks, show_peaks, main_peak_idx, time_array
            )

            # Combine all standard peaks
            all_std_peaks = np.concatenate([front_peaks, back_peaks]) if len(front_peaks) > 0 or len(
                back_peaks) > 0 else np.array([])

            # Determine which peaks to show and analyze
            if show_peaks == 'all':
                # Show all peaks (standards + samples)
                if len(all_std_peaks) > 0 and len(sample_peaks) > 0:
                    peaks_to_show = np.sort(np.concatenate([all_std_peaks, sample_peaks]))
                elif len(all_std_peaks) > 0:
                    peaks_to_show = np.sort(all_std_peaks)
                elif len(sample_peaks) > 0:
                    peaks_to_show = np.sort(sample_peaks)
                else:
                    peaks_to_show = np.array([])
                peaks_for_table = peaks_to_show  # Include all in table
            elif show_peaks == 'top_n':
                # Show filtered sample peaks in table, but include standards for visualization
                peaks_for_table = np.sort(filtered_sample_peaks) if len(filtered_sample_peaks) > 0 else np.array([])
                # For boundaries and visualization, include both standards and filtered samples
                if len(all_std_peaks) > 0 and len(filtered_sample_peaks) > 0:
                    peaks_to_show = np.sort(np.concatenate([all_std_peaks, filtered_sample_peaks]))
                elif len(all_std_peaks) > 0:
                    peaks_to_show = np.sort(all_std_peaks)
                elif len(filtered_sample_peaks) > 0:
                    peaks_to_show = np.sort(filtered_sample_peaks)
                else:
                    peaks_to_show = np.array([])
            else:  # show_peaks == 'none'
                peaks_to_show = np.array([])
                peaks_for_table = np.array([])

            # Boundaries
            boundaries = find_peak_boundaries(peaks_to_show, signal, baseline, boundary_method,
                                              std_peak_indices=all_std_peaks) if len(peaks_to_show) > 0 else []

            # pI calibration
            std_times = []
            std_pis = []
            for peak_idx in all_std_peaks:
                if peak_idx in std_labels:
                    std_times.append(float(time_array[peak_idx]))
                    pi_value = float(std_labels[peak_idx].replace("pI ", ""))
                    std_pis.append(pi_value)

            slope, intercept, r_squared, pi_calc_func = calculate_pi_calibration(all_std_peaks, std_times, std_pis)

            if slope is not None:
                all_calibration_data.append({
                    'Sample ID': meta["sample_id"],
                    'Slope': f"{slope:.4f}",
                    'Intercept': f"{intercept:.4f}",
                    'R²': f"{r_squared:.4f}"
                })

            # Classifications
            classifications = classify_peaks(peaks_to_show, main_peak_idx, time_array)

            # Sample region bounds
            sample_region_start = sample_start_time
            sample_region_end = sample_end_time

            if len(filtered_sample_peaks) > 0 and len(boundaries) > 0:
                first_sample_idx = np.where(peaks_to_show == filtered_sample_peaks[0])[0]
                last_sample_idx = np.where(peaks_to_show == filtered_sample_peaks[-1])[0]

                if len(first_sample_idx) > 0 and len(last_sample_idx) > 0:
                    first_boundary = boundaries[first_sample_idx[0]]
                    last_boundary = boundaries[last_sample_idx[0]]
                    sample_region_start = time_array[first_boundary['left']]
                    sample_region_end = time_array[last_boundary['right']]

            # Peak markers
            if len(peaks_to_show) > 0:
                peak_times = [time_array[p] for p in peaks_to_show]
                peak_heights = [signal[p] for p in peaks_to_show]

                fig.add_trace(
                    go.Scatter(x=peak_times, y=peak_heights, mode='markers',
                               marker=dict(size=8, color='red', symbol='circle'),
                               name='Peaks' if idx == 0 else None,  # Only show legend for first sample
                               showlegend=(idx == 0),  # Only first sample shows in legend
                               legendgroup="peaks"),
                    row=row, col=col
                )

                # Process peaks
                sample_peaks_data = []
                peak_number = 1

                # First pass: calculate all pI values and get main peak pI
                peak_pis = {}
                main_peak_pi = None
                for peak_idx in peaks_to_show:
                    peak_pi = pi_calc_func(float(time_array[peak_idx])) if pi_calc_func else None
                    peak_pis[peak_idx] = peak_pi
                    if peak_idx == main_peak_idx:
                        main_peak_pi = peak_pi

                for i, (peak_idx, boundary) in enumerate(zip(peaks_to_show, boundaries)):
                    left = boundary['left']
                    right = boundary['right']

                    # Get pI value for this peak
                    peak_pi = peak_pis[peak_idx]

                    # Get classification
                    classification = classifications.get(peak_idx, 'Unknown')

                    # Get color based on classification
                    peak_color = get_classification_color(classification, peak_pi, main_peak_pi)

                    # Only shade sample peaks with gradient fill
                    if peak_idx not in all_std_peaks:
                        x_fill = np.concatenate([time_array[left:right + 1],
                                                 time_array[right:left - 1:-1] if right >= left else []])
                        y_fill = np.concatenate([signal[left:right + 1],
                                                 baseline[right:left - 1:-1] if right >= left else []])

                        if len(x_fill) > 0 and len(y_fill) > 0:
                            # Get lighter color for gradient
                            base_color = peak_color.replace('rgb(', '').replace(')', '')
                            r, g, b = map(int, base_color.split(','))
                            light_color = f'rgba({r}, {g}, {b}, 0.1)'
                            dark_color = f'rgba({r}, {g}, {b}, 0.5)'

                            fig.add_trace(
                                go.Scatter(x=x_fill, y=y_fill, fill='toself',
                                           fillcolor=dark_color,
                                           line=dict(color=peak_color, width=2),
                                           showlegend=False, hoverinfo='skip'),
                                row=row, col=col
                            )

                    # Only add to table data if this peak is in peaks_for_table
                    if peak_idx not in peaks_for_table:
                        continue

                    # Calculate area
                    area = integrate_peak(signal, baseline, left, right, time_array)

                    # Add to table data
                    classification = classifications.get(peak_idx, 'Unknown')
                    all_peaks_data.append({
                        'Sample ID': meta["sample_id"],
                        'Classification': classification,
                        'Peak #': peak_number,
                        'Time (min)': f"{time_array[peak_idx]:.2f}",
                        'Height': f"{signal[peak_idx]:.0f}",
                        'Area': f"{area:.0f}",
                        'pI': f"{peak_pi:.2f}" if peak_pi else "N/A",
                        'Left Bound': f"{time_array[left]:.2f}",
                        'Right Bound': f"{time_array[right]:.2f}"
                    })

                    # Only increment peak number for peaks that are added to table
                    peak_number += 1

                    if peak_idx in sample_peaks:
                        sample_peaks_data.append({
                            'area': area,
                            'pI': peak_pi,
                            'classification': classification
                        })

                    # Labels without arrows
                    label_parts = []
                    if peak_idx in std_labels:
                        label_parts.append(std_labels[peak_idx])
                    elif peak_pi is not None and peak_idx in sample_peaks:
                        label_parts.append(f"pI {peak_pi:.2f}")

                    if peak_idx in classifications and peak_idx not in all_std_peaks:
                        label_parts.append(f"({classifications[peak_idx]})")

                    if label_parts:
                        # Position closer to peak - only 5% above
                        y_offset = signal[peak_idx] + (np.max(signal) - np.min(signal)) * 0.05

                        fig.add_annotation(
                            x=time_array[peak_idx],
                            y=y_offset,
                            text="<br>".join(label_parts),
                            showarrow=False,  # No arrows
                            font=dict(size=9, color='black'),
                            bgcolor='rgba(255, 255, 255, 0.8)',
                            bordercolor='black',
                            borderwidth=1,
                            row=row,
                            col=col
                        )

            # Calculate distribution
            if sample_peaks_data:
                total_area = sum(p['area'] for p in sample_peaks_data)
                distribution = {'Main Peak': 0, 'Basic': 0, 'Acidic': 0}
                weighted_pi_sum = 0

                for peak in sample_peaks_data:
                    area_percent = (peak['area'] / total_area) * 100 if total_area > 0 else 0
                    distribution[peak['classification']] += area_percent

                    if peak['pI'] is not None:
                        weighted_pi_sum += peak['pI'] * peak['area']

                weighted_pi = weighted_pi_sum / total_area if total_area > 0 else None

                all_summary_data.append({
                    'Sample ID': meta["sample_id"],
                    'Basic (%)': f"{distribution['Basic']:.1f}",
                    'Main Peak (%)': f"{distribution['Main Peak']:.1f}",
                    'Acidic (%)': f"{distribution['Acidic']:.1f}",
                    'Weighted pI': f"{weighted_pi:.2f}" if weighted_pi else "N/A"
                })

            # Sample region shading - use the calculated sample start and end times
            if len(sample_peaks) > 0:
                fig.add_vrect(
                    x0=sample_start_time,
                    x1=sample_end_time,
                    fillcolor="LightGray",
                    opacity=0.2,
                    layer="below",
                    line_width=0,
                    annotation_text="Sample Region",
                    annotation_position="top left",
                    annotation_font_size=10,
                    row=row,
                    col=col
                )

            # Store peak boundaries for zoom functionality
            if len(filtered_sample_peaks) > 0 and len(boundaries) > 0:
                # Find the boundaries of first and last sample peaks
                sample_peak_indices = [i for i, p in enumerate(peaks_to_show) if p in filtered_sample_peaks]
                if sample_peak_indices:
                    first_sample_boundary = boundaries[sample_peak_indices[0]]
                    last_sample_boundary = boundaries[sample_peak_indices[-1]]
                    peak_region_start = time_array[first_sample_boundary['left']]
                    peak_region_end = time_array[last_sample_boundary['right']]

                    # Store in analysis results
                    analysis_results['peak_regions'][meta["sample_id"]] = {
                        'start': peak_region_start,
                        'end': peak_region_end
                    }

        # Update axes
        fig.update_xaxes(title_text="Time (min)" if row == num_rows else "", row=row, col=col)
        fig.update_yaxes(title_text="Signal" if col == 1 else "", row=row, col=col)

        # Zoom functionality based on dropdown selection
        if zoom_view == 'peaks' and meta["sample_id"] in analysis_results['peak_regions']:
            # Zoom to peak boundaries with no padding
            peak_region = analysis_results['peak_regions'][meta["sample_id"]]
            fig.update_xaxes(range=[peak_region['start'], peak_region['end']],
                             row=row, col=col)
        elif zoom_view == 'sample' and len(sample_peaks) > 0:
            # Zoom to sample region
            padding = (sample_end_time - sample_start_time) * 0.1
            fig.update_xaxes(range=[sample_start_time - padding, sample_end_time + padding],
                             row=row, col=col)
        # zoom_view == 'all' shows everything (default)

        debug_times[f'sample_{idx}_total'] = time.time() - sample_start
        print(f"DEBUG: Total processing for sample {idx} took {debug_times[f'sample_{idx}_total']:.3f} seconds")

    # Update layout
    fig.update_layout(
        height=plot_height * num_rows,
        title_text="cIEF Analysis Results",
        showlegend=True,
        template="plotly_white",
        legend=dict(orientation="v", yanchor="top", y=0.99, xanchor="left", x=1.01)
    )

    # Create tables
    peak_table = dash_table.DataTable(
        data=all_peaks_data,
        columns=[{"name": i, "id": i} for i in all_peaks_data[0].keys()] if all_peaks_data else [],
        style_cell={'textAlign': 'center'},
        style_data_conditional=[
            {'if': {'column_id': 'Classification', 'filter_query': '{Classification} = "Main Peak"'},
             'backgroundColor': '#d4edda', 'color': 'black'},
            {'if': {'column_id': 'Classification', 'filter_query': '{Classification} = "Basic"'},
             'backgroundColor': '#cce5ff', 'color': 'black'},
            {'if': {'column_id': 'Classification', 'filter_query': '{Classification} = "Acidic"'},
             'backgroundColor': '#f8d7da', 'color': 'black'},
        ],
        filter_action="native",
        sort_action="native",
        page_action="native",
        page_size=20,
    ) if all_peaks_data else html.Div("No peak data available")

    summary_table = dash_table.DataTable(
        data=all_summary_data,
        columns=[{"name": i, "id": i} for i in all_summary_data[0].keys()] if all_summary_data else [],
        style_cell={'textAlign': 'center'},
        style_data_conditional=[
            {'if': {'column_id': 'Weighted pI'}, 'fontWeight': 'bold'}
        ]
    ) if all_summary_data else html.Div("No summary data available")

    calibration_table = dash_table.DataTable(
        data=all_calibration_data,
        columns=[{"name": i, "id": i} for i in all_calibration_data[0].keys()] if all_calibration_data else [],
        style_cell={'textAlign': 'center'}
    ) if all_calibration_data else html.Div("No calibration data available")

    # Print debug summary
    total_time = time.time() - start_time
    print(f"\nDEBUG: TOTAL EXECUTION TIME: {total_time:.3f} seconds")
    print(f"DEBUG: Time breakdown:")
    for key, value in sorted(debug_times.items()):
        print(f"  {key}: {value:.3f} seconds ({value / total_time * 100:.1f}%)")

    # Update analysis results with collected data
    analysis_results['peaks'] = all_peaks_data
    analysis_results['summary'] = all_summary_data
    analysis_results['calibration'] = all_calibration_data

    # Get sample options for dropdown
    sample_options = []
    if all_peaks_data:
        unique_samples = list(set(p['Sample ID'] for p in all_peaks_data))
        sample_options = [{'label': s, 'value': s} for s in sorted(unique_samples)]
        first_sample = sorted(unique_samples)[0] if unique_samples else None
    else:
        first_sample = None

    return (dcc.Graph(
        id='chromatogram-plot',
        figure=fig,
        style={'height': f'{plot_height * num_rows}px'},
        config={'responsive': True}
    ), sample_options, first_sample, analysis_results)


# Callback for filtering peak table by sample
@app.callback(
    [Output('peak-table-container', 'children'),
     Output('category-summary-container', 'children'),
     Output('pi-calibration-container', 'children')],
    [Input('sample-selector', 'value'),
     Input('analysis-results', 'data')]
)
def update_tables(selected_sample, analysis_data):
    if not analysis_data:
        return (html.Div("No data available"),
                html.Div("No data available"),
                html.Div("No data available"))

    all_peaks_data = analysis_data.get('peaks', [])
    all_summary_data = analysis_data.get('summary', [])
    all_calibration_data = analysis_data.get('calibration', [])

    # Filter peak data by selected sample
    if selected_sample and all_peaks_data:
        filtered_peaks = [p for p in all_peaks_data if p['Sample ID'] == selected_sample]
    else:
        filtered_peaks = all_peaks_data

    # Create peak table
    peak_table = dash_table.DataTable(
        data=filtered_peaks,
        columns=[{"name": i, "id": i} for i in filtered_peaks[0].keys()] if filtered_peaks else [],
        style_cell={'textAlign': 'center'},
        style_data_conditional=[
            {'if': {'column_id': 'Classification', 'filter_query': '{Classification} = "Main Peak"'},
             'backgroundColor': '#d4edda', 'color': 'black'},
            {'if': {'column_id': 'Classification', 'filter_query': '{Classification} = "Basic"'},
             'backgroundColor': '#cce5ff', 'color': 'black'},
            {'if': {'column_id': 'Classification', 'filter_query': '{Classification} = "Acidic"'},
             'backgroundColor': '#f8d7da', 'color': 'black'},
        ],
        filter_action="native",
        sort_action="native",
        page_action="native",
        page_size=20,
    ) if filtered_peaks else html.Div("No peak data available")

    # Summary table
    summary_table = dash_table.DataTable(
        data=all_summary_data,
        columns=[{"name": i, "id": i} for i in all_summary_data[0].keys()] if all_summary_data else [],
        style_cell={'textAlign': 'center'},
        style_data_conditional=[
            {'if': {'column_id': 'Weighted pI'}, 'fontWeight': 'bold'}
        ]
    ) if all_summary_data else html.Div("No summary data available")

    # Calibration table
    calibration_table = dash_table.DataTable(
        data=all_calibration_data,
        columns=[{"name": i, "id": i} for i in all_calibration_data[0].keys()] if all_calibration_data else [],
        style_cell={'textAlign': 'center'},
        style_data_conditional=[
            {
                'if': {
                    'column_id': 'R²',
                    'filter_query': '{R²} >= 0.999'
                },
                'backgroundColor': '#d4edda',
                'color': 'black'
            },
            {
                'if': {
                    'column_id': 'R²',
                    'filter_query': '{R²} < 0.999'
                },
                'backgroundColor': '#fff3cd',
                'color': 'black'
            }
        ]
    ) if all_calibration_data else html.Div("No calibration data available")

    return peak_table, summary_table, calibration_table


# Export callback
@app.callback(
    Output('download-data', 'data'),
    [Input('export-results-btn', 'n_clicks')],
    [State('analysis-results', 'data')],
    prevent_initial_call=True
)
def export_results(n_clicks, analysis_data):
    if not n_clicks or not analysis_data:
        return None

    import pandas as pd
    from datetime import datetime

    # Create Excel writer with xlsxwriter engine
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book

        # Peak Analysis sheet
        if analysis_data.get('peaks'):
            df_peaks = pd.DataFrame(analysis_data['peaks'])
            df_peaks.to_excel(writer, sheet_name='Peak Analysis', index=False)

            # Format the worksheet
            worksheet = writer.sheets['Peak Analysis']
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D3D3D3',
                'border': 1
            })

            # Apply header format
            for col_num, value in enumerate(df_peaks.columns.values):
                worksheet.write(0, col_num, value, header_format)

            # Auto-adjust column widths
            for column in df_peaks:
                column_width = max(df_peaks[column].astype(str).map(len).max(), len(column))
                col_idx = df_peaks.columns.get_loc(column)
                worksheet.set_column(col_idx, col_idx, column_width + 2)

        # Species Distribution sheet
        if analysis_data.get('summary'):
            df_summary = pd.DataFrame(analysis_data['summary'])
            df_summary.to_excel(writer, sheet_name='Species Distribution', index=False)

            # Format the worksheet
            worksheet = writer.sheets['Species Distribution']
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D3D3D3',
                'border': 1
            })

            for col_num, value in enumerate(df_summary.columns.values):
                worksheet.write(0, col_num, value, header_format)

            # Auto-adjust column widths
            for column in df_summary:
                column_width = max(df_summary[column].astype(str).map(len).max(), len(column))
                col_idx = df_summary.columns.get_loc(column)
                worksheet.set_column(col_idx, col_idx, column_width + 2)

        # pI Linear Regression sheet
        if analysis_data.get('calibration'):
            df_calibration = pd.DataFrame(analysis_data['calibration'])
            df_calibration.to_excel(writer, sheet_name='pI Linear Regression', index=False)

            # Format the worksheet
            worksheet = writer.sheets['pI Linear Regression']
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D3D3D3',
                'border': 1
            })

            for col_num, value in enumerate(df_calibration.columns.values):
                worksheet.write(0, col_num, value, header_format)

            # Auto-adjust column widths
            for column in df_calibration:
                column_width = max(df_calibration[column].astype(str).map(len).max(), len(column))
                col_idx = df_calibration.columns.get_loc(column)
                worksheet.set_column(col_idx, col_idx, column_width + 2)

        # Add metadata sheet with export information
        metadata_sheet = workbook.add_worksheet('Export Info')
        metadata_sheet.write('A1', 'Export Date:')
        metadata_sheet.write('B1', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        metadata_sheet.write('A2', 'Number of Samples:')
        metadata_sheet.write('B2', len(set(p['Sample ID'] for p in analysis_data.get('peaks', []))))
        metadata_sheet.write('A3', 'Total Peaks Analyzed:')
        metadata_sheet.write('B3', len(analysis_data.get('peaks', [])))

    output.seek(0)
    filename = f"cIEF_Analysis_Results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return dcc.send_bytes(output.getvalue(), filename)


# Report results callback
@app.callback(
    [Output('threshold-params', 'style'),
     Output('gaussian-params', 'style'),
     Output('derivative-params', 'style')],
    Input('detection-method', 'value')
)
def update_parameter_visibility(method):
    """Show/hide parameter controls based on detection method"""
    styles = [{'display': 'none'}, {'display': 'none'}, {'display': 'none'}]

    if method == 'threshold':
        styles[0] = {'display': 'block'}
    elif method == 'gaussian':
        styles[1] = {'display': 'block'}
    elif method == 'derivative':
        styles[2] = {'display': 'block'}

    return styles


@app.callback(
    [Output("report-results-btn", "style"),
     Output("report-results-btn", "children")],
    Input("report-results-btn", "n_clicks"),
    State("analysis-results", "data"),
    State("selected-report", "data"),
    prevent_initial_call=True
)
def link_cief_results_to_lims(n_clicks, analysis_data, selected_report):
    """Link cIEF species distribution results to LIMS tables"""
    from django.utils import timezone

    base_style = {
        'backgroundColor': '#17a2b8',
        'color': 'white',
        'border': 'none',
        'padding': '12px 24px',
        'fontSize': '14px',
        'cursor': 'pointer',
        'borderRadius': '8px',
        'fontWeight': '500',
        'transition': 'background-color 0.3s ease'
    }

    original_text = [html.Span("🔗 ", style={'marginRight': '5px'}), "Report Results"]

    if not analysis_data or not selected_report:
        # Red for failure
        error_style = {**base_style, 'backgroundColor': '#dc3545'}
        error_text = [html.Span("❌ ", style={'marginRight': '5px'}), "No Data/Report"]
        return error_style, error_text

    # Get the report object
    try:
        report = CIEFReport.objects.get(report_name=selected_report)
    except CIEFReport.DoesNotExist:
        error_style = {**base_style, 'backgroundColor': '#dc3545'}
        error_text = [html.Span("❌ ", style={'marginRight': '5px'}), "Report Not Found"]
        return error_style, error_text

    summary_data = analysis_data.get('summary', [])
    if not summary_data:
        error_style = {**base_style, 'backgroundColor': '#dc3545'}
        error_text = [html.Span("❌ ", style={'marginRight': '5px'}), "No Data Available"]
        return error_style, error_text

    success_count = 0
    failed_samples = []

    def safe_float(value):
        """Safely convert percentage string to float"""
        try:
            # Remove % sign and convert to float
            cleaned = str(value).replace('%', '').strip()
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0

    for row in summary_data:
        sample_id = str(row.get("Sample ID")).strip()

        try:
            # Extract values from the species distribution data
            basic_percent = safe_float(row.get("Basic (%)", 0))
            main_peak_percent = safe_float(row.get("Main Peak (%)", 0))
            acidic_percent = safe_float(row.get("Acidic (%)", 0))

            # Get the LIMS sample
            sample = LimsSampleAnalysis.objects.get(sample_id=sample_id)

            # Explicit approach - handle create vs update separately to ensure FK is set
            try:
                # Try to get existing cIEF result
                cief_result = LimsCiefResult.objects.get(sample_id=sample)

                # Update existing record
                print(f"Before update: cief_result.report = {cief_result.report}")
                cief_result.main_peak = main_peak_percent
                cief_result.acidic_variants = acidic_percent
                cief_result.basic_variants = basic_percent
                cief_result.status = "complete"
                cief_result.report = report  # Explicitly set the FK to the report object
                cief_result.updated_at = timezone.now()
                cief_result.save()
                print(f"After update: cief_result.report = {cief_result.report}")

                print(f"Updated existing cIEF result for {sample_id} with FK to report {report.id}")

            except LimsCiefResult.DoesNotExist:
                # Create new record
                cief_result = LimsCiefResult.objects.create(
                    sample_id=sample,
                    main_peak=main_peak_percent,
                    acidic_variants=acidic_percent,
                    basic_variants=basic_percent,
                    status="complete",
                    report=report,  # Set the FK to the report object on creation
                    updated_at=timezone.now()
                )

                print(f"Created new cIEF result for {sample_id} with FK to report {report.id}")

            # Update the relationship in LimsSampleAnalysis
            sample.cief_result = cief_result
            sample.save()
            success_count += 1
            print(f"SUCCESS: Processed {sample_id}, total success count: {success_count}")

        except Exception as e:
            print(f"ERROR processing {sample_id}: {str(e)}")
            failed_samples.append(f"{sample_id} (Error: {str(e)})")

    print(f"FINAL RESULTS: success_count={success_count}, failed_samples={len(failed_samples)}")

    # Simplified success/failure logic
    if success_count > 0:
        # Green for success
        success_style = {**base_style, 'backgroundColor': '#28a745'}
        success_text = [html.Span("✅ ", style={'marginRight': '5px'}), f"Linked {success_count} Results"]
        return success_style, success_text
    else:
        # Red for complete failure
        error_style = {**base_style, 'backgroundColor': '#dc3545'}
        error_text = [html.Span("❌ ", style={'marginRight': '5px'}), "Failed - No Results Linked"]
        return error_style, error_text


# Callback to trigger reset timer
@app.callback(
    [Output('button-reset-interval', 'disabled'),
     Output('button-reset-trigger', 'data')],
    Input("report-results-btn", "n_clicks"),
    prevent_initial_call=True
)
def start_reset_timer(n_clicks):
    """Start 10-second timer to reset button"""
    return False, n_clicks  # Enable interval and store click count


# Callback to reset button after 10 seconds
@app.callback(
    [Output("report-results-btn", "style", allow_duplicate=True),
     Output("report-results-btn", "children", allow_duplicate=True),
     Output('button-reset-interval', 'disabled', allow_duplicate=True)],
    Input('button-reset-interval', 'n_intervals'),
    State('button-reset-trigger', 'data'),
    prevent_initial_call=True
)
def reset_button_after_delay(n_intervals, trigger_data):
    """Reset button to original style after 10 seconds"""
    if n_intervals > 0 and trigger_data:
        base_style = {
            'backgroundColor': '#17a2b8',
            'color': 'white',
            'border': 'none',
            'padding': '12px 24px',
            'fontSize': '14px',
            'cursor': 'pointer',
            'borderRadius': '8px',
            'fontWeight': '500',
            'transition': 'background-color 0.3s ease'
        }
        original_text = [html.Span("🔗 ", style={'marginRight': '5px'}), "Report Results"]
        return base_style, original_text, True  # Reset style and disable interval

    return dash.no_update, dash.no_update, dash.no_update
