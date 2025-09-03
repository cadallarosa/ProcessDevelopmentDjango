"""
Test the simple DASGIP parser
"""

from dasgip_simple_parser_v3 import DasgipSimpleParserV3 as DasgipSimpleParser

def test_simple_parser():
    # Test all three files
    files = [
        r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\cell_culture\dasgip\raw_data\CTPCNK808814.E59BRX.Control.csv",
        r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\cell_culture\dasgip\raw_data\CTPCNK808814.E59BRX.Control2.csv",
        r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\cell_culture\dasgip\raw_data\CTPCNK808814.manager 419daf2c.Control.csv"
    ]
    
    print("Testing Simple DASGIP Parser on Multiple Files")
    print("=" * 60)
    
    for i, file_path in enumerate(files):
        print(f"\n{i+1}. Testing: {file_path.split('\\')[-1]}")
        print("-" * 40)
        
        parser = DasgipSimpleParser(file_path)
        success = parser.parse()
        
        print(f"Parse success: {success}")
        
        if success:
            # Experiment info
            exp_info = parser.get_experiment_info()
            print(f"Experiment: {exp_info['project_name']}")
            print(f"Host: {exp_info['host']}")
            print(f"Units: {exp_info['units_count']}")
            
            # Units
            units = parser.get_units_info()
            print(f"Detected Units: {[u['unit_number'] for u in units]}")
            
            # Show parameters for first unit
            if units:
                unit_no = units[0]['unit_number']
                tracks = parser.get_unit_tracks(unit_no)
                print(f"Parameters for Unit {unit_no}: {[t['parameter_name'] for t in tracks]}")
        else:
            print("Failed to parse file")

if __name__ == "__main__":
    test_simple_parser()