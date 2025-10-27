# View/Edit Existing Source Materials Feature

## Overview

Added comprehensive view/edit functionality to manage existing source materials through a dedicated "Manage Existing Source Materials" tab.

## Features

### 1. Filterable Table View
- **Modern DataTable** showing all source materials
- **Columns**: SM ID, Name, Project, DN, PD Sample, Created Date, Status
- **Filters**:
  - Project ID dropdown (populated from existing projects)
  - Search across all fields (future enhancement)
  - Refresh button
- **Sorting**: Click any column header
- **Pagination**: 20 rows per page
- **Selection**: Click row to load into edit form

### 2. Full Edit Capabilities
Edit all aspects of existing source materials:

**Basic Properties:**
- Source Material Name
- Final pH
- Final Conductivity (mS/cm)
- Final Concentration (mg/mL)
- Final Volume (mL)

**Relationships:**
- **DN Link**: Change which DN experiment the SM is linked to
  - Dropdown shows: "DN{id} - {project} - {unit_op}"
  - Option to unlink ("None")
  - Updates both SM → DN and DN → SM relationships

**Sample Pooling:**
- Add/remove pooled samples
- Multi-select dropdown with all available samples
- Preserves existing selections

**Process Steps:**
- Full CRUD on process steps table
- Add new steps with dropdown (Concentration, Pooling, etc.)
- Edit existing steps
- Delete steps (remove row)

**Read-Only Fields:**
- Resulting PD Sample (display only, cannot change)

### 3. User Workflow

**Viewing SMs:**
1. Click "Manage Existing Source Materials" tab
2. (Optional) Filter by project
3. Table loads with all matching SMs
4. Sort/filter as needed

**Editing an SM:**
1. Click row in table
2. Edit form appears below
3. Modify any fields
4. Click "Save Changes"
5. Success alert appears
6. Form hides
7. Table refreshes with updated data

**Canceling:**
- Click "Cancel" button
- Form hides without saving
- Table selection clears

## Implementation Details

### Files Created (2)

#### 1. `layout_helpers.py` (210 lines)
Helper function to create the Manage Existing tab layout:
- Filter controls
- Source materials table
- Edit form (conditional display)
- All form fields and controls

**Function**: `create_manage_existing_tab()`

#### 2. `callbacks/view_edit.py` (250 lines)
All callbacks for view/edit functionality:

**Callbacks**:
1. `load_sm_table()` - Load/refresh table data
2. `load_sm_for_edit()` - Load selected SM into form
3. `add_process_step_edit()` - Add process step in edit mode
4. `save_edited_sm()` - Save all changes to database
5. `cancel_edit()` - Cancel and hide form

### Files Modified (4)

#### 1. `utils/data_helpers.py` (+70 lines)
**New Functions:**
- `get_all_source_materials()` - Query SMs with filters
- `get_all_dn_assignments()` - Get DNs for dropdown

#### 2. `components/tables.py` (+45 lines)
**New Function:**
- `create_sm_management_table()` - Table component with styling

#### 3. `layout.py` (restructured)
- Wrapped existing content in tabs
- Added "Create New" tab (existing functionality)
- Added "Manage Existing" tab (new)
- Imports layout helper

#### 4. `callbacks/__init__.py` (+2 lines)
- Import view_edit callbacks
- Register in `register_all_callbacks()`

### Database Operations

**Read Operations:**
- Load all SMs with related data (DN, PD sample)
- Load pooled samples
- Load process steps
- Load DN options for dropdown

**Write Operations (Transactional):**
- Update SM basic properties
- Update DN link (bidirectional)
  - Set `PD_sample.dn = DN`
  - Set `DN.source_material = SM`
- Update pooled samples (M2M relationship)
- Delete all existing process steps
- Create new process steps

**Atomicity**: All updates wrapped in `transaction.atomic()` for safety

### UI Components Used

**DBC Components:**
- `dbc.Card` - Organize sections
- `dbc.CardHeader/Body/Footer` - Card structure
- `dbc.Row/Col` - Responsive grid
- `dbc.Button` - Actions
- `dbc.Alert` - Success/error messages
- `dbc.Badge` - "EDITING" indicator
- `dbc.FormText` - Help text

