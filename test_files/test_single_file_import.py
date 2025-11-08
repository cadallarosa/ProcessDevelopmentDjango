"""
Test importing a single error file to see what fails
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

# Now import after Django setup
from plotly_integration.process_development.downstream_processing.empower.database import process_ars

# Test with a file that has multiple result IDs
test_file = r"S:\Shared\DjangoRawData\Empower\Error Files\CAD_export_report93265.ars"

print(f"Testing import of: {test_file}\n")
print("="*80)

try:
    # Extract metadata
    metadata_dict, result_id = process_ars.extract_metadata(test_file)

    print(f"\nExtracted Result ID: {result_id}")
    print(f"Sample Name: {metadata_dict.get('Sample Name')}")
    print(f"System Name: {metadata_dict.get('System Name')}")

    # Try to extract peak results
    print(f"\nExtracting peak results...")
    peak_results_df = process_ars.extract_peak_results(test_file, result_id, metadata_dict['System Name'])

    if peak_results_df is not None:
        print(f"Peak results found: {len(peak_results_df)} rows")
        print(f"\nColumns: {list(peak_results_df.columns)}")
        print(f"\nFirst few rows:")
        print(peak_results_df.head())
    else:
        print("No peak results found")

    print("\n" + "="*80)
    print("SUCCESS: File can be parsed")

except Exception as e:
    print(f"\nERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
