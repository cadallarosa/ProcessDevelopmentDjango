# SEC File Import Issues - Diagnosis and Fix Summary

## Investigation Date
2025-11-06

## Location
Error Files Directory: `S:\Shared\DjangoRawData\Empower\Error Files`
Import Scripts:
- `process_ars.py`: Processes `.ars` files (metadata and peak results)
- `process_arw.py`: Processes `.arw` files (chromatogram time-series data)

## Issues Found

### Issue #1: Result ID Mismatch (CRITICAL)
**Severity**: HIGH - Causes 50% of files to import with wrong Result ID

**Problem**:
- Files contain multiple Result IDs in comma-separated format (e.g., "93271, 93270, 93272")
- The original code arbitrarily took the LAST Result ID from the list
- The correct Result ID is actually in the FILENAME (e.g., `CAD_export_report93270.ars` should use ID 93270)

**Impact**:
- Sample data gets associated with the wrong Result ID
- Same sample analyzed multiple times gets mismatched with wrong analysis run
- 10 out of 20 test files had Result ID mismatches

**Examples**:
| Filename | Content Result IDs | Old Logic Used | Should Use |
|----------|-------------------|----------------|------------|
| CAD_export_report93270.ars | [93271, 93270, 93272] | 93272 ❌ | 93270 ✓ |
| CAD_export_report93274.ars | [93274, 93837, 93275] | 93275 ❌ | 93274 ✓ |
| CAD_export_report93280.ars | [93280, 93281, 93844] | 93844 ❌ | 93280 ✓ |

**Root Cause**:
```python
# OLD CODE (WRONG):
result_id = int(result_id_str.split(",")[-1].strip())  # Takes last one
```

**Fix Applied**:
```python
# NEW CODE (CORRECT):
# 1. Extract Result IDs from file content
result_ids_in_content = [int(x.strip()) for x in result_id_str.split(",")]

# 2. Extract Result ID from filename
filename_match = re.search(r'(\d+)\.ars$', file_path)
filename_result_id = int(filename_match.group(1)) if filename_match else None

# 3. Use filename's Result ID if it's in the content list
if filename_result_id and filename_result_id in result_ids_in_content:
    result_id = filename_result_id  # ✓ Use filename ID
else:
    result_id = result_ids_in_content[-1]  # Fallback to last one
```

### Issue #2: Separator Rows Breaking Peak Data Extraction
**Severity**: MEDIUM - Causes incomplete peak data import

**Problem**:
- Some files have separator rows (`#`) in the middle of peak results data
- The parser was not skipping these separator rows
- This caused peak data extraction to fail or return incomplete results

**Examples**:
- `CAD_export_report93265.ars`: Has separator row at position 29
- `CAD_export_report93274.ars`: Has separator row at position 33
- ~50% of files have these separator rows

**Root Cause**:
The `extract_peak_results()` function didn't check for separator rows

**Fix Applied**:
```python
# NEW CODE: Skip separator rows before processing peak data
if check and (row == ['#'] or (len(row) > 0 and row[0] == '#' and all(x == '' or x == ' ' for x in row[1:]))):
    print(f"Skipping separator row: {row[:3]}")
    continue
```

### Issue #3: Missing Channel Name in Peak Detection
**Severity**: LOW - Minor issue that could cause some peaks to be missed

**Problem**:
- The code was checking for "ACQUITY TUV ChA" but NOT "ACQUITY TUV ChB"
- Both channels appear in the data files

**Fix Applied**:
```python
# OLD: Only checked for ChA
elif check and any(keyword in row for keyword in ["ACQUITY TUV ChA", "2998 Ch1 280nm@6.0nm","DAD.0.0"]):

# NEW: Added ChB
elif check and any(keyword in row for keyword in ["ACQUITY TUV ChA", "ACQUITY TUV ChB", "2998 Ch1 280nm@6.0nm","DAD.0.0"]):
```

## Files Modified

### `process_ars.py`
- Line 164-175: Added filename-based Result ID extraction
- Line 330-333: Added separator row handling in peak extraction
- Line 336: Added "ACQUITY TUV ChB" to channel detection

## Testing Results

### Result ID Extraction Test
Tested 5 files with known mismatches:
```
CAD_export_report93265.ars  Expected: 93265  Got: 93265  [PASS]
CAD_export_report93270.ars  Expected: 93270  Got: 93270  [PASS]
CAD_export_report93274.ars  Expected: 93274  Got: 93274  [PASS]
CAD_export_report93280.ars  Expected: 93280  Got: 93280  [PASS]
CAD_export_report93287.ars  Expected: 93287  Got: 93287  [PASS]
```
✅ **All tests passed**

## Recommendations

### 1. Re-import All Error Files
Now that the fixes are in place, you should re-import all files in the Error Files directory:
```python
from plotly_integration.process_development.downstream_processing.empower.database import process_ars

error_dir = r"S:\Shared\DjangoRawData\Empower\Error Files"
reported_dir = r"S:\Shared\DjangoRawData\Empower\Reported"

process_ars.process_files(error_dir, reported_dir)
```

### 2. Verify Data Integrity
After re-import, verify that:
- Each sample's Result ID matches the filename
- Peak results are complete (no missing data due to separator rows)
- All channels (ChA and ChB) are captured

### 3. Consider Adding Validation
Add validation to ensure:
- Filename Result ID always matches one of the content Result IDs
- Warn if this is not the case
- Log which Result ID was chosen and why

## Next Steps

1. **Test on a few files manually** to verify the fixes work in your environment
2. **Back up the database** before bulk re-import
3. **Run the import process** on all error files
4. **Verify results** by spot-checking a few imported records

## Questions?

If you have any questions about these fixes or need help with the re-import process, let me know!
