"""
Test re-importing a file that already exists in the database
"""
import os
import sys

sys.path.insert(0, r'C:\Users\cdallarosa\DataAlchemy\djangoProject')

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from plotly_integration.process_development.downstream_processing.empower.database import process_ars

# Test file that already exists in DB
test_file = r"S:\Shared\DjangoRawData\Empower\Error Files\CAD_export_report93265.ars"

print(f"Attempting to re-import: {test_file}")
print("="*80)

try:
    print("\nStep 1: Extracting metadata...")
    metadata_dict, result_id = process_ars.extract_metadata(test_file)

    if metadata_dict is None:
        print("ERROR: Could not extract metadata")
        sys.exit(1)

    print(f"  Result ID: {result_id}")
    print(f"  Sample Name: {metadata_dict.get('Sample Name')}")

    print("\nStep 2: Normalizing sample names...")
    metadata_dict = process_ars.normalize_sample_names(metadata_dict)

    print("\nStep 3: Inserting metadata (update_or_create)...")
    process_ars.insert_metadata(metadata_dict, use_orm=True)
    print("  SUCCESS: Metadata inserted/updated")

    print("\nStep 4: Extracting peak results...")
    system_name = metadata_dict['System Name']
    peak_results_df = process_ars.extract_peak_results(test_file, result_id, system_name)

    if peak_results_df is not None:
        print(f"  Found {len(peak_results_df)} peak results")

        print("\nStep 5: Inserting peak results (with delete + bulk_create)...")
        process_ars.insert_peak_results(peak_results_df, use_orm=True)
        print("  SUCCESS: Peak results inserted")
    else:
        print("  No peak results to insert")

    print("\n" + "="*80)
    print("RE-IMPORT SUCCESSFUL!")

except Exception as e:
    print(f"\nERROR during import: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
