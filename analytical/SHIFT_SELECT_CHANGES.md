# Shift-Select Functionality for SEC Report Creator

## Overview
Adding documentation and clarification for the existing shift-select functionality in the SEC Report Creator left table (Available Samples).

## Current Status
The left table already has shift-select enabled via these Tabulator settings:
- `selectable: true` - Enables multi-row selection
- `selectableRangeMode: "click"` - Enables shift+click range selection

## Changes Needed

### 1. JavaScript File Update
**File:** `analytical/static/analytical/js/sec_report_create_v2.js`

**Location:** Line 56-57

**Current Code:**
```javascript
selectable: true, // Enable multi-row selection
selectableRangeMode: "click", // Allow click-based range selection
```

**Updated Code:**
```javascript
selectable: true, // Enable multi-row selection
selectableRangeMode: "click", // Allow Shift+Click for range selection (select multiple rows)
```

### 2. Help Modal Update
**File:** `analytical/templates/analytical/sec/create_report_v2.html`

**Location:** Lines 424-433 (Keyboard Shortcuts table)

**Current Rows:**
```html
<tr>
    <td><strong>Add Sample</strong></td>
    <td><kbd>Click</kbd> on row</td>
    <td>Add individual sample to selected group</td>
</tr>
<tr>
    <td><strong>Bulk Add</strong></td>
    <td><kbd>Double-Click</kbd> on group header</td>
    <td>Add all samples from a sample set to selected group</td>
</tr>
```

**Updated Rows:**
```html
<tr>
    <td><strong>Select Row</strong></td>
    <td><kbd>Click</kbd> on row</td>
    <td>Select a single row (toggle selection)</td>
</tr>
<tr>
    <td><strong>Select Multiple Rows</strong></td>
    <td><kbd>Shift</kbd> + <kbd>Click</kbd> on row</td>
    <td>Select range of rows (from last selected to clicked row)</td>
</tr>
<tr>
    <td><strong>Add Selected Samples</strong></td>
    <td><kbd>Double-Click</kbd> on selected row</td>
    <td>Add all selected samples to the active group</td>
</tr>
<tr>
    <td><strong>Bulk Add</strong></td>
    <td><kbd>Double-Click</kbd> on group header</td>
    <td>Add all samples from a sample set to selected group</td>
</tr>
```

### 3. Workflow Tips Update (Optional Enhancement)
**File:** `analytical/templates/analytical/sec/create_report_v2.html`

**Location:** Lines 467-474

**Add new tip:**
```html
<li><strong>Multi-Select Samples:</strong> Use Shift+Click to select a range of samples, then double-click any selected row to add them all to your report</li>
```

Insert this after line 470 (after "Switch Active Group" tip).

## How Shift-Select Works

### User Workflow:
1. **Click** first row → Selects row and highlights it
2. **Shift+Click** last row → Selects all rows between first and last
3. **Double-Click** any selected row → Adds all selected rows to the report
4. **Click** empty table area → Clears selection

### Current Implementation:
The existing code already supports this workflow:

- **Line 124-158**: `rowClick` handler toggles row selection with `row.toggleSelect()`
- **Line 161-182**: `rowDblClick` handler checks if clicked row is in selection
  - If YES → Adds all selected rows via `selectedRows.forEach()`
  - If NO → Adds only clicked row
- **Line 231-238**: `tableClick` handler clears selection when clicking empty space

### What's Already Working:
✅ Shift+Click range selection (built into Tabulator)
✅ Multi-row double-click to bulk add
✅ Visual selection highlighting
✅ Clear selection on empty click

## Testing Instructions

1. Open SEC Report Creator: `/analytical/sec/create-report/`
2. Load samples using prefix filter
3. Test shift-select:
   - Click first sample row → Row highlights
   - Scroll down and Shift+Click another row → Range selects
   - Double-click any selected row → All selected rows added to report
4. Verify help modal documents this feature correctly

## Additional Notes

- The shift-select feature works with grouped AND ungrouped views
- Works across group boundaries when groups are expanded
- Compatible with Alt+Click preview (previews all selected rows)
- No additional JavaScript code needed - Tabulator handles range selection natively