**Dash Components:**
- `dash_table.DataTable` - Main table and process steps
- `dcc.Dropdown` - DN and samples selection
- `dbc.Input` - Text and number inputs

### Styling

**Table Highlights:**
- Selected row: Light blue background (`#d1ecf1`)
- SM ID column: Bold blue text (`#0d6efd`)
- Striped rows for readability

**Form:**
- Consistent with "Create New" tab styling
- Yellow "EDITING" badge for visual feedback
- Disabled state for read-only PD sample

## Usage Examples

### Example 1: Change DN Link
```
1. Navigate to "Manage Existing" tab
2. Click on SM5 in table
3. Form loads with current DN = DN42
4. Change DN dropdown to DN50
5. Click "Save Changes"
6. SM5 now linked to DN50
7. DN50.source_material = SM5
8. PD123.dn = DN50
```

### Example 2: Add Pooled Samples
```
1. Select SM8 from table
2. Current pooled samples: [PD1, PD2]
3. Multi-select shows PD1, PD2 selected
4. Add PD5 to selection
5. Save changes
6. SM8 now pools PD1, PD2, PD5
```

### Example 3: Edit Process Steps
```
1. Select SM3
2. Current steps: [1: Concentration, 2: pH Adjustment]
3. Edit step 1 notes: "Concentrated to 50 mg/mL"
4. Click "Add Step" - adds step 3
5. Select "Dilution" from dropdown for step 3
6. Delete step 2 (remove row)
7. Save changes
8. SM3 now has: [1: Concentration (with notes), 2: Dilution]
```

## Future Enhancements

**Potential Additions:**
- [ ] Delete SM functionality (with cascade warning)
- [ ] Duplicate SM feature (copy with new ID)
- [ ] Bulk edit (select multiple rows)
- [ ] Export table to Excel
- [ ] Audit trail (show edit history)
- [ ] Date range filter for creation date
- [ ] Advanced search (regex, multi-field)
- [ ] Inline editing (edit directly in table)
- [ ] Undo last change

**Change Detection:**
- [ ] Highlight modified fields in yellow
- [ ] Warn before navigating away with unsaved changes
- [ ] Show diff of changes before saving

**Validation:**
- [ ] Prevent unlinking DN if SM is in use
- [ ] Warn if removing pooled samples
- [ ] Validate numeric fields (pH 0-14, etc.)

## Testing Checklist

- [ ] Table loads all SMs correctly
- [ ] Project filter works
- [ ] Clicking row loads data into form
- [ ] Can edit SM name
- [ ] Can edit sample properties
- [ ] DN dropdown populates
- [ ] Changing DN updates both SM and DN
- [ ] Unlinking DN (select "None") works
- [ ] Pooled samples multi-select works
- [ ] Adding pooled samples works
- [ ] Removing pooled samples works
- [ ] Process steps load correctly
- [ ] Adding process step works
- [ ] Editing process step works
- [ ] Deleting process step (remove row) works
- [ ] Save updates database
- [ ] Success alert shows
- [ ] Table refreshes after save
- [ ] Form hides after save
- [ ] Cancel button works
- [ ] Transaction rollback on error

## Performance Considerations

**Optimizations:**
- `select_related()` for DN and PD sample (reduces queries)
- Limit DN dropdown to last 100 DNs
- Pagination on table (20 rows per page)
- Native filtering/sorting (client-side)

**Scaling:**
- For 1000+ SMs, consider server-side pagination
- For 100+ DNs, add search to DN dropdown
- Add database indexes on commonly filtered fields

## Security

**Considerations:**
- All updates wrapped in transactions
- Django ORM prevents SQL injection
- No user input directly in queries
- Foreign key constraints enforced

**Future:**
- Add user permissions (who can edit?)
- Log all changes for audit
- Add confirmation modals for destructive actions

## Conclusion

The View/Edit functionality provides a complete CRUD interface for managing existing source materials. Users can easily find, view, and modify SMs without recreating them, fixing errors and keeping data accurate.

**Key Benefits:**
✅ Fix mistakes in existing SMs
✅ Update relationships (DN, pooled samples)
✅ Modify process steps
✅ Professional table interface
✅ Transaction-safe updates
✅ Consistent with create workflow
