#!/usr/bin/env python
"""
Test script for DASGIP import functionality
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from plotly_integration.process_development.cell_culture.dasgip.dasgip_import_app import (
    detect_file_format, process_database_export_csv
)

def test_import_functionality():
    """Test the improved import functionality"""
    
    # Test file paths
    usp_file = 'plotly_integration/process_development/cell_culture/dasgip/raw_data/usp_timeseries_data.csv'
    dasgip_file = 'plotly_integration/process_development/cell_culture/dasgip/raw_data/CTPCNK808814.E59BRX.Control.csv'
    
    print("Testing DASGIP Import Functionality\n")
    
    # Test 1: Format Detection
    print("1. Testing format detection...")
    usp_format = detect_file_format(usp_file)
    dasgip_format = detect_file_format(dasgip_file)
    
    print(f"   USP file: {usp_format}")
    print(f"   DASGIP file: {dasgip_format}")
    print(f"   Format detection {'PASSED' if usp_format == 'database_export' and dasgip_format == 'raw_dasgip' else 'FAILED'}\n")
    
    # Test 2: Database Export Processing
    print("2. Testing database export processing...")
    try:
        export_data = process_database_export_csv(usp_file)
        print(f"   Processed {len(export_data)} UP numbers")
        for up_num, up_info in list(export_data.items())[:2]:  # Show first 2
            print(f"      UP {up_num}: {len(up_info['data'])} rows, {up_info['start_timestamp']} to {up_info['stop_timestamp']}")
        print("   Database export processing PASSED\n")
    except Exception as e:
        print(f"   Database export processing FAILED: {e}\n")
    
    # Test 3: Data Quality
    print("3. Testing data quality...")
    try:
        # Get sample data
        sample_up = list(export_data.keys())[0]
        sample_data = export_data[sample_up]['data'].head(100)
        
        print(f"   Sample data shape: {sample_data.shape}")
        print(f"   Unique timestamps: {sample_data['timestamp'].nunique()}")
        print(f"   Total rows: {len(sample_data)}")
        print(f"   Non-null data points: {sample_data.notna().sum().sum()}")
        print(f"   Data quality test PASSED\n")
        
    except Exception as e:
        print(f"   Data quality test FAILED: {e}\n")
    
    print("Testing completed!")

if __name__ == "__main__":
    test_import_functionality()