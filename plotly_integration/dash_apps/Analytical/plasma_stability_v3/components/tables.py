"""
Table Components
Create monomer % summary tables
"""

from dash import dash_table
from typing import Dict, List


def create_results_table(conditions_data: Dict[str, List[Dict]]) -> dash_table.DataTable:
    """
    Create results table showing monomer % for each condition and timepoint

    Args:
        conditions_data: Dict mapping condition name to list of sample data

    Returns:
        DataTable component
    """
    # Collect all unique days across all conditions
    all_days = set()
    for samples in conditions_data.values():
        for sample in samples:
            all_days.add(sample['day'])

    days_sorted = sorted(list(all_days))

    # Build table data
    table_data = []
    for condition in sorted(conditions_data.keys()):
        row = {'Condition': condition}
        samples = conditions_data.get(condition, [])

        for day in days_sorted:
            day_label = f'D{day}'

            # Find matching sample for this day
            matching = [s for s in samples if s['day'] == day]

            if matching and matching[0].get('peak_areas'):
                monomer_pct = matching[0]['peak_areas']['monomer_pct']
                row[day_label] = f"{monomer_pct:.1f}%"
            else:
                row[day_label] = "N/A"

        table_data.append(row)

    # Build columns
    columns = [{'name': 'Condition', 'id': 'Condition'}]
    for day in days_sorted:
        day_label = f'D{day}'
        columns.append({'name': day_label, 'id': day_label})

    # Create DataTable
    return dash_table.DataTable(
        columns=columns,
        data=table_data,
        style_cell={
            'textAlign': 'center',
            'padding': '14px 16px',
            'fontSize': '14px',
            'border': '1px solid #e5e7eb',
            'fontWeight': '600',
            'fontFamily': 'Arial, sans-serif'
        },
        style_header={
            'backgroundColor': '#f3f4f6',
            'fontWeight': '700',
            'color': '#374151',
            'border': '1px solid #d1d5db',
            'fontSize': '14px',
            'textTransform': 'uppercase',
            'letterSpacing': '0.5px'
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'Condition'},
                'fontWeight': '700',
                'textAlign': 'left',
                'backgroundColor': '#f9fafb',
                'borderRight': '2px solid #d1d5db'
            },
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#fafafa'
            }
        ],
        style_cell_conditional=[
            {'if': {'column_id': 'Condition'}, 'width': '180px', 'minWidth': '180px'}
        ],
        style_table={
            'overflowX': 'auto',
            'borderRadius': '8px',
            'border': '2px solid #e5e7eb'
        }
    )
