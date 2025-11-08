"""
Diagnostic script to identify issues with SEC file imports
"""
import csv
import os
from pathlib import Path

def diagnose_ars_file(file_path):
    """Diagnose issues with an .ars file"""
    issues = []

    with open(file_path) as file_obj:
        reader = csv.reader(file_obj, delimiter='\t')
        data = [row for row in reader]

    # Check for metadata section
    start_found = False
    metadata_rows = []
    peak_data_rows = []
    in_peak_section = False

    for i, row in enumerate(data):
        # Check for metadata start
        if row == ['#', 'Inj Summary Report CAD Final 2  ']:
            start_found = True
            continue

        if start_found and not in_peak_section:
            # Check for the break condition that should end metadata
            if len(row) >= 2:
                # Check if both "Project Name:" and "Reported by User:" are in the row
                row_str = ' '.join(row)
                if "Project Name:" in row_str and "Reported by User:" in row_str:
                    issues.append(f"Found end of metadata at row {i}: {row[:2]}")
                    in_peak_section = True
                    continue
            metadata_rows.append((i, row))

        if in_peak_section:
            peak_data_rows.append((i, row))

    # Extract Result ID from metadata
    result_ids = []
    for i, row in metadata_rows:
        if len(row) > 0 and "Result Id:" in row[0]:
            result_id_str = row[0].replace("Result Id:", "").strip()
            result_ids = [x.strip() for x in result_id_str.split(",")]
            issues.append(f"Found multiple Result IDs: {result_ids} (will use last: {result_ids[-1]})")
            break

    # Check for peak data issues
    has_peak_header = False
    has_peak_data = False
    separator_rows = []

    for i, row in peak_data_rows:
        if "% Area" in row or "(min)" in row:
            has_peak_header = True

        if any(keyword in row for keyword in ["ACQUITY TUV ChA", "ACQUITY TUV ChB", "2998 Ch1 280nm@6.0nm", "DAD.0.0"]):
            has_peak_data = True

        # Check for separator rows in the middle of data
        if row == ['#'] or (len(row) > 0 and row[0] == '#' and all(x == '' or x == ' ' for x in row[1:])):
            separator_rows.append(i)

    if has_peak_header and not has_peak_data:
        issues.append("[ERROR] Has peak header but NO peak data")

    if separator_rows:
        issues.append(f"[WARNING] Found {len(separator_rows)} separator rows in peak section at rows: {separator_rows}")

    # Check metadata parsing
    if not start_found:
        issues.append("[ERROR] Could not find metadata start marker")

    if len(metadata_rows) == 0:
        issues.append("[ERROR] No metadata rows found")

    return issues

def main():
    error_dir = Path("S:/Shared/DjangoRawData/Empower/Error Files")
    ars_files = list(error_dir.glob("*.ars"))[:10]  # Check first 10 files

    print(f"Diagnosing {len(ars_files)} .ars files...\n")

    for file_path in ars_files:
        print(f"\n{'='*80}")
        print(f"File: {file_path.name}")
        print('='*80)

        issues = diagnose_ars_file(file_path)

        if issues:
            for issue in issues:
                print(f"  {issue}")
        else:
            print("  [OK] No issues detected")

if __name__ == "__main__":
    main()
