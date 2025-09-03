"""
Test the final DASGIP parser
"""

from dasgip_final_parser import DasgipFinalParser

def test_final_parser():
    # Test the parser that should handle multiple data sections
    file_path = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\cell_culture\dasgip\raw_data\CTPCNK808814.E59BRX.Control.csv"
    
    print("Testing Final DASGIP Parser")
    print("=" * 60)
    print(f"File: {file_path.split('\\')[-1]}")
    print("-" * 40)
    
    parser = DasgipFinalParser(file_path)
    success = parser.parse()
    
    print(f"Parse success: {success}")
    
    if success:
        # Experiment info
        exp_info = parser.get_experiment_info()
        print(f"Experiment: {exp_info['project_name']}")
        print(f"Host: {exp_info['host']}")
        print(f"Units count: {exp_info['units_count']}")
        print(f"Tracks count: {exp_info['tracks_count']}")
        
        # Units
        units = parser.get_units_info()
        print(f"Detected Units: {[u['unit_number'] for u in units]}")
        
        # Show parameters for each unit
        for unit in units:
            unit_no = unit['unit_number']
            tracks = parser.get_unit_tracks(unit_no)
            print(f"Unit {unit_no} parameters: {[t['parameter_name'] for t in tracks]}")
            
            # Show sample data
            df = parser.get_sample_data(unit_no, 5)  # Just 5 rows for testing
            if not df.empty:
                print(f"Unit {unit_no} sample data shape: {df.shape}")
                print(f"Unit {unit_no} columns: {list(df.columns)}")
                print(f"Unit {unit_no} first row values: {df.iloc[0].to_dict() if len(df) > 0 else 'No data'}")
            else:
                print(f"Unit {unit_no}: No data found")
            print()
    else:
        print("Failed to parse file")

if __name__ == "__main__":
    test_final_parser()