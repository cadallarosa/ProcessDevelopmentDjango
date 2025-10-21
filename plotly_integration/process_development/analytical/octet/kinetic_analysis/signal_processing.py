"""
Data Processing

Functions for processing Octet sensor data:
- Reference subtraction
- Baseline alignment
- Savitzky-Golay filtering
"""

import numpy as np
from scipy.signal import savgol_filter
from typing import Optional, Tuple


def subtract_reference(sample_signal: np.ndarray,
                       reference_signal: np.ndarray,
                       time_array: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Subtract reference well signal from sample signal

    Args:
        sample_signal: Signal from sample well
        reference_signal: Signal from reference well (buffer only)
        time_array: Optional time array for validation

    Returns:
        Reference-corrected signal
    """
    # Ensure arrays are same length
    min_len = min(len(sample_signal), len(reference_signal))

    corrected_signal = sample_signal[:min_len] - reference_signal[:min_len]

    return corrected_signal


def align_baseline(signal: np.ndarray,
                   time: np.ndarray,
                   baseline_start: float = 50.0,
                   baseline_end: float = 100.0) -> np.ndarray:
    """
    Align signal to baseline by subtracting average in baseline window

    Args:
        signal: Signal array
        time: Time array
        baseline_start: Start of baseline window (seconds)
        baseline_end: End of baseline window (seconds)

    Returns:
        Baseline-aligned signal
    """
    # Find indices for baseline window
    baseline_mask = (time >= baseline_start) & (time <= baseline_end)

    if not np.any(baseline_mask):
        # If no data in window, use first 50 points
        baseline_avg = np.mean(signal[:50])
    else:
        baseline_avg = np.mean(signal[baseline_mask])

    aligned_signal = signal - baseline_avg

    return aligned_signal


def apply_savgol_filter(signal: np.ndarray,
                        window_length: int = 11,
                        polyorder: int = 3) -> np.ndarray:
    """
    Apply Savitzky-Golay smoothing filter

    Args:
        signal: Signal array
        window_length: Size of smoothing window (must be odd)
        polyorder: Polynomial order for fitting

    Returns:
        Smoothed signal
    """
    # Ensure window length is odd
    if window_length % 2 == 0:
        window_length += 1

    # Ensure window length is not larger than signal
    window_length = min(window_length, len(signal))
    if window_length < polyorder + 2:
        return signal  # Can't filter, return original

    smoothed_signal = savgol_filter(signal, window_length, polyorder)

    return smoothed_signal


def process_sensor_data(sample_signal: np.ndarray,
                        time: np.ndarray,
                        reference_signal: Optional[np.ndarray] = None,
                        baseline_window: Tuple[float, float] = (50.0, 100.0),
                        apply_filter: bool = True,
                        filter_window: int = 11,
                        filter_polyorder: int = 3) -> np.ndarray:
    """
    Complete processing pipeline for sensor data

    Steps:
    1. Reference subtraction (if reference provided)
    2. Baseline alignment
    3. Savitzky-Golay filtering (optional)

    Args:
        sample_signal: Raw signal from sample well
        time: Time array
        reference_signal: Optional reference signal for subtraction
        baseline_window: (start, end) time window for baseline calculation
        apply_filter: Whether to apply Savitzky-Golay filter
        filter_window: Window size for filter
        filter_polyorder: Polynomial order for filter

    Returns:
        Processed signal
    """
    signal = sample_signal.copy()

    # Step 1: Reference subtraction
    if reference_signal is not None:
        signal = subtract_reference(signal, reference_signal, time)

    # Step 2: Baseline alignment
    signal = align_baseline(signal, time, baseline_window[0], baseline_window[1])

    # Step 3: Savitzky-Golay filtering
    if apply_filter:
        signal = apply_savgol_filter(signal, filter_window, filter_polyorder)

    return signal


def calculate_steady_state_response(signal: np.ndarray,
                                     time: np.ndarray,
                                     ss_start: float = 170.0,
                                     ss_end: float = 180.0) -> float:
    """
    Calculate steady-state response (average signal near end of association)

    Args:
        signal: Signal array
        time: Time array
        ss_start: Start of steady-state window (seconds)
        ss_end: End of steady-state window (seconds)

    Returns:
        Average steady-state response
    """
    ss_mask = (time >= ss_start) & (time <= ss_end)

    if not np.any(ss_mask):
        # Use last 10 points
        return np.mean(signal[-10:])

    return np.mean(signal[ss_mask])


def split_association_dissociation(time: np.ndarray,
                                    signal: np.ndarray,
                                    split_time: float = 180.0) -> Tuple[Tuple[np.ndarray, np.ndarray],
                                                                          Tuple[np.ndarray, np.ndarray]]:
    """
    Split binding curve into association and dissociation phases

    Args:
        time: Time array
        signal: Signal array
        split_time: Time point to split (end of association)

    Returns:
        ((assoc_time, assoc_signal), (dissoc_time, dissoc_signal))
    """
    # Find split point
    split_idx = np.searchsorted(time, split_time)

    # Association phase
    assoc_time = time[:split_idx]
    assoc_signal = signal[:split_idx]

    # Dissociation phase (reset time to start at 0)
    dissoc_time = time[split_idx:] - time[split_idx]
    dissoc_signal = signal[split_idx:]

    return (assoc_time, assoc_signal), (dissoc_time, dissoc_signal)


def calculate_response_at_time(time: np.ndarray,
                                signal: np.ndarray,
                                target_time: float) -> float:
    """
    Get response at specific time point (with interpolation)

    Args:
        time: Time array
        signal: Signal array
        target_time: Desired time point

    Returns:
        Interpolated signal value at target time
    """
    return np.interp(target_time, time, signal)


if __name__ == "__main__":
    # Test data processing functions
    print("Testing Data Processing Functions...")

    # Generate synthetic data
    time = np.linspace(0, 240, 1200)  # 0.2s intervals

    # Simulate association (exponential rise) and dissociation (exponential decay)
    signal = np.zeros_like(time)

    # Association phase (0-180s)
    assoc_mask = time <= 180
    signal[assoc_mask] = 1.0 * (1 - np.exp(-0.01 * time[assoc_mask]))

    # Dissociation phase (180-240s)
    dissoc_mask = time > 180
    dissoc_time = time[dissoc_mask] - 180
    signal[dissoc_mask] = signal[assoc_mask][-1] * np.exp(-0.005 * dissoc_time)

    # Add noise
    signal += np.random.normal(0, 0.02, len(signal))

    # Add baseline offset
    signal += 0.5

    # Create reference signal (drift only)
    reference = 0.5 + 0.0001 * time + np.random.normal(0, 0.01, len(signal))

    print("\nOriginal signal:")
    print(f"  Mean: {signal.mean():.3f}")
    print(f"  Range: {signal.min():.3f} - {signal.max():.3f}")

    # Process signal
    processed = process_sensor_data(
        signal,
        time,
        reference_signal=reference,
        baseline_window=(50, 100),
        apply_filter=True
    )

    print("\nProcessed signal:")
    print(f"  Mean: {processed.mean():.3f}")
    print(f"  Range: {processed.min():.3f} - {processed.max():.3f}")

    # Calculate steady-state response
    ss_response = calculate_steady_state_response(processed, time)
    print(f"\nSteady-state response: {ss_response:.3f}")

    # Split into phases
    (assoc_time, assoc_signal), (dissoc_time, dissoc_signal) = split_association_dissociation(
        time, processed
    )
    print(f"\nAssociation phase: {len(assoc_time)} points, {assoc_time[-1]:.1f}s")
    print(f"Dissociation phase: {len(dissoc_time)} points, {dissoc_time[-1]:.1f}s")
