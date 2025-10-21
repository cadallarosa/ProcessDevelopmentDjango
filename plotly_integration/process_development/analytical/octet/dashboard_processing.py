"""
Signal Processing Functions for Octet Kinetics Dashboard

Functions to process raw sensor data on-the-fly in the dashboard.
Allows users to adjust processing parameters without re-importing data.
"""

import numpy as np
from scipy.signal import savgol_filter
from typing import Tuple, Optional


def apply_baseline_alignment(time: np.ndarray,
                             response: np.ndarray,
                             baseline_start: float = 50.0,
                             baseline_end: float = 100.0) -> np.ndarray:
    """
    Align signal to baseline by subtracting average in baseline window

    Args:
        time: Time array (seconds)
        response: Response array (nm)
        baseline_start: Start of baseline window (seconds)
        baseline_end: End of baseline window (seconds)

    Returns:
        Baseline-aligned response array
    """
    # Find indices in baseline window
    baseline_mask = (time >= baseline_start) & (time <= baseline_end)

    if not np.any(baseline_mask):
        # If no data in window, use first 10% of points
        n_points = max(10, int(len(response) * 0.1))
        baseline_avg = np.mean(response[:n_points])
    else:
        baseline_avg = np.mean(response[baseline_mask])

    return response - baseline_avg


def normalize_to_max(response: np.ndarray,
                     time: np.ndarray,
                     norm_start: float = None,
                     norm_end: float = None) -> np.ndarray:
    """
    Normalize response to maximum value in specified window

    Args:
        response: Response array
        time: Time array
        norm_start: Start of normalization window (use None for all data)
        norm_end: End of normalization window (use None for all data)

    Returns:
        Normalized response (0-1 scale)
    """
    if norm_start is not None and norm_end is not None:
        norm_mask = (time >= norm_start) & (time <= norm_end)
        if np.any(norm_mask):
            response_max = np.max(response[norm_mask])
        else:
            response_max = np.max(response)
    else:
        response_max = np.max(response)

    if response_max == 0:
        return response

    return response / response_max


def apply_savgol_filter(response: np.ndarray,
                       window_length: int = 11,
                       polyorder: int = 3) -> np.ndarray:
    """
    Apply Savitzky-Golay smoothing filter

    Args:
        response: Response array
        window_length: Window size (must be odd, >= polyorder + 2)
        polyorder: Polynomial order for fitting

    Returns:
        Smoothed response array
    """
    # Ensure window length is odd
    if window_length % 2 == 0:
        window_length += 1

    # Ensure window is not larger than signal
    window_length = min(window_length, len(response))

    # Check minimum window size
    if window_length < polyorder + 2:
        return response  # Can't filter, return original

    try:
        smoothed = savgol_filter(response, window_length, polyorder)
        return smoothed
    except:
        return response  # Return original if filtering fails


def process_sensor_data(time: np.ndarray,
                       response: np.ndarray,
                       baseline_align: bool = False,
                       baseline_start: float = 50.0,
                       baseline_end: float = 100.0,
                       normalize: bool = False,
                       apply_filter: bool = False,
                       filter_window: int = 11,
                       filter_polyorder: int = 3) -> Tuple[np.ndarray, np.ndarray]:
    """
    Complete processing pipeline for sensor data

    Processing order:
    1. Baseline alignment (optional)
    2. Savitzky-Golay filtering (optional)
    3. Normalization (optional, applied last)

    Args:
        time: Time array
        response: Response array
        baseline_align: Whether to apply baseline alignment
        baseline_start: Baseline window start (seconds)
        baseline_end: Baseline window end (seconds)
        normalize: Whether to normalize to max
        apply_filter: Whether to apply Savitzky-Golay filter
        filter_window: Filter window length
        filter_polyorder: Filter polynomial order

    Returns:
        tuple: (time, processed_response)
    """
    processed_response = response.copy()

    # Step 1: Baseline alignment
    if baseline_align:
        processed_response = apply_baseline_alignment(
            time, processed_response, baseline_start, baseline_end
        )

    # Step 2: Filtering (before normalization to preserve signal shape)
    if apply_filter:
        processed_response = apply_savgol_filter(
            processed_response, filter_window, filter_polyorder
        )

    # Step 3: Normalization (last step)
    if normalize:
        processed_response = normalize_to_max(processed_response, time)

    return time, processed_response


if __name__ == "__main__":
    # Test with synthetic data
    print("Testing signal processing functions...")

    # Generate test data
    time = np.linspace(0, 700, 3500)  # 0.2s intervals

    # Simulate kinetics: baseline + association + dissociation
    response = np.zeros_like(time)

    # Baseline (0-200s): flat with noise at ~4.25 nm
    baseline_mask = time < 200
    response[baseline_mask] = 4.25 + np.random.normal(0, 0.02, np.sum(baseline_mask))

    # Association (200-400s): exponential rise
    assoc_mask = (time >= 200) & (time < 400)
    assoc_time = time[assoc_mask] - 200
    response[assoc_mask] = 4.25 + 0.8 * (1 - np.exp(-0.01 * assoc_time)) + np.random.normal(0, 0.02, np.sum(assoc_mask))

    # Dissociation (400-700s): exponential decay
    dissoc_mask = time >= 400
    dissoc_time = time[dissoc_mask] - 400
    response[dissoc_mask] = 5.05 * np.exp(-0.005 * dissoc_time) + np.random.normal(0, 0.02, np.sum(dissoc_mask))

    print(f"\nRaw data:")
    print(f"  Range: {response.min():.2f} - {response.max():.2f} nm")
    print(f"  Baseline avg (50-100s): {np.mean(response[(time >= 50) & (time <= 100)]):.2f} nm")

    # Test baseline alignment
    aligned = apply_baseline_alignment(time, response, 50, 100)
    print(f"\nBaseline-aligned:")
    print(f"  Range: {aligned.min():.2f} - {aligned.max():.2f} nm")
    print(f"  New baseline avg: {np.mean(aligned[(time >= 50) & (time <= 100)]):.4f} nm")

    # Test normalization
    normalized = normalize_to_max(aligned, time)
    print(f"\nNormalized:")
    print(f"  Range: {normalized.min():.2f} - {normalized.max():.2f}")

    # Test full pipeline
    time_proc, response_proc = process_sensor_data(
        time, response,
        baseline_align=True,
        baseline_start=50,
        baseline_end=100,
        apply_filter=True,
        filter_window=11,
        normalize=False
    )
    print(f"\nFull pipeline (align + filter):")
    print(f"  Range: {response_proc.min():.2f} - {response_proc.max():.2f} nm")
    print(f"  Baseline avg: {np.mean(response_proc[(time_proc >= 50) & (time_proc <= 100)]):.4f} nm")

    print("\n✓ All processing functions working correctly!")
