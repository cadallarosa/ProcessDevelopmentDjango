"""
Analyze the Result ID mismatch issue
"""
import csv
import re
from pathlib import Path

def extract_result_ids_from_file(file_path):
    """Extract result IDs from both filename and file content"""
    filename = file_path.name

    # Extract from filename (e.g., CAD_export_report93265.ars -> 93265)
    filename_match = re.search(r'(\d+)\.ars$', filename)
    filename_result_id = int(filename_match.group(1)) if filename_match else None

    # Extract from file content
    with open(file_path) as f:
        reader = csv.reader(f, delimiter='\t')
        data = [row for row in reader]

    content_result_ids = []
    for row in data:
        if len(row) > 0 and "Result Id:" in row[0]:
            result_id_str = row[0].replace("Result Id:", "").strip()
            content_result_ids = [int(x.strip()) for x in result_id_str.split(",")]
            break

    # Current logic (takes last one)
    current_logic_id = content_result_ids[-1] if content_result_ids else None

    return {
        'filename': filename,
        'filename_id': filename_result_id,
        'content_ids': content_result_ids,
        'current_logic_id': current_logic_id,
        'mismatch': filename_result_id != current_logic_id if filename_result_id else False
    }

# Check error files
error_dir = Path(r"S:\Shared\DjangoRawData\Empower\Error Files")
ars_files = list(error_dir.glob("*.ars"))[:20]

print("Analyzing Result ID mismatches...\n")
print(f"{'Filename':<40} {'Filename ID':<12} {'Content IDs':<25} {'Current Logic':<15} {'Mismatch'}")
print("="*120)

mismatch_count = 0
match_count = 0

for file_path in ars_files:
    info = extract_result_ids_from_file(file_path)

    status = "MISMATCH" if info['mismatch'] else "OK"
    if info['mismatch']:
        mismatch_count += 1
    else:
        match_count += 1

    content_ids_str = str(info['content_ids'])
    print(f"{info['filename']:<40} {info['filename_id']:<12} {content_ids_str:<25} {info['current_logic_id']:<15} {status}")

print("\n" + "="*120)
print(f"Files with mismatch: {mismatch_count}")
print(f"Files matching: {match_count}")
print(f"\nConclusion: The code should use the Result ID from the FILENAME, not the last ID in the content!")
