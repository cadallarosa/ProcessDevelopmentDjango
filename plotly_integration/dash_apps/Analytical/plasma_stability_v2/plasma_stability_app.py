"""
Plasma Stability SEC Analysis App - Updated
Track protein stability in plasma vs buffer over time
"""

from django_plotly_dash import DjangoDash
from dash import callback, Input, Output, State, no_update, html, dcc, dash_table
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import io
from datetime import datetime
import dash_bootstrap_components as dbc

from .layout import app_layout
from plotly_integration.models import SampleMetadata, TimeSeriesData, PeakResults, SystemInformation

# Create the Dash app with Bootstrap components
app = DjangoDash("PlasmaStabilityAppV2", external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = app_layout


# ==================== HELPER FUNCTIONS ====================

def calculate_monomer_from_empower(result_id, main_peak_rt=7.843, lmw_cutoff=12):
    """Calculate monomer % using Empower PeakResults"""
    try:
        sample = SampleMetadata.objects.filter(result_id=result_id).first()
        if not sample:
            return None

        system_name = sample.system_name
        system = SystemInformation.objects.filter(system_name=system_name).first()
        if not system:
            return None

        channel_name = system.channel_1
        peak_results = PeakResults.objects.filter(
            result_id=result_id, channel_name=channel_name, system_name=system_name
        )

        if not peak_results.exists():
            return None

        df = pd.DataFrame.from_records(peak_results.values())
        df['peak_retention_time'] = pd.to_numeric(df['peak_retention_time'], errors='coerce')
        df = df.dropna(subset=['peak_retention_time'])
        df['area'] = df['area'].astype(float)
        df['peak_start_time'] = df['peak_start_time'].astype(float)
        df['peak_end_time'] = df['peak_end_time'].astype(float)

        main_peak_index = (df['peak_retention_time'] - main_peak_rt).abs().idxmin()
        main_peak_row = df.loc[main_peak_index]
        main_peak_area = round(main_peak_row['area'], 2)
        main_peak_start = main_peak_row['peak_start_time']
        main_peak_end = main_peak_row['peak_end_time']

        df_excluding_main = df.drop(index=main_peak_index)

        hmw_area = round(df_excluding_main[df_excluding_main['peak_retention_time'] < main_peak_rt]['area'].sum(), 2)
        lmw_area = round(df_excluding_main[
            (df_excluding_main['peak_retention_time'] > main_peak_rt) &
            (df_excluding_main['peak_retention_time'] <= lmw_cutoff)
        ]['area'].sum(), 2)

        total_area = main_peak_area + hmw_area + lmw_area
        monomer_percent = round((main_peak_area / total_area) * 100, 2) if total_area > 0 else 0

        return {
            'monomer_pct': monomer_percent,
            'hmw_pct': round((hmw_area / total_area) * 100, 2) if total_area > 0 else 0,
            'lmw_pct': round((lmw_area / total_area) * 100, 2) if total_area > 0 else 0,
            'main_start': main_peak_start,
            'main_end': main_peak_end,
            'hmw_start': df['peak_start_time'].min(),
            'hmw_end': main_peak_start,
            'lmw_start': main_peak_end,
            'lmw_end': min(df['peak_end_time'].max(), lmw_cutoff)
        }
    except Exception as e:
        print(f"Error calculating monomer for {result_id}: {e}")
        return None


def fetch_time_series_data(id_value, id_type):
    """Fetch time series data for plotting"""
    try:
        if id_type == 'result_id':
            sample = SampleMetadata.objects.filter(result_id=id_value).first()
        else:
            sample = SampleMetadata.objects.filter(sample_name=id_value).first()

        if not sample:
            return None, None

        time_series = TimeSeriesData.objects.filter(result_id=sample.injection_id)
        df = pd.DataFrame(list(time_series.values()))

        if df.empty:
            return None, None

        return sample, df
    except Exception as e:
        print(f"Error fetching data for {id_value}: {e}")
        return None, None


# ==================== CONDITION & MATRIX MANAGEMENT ====================

@app.callback(
    [Output('matrix-table-container', 'children'),
     Output('conditions-store', 'data')],
    Input('update-conditions-btn', 'n_clicks'),
    [State('conditions-input', 'value'),
     State('conditions-store', 'data'),
     State('matrix-table-container', 'children')],
    prevent_initial_call=False
)
def update_matrix_table(update_clicks, conditions_text, current_conditions, current_table):
    """Update matrix table based on conditions"""
    from dash import callback_context

    # Parse conditions
    conditions = [c.strip() for c in conditions_text.split(',') if c.strip()] if conditions_text else ['Plasma', 'Buffer']

    # Get current table data if exists
    current_data = []
    if current_table and isinstance(current_table, dict) and current_table.get('props'):
        table_props = current_table['props']
        if 'children' in table_props and isinstance(table_props['children'], dict):
            current_data = table_props['children'].get('props', {}).get('data', [])

    # Generate new matrix with default timepoints on update or initial load
    trigger = callback_context.triggered[0]['prop_id'].split('.')[0] if callback_context.triggered else None

    if trigger == 'update-conditions-btn' or not current_data:
        # Generate new matrix with default timepoints
        current_data = [
            {'day_number': 0, **{cond: '' for cond in conditions}},
            {'day_number': 3, **{cond: '' for cond in conditions}},
            {'day_number': 7, **{cond: '' for cond in conditions}}
        ]

    # Create table columns
    columns = [{'name': 'Day #', 'id': 'day_number', 'type': 'numeric', 'editable': True}]
    for cond in conditions:
        columns.append({'name': f'{cond} (ID)', 'id': cond, 'type': 'text', 'editable': True})

    # Create DataTable with add/delete rows
    table = html.Div([
        html.Label("Sample Configuration Matrix (click 'Add Row' to add timepoints, 'x' to delete rows):",
                   style={'fontWeight': '600', 'marginBottom': '10px', 'display': 'block', 'fontSize': '14px', 'color': '#374151'}),
        dash_table.DataTable(
            id='config-matrix-table',
            columns=columns,
            data=current_data,
            editable=True,
            row_deletable=True,
            row_selectable=False,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'center',
                'padding': '16px',
                'fontSize': '14px',
                'fontFamily': 'system-ui',
                'border': '1px solid #e5e7eb',
                'minWidth': '150px'
            },
            style_header={
                'backgroundColor': '#2563eb',
                'color': 'white',
                'fontWeight': '700',
                'fontSize': '14px',
                'textTransform': 'uppercase',
                'letterSpacing': '0.5px'
            },
            style_data={
                'backgroundColor': 'white',
                'color': '#374151'
            },
            style_data_conditional=[
                {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9fafb'},
                {'if': {'column_id': 'day_number'}, 'fontWeight': '700', 'color': '#2563eb'}
            ],
            page_action='none'
        ),
        html.Button("➕ Add Row", id='add-row-btn', n_clicks=0, style={
            'backgroundColor': '#10b981',
            'color': 'white',
            'border': 'none',
            'padding': '8px 16px',
            'fontSize': '13px',
            'cursor': 'pointer',
            'borderRadius': '6px',
            'fontWeight': '600',
            'marginTop': '10px'
        })
    ])

    return table, conditions


@app.callback(
    Output('config-matrix-table', 'data'),
    Input('add-row-btn', 'n_clicks'),
    [State('config-matrix-table', 'data'),
     State('conditions-store', 'data')],
    prevent_initial_call=True
)
def add_row(n_clicks, current_data, conditions):
    """Add a new row to the matrix table"""
    if not current_data:
        current_data = []

    # Get the next day number
    existing_days = [row.get('day_number', 0) for row in current_data if isinstance(row, dict) and row.get('day_number') is not None]
    next_day = max(existing_days) + 1 if existing_days else 0

    # Create new row
    new_row = {'day_number': next_day}
    for cond in conditions:
        new_row[cond] = ''

    current_data.append(new_row)
    return current_data


@app.callback(
    [Output('stability-config-store', 'data'),
     Output('id-type-store-ps', 'data')],
    [Input('config-matrix-table', 'data'),
     Input('id-type-dropdown-ps', 'value')],
    prevent_initial_call=False
)
def update_stores(table_data, id_type):
    """Update data stores"""
    return table_data or [], id_type


# ==================== MODAL CONTROL ====================

@app.callback(
    Output('config-modal', 'is_open'),
    [Input('open-config-modal-btn', 'n_clicks'),
     Input('generate-analysis-btn', 'n_clicks')],
    [State('config-modal', 'is_open')],
    prevent_initial_call=True
)
def toggle_modal(open_clicks, generate_clicks, is_open):
    """Open modal with configure button, close with generate analysis"""
    from dash import callback_context

    if not callback_context.triggered:
        return is_open

    trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'open-config-modal-btn':
        return True
    elif trigger_id == 'generate-analysis-btn':
        return False

    return is_open


# ==================== MAIN ANALYSIS ====================

@app.callback(
    [Output('sec-plots-section', 'children'),
     Output('results-section', 'children'),
     Output('monomer-data-store', 'data'),
     Output('project-id-store', 'data')],
    Input('generate-analysis-btn', 'n_clicks'),
    [State('stability-config-store', 'data'),
     State('conditions-store', 'data'),
     State('id-type-store-ps', 'data'),
     State('project-id-input', 'value'),
     State('channel-checklist-ps', 'value'),
     State('peak-options-ps', 'value'),
     State('table-data-options', 'value')],
    prevent_initial_call=True
)
def generate_analysis(n_clicks, config_data, conditions, id_type, project_id, channels,
                     peak_options, table_data_options):
    """Generate complete stability analysis"""

    print("=" * 50)
    print("GENERATE ANALYSIS CALLED")
    print(f"Config data: {config_data}")
    print(f"Conditions: {conditions}")
    print(f"ID Type: {id_type}")
    print(f"Project ID: {project_id}")
    print(f"Channels: {channels}")
    print(f"Peak options: {peak_options}")
    print(f"Table data options: {table_data_options}")
    print("=" * 50)

    if not config_data or not conditions:
        print("No config data or conditions - preventing update")
        raise PreventUpdate

    # Filter out empty rows
    config_data = [row for row in config_data if any(row.get(cond) for cond in conditions)]

    project_id_display = project_id or "No Project ID"

    # Default table orientation
    table_orientation = 'day_rows'

    if not config_data:
        print("No valid config data after filtering")
        return (
            html.Div(),  # Empty plots section
            html.Div(),  # Empty results section
            [],
            project_id or ""
        )

    # Sort by day number
    config_data = sorted(config_data, key=lambda x: x.get('day_number', 0))

    # Collect data by condition
    condition_data = {cond: [] for cond in conditions}
    results_data = []

    print(f"Processing {len(config_data)} rows...")
    for row in config_data:
        day = row.get('day_number', 0)
        result_entry = {'day': day}
        print(f"\nProcessing Day {day}:")

        for condition in conditions:
            id_value = row.get(condition, '').strip()
            print(f"  {condition}: {id_value}")
            if id_value:
                sample, df = fetch_time_series_data(id_value, id_type)
                if sample and df is not None:
                    print(f"    ✓ Found sample data")
                    result_id = sample.result_id if id_type == 'sample_id' else id_value
                    peak_data = calculate_monomer_from_empower(result_id)
                    if peak_data:
                        print(f"    ✓ Calculated peaks: Monomer={peak_data['monomer_pct']}%")
                        condition_data[condition].append({
                            'day': day,
                            'sample': sample,
                            'df': df,
                            'peak_data': peak_data,
                            'label': f"D{day}"
                        })
                        result_entry[f'{condition}_monomer'] = peak_data['monomer_pct']
                        result_entry[f'{condition}_hmw'] = peak_data['hmw_pct']
                        result_entry[f'{condition}_lmw'] = peak_data['lmw_pct']
                    else:
                        print(f"    ✗ No peak data found")
                else:
                    print(f"    ✗ No sample/timeseries data found")

        results_data.append(result_entry)

    print(f"\nTotal samples collected: {sum(len(v) for v in condition_data.values())}")

    # Generate SEC plots (side by side for each condition)
    sec_plots_content = create_multi_condition_plots(
        condition_data, project_id or "SI-XXXXX",
        channels or ['channel_1'],
        'shading' in (peak_options or []),
        'percentages' in (peak_options or [])
    )

    # Wrap plots in a card with Project ID title
    sec_plots_section = html.Div(
        style={
            'backgroundColor': 'white',
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 4px 12px rgba(0,0,0,0.08)'
        },
        children=[
            html.H3(project_id_display, style={
                'margin': '0 0 20px 0',
                'color': '#374151',
                'fontSize': '24px',
                'fontWeight': '700'
            }),
            sec_plots_content
        ]
    )

    # Generate results table
    results_table = create_results_table(
        results_data, conditions, table_orientation, table_data_options or ['monomer']
    )

    # Generate trend plot
    trend_fig = create_trend_plot(results_data, conditions, project_id or "SI-XXXXX", table_data_options or ['monomer'])

    # Create results section with trend plot and table
    results_section = html.Div(
        style={
            'backgroundColor': 'white',
            'borderRadius': '16px',
            'padding': '24px',
            'boxShadow': '0 4px 12px rgba(0,0,0,0.08)'
        },
        children=[
            # Header with table orientation toggle and export
            html.Div(
                style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '24px'},
                children=[
                    html.H3("Analysis Results", style={
                        'margin': '0',
                        'color': '#374151',
                        'fontSize': '22px',
                        'fontWeight': '700'
                    }),
                    html.Div(
                        style={'display': 'flex', 'gap': '16px', 'alignItems': 'center'},
                        children=[
                            html.Label("Table View:", style={'fontWeight': '600', 'fontSize': '14px', 'color': '#6b7280'}),
                            dcc.RadioItems(
                                id='table-orientation-toggle',
                                options=[
                                    {'label': ' Day Rows', 'value': 'day_rows'},
                                    {'label': ' Type Rows', 'value': 'type_rows'}
                                ],
                                value='day_rows',
                                inline=True,
                                labelStyle={'marginRight': '15px'},
                                style={'display': 'flex', 'alignItems': 'center'}
                            ),
                            html.Button("📥 Export", id='export-data-btn', style={
                                'backgroundColor': '#059669',
                                'color': 'white',
                                'border': 'none',
                                'padding': '8px 16px',
                                'fontSize': '14px',
                                'cursor': 'pointer',
                                'borderRadius': '6px',
                                'fontWeight': '600',
                                'boxShadow': '0 2px 6px rgba(5, 150, 105, 0.3)'
                            })
                        ]
                    )
                ]
            ),
            # Trend Plot (full width on top)
            html.Div([
                html.H4("Stability Trend", style={
                    'margin': '0 0 16px 0',
                    'color': '#374151',
                    'fontSize': '18px',
                    'fontWeight': '600'
                }),
                dcc.Graph(
                    id='trend-plot',
                    figure=trend_fig,
                    config={'displayModeBar': True, 'displaylogo': False},
                    style={'marginBottom': '24px'}
                )
            ]),
            # Data Table (full width below trend)
            html.Div([
                html.H4("Data Summary", style={
                    'margin': '0 0 16px 0',
                    'color': '#374151',
                    'fontSize': '18px',
                    'fontWeight': '600'
                }),
                results_table
            ])
        ]
    )

    return sec_plots_section, results_section, results_data, project_id or ""


