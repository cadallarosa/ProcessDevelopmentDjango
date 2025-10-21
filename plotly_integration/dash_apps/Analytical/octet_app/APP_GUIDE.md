# Octet Analysis App - User Guide

## Overview

The Octet Analysis App provides an interactive interface for visualizing and analyzing biolayer interferometry binding kinetics data. The app allows you to:

- Select experiments from the database
- View experiment metadata
- Visualize binding curves for all sensors or selected sensors
- Choose different experimental steps (Association, Dissociation, etc.)
- View sensor results in tabular format
- Normalize baseline values
- Export plots

---

## Accessing the App

### URL
```
http://localhost:8000/plotly_integration/octet-analysis/
```

### Direct Django URL Pattern
```python
path('octet-analysis/', views.octet_analysis_view, name='octet_analysis')
```

---

## Features

### 1. Experiment Selection

**Dropdown Menu:** Select from all imported Octet experiments in the database

The dropdown shows:
- Experiment name
- Experiment type (KINETICS, QUANTITATION, etc.)
- Date of experiment

**Example:**
```
20250917 PE P5216 - 5377 plate 2 kappa 50 ugl (KINETICS) - 2025-09-17
```

### 2. Experiment Information Card

Once selected, displays:
- **Type:** Experiment type and subtype (e.g., KINETICS - KBASIC)
- **Date:** Experiment date and time
- **Temperature:** Experimental temperature in °C
- **Sensors:** Total number of sensors used

### 3. Step Selection

**Dropdown Menu:** Choose which experimental step to visualize

Available steps typically include:
- Baseline 1
- Condition
- Baseline 120
- Loading
- Baseline 60
- **Association** ← Default selection
- Dissociation
- Baseline 20

### 4. Sensor Selection Modes

#### Mode: Show All Sensors (Default)
- Displays all 16 sensors from the experiment
- Color-coded traces for easy identification
- Interactive legend

#### Mode: Select Specific Sensors
- Reveals multi-select dropdown
- Choose specific sensors to display
- Useful for comparing subsets of data

**Example Selections:**
```
A1 - aKappa 50ug/ml
B1 - aKappa 50ug/ml
C1 - aKappa 50ug/ml
```

### 5. Plot Options

**Checkboxes:**
- ☑ **Show Grid** - Display grid lines on plot
- ☑ **Show Legend** - Display sensor legend (default: on)
- ☐ **Normalize Baseline** - Subtract initial response value from all points

### 6. Interactive Plot Features

**The binding curves plot includes:**
- **Zoom:** Click and drag to zoom in
- **Pan:** Hold shift + drag to pan
- **Reset:** Double-click to reset view
- **Hover Info:** Shows time, response, and sensor ID
- **Toggle Traces:** Click legend items to show/hide sensors
- **Autoscale:** Automatically fits all visible traces

**Plot Elements:**
- X-axis: Time (seconds)
- Y-axis: Response (nanometers)
- Title: Shows experiment name and current step
- Multiple color-coded traces (one per sensor)

### 7. Results Table

**Displays for each sensor:**
- Location (e.g., A1, B1, C1)
- Sample ID
- Response (nm) - calculated binding response
- Concentration
- Number of data points

Table features:
- Alternating row colors for readability
- Sortable columns (click header)
- Responsive layout

---

## Typical Workflow

### Step 1: Select Experiment
1. Open the app at `/plotly_integration/octet-analysis/`
2. Click the "Select Experiment" dropdown
3. Choose your experiment

### Step 2: Review Experiment Info
- Check the displayed metadata
- Verify temperature, date, and sensor count

### Step 3: Choose Analysis Step
1. Use the "Select Step" dropdown
2. Default is "Association" (binding phase)
3. Try "Dissociation" to see dissociation kinetics

### Step 4: Adjust View (Optional)
- Switch to "Select Specific Sensors" if needed
- Toggle plot options (grid, legend, normalize)

### Step 5: Click "Refresh Plot"
- Updates the visualization
- Regenerates the results table

### Step 6: Analyze Data
- Hover over traces to see values
- Zoom into regions of interest
- Toggle sensors on/off via legend
- Review results table

---

## Understanding the Plots

### Association Phase
**What you see:**
- Rising curves (binding occurring)
- Response increases over time
- Plateau indicates equilibrium binding

**Example:**
```
Time: 520s → 640s
Response: 0.60nm → 0.71nm (rising)
```

### Dissociation Phase
**What you see:**
- Falling curves (unbinding occurring)
- Response decreases over time
- Rate indicates dissociation kinetics (koff)

### Baseline Phases
**What you see:**
- Relatively flat response
- Establishes reference point
- Used for normalization

---

## Plot Customization

