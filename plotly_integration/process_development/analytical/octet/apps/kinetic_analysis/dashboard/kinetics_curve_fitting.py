"""
Kinetic Curve Fitting Models for Octet Data

Implements common kinetic binding models:
- 1:1 Langmuir (simple binding)
- 2-state heterogeneous
- Bivalent analyte
- Mass transport limited

Author: DataAlchemy
"""

import numpy as np
from scipy.optimize import curve_fit, differential_evolution
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


# ============================================
# 1:1 LANGMUIR MODEL (Most Common)
# ============================================

def langmuir_association(t, kon, koff, rmax, conc_M):
    """
    1:1 Langmuir association model

    R(t) = Rmax * (1 - exp(-kobs * t))
    where kobs = kon * [Analyte] + koff

    Parameters:
    -----------
    t : array
        Time points (seconds)
    kon : float
        Association rate constant (1/Ms)
    koff : float
        Dissociation rate constant (1/s)
    rmax : float
        Maximum response (nm)
    conc_M : float
        Analyte concentration (M)

    Returns:
    --------
    R : array
        Response at each time point
    """
    kobs = kon * conc_M + koff
    return rmax * (1 - np.exp(-kobs * t))


def langmuir_dissociation(t, koff, r0):
    """
    1:1 Langmuir dissociation model

    R(t) = R0 * exp(-koff * t)

    Parameters:
    -----------
    t : array
        Time points (seconds)
    koff : float
        Dissociation rate constant (1/s)
    r0 : float
        Initial response at dissociation start (nm)

    Returns:
    --------
    R : array
        Response at each time point
    """
    return r0 * np.exp(-koff * t)


# ============================================
# 2-STATE HETEROGENEOUS MODEL
# ============================================

def two_state_association(t, kon1, koff1, rmax1, kon2, koff2, rmax2, conc_M):
    """
    2-state heterogeneous association
    Two independent binding sites/populations

    R(t) = Rmax1 * (1 - exp(-kobs1*t)) + Rmax2 * (1 - exp(-kobs2*t))
    """
    kobs1 = kon1 * conc_M + koff1
    kobs2 = kon2 * conc_M + koff2
    return rmax1 * (1 - np.exp(-kobs1 * t)) + rmax2 * (1 - np.exp(-kobs2 * t))


def two_state_dissociation(t, koff1, r01, koff2, r02):
    """
    2-state heterogeneous dissociation

    R(t) = R01 * exp(-koff1*t) + R02 * exp(-koff2*t)
    """
    return r01 * np.exp(-koff1 * t) + r02 * np.exp(-koff2 * t)


# ============================================
# MASS TRANSPORT LIMITED MODEL
# ============================================

def mass_transport_association(t, kon, koff, kt, rmax, conc_M):
    """
    Mass transport limited association

    Includes mass transport coefficient kt
    kobs = kon * [Analyte] + koff + kt
    """
    kobs = kon * conc_M + koff + kt
    return rmax * (1 - np.exp(-kobs * t))


# ============================================
# FIT QUALITY METRICS
# ============================================

def calculate_fit_quality(y_data, y_fit):
    """
    Calculate goodness of fit metrics

    Returns:
    --------
    dict with:
        - r_squared: R² coefficient of determination
        - rmse: Root mean square error
        - chi_squared: Chi-squared
    """
    # Residuals
    residuals = y_data - y_fit
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y_data - np.mean(y_data))**2)

    # R-squared
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

    # RMSE
    rmse = np.sqrt(np.mean(residuals**2))

    # Chi-squared
    chi_squared = ss_res / len(y_data) if len(y_data) > 0 else 0

    return {
        'r_squared': r_squared,
        'rmse': rmse,
        'chi_squared': chi_squared,
        'residuals': residuals
    }


# ============================================
# GLOBAL FITTING FUNCTIONS
# ============================================