def create_multi_condition_plots(condition_data, project_id, channels, show_shading, show_percentages):
    """Create 2-column grid of plots for all conditions"""
    plots = []
    # Professional matplotlib-style color palette
    timepoint_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

    for condition, data_list in condition_data.items():
        if not data_list:
            continue

        fig = create_single_sec_plot(
            data_list, condition,  # Just the condition name, no "Stability -" prefix
            timepoint_colors, channels, show_shading, show_percentages
        )

        plots.append(
            html.Div([
                dcc.Graph(figure=fig, config={'displayModeBar': True, 'displaylogo': False})
            ])
        )

    if not plots:
        return html.Div("No data available", style={'textAlign': 'center', 'padding': '40px', 'color': '#6b7280'})

    # 2-column grid layout
    return html.Div(
        plots,
        style={
            'display': 'grid',
            'gridTemplateColumns': 'repeat(2, 1fr)',
            'gap': '20px',
            'justifyItems': 'center'
        }
    )


def create_single_sec_plot(data_list, title, colors, channels, show_shading, show_percentages):
    """Create a single SEC chromatogram (wider format for better visibility)"""
    fig = go.Figure()

    region_colors = {
        "HMW": "rgba(255, 87, 87, 0.2)",
        "Main": "rgba(72, 149, 239, 0.2)",
        "LMW": "rgba(122, 230, 160, 0.2)"
    }

    for idx, item in enumerate(data_list):
        df = item['df']
        label = item['label']
        peak_data = item['peak_data']
        color = colors[idx % len(colors)]

        for channel in channels:
            if channel in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['time'], y=df[channel],
                    mode='lines', name=label,
                    line=dict(color=color, width=2.5),
                    hovertemplate=f'<b>{label}</b><br>Time: %{{x:.2f}} min<br>UV280: %{{y:.2f}}<extra></extra>'
                ))

                if show_shading and peak_data:
                    # HMW shading
                    hmw_df = df[(df['time'] >= peak_data['hmw_start']) & (df['time'] <= peak_data['hmw_end'])]
                    if not hmw_df.empty:
                        fig.add_trace(go.Scatter(
                            x=hmw_df['time'], y=hmw_df[channel],
                            fill='tozeroy', mode='none',
                            fillcolor=region_colors['HMW'],
                            showlegend=False, hoverinfo='skip'
                        ))

                    # Main Peak shading
                    main_df = df[(df['time'] >= peak_data['main_start']) & (df['time'] <= peak_data['main_end'])]
                    if not main_df.empty:
                        fig.add_trace(go.Scatter(
                            x=main_df['time'], y=main_df[channel],
                            fill='tozeroy', mode='none',
                            fillcolor=region_colors['Main'],
                            showlegend=False, hoverinfo='skip'
                        ))

                    # LMW shading
                    lmw_df = df[(df['time'] >= peak_data['lmw_start']) & (df['time'] <= peak_data['lmw_end'])]
                    if not lmw_df.empty:
                        fig.add_trace(go.Scatter(
                            x=lmw_df['time'], y=lmw_df[channel],
                            fill='tozeroy', mode='none',
                            fillcolor=region_colors['LMW'],
                            showlegend=False, hoverinfo='skip'
                        ))

                if show_percentages and peak_data:
                    max_y = df[channel].max()
                    y_pos = max_y * 0.88 - (idx * max_y * 0.08)
                    annotation_text = f"Monomer: {peak_data['monomer_pct']}%"
                    fig.add_annotation(
                        x=df['time'].mean(), y=y_pos,
                        text=annotation_text,
                        showarrow=False,
                        font=dict(size=10, color='white'),
                        bgcolor=color,
                        borderpad=6,
                        opacity=0.9
                    )

    fig.update_layout(
        title={'text': title, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 16, 'weight': 'bold', 'color': '#374151'}},
        xaxis_title="Time (minutes)",
        yaxis_title="UV280",
        template='plotly_white',
        width=1100, height=580,  # Even wider plots for better visibility
        showlegend=True,
        legend=dict(
            x=1.02, y=1,
            xanchor='left', yanchor='top',
            bgcolor='rgba(255, 255, 255, 0.95)',
            bordercolor='#d1d5db',
            borderwidth=1
        ),
        hovermode='closest',
        plot_bgcolor='white',
        margin=dict(l=60, r=120, t=60, b=60)
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#e5e7eb')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#e5e7eb')

    return fig


