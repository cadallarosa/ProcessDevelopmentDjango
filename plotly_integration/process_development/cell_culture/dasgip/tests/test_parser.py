"""
Test script for DASGIP parser
"""

import sys
import os
import json
from pprint import pprint

# Add project to path
sys.path.append(r'C:\Users\cdallarosa\DataAlchemy\djangoProject')

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
import django
django.setup()

from dasgip_parser_v2 import DasgipParserV2 as DasgipParser

def test_parser():
    """Test the DASGIP parser with the sample file"""
    
    file_path = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\cell_culture\dasgip\raw_data\CTPCNK808814.E59BRX.Control.csv"
    
    print(f"Testing parser with file: {file_path}")
    print("-" * 80)
    
    # Create parser instance
    parser = DasgipParser(file_path)
    
    # Parse the file
    parsed_data = parser.parse()
    
    # Print summary
    print("\n1. FILE INFO:")
    print(f"   Product: {parsed_data['info'].get('product', 'N/A')}")
    print(f"   Version: {parsed_data['info'].get('version', 'N/A')}")
    print(f"   Host: {parsed_data['info'].get('host', 'N/A')}")
    
    print("\n2. EXPERIMENT INFO:")
    exp_info = parser.get_experiment_info()
    print(f"   Project Name: {exp_info['project_name']}")
    print(f"   Start Time: {exp_info['start_timestamp']}")
    print(f"   Stop Time: {exp_info['stop_timestamp']}")
    
    print("\n3. UNITS DETECTED:")
    units_info = parser.get_units_info()
    for unit in units_info:
        print(f"   Unit {unit['unit_number']}: {unit['setup_name']}")
        print(f"      - Tracks: {len(unit['tracks'])}")
        print(f"      - Start: {unit['start_timestamp']}")
        print(f"      - Stop: {unit['stop_timestamp']}")
    
    print("\n4. DATA SUMMARY:")
    print(f"   Data starts at line: {parsed_data.get('data_start_line', 'N/A')}")
    print(f"   Total tracks: {len(parsed_data['track_info'])}")
    
    # Test getting data for a specific unit
    print("\n5. SAMPLE DATA FOR UNIT 1:")
    if units_info:
        unit_1_data = parser.get_unit_data_df(units_info[0]['unit_number'], sample_size=100)
        if not unit_1_data.empty:
            print(f"   Data shape: {unit_1_data.shape}")
            print(f"   Columns: {list(unit_1_data.columns[:10])}...")  # Show first 10 columns
            print(f"   First timestamp: {unit_1_data['timestamp'].min()}")
            print(f"   Last timestamp: {unit_1_data['timestamp'].max()}")
            print("\n   First 5 rows:")
            print(unit_1_data.head())
        else:
            print("   No data found for Unit 1")
    
    print("\n" + "=" * 80)
    print("Parser test completed successfully!")

if __name__ == "__main__":
    test_parser()