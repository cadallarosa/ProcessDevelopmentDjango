"""
Data Access Layer for CE-SDS Analysis App
Handles all database queries and data retrieval operations.
"""

import pandas as pd
from plotly_integration.models import (
    CESDSReport, LimsSampleAnalysis, LimsCeSdsResult,
    SampleMetadata, TimeSeriesData, PeakResults
)


def get_metadata_from_source(result_ids):
    """Get metadata from SampleMetadata using result IDs"""
    if not result_ids:
        return {}
    
    try:
        metadata_objects = SampleMetadata.objects.filter(id__in=result_ids)
        return {obj.id: {
            "sample_id": obj.sample_id,
            "data": None  # Will be populated by get_timeseries_data
        } for obj in metadata_objects}
    except Exception as e:
        print(f"Error getting metadata: {e}")
        return {}


def get_timeseries_data(result_id):
    """Get time series data for a specific result ID"""
    try:
        timeseries_objects = TimeSeriesData.objects.filter(metadata_id=result_id).order_by('time_min')
        if not timeseries_objects.exists():
            return pd.DataFrame()
        
        data = []
        for ts in timeseries_objects:
            data.append({
                'time_min': ts.time_min,
                'channel_1': ts.channel_1
            })
        
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error getting timeseries data for {result_id}: {e}")
        return pd.DataFrame()


def get_peak_results(result_id, integration_method='manual'):
    """Get peak results for a specific result ID"""
    try:
        peak_objects = PeakResults.objects.filter(
            metadata_id=result_id,
            integration_method=integration_method
        ).order_by('retention_time')
        
        if not peak_objects.exists():
            return []
        
        peaks = []
        for peak in peak_objects:
            peaks.append({
                'retention_time': peak.retention_time,
                'area': peak.area,
                'height': peak.height,
                'percent_area': peak.percent_area,
                'peak_start_time': peak.peak_start_time,
                'peak_end_time': peak.peak_end_time,
                'peak_width': peak.peak_width,
                'theoretical_plates': peak.theoretical_plates,
                'asymmetry_factor': peak.asymmetry_factor,
                'component_name': peak.component_name
            })
        
        return peaks
    except Exception as e:
        print(f"Error getting peak results for {result_id}: {e}")
        return []


def process_empower_peaks(peaks, sample_name, light_chain_time=None):
    """
    Process Empower peak data and classify peaks into categories.
    
    Args:
        peaks: List of peak dictionaries
        sample_name: Name of the sample
        light_chain_time: Optional light chain time for classification
    
    Returns:
        List of tuples (peak_dict, class_label)
    """
    classified_peaks = []
    
    for peak in peaks:
        rt = peak["retention_time"]
        
        # Classification logic based on retention time
        if rt < 8.0:
            class_label = "LMW"
        elif rt < 12.0:
            if light_chain_time and abs(rt - light_chain_time) < 0.5:
                class_label = "Light Chain"
            else:
                class_label = "Light Chain"
        elif rt < 18.0:
            class_label = "Heavy Chain"
        else:
            class_label = "HMW"
        
        # Ensure required fields are present
        peak_dict = {
            "peak_time": rt,
            "area": peak.get("area", 0),
            "height": peak.get("height", 0),
            "percent_area": peak.get("percent_area", 0),
            "start_time": peak.get("peak_start_time", rt - 0.1),
            "end_time": peak.get("peak_end_time", rt + 0.1),
            "baseline": peak.get("baseline", [0])
        }
        
        classified_peaks.append((peak_dict, class_label))
    
    return classified_peaks


def split_result_ids_by_prefix(result_ids):
    """Split result IDs into reduced and non-reduced based on sample naming"""
    if not result_ids:
        return [], []
    
    try:
        metadata_objects = SampleMetadata.objects.filter(id__in=result_ids)
        reduced_ids = []
        nonreduced_ids = []
        
        for obj in metadata_objects:
            sample_id = obj.sample_id
            if any(keyword in sample_id.upper() for keyword in ["REDUCED", "RED", "DTT"]):
                reduced_ids.append(obj.id)
            elif any(keyword in sample_id.upper() for keyword in ["NONREDUCED", "NR", "NON-REDUCED"]):
                nonreduced_ids.append(obj.id)
            else:
                # Default classification logic could go here
                reduced_ids.append(obj.id)
        
        return reduced_ids, nonreduced_ids
    except Exception as e:
        print(f"Error splitting result IDs: {e}")
        return [], []