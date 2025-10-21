# Octet Kinetics Parameters - Implementation Guide

## Overview

This implementation adds complete support for displaying and analyzing kinetic parameters (Ka, Kd, Kdis, Rmax, R²) from Octet binding experiments. The system now includes:

1. **Database Storage**: Kinetic parameters are stored in the `OctetKineticsSensor` model
2. **Import Tool**: Management command to import parameters from Excel reports
3. **Interactive Dashboard**: Enhanced Octet Kinetics Dashboard with parameters table and plot annotations
4. **Visualization Options**: Multiple display modes for kinetic parameters

---

## 1. Importing Kinetic Parameters from Excel

### Command Usage

```bash
python manage.py import_kinetic_parameters <experiment_name> <excel_path>
```

### Example

```bash
python manage.py import_kinetic_parameters OE292 "C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292\Results\ExcelReport_2025_10_15 13_27_15.xlsx"
```

### What It Does

- Reads the "Result Table" sheet from the Octet Excel report
- Extracts kinetic parameters for each antibody-concentration pair:
  - **KD (M)**: Dissociation constant
  - **Ka (1/Ms)**: Association rate constant
  - **Kdis (1/s)**: Dissociation rate constant
  - **Rmax (nm)**: Maximum response
  - **Full R²**: Goodness of fit
- Updates the database with these values
- Handles special formats like "<1.0E-12" (converts to numeric values)

### Expected Output

```
Importing kinetic parameters for OE292
Excel file: C:\...\ExcelReport_2025_10_15 13_27_15.xlsx
Sheet: Result Table

Found experiment: OE292
Loaded 112 rows from Excel
Updated 10 sensors...
Updated 20 sensors...
...

============================================================
Updated: 112 sensors
Skipped: 0 sensors
============================================================
```

---

## 2. Octet Kinetics Dashboard Features

### Access the Dashboard

Navigate to: `/octet-kinetics/` (Django URL pattern)

### Two Main Tabs

#### Tab 1: Binding Curves
- **All Antibodies (Grid View)**: Show all antibodies as subplots
- **Single Antibody View**: Detailed view of one antibody with concentration series

#### Tab 2: Kinetic Parameters
- **Interactive Table**: Sortable, filterable table with all kinetic parameters
- **Export to Excel**: Download the table as an Excel file
- **Color Coding**:
  - Yellow background: Reference sensors (0 nM concentration)
  - Red background: Missing kinetic parameters

---

## 3. Display Options for Binding Curves

### Display Options Checkboxes

1. **Show KD**: Display KD value in subplot titles
2. **Show Ka/Kdis**: Display Ka and Kdis values in subplot titles
3. **Annotate on Plot**: Add a text box with kinetic parameters on each plot
4. **Show All Steps**: Show loading/baseline steps (default: only association/dissociation)

### Examples

#### Just KD in Title
```
SI-157C11_P5158
KD=1.23e-09M
```

#### KD + Ka/Kdis in Title
```
SI-157C11_P5158
KD=1.23e-09M
Ka=8.18e+04 1/Ms
Kdis=2.00e-05 1/s
```

#### Annotation Box on Plot
A semi-transparent text box appears in the top-right corner:
```
┌─────────────────────────┐
│ KD: 1.23e-09 M         │
│ Ka: 8.18e+04 1/Ms      │
│ Kdis: 2.00e-05 1/s     │
└─────────────────────────┘
```

---

## 4. Kinetic Parameters Table Features

### Table Columns
- **Antibody**: Antibody ID (e.g., SI-157C11_P5158)
- **Concentration (nM)**: Analyte concentration
- **KD (M)**: Dissociation constant
- **Ka (1/Ms)**: Association rate constant
- **Kdis (1/s)**: Dissociation rate constant
- **Rmax (nm)**: Maximum binding response
- **R²**: Goodness of fit
- **Well**: Loading well location

### Interactive Features
- **Sort**: Click column headers to sort (multi-column supported)
- **Filter**: Type in column headers to filter rows
- **Pagination**: 20 rows per page (configurable)
- **Export**: Click "Export" button to download as Excel

### Example View
```
| Antibody          | Conc. (nM) | KD (M)      | Ka (1/Ms)   | Kdis (1/s)  | Rmax (nm) | R²     | Well |
|-------------------|------------|-------------|-------------|-------------|-----------|--------|------|
| SI-157C11_P5158   | 200.0      | 0.00e+00    | 8.18e+04    | 2.00e-05    | 0.7570    | 0.9850 | A1   |
| SI-157C12_P5159   | 200.0      | 1.00e-12    | 8.81e+04    | 1.00e-07    | 0.7511    | 0.9920 | A2   |
| SI-157C15_P5235   | 200.0      | 0.00e+00    | 1.10e+05    | 7.86e-03    | 0.3433    | 0.9873 | A3   |
```