@app.callback(
    Output('results-section', 'children', allow_duplicate=True),
    Input('table-orientation-toggle', 'value'),
    [State('monomer-data-store', 'data'),
     State('conditions-store', 'data'),
     State('table-data-options', 'value'),
     State('project-id-store', 'data')],
    prevent_initial_call=True
)
def update_table_orientation(orientation, results_data, conditions, table_data_options, project_id):
    """Update table when orientation toggle changes"""

    print(f"\n🔄 TABLE ORIENTATION TOGGLE TRIGGERED: {orientation}")
    print(f"Results data available: {bool(results_data)}")
    print(f"Conditions: {conditions}")

    if not results_data or not conditions:
        print("❌ No results data or conditions - preventing update")
        raise PreventUpdate

    # Generate results table with new orientation
    results_table = create_results_table(
        results_data, conditions, orientation, table_data_options or ['monomer']
    )

    # Generate trend plot
    trend_fig = create_trend_plot(results_data, conditions, project_id or "Project", table_data_options or ['monomer'])

    print(f"✓ Creating results section with orientation: {orientation}")

    # Recreate results section
    results_section = html.Div(
        style={
            'backgroundColor': 'white',
            'borderRadius': '16px',
            'padding': '24px',
            'boxShadow': '0 4px 12px rgba(0,0,0,0.08)'
        },
        children=[
            # Header with table orientation toggle and export
            html.Div(
                style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '24px'},
                children=[
                    html.H3("Analysis Results", style={
                        'margin': '0',
                        'color': '#374151',
                        'fontSize': '22px',
                        'fontWeight': '700'
                    }),
                    html.Div(
                        style={'display': 'flex', 'gap': '16px', 'alignItems': 'center'},
                        children=[
                            html.Label("Table View:", style={'fontWeight': '600', 'fontSize': '14px', 'color': '#6b7280'}),
                            dcc.RadioItems(
                                id='table-orientation-toggle',
                                options=[
                                    {'label': ' Day Rows', 'value': 'day_rows'},
                                    {'label': ' Type Rows', 'value': 'type_rows'}
                                ],
                                value=orientation,
                                inline=True,
                                labelStyle={'marginRight': '15px'},
                                style={'display': 'flex', 'alignItems': 'center'}
                            ),
                            html.Button("📥 Export", id='export-data-btn', style={
                                'backgroundColor': '#059669',
                                'color': 'white',
                                'border': 'none',
                                'padding': '8px 16px',
                                'fontSize': '14px',
                                'cursor': 'pointer',
                                'borderRadius': '6px',
                                'fontWeight': '600',
                                'boxShadow': '0 2px 6px rgba(5, 150, 105, 0.3)'
                            })
                        ]
                    )
                ]
            ),
            # Trend Plot (full width on top)
            html.Div([
                html.H4("Stability Trend", style={
                    'margin': '0 0 16px 0',
                    'color': '#374151',
                    'fontSize': '18px',
                    'fontWeight': '600'
                }),
                dcc.Graph(
                    id='trend-plot',
                    figure=trend_fig,
                    config={'displayModeBar': True, 'displaylogo': False},
                    style={'marginBottom': '24px'}
                )
            ]),
            # Data Table (full width below trend)
            html.Div([
                html.H4("Data Summary", style={
                    'margin': '0 0 16px 0',
                    'color': '#374151',
                    'fontSize': '18px',
                    'fontWeight': '600'
                }),
                results_table
            ])
        ]
    )

    return results_section


