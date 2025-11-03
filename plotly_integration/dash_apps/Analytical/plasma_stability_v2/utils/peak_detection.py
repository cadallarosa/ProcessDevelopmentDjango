"""
Peak Detection Algorithms
Implements 3 modes for identifying the main (monomer) peak in SEC data
"""

import pandas as pd
from typing import Optional, Dict


def detect_main_peak(
    peaks_df: pd.DataFrame,
    mode: int,
    reference_rt: Optional[float] = None,
    lmw_cutoff: float = 12.0
) -> Optional[Dict]:
    """
    Detect the main (monomer) peak using one of three modes

    Args:
        peaks_df: DataFrame with peak results (must have peak_retention_time, area columns)
        mode: Detection mode (0=Auto, 1=Manual RT, 2=Highest Peak)
        reference_rt: Reference retention time (used for mode 0 Day 3+ or mode 1)
        lmw_cutoff: Maximum RT for LMW region (default 12 min)

    Returns:
        Dict with main_peak_index and main_peak_rt, or None if failed
    """
    if peaks_df is None or peaks_df.empty:
        print(f"       ✗ No peaks available for detection")
        return None

    try:
        if mode == 0:
            # Auto Peak Detection
            return _auto_peak_detection(peaks_df, reference_rt)

        elif mode == 1:
            # Manual Peak RT
            if reference_rt is None:
                print(f"       ✗ Mode 1 requires reference_rt to be specified")
                return None
            return _manual_rt_detection(peaks_df, reference_rt)

        elif mode == 2:
            # Use Highest Peak
            return _highest_peak_detection(peaks_df)

        else:
            print(f"       ✗ Unknown peak detection mode: {mode}")
            return None

    except Exception as e:
        print(f"       ✗ Error in peak detection: {e}")
        import traceback
        traceback.print_exc()
        return None


def _auto_peak_detection(peaks_df: pd.DataFrame, reference_rt: Optional[float] = None) -> Dict:
    """
    Mode 0: Auto Peak Detection

    If reference_rt provided: Find peak closest to reference RT (for Day 3+)
    If no reference_rt: Find highest peak (for Day 0)

    Args:
        peaks_df: DataFrame with peak results
        reference_rt: Reference RT from Day 0 (None for Day 0 samples)

    Returns:
        Dict with main_peak_index and main_peak_rt
    """
    if reference_rt is None:
        # Day 0: Use highest peak
        main_peak_index = peaks_df['area'].idxmax()
        main_peak_rt = peaks_df.loc[main_peak_index, 'peak_retention_time']
        print(f"       ✓ Auto (Day 0): Highest peak at RT {main_peak_rt:.2f}")
    else:
        # Day 3+: Find closest peak to Day 0 reference
        main_peak_index = (peaks_df['peak_retention_time'] - reference_rt).abs().idxmin()
        main_peak_rt = peaks_df.loc[main_peak_index, 'peak_retention_time']
        print(f"       ✓ Auto (Day 3+): Closest to reference {reference_rt:.2f} → {main_peak_rt:.2f}")

    return {
        'main_peak_index': main_peak_index,
        'main_peak_rt': main_peak_rt
    }


def _manual_rt_detection(peaks_df: pd.DataFrame, target_rt: float) -> Dict:
    """
    Mode 1: Manual Peak RT

    Find peak closest to user-specified retention time

    Args:
        peaks_df: DataFrame with peak results
        target_rt: User-specified target retention time

    Returns:
        Dict with main_peak_index and main_peak_rt
    """
    main_peak_index = (peaks_df['peak_retention_time'] - target_rt).abs().idxmin()
    main_peak_rt = peaks_df.loc[main_peak_index, 'peak_retention_time']
    print(f"       ✓ Manual RT: Specified {target_rt:.2f} → Found {main_peak_rt:.2f}")

    return {
        'main_peak_index': main_peak_index,
        'main_peak_rt': main_peak_rt
    }