---

## 5. Database Schema

### OctetKineticsSensor Model Fields

```python
class OctetKineticsSensor(models.Model):
    # ... other fields ...

    # Kinetic parameters (from vendor analysis)
    kd_m = models.FloatField(
        null=True,
        blank=True,
        help_text="Dissociation constant (M)"
    )
    ka_1_ms = models.FloatField(
        null=True,
        blank=True,
        help_text="Association rate constant (1/Ms)"
    )
    kdis_1_s = models.FloatField(
        null=True,
        blank=True,
        help_text="Dissociation rate constant (1/s)"
    )
    rmax = models.FloatField(
        null=True,
        blank=True,
        help_text="Maximum response (nm)"
    )
    r_squared = models.FloatField(
        null=True,
        blank=True,
        help_text="Goodness of fit"
    )
```

---

## 6. Workflow Example

### Complete Workflow for OE292 Experiment

1. **Import FRD Data** (if not already done):
   ```bash
   python manage.py import_kinetics_frd OE292 "C:\...\OE292"
   ```

2. **Import Kinetic Parameters from Excel**:
   ```bash
   python manage.py import_kinetic_parameters OE292 "C:\...\ExcelReport_2025_10_15 13_27_15.xlsx"
   ```

3. **View in Dashboard**:
   - Navigate to `/octet-kinetics/`
   - Click "Select Experiment"
   - Choose "OE292"
   - Click "Load Selected"

4. **Explore Binding Curves Tab**:
   - Select view mode (Grid or Single Antibody)
   - Enable display options:
     - ✓ Show KD
     - ✓ Show Ka/Kdis
     - ✓ Annotate on Plot
   - Click "Generate Plot"

5. **Review Kinetic Parameters Tab**:
   - Switch to "Kinetic Parameters" tab
   - Click "Refresh Table"
   - Sort by KD to find best binders
   - Filter by antibody name
   - Export to Excel for further analysis

---

## 7. Excel Report Format

### Expected Excel Structure

**Sheet Name**: "Result Table"

**Required Columns**:
- `Loading Sample ID` → Antibody identifier
- `Conc. (nM)` → Concentration in nanomolar

**Kinetic Parameter Columns**:
- `KD (M)` → Dissociation constant
- `ka (1/Ms)` → Association rate
- `kdis (1/s)` → Dissociation rate
- `Rmax` → Maximum response
- `Full R^2` → R-squared value

**Special Formats Handled**:
- `<1.0E-12` → Converted to `1.0e-12`
- `0.0` → Stored as `NULL` in database

---

## 8. Troubleshooting

### Issue: "No kinetic parameters found"

**Cause**: Parameters haven't been imported from Excel yet

**Solution**: Run the import command:
```bash
python manage.py import_kinetic_parameters <experiment_name> <excel_path>
```

### Issue: "Sensor not found" errors during import

**Cause**: Mismatch between Excel report and FRD import data

**Possible Reasons**:
1. Antibody names don't match exactly (check capitalization, spaces)
2. Concentration values don't match (e.g., 200.0 vs 200)
3. FRD data wasn't imported for this experiment

**Solution**:
1. Check antibody names in database vs Excel
2. Verify concentrations match
3. Re-import FRD data if needed

### Issue: Table shows "N/A" for all parameters

**Cause**: Excel import failed or parameters are NULL

**Solution**:
1. Check that Excel file has correct sheet name ("Result Table")
2. Verify Excel columns match expected names
3. Re-run import command with verbose output

---

## 9. Future Enhancements

### Potential Features
- **Automatic calculation of KD from Ka/Kdis**: `KD = Kdis / Ka`
- **Quality filtering**: Highlight low R² values
- **Comparison plots**: Overlay multiple antibodies on same plot
- **Heatmap view**: KD heatmap across all antibodies
- **Statistical analysis**: Calculate mean, std dev for replicates

---

## Files Modified

1. **Management Command**:
   - `plotly_integration/management/commands/import_kinetic_parameters.py`

2. **Dashboard**:
   - `plotly_integration/process_development/analytical/octet/octet_kinetics_dash_app.py`

3. **Models** (already had fields):
   - `plotly_integration/models.py` (OctetKineticsSensor)

---

## Summary

✅ **Kinetic parameters are now fully integrated into the Octet analysis workflow**

Key capabilities:
- Import Ka, Kd, Kdis, Rmax, R² from vendor Excel reports
- Display parameters in titles, annotations, and tables
- Filter, sort, and export parameter tables
- Visualize binding curves with kinetic constants overlaid

This provides a complete solution for analyzing and presenting Octet kinetics data with quantitative binding parameters.
