"""
Summary Tables Component
Generates 4 summary tables matching the Excel template structure
"""

from dash import html, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np


def calculate_comparative_colors(values):
    """
    Calculate color scale for comparative coloring (like Excel).
    Red (worst) → Yellow (middle) → Green (best)

    Args:
        values: List of numeric values

    Returns:
        List of RGB color tuples
    """
    if not values or all(pd.isna(v) for v in values):
        return ['#ffffff'] * len(values)

    # Filter out NaN values for min/max calculation
    numeric_values = [v for v in values if not pd.isna(v)]
    if not numeric_values:
        return ['#ffffff'] * len(values)

    min_val = min(numeric_values)
    max_val = max(numeric_values)

    # If all values are the same
    if min_val == max_val:
        return ['#FFEB9C'] * len(values)  # Yellow

    colors = []
    for val in values:
        if pd.isna(val):
            colors.append('#f3f4f6')  # Gray for N/A
            continue

        # Normalize to 0-1 range
        normalized = (val - min_val) / (max_val - min_val)

        # Green to Yellow to Red color scale
        if normalized <= 0.5:
            # Green to Yellow (bottom 50%)
            ratio = normalized * 2  # 0-1
            r = int(198 + (255 - 198) * ratio)
            g = int(239 + (235 - 239) * ratio)
            b = int(206 + (156 - 206) * ratio)
        else:
            # Yellow to Red (top 50%)
            ratio = (normalized - 0.5) * 2  # 0-1
            r = int(255)
            g = int(235 - (235 - 199) * ratio)
            b = int(156 - (156 - 206) * ratio)

        colors.append(f'#{r:02x}{g:02x}{b:02x}')

    return colors


def create_single_table(title, data_df, metric_key, reverse_colors=False):
    """
    Create a single summary table with comparative color coding.

    Args:
        title: Table title
        data_df: DataFrame with molecule data
        metric_key: Key for the metric ('aggregate', 'fragment', 'monomer', 'change')
        reverse_colors: If True, flip color scale (for negative changes)

    Returns:
        html.Div with table
    """
    if data_df.empty:
        return html.Div(f"No data available for {title}",
                       style={'padding': '20px', 'textAlign': 'center', 'color': '#6b7280'})

    # No color coding - removed per user request
    style_data_conditional = []

    # Create multi-level column headers
    columns = [
        {'name': ['', 'Molecule'], 'id': 'Molecule'}
    ]

    # Add Plasma columns with grouping
    for day in ['D0', 'D3', 'D7']:
        columns.append({
            'name': ['Plasma', day],
            'id': f'Plasma {day}'
        })

    # Add Buffer columns with grouping
    for day in ['D0', 'D3', 'D7']:
        columns.append({
            'name': ['Buffer', day],
            'id': f'Buffer {day}'
        })

    # Create DataTable
    table = dash_table.DataTable(
        data=data_df.to_dict('records'),
        columns=columns,
        merge_duplicate_headers=True,
        style_table={
            'overflowX': 'auto',
            'borderRadius': '8px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'
        },
        style_header={
            'backgroundColor': '#2563eb',
            'color': 'white',
            'fontWeight': '700',
            'fontSize': '12px',
            'textAlign': 'center',
            'padding': '10px',
            'border': '1px solid #1e40af'
        },
        style_cell={
            'textAlign': 'center',
            'padding': '10px',
            'fontSize': '12px',
            'fontFamily': 'Arial, sans-serif',
            'border': '1px solid #e5e7eb',
            'minWidth': '90px',
            'maxWidth': '140px',
            'whiteSpace': 'normal',
            'height': 'auto'
        },
        style_data={
            'backgroundColor': '#ffffff',
            'color': '#1f2937'
        },
        style_data_conditional=style_data_conditional
    )

    return html.Div([
        html.H5(title, style={'fontWeight': '700', 'marginBottom': '12px', 'color': '#1f2937'}),
        table
    ], style={'marginBottom': '32px'})


