"""
Analyze FRD File Structure and Create Mapping

This script analyzes all FRD files to understand:
1. How many cycles are in each FRD file
2. Which antibodies are in which cycles
3. What concentrations are tested
4. How sensor locations map to antibodies

Outputs to Excel for verification before import.
"""

import sys
from pathlib import Path
import pandas as pd

# Import FRD parser
kinetic_analysis_path = Path(__file__).parent / 'kinetic_analysis'
sys.path.insert(0, str(kinetic_analysis_path))
from frd_parser import FRDParser

# Import HT settings parser
from parse_ht_settings import parse_ht_settings


def analyze_all_frds(frd_directory):
    """Analyze all FRD files and create mapping"""
    frd_dir = Path(frd_directory)
    frd_files = sorted(frd_dir.glob("*.frd"))

    print(f"Analyzing {len(frd_files)} FRD files...")
    print("=" * 80)

    all_data = []

    for frd_idx, frd_file in enumerate(frd_files, 1):
        print(f"\n[{frd_idx}/{len(frd_files)}] {frd_file.name}")

        try:
            parser = FRDParser(str(frd_file))
            cycles = parser.get_all_cycles()

            print(f"  Cycles found: {len(cycles)}")

            for cycle_idx, cycle in enumerate(cycles, 1):
                antibody_id = cycle['antibody_id']
                analyte_id = cycle['analyte_id']
                concentration_nm = cycle['concentration_nm']

                # Extract step details
                loading_step = cycle.get('loading_step', {})
                baseline_step = cycle.get('baseline_step', {})
                assoc_step = cycle.get('association_step', {})
                dissoc_step = cycle.get('dissociation_step', {})

                # Count data points in each step
                loading_points = len(loading_step.get('time_array', [])) if loading_step else 0
                baseline_points = len(baseline_step.get('time_array', [])) if baseline_step else 0
                assoc_points = len(assoc_step.get('time_array', [])) if assoc_step else 0
                dissoc_points = len(dissoc_step.get('time_array', [])) if dissoc_step else 0

                # Get time range
                if assoc_step and 'time_array' in assoc_step:
                    assoc_time = assoc_step['time_array']
                    time_start = assoc_time[0] if len(assoc_time) > 0 else 0
                    time_end = assoc_time[-1] if len(assoc_time) > 0 else 0
                else:
                    time_start = 0
                    time_end = 0

                # Get sample IDs and well locations from steps
                loading_sample = loading_step.get('sample_id', antibody_id) if loading_step else antibody_id
                baseline_sample = baseline_step.get('sample_id', '') if baseline_step else ''
                assoc_sample = assoc_step.get('sample_id', analyte_id) if assoc_step else analyte_id

                # Extract well locations (combine row + location number)
                # sample_row = 'A', sample_location = 5 -> 'A5'
                loading_well = None
                if loading_step:
                    row = loading_step.get('sample_row', '')
                    loc = loading_step.get('sample_location', '')
                    if row and loc:
                        loading_well = f"{row}{loc}"

                baseline_well = None
                if baseline_step:
                    row = baseline_step.get('sample_row', '')
                    loc = baseline_step.get('sample_location', '')
                    if row and loc:
                        baseline_well = f"{row}{loc}"

                assoc_well = None
                if assoc_step:
                    row = assoc_step.get('sample_row', '')
                    loc = assoc_step.get('sample_location', '')
                    if row and loc:
                        assoc_well = f"{row}{loc}"

                dissoc_well = None
                if dissoc_step:
                    row = dissoc_step.get('sample_row', '')
                    loc = dissoc_step.get('sample_location', '')
                    if row and loc:
                        dissoc_well = f"{row}{loc}"

                data_row = {
                    'FRD_File': frd_file.name,
                    'FRD_Number': frd_idx,
                    'Cycle_Number': cycle_idx,
                    'Antibody_ID': antibody_id,
                    'Analyte_ID': analyte_id,
                    'Concentration_nM': concentration_nm,
                    'Loading_Sample': loading_sample,
                    'Loading_Well': loading_well,
                    'Baseline_Sample': baseline_sample,
                    'Baseline_Well': baseline_well,
                    'Association_Sample': assoc_sample,
                    'Association_Well': assoc_well,
                    'Dissociation_Well': dissoc_well,
                    'Is_Reference': concentration_nm == 0.0,
                    'Loading_Points': loading_points,
                    'Baseline_Points': baseline_points,
                    'Association_Points': assoc_points,
                    'Dissociation_Points': dissoc_points,
                    'Total_Points': loading_points + baseline_points + assoc_points + dissoc_points,
                    'Assoc_Time_Start': time_start,
                    'Assoc_Time_End': time_end,
                }

                all_data.append(data_row)

                if cycle_idx <= 3:  # Show first 3 cycles
                    print(f"    Cycle {cycle_idx}: {antibody_id} @ {concentration_nm} nM")

        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    return pd.DataFrame(all_data)


