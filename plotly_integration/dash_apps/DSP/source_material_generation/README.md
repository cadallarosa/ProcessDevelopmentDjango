# Source Material Generation App

A modern, standalone Dash application for creating and managing source materials in downstream processing experiments.

## Overview

This app provides a clean, intuitive interface for:
- Creating new source materials or using existing ones
- Pooling multiple samples together
- Recording detailed process steps
- Auto-generating resulting PD samples
- Managing sample properties (pH, conductivity, concentration, volume)

## Architecture

The app follows modern best practices with clear separation of concerns:

```
source_material_generation/
├── app.py                      # Main app registration
├── layout.py                   # DBC-based UI layout
├── callbacks/                  # Callback logic organized by feature
│   ├── __init__.py
│   ├── mode_toggle.py         # Existing vs New mode switching
│   ├── sample_selection.py    # Sample pooling dropdowns
│   ├── process_steps.py       # Process steps table
│   └── save_operations.py     # Save/update with validation
├── components/                 # Reusable UI components
│   ├── __init__.py
│   ├── forms.py               # DBC form helpers
│   └── tables.py              # DataTable configurations
└── utils/                      # Utility functions
    ├── __init__.py
    └── data_helpers.py        # Database query helpers
```

## Features

### Modern UI with Dash Bootstrap Components (DBC)

- **Cards**: Clean, organized sections with headers
- **Forms**: Responsive grid layout with labeled inputs
- **Buttons**: Color-coded actions (primary, secondary)
- **Modals**: Confirmation dialogs for data overwrites
- **Alerts**: Auto-dismissing success/error messages
- **Icons**: Bootstrap icons for visual clarity

### Functionality

1. **Mode Selection**
   - **Use Existing**: Select and edit existing source materials
   - **Create New**: Generate new source materials with auto-ID

2. **Sample Pooling**
   - Filter by sample type (UP, FB, PD)
   - Multi-select dropdown with descriptions and dates
   - Auto-populate from existing source materials

3. **Sample Properties**
   - Final pH, conductivity, concentration, volume
   - Auto-generated resulting sample ID (PD#)

4. **Process Steps**
   - Editable table with step number, process, notes
   - Add/remove steps dynamically
   - Preserved when loading existing source materials

5. **Validation & Safety**
   - Required field validation
   - Change detection for existing source materials
   - Confirmation modal before overwriting
   - Transaction-safe database operations

## Usage

### Accessing the App

**URL**: `/django_plotly_dash/app/SourceMaterialGenerationApp/`

Example: `http://localhost:8000/django_plotly_dash/app/SourceMaterialGenerationApp/`

### Creating a New Source Material

1. Ensure mode is set to "Create New Source Material"
2. Enter **Project ID** (required)
3. Enter **Source Material Name** (required)
4. Select **Sample Type** filter (UP/FB/PD)
5. Choose **Pooled Samples** (multi-select)
6. Fill in **Final Properties** (pH, conductivity, etc.)
7. Add **Process Steps** as needed
8. Click **Save Source Material**

The app will:
- Auto-generate a new SM ID
- Create a corresponding PD sample
- Link all pooled samples
- Save all process steps

### Editing an Existing Source Material

1. Set mode to "Use Existing Source Material"
2. Enter **Project ID**
3. Select from **Existing Source Materials** dropdown
4. Form auto-populates with existing data
5. Make desired changes
6. Click **Save Source Material**
7. Confirm overwrite if changes detected

## Database Models

The app interacts with:

- **LimsSourceMaterial**: Main source material record
- **LimsSampleAnalysis**: Sample records (input and resulting)
- **LimsSourceMaterialStep**: Process step records

## Code Organization

### Components (components/forms.py)

Reusable form helpers:
- `create_labeled_input()` - Input fields with labels
- `create_labeled_dropdown()` - Dropdowns with labels
- `create_labeled_radio()` - Radio button groups
- `create_info_display()` - Read-only displays

### Utilities (utils/data_helpers.py)

Database query helpers:
- `get_source_materials_by_project()` - Filter SMs by project
- `get_samples_by_project_and_type()` - Filter samples
- `get_next_pd_number()` - Auto-increment PD numbers
- `format_sample_dropdown_label()` - Readable labels

### Callbacks

**mode_toggle.py**:
- Toggle visibility of existing SM section
- Populate existing SM dropdown
- Load SM data when selected

**sample_selection.py**:
- Populate available samples by project/type
- Pre-select pooled samples for existing SMs

**process_steps.py**:
- Add new process steps
- Load steps from existing SMs

**save_operations.py**:
- Validate input fields
- Detect changes in existing SMs
- Show confirmation modals
- Save/update with transactions
- Display success/error alerts

## Development Notes

### Adding New Fields

1. Add to layout (layout.py)
2. Add to save callback State (save_operations.py)
3. Update has_changes() if needed
4. Update database model if needed

### Styling

All DBC theme variables are available. Current theme: **BOOTSTRAP (default)**

Custom styles in:
- `components/tables.py` - Table styling constants
- `layout.py` - Inline component styles

### Testing

1. Test creating new source materials
2. Test editing existing source materials
3. Test change detection and modals
4. Test validation (missing required fields)
5. Test sample pooling with different types
6. Test process step management

## Integration

This app is registered in `plotly_integration/apps.py`:

```python
import plotly_integration.dash_apps.DSP.source_material_generation
```

It's a standalone app and doesn't require the DN Assignment app to function.

## Future Enhancements

Potential improvements:
- [ ] Batch creation of multiple source materials
- [ ] Export source material details to Excel
- [ ] History/audit trail for changes
- [ ] Link to DN assignment from here
- [ ] Advanced filtering and search
- [ ] Sample quality metrics tracking

## Troubleshooting

### App not appearing
- Check `apps.py` for import statement
- Verify Django server restarted
- Check browser console for errors

### Callbacks not firing
- Check component IDs match between layout and callbacks
- Verify prevent_initial_call settings
- Check browser console for Dash errors

### Database errors
- Verify models are migrated
- Check foreign key relationships
- Ensure sample IDs exist before pooling

## Contact

For questions or issues with this app, contact the development team.
