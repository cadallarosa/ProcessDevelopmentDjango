"""
Test parsing functions without Django
"""
import csv
import re
import pandas as pd

def extract_metadata(file_path):
    with open(file_path) as file_obj:
        reader = csv.reader(file_obj, delimiter='\t')
        data = [row for row in reader]

    # Extract metadata
    start_found = False
    metadata = []
    for i, row in enumerate(data):
        # Handle both formats:
        if row == ['#', 'Inj Summary Report CAD Final 2  ']:
            start_found = True
            print('START FOUND (Format 1: tab-separated)')
            continue
        elif row == ['#'] and i + 1 < len(data) and data[i + 1] == ['Inj Summary Report CAD Final 2  ']:
            start_found = True
            print('START FOUND (Format 2: newline-separated)')
            continue
        elif start_found and row == ['Inj Summary Report CAD Final 2  ']:
            continue

        if start_found and ("Project Name:" in row and "Reported by User:" in row):
            print(f"BREAK CONDITION HIT at row {i}: {row[:2]}")
            break

        if start_found:
            metadata.append(row[0])

    print(f"\nMetadata rows collected: {len(metadata)}")

    # Process metadata into a dictionary
    metadata_dict = {
        key.strip(): value.strip()
        for row in metadata if ":" in row
        for key, value in [row.split(":", 1)]
    }

    # Extract result_id
    result_id_str = metadata_dict.get("Result Id", "0")
    result_ids = [x.strip() for x in result_id_str.split(",")]
    result_id = int(result_ids[-1])

    metadata_dict["Result Id"] = result_id

    print(f"Extracted Result IDs: {result_ids} (using: {result_id})")

    return metadata_dict, result_id, data

def extract_peak_results(data, result_id, system_name):
    expected_columns = [
        "Channel Name", "Name", "RT", "Area", "% Area", "Height",
        "Asym@10", "Plate Count", "Res (HH)", "Start Time", "End Time"
    ]

    report = []
    report.append(expected_columns)
    check = False
    separator_count = 0

    for i, row in enumerate(data):
        row = [col.strip() for col in row]

        # Detect the column header row
        if "% Area" in row:
            check = True
            print(f"Found peak header at row {i}")
            continue
        elif "(min)" in row:
            check = True
            print(f"Found peak header at row {i}")
            continue

        # Skip separator rows
        if check and (row == ['#'] or (len(row) > 0 and row[0] == '#' and all(x == '' or x == ' ' for x in row[1:]))):
            separator_count += 1
            print(f"Skipping separator row {i}: {row[:3]}")
            continue

        # Collect peak data
        elif check and any(keyword in row for keyword in ["ACQUITY TUV ChA", "ACQUITY TUV ChB", "2998 Ch1 280nm@6.0nm","DAD.0.0"]):
            # Align data properly
            while len(row) > len(expected_columns):
                row = row[1:]

            report.append(row)
            print(f"Added peak row {i}: {row[:3]}")

    print(f"\nTotal separator rows skipped: {separator_count}")
    print(f"Total peak rows collected: {len(report) - 1}")

    if report and len(report) > 1:
        df = pd.DataFrame(data=report)
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)
        return df

    return None

# Test file
test_file = r"S:\Shared\DjangoRawData\Empower\Error Files\CAD_export_report93265.ars"

print(f"Testing: {test_file}")
print("="*80)

try:
    metadata_dict, result_id, data = extract_metadata(test_file)
    print(f"\n{'='*80}")
    print("METADATA EXTRACTION SUCCESS")
    print(f"Sample Name: {metadata_dict.get('Sample Name')}")
    print(f"Result ID: {result_id}")

    print(f"\n{'='*80}")
    print("EXTRACTING PEAK RESULTS")
    print('='*80)

    peak_df = extract_peak_results(data, result_id, metadata_dict.get('System Name'))

    if peak_df is not None:
        print(f"\nPeak results: {len(peak_df)} rows")
        print(peak_df)
    else:
        print("\nNo peak results found")

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