def create_sensor_mapping(df):
    """Create sensor mapping from analyzed data"""

    # Group by antibody and concentration to create unique sensors
    sensor_map = []

    for (antibody, conc), group in df.groupby(['Antibody_ID', 'Concentration_nM']):
        # Use first occurrence for this antibody/concentration
        first_row = group.iloc[0]

        sensor_map.append({
            'Antibody_ID': antibody,
            'Concentration_nM': conc,
            'FRD_File': first_row['FRD_File'],
            'Cycle_Number': first_row['Cycle_Number'],
            'Analyte_ID': first_row['Analyte_ID'],
            'Total_Points': first_row['Total_Points'],
        })

    return pd.DataFrame(sensor_map)


def analyze_concentrations(df):
    """Analyze concentration series"""

    conc_summary = []

    for antibody in df['Antibody_ID'].unique():
        ab_data = df[df['Antibody_ID'] == antibody]
        concentrations = sorted(ab_data['Concentration_nM'].unique())

        conc_summary.append({
            'Antibody_ID': antibody,
            'Num_Concentrations': len(concentrations),
            'Concentrations': ', '.join([f'{c:.1f}' for c in concentrations]),
            'Min_Conc': min(concentrations),
            'Max_Conc': max(concentrations),
        })

    return pd.DataFrame(conc_summary)


def main():
    """Main analysis function"""

    frd_dir = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292"

    print("\n" + "=" * 80)
    print("FRD STRUCTURE ANALYSIS")
    print("=" * 80)

    # Analyze all FRD files
    df_all = analyze_all_frds(frd_dir)

    # Create summaries
    print("\n" + "=" * 80)
    print("CREATING SUMMARIES")
    print("=" * 80)

    df_sensor_map = create_sensor_mapping(df_all)
    df_conc_summary = analyze_concentrations(df_all)

    # Print summary statistics
    print(f"\nTotal FRD files: {df_all['FRD_File'].nunique()}")
    print(f"Total cycles: {len(df_all)}")
    print(f"Unique antibodies: {df_all['Antibody_ID'].nunique()}")
    print(f"Unique concentrations: {df_all['Concentration_nM'].nunique()}")
    print(f"Unique sensors (antibody × concentration): {len(df_sensor_map)}")

    print("\nConcentrations found:")
    for conc in sorted(df_all['Concentration_nM'].unique()):
        count = len(df_all[df_all['Concentration_nM'] == conc])
        print(f"  {conc:6.1f} nM: {count:3d} cycles")

    print("\nAntibodies found:")
    for ab in sorted(df_all['Antibody_ID'].unique()):
        count = len(df_all[df_all['Antibody_ID'] == ab]['Concentration_nM'].unique())
        print(f"  {ab}: {count} concentrations")

    # Parse HTSettings for processing parameters
    ht_settings_path = Path(frd_dir) / "HTSettings.efrd"
    ht_settings = {}

    if ht_settings_path.exists():
        print(f"\nParsing HTSettings.efrd...")
        ht_settings = parse_ht_settings(str(ht_settings_path))
        print(f"  Binding Model: {ht_settings.get('binding_model')}")
        print(f"  Association: {ht_settings.get('assoc_start_time')}-{ht_settings.get('assoc_end_time')} s")
        print(f"  Dissociation: {ht_settings.get('dissoc_start_time')}-{ht_settings.get('dissoc_end_time')} s")
    else:
        print(f"\nWARNING: HTSettings.efrd not found at {ht_settings_path}")

    # Create HTSettings dataframe
    df_ht_settings = pd.DataFrame([ht_settings])

    # Save to Excel
    output_file = Path(frd_dir) / "FRD_Analysis.xlsx"

    print(f"\n" + "=" * 80)
    print(f"SAVING TO EXCEL: {output_file.name}")
    print("=" * 80)

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Processing parameters first
        df_ht_settings.to_excel(writer, sheet_name='Processing_Parameters', index=False)

        # Then data sheets
        df_all.to_excel(writer, sheet_name='All_Cycles', index=False)
        df_sensor_map.to_excel(writer, sheet_name='Sensor_Map', index=False)
        df_conc_summary.to_excel(writer, sheet_name='Concentration_Summary', index=False)

        # Create pivot table for easy viewing
        pivot = df_all.pivot_table(
            index='Antibody_ID',
            columns='Concentration_nM',
            values='FRD_File',
            aggfunc='first'
        )
        pivot.to_excel(writer, sheet_name='Antibody_x_Concentration')

    print(f"\nAnalysis complete! Saved to {output_file}")
    print(f"\nPlease review the Excel file to verify the mapping.")
    print("\nSheets:")
    print("  - Processing_Parameters: Vendor analysis settings from HTSettings.efrd")
    print("  - All_Cycles: Complete list of all cycles in all FRD files")
    print("  - Sensor_Map: Unique sensors (antibody × concentration)")
    print("  - Concentration_Summary: Concentrations tested per antibody")
    print("  - Antibody_x_Concentration: Pivot table view")
    print("\nNew columns in All_Cycles:")
    print("  - Loading_Sample: Sample loaded onto sensor")
    print("  - Loading_Well: Well location for loading (e.g., A5, B3)")
    print("  - Baseline_Sample: Sample used for baseline")
    print("  - Baseline_Well: Well location for baseline")
    print("  - Association_Sample: Sample for association step")
    print("  - Association_Well: Well location for association (e.g., A2)")
    print("  - Dissociation_Well: Well location for dissociation")
    print("  - Is_Reference: True if concentration = 0.0 nM (buffer only)")


if __name__ == "__main__":
    main()
