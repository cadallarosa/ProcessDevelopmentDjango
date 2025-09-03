"""
Simple debug test for DASGIP import - no emojis
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
from datetime import datetime
import pandas as pd

def test_import():
    file_path = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\cell_culture\dasgip\raw_data\CTPCNK808814.manager 419daf2c.Control.csv"
    
    print("TESTING PARSER...")
    
    # Test parser
    parser = DasgipFinalParser(file_path)
    success = parser.parse()
    print(f"Parser success: {success}")
    
    if not success:
        print("Parser failed!")
        return
    
    # Get info
    exp_info = parser.get_experiment_info()
    units_info = parser.get_units_info()
    
    print(f"Units found: {[u['unit_number'] for u in units_info]}")
    print(f"Experiment: {exp_info}")
    
    print("\nTESTING DATABASE...")
    
    # Test database
    user = User.objects.first()
    if not user:
        print("No user found!")
        return
    
    print(f"User found: {user.username}")
    
    # Clean up test data
    USPBioreactorRun.objects.filter(up_number__startswith="TEST_").delete()
    print("Cleaned up old test data")
    
    print("\nTESTING IMPORT...")
    
    # Test import for first unit only
    if units_info:
        unit_info = units_info[0]  # First unit only
        unit_no = unit_info['unit_number']
        up_number = f"TEST_{unit_no}_{datetime.now().strftime('%H%M%S')}"
        
        print(f"Importing Unit {unit_no} as {up_number}")
        
        try:
            # Create run record
            run = USPBioreactorRun.objects.create(
                up_number=up_number,
                file_name=os.path.basename(file_path),
                file_path=file_path,
                project_name=exp_info.get('project_name', 'Test'),
                unit_number=unit_no,
                setup_name=unit_info.get('setup_name', f'Unit {unit_no}'),
                start_timestamp=datetime.now(),
                stop_timestamp=datetime.now(),
                uploaded_by=user,
                host=exp_info.get('host', 'Unknown')
            )
            print(f"Created run: {run.up_number}")
            
            # Get data
            df = parser.get_sample_data(unit_no, 10)  # Just 10 records
            print(f"Data shape: {df.shape}")
            
            if not df.empty:
                print(f"Columns: {list(df.columns)}")
                
                # Create first time series record manually
                first_row = df.iloc[0]
                ts_record = USPTimeSeriesData.objects.create(
                    run=run,
                    timestamp=first_row['timestamp'],
                    duration=first_row.get('duration'),
                    do_pv=first_row.get('do_pv'),
                    ph_pv=first_row.get('ph_pv'),
                    temp_pv=first_row.get('temp_pv'),
                    volume_pv=first_row.get('volume_pv')
                )
                print(f"Created time series record: {ts_record}")
                
                # Verify it was saved
                count = USPTimeSeriesData.objects.filter(run=run).count()
                print(f"Records in database: {count}")
                
                print("SUCCESS: Import test completed!")
                
        except Exception as e:
            print(f"ERROR during import: {e}")
            import traceback
            traceback.print_exc()
    
    else:
        print("No units found to test!")

if __name__ == "__main__":
    test_import()