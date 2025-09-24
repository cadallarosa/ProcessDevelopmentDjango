# ==================== Helper Functions for Data Fetching ====================
import pandas as pd

from plotly_integration.models import SampleMetadata, TimeSeriesData, PeakResults


def get_metadata_from_source(result_ids):
    """
    Fetch metadata from unified tables

    Args:
        result_ids: List of result IDs to fetch

    Returns:
        List of metadata objects
    """
    # Always use unified tables - filter by analysis_type=3 for CE-SDS
    metas = SampleMetadata.objects.filter(
        result_id__in=result_ids,
        analysis_type=3  # CE-SDS
    )
    # Convert to have consistent attributes for compatibility
    converted_metas = []
    for m in metas:
        # Create a simple object with attributes matching legacy structure
        class MetaObj:
            def __init__(self, unified_meta):
                self.id = unified_meta.result_id  # Use result_id as ID
                self.result_id = unified_meta.result_id
                self.sample_id_full = unified_meta.sample_name
                self.sample_prefix = unified_meta.sample_prefix
                self.sample_name = unified_meta.sample_name
                self.date_acquired = unified_meta.date_acquired
                self.sample_set_name = unified_meta.sample_set_name

        converted_metas.append(MetaObj(m))
    return converted_metas


def get_timeseries_data(result_id):
    """
    Fetch time series data from unified tables

    Args:
        result_id: The result ID

    Returns:
        DataFrame with time_min and channel_1 columns
    """
    # Always use unified tables
    qs = TimeSeriesData.objects.filter(
        result_id=result_id,
        system_name__icontains='CE'  # Filter for CE-SDS data
    ).values('time', 'channel_1')
    df = pd.DataFrame(list(qs))
    if not df.empty:
        # Rename 'time' to 'time_min' for consistency
        df = df.rename(columns={'time': 'time_min'})
        # Scale channel_1 by 1,000,000 to convert from base units to micro units (match peak results)
        df['channel_1'] = df['channel_1'] * 1_000_000
        print(f"[DEBUG] Scaled {len(df)} time series data points by 1M for result_id {result_id}")

    return df


def get_peak_results(result_id):
    """
    Get peak results either from database (Empower) or through manual detection

    Args:
        result_id: The result ID
        integration_method: 'empower' or 'manual'

    Returns:
        List of peak dictionaries with retention_time, area, height, etc.
    """
    # Fetch from PeakResults table
    peaks = PeakResults.objects.filter(
        result_id=result_id,
        system_name__icontains='CE'  # Filter for CE-SDS data
    ).values(
        'peak_name',
        'peak_retention_time',
        'area',
        'percent_area',
        'height',
        'peak_start_time',
        'peak_end_time'
    )
    peak_list = list(peaks)
    print(f"[DEBUG] Found {len(peak_list)} peaks for result_id {result_id}")
    for i, peak in enumerate(peak_list):
        print(
            f"[DEBUG] Peak {i + 1}: RT={peak['peak_retention_time']:.3f}, Area={peak['area']}, %Area={peak['percent_area']:.2f}%")
    return peak_list