def fit_1_1_langmuir_global(
    concentration_data: Dict[float, Dict],
    step_info: Dict = None,
    initial_guess: Optional[Dict] = None
) -> Dict:
    """
    Global fit of 1:1 Langmuir model across all concentrations

    CORRECT APPROACH:
    1. Fit DISSOCIATION phase first (all curves together) → get k_off
    2. Fit ASSOCIATION phase (all curves together) with fixed k_off → get k_on, R_max per concentration
    3. Calculate K_D = k_off / k_on

    Parameters:
    -----------
    concentration_data : dict
        {conc_nM: {'time': array, 'response': array}}
    step_info : dict, optional
        Step timing information (association_start, dissociation_start, etc.)
    initial_guess : dict, optional
        {'kon': 1e5, 'koff': 1e-3, 'rmax': 1.0}

    Returns:
    --------
    dict with fitted parameters and quality metrics
    """

    if initial_guess is None:
        initial_guess = {
            'kon': 1e5,      # 1/Ms
            'koff': 1e-3,    # 1/s
            'rmax': 1.0      # nm (will be scaled per concentration)
        }

    # Prepare data - separate association from dissociation using step_info
    # IMPORTANT: Data coming in should already be processed (baseline aligned, ref subtracted, smoothed)
    # and time should be normalized so association starts at 0
    assoc_data = []
    dissoc_data = []

    logger.info(f"Starting curve fitting for {len(concentration_data)} concentrations")

    for conc_nM, data in concentration_data.items():
        if conc_nM == 0.0:
            continue  # Skip reference

        time = np.array(data['time'])
        response = np.array(data['response'])

        logger.info(f"Concentration {conc_nM} nM: time range [{time.min():.1f}, {time.max():.1f}] s, {len(time)} points")

        # Use step_info to properly split association and dissociation
        # Time is already normalized so association starts at 0
        if step_info:
            assoc_start = step_info.get('association_start', 0)  # Should be 0
            assoc_end = step_info.get('association_end', 300)
            dissoc_start = step_info.get('dissociation_start', 300)
            dissoc_end = step_info.get('dissociation_end', 600)

            logger.info(f"  Step info: assoc=[{assoc_start:.1f}, {assoc_end:.1f}], dissoc=[{dissoc_start:.1f}, {dissoc_end:.1f}]")

            # Extract association phase (should start at t=0)
            assoc_mask = (time >= assoc_start) & (time <= assoc_end)
            assoc_time = time[assoc_mask]
            assoc_response = response[assoc_mask]

            logger.info(f"  Association: {len(assoc_time)} points from t={assoc_time[0]:.1f} to {assoc_time[-1]:.1f}s")

            # Extract dissociation phase
            dissoc_mask = (time >= dissoc_start) & (time <= dissoc_end)
            dissoc_time = time[dissoc_mask]
            dissoc_response = response[dissoc_mask]

            logger.info(f"  Dissociation: {len(dissoc_time)} points from t={dissoc_time[0]:.1f} to {dissoc_time[-1]:.1f}s")
        else:
            # Fallback: split based on response max
            logger.warning(f"  No step_info provided! Using fallback (response max)")
            max_idx = np.argmax(response)
            assoc_time = time[:max_idx+1]
            assoc_response = response[:max_idx+1]
            dissoc_time = time[max_idx:]
            dissoc_response = response[max_idx:]

        if len(assoc_time) > 5:
            # Association time should already start at 0, but normalize just in case
            assoc_time_norm = assoc_time - assoc_time[0]
            assoc_data.append({
                'conc_M': conc_nM * 1e-9,  # Convert nM to M
                'conc_nM': conc_nM,
                'time': assoc_time_norm,
                'response': assoc_response,
                'rmax_est': np.max(assoc_response),
                'time_original': assoc_time  # Keep original for plotting
            })
            logger.info(f"  ✓ Association data prepared: t=[0, {assoc_time_norm[-1]:.1f}], R=[{assoc_response.min():.2f}, {assoc_response.max():.2f}]")
        else:
            logger.warning(f"  ✗ Skipping association: only {len(assoc_time)} points")

        if len(dissoc_time) > 5:
            # Normalize dissociation time to start at 0
            dissoc_time_norm = dissoc_time - dissoc_time[0]
            dissoc_data.append({
                'conc_nM': conc_nM,
                'time': dissoc_time_norm,
                'response': dissoc_response,
                'r0': dissoc_response[0],
                'time_original': dissoc_time  # Keep original for plotting
            })
            logger.info(f"  ✓ Dissociation data prepared: t=[0, {dissoc_time_norm[-1]:.1f}], R0={dissoc_response[0]:.2f}")
        else:
            logger.warning(f"  ✗ Skipping dissociation: only {len(dissoc_time)} points")

    if not assoc_data or not dissoc_data:
        return {'success': False, 'error': 'Insufficient data for fitting'}

    # ========================================
    # FIT DISSOCIATION FIRST (simpler)
    # ========================================

    logger.info(f"\n{'='*60}")
    logger.info(f"STEP 1: Fitting DISSOCIATION phase")
    logger.info(f"{'='*60}")

    # Combine all dissociation curves
    all_dissoc_time = []
    all_dissoc_response = []
    dissoc_r0_values = []

    for dd in dissoc_data:
        all_dissoc_time.extend(dd['time'])
        all_dissoc_response.extend(dd['response'])
        dissoc_r0_values.append(dd['r0'])

    all_dissoc_time = np.array(all_dissoc_time)
    all_dissoc_response = np.array(all_dissoc_response)
    avg_r0 = np.mean(dissoc_r0_values)

    logger.info(f"Dissociation data: {len(dissoc_data)} curves, {len(all_dissoc_time)} total points")
    logger.info(f"Time range: [0, {all_dissoc_time.max():.1f}] s")
    logger.info(f"Response range: [{all_dissoc_response.min():.2f}, {all_dissoc_response.max():.2f}] nm")
    logger.info(f"Average R0: {avg_r0:.2f} nm")

    try:
        # Fit dissociation to get koff
        popt_dissoc, _ = curve_fit(
            lambda t, koff: langmuir_dissociation(t, koff, avg_r0),
            all_dissoc_time,
            all_dissoc_response,
            p0=[initial_guess['koff']],
            bounds=([1e-6], [1.0]),  # koff bounds
            maxfev=10000
        )

        fitted_koff = popt_dissoc[0]
        logger.info(f"✓ Dissociation fit SUCCESS: k_off = {fitted_koff:.4e} /s")

    except Exception as e:
        logger.error(f"✗ Dissociation fit FAILED: {e}")
        return {'success': False, 'error': f'Dissociation fit failed: {str(e)}'}

    # ========================================
    # FIT ASSOCIATION (using fitted koff)
    # ========================================

    logger.info(f"\n{'='*60}")
    logger.info(f"STEP 2: Fitting ASSOCIATION phase (k_off fixed = {fitted_koff:.4e})")
    logger.info(f"{'='*60}")

    # Global fit approach: fit kon globally, rmax per concentration
    # We'll use a combined objective function

    def global_assoc_objective(params):
        """
        Objective function for global association fitting
        params = [kon, rmax1, rmax2, ..., rmaxN]
        """
        kon = params[0]
        rmax_values = params[1:]

        total_error = 0

        for i, ad in enumerate(assoc_data):
            rmax = rmax_values[i]
            y_pred = langmuir_association(
                ad['time'],
                kon,
                fitted_koff,
                rmax,
                ad['conc_M']
            )
            residuals = ad['response'] - y_pred
            total_error += np.sum(residuals**2)

        return total_error

    # Initial guess for global fit
    n_concentrations = len(assoc_data)
    initial_params = [initial_guess['kon']] + [ad['rmax_est'] for ad in assoc_data]

    # Bounds: kon in [1e3, 1e7], rmax in [0, 10*max_response]
    max_response = max([ad['rmax_est'] for ad in assoc_data])
    bounds = [(1e3, 1e7)] + [(0, 10*max_response)] * n_concentrations

    logger.info(f"Association data: {n_concentrations} curves")
    logger.info(f"Initial k_on guess: {initial_guess['kon']:.2e} /Ms")
    logger.info(f"k_on bounds: [1e3, 1e7] /Ms")
    logger.info(f"R_max bounds: [0, {10*max_response:.2f}] nm")

    for i, ad in enumerate(assoc_data):
        logger.info(f"  Curve {i+1}: {ad['conc_nM']:.1f} nM, {len(ad['time'])} points, R_max_est={ad['rmax_est']:.2f} nm")

    try:
        # Use differential evolution for robust global optimization
        logger.info("Starting differential evolution optimization...")
        result = differential_evolution(
            global_assoc_objective,
            bounds,
            maxiter=1000,
            seed=42,
            workers=1
        )

        fitted_kon = result.x[0]
        fitted_rmax_values = result.x[1:]

        logger.info(f"✓ Association fit SUCCESS:")
        logger.info(f"  k_on = {fitted_kon:.4e} /Ms")
        logger.info(f"  Fitted R_max values:")
        for i, (ad, rmax) in enumerate(zip(assoc_data, fitted_rmax_values)):
            logger.info(f"    {ad['conc_nM']:.1f} nM: R_max = {rmax:.2f} nm (est: {ad['rmax_est']:.2f} nm)")

    except Exception as e:
        logger.error(f"✗ Association fit FAILED: {e}")
        return {'success': False, 'error': f'Association fit failed: {str(e)}'}

    # ========================================
    # CALCULATE FITTED CURVES AND QUALITY
    # ========================================

    # Calculate KD
    fitted_kd = fitted_koff / fitted_kon  # in M

    logger.info(f"\n{'='*60}")
    logger.info(f"FINAL RESULTS:")
    logger.info(f"{'='*60}")
    logger.info(f"k_on  = {fitted_kon:.4e} /Ms")
    logger.info(f"k_off = {fitted_koff:.4e} /s")
    logger.info(f"K_D   = {fitted_kd:.4e} M ({fitted_kd*1e9:.2f} nM)")
    logger.info(f"{'='*60}\n")

    # Generate fitted curves for each concentration
    # IMPORTANT: Return association and dissociation fits SEPARATELY
    fitted_curves = {}
    fit_quality = {}

    for i, (conc_nM, data) in enumerate(concentration_data.items()):
        if conc_nM == 0.0:
            continue

        conc_M = conc_nM * 1e-9
        time = np.array(data['time'])
        response = np.array(data['response'])

        # Use step_info to properly split association and dissociation
        if step_info:
            assoc_start = step_info.get('association_start', 0)
            assoc_end = step_info.get('association_end', 300)
            dissoc_start = step_info.get('dissociation_start', 300)
            dissoc_end = step_info.get('dissociation_end', 600)

            # Extract association phase
            assoc_mask = (time >= assoc_start) & (time <= assoc_end)
            assoc_time = time[assoc_mask]
            assoc_response = response[assoc_mask]

            # Extract dissociation phase
            dissoc_mask = (time >= dissoc_start) & (time <= dissoc_end)
            dissoc_time = time[dissoc_mask]
            dissoc_response = response[dissoc_mask]
        else:
            # Fallback: split based on response max
            max_idx = np.argmax(response)
            assoc_time = time[:max_idx+1]
            assoc_response = response[:max_idx+1]
            dissoc_time = time[max_idx:]
            dissoc_response = response[max_idx:]

        # Get rmax for this concentration
        conc_idx = next((j for j, ad in enumerate(assoc_data) if abs(ad['conc_M'] - conc_M) < 1e-12), None)
        if conc_idx is not None:
            rmax = fitted_rmax_values[conc_idx]
        else:
            rmax = np.max(assoc_response)

        # Generate ASSOCIATION fit (normalized time starting at 0)
        assoc_time_norm = assoc_time - assoc_time[0]
        assoc_fit = langmuir_association(
            assoc_time_norm,
            fitted_kon,
            fitted_koff,
            rmax,
            conc_M
        )

        # Generate DISSOCIATION fit (normalized time starting at 0)
        dissoc_time_norm = dissoc_time - dissoc_time[0]
        r0 = dissoc_response[0] if len(dissoc_response) > 0 else 0
        dissoc_fit = langmuir_dissociation(
            dissoc_time_norm,
            fitted_koff,
            r0
        )

        # Store SEPARATE fitted curves (not combined!)
        fitted_curves[conc_nM] = {
            'association': {
                'time': assoc_time.tolist(),  # Use original time (not normalized)
                'response': assoc_fit.tolist()
            },
            'dissociation': {
                'time': dissoc_time.tolist(),  # Use original time (not normalized)
                'response': dissoc_fit.tolist()
            }
        }

        # Quality metrics
        assoc_quality = calculate_fit_quality(assoc_response, assoc_fit)
        dissoc_quality = calculate_fit_quality(dissoc_response, dissoc_fit)

        fit_quality[conc_nM] = {
            'assoc_r_squared': assoc_quality['r_squared'],
            'assoc_rmse': assoc_quality['rmse'],
            'dissoc_r_squared': dissoc_quality['r_squared'],
            'dissoc_rmse': dissoc_quality['rmse'],
            'residuals': {
                'association': {
                    'time': assoc_time.tolist(),
                    'residual': assoc_quality['residuals'].tolist()
                },
                'dissociation': {
                    'time': dissoc_time.tolist(),
                    'residual': dissoc_quality['residuals'].tolist()
                }
            }
        }

    return {
        'success': True,
        'model': '1:1_langmuir',
        'fitted_kon': fitted_kon,
        'fitted_koff': fitted_koff,
        'fitted_kd': fitted_kd,
        'fitted_rmax_values': {
            conc_nM: fitted_rmax_values[i]
            for i, conc_nM in enumerate([ad['conc_M']*1e9 for ad in assoc_data])
        },
        'fitted_curves': fitted_curves,
        'fit_quality': fit_quality
    }


