# OE292 FRD File Structure and Mapping

## Summary

**Total Data:**
- 16 FRD files
- 192 total cycles (16 files × 12 cycles each)
- **24 unique antibodies**
- **8 concentrations** (including 0.0 nM reference)
- **192 unique sensors** to import (24 antibodies × 8 concentrations)

## Structure

Each FRD file contains 12 cycles testing different antibodies at the **same concentration**.

### FRD File Organization:

**Files 001-008:** First set of 12 antibodies across 8 concentrations
- `251013_001.frd`: 12 antibodies @ **200.0 nM**
- `251013_002.frd`: 12 antibodies @ **100.0 nM**
- `251013_003.frd`: 12 antibodies @ **50.0 nM**
- `251013_004.frd`: 12 antibodies @ **25.0 nM**
- `251013_005.frd`: 12 antibodies @ **12.5 nM**
- `251013_006.frd`: 12 antibodies @ **6.25 nM**
- `251013_007.frd`: 12 antibodies @ **3.125 nM**
- `251013_008.frd`: 12 antibodies @ **0.0 nM** (REFERENCE)

**Files 009-016:** Second set of 12 antibodies across 8 concentrations
- `251013_009.frd`: 12 antibodies @ **200.0 nM**
- `251013_010.frd`: 12 antibodies @ **100.0 nM**
- `251013_011.frd`: 12 antibodies @ **50.0 nM**
- `251013_012.frd`: 12 antibodies @ **25.0 nM**
- `251013_013.frd`: 12 antibodies @ **12.5 nM**
- `251013_014.frd`: 12 antibodies @ **6.25 nM**
- `251013_015.frd`: 12 antibodies @ **3.125 nM**
- `251013_016.frd`: 12 antibodies @ **0.0 nM** (REFERENCE)

## Antibodies (24 total)

**First 12 antibodies** (in files 001-008):
1. SI-157C11_P5158
2. SI-157C12_P5159
3. SI-157C15_P5235
4. SI-157C16_P5236
5. SI-83X1_P5364
6. SI-157C19_P5365
7. SI-157X47_P5533
8. SI-157X56_P5534
9. SI-157X61_P5535
10. SI-157X62_P5536
11. SI-157X49_P5563
12. SI-157X50_P5564

**Second 12 antibodies** (in files 009-016):
13. SI-157C13_P5198
14. SI-157C14_P5199
15. SI-157C17_P5237
16. SI-157C18_P5317
17. SI-157X53_P5565
18. SI-157X57_P5566
19. SI-157X63_P5537
20. SI-157X64_P5538
21. SI-157X65_P5567
22. SI-157X66_P5568
23. SI-157X67_P5569
24. SI-157X68_P5570

## Concentration Series (8 levels)

Each antibody was tested at 8 concentrations:
- 200.0 nM (highest)
- 100.0 nM
- 50.0 nM
- 25.0 nM
- 12.5 nM
- 6.25 nM
- 3.125 nM
- **0.0 nM** (buffer/reference - no analyte)

## Reference Wells

The **0.0 nM concentration** represents buffer-only measurements (no analyte).
These are used for reference subtraction to remove:
- Instrument drift
- Non-specific binding
- Baseline fluctuations

**Import strategy:**
- Import all 192 sensors (24 × 8)
- Mark sensors with concentration = 0.0 nM as `is_reference=True`
- In dashboard, allow user to select reference sensor for subtraction

## Analyte

All experiments test binding to: **hsCD3d/e_Acro_CDD-H52W1**

## Steps in Each Cycle

1. **Loading**: Load antibody onto sensor (~120s)
2. **Baseline**: Equilibrate in buffer (~100s)
3. **Association**: Expose to analyte (~180s)
4. **Dissociation**: Return to buffer (~300s)

Total time per cycle: ~700 seconds

## Data Points

Each complete cycle contains:
- Loading: ~600 points
- Baseline: ~500 points
- Association: ~900 points
- Dissociation: ~1500 points
- **Total: ~3500 points per sensor**

For 192 sensors: **~672,000 total time series points**

## Next Steps

1. ✅ Verify mapping in `FRD_Analysis.xlsx`
2. Import all 192 sensors to database
3. Add `is_reference` field to OctetSensorData model
4. Mark 0.0 nM sensors as references
5. Implement reference subtraction in dashboard
6. Shift time axis so Association starts at t=0
7. Add data downsampling for plotting performance
