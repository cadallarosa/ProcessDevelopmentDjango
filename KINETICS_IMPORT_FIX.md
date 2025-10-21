# Kinetics Import Fix - Understanding Global vs Concentration-Specific Parameters

## The Issue

You were seeing all "N/A" values in the kinetics table because the original import command didn't understand how Octet kinetic fits work.

## How Octet Kinetic Fits Work

### Global Fit Parameters (Same for ALL concentrations)
When Octet performs a **global fit** (which is the default for kinetics experiments), it calculates a single set of kinetic parameters that apply to the entire concentration series:

- **KD (M)**: Dissociation constant - ONE value per antibody
- **Ka (1/Ms)**: Association rate - ONE value per antibody
- **Kdis (1/s)**: Dissociation rate - ONE value per antibody
- **R² (Full R²)**: Goodness of fit - ONE value per antibody

### Concentration-Specific Parameters
- **Rmax (nm)**: Maximum response - DIFFERENT for each concentration
- **Response (nm)**: Observed response at steady state

### Example from Your Data (SI-157C11_P5158)

```
Conc. (nM)  |  KD (M)  |  Ka (1/Ms)    | Kdis (1/s) |  Rmax
---------------------------------------------------------
200.0       |  0.0     |  81765.80     |  0.00002   |  0.757
100.0       |  0.0     |  81765.80     |  0.00002   |  0.960  ← Same Ka, Kdis
50.0        |  0.0     |  81765.80     |  0.00002   |  1.159  ← Different Rmax
25.0        |  0.0     |  81765.80     |  0.00002   |  1.436
12.5        |  0.0     |  81765.80     |  0.00002   |  1.791
6.25        |  0.0     |  81765.80     |  0.00002   |  1.977
3.125       |  0.0     |  81765.80     |  0.00002   |  2.036
```

Notice: Ka and Kdis are **identical** for all concentrations (global fit), but Rmax varies.

## Why the Original Import Failed

Your database has sensors for concentrations like **0 nM (reference)**, **3.125 nM**, **6.25 nM**, etc.

The original import tried to match:
1. **Antibody name** ✓
2. **Exact concentration** ✗ (0 nM not in Excel, floating point precision issues)

So it failed to find matches and left everything as NULL.

## The Solution: Two-Step Import

The new `import_kinetic_parameters_v2.py` command does this correctly:

### Step 1: Import Global Kinetic Parameters
- Extract KD, Ka, Kdis, R² from the Excel (one set per antibody)
- Apply these values to **ALL** sensors for that antibody
- This includes 0 nM reference sensors!

### Step 2: Import Concentration-Specific Rmax
- For each concentration in the Excel, import Rmax
- Only updates sensors with matching concentrations

## Usage

```bash
# Use the NEW v2 command
python manage.py import_kinetic_parameters_v2 OE292 "C:\...\ExcelReport_2025_10_15 13_27_15.xlsx"
```

### Expected Output

```
============================================================
Importing kinetic parameters for OE292
Excel file: C:\...\ExcelReport_2025_10_15 13_27_15.xlsx
Sheet: Result Table
============================================================

✓ Found experiment: OE292
✓ Loaded 168 rows from Excel

Step 1: Collecting global kinetic parameters (KD, Ka, Kdis, R²)...
  → Found kinetic parameters for 14 antibodies

Step 2: Applying global kinetic parameters to all sensors...
  → Updated 20 sensors...
  → Updated 40 sensors...
  → Updated 60 sensors...
  → Updated 80 sensors...
  → Updated 100 sensors...
  → Applied global kinetics to 112 sensors

Step 3: Importing concentration-specific Rmax values...
  → Updated 20 Rmax values...
  → Updated 40 Rmax values...
  → Updated Rmax values for 98 sensors

============================================================
✓ Global kinetics updated: 112 sensors
✓ Rmax values updated: 98 sensors
============================================================
```

## What This Means for Your Data

After running the v2 import, you'll see:

### In the Kinetics Table (All Concentrations)

```
Antibody          | Conc. (nM) | KD (M)      | Ka (1/Ms)   | Kdis (1/s)  | Rmax (nm) | R²     |
------------------------------------------------------------------------------------------
SI-157C11_P5158   | 0          | N/A         | 8.18e+04    | 2.00e-05    | N/A       | 0.9850 |
SI-157C11_P5158   | 3.125      | N/A         | 8.18e+04    | 2.00e-05    | 2.036     | 0.9850 |
SI-157C11_P5158   | 6.25       | N/A         | 8.18e+04    | 2.00e-05    | 1.977     | 0.9850 |
SI-157C11_P5158   | 12.5       | N/A         | 8.18e+04    | 2.00e-05    | 1.791     | 0.9850 |
SI-157C11_P5158   | 25         | N/A         | 8.18e+04    | 2.00e-05    | 1.436     | 0.9850 |
SI-157C11_P5158   | 50         | N/A         | 8.18e+04    | 2.00e-05    | 1.159     | 0.9850 |
SI-157C11_P5158   | 100        | N/A         | 8.18e+04    | 2.00e-05    | 0.960     | 0.9850 |
SI-157C11_P5158   | 200        | N/A         | 8.18e+04    | 2.00e-05    | 0.757     | 0.9850 |
```

Notes:
- **KD = N/A**: This is because your Excel shows `KD = 0.0` which we treat as NULL (no fit or infinite affinity)
- **Ka, Kdis, R²**: Same for ALL concentrations (global fit)
- **Rmax**: Different for each concentration (except 0 nM which isn't in Excel)

### In the Plots

With "Annotate on Plot" enabled, you'll see:

```
┌─────────────────────────┐
│ KD: N/A                │
│ Ka: 8.18e+04 1/Ms      │
│ Kdis: 2.00e-05 1/s     │
└─────────────────────────┘
```

## Why KD = 0.0 in the Excel?

When KD = 0.0 in the vendor software, it typically means:
1. **No dissociation detected** (infinite affinity)
2. **Fit failed** (couldn't converge)
3. **Below detection limit** (shown as `<1.0E-12`)

You can calculate KD from Ka and Kdis:
```
KD = Kdis / Ka
KD = 2.00e-05 / 8.18e+04 = 2.44e-10 M
```

So the actual KD is around **244 pM** (very strong binding).

## Files

- **NEW**: `import_kinetic_parameters_v2.py` - Use this one!
- **OLD**: `import_kinetic_parameters.py` - Don't use (has the bug)

## Summary

✅ **Problem**: Original import expected exact concentration matches
✅ **Solution**: Recognize global vs concentration-specific parameters
✅ **Result**: All sensors get Ka, Kdis, R² values; only matching concentrations get Rmax

Now your kinetics data will display correctly in the table and plots!
