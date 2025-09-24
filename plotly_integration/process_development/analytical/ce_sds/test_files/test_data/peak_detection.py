import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter, find_peaks

# Simulate signal data
np.random.seed(42)
x = np.linspace(0, 30, 3000)
baseline = 0.02 * x + 0.5 + 0.02 * np.sin(0.5 * x)
peaks = (
    np.exp(-((x - 5) / 0.3)**2) +
    0.8 * np.exp(-((x - 15) / 1.0)**2) +
    0.6 * np.exp(-((x - 24) / 0.7)**2)
)
signal = baseline + peaks + np.random.normal(0, 0.02, len(x))

# Smooth the signal
smoothed_signal = savgol_filter(signal, window_length=31, polyorder=3)

# Find peaks
peak_indices, _ = find_peaks(smoothed_signal, prominence=0.05, distance=200)

# Dynamic baseline function
def compute_peak_baseline(time, signal, peak_idx, window_min=2.0):
    """Compute baseline using average of 10 minimum signal values in ±window/2 around peak."""
    peak_time = time[peak_idx]
    half_window = window_min / 2
    mask = (time >= peak_time - half_window) & (time <= peak_time + half_window)
    window_signal = signal[mask]
    if len(window_signal) < 10:
        baseline = np.min(window_signal)
    else:
        baseline = np.mean(np.sort(window_signal)[:10])
    return baseline

# Compute dynamic baselines
window_min = 4.0
peak_baselines = []
for idx in peak_indices:
    baseline = compute_peak_baseline(x, smoothed_signal, idx, window_min)
    peak_baselines.append({
        "peak_time": x[idx],
        "peak_height": smoothed_signal[idx],
        "baseline": baseline
    })

# Plot the results
plt.figure(figsize=(12, 6))
plt.plot(x, smoothed_signal, label="Smoothed Signal", zorder=1)
for pb in peak_baselines:
    plt.axvline(pb["peak_time"], color='red', linestyle='--', zorder=2)
    plt.hlines(
        pb["baseline"],
        pb["peak_time"] - window_min / 2,
        pb["peak_time"] + window_min / 2,
        color='green',
        linestyle='--',
        label="Baseline" if pb == peak_baselines[0] else None,
        zorder=2
    )

plt.title("Dynamic Local Baselines Using Top 10 Min Values per Peak")
plt.xlabel("Time (min)")
plt.ylabel("Signal")
plt.legend()
plt.tight_layout()
plt.show()