def create_summary_tables(molecule_data):
    """
    Create 4 summary tables from molecule data.

    Args:
        molecule_data: Dict mapping molecule_id -> data with conditions

    Returns:
        html.Div with all 4 tables
    """
    if not molecule_data:
        return html.Div(
            "No summary data available. Please run analysis first.",
            style={'textAlign': 'center', 'padding': '40px', 'color': '#6b7280'}
        )

    # Build data for each table
    molecule_ids = list(molecule_data.keys())

    # Table 1: % Aggregate by SEC (HMW)
    aggregate_data = []
    # Table 2: % Fragment by SEC (LMW)
    fragment_data = []
    # Table 3: % Monomer by SEC
    monomer_data = []
    # Table 4: Change in % Monomer (from Buffer D0)
    change_data = []

    for mol_id in molecule_ids:
        mol_info = molecule_data[mol_id]
        conditions = mol_info.get('conditions', {})

        # Debug: Print structure for first molecule
        if mol_id == molecule_ids[0]:
            print(f"\n=== DEBUG: Data structure for {mol_id} ===")
            print(f"Conditions keys: {list(conditions.keys())}")
            for cond in conditions.keys():
                day_keys = list(conditions[cond].keys())
                print(f"  {cond} days: {day_keys}")
                print(f"  {cond} day types: {[type(k) for k in day_keys]}")
                if conditions[cond]:
                    first_day = day_keys[0]
                    print(f"    Day {first_day} (type: {type(first_day)}) keys: {list(conditions[cond][first_day].keys())}")
                    if 'peak_areas' in conditions[cond][first_day]:
                        print(f"      peak_areas keys: {list(conditions[cond][first_day]['peak_areas'].keys())}")

        # Helper function to get metric value
        def get_metric(condition, day, metric_name):
            cond_data = conditions.get(condition, {})
            # Try both integer and string keys (JSON serialization converts int keys to strings)
            day_data = cond_data.get(day, {})
            if not day_data:
                day_data = cond_data.get(str(day), {})
            if not day_data:
                return None

            # Get peak_areas if stored directly, otherwise extract from dict
            # This handles different possible data structures
            if 'peak_areas' in day_data:
                peak_areas = day_data['peak_areas']
                result = peak_areas.get(metric_name)
                # Debug first molecule
                if mol_id == molecule_ids[0] and condition == 'Buffer' and day == 0:
                    print(f"  peak_areas keys: {list(peak_areas.keys()) if isinstance(peak_areas, dict) else 'not a dict'}")
                    print(f"  Looking for '{metric_name}': {result}")
                return result
            elif metric_name in day_data:
                return day_data[metric_name]
            return None

        # Get Buffer D0 baseline for monomer change calculation
        buffer_d0_monomer = get_metric('Buffer', 0, 'monomer_pct')

        # Build row for each table
        aggregate_row = {'Molecule': mol_id}
        fragment_row = {'Molecule': mol_id}
        monomer_row = {'Molecule': mol_id}
        change_row = {'Molecule': mol_id}

        for day in [0, 3, 7]:
            # Plasma values
            plasma_agg = get_metric('Plasma', day, 'hmw_pct')
            plasma_frag = get_metric('Plasma', day, 'lmw_pct')
            plasma_mono = get_metric('Plasma', day, 'monomer_pct')

            # Buffer values
            buffer_agg = get_metric('Buffer', day, 'hmw_pct')
            buffer_frag = get_metric('Buffer', day, 'lmw_pct')
            buffer_mono = get_metric('Buffer', day, 'monomer_pct')

            # Format values
            def fmt(val):
                return f"{val:.1f}%" if val is not None else 'N/A'

            aggregate_row[f'Plasma D{day}'] = fmt(plasma_agg)
            aggregate_row[f'Buffer D{day}'] = fmt(buffer_agg)

            fragment_row[f'Plasma D{day}'] = fmt(plasma_frag)
            fragment_row[f'Buffer D{day}'] = fmt(buffer_frag)

            monomer_row[f'Plasma D{day}'] = fmt(plasma_mono)
            monomer_row[f'Buffer D{day}'] = fmt(buffer_mono)

            # Calculate change from baseline
            if plasma_mono is not None and buffer_d0_monomer is not None:
                change = plasma_mono - buffer_d0_monomer
                change_row[f'Plasma D{day}'] = f"{change:+.1f}%"
            else:
                change_row[f'Plasma D{day}'] = 'N/A'

            if buffer_mono is not None and buffer_d0_monomer is not None:
                change = buffer_mono - buffer_d0_monomer
                change_row[f'Buffer D{day}'] = f"{change:+.1f}%"
            else:
                change_row[f'Buffer D{day}'] = 'N/A'

        aggregate_data.append(aggregate_row)
        fragment_data.append(fragment_row)
        monomer_data.append(monomer_row)
        change_data.append(change_row)

    # Create DataFrames
    aggregate_df = pd.DataFrame(aggregate_data)
    fragment_df = pd.DataFrame(fragment_data)
    monomer_df = pd.DataFrame(monomer_data)
    change_df = pd.DataFrame(change_data)

    # Reorder columns
    col_order = ['Molecule', 'Plasma D0', 'Plasma D3', 'Plasma D7', 'Buffer D0', 'Buffer D3', 'Buffer D7']
    aggregate_df = aggregate_df[col_order]
    fragment_df = fragment_df[col_order]
    monomer_df = monomer_df[col_order]
    change_df = change_df[col_order]

    # Create tables
    table_hmw = create_single_table("% Aggregate by SEC (HMW)", aggregate_df, 'aggregate')
    table_monomer = create_single_table("% Monomer by SEC", monomer_df, 'monomer')
    table_lmw = create_single_table("% Fragment by SEC (LMW)", fragment_df, 'fragment')
    table_change = create_single_table("Change in % Monomer (from Buffer D0 Baseline)", change_df, 'change', reverse_colors=True)

    # Create Sample ID detail table
    sample_id_table = create_sample_id_table(molecule_data)

    # Combine all tables - reordered: HMW, Monomer, LMW, Change
    return html.Div([
        html.Div([
            html.H4("Summary Tables", style={'fontWeight': '700', 'marginBottom': '8px'}),
            html.P(
                "All tables use Buffer Day 0 as baseline.",
                style={'fontSize': '13px', 'color': '#6b7280', 'marginBottom': '24px'}
            )
        ]),
        table_hmw,
        table_monomer,
        table_lmw,
        table_change,
        html.Hr(style={'margin': '40px 0', 'border': '1px solid #e5e7eb'}),
        sample_id_table
    ])