### Normalizing Baseline
**When to use:**
- Comparing sensors with different baseline drift
- Focusing on binding response magnitude
- Removing instrument baseline shifts

**Effect:**
- Subtracts the first data point from all points
- All curves start at ~0 nm
- Relative binding responses preserved

### Selecting Specific Sensors
**When to use:**
- Comparing replicates (e.g., A1, B1, C1)
- Focusing on specific concentration series
- Reducing visual clutter

**How to:**
1. Select "Select Specific Sensors" radio button
2. Multi-select dropdown appears
3. Choose sensors (e.g., A1, B1, C1)
4. Click "Refresh Plot"

---

## Data Export

### Current Export Options
- **Screenshot:** Use browser screenshot tool
- **Plot Image:** Right-click plot → "Download plot as png"
- **Plot Data:** Hover over trace → click "Download" icon

### Future Export Features (Coming Soon)
- Export to Excel
- Export to CSV
- Export fitted parameters
- Generate PDF reports

---

## Keyboard Shortcuts (Plot Area)

- **Double-click:** Reset zoom to fit all data
- **Shift + Drag:** Pan the plot
- **Scroll:** Zoom in/out
- **Click legend:** Toggle trace visibility

---

## Troubleshooting

### Issue: No experiments appear in dropdown
**Solution:** Import experiments first using:
```bash
python manage.py import_octet_data "path/to/consolidated.xlsx" --user USERNAME
```

### Issue: Plot not updating after changing settings
**Solution:** Click the "Refresh Plot" button

### Issue: "No data to display"
**Solution:**
- Verify experiment is selected
- Check that the selected step exists in the experiment
- Ensure sensors have data for that step

### Issue: Too many traces, plot is cluttered
**Solution:**
- Switch to "Select Specific Sensors" mode
- Choose only the sensors you want to view

### Issue: Curves look strange/unexpected
**Solution:**
- Try "Normalize Baseline" to remove baseline drift
- Check if you're viewing the correct step
- Verify data quality in admin interface

---

## Technical Details

### App Architecture
- **Framework:** Plotly Dash + Django
- **Database:** Django ORM → MySQL
- **Rendering:** Server-side callbacks
- **Visualization:** Plotly.js

### Performance
- **Time Series Query:** ~0.5s for 600 points
- **Plot Rendering:** ~1s for 16 sensors
- **Interactive Updates:** Real-time

### Browser Compatibility
- Chrome (recommended)
- Firefox
- Edge
- Safari

---

## Future Enhancements (Roadmap)

### Phase 1: Current ✅
- [x] Experiment selection
- [x] Step visualization
- [x] Multi-sensor overlay
- [x] Results table
- [x] Basic plot options

### Phase 2: Analysis Tools (Coming Soon)
- [ ] Curve fitting (1:1 Binding, Steady-State)
- [ ] KD calculation
- [ ] kon/koff determination
- [ ] R² and χ² quality metrics
- [ ] Residual plots

### Phase 3: Advanced Features (Future)
- [ ] Batch analysis
- [ ] Experiment comparison
- [ ] Statistical analysis (mean, SD, CV)
- [ ] Custom models
- [ ] Automated QC checks

---

## Related Documentation

- **Import Guide:** `IMPORT_USAGE_GUIDE.md`
- **Database Schema:** `OCTET_DATABASE_SCHEMA.md`
- **Pipeline Plan:** `OCTET_PIPELINE_PLAN.md`
- **Quick Reference:** `QUICK_REFERENCE.md`

---

## Support

### View Experiment in Admin
```
http://localhost:8000/admin/plotly_integration/octetexperiment/<id>/
```

### Verify Import
```bash
python manage.py verify_octet_import --id <experiment_id>
```

### Re-import Experiment
```bash
python manage.py import_octet_data "file.xlsx" --user USERNAME --overwrite
```

---

## Example Analysis Session

```
1. Navigate to http://localhost:8000/plotly_integration/octet-analysis/

2. Select experiment: "20250917 PE P5216..."
   → Info card shows: KINETICS, 30.0°C, 16 sensors

3. Step is already "Association" (default)

4. Click "Refresh Plot"
   → 16 binding curves appear

5. Observe:
   - A1: 0.7066 nm response
   - B1: 0.3417 nm response
   - C1: 0.3804 nm response

6. Switch to "Select Specific Sensors"
   → Choose A1, B1, C1

7. Check "Normalize Baseline"

8. Click "Refresh Plot"
   → Three curves, all starting at ~0 nm
   → Easier to compare binding magnitudes

9. Zoom into association phase (520s - 640s)
   → See binding kinetics in detail

10. Switch step to "Dissociation"
    → See unbinding curves

11. Review results table
    → Verify response values match plot
```

---

**Version:** 1.0
**Date:** 2025-10-13
**Status:** Production Ready
