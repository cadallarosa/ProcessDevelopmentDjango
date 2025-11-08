"""
Check if the error files have database conflicts
"""
import os
import sys
import csv

# Add the project root to path
sys.path.insert(0, r'C:\Users\cdallarosa\DataAlchemy\djangoProject')

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from plotly_integration.models import SampleMetadata, PeakResults
from pathlib import Path

def check_file_in_db(file_path):
    """Check if a file's data already exists in the database"""
    with open(file_path) as file_obj:
        reader = csv.reader(file_obj, delimiter='\t')
        data = [row for row in reader]

    # Find Result ID
    result_ids = []
    for row in data:
        if len(row) > 0 and "Result Id:" in row[0]:
            result_id_str = row[0].replace("Result Id:", "").strip()
            result_ids = [int(x.strip()) for x in result_id_str.split(",")]
            break

    if not result_ids:
        return None, "No Result ID found"

    # Check each result ID
    conflicts = []
    for rid in result_ids:
        metadata = SampleMetadata.objects.filter(result_id=rid).first()
        if metadata:
            conflicts.append({
                'result_id': rid,
                'sample_name': metadata.sample_name,
                'system_name': metadata.system_name,
                'date_acquired': metadata.date_acquired
            })

    return result_ids, conflicts

# Check first 10 error files
error_dir = Path(r"S:\Shared\DjangoRawData\Empower\Error Files")
ars_files = list(error_dir.glob("*.ars"))[:10]

print(f"Checking {len(ars_files)} files for database conflicts...\n")

files_with_conflicts = 0
files_without_conflicts = 0

for file_path in ars_files:
    result_ids, conflicts = check_file_in_db(file_path)

    print(f"\n{file_path.name}")
    print(f"  Result IDs: {result_ids}")

    if isinstance(conflicts, str):
        print(f"  Error: {conflicts}")
    elif conflicts:
        files_with_conflicts += 1
        print(f"  CONFLICTS FOUND ({len(conflicts)}):")
        for c in conflicts:
            print(f"    - ID {c['result_id']}: {c['sample_name']} ({c['system_name']}) on {c['date_acquired']}")
    else:
        files_without_conflicts += 1
        print(f"  No conflicts - safe to import")

print(f"\n{'='*80}")
print(f"Summary:")
print(f"  Files with conflicts: {files_with_conflicts}")
print(f"  Files without conflicts: {files_without_conflicts}")
