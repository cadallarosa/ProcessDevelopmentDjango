#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from plotly_integration.models import TimeSeriesData

def check_available_data():
    print("Checking available data in TimeSeriesData...")
    
    # Check unique system names
    systems = TimeSeriesData.objects.values_list('system_name', flat=True).distinct()
    print(f"Available systems: {list(systems)}")
    
    # Check if result_id 23617 exists with any system
    result_data = TimeSeriesData.objects.filter(result_id=23617)
    if result_data.exists():
        print(f"Found result_id 23617 in systems: {list(result_data.values_list('system_name', flat=True).distinct())}")
        print(f"Data count: {result_data.count()}")
    else:
        print("Result_id 23617 not found in any system")
        
        # Check some example result_ids
        print("\nChecking some available result_ids...")
        sample_ids = TimeSeriesData.objects.values_list('result_id', flat=True).distinct().order_by('-result_id')[:10]
        print(f"Latest result_ids: {list(sample_ids)}")

if __name__ == "__main__":
    check_available_data()