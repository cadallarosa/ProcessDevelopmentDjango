#!/usr/bin/env python
"""
Script to directly clear USP time series and USP bioreactor run tables
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from plotly_integration.models import USPBioreactorRun, USPTimeSeriesData

def clear_usp_tables_direct():
    """Clear USP time series and bioreactor run tables directly"""
    
    print("Clearing USP tables...")
    
    # Get counts before deletion
    timeseries_count = USPTimeSeriesData.objects.count()
    runs_count = USPBioreactorRun.objects.count()
    
    print(f"Current data:")
    print(f"  - USP Time Series Data: {timeseries_count:,} rows")
    print(f"  - USP Bioreactor Runs: {runs_count:,} rows")
    
    if timeseries_count == 0 and runs_count == 0:
        print("Tables are already empty.")
        return
    
    print(f"\nDeleting ALL {timeseries_count:,} time series records and {runs_count:,} bioreactor runs...")
    
    # Delete time series data first (due to foreign key constraint)
    deleted_timeseries = USPTimeSeriesData.objects.all().delete()
    print(f"Deleted {deleted_timeseries[0]:,} time series records")
    
    # Delete bioreactor runs
    deleted_runs = USPBioreactorRun.objects.all().delete()
    print(f"Deleted {deleted_runs[0]:,} bioreactor run records")
    
    # Verify tables are empty
    final_timeseries_count = USPTimeSeriesData.objects.count()
    final_runs_count = USPBioreactorRun.objects.count()
    
    print(f"\nFinal counts:")
    print(f"  - USP Time Series Data: {final_timeseries_count} rows")
    print(f"  - USP Bioreactor Runs: {final_runs_count} rows")
    
    if final_timeseries_count == 0 and final_runs_count == 0:
        print("Tables cleared successfully!")
    else:
        print("Warning: Some records may not have been deleted.")

if __name__ == "__main__":
    clear_usp_tables_direct()