def fit_dissociation_only(dissociation_data: Dict) -> Dict:
    """
    Fit only the dissociation phase to extract koff

    Useful for quick koff estimation

    Parameters:
    -----------
    dissociation_data : dict
        {'time': array, 'response': array}

    Returns:
    --------
    dict with fitted koff and quality metrics
    """
    time = np.array(dissociation_data['time'])
    response = np.array(dissociation_data['response'])

    # Normalize time to start at 0
    time_norm = time - time[0]
    r0 = response[0]

    try:
        popt, pcov = curve_fit(
            lambda t, koff: langmuir_dissociation(t, koff, r0),
            time_norm,
            response,
            p0=[1e-3],
            bounds=([1e-6], [1.0]),
            maxfev=10000
        )

        fitted_koff = popt[0]
        koff_error = np.sqrt(np.diag(pcov))[0]

        # Generate fitted curve
        fitted_response = langmuir_dissociation(time_norm, fitted_koff, r0)

        # Quality metrics
        quality = calculate_fit_quality(response, fitted_response)

        return {
            'success': True,
            'fitted_koff': fitted_koff,
            'koff_error': koff_error,
            'fitted_r0': r0,
            'fitted_curve': {
                'time': time.tolist(),
                'response': fitted_response.tolist()
            },
            'r_squared': quality['r_squared'],
            'rmse': quality['rmse'],
            'residuals': {
                'time': time.tolist(),
                'residual': quality['residuals'].tolist()
            }
        }

    except Exception as e:
        logger.error(f"Dissociation fit failed: {e}")
        return {'success': False, 'error': str(e)}
