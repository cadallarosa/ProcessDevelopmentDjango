"""
Formulation Data Management App
Modern interface for managing formulation stability data
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table, no_update
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from plotly_integration.models import FormulationData

app = DjangoDash("FormulationApp")

def get_experiments():
    """Get all available experiments using the property"""
    try:
        experiments = set()
        for sample in FormulationData.objects.all():
            experiments.add(sample.experiment_id)
        return [{'label': exp, 'value': exp} for exp in sorted(list(experiments))]
    except Exception as e:
        print(f"Error fetching experiments: {e}")
        return []

COLOR_PALETTE = {
    "primary": "#2E86C1",
    "secondary": "#E74C3C", 
    "success": "#27AE60",
    "warning": "#F39C12",
    "info": "#8E44AD",
    "light": "#F8F9FA",
    "dark": "#2C3E50",
    "background": "#FFFFFF",
}

MODERN_STYLE = {
    "font_family": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    "card_shadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
    "border_radius": "8px"
}

def create_header():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1([
                    html.I(className="fas fa-flask me-3", style={"color": COLOR_PALETTE["primary"]}),
                    "Formulation"
                ], className="mb-4", style={"fontFamily": MODERN_STYLE["font_family"]})
            ])
        ])
    ], fluid=True, className="mb-4")

def create_controls():
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-sliders-h me-2"),
                "Experiment Controls"
            ], className="mb-0", style={"fontFamily": MODERN_STYLE["font_family"]})
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Select Experiment:", className="fw-bold"),
                    dcc.Dropdown(
                        id="experiment-dropdown",
                        options=get_experiments(),
                        value="FD-003",  # Default to FD-003
                        placeholder="Choose experiment...",
                        clearable=False,
                        style={"fontFamily": MODERN_STYLE["font_family"]}
                    )
                ], width=4),
                dbc.Col([
                    html.Div(id="save-status", className="mt-2")
                ], width=8)
            ])
        ])
    ], className="mb-4", style={"boxShadow": MODERN_STYLE["card_shadow"]})

def create_tabs_content():
    return html.Div([
        dcc.Tabs(
            id="main-tabs",
            value="data-tab",
            children=[
                dcc.Tab(label="Data Table", value="data-tab"),
                dcc.Tab(label="Graphs", value="graphs-tab"),
            ],
            className="mb-4"
        ),
        html.Div(id="tab-content")
    ])

def create_data_tab_content():
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Button([
                    html.I(className="fas fa-save me-2"),
                    "Update Database"
                ], id="save-btn", color="success", disabled=True, className="me-2"),
                html.Small("Changes are automatically detected", className="text-muted")
            ], width=12, className="mb-3")
        ]),
        html.Div(id="data-table-container")
    ])

def create_graphs_tab_content():
    return html.Div([
        dbc.Card([
            dbc.CardHeader([
                html.H6([
                    html.I(className="fas fa-chart-line me-2"),
                    "Graph Controls"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Storage Condition:", className="fw-bold"),
                        dcc.Dropdown(
                            id="storage-condition-filter",
                            options=[
                                {"label": "All Conditions", "value": "all"},
                                {"label": "25°C Only", "value": "25°C"},
                                {"label": "40°C Only", "value": "40°C"},
                                {"label": "4°C Only", "value": "4°C"},
                                {"label": "-80°C Only", "value": "-80°C"}
                            ],
                            value="all",
                            clearable=False
                        )
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Y-Axis Variable:", className="fw-bold"),
                        dcc.Dropdown(
                            id="y-axis-selector",
                            options=[
                                {"label": "HMW %", "value": "hmw"},
                                {"label": "Main %", "value": "main"},
                                {"label": "LMW %", "value": "lmw"},
                                {"label": "Concentration (mg/mL)", "value": "concentration"},
                                {"label": "pH (measured)", "value": "ph_measured"},
                                {"label": "Total Area", "value": "total_area"},
                                {"label": "Tm (°C)", "value": "tm_celsius"},
                                {"label": "Osmolality", "value": "osmolality"}
                            ],
                            value="hmw",
                            clearable=False
                        )
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Select Formulations:", className="fw-bold"),
                        dcc.Dropdown(
                            id="formulation-selector",
                            options=[],
                            value=[],
                            multi=True,
                            placeholder="All formulations (leave blank for all)"
                        )
                    ], width=4)
                ])
            ])
        ], className="mb-4"),
        dcc.Graph(id="main-graph", style={"height": "80vh"})
    ])

# Define columns exactly matching Excel structure
COLUMNS = [
    {"name": "Sample Number", "id": "sample_number", "editable": False, "type": "text"},
    {"name": "Buffer", "id": "buffer", "editable": True, "type": "text"},
    {"name": "pH", "id": "ph", "editable": True, "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "Excipients", "id": "excipients", "editable": True, "type": "text"},
    {"name": "Formulation", "id": "formulation", "editable": True, "type": "text"},
    {"name": "Condition", "id": "condition", "editable": True, "type": "text"},
    {"name": "Pull Day", "id": "pull_day", "editable": True, "type": "numeric"},
    {"name": "Time Point (months)", "id": "time_point_months", "editable": True, "type": "numeric", "format": {"specifier": ".1f"}},
    {"name": "Appearance", "id": "appearance", "editable": True, "type": "text"},
    {"name": "Concentration (mg/mL)", "id": "concentration", "editable": True, "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "pH (measured)", "id": "ph_measured", "editable": True, "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "Result ID", "id": "result_id", "editable": True, "type": "text"},
    {"name": "HMW", "id": "hmw", "editable": True, "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "Main", "id": "main", "editable": True, "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "LMW", "id": "lmw", "editable": True, "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "Total Area", "id": "total_area", "editable": True, "type": "numeric"},
    {"name": "Osmolality (mOsm/kg)", "id": "osmolality", "editable": True, "type": "numeric"},
    {"name": "Tm (°C)", "id": "tm_celsius", "editable": True, "type": "numeric", "format": {"specifier": ".1f"}},
    {"name": "Scattering Onset", "id": "scattering_onset", "editable": True, "type": "numeric", "format": {"specifier": ".1f"}},
]

# Main Layout
app.layout = dbc.Container([
    dcc.Store(id='original-data-store'),
    dcc.Store(id='has-changes-store', data=False),

    create_header(),
    create_controls(),
    create_tabs_content(),

    dcc.Loading(
        id="loading",
        children=html.Div(id="loading-output"),
        type="default",
    )
], fluid=True, className="p-4", style={
    "backgroundColor": COLOR_PALETTE["light"],
    "minHeight": "100vh",
    "fontFamily": MODERN_STYLE["font_family"]
})

# Callbacks
@app.callback(
    Output('tab-content', 'children'),
    [Input('main-tabs', 'value'),
     Input('experiment-dropdown', 'value')]
)
def switch_tab(active_tab, experiment_id):
    if active_tab == "data-tab":
        return create_data_tab_content()
    elif active_tab == "graphs-tab":
        return create_graphs_tab_content()
    return create_data_tab_content()

@app.callback(
    [Output('data-table-container', 'children'),
     Output('original-data-store', 'data')],
    Input('experiment-dropdown', 'value')
)
def load_table(experiment_id):
    if not experiment_id:
        return html.Div([
            dbc.Alert("Please select an experiment to view data.", color="info", className="text-center")
        ]), {}

    try:
        # Get data for selected experiment using the property
        all_samples = FormulationData.objects.all()
        filtered_samples = [s for s in all_samples if s.experiment_id == experiment_id]

        if not filtered_samples:
            return html.Div([
                dbc.Alert(f"No data found for experiment {experiment_id}.", color="warning", className="text-center")
            ]), {}

        # Convert to DataFrame-like structure
        data = []
        for sample in filtered_samples:
            data.append({
                'id': sample.id,
                'sample_number': sample.sample_number,
                'buffer': sample.buffer,
                'ph': sample.ph,
                'excipients': sample.excipients,
                'formulation': sample.formulation,
                'condition': sample.condition,
                'pull_day': sample.pull_day,
                'time_point_months': sample.time_point_months,
                'appearance': sample.appearance,
                'concentration': sample.concentration,
                'ph_measured': sample.ph_measured,
                'result_id': sample.result_id,
                'hmw': sample.hmw,
                'main': sample.main,
                'lmw': sample.lmw,
                'total_area': sample.total_area,
                'osmolality': sample.osmolality,
                'tm_celsius': sample.tm_celsius,
                'scattering_onset': sample.scattering_onset,
            })

        # Sort by sample number
        data.sort(key=lambda x: x['sample_number'])
        
        # Add a blank row at the bottom for new entries
        # Find next sample number
        existing_numbers = []
        for sample in filtered_samples:
            try:
                num = int(sample.formulation_number)
                existing_numbers.append(num)
            except:
                pass
        
        next_num = max(existing_numbers) + 1 if existing_numbers else 121
        blank_row = {
            'id': None,
            'sample_number': f"{experiment_id}-{next_num:03d}",
            'buffer': '',
            'ph': None,
            'excipients': '',
            'formulation': '',
            'condition': '',
            'pull_day': None,
            'time_point_months': None,
            'appearance': '',
            'concentration': None,
            'ph_measured': None,
            'result_id': '',
            'hmw': None,
            'main': None,
            'lmw': None,
            'total_area': None,
            'osmolality': None,
            'tm_celsius': None,
            'scattering_onset': None,
        }
        data.append(blank_row)

        table = dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className="fas fa-table me-2"),
                    f"Data for Experiment: {experiment_id} ({len(data)} samples)"
                ], className="mb-0", style={"fontFamily": MODERN_STYLE["font_family"]})
            ]),
            dbc.CardBody([
                dash_table.DataTable(
                    id='editable-table',
                    data=data,
                    columns=COLUMNS,
                    editable=True,
                    row_deletable=True,
                    style_table={
                        'overflowX': 'auto',
                        'overflowY': 'auto',
                        'maxHeight': '70vh'
                    },
                    style_cell={
                        'textAlign': 'left',
                        'fontSize': 13,
                        'fontFamily': MODERN_STYLE["font_family"],
                        'padding': '10px',
                        'whiteSpace': 'normal',
                        'height': 'auto',
                        'minWidth': '120px',
                        'maxWidth': '180px',
                        'border': '1px solid #dee2e6'
                    },
                    style_header={
                        'backgroundColor': COLOR_PALETTE["primary"],
                        'color': 'white',
                        'fontWeight': 'bold',
                        'textAlign': 'center',
                        'border': '1px solid #dee2e6'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': COLOR_PALETTE["light"]
                        },
                        {
                            'if': {'column_id': 'sample_number'},
                            'backgroundColor': '#E3F2FD',
                            'fontWeight': 'bold'
                        },
                        {
                            'if': {'state': 'selected'},
                            'backgroundColor': '#D1ECF1',
                            'border': '1px solid #bee5eb'
                        }
                    ],
                    sort_action="native",
                    filter_action="native",
                    export_format="xlsx",
                    export_headers="display",
                    fill_width=False,
                    fixed_rows={'headers': True}
                )
            ])
        ], style={"boxShadow": MODERN_STYLE["card_shadow"]})

        return table, data

    except Exception as e:
        print(f"Error loading data: {e}")
        return html.Div([
            dbc.Alert(f"Error loading data: {str(e)}", color="danger")
        ]), {}

@app.callback(
    [Output('has-changes-store', 'data'),
     Output('save-btn', 'disabled')],
    [Input('editable-table', 'data'),
     Input('editable-table', 'data_previous')],
    [State('original-data-store', 'data')],
    prevent_initial_call=True
)
def detect_changes(current_data, previous_data, original_data):
    if not current_data or not original_data:
        return False, True

    # Compare current data with original
    has_changes = current_data != original_data
    return has_changes, not has_changes

@app.callback(
    [Output('save-status', 'children'),
     Output('original-data-store', 'data', allow_duplicate=True),
     Output('has-changes-store', 'data', allow_duplicate=True)],
    Input('save-btn', 'n_clicks'),
    [State('editable-table', 'data'),
     State('original-data-store', 'data')],
    prevent_initial_call=True
)
def save_changes(n_clicks, current_data, original_data):
    if not n_clicks or not current_data:
        return "", no_update, no_update

    try:
        saved_count = 0
        created_count = 0
        errors = []

        # Create a map of original data by ID for quick lookup
        original_map = {item.get('id'): item for item in original_data if item.get('id')}

        for row in current_data:
            try:
                row_id = row.get('id')
                
                if not row_id:
                    # This is a new row - create it
                    sample_number = row.get('sample_number')
                    if not sample_number:
                        continue
                        
                    new_sample = FormulationData.objects.create(
                        sample_number=sample_number,
                        buffer=row.get('buffer') or None,
                        ph=row.get('ph'),
                        excipients=row.get('excipients') or None,
                        formulation=row.get('formulation') or None,
                        condition=row.get('condition') or None,
                        pull_day=row.get('pull_day'),
                        time_point_months=row.get('time_point_months'),
                        appearance=row.get('appearance') or None,
                        concentration=row.get('concentration'),
                        ph_measured=row.get('ph_measured'),
                        result_id=row.get('result_id') or None,
                        hmw=row.get('hmw'),
                        main=row.get('main'),
                        lmw=row.get('lmw'),
                        total_area=row.get('total_area'),
                        osmolality=row.get('osmolality'),
                        tm_celsius=row.get('tm_celsius'),
                        scattering_onset=row.get('scattering_onset'),
                    )
                    # Update the row with the new ID
                    row['id'] = new_sample.id
                    created_count += 1
                else:
                    # Update existing row
                    sample = FormulationData.objects.get(id=row_id)
                    original_row = original_map.get(row_id, {})

                    # Update all fields
                    sample.buffer = row.get('buffer') or None
                    sample.ph = row.get('ph')
                    sample.excipients = row.get('excipients') or None
                    sample.formulation = row.get('formulation') or None
                    sample.condition = row.get('condition') or None
                    sample.pull_day = row.get('pull_day')
                    sample.time_point_months = row.get('time_point_months')
                    sample.appearance = row.get('appearance') or None
                    sample.concentration = row.get('concentration')
                    sample.ph_measured = row.get('ph_measured')
                    sample.result_id = row.get('result_id') or None
                    sample.hmw = row.get('hmw')
                    sample.main = row.get('main')
                    sample.lmw = row.get('lmw')
                    sample.total_area = row.get('total_area')
                    sample.osmolality = row.get('osmolality')
                    sample.tm_celsius = row.get('tm_celsius')
                    sample.scattering_onset = row.get('scattering_onset')

                    sample.save()
                    saved_count += 1

            except Exception as e:
                errors.append(f"Row {row.get('sample_number', 'Unknown')}: {str(e)}")

        # Update the original data store to current data to prevent showing changes
        message_parts = []
        if created_count > 0:
            message_parts.append(f"Created {created_count} new records")
        if saved_count > 0:
            message_parts.append(f"Updated {saved_count} records")
        
        success_message = ", ".join(message_parts) + "!"

        if errors:
            return dbc.Alert([
                html.Strong(f"{success_message} {len(errors)} errors occurred:"),
                html.Ul([html.Li(error) for error in errors[:5]])
            ], color="warning", dismissable=True), current_data, False
        else:
            return dbc.Alert(success_message, color="success", dismissable=True), current_data, False

    except Exception as e:
        return dbc.Alert(f"Error saving data: {str(e)}", color="danger", dismissable=True), no_update, no_update

# Graph callbacks
@app.callback(
    Output('formulation-selector', 'options'),
    Input('experiment-dropdown', 'value')
)
def update_formulation_dropdown(experiment_id):
    if not experiment_id:
        return []
    
    try:
        # Get all samples for the experiment
        all_samples = FormulationData.objects.all()
        filtered_samples = [s for s in all_samples if s.experiment_id == experiment_id]
        
        # Group by unique formulation (Buffer + pH + Excipients)
        formulation_groups = {}
        for sample in filtered_samples:
            # Create formulation key from Buffer + pH + Excipients
            buffer = sample.buffer or "Unknown"
            ph = f"pH{sample.ph}" if sample.ph else "pHUnknown"
            excipients = sample.excipients[:30] + "..." if sample.excipients and len(sample.excipients) > 30 else (sample.excipients or "No excipients")
            
            formulation_key = f"{buffer} | {ph} | {excipients}"
            
            if formulation_key not in formulation_groups:
                formulation_groups[formulation_key] = {
                    'key': formulation_key,
                    'buffer': buffer,
                    'ph': sample.ph,
                    'excipients': sample.excipients,
                    'samples': []
                }
            
            formulation_groups[formulation_key]['samples'].append(sample)
        
        # Create dropdown options
        formulation_options = []
        for key, group in sorted(formulation_groups.items()):
            sample_count = len(group['samples'])
            formulation_options.append({
                'label': f"{key} ({sample_count} samples)",
                'value': key
            })
        
        return formulation_options
    except Exception as e:
        print(f"Error updating dropdown: {e}")
        return []

@app.callback(
    Output('main-graph', 'figure'),
    [Input('y-axis-selector', 'value'),
     Input('formulation-selector', 'value'),
     Input('storage-condition-filter', 'value'),
     Input('experiment-dropdown', 'value')]
)
def update_graph(y_axis_variable, selected_formulations, storage_condition_filter, experiment_id):
    if not experiment_id or not y_axis_variable:
        return go.Figure().add_annotation(
            text="Select experiment and Y-axis variable",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
        )
    
    try:
        # Get all samples for the experiment
        all_samples = FormulationData.objects.all()
        filtered_samples = [s for s in all_samples if s.experiment_id == experiment_id]
        
        if not filtered_samples:
            return go.Figure().add_annotation(
                text="No data available",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
            )
        
        # Group samples by formulation (Buffer + pH + Excipients)
        formulation_groups = {}
        for sample in filtered_samples:
            buffer = sample.buffer or "Unknown"
            ph = f"pH{sample.ph}" if sample.ph else "pHUnknown"
            excipients = sample.excipients[:30] + "..." if sample.excipients and len(sample.excipients) > 30 else (sample.excipients or "No excipients")
            
            formulation_key = f"{buffer} | {ph} | {excipients}"
            
            if formulation_key not in formulation_groups:
                formulation_groups[formulation_key] = []
            
            formulation_groups[formulation_key].append(sample)
        
        # Filter by selected formulations if any
        if selected_formulations:
            formulation_groups = {k: v for k, v in formulation_groups.items() if k in selected_formulations}
        
        if not formulation_groups:
            return go.Figure().add_annotation(
                text="No data matches the selected filters",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
            )
        
        # Create subplots - one for each formulation
        num_formulations = len(formulation_groups)
        cols = min(2, num_formulations)  # Max 2 columns
        rows = (num_formulations + cols - 1) // cols  # Ceiling division
        
        fig = make_subplots(
            rows=rows, cols=cols,
            subplot_titles=list(formulation_groups.keys()),
            vertical_spacing=0.12,  # Optimized spacing between rows
            horizontal_spacing=0.08
        )
        
        # Color palette for conditions
        condition_colors = {
            '25°C': '#1f77b4',
            '40°C': '#ff7f0e', 
            '4°C': '#2ca02c',
            '-80°C': '#d62728',
            'FT': '#9467bd',
            '25 °C': '#1f77b4',  # Alternative formatting
            '40 °C': '#ff7f0e',
        }
        
        y_axis_labels = {
            'hmw': 'HMW %',
            'main': 'Main %',
            'lmw': 'LMW %',
            'concentration': 'Concentration (mg/mL)',
            'ph_measured': 'pH (measured)',
            'total_area': 'Total Area',
            'tm_celsius': 'Tm (°C)',
            'osmolality': 'Osmolality (mOsm/kg)'
        }
        
        for i, (formulation_key, samples) in enumerate(formulation_groups.items()):
            row = (i // cols) + 1
            col = (i % cols) + 1
            
            # Group samples by condition within this formulation
            condition_groups = {}
            for sample in samples:
                condition = sample.condition or "Unknown"
                
                # Filter by storage condition if specified (with flexible matching)
                if storage_condition_filter != "all":
                    condition_normalized = condition.replace(" ", "").lower()
                    filter_normalized = storage_condition_filter.replace(" ", "").lower()
                    if condition_normalized != filter_normalized:
                        continue
                
                if condition not in condition_groups:
                    condition_groups[condition] = []
                condition_groups[condition].append(sample)
            
            # Plot each condition as a separate line
            for condition, condition_samples in condition_groups.items():
                # Extract time points and y values
                time_points = []
                y_values = []
                
                for sample in condition_samples:
                    if sample.time_point_months is not None:
                        time_points.append(sample.time_point_months)
                        y_val = getattr(sample, y_axis_variable, None)
                        y_values.append(y_val)
                
                # Sort by time
                if time_points and y_values:
                    paired_data = list(zip(time_points, y_values))
                    paired_data = [(t, y) for t, y in paired_data if y is not None]
                    if paired_data:
                        paired_data.sort()
                        time_points, y_values = zip(*paired_data)
                    
                        # Add trace
                        fig.add_trace(
                            go.Scatter(
                                x=time_points,
                                y=y_values,
                                mode='lines+markers',
                                name=condition,
                                line=dict(color=condition_colors.get(condition, '#8c564b')),
                                showlegend=(i == 0)  # Only show legend for first subplot
                            ),
                            row=row, col=col
                        )
        
        # Update layout with improved height calculation
        # Give more height per row to ensure subplots are properly sized
        base_height = 400  # Base height for single row
        additional_height = 350  # Height added per additional row
        calculated_height = base_height + (additional_height * (rows - 1))
        
        fig.update_layout(
            height=calculated_height,
            title=f"Time Series: {y_axis_labels.get(y_axis_variable, y_axis_variable)} by Formulation and Storage Condition",
            showlegend=True,
            title_x=0.5  # Center the title
        )
        
        # Update axes
        for i in range(1, rows + 1):
            for j in range(1, cols + 1):
                fig.update_xaxes(title_text="Time (months)", row=i, col=j)
                fig.update_yaxes(title_text=y_axis_labels.get(y_axis_variable, y_axis_variable), row=i, col=j)
        
        return fig
        
    except Exception as e:
        print(f"Error creating graph: {e}")
        return go.Figure().add_annotation(
            text=f"Error creating graph: {str(e)}",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
        )


if __name__ == '__main__':
    app.run_server(debug=True)
