"""
Simple Formulation Data Table App
Basic table view for formulation stability data
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table, no_update
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd

from plotly_integration.models import FormulationData

app = DjangoDash("FormulationTableApp")

COLOR_PALETTE = {
    "primary": "#2E86C1",
    "secondary": "#E74C3C", 
    "success": "#27AE60",
    "warning": "#F39C12",
    "info": "#8E44AD",
    "light": "#F8F9FA",
    "dark": "#2C3E50",
}

def get_experiments():
    """Get all available experiments"""
    try:
        experiments = FormulationData.objects.values('experiment_id').distinct().order_by('experiment_id')
        return [{'label': exp['experiment_id'], 'value': exp['experiment_id']} for exp in experiments]
    except Exception as e:
        print(f"Error fetching experiments: {e}")
        return []

def create_header():
    return html.Div([
        html.H1([
            html.I(className="fas fa-table me-3", style={"color": COLOR_PALETTE["primary"]}),
            "Formulation Data Table"
        ], className="mb-2"),
        html.P("View and manage formulation stability data", className="text-muted mb-4")
    ])

def create_controls():
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Select Experiment:"),
                    dcc.Dropdown(
                        id="experiment-dropdown",
                        options=get_experiments(),
                        value=None,
                        placeholder="Choose experiment...",
                        clearable=False
                    )
                ], width=6),
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-plus me-2"),
                        "Add New Sample"
                    ], id="add-sample-btn", color="primary", className="mt-4")
                ], width=6, className="d-flex justify-content-end")
            ])
        ])
    ], className="mb-4")

def create_add_sample_modal():
    return dbc.Modal([
        dbc.ModalHeader("Add New Sample"),
        dbc.ModalBody([
            dbc.Form([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Sample Number:"),
                        dbc.Input(id="sample-number", placeholder="e.g., FD-003-011", required=True)
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Time Point (months):"),
                        dbc.Input(id="time-point", type="number", step=0.5, placeholder="0, 1, 3, 6...")
                    ], width=6)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Buffer:"),
                        dbc.Input(id="buffer", placeholder="e.g., Phosphate")
                    ], width=6),
                    dbc.Col([
                        dbc.Label("pH:"),
                        dbc.Input(id="ph", type="number", step=0.1, placeholder="e.g., 6.5")
                    ], width=6)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Excipients:"),
                        dbc.Textarea(id="excipients", placeholder="Describe excipients", rows=2)
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Condition:"),
                        dbc.Input(id="condition", placeholder="e.g., 25°C")
                    ], width=6)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("HMW %:"),
                        dbc.Input(id="hmw", type="number", step=0.01)
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Main %:"),
                        dbc.Input(id="main", type="number", step=0.01)
                    ], width=4),
                    dbc.Col([
                        dbc.Label("LMW %:"),
                        dbc.Input(id="lmw", type="number", step=0.01)
                    ], width=4)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Concentration (mg/mL):"),
                        dbc.Input(id="concentration", type="number", step=0.1)
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Tm (°C):"),
                        dbc.Input(id="tm", type="number", step=0.1)
                    ], width=6)
                ])
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-btn", color="secondary", className="me-2"),
            dbc.Button("Save", id="save-btn", color="primary")
        ])
    ], id="add-modal", size="lg", is_open=False)

# Main Layout
app.layout = dbc.Container([
    create_header(),
    create_controls(),
    
    html.Div([
        html.Div(id="data-table-container")
    ], className="mb-4"),
    
    create_add_sample_modal(),
    
    dcc.Loading(
        id="loading",
        children=html.Div(id="loading-output"),
        type="default",
    )
], fluid=True, className="p-4")

# Callbacks
@app.callback(
    Output('data-table-container', 'children'),
    Input('experiment-dropdown', 'value')
)
def update_table(experiment_id):
    if not experiment_id:
        return html.Div([
            dbc.Alert("Please select an experiment to view data.", color="info", className="text-center")
        ])
    
    try:
        # Get data for selected experiment
        data = FormulationData.objects.filter(experiment_id=experiment_id).order_by('formulation_number', 'time_point_months')
        
        if not data.exists():
            return html.Div([
                dbc.Alert(f"No data found for experiment {experiment_id}.", color="warning", className="text-center")
            ])
        
        # Convert to DataFrame
        df = pd.DataFrame(list(data.values()))
        
        # Select and rename columns for display
        display_columns = [
            'sample_number', 'formulation_number', 'time_point_months', 
            'buffer', 'ph', 'condition', 'hmw_percent', 'main_percent', 
            'lmw_percent', 'concentration', 'tm_celsius', 'osmolality'
        ]
        
        df_display = df[display_columns].copy()
        
        # Rename columns for better display
        column_names = {
            'sample_number': 'Sample Number',
            'formulation_number': 'Formulation',
            'time_point_months': 'Time (months)',
            'buffer': 'Buffer',
            'ph': 'pH',
            'condition': 'Condition',
            'hmw_percent': 'HMW %',
            'main_percent': 'Main %',
            'lmw_percent': 'LMW %',
            'concentration': 'Conc (mg/mL)',
            'tm_celsius': 'Tm (°C)',
            'osmolality': 'Osmolality'
        }
        
        return html.Div([
            html.H5(f"Data for Experiment: {experiment_id}", className="mb-3"),
            dash_table.DataTable(
                data=df_display.to_dict('records'),
                columns=[{"name": column_names.get(col, col), "id": col} for col in df_display.columns],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left', 
                    'fontSize': 14, 
                    'fontFamily': 'Arial',
                    'padding': '10px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                },
                style_header={
                    'backgroundColor': COLOR_PALETTE["primary"], 
                    'color': 'white',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': COLOR_PALETTE["light"]
                    }
                ],
                page_size=20,
                sort_action="native",
                filter_action="native",
                export_format="xlsx",
                export_headers="display"
            )
        ])
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return html.Div([
            dbc.Alert(f"Error loading data: {str(e)}", color="danger")
        ])

# Modal callbacks
@app.callback(
    Output("add-modal", "is_open"),
    [Input("add-sample-btn", "n_clicks"), Input("cancel-btn", "n_clicks"), Input("save-btn", "n_clicks")],
    [State("add-modal", "is_open")]
)
def toggle_modal(add_clicks, cancel_clicks, save_clicks, is_open):
    if add_clicks or cancel_clicks or save_clicks:
        return not is_open
    return is_open

@app.callback(
    [Output("sample-number", "value"),
     Output("time-point", "value"),
     Output("buffer", "value"),
     Output("ph", "value"),
     Output("excipients", "value"),
     Output("condition", "value"),
     Output("hmw", "value"),
     Output("main", "value"),
     Output("lmw", "value"),
     Output("concentration", "value"),
     Output("tm", "value"),
     Output("experiment-dropdown", "options", allow_duplicate=True),
     Output("data-table-container", "children", allow_duplicate=True)],
    Input("save-btn", "n_clicks"),
    [State("sample-number", "value"),
     State("time-point", "value"),
     State("buffer", "value"),
     State("ph", "value"),
     State("excipients", "value"),
     State("condition", "value"),
     State("hmw", "value"),
     State("main", "value"),
     State("lmw", "value"),
     State("concentration", "value"),
     State("tm", "value"),
     State("experiment-dropdown", "value")],
    prevent_initial_call=True
)
def save_sample(n_clicks, sample_number, time_point, buffer, ph, excipients, 
               condition, hmw, main, lmw, concentration, tm, current_experiment):
    if not n_clicks or not sample_number:
        return [no_update] * 11 + [get_experiments(), no_update]
    
    try:
        # Parse sample number
        parts = sample_number.split('-')
        if len(parts) >= 3:
            experiment_id = f"{parts[0]}-{parts[1]}"
            formulation_number = parts[2]
        else:
            experiment_id = "Unknown"
            formulation_number = "Unknown"
        
        # Create new sample
        FormulationData.objects.create(
            sample_number=sample_number,
            experiment_id=experiment_id,
            formulation_number=formulation_number,
            time_point_months=float(time_point) if time_point else None,
            buffer=buffer or "",
            ph=float(ph) if ph else None,
            excipients=excipients or "",
            condition=condition or "",
            hmw_percent=float(hmw) if hmw else None,
            main_percent=float(main) if main else None,
            lmw_percent=float(lmw) if lmw else None,
            concentration=float(concentration) if concentration else None,
            tm_celsius=float(tm) if tm else None,
        )
        
        # Clear form and refresh table
        updated_experiments = get_experiments()
        
        # Refresh table if we're viewing the same experiment
        if current_experiment == experiment_id:
            # Get updated data
            data = FormulationData.objects.filter(experiment_id=experiment_id).order_by('formulation_number', 'time_point_months')
            df = pd.DataFrame(list(data.values()))
            
            display_columns = [
                'sample_number', 'formulation_number', 'time_point_months', 
                'buffer', 'ph', 'condition', 'hmw_percent', 'main_percent', 
                'lmw_percent', 'concentration', 'tm_celsius', 'osmolality'
            ]
            
            df_display = df[display_columns].copy()
            
            column_names = {
                'sample_number': 'Sample Number',
                'formulation_number': 'Formulation',
                'time_point_months': 'Time (months)',
                'buffer': 'Buffer',
                'ph': 'pH',
                'condition': 'Condition',
                'hmw_percent': 'HMW %',
                'main_percent': 'Main %',
                'lmw_percent': 'LMW %',
                'concentration': 'Conc (mg/mL)',
                'tm_celsius': 'Tm (°C)',
                'osmolality': 'Osmolality'
            }
            
            updated_table = html.Div([
                html.H5(f"Data for Experiment: {experiment_id}", className="mb-3"),
                dash_table.DataTable(
                    data=df_display.to_dict('records'),
                    columns=[{"name": column_names.get(col, col), "id": col} for col in df_display.columns],
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left', 
                        'fontSize': 14, 
                        'fontFamily': 'Arial',
                        'padding': '10px',
                        'whiteSpace': 'normal',
                        'height': 'auto',
                    },
                    style_header={
                        'backgroundColor': COLOR_PALETTE["primary"], 
                        'color': 'white',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': COLOR_PALETTE["light"]
                        }
                    ],
                    page_size=20,
                    sort_action="native",
                    filter_action="native",
                    export_format="xlsx",
                    export_headers="display"
                )
            ])
        else:
            updated_table = no_update
        
        return [""] * 11 + [updated_experiments, updated_table]
        
    except Exception as e:
        print(f"Error saving sample: {e}")
        return [no_update] * 11 + [get_experiments(), no_update]

if __name__ == '__main__':
    app.run_server(debug=True)