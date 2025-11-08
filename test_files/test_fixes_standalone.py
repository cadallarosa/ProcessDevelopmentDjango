"""
Standalone test of the fixes (no Django needed)
"""
import csv
import re
import pandas as pd

def extract_metadata_fixed(file_path):
    """Fixed version that uses filename Result ID"""
    with open(file_path) as file_obj:
        reader = csv.reader(file_obj, delimiter='\t')
        data = [row for row in reader]

    # Extract metadata
    start_found = False
    metadata = []
    for i, row in enumerate(data):
        if row == ['#', 'Inj Summary Report CAD Final 2  ']:
            start_found = True
            continue
        if start_found and ("Project Name:" in row and "Reported by User:" in row):
            break
        if start_found:
            metadata.append(row[0])

    metadata_dict = {
        key.strip(): value.strip()
        for row in metadata if ":" in row
        for key, value in [row.split(":", 1)]
    }

    # Extract Result IDs from content
    result_id_str = metadata_dict.get("Result Id", "0")
    result_ids_in_content = [int(x.strip()) for x in result_id_str.split(",")]

    # Extract Result ID from filename
    filename_match = re.search(r'(\d+)\.ars$', file_path)
    filename_result_id = int(filename_match.group(1)) if filename_match else None

    # Use filename's Result ID if it's in the content list
    if filename_result_id and filename_result_id in result_ids_in_content:
        result_id = filename_result_id
        status = f"Using filename ID {result_id}"
    else:
        result_id = result_ids_in_content[-1]
        status = f"Filename ID {filename_result_id} not in {result_ids_in_content}, using last: {result_id}"

    return result_id, result_ids_in_content, status

# Test files
test_cases = [
    ("CAD_export_report93265.ars", 93265, [93269, 93267, 93265]),
    ("CAD_export_report93270.ars", 93270, [93271, 93270, 93272]),
    ("CAD_export_report93274.ars", 93274, [93274, 93837, 93275]),
    ("CAD_export_report93280.ars", 93280, [93280, 93281, 93844]),
    ("CAD_export_report93287.ars", 93287, [93286, 93287, 93849]),
]

error_dir = r"S:\Shared\DjangoRawData\Empower\Error Files"

print("Testing Result ID Extraction Fix")
print("="*100)
print(f"{'Filename':<35} {'Expected':<10} {'Got':<10} {'Content IDs':<30} {'Status':<20}")
print("="*100)

all_correct = True

for filename, expected_id, content_ids in test_cases:
    file_path = f"{error_dir}\\{filename}"

    result_id, extracted_ids, status = extract_metadata_fixed(file_path)

    correct = "PASS" if result_id == expected_id else "FAIL"
    if result_id != expected_id:
        all_correct = False

    print(f"{filename:<35} {expected_id:<10} {result_id:<10} {str(extracted_ids):<30} {correct}")

print("="*100)
if all_correct:
    print("SUCCESS: All Result IDs extracted correctly!")
else:
    print("FAILURE: Some Result IDs were incorrect")
