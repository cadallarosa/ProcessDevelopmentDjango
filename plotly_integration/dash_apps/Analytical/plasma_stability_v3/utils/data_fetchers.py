"""
Data Fetchers
Optimized database queries for SEC analysis
"""

import pandas as pd
from typing import Optional, Dict, List, Tuple
from plotly_integration.models import SampleMetadata, TimeSeriesData, PeakResults, SystemInformation


def fetch_sample_data(result_id: str) -> Optional[SampleMetadata]:
    """
    Fetch sample metadata for a given result ID

    Args:
        result_id: The result ID to fetch

    Returns:
        SampleMetadata object or None if not found
    """
    try:
        sample = SampleMetadata.objects.filter(result_id=result_id).first()
        if not sample:
            print(f"       ⚠ No sample found for Result ID: {result_id}")
        return sample
    except Exception as e:
        print(f"       ✗ Error fetching sample {result_id}: {e}")
        return None


def fetch_peak_results(result_id: str) -> Optional[pd.DataFrame]:
    """
    Fetch peak results for SEC analysis

    Args:
        result_id: The result ID to fetch peaks for

    Returns:
        DataFrame with peak results or None if not found
    """
    try:
        # Get sample to find system info
        sample = fetch_sample_data(result_id)
        if not sample:
            return None

        system_name = sample.system_name

        # Get channel info
        system = SystemInformation.objects.filter(system_name=system_name).first()
        if not system:
            print(f"       ✗ No system information found for: {system_name}")
            return None

        channel_name = system.channel_1

        # Get peak results
        peak_results = PeakResults.objects.filter(
            result_id=result_id,
            channel_name=channel_name,
            system_name=system_name
        )

        if not peak_results.exists():
            print(f"       ✗ No peak results found for {result_id}")
            return None

        # Convert to DataFrame
        df = pd.DataFrame.from_records(peak_results.values())

        # Clean data
        df['peak_retention_time'] = pd.to_numeric(df['peak_retention_time'], errors='coerce')
        df = df.dropna(subset=['peak_retention_time'])
        df['area'] = df['area'].astype(float)
        df['peak_start_time'] = df['peak_start_time'].astype(float)
        df['peak_end_time'] = df['peak_end_time'].astype(float)

        # Sort by retention time
        df = df.sort_values('peak_retention_time').reset_index(drop=True)

        print(f"       ✓ Found {len(df)} peaks for {result_id}")
        return df

    except Exception as e:
        print(f"       ✗ Error fetching peaks for {result_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def fetch_time_series(result_id: str) -> Optional[Tuple[SampleMetadata, pd.DataFrame]]:
    """
    Fetch time series data for chromatogram plotting

    Args:
        result_id: The result ID to fetch

    Returns:
        Tuple of (SampleMetadata, DataFrame) or (None, None) if not found
    """
    try:
        sample = fetch_sample_data(result_id)
        if not sample:
            return None, None

        # Get time series data using injection_id
        time_series = TimeSeriesData.objects.filter(result_id=sample.injection_id)
        df = pd.DataFrame(list(time_series.values()))

        if df.empty:
            print(f"       ✗ No time series data for injection ID: {sample.injection_id}")
            return None, None

        print(f"       ✓ Time series data found: {len(df)} points")
        return sample, df

    except Exception as e:
        print(f"       ✗ Error fetching time series for {result_id}: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def batch_fetch_samples(result_ids: List[str]) -> Dict[str, Dict]:
    """
    Batch fetch data for multiple result IDs to optimize database queries

    Args:
        result_ids: List of result IDs to fetch

    Returns:
        Dict mapping result_id to {sample, peaks_df, timeseries_df}
    """
    results = {}

    print(f"\n   → Batch fetching data for {len(result_ids)} samples...")

    for result_id in result_ids:
        print(f"   → Processing {result_id}...")

        # Fetch all data for this result
        sample, ts_df = fetch_time_series(result_id)
        peaks_df = fetch_peak_results(result_id)

        if sample and ts_df is not None and peaks_df is not None:
            results[result_id] = {
                'sample': sample,
                'peaks_df': peaks_df,
                'timeseries_df': ts_df,
                'found': True
            }
            print(f"       ✓ Data loaded successfully")
        else:
            results[result_id] = {
                'sample': None,
                'peaks_df': None,
                'timeseries_df': None,
                'found': False
            }
            print(f"       ✗ Could not load complete data")

    found_count = sum(1 for r in results.values() if r['found'])
    print(f"   ✓ Successfully loaded {found_count}/{len(result_ids)} samples\n")

    return results
