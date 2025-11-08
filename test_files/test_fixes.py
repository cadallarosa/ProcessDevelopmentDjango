"""
Test the fixes for Result ID extraction and separator row handling
"""
import os
import sys

sys.path.insert(0, r'C:\Users\cdallarosa\DataAlchemy\djangoProject')

# Setup Django before importing
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

# Import the updated functions
from plotly_integration.process_development.downstream_processing.empower.database import process_ars

test_files = [
    (r"S:\Shared\DjangoRawData\Empower\Error Files\CAD_export_report93265.ars", 93265, "Should match"),
    (r"S:\Shared\DjangoRawData\Empower\Error Files\CAD_export_report93270.ars", 93270, "Was mismatch (was using 93272)"),
    (r"S:\Shared\DjangoRawData\Empower\Error Files\CAD_export_report93274.ars", 93274, "Was mismatch (was using 93275)"),
]

print("Testing the fixes...")
print("="*100)

for file_path, expected_id, note in test_files:
    print(f"\nFile: {os.path.basename(file_path)}")
    print(f"Expected Result ID: {expected_id} ({note})")
    print("-"*100)

    try:
        # Test metadata extraction with new logic
        metadata_dict, result_id = process_ars.extract_metadata(file_path)

        if result_id == expected_id:
            print(f"✅ CORRECT: Got Result ID {result_id}")
        else:
            print(f"❌ WRONG: Got Result ID {result_id}, expected {expected_id}")

        # Test peak results extraction with separator row handling
        system_name = metadata_dict.get('System Name')
        peak_results_df = process_ars.extract_peak_results(file_path, result_id, system_name)

        if peak_results_df is not None and len(peak_results_df) > 0:
            print(f"✅ Peak results: {len(peak_results_df)} rows extracted")
        else:
            print(f"⚠️  No peak results extracted")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*100)
print("Testing complete!")