def create_sample_id_table(molecule_data):
    """
    Create a table showing sample IDs with all peak data for each molecule/condition/timepoint

    Args:
        molecule_data: Dict mapping molecule_id -> data with conditions

    Returns:
        html.Div with sample ID table
    """
    if not molecule_data:
        return html.Div()

    # Build table data
    table_rows = []

    for mol_id in sorted(molecule_data.keys()):
        mol_info = molecule_data[mol_id]
        conditions = mol_info.get('conditions', {})

        for condition_name in sorted(conditions.keys()):
            cond_data = conditions[condition_name]

            # Handle both integer and string day keys
            day_keys = list(cond_data.keys())
            for day_key in sorted(day_keys, key=lambda x: int(x) if isinstance(x, int) else int(x) if x.isdigit() else 0):
                day_data = cond_data[day_key]

                result_id = day_data.get('result_id', 'N/A')
                day = day_data.get('day', day_key)
                peak_areas = day_data.get('peak_areas', {})

                # Calculate section peak RTs (midpoint of region)
                hmw_start = peak_areas.get('hmw_start', 0)
                hmw_end = peak_areas.get('hmw_end', 0)
                hmw_section_rt = (hmw_start + hmw_end) / 2 if hmw_start and hmw_end else 0

                lmw_start = peak_areas.get('lmw_start', 0)
                lmw_end = peak_areas.get('lmw_end', 0)
                lmw_section_rt = (lmw_start + lmw_end) / 2 if lmw_start and lmw_end else 0

                # Format peak data with separate columns for start/stop times
                table_rows.append({
                    'Molecule': mol_id,
                    'Condition': condition_name,
                    'Day': f'D{day}',
                    'Result ID': result_id,
                    # HMW data
                    'HMW %': f"{peak_areas.get('hmw_pct', 0):.1f}%",
                    'HMW Section Peak RT (min)': f"{hmw_section_rt:.2f}",
                    'HMW Start (min)': f"{hmw_start:.2f}",
                    'HMW Stop (min)': f"{hmw_end:.2f}",
                    'HMW Area': f"{peak_areas.get('hmw_area', 0):.2f}",
                    # Monomer data
                    'Monomer %': f"{peak_areas.get('monomer_pct', 0):.1f}%",
                    'Monomer RT (min)': f"{peak_areas.get('main_rt', 0):.2f}",
                    'Monomer Start (min)': f"{peak_areas.get('main_start', 0):.2f}",
                    'Monomer Stop (min)': f"{peak_areas.get('main_end', 0):.2f}",
                    'Monomer Area': f"{peak_areas.get('main_peak_area', 0):.2f}",
                    # LMW data
                    'LMW %': f"{peak_areas.get('lmw_pct', 0):.1f}%",
                    'LMW Section Peak RT (min)': f"{lmw_section_rt:.2f}",
                    'LMW Start (min)': f"{lmw_start:.2f}",
                    'LMW Stop (min)': f"{lmw_end:.2f}",
                    'LMW Area': f"{peak_areas.get('lmw_area', 0):.2f}",
                    # Total
                    'Total Area': f"{peak_areas.get('total_area', 0):.2f}"
                })

    if not table_rows:
        return html.Div()

    # Create DataFrame
    df = pd.DataFrame(table_rows)

    # Create DataTable
    table = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in df.columns],
        style_table={
            'overflowX': 'auto',
            'borderRadius': '8px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'
        },
        style_header={
            'backgroundColor': '#10b981',
            'color': 'white',
            'fontWeight': '700',
            'fontSize': '11px',
            'textAlign': 'center',
            'padding': '10px',
            'border': '1px solid #059669'
        },
        style_cell={
            'textAlign': 'center',
            'padding': '8px',
            'fontSize': '11px',
            'fontFamily': 'Arial, sans-serif',
            'border': '1px solid #e5e7eb',
            'minWidth': '80px',
            'maxWidth': '150px',
            'whiteSpace': 'normal',
            'height': 'auto'
        },
        style_data={
            'backgroundColor': '#ffffff',
            'color': '#1f2937'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f9fafb'
            }
        ],
        page_size=20,
        sort_action='native',
        filter_action='native'
    )

    return html.Div([
        html.H5("Detailed Sample Data by Molecule", style={'fontWeight': '700', 'marginBottom': '12px', 'marginTop': '24px', 'color': '#1f2937'}),
        html.P(
            "Complete peak analysis data for all samples, sorted by molecule, condition, and timepoint.",
            style={'fontSize': '13px', 'color': '#6b7280', 'marginBottom': '16px'}
        ),
        table
    ], style={'marginBottom': '32px'})
