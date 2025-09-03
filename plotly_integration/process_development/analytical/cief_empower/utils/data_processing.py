import numpy as np
import pandas as pd
from scipy.signal import find_peaks, savgol_filter, peak_widths
from scipy.integrate import simpson
from scipy.optimize import curve_fit

def process_cief_data(time, signal, smoothing_window=5, baseline_correction=True):
    """
    Process cIEF data with smoothing and baseline correction
    
    Parameters:
    -----------
    time : array-like
        Time values in minutes
    signal : array-like
        Absorbance values
    smoothing_window : int
        Window size for Savitzky-Golay filter
    baseline_correction : bool
        Whether to apply baseline correction
    
    Returns:
    --------
    dict
        Processed data with time, original signal, smoothed signal, and baseline
    """
    
    time = np.array(time)
    signal = np.array(signal)
    
    # Apply smoothing
    if smoothing_window > 0:
        if smoothing_window % 2 == 0:
            smoothing_window += 1
        if len(signal) > smoothing_window:
            smoothed = savgol_filter(signal, smoothing_window, 3)
        else:
            smoothed = signal.copy()
    else:
        smoothed = signal.copy()
    
    # Apply baseline correction
    baseline = np.zeros_like(signal)
    if baseline_correction:
        baseline = calculate_baseline(time, smoothed)
        corrected = smoothed - baseline
    else:
        corrected = smoothed
    
    return {
        'time': time,
        'original': signal,
        'smoothed': smoothed,
        'baseline': baseline,
        'corrected': corrected
    }

def calculate_baseline(time, signal, method='asls'):
    """
    Calculate baseline using Asymmetric Least Squares Smoothing
    
    Parameters:
    -----------
    time : array-like
        Time values
    signal : array-like
        Signal values
    method : str
        Baseline calculation method ('asls', 'linear', 'polynomial')
    
    Returns:
    --------
    array
        Baseline values
    """
    
    if method == 'linear':
        # Simple linear baseline
        baseline = np.linspace(signal[0], signal[-1], len(signal))
    
    elif method == 'polynomial':
        # Polynomial baseline through valleys
        valleys = []
        for i in range(1, len(signal) - 1):
            if signal[i] < signal[i-1] and signal[i] < signal[i+1]:
                valleys.append(i)
        
        if len(valleys) > 2:
            poly_coeffs = np.polyfit(time[valleys], signal[valleys], 2)
            baseline = np.polyval(poly_coeffs, time)
        else:
            baseline = np.linspace(signal[0], signal[-1], len(signal))
    
    elif method == 'asls':
        # Asymmetric Least Squares Smoothing
        baseline = asls_baseline(signal)
    
    else:
        baseline = np.zeros_like(signal)
    
    return baseline

def asls_baseline(y, lam=1e6, p=0.01, niter=10):
    """
    Asymmetric Least Squares Smoothing baseline correction
    
    Parameters:
    -----------
    y : array-like
        Signal values
    lam : float
        Smoothness parameter
    p : float
        Asymmetry parameter
    niter : int
        Number of iterations
    
    Returns:
    --------
    array
        Baseline values
    """
    from scipy import sparse
    from scipy.sparse.linalg import spsolve
    
    L = len(y)
    D = sparse.diags([1, -2, 1], [0, -1, -2], shape=(L, L-2))
    w = np.ones(L)
    
    for i in range(niter):
        W = sparse.spdiags(w, 0, L, L)
        Z = W + lam * D.dot(D.transpose())
        z = spsolve(Z, w * y)
        w = p * (y > z) + (1 - p) * (y < z)
    
    return z

def detect_cief_peaks(time, signal, min_height=0.01, min_prominence=0.005, min_distance=10):
    """
    Detect peaks in cIEF data with specific parameters
    
    Parameters:
    -----------
    time : array-like
        Time values in minutes
    signal : array-like
        Signal values (absorbance)
    min_height : float
        Minimum peak height
    min_prominence : float
        Minimum peak prominence
    min_distance : int
        Minimum distance between peaks (in data points)
    
    Returns:
    --------
    list
        List of peak dictionaries with properties
    """
    
    # Find peaks
    peaks, properties = find_peaks(
        signal,
        height=min_height,
        prominence=min_prominence,
        distance=min_distance
    )
    
    if len(peaks) == 0:
        return []
    
    # Calculate peak widths
    widths, width_heights, left_ips, right_ips = peak_widths(
        signal, peaks, rel_height=0.5
    )
    
    # Calculate areas
    peak_list = []
    for i, peak_idx in enumerate(peaks):
        # Find integration bounds
        left_idx = int(left_ips[i])
        right_idx = int(right_ips[i]) + 1
        
        # Ensure bounds are within array
        left_idx = max(0, left_idx)
        right_idx = min(len(signal), right_idx)
        
        # Calculate area using Simpson's rule
        peak_time = time[left_idx:right_idx]
        peak_signal = signal[left_idx:right_idx]
        
        if len(peak_time) > 1:
            area = simpson(peak_signal, x=peak_time)
        else:
            area = 0
        
        peak_list.append({
            'index': peak_idx,
            'time': time[peak_idx],
            'height': signal[peak_idx],
            'width': widths[i] * (time[1] - time[0]),  # Convert to time units
            'area': area,
            'prominence': properties['prominences'][i],
            'left_base': left_idx,
            'right_base': right_idx
        })
    
    return peak_list

def calculate_peak_resolution(peak1, peak2, time, signal):
    """
    Calculate resolution between two peaks
    
    Parameters:
    -----------
    peak1, peak2 : dict
        Peak dictionaries from detect_cief_peaks
    time : array-like
        Time values
    signal : array-like
        Signal values
    
    Returns:
    --------
    float
        Resolution value
    """
    
    t1 = peak1['time']
    t2 = peak2['time']
    w1 = peak1['width']
    w2 = peak2['width']
    
    # Resolution = 2 * (t2 - t1) / (w1 + w2)
    if w1 + w2 > 0:
        resolution = 2 * abs(t2 - t1) / (w1 + w2)
    else:
        resolution = 0
    
    return resolution

def fit_gaussian_to_peak(time, signal, peak_idx, window=20):
    """
    Fit a Gaussian function to a peak
    
    Parameters:
    -----------
    time : array-like
        Time values
    signal : array-like
        Signal values
    peak_idx : int
        Index of peak maximum
    window : int
        Number of points on each side of peak to include
    
    Returns:
    --------
    dict
        Gaussian parameters (amplitude, center, sigma)
    """
    
    # Extract peak region
    left = max(0, peak_idx - window)
    right = min(len(signal), peak_idx + window + 1)
    
    peak_time = time[left:right]
    peak_signal = signal[left:right]
    
    # Gaussian function
    def gaussian(x, amp, cen, wid):
        return amp * np.exp(-(x - cen)**2 / (2 * wid**2))
    
    # Initial guess
    p0 = [signal[peak_idx], time[peak_idx], 0.1]
    
    try:
        popt, pcov = curve_fit(gaussian, peak_time, peak_signal, p0=p0)
        
        return {
            'amplitude': popt[0],
            'center': popt[1],
            'sigma': abs(popt[2]),
            'fwhm': 2.355 * abs(popt[2]),  # Full width at half maximum
            'fit_success': True
        }
    except:
        return {
            'amplitude': signal[peak_idx],
            'center': time[peak_idx],
            'sigma': 0.1,
            'fwhm': 0.235,
            'fit_success': False
        }