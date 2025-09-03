"""
Debug the complete import process step by step
"""
import os
import sys
import django

# Setup Django
sys.path.append(r'C:\Users\cdallarosa\DataAlchemy\djangoProject')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from dasgip_final_parser import DasgipFinalParser
from plotly_integration.models import USPBioreactorRun, USPTimeSeriesData, User

def test_complete_import():
    file_path = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\cell_culture\dasgip\raw_data\CTPCNK808814.manager 419daf2c.Control.csv"
    
    print("STEP 1: Testing Parser")
    print("=" * 50)
    
    # Test parser
    parser = DasgipFinalParser(file_path)
    success = parser.parse()
    
    print(f"Parse success: {success}")
    
    if not success:
        print("ERROR: Parser failed!")
        return
    
    # Get experiment info
    exp_info = parser.get_experiment_info()
    print(f"Experiment info: {exp_info}")
    
    # Get units
    units_info = parser.get_units_info()
    print(f"Units detected: {[u['unit_number'] for u in units_info]}")
    
    # Test data for first unit
    if units_info:
        unit_no = units_info[0]['unit_number']
        df = parser.get_sample_data(unit_no, 5)
        print(f"Sample data for Unit {unit_no}:")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        if not df.empty:
            print(f"First row: {df.iloc[0].to_dict()}")
    
    print("\nSTEP 2: Testing Database Connection")
    print("=" * 50)
    
    # Test database connection
    try:
        user = User.objects.first()
        print(f"User found: {user}")
        
        # Test if we can create a test record
        test_up = "TEST_DEBUG_123"
        
        # Clean up any existing test record
        USPBioreactorRun.objects.filter(up_number=test_up).delete()
        
        # Create test record
        from datetime import datetime
        test_run = USPBioreactorRun.objects.create(
            up_number=test_up,
            file_name="test.csv",
            file_path="/test/path",
            project_name="Test Project",
            unit_number=1,
            setup_name="Test Setup",
            start_timestamp=datetime.now(),
            stop_timestamp=datetime.now(),
            uploaded_by=user,
            host="TEST_HOST"
        )
        print(f"✅ Test run created: {test_run}")
        
        # Clean up
        test_run.delete()
        print("✅ Test run deleted successfully")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        print(traceback.format_exc())
        return
    
    print("\n🔍 STEP 3: Testing Import Function")
    print("=" * 50)
    
    # Test the actual import
    try:
        from django.db import transaction
        import pandas as pd
        
        with transaction.atomic():
            print("🔄 Starting test import...")
            
            # Create UP mapping
            up_mapping = {
                1: "TEST_UP_001",
                3: "TEST_UP_003", 
                4: "TEST_UP_004",
                7: "TEST_UP_007",
                8: "TEST_UP_008"
            }
            
            # Clean up any existing test records
            USPBioreactorRun.objects.filter(up_number__startswith="TEST_UP_").delete()
            
            runs_created = 0
            data_points_created = 0
            
            for unit_info in units_info:
                unit_no = unit_info['unit_number']
                up_number = up_mapping.get(unit_no, f"TEST_AUTO_{unit_no}")
                
                print(f"🧪 Processing Unit {unit_no} -> {up_number}")
                
                # Create run record
                run = USPBioreactorRun.objects.create(
                    up_number=up_number,
                    file_name="test_import.csv",
                    file_path=file_path,
                    project_name=exp_info.get('project_name', 'Test'),
                    unit_number=unit_no,
                    setup_name=unit_info.get('setup_name', f'Test Unit {unit_no}'),
                    start_timestamp=unit_info.get('start_timestamp', datetime.now()),
                    stop_timestamp=unit_info.get('stop_timestamp', datetime.now()),
                    uploaded_by=user,
                    host=exp_info.get('host', 'TEST_HOST')
                )
                runs_created += 1
                print(f"✅ Created run: {run}")
                
                # Get time series data
                df = parser.get_sample_data(unit_no, 100)  # Just 100 points for test
                print(f"📊 Data shape: {df.shape}")
                
                if not df.empty:
                    timeseries_data = []
                    for _, row in df.iterrows():
                        if pd.notna(row.get('timestamp')):
                            timeseries_record = USPTimeSeriesData(
                                run=run,
                                timestamp=row['timestamp'],
                                duration=row.get('duration'),
                                do_pv=row.get('do_pv'),
                                do_sp=row.get('do_sp'), 
                                do_out=row.get('do_out'),
                                ph_pv=row.get('ph_pv'),
                                ph_sp=row.get('ph_sp'),
                                ph_out=row.get('ph_out'),
                                temp_pv=row.get('temp_pv'),
                                temp_sp=row.get('temp_sp'),
                                temp_out=row.get('temp_out'),
                                rpm_pv=row.get('rpm_pv'),
                                rpm_sp=row.get('rpm_sp'),
                                volume_pv=row.get('volume_pv'),
                                air_flow_pv=row.get('air_flow_pv'),
                                air_flow_sp=row.get('air_flow_sp'),
                                feed_a_pv=row.get('feed_a_pv'),
                                feed_a_sp=row.get('feed_a_sp'),
                                feed_b_pv=row.get('feed_b_pv'),
                                feed_b_sp=row.get('feed_b_sp'),
                                o2_conc_pv=row.get('o2_conc_pv'),
                                o2_conc_sp=row.get('o2_conc_sp'),
                                co2_conc_pv=row.get('co2_conc_pv'),
                                co2_conc_sp=row.get('co2_conc_sp')
                            )
                            timeseries_data.append(timeseries_record)
                    
                    print(f"💾 Creating {len(timeseries_data)} time series records...")
                    USPTimeSeriesData.objects.bulk_create(timeseries_data)
                    data_points_created += len(timeseries_data)
                    print(f"✅ Created {len(timeseries_data)} records for {up_number}")
            
            print(f"\n🎉 TEST IMPORT COMPLETED!")
            print(f"📋 Results:")
            print(f"  - Runs created: {runs_created}")
            print(f"  - Data points created: {data_points_created}")
            
            # Verify data was actually saved
            saved_runs = USPBioreactorRun.objects.filter(up_number__startswith="TEST_UP_").count()
            saved_data = USPTimeSeriesData.objects.filter(run__up_number__startswith="TEST_UP_").count()
            
            print(f"📊 Verification:")
            print(f"  - Runs in DB: {saved_runs}")
            print(f"  - Data points in DB: {saved_data}")
            
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_complete_import()