def create_results_table(results_data, conditions, orientation, data_options):
    """Create results table with toggle between day rows and type rows"""
    if not results_data:
        return html.Div("No data available")

    data_types = []
    if 'monomer' in data_options:
        data_types.append(('Monomer %', 'monomer'))
    if 'hmw' in data_options:
        data_types.append(('HMW %', 'hmw'))
    if 'lmw' in data_options:
        data_types.append(('LMW %', 'lmw'))

    if orientation == 'day_rows':
        # Rows are days, columns are conditions
        table_data = []
        for result in results_data:
            day_label = f"D{result['day']}"
            for data_label, data_key in data_types:
                row = {'Timepoint': f"{day_label}", 'Data Type': data_label}
                for cond in conditions:
                    value = result.get(f'{cond}_{data_key}')
                    row[cond] = f"{value:.2f}" if value is not None else '—'
                table_data.append(row)

        columns = [{'name': 'Timepoint', 'id': 'Timepoint'}, {'name': 'Data Type', 'id': 'Data Type'}]
        for cond in conditions:
            columns.append({'name': cond, 'id': cond})

    else:  # type_rows
        # Rows are conditions, columns are days
        table_data = []
        for cond in conditions:
            for data_label, data_key in data_types:
                row = {'Condition': cond, 'Data Type': data_label}
                for result in results_data:
                    day_label = f"D{result['day']}"
                    value = result.get(f'{cond}_{data_key}')
                    row[day_label] = f"{value:.2f}" if value is not None else '—'
                table_data.append(row)

        columns = [{'name': 'Condition', 'id': 'Condition'}, {'name': 'Data Type', 'id': 'Data Type'}]
        for result in results_data:
            day_label = f"D{result['day']}"
            columns.append({'name': day_label, 'id': day_label})

    return dash_table.DataTable(
        columns=columns,
        data=table_data,
        style_cell={
            'textAlign': 'center',
            'padding': '12px',
            'fontSize': '14px',
            'border': '1px solid #e5e7eb'
        },
        style_header={
            'backgroundColor': '#f3f4f6',
            'fontWeight': '700',
            'color': '#374151',
            'border': '1px solid #d1d5db'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9fafb'}
        ]
    )