def _highest_peak_detection(peaks_df: pd.DataFrame) -> Dict:
    """
    Mode 2: Use Highest Peak

    Always use the peak with the largest area

    Args:
        peaks_df: DataFrame with peak results

    Returns:
        Dict with main_peak_index and main_peak_rt
    """
    main_peak_index = peaks_df['area'].idxmax()
    main_peak_rt = peaks_df.loc[main_peak_index, 'peak_retention_time']
    print(f"       ✓ Highest Peak: RT {main_peak_rt:.2f}")

    return {
        'main_peak_index': main_peak_index,
        'main_peak_rt': main_peak_rt
    }


def calculate_peak_areas(
    peaks_df: pd.DataFrame,
    main_peak_index: int,
    lmw_cutoff: float = 12.0
) -> Dict:
    """
    Calculate monomer, HMW, and LMW percentages

    Args:
        peaks_df: DataFrame with peak results
        main_peak_index: Index of the main (monomer) peak
        lmw_cutoff: Maximum RT for LMW region (default 12 min)

    Returns:
        Dict with percentages and region boundaries
    """
    try:
        main_peak_row = peaks_df.loc[main_peak_index]
        main_peak_rt = main_peak_row['peak_retention_time']
        main_peak_area = float(main_peak_row['area'])
        main_peak_start = float(main_peak_row['peak_start_time'])
        main_peak_end = float(main_peak_row['peak_end_time'])

        # Remove main peak from consideration
        df_excluding_main = peaks_df.drop(index=main_peak_index)

        # HMW: All peaks BEFORE main peak
        hmw_peaks = df_excluding_main[df_excluding_main['peak_retention_time'] < main_peak_rt]
        hmw_area = float(hmw_peaks['area'].sum()) if not hmw_peaks.empty else 0.0

        # LMW: All peaks AFTER main peak (up to cutoff)
        lmw_peaks = df_excluding_main[
            (df_excluding_main['peak_retention_time'] > main_peak_rt) &
            (df_excluding_main['peak_retention_time'] <= lmw_cutoff)
        ]
        lmw_area = float(lmw_peaks['area'].sum()) if not lmw_peaks.empty else 0.0

        # Calculate total and percentages
        total_area = main_peak_area + hmw_area + lmw_area

        if total_area > 0:
            monomer_pct = round((main_peak_area / total_area) * 100, 2)
            hmw_pct = round((hmw_area / total_area) * 100, 2)
            lmw_pct = round((lmw_area / total_area) * 100, 2)
        else:
            monomer_pct = hmw_pct = lmw_pct = 0.0

        # Determine region boundaries for plotting
        hmw_start = peaks_df['peak_start_time'].min() if not df_excluding_main.empty else main_peak_start
        hmw_end = main_peak_start
        lmw_start = main_peak_end
        lmw_end = min(peaks_df['peak_end_time'].max(), lmw_cutoff)

        result = {
            'monomer_pct': monomer_pct,
            'hmw_pct': hmw_pct,
            'lmw_pct': lmw_pct,
            'main_peak_area': round(main_peak_area, 2),
            'hmw_area': round(hmw_area, 2),
            'lmw_area': round(lmw_area, 2),
            'total_area': round(total_area, 2),
            'main_rt': round(main_peak_rt, 3),
            'main_start': round(main_peak_start, 3),
            'main_end': round(main_peak_end, 3),
            'hmw_start': round(hmw_start, 3),
            'hmw_end': round(hmw_end, 3),
            'lmw_start': round(lmw_start, 3),
            'lmw_end': round(lmw_end, 3),
        }

        print(f"       ✓ Calculated: Monomer {monomer_pct}%, HMW {hmw_pct}%, LMW {lmw_pct}%")

        return result

    except Exception as e:
        print(f"       ✗ Error calculating peak areas: {e}")
        import traceback
        traceback.print_exc()
        return None