def create_trend_plot(results_data, conditions, project_id, data_options):
    """Create line plot showing trends over time"""
    if not results_data:
        return go.Figure()

    fig = go.Figure()
    colors = ['#ec4899', '#10b981', '#3b82f6', '#f59e0b', '#8b5cf6']

    days = [r['day'] for r in results_data]

    for idx, condition in enumerate(conditions):
        color = colors[idx % len(colors)]

        if 'monomer' in data_options:
            values = [r.get(f'{condition}_monomer') for r in results_data]
            fig.add_trace(go.Scatter(
                x=days, y=values,
                mode='lines+markers',
                name=f'{condition} - Monomer',
                line=dict(color=color, width=3),
                marker=dict(size=10)
            ))

    fig.update_layout(
        title={'text': f"{project_id} - Stability Trend", 'x': 0.5, 'xanchor': 'center'},
        xaxis_title="Day",
        yaxis_title="Monomer (%)",
        template='plotly_white',
        height=400,
        showlegend=True,
        legend=dict(
            x=1.02,
            y=1,
            xanchor='left',
            yanchor='top',
            bgcolor='rgba(255,255,255,0.95)',
            bordercolor='#d1d5db',
            borderwidth=1
        ),
        hovermode='x unified',
        margin=dict(l=60, r=120, t=60, b=60)  # Add right margin for legend
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#e5e7eb')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#e5e7eb', range=[0, 100])

    return fig


# ==================== EXPORT ====================

@app.callback(
    Output('download-plasma-stability-data', 'data'),
    Input('export-data-btn', 'n_clicks'),
    [State('monomer-data-store', 'data'),
     State('stability-config-store', 'data'),
     State('project-id-input', 'value'),
     State('conditions-store', 'data')],
    prevent_initial_call=True
)
def export_data(n_clicks, monomer_data, config_data, project_id, conditions):
    """Export stability data to Excel"""
    if not monomer_data:
        raise PreventUpdate

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Configuration sheet
        df_config = pd.DataFrame(config_data)
        df_config.to_excel(writer, sheet_name='Configuration', index=False)

        # Results sheet
        results_list = []
        for result in monomer_data:
            day_label = f"D{result['day']}"
            row = {'Timepoint': day_label, 'Day': result['day']}
            for cond in conditions:
                row[f'{cond} Monomer %'] = result.get(f'{cond}_monomer')
                row[f'{cond} HMW %'] = result.get(f'{cond}_hmw')
                row[f'{cond} LMW %'] = result.get(f'{cond}_lmw')
            results_list.append(row)

        df_results = pd.DataFrame(results_list)
        df_results.to_excel(writer, sheet_name='Results', index=False)

    output.seek(0)

    filename = f'plasma_stability_{project_id or "data"}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

    return {
        'content': output.getvalue(),
        'filename': filename,
        'type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }


print("✅ Plasma Stability App initialized successfully")
